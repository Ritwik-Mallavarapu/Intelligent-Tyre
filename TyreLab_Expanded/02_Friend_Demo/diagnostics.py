"""Read-only local server + BLE diagnostic. Does not change Windows settings or Arduino firmware."""
import asyncio,json,sys,platform,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
async def scan():
 try:
  from bleak import BleakScanner
  print('Scanning Bluetooth for 8 seconds. Keep the Nano powered and nearby.',flush=True)
  found=await BleakScanner.discover(timeout=8,return_adv=True);matched=[]
  for device,adv in found.values():
   name=adv.local_name or device.name or ''
   if name in ('TyreLabExpanded','TyreLabRev2','TyreTinyML'):
    matched.append(name);print('FOUND:',name,'| address:',device.address,'| RSSI:',adv.rssi)
  if 'TyreLabExpanded' in matched:print('Board advertisement found. Dashboard should connect; close other BLE apps and restart START_DEMO if it does not.')
  elif matched:print('OLD_FIRMWARE: upload audited TyreLabExpanded.ino. Earlier firmware names cannot stream to this dashboard.')
  else:print('NO_BOARD: board may be off, already connected to another app, too far away, or running different firmware. Reset it, close phone/nRF Connect apps, enable Bluetooth and scan again.')
 except Exception as exc:print('BLUETOOTH_ERROR:',str(exc) or type(exc).__name__,'\nEnable Bluetooth; run setup if modules are missing; restart Bluetooth/board.')
def main():
 print('Entra Intelligent Tyre diagnostics |',platform.system(),platform.release(),'| Python',sys.version.split()[0])
 url=(ROOT/'dashboard_url.txt').read_text().strip() if (ROOT/'dashboard_url.txt').is_file() else 'http://127.0.0.1:8000'
 if not url.startswith('http://127.0.0.1:'):print('Invalid dashboard URL file. Restart START_DEMO.bat.');return
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));state=None
 try:
  with opener.open(url+'/api/health',timeout=3) as r:health=json.load(r)
  print('SERVER_OK:',url,'| protocol',health.get('protocol_version'))
  with opener.open(url+'/api/state',timeout=3) as r:state=json.load(r)
  print('Bluetooth:',state['connection'],'| stream:',state['stream'],'| status:',state['status'])
  for issue in state.get('issues',[]):print('ISSUE:',issue)
  print('If Opera still shows ERR_CONNECTION_RESET, open the EXACT URL above in Edge/Chrome. The server responded directly; check browser proxy/VPN handling of localhost.')
 except Exception as exc:print('SERVER_UNREACHABLE:',str(exc),'\nRun START_DEMO.bat and KEEP ITS CONSOLE OPEN. Read startup errors. Close older demos, then use the URL printed by the current launcher.')
 if state and state.get('connection')=='Connected':print('Dashboard has the board connected. Skipping competing BLE scan. If data is stale, inspect the issue messages above.')
 else:asyncio.run(scan())
 print('If Bluetooth keeps restarting, send logs/bluetooth_worker.log and logs/diagnostics.log from this folder.')
 print('Copy this full diagnostic output if you need help. Diagnostic reads do not prove physical model accuracy.')
if __name__=='__main__':main()
