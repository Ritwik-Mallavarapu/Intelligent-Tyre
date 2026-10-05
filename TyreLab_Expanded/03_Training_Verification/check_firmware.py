"""Host syntax/contract check. NOT an Arduino-core compile or hardware check."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SKETCH=ROOT/'01_Arduino_Upload/TyreLabExpanded'
STUBS={
'Arduino.h':r'''#pragma once
#include <stdint.h>
#include <cmath>
using std::isfinite;
enum {B1=1,B10=2,B11=3};
#define PI 3.14159265358979323846
const int LED_BUILTIN=13,OUTPUT=1,HIGH=1,LOW=0;
inline void pinMode(int,int){} inline void digitalWrite(int,int){} inline int digitalRead(int){return 0;}
inline uint32_t millis(){return 0;}inline uint32_t micros(){return 0;}inline void delay(int){}
struct SerialStub{void begin(int){}operator bool(){return true;}template<typename T>void print(T){}template<typename T>void println(T){}};
extern SerialStub Serial;
''',
'Wire.h':r'''#pragma once
#include <Arduino.h>
struct WireStub{void begin(){}void beginTransmission(uint8_t){}void write(uint8_t){}int endTransmission(bool=true){return 0;}uint8_t requestFrom(uint8_t,uint8_t n){return n;}int read(){return 0;}};
extern WireStub Wire1;
''',
'Arduino_BMI270_BMM150.h':r'''#pragma once
struct IMUStub{int begin(){return 1;}int gyroscopeAvailable(){return 1;}int accelerationAvailable(){return 1;}int readGyroscope(float&,float&,float&){return 1;}int readAcceleration(float&,float&,float&){return 1;}};
extern IMUStub IMU;
''',
'ArduinoBLE.h':r'''#pragma once
#include <Arduino.h>
const int BLERead=2,BLENotify=16,BLEWrite=8;
struct BLECharacteristic{BLECharacteristic(const char*,uint16_t,int,bool=false){}int writeValue(const uint8_t*,int){return 1;} int valueLength(){return 14;} int readValue(uint8_t*,int n){return n;} bool written(){return false;}};
struct BLEService{BLEService(const char*){}void addCharacteristic(BLECharacteristic&){} };
struct BLEStub{int begin(){return 1;}void poll(){}void setLocalName(const char*){}void setAdvertisedService(BLEService&){}void addService(BLEService&){}void advertise(){}bool connected(){return false;}};
extern BLEStub BLE;
'''}
with tempfile.TemporaryDirectory() as td:
    temp=Path(td)
    for name,text in STUBS.items():(temp/name).write_text(text)
    subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-include',str(temp/'Arduino.h'),'-I',str(temp),'-x','c++','-fsyntax-only',str(SKETCH/'TyreLabExpanded.ino')],check=True)
print('Firmware host syntax/Arduino symbol-collision check passed. Full Arduino core compile and hardware test remain required.')
