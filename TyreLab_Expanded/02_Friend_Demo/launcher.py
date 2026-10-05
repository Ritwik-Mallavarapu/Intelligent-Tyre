"""Single entry point: verify runtime, reuse healthy server, or start it.
Only the server/Arduino perform their existing duties; this file runs no inference.
"""
import hashlib,json,os,subprocess,sys,time,urllib.request,urllib.parse,webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PACKAGE_ID=hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16]
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def healthy_url(root=ROOT):
 candidates=[]
 saved=root/'dashboard_url.txt'
 if saved.is_file():
  try:candidates.append(saved.read_text(encoding='utf-8').strip())
  except OSError:pass
 candidates.extend(f'http://127.0.0.1:{p}' for p in range(8000,8010))
 package_id=hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
 for url in dict.fromkeys(candidates):
  # Never follow an arbitrary URL from an edited runtime file.
  try:
   parts=urllib.parse.urlsplit(url)
   if parts.scheme!='http' or parts.hostname!='127.0.0.1' or not parts.port or parts.path or parts.query or parts.fragment or parts.username or parts.password:continue
  except ValueError:continue
  try:
   with OPENER.open(url+'/api/health',timeout=.3) as response:health=json.load(response)
   if health.get('ok') is True and health.get('protocol_version')==2 and health.get('package_id')==package_id:return url
  except (OSError,ValueError):pass
 return None

def runtime_python(root=ROOT):
 return root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def runtime_ready(python):
 if not python.is_file():return False
 code="import sys,bleak;from importlib.metadata import version;assert sys.version_info[:2] in [(3,11),(3,12)];assert version('bleak')=='0.22.3'"
 try:return subprocess.run([str(python),'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15).returncode==0
 except (OSError,subprocess.TimeoutExpired):return False

def ensure_runtime(root=ROOT):
 python=runtime_python(root)
 if runtime_ready(python):return python
 if sys.version_info[:2] not in [(3,11),(3,12)]:raise RuntimeError('Install Python 3.11 or 3.12 with the Python launcher, then run START_DEMO.bat again.')
 print('Preparing/repairing the Python environment. First setup needs internet.',flush=True)
 # Do not recreate a running Windows environment merely to repair dependencies.
 valid_python=False
 if python.is_file():
  try:valid_python=subprocess.run([str(python),'-c',"import sys;assert sys.version_info[:2] in [(3,11),(3,12)]"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15).returncode==0
  except (OSError,subprocess.TimeoutExpired):pass
 if not valid_python:
  base=getattr(sys,'_base_executable',sys.executable)
  subprocess.run([base,'-m','venv','--clear',str(root/'.venv')],check=True)
 subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(root/'requirements.txt')],check=True)
 if not runtime_ready(python):raise RuntimeError('Python/Bluetooth dependency check failed. Read the installation error above.')
 return python

def main():
 root=ROOT
 try:
  for name in ['app.py','protocol.py','ble_transport.py','requirements.txt','model_manifest.json','static/index.html','static/app.js','static/style.css']:
   if not (root/name).is_file():raise RuntimeError('Missing '+name+'. Extract the entire ZIP before starting.')
  url=healthy_url(root)
  if url:
   print('DASHBOARD ALREADY RUNNING: '+url,flush=True)
   try:webbrowser.open(url)
   except Exception:print('Open the URL above manually.',flush=True)
   return 0
  try:python=ensure_runtime(root)
  except (subprocess.CalledProcessError,RuntimeError,OSError) as exc:
   print('BLUETOOTH SETUP INCOMPLETE: '+str(exc)+'\nStarting the website anyway. Bluetooth errors will appear on the dashboard.',flush=True)
   python=Path(sys.executable)
  subprocess.run([str(python),str(root/'CHECK_INSTALLATION.py'),'--dashboard-only'],check=True)
  logs=root/'logs';logs.mkdir(exist_ok=True)
  with (logs/'startup.log').open('a',encoding='utf-8') as log:
   log.write('\nSTART '+time.strftime('%Y-%m-%d %H:%M:%S')+'\n');log.flush()
   print('Starting dashboard. KEEP THIS CONSOLE OPEN.',flush=True)
   child=subprocess.Popen([str(python),'-u',str(root/'app.py')],cwd=root,env=dict(os.environ,PYTHONIOENCODING='utf-8'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
   try:
    for line in child.stdout:
     print(line,end='',flush=True);log.write(line);log.flush()
    code=child.wait()
   except KeyboardInterrupt:
    child.terminate();child.wait(timeout=10);return 0
   if code:raise RuntimeError('Dashboard exited with code '+str(code)+'. See logs/startup.log.')
   return 0
 except Exception as exc:
  print('\nSTART FAILED: '+str(exc)+'\nDo not open port 8000 manually. Send this console message or logs/startup.log.',flush=True)
  return 1
if __name__=='__main__':sys.exit(main())
