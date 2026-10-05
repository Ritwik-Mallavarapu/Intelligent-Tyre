#include <iostream>
#include <cstdlib>
#include "../01_Arduino_Upload/TyreLabExpanded/signal_core.h"
#include "../01_Arduino_Upload/TyreLabExpanded/model.h"
enum { B1=1 }; // Old Arduino naming collision must stay harmless.
int main(int argc,char**argv){std::cout.precision(9);if(argc>1){int road=atoi(argv[1]),issue=atoi(argv[2]);float amount=atof(argv[3]),rpm=atof(argv[4]);uint32_t seed=argc>5?strtoul(argv[5],nullptr,10):20261005;tyre::Simulator sim(seed,road,issue,amount,rpm,seed^0x34abcd);float y[tyre::N],z[tyre::N],t[tyre::N],x,f[tyre::F],c[4],r[4];for(int i=0;i<tyre::N;i++){t[i]=i/tyre::FS;sim.at(t[i],x,y[i],z[i]);}tyre::features(y,z,t,rpm/60,f);tyre::infer_condition(f,c);tyre::infer_road(f,r);for(float a:f)std::cout<<a<<' ';for(float a:c)std::cout<<a<<' ';for(float a:r)std::cout<<a<<' ';std::cout<<'\n';return 0;}float f[tyre::F],c[4],r[4];while(std::cin>>f[0]){for(int i=1;i<tyre::F;i++)std::cin>>f[i];tyre::infer_condition(f,c);tyre::infer_road(f,r);for(float a:c)std::cout<<a<<' ';for(float a:r)std::cout<<a<<' ';std::cout<<'\n';}}
