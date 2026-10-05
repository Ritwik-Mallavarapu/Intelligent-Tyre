"""Protocol v2: all telemetry is tagged with active settings and source."""
import struct
SERVICE='8c220001-89ab-4cde-9012-34567890abcd'
MOTION='8c220002-89ab-4cde-9012-34567890abcd'
ENV='8c220003-89ab-4cde-9012-34567890abcd'
SCORES='8c220004-89ab-4cde-9012-34567890abcd'
CONTROL='8c220005-89ab-4cde-9012-34567890abcd'
PROTOCOL_VERSION=2
ROADS=['Smooth asphalt','Rough asphalt','Concrete','Gravel']
CONDITIONS=['Normal','Imbalance-like periodic vibration','Other periodic abnormality','Impact']
QUALITY={0:'Warming up',1:'Valid window',2:'Too slow',3:'Too fast',4:'Sensor clipped',5:'Sampling irregular',6:'Check mounting',7:'IMU unavailable',8:'Unfamiliar signal',9:'Speed unstable',10:'Motion sensor data unavailable'}
FAULTS={1:'Motion sensor initialization failed',2:'16 g range setup failed',4:'Pressure sensor initialization failed',8:'Temperature/humidity initialization failed',16:'Pressure reading failed',32:'Temperature/humidity reading failed',64:'In-plane acceleration clipped'}
def check(data):
 if len(data)!=20:raise ValueError('Invalid BLE packet length. Upload matching audited firmware.')
def signed(v,scale):return None if v==-32768 else v/scale
def motion(data):
 check(data);ms,ax,ay,az,gz,request,rpm,q,mode,seq=struct.unpack('<IhhhhHHBBH',data)
 if mode>1 or q not in QUALITY:raise ValueError('Unknown telemetry protocol. Upload audited firmware.')
 return dict(device_ms=ms,ax=signed(ax,1000),ay=signed(ay,1000),az=signed(az,1000),gz=signed(gz,10),rpm=None if rpm==65535 else rpm/10,quality=q,mode=mode,seq=seq,request=request)
def environment(data):
 check(data);pa,temp,rh,request,mode,version,window,faults,model=struct.unpack('<IhHHBBHHI',data)
 if version!=PROTOCOL_VERSION or mode>1:raise ValueError('OLD_FIRMWARE: expected protocol v2. Upload TyreLabExpanded.ino from the audited ZIP, then restart the board.')
 if pa and not 26000<=pa<=126000:raise ValueError('Pressure packet is outside the barometer range.')
 if temp!=-32768 and not -4000<=temp<=12500:raise ValueError('Temperature packet is outside sensor limits.')
 if rh!=65535 and rh>10000:raise ValueError('Humidity packet exceeds 100%.')
 return dict(pressure_psi=pa/6894.757293168 if pa else None,temperature_c=temp/100 if temp!=-32768 else None,humidity_pct=rh/100 if rh!=65535 else None,window=window,faults=faults,model_id=model,request=request,mode=mode,protocol_version=version)
def scores(data):
 check(data);*v,q,mode,request=struct.unpack('<8HBBH',data)
 if q not in QUALITY or mode>1 or any(a>10000 for a in v):raise ValueError('Invalid model-score packet.')
 for head in [v[:4],v[4:]]:
  if any(head) and abs(sum(head)-10000)>4:raise ValueError('Model scores do not sum to 100%.')
 if q!=1 and any(v):raise ValueError('Invalid-data window must not contain prediction scores.')
 if mode==0 and any(v[4:]):raise ValueError('Live airborne mode must not contain road predictions.')
 return dict(condition=[a/10000 for a in v[:4]],road=[a/10000 for a in v[4:]],quality=q,mode=mode,request=request)
def command(settings,request):
 return struct.pack('<BBBBHHIH',1,settings['mode'],settings['surface'],settings['issue'],settings['severity'],settings['rpm'],settings['seed'],request)
def decision(values,threshold):
 order=sorted(range(4),key=lambda i:values[i],reverse=True)
 return order[0] if sum(values)>.99 and values[order[0]]>=threshold and values[order[0]]-values[order[1]]>=.15 else None
