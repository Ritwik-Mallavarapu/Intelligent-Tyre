#include <ArduinoBLE.h>
#include <Arduino_BMI270_BMM150.h>
#include <Wire.h>
#include "signal_core.h"
#include "model.h"
const char* SERVICE="8c220001-89ab-4cde-9012-34567890abcd";
BLEService service(SERVICE);
BLECharacteristic motion("8c220002-89ab-4cde-9012-34567890abcd",BLERead|BLENotify,20,true);
BLECharacteristic environment("8c220003-89ab-4cde-9012-34567890abcd",BLERead|BLENotify,20,true);
BLECharacteristic scoresChar("8c220004-89ab-4cde-9012-34567890abcd",BLERead|BLENotify,20,true);
BLECharacteristic control("8c220005-89ab-4cde-9012-34567890abcd",BLEWrite,14,true);
float ySamples[tyre::N],zSamples[tyre::N],times[tyre::N],rotationSamples[tyre::N],conditionScores[4]={0},roadScores[4]={0};
float ax=0,ay=0,az=0,gx=0,gy=0,gz=0;
int sampleCount=0;uint16_t packetSequence=0,windowSequence=0,requestId=0;
const uint8_t PROTOCOL_VERSION=2;
uint8_t quality=0,mode=0,surface=0,issue=0;float amount=50,rpmSetting=120;
uint32_t simSeed=20261005,simWindow=0,windowStart=0,lastSample=0,lastMotion=0,lastEnvironment=0,nextSim=0;
uint16_t startupFaults=0,runtimeFaults=0;bool imuOK=false,rangeOK=false,baroOK=false,hsOK=false,windowClip=false,windowTiming=false,windowMount=false;
uint32_t pressurePa=0;int16_t temperatureCenti=-32768;uint16_t humidityCenti=65535;
uint32_t lastGyro=0;
bool gyroFresh=false;
uint8_t baroAddress=0x5c;bool hsPending=false;uint32_t hsRequested=0,hsLast=0;
tyre::Simulator simulator(simSeed,0,0,50,120);
bool writeRegister(uint8_t address,uint8_t reg,uint8_t value){
  Wire1.beginTransmission(address);Wire1.write(reg);Wire1.write(value);return Wire1.endTransmission()==0;
}
bool readRegisters(uint8_t address,uint8_t reg,uint8_t* data,int n){
  Wire1.beginTransmission(address);Wire1.write(reg);
  if(Wire1.endTransmission(false)!=0)return false;
  if(Wire1.requestFrom(address,(uint8_t)n)!=(uint8_t)n)return false;
  for(int i=0;i<n;i++)data[i]=(uint8_t)Wire1.read();return true;
}
bool configureRange(){
  uint8_t v=0;if(!writeRegister(0x68,0x41,3))return false;delay(5);
  return readRegisters(0x68,0x41,&v,1)&&(v&3)==3;
}
bool startHS(){Wire1.beginTransmission(0x44);return Wire1.endTransmission()==0;}
void initializeEnvironment(){
  uint8_t id=0;
  if(!(readRegisters(0x5c,0x0f,&id,1)&&id==0xb1)){
    baroAddress=0x5d;id=0;
  }
  baroOK=readRegisters(baroAddress,0x0f,&id,1)&&id==0xb1;
  // LPS22HB: continuous1Hz, BDU on; register auto-increment on.
  if(baroOK)baroOK=writeRegister(baroAddress,0x11,0x10)&&writeRegister(baroAddress,0x10,0x12);
  if(!baroOK)startupFaults|=4;
  hsOK=startHS();if(!hsOK)startupFaults|=8;
  if(hsOK){hsPending=true;hsRequested=millis();}
}
void pollEnvironment(){
  uint32_t now=millis();
  // Split HS3003 request/read so its conversion does NOT block IMU sampling.
  if(hsOK && hsPending && (uint32_t)(now-hsRequested)>=50){
    hsPending=false;
    uint8_t b[4];bool ok=Wire1.requestFrom((uint8_t)0x44,(uint8_t)4)==4;
    if(ok)for(int i=0;i<4;i++)b[i]=(uint8_t)Wire1.read();
    if(ok && (b[0]>>6)==0){
      uint16_t rh=((uint16_t)(b[0]&0x3f)<<8)|b[1];
      uint16_t rt=(((uint16_t)b[2]<<8)|b[3])>>2;
      float temp=rt*165.0f/16383.0f-40.0f,humidity=rh*100.0f/16383.0f;
      if(isfinite(temp)&&temp>=-40&&temp<=125){temperatureCenti=(int16_t)roundf(temp*100);humidityCenti=(uint16_t)roundf(humidity*100);runtimeFaults&=~32;}
      else{temperatureCenti=-32768;humidityCenti=65535;runtimeFaults|=32;}
    }else{temperatureCenti=-32768;humidityCenti=65535;runtimeFaults|=32;}
    hsLast=now;
  }
  if(hsOK&&!hsPending&&(uint32_t)(now-hsLast)>=1000){
    hsPending=startHS();hsRequested=now;if(!hsPending){runtimeFaults|=32;hsLast=now;temperatureCenti=-32768;humidityCenti=65535;}
  }
  if((uint32_t)(now-lastEnvironment)<1000)return;lastEnvironment=now;
  if(baroOK){
    uint8_t b[3];if(readRegisters(baroAddress,0x28,b,3)){
      uint32_t raw=(uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16);
      float pa=raw*(100.0f/4096.0f);
      if(pa>=26000&&pa<=126000){pressurePa=(uint32_t)roundf(pa);runtimeFaults&=~16;}else{pressurePa=0;runtimeFaults|=16;}
    }else{pressurePa=0;runtimeFaults|=16;}
  }
}
void put16(uint8_t* p,uint16_t value){p[0]=value&255;p[1]=value>>8;}
void put32(uint8_t* p,uint32_t value){for(int i=0;i<4;i++)p[i]=(value>>(8*i))&255;}
void emitEnvironment(){
 uint8_t p[20];float t=millis()*.001f;
 put32(p,mode?93500+(uint32_t)(25*(1+sinf(t*.05f))):pressurePa);
 put16(p+4,mode?2700+(int16_t)(20*sinf(t*.05f)):(uint16_t)temperatureCenti);
 put16(p+6,mode?4800:(uint16_t)humidityCenti);
 put16(p+8,requestId);p[10]=mode;p[11]=PROTOCOL_VERSION;
 put16(p+12,windowSequence);put16(p+14,startupFaults|runtimeFaults);put32(p+16,tyre::MODEL_ID);environment.writeValue(p,20);
}
void emitScores(){uint8_t p[20];for(int i=0;i<4;i++){put16(p+2*i,(uint16_t)roundf(conditionScores[i]*10000));put16(p+8+2*i,(uint16_t)roundf(roadScores[i]*10000));}p[16]=quality;p[17]=mode;put16(p+18,requestId);scoresChar.writeValue(p,20);}
int16_t encodeSigned(float value,float scale){
 if(!isfinite(value))return -32768;
 return (int16_t)roundf(fmaxf(-32767,fminf(32767,value*scale)));
}
void emitMotion(){uint8_t p[20];put32(p,millis());put16(p+4,(uint16_t)encodeSigned(ax,1000));put16(p+6,(uint16_t)encodeSigned(ay,1000));put16(p+8,(uint16_t)encodeSigned(az,1000));put16(p+10,(uint16_t)encodeSigned(gz,10));put16(p+12,requestId);put16(p+14,isfinite(gz)?(uint16_t)roundf(fminf(65535,fabsf(gz)/6*10)):65535);p[16]=quality;p[17]=mode;put16(p+18,packetSequence++);motion.writeValue(p,20);}
void resetWindow(){sampleCount=0;quality=0;lastSample=0;gyroFresh=false;ax=ay=az=gx=gy=gz=NAN;for(int i=0;i<4;i++){conditionScores[i]=0;roadScores[i]=0;}}
uint16_t get16(const uint8_t* p){return p[0]|((uint16_t)p[1]<<8);}
void applyControl(){
 uint8_t p[14];if(control.valueLength()!=14||control.readValue(p,14)!=14)return;
 uint16_t a=get16(p+4),r=get16(p+6);if(p[0]!=1||p[1]>1||p[2]>3||p[3]>3||a>100||r<78||r>162)return;
 uint32_t seed=0;for(int i=0;i<4;i++)seed|=(uint32_t)p[8+i]<<(8*i);
 if(seed==0)return;
 uint16_t incoming=get16(p+12);
 // Retransmission of an identical command acknowledges it without restarting a window.
 if(incoming==requestId && mode==p[1] && surface==p[2] && issue==p[3] && amount==a && rpmSetting==r && simSeed==seed){emitScores();emitEnvironment();return;}
 mode=p[1];surface=p[2];issue=p[3];amount=a;rpmSetting=r;simSeed=seed;requestId=incoming;simWindow=0;
 resetWindow();simulator=tyre::Simulator(simSeed,surface,issue,amount,rpmSetting,simSeed^0x34abcd);nextSim=micros();emitScores();emitEnvironment();emitMotion();
}
void finishWindow(){
 windowSequence++;float f=0;for(int i=0;i<tyre::N;i++)f+=rotationSamples[i];f/=tyre::N;float variance=0;for(int i=0;i<tyre::N;i++)variance+=(rotationSamples[i]-f)*(rotationSamples[i]-f);float cv=sqrtf(variance/tyre::N)/fmaxf(f,.001f);
 if(windowClip)quality=4;else if(windowTiming)quality=5;else if(windowMount)quality=6;else if(f<1.3f)quality=2;else if(f>2.7f)quality=3;else if(cv>.10f)quality=9;else {
  float features[tyre::F];tyre::features(ySamples,zSamples,times,f,features);bool valid=true;for(int i=0;i<tyre::F;i++)if(!isfinite(features[i]))valid=false;
  if(valid){tyre::infer_condition(features,conditionScores);if(mode)tyre::infer_road(features,roadScores);quality=1;
   // Reject clearly unfamiliar axial feature vectors. This is a heuristic, not a calibrated OOD guarantee.
   for(int i=0;i<tyre::CONDITION_D;i++)if(fabsf((features[tyre::CONDITION_COLS[i]]-tyre::CONDITION_MEAN[i])/tyre::CONDITION_SCALE[i])>7)quality=8;
  }else quality=8;
 }
 if(quality!=1){for(int i=0;i<4;i++){conditionScores[i]=0;roadScores[i]=0;}}
 emitScores();emitEnvironment();sampleCount=0;
 if(mode){simWindow++;simulator=tyre::Simulator(simSeed+simWindow*7919,surface,issue,amount,rpmSetting,simSeed^0x34abcd);nextSim=micros()+10016;}
}
void collect(uint32_t now){
 if(!sampleCount){windowStart=now;windowClip=false;windowTiming=false;windowMount=false;}
 if(lastSample&&sampleCount>0){uint32_t dt=now-lastSample;if(!mode && (dt<6000||dt>18000))windowTiming=true;}lastSample=now;
 if(fabsf(ax)>15.5f||fabsf(ay)>15.5f||fabsf(az)>15.5f||fabsf(gz)>1950||fabsf(gx)>1950||fabsf(gy)>1950)windowClip=true;
 float totalGyro=sqrtf(gx*gx+gy*gy+gz*gz);
 if(!mode && totalGyro>200 && fabsf(gz)<.9f*totalGyro)windowMount=true;
 ySamples[sampleCount]=ay;zSamples[sampleCount]=az;times[sampleCount]=mode?sampleCount/tyre::FS:(uint32_t)(now-windowStart)*1e-6f;
 rotationSamples[sampleCount]=fabsf(gz)/360;sampleCount++;if(sampleCount%4==0)emitMotion();if(sampleCount==tyre::N)finishWindow();
}
void setup(){
 pinMode(LED_BUILTIN,OUTPUT);Serial.begin(115200);
 if(!BLE.begin()){if(Serial)Serial.println("BLE_INIT failed. Restart board/check ArduinoBLE.");while(true){digitalWrite(LED_BUILTIN,!digitalRead(LED_BUILTIN));delay(200);}}
 BLE.setLocalName("TyreLabExpanded");BLE.setAdvertisedService(service);service.addCharacteristic(motion);service.addCharacteristic(environment);service.addCharacteristic(scoresChar);service.addCharacteristic(control);BLE.addService(service);
 Wire1.begin();imuOK=IMU.begin();if(!imuOK)startupFaults|=1;
 if(imuOK){rangeOK=configureRange();if(!rangeOK)startupFaults|=2;}initializeEnvironment();
 emitEnvironment();emitScores();emitMotion();BLE.advertise();if(Serial)Serial.println("TyreLabExpanded ready. Website controls Live or onboard Simulation.");
}
void loop(){
 BLE.poll();if(control.written())applyControl();pollEnvironment();
 static uint32_t envSent=0;if((uint32_t)(millis()-envSent)>=1000){envSent=millis();emitEnvironment();emitScores();}
 if(mode){uint32_t now=micros();if((int32_t)(now-nextSim)<0)return;nextSim=now+10016;simulator.at(sampleCount/tyre::FS,ax,ay,az);gx=gy=0;gz=rpmSetting*6;collect(now);}
 else {
  if(!imuOK||!rangeOK){quality=7;if((uint32_t)(millis()-lastMotion)>=200){lastMotion=millis();emitMotion();emitScores();}return;}
  if(IMU.gyroscopeAvailable()){
   gyroFresh=IMU.readGyroscope(gx,gy,gz) && isfinite(gx) && isfinite(gy) && isfinite(gz);
   if(gyroFresh)lastGyro=micros();
  }
  if(!IMU.accelerationAvailable())return;
  bool accelerationOK=IMU.readAcceleration(ax,ay,az) && isfinite(ax) && isfinite(ay) && isfinite(az);
  if(!accelerationOK || !gyroFresh || (uint32_t)(micros()-lastGyro)>50000){
   resetWindow();quality=10;emitMotion();emitScores();return;
  }
  ax*=4;ay*=4;az*=4;collect(micros());
 }
 digitalWrite(LED_BUILTIN,BLE.connected()?HIGH:LOW);
}
