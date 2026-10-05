"""UI-only mock telemetry. Never included in the friend application runtime."""
import sys,time,threading,struct,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'02_Friend_Demo'))
from app import Engine,Handler,ROOT
from http.server import ThreadingHTTPServer
import tempfile
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'model_manifest.json').write_bytes((ROOT/'model_manifest.json').read_bytes());e=Engine(p);Handler.engine=e
 def stream():
  seq=0
  while not e.stop.is_set():
   with e.lock:
    mode=e.settings['mode'];road=e.settings['surface'];issue=e.settings['issue'];e.connection='Connected';cs=[500]*4;cs[issue]=8500;rs=[500]*4;rs[road]=8500
    if not mode:rs=[0]*4
    e.consume_scores(struct.pack('<8HBBH',*cs,*rs,1,mode,e.request));e.consume_environment(struct.pack('<IhHHBBHHI',93500,2700,4800,e.request,mode,2,int(time.time()/2.56)%65536,0,e.model_id))
    seq+=1;t=time.time();e.consume_motion(struct.pack('<IhhhhHHBBH',int(t*1000)%4294967296,-3540,int(1000*math.cos(t*12)),int(150*math.sin(t*12)),7200,e.request,1200,1,mode,seq%65536))
   time.sleep(.04)
 threading.Thread(target=stream,daemon=True).start();s=ThreadingHTTPServer(('127.0.0.1',8004),Handler)
 try:s.serve_forever()
 finally:e.stop.set();s.server_close();e.close()
