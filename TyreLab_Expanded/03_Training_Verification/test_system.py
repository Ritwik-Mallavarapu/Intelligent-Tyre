import asyncio,json,struct,subprocess,sys,tempfile,time,threading,urllib.request,urllib.error,csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DEMO=ROOT/'02_Friend_Demo';HERE=Path(__file__).parent;sys.path.insert(0,str(DEMO))
from protocol import *
from app import Engine,Handler
from http.server import ThreadingHTTPServer
models=json.loads((HERE/'models.json').read_text());a=np.loadtxt(HERE/'synthetic_features.csv',delimiter=',');report=json.loads((HERE/'training_report.json').read_text())
subprocess.run([sys.executable,str(HERE/'check_firmware.py')],check=True)
with tempfile.TemporaryDirectory() as td:
 exe=Path(td)/'model_check';subprocess.run(['g++','-O2','-std=c++11',str(HERE/'model_check.cpp'),'-o',str(exe)],check=True)
 subset=a[a[:,0]>=170];out=subprocess.run([str(exe)],input='\n'.join(' '.join(map(str,row)) for row in subset[:,5:]),text=True,capture_output=True,check=True)
 actual=np.loadtxt(out.stdout.splitlines());expected=[]
 for name in ['condition','road']:
  m=models[name];x=(subset[:,5:][:,m['columns']]-m['mean'])/m['scale'];h=np.maximum(x@np.array(m['w1'])+m['b1'],0);o=h@np.array(m['w2'])+m['b2'];o-=o.max(1,keepdims=True);p=np.exp(o);p/=p.sum(1,keepdims=True);expected.append(p)
 expected=np.hstack(expected);error=np.max(abs(actual-expected));assert error<1e-5,error;print('All 1800 test windows: compiled C++ / exported Python weights agree; max error',error)
 for road in range(4):
  for fault in range(4):
   o=np.array(list(map(float,subprocess.check_output([str(exe),str(road),str(fault),'50','120'],text=True).split())));assert o.shape==(30,) and np.isfinite(o).all();assert o[22:26].argmax()==fault,(road,fault,o[22:26]);assert o[26:].argmax()==road or decision(o[26:],report['models']['road']['threshold']) is None,(road,fault,o[26:])
   if fault:
    zero=np.array(list(map(float,subprocess.check_output([str(exe),str(road),str(fault),'0','120'],text=True).split())));assert zero[22:26].argmax()==0,'Selecting a fault at zero severity must not force it'
 print('All 16 default surface/fault combinations and zero-severity non-forced predictions passed')
 # Recompute deployed condition success with the actual firmware novelty guard.
 m=models['condition'];novel=np.max(abs((subset[:,5:][:,m['columns']]-m['mean'])/m['scale']),axis=1)>7
 chosen=np.array([-1 if novel[i] else (decision(row,report['models']['condition']['threshold']) if decision(row,report['models']['condition']['threshold']) is not None else -1) for i,row in enumerate(actual[:,:4])]);success=(chosen==subset[:,2]).mean();print('Exact deployed condition success including novelty:',success)
 report['models']['condition']['decision_success_uncertain_counts_wrong']=float(success);report['models']['condition']['novelty_rejections']=int(novel.sum())
 (HERE/'training_report.json').write_text(json.dumps(report,indent=2));manifest=json.loads((DEMO/'model_manifest.json').read_text());manifest['report']=report;(DEMO/'model_manifest.json').write_text(json.dumps(manifest,indent=2))
# Packet and engine boundaries.
def sp(engine,mode=1,q=1,c=(8000,1000,500,500),r=(1000,8000,500,500),req=None):return struct.pack('<8HBBH',*c,*r,q,mode,engine.request if req is None else req)
def mp(mode=1,q=1,seq=1,req=1):return struct.pack('<IhhhhHHBBH',1000,-3540,400,120,7200,req,1200,q,mode,seq)
def ep(engine,match=True):return struct.pack('<IhHHBBHHI',93500,2700,4800,engine.request,engine.settings['mode'],2,1,0,engine.model_id if match else engine.model_id+1)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'model_manifest.json').write_bytes((DEMO/'model_manifest.json').read_bytes());e=Engine(root);e.request=1;e.connection='Connected';e.consume_scores(sp(e));e.consume_environment(ep(e));e.consume_motion(mp());s=e.snapshot();assert s['condition_label']=='Normal' and s['road_label']=='Rough asphalt';assert abs(sum(s['condition_scores'])-1)<1e-5
 e.configure({'mode':0});e.consume_scores(sp(e,req=(e.request-1)%65536));assert not e.snapshot()['ack'];e.consume_scores(sp(e,mode=0,r=(0,0,0,0)));e.consume_environment(ep(e));e.consume_motion(mp(mode=0,seq=2,req=e.request));s=e.snapshot();assert 'unavailable' in s['road_label'] and s['road_scores']==[0]*4
 e.consume_scores(sp(e,mode=0,q=4,c=(0,0,0,0),r=(0,0,0,0)));e.consume_motion(mp(mode=0,q=4,seq=3,req=e.request));assert e.snapshot()['condition_label']=='Sensor clipped'
 e.consume_scores(sp(e,mode=0,c=(4000,3000,2000,1000),r=(0,0,0,0)));e.consume_motion(mp(mode=0,seq=4,req=e.request));assert e.snapshot()['condition_label']=='Uncertain'
 e.consume_environment(ep(e,False));assert not any(e.snapshot()['condition_scores']);e.consume_environment(ep(e));e.last_motion=time.monotonic()-3;assert e.snapshot()['condition_label']=='Data stale' and not e.snapshot()['history'];e.last_motion=time.monotonic();e.last_scores=time.monotonic()-6;assert not any(e.snapshot()['condition_scores'])
 for body in [{'rpm':77},{'mode':2},{'severity':float('nan')},{'issue':5},{'seed':0},{'mode':True}]:
  try:e.configure(body);raise AssertionError('Invalid settings accepted')
  except ValueError:pass
 Handler.engine=e;server=ThreadingHTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start();base=f'http://127.0.0.1:{server.server_port}'
 for route in ['/','/app.js','/style.css','/api/state','/api/log']:
  with urllib.request.urlopen(base+route) as r:assert r.status==200 and r.read()
 request=urllib.request.Request(base+'/api/control',data=json.dumps({'mode':1,'issue':2}).encode(),headers={'Content-Type':'application/json'},method='POST');assert json.load(urllib.request.urlopen(request))['settings']['issue']==2
 request=urllib.request.Request(base+'/api/control',data=b'{"mode":0}',headers={'Origin':'https://example.org'},method='POST')
 try:urllib.request.urlopen(request);raise AssertionError('Foreign origin accepted')
 except urllib.error.HTTPError as err:assert err.code==403
 server.shutdown();server.server_close();t.join();e.close()
 print('Packet units, ack/source guards, clipping, uncertainty, mismatch, stale data, settings validation, HTTP/static/CSV and origin checks passed')
# Exercise the actual BLE worker with a mocked adapter, not a substitute backend.
class Device:name='TyreLabExpanded';address='mock'
class Advertisement:local_name='TyreLabExpanded';service_uuids=[SERVICE]
class Scanner:
 @staticmethod
 async def discover(**kwargs):return {'mock':(Device(),Advertisement())}
class Services:
 def get_characteristic(self,u):return object() if u in [MOTION,ENV,SCORES,CONTROL] else None
class Client:
 engine=None;writes=[]
 def __init__(self,*args,**kwargs):self.services=Services();self.is_connected=True;self.callbacks={}
 async def __aenter__(self):return self
 async def __aexit__(self,*args):self.is_connected=False
 async def start_notify(self,u,fn):self.callbacks[u]=fn
 async def read_gatt_char(self,u):return ep(self.engine) if u==ENV else sp(self.engine,mode=self.engine.settings['mode'],r=(1000,8000,500,500) if self.engine.settings['mode'] else (0,0,0,0))
 async def write_gatt_char(self,u,data,response):
  assert u==CONTROL and len(data)==14 and response;v,mode,road,fault,severity,rpm,seed,req=struct.unpack('<BBBBHHIH',data);self.writes.append((mode,road,fault,severity,rpm,seed,req));self.callbacks[SCORES](None,sp(self.engine,mode=mode,req=req,r=(1000,8000,500,500) if mode else (0,0,0,0)));self.callbacks[ENV](None,ep(self.engine));self.callbacks[MOTION](None,mp(mode=mode,seq=len(self.writes),req=req))
async def mock_test():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);(root/'model_manifest.json').write_bytes((DEMO/'model_manifest.json').read_bytes());e=Engine(root);Client.engine=e;task=asyncio.create_task(e.worker(Scanner,Client));await asyncio.sleep(.25);assert e.snapshot()['ack'] and e.snapshot()['verified'];e.configure({'mode':0});await asyncio.sleep(.25);assert Client.writes[-1][0]==0 and 'unavailable' in e.snapshot()['road_label'];e.configure({'mode':1,'issue':3,'surface':3,'severity':80});await asyncio.sleep(.25);assert Client.writes[-1][1:4]==(3,3,80) and e.snapshot()['ack'];e.stop.set();await task;e.close()
asyncio.run(mock_test());print('Actual BLE worker: handshake, acknowledged settings and live/synthetic switch passed using mocked adapter')
print('ALL SOFTWARE CHECKS PASSED. Physical sensors/BLE/real classification require hardware checks.')
