"""Real launcher runtime setup and healthy-server discovery, no physical BLE."""
import importlib.util,json,os,subprocess,sys,tempfile,threading,shutil
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
ROOT=Path(__file__).resolve().parents[1]/'02_Friend_Demo'
spec=importlib.util.spec_from_file_location('launcher',ROOT/'launcher.py');launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
with tempfile.TemporaryDirectory(prefix='Tyre Lab test ') as td:
 root=Path(td)/'dashboard with spaces';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.venv','logs','__pycache__','dashboard_url.txt'))
 package_id=launcher.hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
 class Handler(BaseHTTPRequestHandler):
  correct=True
  def log_message(self,*args):pass
  def do_GET(self):
   data=json.dumps({'ok':True,'protocol_version':2,'package_id':package_id if self.correct else 'foreign'}).encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  url=f'http://127.0.0.1:{server.server_port}';(root/'dashboard_url.txt').write_text(url)
  assert launcher.healthy_url(root)==url
  Handler.correct=False;assert launcher.healthy_url(root) is None
  (root/'dashboard_url.txt').write_text('http://127.0.0.1:123@remote.invalid');assert launcher.healthy_url(root) is None
 finally:server.shutdown();server.server_close()
 python=launcher.ensure_runtime(root);assert launcher.runtime_ready(python)
 # Re-enter launcher from the virtual environment, as START_DEMO does on Windows.
 subprocess.run([str(python),'-m','pip','uninstall','-y','bleak'],check=True,stdout=subprocess.DEVNULL)
 probe="import importlib.util;from pathlib import Path;p=Path('launcher.py');s=importlib.util.spec_from_file_location('l',p);l=importlib.util.module_from_spec(s);s.loader.exec_module(l);assert l.runtime_ready(l.ensure_runtime(Path.cwd()))"
 subprocess.run([str(python),'-c',probe],cwd=root,check=True)
 # Start the real launcher and verify that a second invocation reuses its server.
 import time,signal
 (root/'dashboard_url.txt').unlink(missing_ok=True)
 env=dict(os.environ,BROWSER='/bin/true')
 process=subprocess.Popen([str(python),str(root/'launcher.py')],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 try:
  for _ in range(200):
   if (root/'dashboard_url.txt').exists():break
   if process.poll() is not None:raise AssertionError(process.stdout.read())
   time.sleep(.05)
  url=launcher.healthy_url(root);assert url
  second=subprocess.run([str(python),str(root/'launcher.py')],cwd=root,env=env,capture_output=True,text=True,timeout=10)
  assert second.returncode==0 and 'ALREADY RUNNING' in second.stdout,second.stdout+second.stderr
  with launcher.OPENER.open(url+'/api/state') as response:assert json.load(response)['connection']!='Connected'
 finally:
  process.send_signal(signal.SIGINT);process.wait(timeout=15)
print('Launcher: fresh environment setup, dependency repair from active venv, paths with spaces, healthy-server reuse and foreign/invalid URL rejection passed.')
