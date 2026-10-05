"""Exercise real RPC child and native-crash containment with a fake BLE backend."""
import asyncio,importlib.util,shutil,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'02_Friend_Demo'
FAKE='''import asyncio,os
from types import SimpleNamespace as S
class BleakScanner:
 @staticmethod
 async def discover(**kwargs):return {'x':(S(address='F2:B5:E2:01:CE:EC',name='TyreLabExpanded'),S(local_name='TyreLabExpanded',service_uuids=[]))}
class BleakClient:
 def __init__(self,device,**kwargs):self.is_connected=False;self.services=[S(characteristics=[S(uuid='motion')])];self.callbacks={}
 async def connect(self):self.is_connected=True
 async def disconnect(self):self.is_connected=False
 async def read_gatt_char(self,uuid):
  if uuid=='crash':os._exit(77)
  return bytes.fromhex('01020304')
 async def write_gatt_char(self,uuid,data,response=True):
  for callback in self.callbacks.values():callback(None,data)
 async def start_notify(self,uuid,callback):self.callbacks[uuid]=callback
'''
async def checks(module):
 transport=module.Transport()
 try:
  found=await transport.discover();device=list(found.values())[0][0];assert device.address=='F2:B5:E2:01:CE:EC'
  async with transport.client(device) as client:
   assert client.is_connected and client.services.get_characteristic('motion') and client.services.get_characteristic('absent') is None
   assert await client.read_gatt_char('motion')==bytes([1,2,3,4])
   values=[];await client.start_notify('motion',lambda _,p:values.append(p));await client.write_gatt_char('control',bytes(range(20)))
   assert values==[bytes(range(20))]
   try:await client.read_gatt_char('crash');raise AssertionError('Crash not propagated')
   except RuntimeError as exc:assert 'BLUETOOTH_PROCESS_EXIT' in str(exc)
   assert not client.is_connected
 finally:await transport.close()
 replacement=module.Transport()
 try:assert len(await replacement.discover())==1
 finally:await replacement.close()
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 for name in ['ble_transport.py','protocol.py']:shutil.copyfile(ROOT/name,root/name)
 (root/'bleak.py').write_text(FAKE)
 spec=importlib.util.spec_from_file_location('transport_test',root/'ble_transport.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 asyncio.run(checks(module))
print('Real BLE RPC subprocess: discovery, connection/services, exact byte read/write/notify, abrupt worker crash propagation, process cleanup and replacement passed; fake radio only.')
