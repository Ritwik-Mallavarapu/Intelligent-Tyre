"""BLE RPC adapter. Native Bluetooth code runs in a disposable child process.
The parent dashboard imports no Bleak/WinRT modules through this adapter.
"""
import asyncio,json,os,subprocess,sys,threading
from pathlib import Path
from types import SimpleNamespace

class Transport:
 def __init__(self):
  self.loop=asyncio.get_running_loop();self.pending={};self.callbacks={};self.next_id=0;self.connected=False;self.closed=False
  root=Path(__file__).resolve().parent;(root/'logs').mkdir(exist_ok=True)
  self.log=(root/'logs/bluetooth_worker.log').open('a',encoding='utf-8')
  self.process=subprocess.Popen([sys.executable,'-u',str(root/'ble_transport.py'),'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8',env=dict(os.environ,PYTHONIOENCODING='utf-8'))
  self.reader=threading.Thread(target=self._read,daemon=True);self.reader.start()
 def _read(self):
  try:
   for line in self.process.stdout:
    try:event=json.loads(line)
    except ValueError:continue
    self.loop.call_soon_threadsafe(self._receive,event)
  finally:
   code=self.process.wait()
   try:self.loop.call_soon_threadsafe(self._failed,code)
   except RuntimeError:pass
 def _receive(self,event):
  if event.get('event')=='notification':
   callback=self.callbacks.get(event['uuid'])
   if callback:callback(None,bytes.fromhex(event['data']))
  elif event.get('event')=='disconnected':self.connected=False
  else:
   future=self.pending.pop(event.get('id'),None)
   if future and not future.done():
    if 'error' in event:future.set_exception(RuntimeError(event['error']))
    else:future.set_result(event.get('result'))
 def _failed(self,code):
  self.connected=False
  error=RuntimeError(f'BLUETOOTH_PROCESS_EXIT: {code} (0x{code & 0xffffffff:08X}). Website remains running. See logs/bluetooth_worker.log.')
  for future in self.pending.values():
   if not future.done():future.set_exception(error)
  self.pending.clear()
 async def rpc(self,operation,**args):
  if self.process.poll() is not None:raise RuntimeError('BLUETOOTH_PROCESS_EXIT: '+str(self.process.returncode)+'. See logs/bluetooth_worker.log.')
  self.next_id+=1;request_id=self.next_id;future=self.loop.create_future();self.pending[request_id]=future
  try:
   self.process.stdin.write(json.dumps({'id':request_id,'op':operation,**args})+'\n');self.process.stdin.flush()
   return await asyncio.wait_for(future,25)
  finally:self.pending.pop(request_id,None)
 async def discover(self,timeout=5,return_adv=True):
  rows=await self.rpc('scan',timeout=timeout)
  return {r['address']:(SimpleNamespace(address=r['address'],name=r['name']),SimpleNamespace(local_name=r['name'],service_uuids=r['services'])) for r in rows}
 def client(self,device,**kwargs):return Client(self,device)
 async def close(self):
  if self.closed:return
  self.closed=True;self.connected=False
  if self.process.poll() is None:
   self.process.terminate()
   await asyncio.to_thread(self.process.wait)
  self.reader.join(timeout=1);self.log.close()

class Client:
 def __init__(self,transport,device):self.transport=transport;self.device=device;self.services=None
 @property
 def is_connected(self):return self.transport.connected and self.transport.process.poll() is None
 async def __aenter__(self):
  uuids=await self.transport.rpc('connect',address=self.device.address)
  self.services=SimpleNamespace(get_characteristic=lambda uuid: uuid if uuid.lower() in uuids else None);self.transport.connected=True;return self
 async def __aexit__(self,*args):
  self.transport.connected=False
  if self.transport.process.poll() is None:
   try:await self.transport.rpc('disconnect')
   except Exception:pass
 async def read_gatt_char(self,uuid):return bytes.fromhex(await self.transport.rpc('read',uuid=uuid))
 async def write_gatt_char(self,uuid,data,response=True):await self.transport.rpc('write',uuid=uuid,data=bytes(data).hex(),response=response)
 async def start_notify(self,uuid,callback):
  self.transport.callbacks[uuid]=callback
  await self.transport.rpc('notify',uuid=uuid)

async def worker():
 # Run Windows WinRT on this process's main asyncio thread, not the HTTP worker thread.
 if sys.platform=='win32':
  sys.coinit_flags=0
  from bleak.backends.winrt.util import uninitialize_sta
  uninitialize_sta()
 from bleak import BleakScanner,BleakClient
 from protocol import SERVICE
 devices={};client=None
 def emit(data):print(json.dumps(data),flush=True)
 try:
  while True:
   line=await asyncio.to_thread(sys.stdin.readline)
   if not line:break
   request=json.loads(line);operation=request['op']
   print('BLE operation: '+operation,file=sys.stderr,flush=True)
   try:
    result=None
    if operation=='scan':
     found=await BleakScanner.discover(timeout=request['timeout'],return_adv=True);devices={d.address:d for d,a in found.values()}
     result=[{'address':d.address,'name':a.local_name or d.name or '', 'services':a.service_uuids} for d,a in found.values() if (a.local_name or d.name or '') in ('TyreLabExpanded','TyreLabRev2','TyreTinyML') or SERVICE in [u.lower() for u in a.service_uuids]]
    elif operation=='connect':
     device=devices.get(request['address'])
     if device is None:raise RuntimeError('Board not present in latest scan.')
     kwargs={'timeout':15,'disconnected_callback':lambda _:emit({'event':'disconnected'})}
     client=BleakClient(device,**kwargs);await client.connect();result=[c.uuid.lower() for service in client.services for c in service.characteristics]
    elif operation=='disconnect':
     if client:await client.disconnect()
     client=None
    elif operation=='read':result=bytes(await client.read_gatt_char(request['uuid'])).hex()
    elif operation=='write':await client.write_gatt_char(request['uuid'],bytes.fromhex(request['data']),response=request['response'])
    elif operation=='notify':
     uuid=request['uuid']
     await client.start_notify(uuid,lambda _,data,u=uuid:emit({'event':'notification','uuid':u,'data':bytes(data).hex()}))
    else:raise ValueError('Unknown Bluetooth operation.')
    emit({'id':request['id'],'result':result})
   except Exception as exc:
    print(type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True);emit({'id':request['id'],'error':str(exc) or type(exc).__name__})
 finally:
  if client and client.is_connected:await client.disconnect()
if __name__=='__main__':
 import faulthandler
 faulthandler.enable()
 asyncio.run(worker())
