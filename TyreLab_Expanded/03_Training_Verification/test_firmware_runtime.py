"""Execute actual .ino control, generator, inference and serialization on a host. Mock hardware only."""
from pathlib import Path
import subprocess,tempfile,runpy,sys,json
HERE=Path(__file__).parent;ROOT=HERE.parent;SKETCH=ROOT/'01_Arduino_Upload/TyreLabExpanded'
# Use the syntax harness's API stubs; it also checks the full .ino before returning.
stubs=runpy.run_path(str(HERE/'check_firmware.py'))['STUBS']
stubs['Arduino.h']=stubs['Arduino.h'].replace('inline uint32_t millis(){return 0;}inline uint32_t micros(){return 0;}','extern uint32_t fakeTime;inline uint32_t millis(){return fakeTime/1000;}inline uint32_t micros(){return fakeTime;}')
stubs['ArduinoBLE.h']=stubs['ArduinoBLE.h'].replace('struct BLECharacteristic{','struct BLECharacteristic{uint8_t data[20]={0};int len=0;').replace('int writeValue(const uint8_t*,int){return 1;}','int writeValue(const uint8_t* p,int n){len=n;for(int i=0;i<n;i++)data[i]=p[i];return 1;}').replace('int readValue(uint8_t*,int n){return n;}','int readValue(uint8_t* p,int n){for(int i=0;i<n;i++)p[i]=data[i];return n;}')
with tempfile.TemporaryDirectory() as td:
 p=Path(td)
 for name,s in stubs.items():(p/name).write_text(s)
 source='''#include <cassert>
#include <iostream>
#include "Arduino.h"
#include "Wire.h"
#include "ArduinoBLE.h"
#include "Arduino_BMI270_BMM150.h"
uint32_t fakeTime=100000;SerialStub Serial;WireStub Wire1;BLEStub BLE;IMUStub IMU;
#include "'''+str(SKETCH/'TyreLabExpanded.ino')+'''"
void settings(uint8_t m,uint8_t road,uint8_t fault,uint16_t severity,uint16_t request){uint8_t p[14]={1,m,road,fault};put16(p+4,severity);put16(p+6,120);put32(p+8,20261005);put16(p+12,request);control.writeValue(p,14);applyControl();}
int main(){
 for(int road=0;road<4;road++)for(int fault=0;fault<4;fault++){
  settings(1,road,fault,50,1+road*4+fault);assert(mode==1&&sampleCount==0&&quality==0);assert(get16(scoresChar.data+18)==requestId);
  for(int i=0;i<tyre::N;i++){fakeTime+=10016;loop();}
  assert(quality==1);float sum=0;int top=0;for(int i=0;i<4;i++){sum+=conditionScores[i];if(conditionScores[i]>conditionScores[top])top=i;}assert(fabsf(sum-1)<.00001f&&top==fault);assert(scoresChar.len==20&&motion.len==20&&environment.len==20);
 }
 fakeTime+=10016;loop();assert(sampleCount>0);int oldCount=sampleCount;settings(1,3,3,50,16);assert(sampleCount==oldCount);
 settings(0,0,0,0,31);assert(mode==0&&quality==0);for(int i=0;i<4;i++)assert(roadScores[i]==0&&conditionScores[i]==0);
 for(int i=0;i<tyre::N;i++){rotationSamples[i]=0;ySamples[i]=zSamples[i]=0;times[i]=i/tyre::FS;}windowClip=windowTiming=windowMount=false;gx=gy=gz=0;finishWindow();assert(quality==2);for(int i=0;i<4;i++)assert(roadScores[i]==0);
 windowClip=true;finishWindow();assert(quality==4);windowClip=false;windowTiming=true;finishWindow();assert(quality==5);
 windowTiming=false;for(int i=0;i<tyre::N;i++)rotationSamples[i]=i%2?1.5f:2.5f;finishWindow();assert(quality==9);
 uint16_t saved=requestId;settings(2,0,0,0,99);assert(requestId==saved&&mode==0);
 std::cout<<"Actual firmware runtime: all 16 simulations, onboard predictions, settings ACK, live reset/road suppression, slow/clipped/irregular/unstable guards and invalid-control rejection passed.\\n";
}
'''
 (p/'run.cpp').write_text(source);subprocess.run(['g++','-O2','-std=c++11','-I',str(p),str(p/'run.cpp'),'-o',str(p/'run')],check=True);subprocess.run([str(p/'run')],check=True)
