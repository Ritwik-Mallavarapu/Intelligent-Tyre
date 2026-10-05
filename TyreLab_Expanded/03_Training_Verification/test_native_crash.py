"""Verify real HTTP server survives an abruptly terminated BLE child process."""
import json,subprocess,sys,tempfile,shutil,time,urllib.request,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'02_Friend_Demo'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/'demo';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.venv','logs','__pycache__','dashboard_url.txt'))
 (root/'bleak.py').write_text('import os\nclass BleakScanner:\n @staticmethod\n async def discover(**kwargs):os._exit(77)\nclass BleakClient:pass\n')
 process=subprocess.Popen([sys.executable,str(root/'app.py'),'--no-browser'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 try:
  for _ in range(100):
   if (root/'dashboard_url.txt').exists():break
   if process.poll() is not None:raise AssertionError(process.stdout.read())
   time.sleep(.05)
  url=(root/'dashboard_url.txt').read_text()
  for _ in range(100):
   with opener.open(url+'/api/state',timeout=2) as response:state=json.load(response)
   if any('BLUETOOTH_PROCESS_EXIT' in message for message in state['issues']):break
   time.sleep(.05)
  assert any('BLUETOOTH_PROCESS_EXIT' in message for message in state['issues']),state
  for _ in range(10):
   with opener.open(url+'/api/health',timeout=2) as response:assert json.load(response)['ok']
   assert process.poll() is None
   time.sleep(.1)
  assert not state['verified'] and not state['ack'] and not any(state['condition_scores'])
  assert 'BLE operation: scan' in (root/'logs/bluetooth_worker.log').read_text()
 finally:process.send_signal(signal.SIGINT);process.wait(timeout=20)
print('Actual HTTP server survives abrupt BLE subprocess exit, reports failure, suppresses predictions and saves the failed operation. Passed with injected crash, no physical radio.')
