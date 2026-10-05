"""Server startup/restart with occupied port and unavailable BLE; no hardware claim."""
import json,subprocess,socket,time,urllib.request,tempfile,shutil,sys,os,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'02_Friend_Demo'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/'demo';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('logs','__pycache__','.venv','dashboard_url.txt'))
 sys.path.insert(0,str(root));from app import Engine
 e=Engine(root);old=e.request;e.configure({'restart':True});assert e.request!=old and e.ack is None
 try:e.configure({'restart':1});raise AssertionError('Invalid restart accepted')
 except ValueError:pass
 e.close()
 occupied=socket.socket();occupied.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);occupied.bind(('127.0.0.1',8000));occupied.listen()
 try:
  for iteration in range(3):
   urlfile=root/'dashboard_url.txt';urlfile.unlink(missing_ok=True)
   launch=[sys.executable,str(root/'app.py'),'--no-browser']
   if iteration==2:
    code="import importlib.util;from pathlib import Path;s=importlib.util.spec_from_file_location('l','launcher.py');l=importlib.util.module_from_spec(s);s.loader.exec_module(l);l.ensure_runtime=lambda root: (_ for _ in ()).throw(RuntimeError('Injected dependency installation failure'));raise SystemExit(l.main())"
    launch=[sys.executable,'-c',code]
   process=subprocess.Popen(launch,cwd=root,env=dict(os.environ,BROWSER='/bin/true'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   try:
    for attempt in range(100):
     if urlfile.exists():break
     if process.poll() is not None:raise AssertionError(process.stdout.read())
     time.sleep(.05)
    assert urlfile.exists(),'Server did not start'
    url=urlfile.read_text();assert ':8000' not in url
    for _ in range(10):
     with opener.open(url+'/api/health',timeout=2) as response:assert json.load(response)['protocol_version']==2
     with opener.open(url+'/api/state',timeout=2) as response:state=json.load(response);assert not state['ack'] and not any(state['condition_scores'])
     time.sleep(.1)
   finally:process.send_signal(signal.SIGINT);process.wait(timeout=15)
 finally:occupied.close()
print('Three real server restarts, occupied-port fallback, health/state during absent BLE explicit simulation restart and launcher HTTP startup despite dependency installation failure passed.')
