#pragma once
#include <math.h>
#include <stdint.h>
namespace tyre {
const int N=256,F=22; const float FS=99.84f,TL_PI=3.14159265358979323846f;
struct Random {uint32_t s; Random(uint32_t seed):s(seed?seed:1){} uint32_t next(){s^=s<<13;s^=s>>17;s^=s<<5;return s;} float u(){return (next()>>8)*(1.0f/16777216.0f);} float between(float a,float b){return a+(b-a)*u();} float noise(){return (u()+u()+u()+u()+u()+u()-3)*1.41421356f;}};
// Assumptions, not empirical fits: the cited papers motivate harmonics and spectral features.
struct Simulator {
 Random rng;float rpm,severity,gain,phase,bias,rotAmp,amps[16],freqs[16],phases[16],jointPeriod,jointPhase,impactTime,impactAmp;int surface,issue;
 Simulator(uint32_t seed,int road,int fault,float amount,float speed,uint32_t rig=1):rng(seed),rpm(speed),severity(amount),surface(road),issue(fault){
  Random rr(rig);gain=rr.between(.75f,1.3f);bias=rr.between(-.04f,.04f);phase=rng.between(0,2*TL_PI);rotAmp=rng.between(.005f,.025f)*gain;
  float spectra[4][4]={{.030f,.014f,.006f,.003f},{.045f,.060f,.040f,.017f},{.025f,.012f,.005f,.003f},{.025f,.030f,.060f,.058f}};
  for(int k=0;k<16;k++){int band=k/4;float lo[4]={4,9,17,30},hi[4]={8,16,29,43};freqs[k]=rng.between(lo[band],hi[band]);phases[k]=rng.between(0,2*TL_PI);amps[k]=(road<4?spectra[road][band]:.002f)*gain*rng.between(.65f,1.35f);}
  jointPeriod=(3.6f/ (rpm/60*2.114f))*rng.between(.85f,1.15f);jointPhase=rng.between(0,jointPeriod);
  impactTime=rng.between(.25f,2.25f);impactAmp=gain*rng.between(.5f,1.5f)*severity/40;
 }
 void at(float t,float &x,float &y,float &z){
  float f=rpm/60,w=2*TL_PI*f*t+phase;float road=0;for(int k=0;k<16;k++)road+=amps[k]*sinf(2*TL_PI*freqs[k]*t+phases[k]);
  if(surface==2){float pos=fmodf(t+jointPhase,jointPeriod);road+=gain*.3f*expf(-pos*pos/(.014f*.014f));}
  if(surface==3 && rng.u()<.025f)road+=gain*rng.between(-.3f,.3f);
  y=cosf(w)+road+rng.noise()*.003f;z=bias+rotAmp*sinf(w)+road*.12f+rng.noise()*.004f*gain;
  float a=gain*(severity/50)*.16f*(f/2)*(f/2);
  if(issue==1)z+=a*sinf(w+.4f);
  if(issue==2)z+=a*(.25f*sinf(w)+sinf(2*w+.5f)+.6f*sinf(3*w+1));
  if(issue==3){float dt=t-impactTime;if(dt>=0){float pulse=impactAmp*expf(-dt*18)*cosf(2*TL_PI*18*dt);z+=pulse;y+=pulse*.4f;}}
  // Board X points approximately inward; DC centripetal acceleration is negative.
  x=-(rpm*2*TL_PI/60)*(rpm*2*TL_PI/60)*.22f/9.80665f+sinf(w)+road*.5f;
 }
};
inline float rms(const float *a,int n,float mean){float v=0;for(int i=0;i<n;i++){float d=a[i]-mean;v+=d*d;}return sqrtf(v/n);}
inline float amplitude(const float *a,const float *t,int n,float mean,float hz){float ss=0,cc=0;for(int i=0;i<n;i++){float w=2*TL_PI*hz*t[i];ss+=(a[i]-mean)*sinf(w);cc+=(a[i]-mean)*cosf(w);}return 2*sqrtf(ss*ss+cc*cc)/n;}
inline void features(const float *y,const float *z,const float *t,float f,float *out){
 float my=0,mz=0;for(int i=0;i<N;i++){my+=y[i];mz+=z[i];}my/=N;mz/=N;
 float ry=rms(y,N,my),rz=rms(z,N,mz),peak=0,kurt=0,diff=0;for(int i=0;i<N;i++){float d=z[i]-mz;peak=fmaxf(peak,fabsf(d));kurt+=d*d*d*d;if(i)diff+=(z[i]-z[i-1])*(z[i]-z[i-1]);}
 out[0]=logf(rz+1e-5f);out[1]=peak/(rz+1e-5f);out[2]=kurt/(N*powf(rz+1e-5f,4));out[3]=logf(sqrtf(diff/(N-1))+1e-5f);
 for(int j=0;j<3;j++)out[4+j]=logf(amplitude(z,t,N,mz,f*(j+1))+1e-5f);
 out[7]=f; // rotation is observed, never supplied fault/road labels
 // Remove 1x gravity component before road features, without passing selected surface.
 float ss=0,cc=0;for(int i=0;i<N;i++){ss+=(y[i]-my)*sinf(2*TL_PI*f*t[i]);cc+=(y[i]-my)*cosf(2*TL_PI*f*t[i]);}ss*=2.0f/N;cc*=2.0f/N;
 float residual[N],mr=0;for(int i=0;i<N;i++){residual[i]=y[i]-my-ss*sinf(2*TL_PI*f*t[i])-cc*cosf(2*TL_PI*f*t[i]);mr+=residual[i];}mr/=N;
 float rr=rms(residual,N,mr),pr=0,kr=0,dr=0;for(int i=0;i<N;i++){float d=residual[i]-mr;pr=fmaxf(pr,fabsf(d));kr+=d*d*d*d;if(i)dr+=(residual[i]-residual[i-1])*(residual[i]-residual[i-1]);}
 out[8]=logf(rr+1e-5f);out[9]=pr/(rr+1e-5f);out[10]=kr/(N*powf(rr+1e-5f,4));out[11]=logf(sqrtf(dr/(N-1))+1e-5f);
 // Coarse spectral grid to keep embedded workload small; broad-band statistical features.
 float bands[4]={0,0,0,0};for(int j=0;j<32;j++){float hz=4+j*1.25f,a=amplitude(residual,t,N,mr,hz);int b=hz<9?0:hz<17?1:hz<30?2:3;bands[b]+=a*a;}
 float total=bands[0]+bands[1]+bands[2]+bands[3]+1e-8f;for(int b=0;b<4;b++){out[12+b]=logf(bands[b]+1e-8f);out[16+b]=bands[b]/total;}
 out[20]=logf(amplitude(residual,t,N,mr,1.2f)+amplitude(residual,t,N,mr,1.8f)+amplitude(residual,t,N,mr,2.5f)+1e-5f);out[21]=logf(ry+1e-5f);
}
}
