#include <iostream>
#include "../01_Arduino_Upload/TyreLabExpanded/signal_core.h"
int main(int argc,char**argv){int groups=argc>1?atoi(argv[1]):160;std::cout.precision(9);for(int g=0;g<groups;g++)for(int road=0;road<5;road++)for(int issue=0;issue<4;issue++)for(int rep=0;rep<3;rep++){
 uint32_t seed=123+g*109091+road*3701+issue*101+rep*17;tyre::Random rng(seed);float severity=issue?rng.between(30,90):0,rpm=rng.between(78,162);
 tyre::Simulator sim(seed,road,issue,severity,rpm,g*137+789);float y[tyre::N],z[tyre::N],t[tyre::N],x,out[tyre::F];for(int i=0;i<tyre::N;i++){t[i]=i/tyre::FS;sim.at(t[i],x,y[i],z[i]);}tyre::features(y,z,t,rpm/60,out);
 std::cout<<g<<","<<road<<","<<issue<<","<<severity<<","<<rpm;for(float v:out)std::cout<<","<<v;std::cout<<"\n";
}}
