import sys,json,importlib,os
from pathlib import Path
root=Path(__file__).parent
try:
 if sys.version_info[:2] not in [(3,11),(3,12)]:raise RuntimeError('Use Python 3.11 or 3.12.')
 if '--dashboard-only' not in sys.argv:importlib.import_module('bleak')
 json.loads((root/'model_manifest.json').read_text())
 for f in ['app.py','protocol.py','ble_transport.py','static/index.html','static/app.js','static/style.css']:
  if not (root/f).is_file():raise RuntimeError('Missing '+f+'. Extract the whole friend folder.')
 (root/'logs').mkdir(exist_ok=True);p=root/'logs/write_check.tmp';p.write_text('ok');p.unlink()
 print('Installation checked. Start START_DEMO.bat. Both modes need the Arduino.')
except Exception as exc:print('INSTALLATION_ERROR:',exc);sys.exit(1)
