"""BLE collector and local display only. This app never performs inference."""
import hashlib,asyncio,csv,json,logging,math,threading,time,webbrowser,argparse,sys,secrets,urllib.request
from pathlib import Path
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from protocol import SERVICE,MOTION,ENV,SCORES,CONTROL,ROADS,CONDITIONS,QUALITY,FAULTS,motion,environment,scores,command,decision
ROOT=Path(__file__).resolve().parent
class Engine:
 def __init__(self,root=ROOT):
  self.lock=threading.RLock();self.stop=threading.Event();self.manifest=json.loads((root/'model_manifest.json').read_text());self.model_id=self.manifest['model_id'];self.report=self.manifest['report']
  self.settings={'mode':1,'surface':0,'issue':0,'severity':50,'rpm':120,'seed':20261005};self.request=secrets.randbelow(65534)+1;self.ack=None;self.last_seq=None;self.last_motion=None;self.last_env=None;self.last_scores=None;self.verified=False;self.connection_epoch=0;self.last_window_time=None;self.last_window=None;self.packet_error=None;self.log_error=None
  self.connection='Starting';self.error=None;self.faults=0;self.env={};self.raw={};self.pred={'condition':[0]*4,'road':[0]*4,'quality':0};self.history=deque(maxlen=500);self.received=0;self.dropped=0;self.run_id='unlabelled';self.truth='unlabelled'
  (root/'logs').mkdir(exist_ok=True);self.log_path=root/'logs'/time.strftime('expanded_%Y%m%d_%H%M%S.csv');self.fp=self.log_path.open('w',newline='');self.writer=csv.DictWriter(self.fp,fieldnames=['time','mode','request','run_id','truth','device_ms','ax','ay','az','gz','rpm','quality','window','pressure_psi','temperature_c','humidity_pct','condition_scores','road_scores','model_verified']);self.writer.writeheader();self.fp.flush()
 def configure(self,body):
  if not isinstance(body,dict):raise ValueError('Expected a settings object.')
  with self.lock:
   restart=body.get('restart',False)
   if not isinstance(restart,bool):raise ValueError('restart must be true or false.')
   new=dict(self.settings)
   for k,v in body.items():
    if k=='restart':continue
    if k not in new:raise ValueError('Unknown setting: '+k)
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or int(v)!=v:raise ValueError('Settings must be finite whole numbers.')
    new[k]=int(v)
   if new['mode'] not in (0,1) or new['surface'] not in range(4) or new['issue'] not in range(4):raise ValueError('Invalid mode, issue or surface.')
   if not 0<=new['severity']<=100 or not 78<=new['rpm']<=162 or not 1<=new['seed']<=4294967295:raise ValueError('Severity: 0–100; RPM: 78–162; seed: 1–4294967295.')
   if new!=self.settings or restart:
    self.settings=new;self.request=(self.request+1)%65536;self.ack=None;self.history.clear();self.last_scores=None;self.last_motion=None;self.env={};self.last_env=None;self.raw={};self.pred={'condition':[0]*4,'road':[0]*4,'quality':0};self.run_id=self.truth='unlabelled';self.last_window=None;self.last_window_time=None
   return dict(self.settings)
 def consume_scores(self,data):
  p=scores(data)
  with self.lock:
   if p['request']!=self.request or p['mode']!=self.settings['mode']:return
   if self.ack!=self.request:self.last_seq=None
   self.ack=self.request;self.pred=p;self.last_scores=time.monotonic()
 def consume_environment(self,data):
  p=environment(data)
  with self.lock:
   if p['request']!=self.request or p['mode']!=self.settings['mode'] or self.ack!=self.request:return
   self.verified=p['model_id']==self.model_id;self.faults=p['faults'];self.env=p;self.last_env=time.monotonic()
   if self.last_window!=p['window']:
    self.last_window=p['window'];self.last_window_time=self.last_env
 def consume_motion(self,data):
  p=motion(data)
  with self.lock:
   if p['mode']!=self.settings['mode'] or p['request']!=self.request or self.ack!=self.request:return
   if self.last_seq is not None:
    delta=(p['seq']-self.last_seq)%65536
    if delta==0 or delta>=32768:return
    self.dropped+=max(0,delta-1)
   self.last_seq=p['seq'];self.received+=1;self.raw=p;self.last_motion=time.monotonic();now=time.time()
   row=dict(time=now,mode='synthetic_on_arduino' if p['mode'] else 'live_sensor',request=self.request,run_id=self.run_id,truth=self.truth,**{k:p[k] for k in ['device_ms','ax','ay','az','gz','rpm','quality']})
   row.update({k:self.env.get(k) for k in ['window','pressure_psi','temperature_c','humidity_pct']});row['condition_scores']=json.dumps(self.pred['condition']);row['road_scores']=json.dumps(self.pred['road']) if p['mode'] else '';row['model_verified']=self.verified
   try:
    self.writer.writerow(row);self.fp.flush();self.log_error=None
   except OSError as exc:self.log_error='CSV_WRITE_FAILED: '+str(exc)+'. Move the demo folder to a writable location.'
   self.history.append({'time':now,'az':p['az'],'ay':p['ay'],'ax':p['ax']})
 def snapshot(self):
  with self.lock:
   now=time.monotonic();age=None if self.last_motion is None else now-self.last_motion;fresh=age is not None and age<2;scorefresh=self.last_scores is not None and now-self.last_scores<5 and self.last_window_time is not None and now-self.last_window_time<5;ack=self.ack==self.request;usable=fresh and scorefresh and self.verified and ack and self.connection=='Connected' and self.pred['quality']==1 and self.raw.get('quality')==1
   cs=self.pred['condition'] if usable else [0]*4;rs=self.pred['road'] if usable and self.settings['mode'] else [0]*4
   ci=decision(cs,self.report['models']['condition']['threshold']);ri=decision(rs,self.report['models']['road']['threshold'])
   status='Valid window' if usable else QUALITY.get(self.pred['quality'],'Waiting')
   if self.connection!='Connected':status=self.connection
   elif not ack:status='Applying settings'
   elif not self.verified:status='Model mismatch / checking'
   elif not fresh:status='Waiting for data' if age is None else 'Data stale'
   elif self.pred['quality']==1 and not scorefresh:status='Predictions stale'
   elif self.raw.get('quality') not in (None,0,1):status=QUALITY[self.raw['quality']]
   label=CONDITIONS[ci] if ci is not None else ('Uncertain' if usable else status)
   issues=[]
   if self.error:issues.append(self.error)
   if self.packet_error:issues.append(self.packet_error)
   if self.log_error:issues.append(self.log_error)
   if self.connection=='Connected' and not self.verified:issues.append('MODEL_MISMATCH: use the firmware and friend folder from the same expanded ZIP.')
   if ack and self.pred['quality']==1 and self.last_scores is not None and not scorefresh:issues.append('PREDICTIONS_STALE: no fresh model result. Restart the board and reconnect.')
   if self.settings['mode']==0:
    issues.extend(FAULTS[b]+'. Restart board and inspect Serial output.' for b in FAULTS if self.faults&b)
   envfresh=self.last_env is not None and now-self.last_env<4 and fresh
   raw=dict(self.raw) if fresh else {};env=dict(self.env) if envfresh else {}
   if self.connection=='Connected' and ack and age is not None and not fresh:issues.append('MOTION_STALE: board connected but fresh readings stopped; automatic recovery will run.')
   if self.connection=='Connected' and ack and self.last_env is not None and not envfresh and fresh:issues.append('ENVIRONMENT_STALE: pressure/temperature telemetry stopped; values are hidden.')
   return {'settings':dict(self.settings),'connection':self.connection,'stream':'Receiving data' if fresh else 'Waiting / stale','verified':self.verified,'ack':ack,'status':status,'condition_label':label,'road_label':ROADS[ri] if ri is not None else ('Uncertain' if self.settings['mode'] and usable else 'Waiting' if self.settings['mode'] else 'Road surface unavailable — airborne rig'),'condition_scores':cs,'road_scores':rs,'raw':raw,'environment':env,'history':list(self.history) if fresh else [],'issues':issues,'received':self.received,'dropped':self.dropped,'age':age,'report':self.report,'log':self.log_path.name,'model_id':self.model_id,'run_id':self.run_id,'truth':self.truth}
 async def worker(self,scanner=None,client_type=None):
  if scanner is None:
   from ble_transport import Transport
   transport=Transport()
   try:await self.worker(transport,transport.client)
   finally:await transport.close()
   return
  while not self.stop.is_set():
   try:
    with self.lock:
     self.connection='Scanning';self.verified=False;self.ack=None;self.connection_epoch+=1
     epoch=self.connection_epoch
    found=await scanner.discover(timeout=5,return_adv=True)
    matches=[];old=[]
    for device,adv in found.values():
     name=adv.local_name or device.name or ''
     if name=='TyreLabExpanded' or SERVICE in [u.lower() for u in adv.service_uuids]:matches.append(device)
     elif name in ('TyreLabRev2','TyreTinyML'):old.append(name)
    if not matches:
     if old:raise RuntimeError('OLD_FIRMWARE: found '+', '.join(old)+'. Upload the audited TyreLabExpanded sketch. This dashboard cannot use earlier sketches.')
     raise RuntimeError('NO_BOARD: no TyreLabExpanded advertisement. Power/reset the Nano, enable Bluetooth, close nRF Connect/phone apps and bring it close. The app retries.')
    if len(matches)>1:raise RuntimeError('MULTIPLE_BOARDS: turn off other TyreLabExpanded boards.')
    with self.lock:self.connection='Connecting'
    kwargs={'timeout':15}
    async with client_type(matches[0],**kwargs) as client:
     if any(client.services.get_characteristic(u) is None for u in [MOTION,ENV,SCORES,CONTROL]):raise RuntimeError('WRONG_FIRMWARE: missing BLE characteristics. Upload audited TyreLabExpanded.ino and power-cycle the board.')
     initial=environment(await asyncio.wait_for(client.read_gatt_char(ENV),5))
     if initial['model_id']!=self.model_id:raise RuntimeError('MODEL_MISMATCH: Arduino model and laptop package differ. Use matching files from the audited ZIP.')
     with self.lock:
      self.request=(self.request+1)%65536;self.ack=None;self.last_motion=None;self.last_scores=None;self.last_env=None;self.last_window=None;self.last_window_time=None;self.history.clear();self.pred={'condition':[0]*4,'road':[0]*4,'quality':0};self.verified=True
     def callback(fn):
      def call(_,data):
       with self.lock:
        if self.connection_epoch!=epoch:return
       try:
        fn(data)
        with self.lock:self.packet_error=None
       except Exception as exc:
        with self.lock:self.packet_error='PACKET_ERROR: '+str(exc)
      return call
     await client.start_notify(SCORES,callback(self.consume_scores));await client.start_notify(ENV,callback(self.consume_environment));await client.start_notify(MOTION,callback(self.consume_motion))
     with self.lock:self.connection='Connected';self.error=None
     sent=None;sent_at=0;retries=0;last_probe=time.monotonic()
     while client.is_connected and not self.stop.is_set():
      with self.lock:req=self.request;settings=dict(self.settings);ack=self.ack;last=self.last_motion
      if sent!=req or (ack!=req and time.monotonic()-sent_at>3):
       if sent==req:
        # Recover a lost notification by reading the board's current ACK before retransmitting.
        self.consume_scores(await asyncio.wait_for(client.read_gatt_char(SCORES),3))
        with self.lock:ack=self.ack
       if sent!=req or ack!=req:
        if sent!=req:retries=0
        retries+=1
        if retries>3:raise RuntimeError('CONTROL_TIMEOUT: board did not acknowledge settings. Restart it and reconnect.')
        await asyncio.wait_for(client.write_gatt_char(CONTROL,command(settings,req),response=True),5);sent=req;sent_at=time.monotonic()
      if time.monotonic()-last_probe>4:
       self.consume_scores(await asyncio.wait_for(client.read_gatt_char(SCORES),3))
       self.consume_environment(await asyncio.wait_for(client.read_gatt_char(ENV),3))
       last_probe=time.monotonic()
       with self.lock:last=self.last_motion;ack=self.ack
       if ack==req and (last is None or time.monotonic()-last>8):raise RuntimeError('NO_DATA: connected, but board motion notifications stopped. Reconnecting automatically; check board power/firmware.')
      await asyncio.sleep(.1)
     if not self.stop.is_set():raise RuntimeError('DISCONNECTED: board connection lost. Check power and distance. Retrying automatically.')
   except asyncio.CancelledError:raise
   except Exception as exc:
    logging.exception('BLE worker')
    with self.lock:
     self.connection='Retrying';self.error=str(exc) or 'BLE operation timed out. Restart board and check Bluetooth.';self.verified=False;self.ack=None;self.last_motion=None;self.last_scores=None;self.connection_epoch+=1
    if getattr(scanner,'process',None) is not None and scanner.process.poll() is not None:raise
    for _ in range(20):
     if self.stop.is_set():return
     await asyncio.sleep(.1)
 def close(self):self.fp.close()
class Handler(BaseHTTPRequestHandler):
 engine=None
 def log_message(self,*args):pass
 def send(self,data,status=200,kind='application/json'):
  payload=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(payload)));self.end_headers()
  try:self.wfile.write(payload)
  except (BrokenPipeError,ConnectionResetError):pass
 def do_GET(self):
  try:
   p=self.path.split('?',1)[0]
   if p=='/api/health':return self.send({'ok':True,'app':'TyreLab audited','protocol_version':2,'package_id':hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16]})
   if p=='/api/state':return self.send(self.engine.snapshot())
   if p=='/api/log':
    with self.engine.lock:self.engine.fp.flush();data=self.engine.log_path.read_bytes()
    return self.send(data,kind='text/csv')
   files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css'),'/entra-logo.png':('entra-logo.png','image/png')}
   if p not in files:return self.send({'error':'Not found'},404)
   name,kind=files[p];return self.send((ROOT/'static'/name).read_bytes(),kind=kind)
  except Exception as exc:self.send({'error':str(exc)},500)
 def do_POST(self):
  try:
   origin=self.headers.get('Origin','')
   if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:return self.send({'error':'Only the local dashboard may control the board.'},403)
   n=int(self.headers.get('Content-Length',0))
   if not 0<n<2048:raise ValueError('Invalid request size')
   body=json.loads(self.rfile.read(n))
   if self.path=='/api/control':return self.send({'settings':self.engine.configure(body)})
   if self.path=='/api/label':
    if not isinstance(body,dict):raise ValueError('Expected label object.')
    with self.engine.lock:
     if self.engine.settings['mode']!=0:raise ValueError('Labels are for physical mode only.')
     truth=body.get('truth');run=str(body.get('run_id','')).strip()
     if truth not in ['unlabelled']+CONDITIONS or len(run)>80 or (truth!='unlabelled' and not run):raise ValueError('Choose a condition and enter a run ID.')
     self.engine.truth=truth;self.engine.run_id=run or 'unlabelled'
    return self.send({'ok':True})
   return self.send({'error':'Not found'},404)
  except (ValueError,TypeError) as exc:self.send({'error':str(exc)},400)
  except Exception as exc:self.send({'error':str(exc)},500)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
 engine=None;server=None;thread=None;server_thread=None;url_file=ROOT/'dashboard_url.txt'
 try:
  engine=Engine();logging.basicConfig(filename=ROOT/'logs/diagnostics.log',level=logging.INFO)
  ports=[args.port] if args.port is not None else list(range(8000,8010))
  if any(not 1<=p<=65535 for p in ports):raise ValueError('Port must be 1–65535.')
  Handler.engine=engine
  for port in ports:
   try:server=ThreadingHTTPServer(('127.0.0.1',port),Handler);break
   except OSError as exc:
    if exc.errno not in (13,48,98,10048) and getattr(exc,'winerror',None) not in (10013,10048):raise
  if server is None:raise RuntimeError('PORT_BUSY: all chosen ports are occupied. Close older demo consoles.')
  # Serve before opening the browser; a failed BLE worker never stops HTTP.
  server_thread=threading.Thread(target=server.serve_forever,daemon=True);server_thread.start()
  url=f'http://127.0.0.1:{server.server_port}'
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  with opener.open(url+'/api/health',timeout=3) as response:
   if json.load(response).get('ok') is not True:raise RuntimeError('SERVER_HEALTH_FAILED: local server did not return its health response.')
  url_file.write_text(url,encoding='utf-8')
  print('SERVER READY: '+url+'\nKeep this console open. BOTH modes require the Arduino. Inference runs on the Nano.\nIf Opera reports a reset, open this exact URL in Edge/Chrome or run RUN_DIAGNOSTICS.bat.',flush=True)
  def run():
   while not engine.stop.is_set():
    try:asyncio.run(engine.worker())
    except Exception as exc:
     logging.exception('Isolated Bluetooth worker')
     print('BLE RECOVERY: '+str(exc)+' Website remains running; Bluetooth will retry.',flush=True)
     with engine.lock:engine.error=str(exc);engine.connection='Retrying';engine.verified=False;engine.ack=None;engine.last_motion=None;engine.last_scores=None
    engine.stop.wait(5)
  thread=threading.Thread(target=run,daemon=True);thread.start()
  if not args.no_browser:
   try:webbrowser.open(url)
   except Exception as exc:print('BROWSER_OPEN_FAILED:',exc,'Open the printed URL manually.',flush=True)
  while server_thread.is_alive():time.sleep(.25)
 except KeyboardInterrupt:pass
 except Exception as exc:print('STARTUP_ERROR:',exc,'\nExtract all files; run setup; inspect logs/diagnostics.log.');return 1
 finally:
  if engine:engine.stop.set()
  if server and server_thread:server.shutdown()
  if server:server.server_close()
  if thread:thread.join(timeout=20)
  if engine and (not thread or not thread.is_alive()):engine.close()
 return 0
if __name__=='__main__':sys.exit(main())
