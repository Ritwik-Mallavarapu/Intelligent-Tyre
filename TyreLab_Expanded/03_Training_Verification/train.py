from pathlib import Path
import json,subprocess,hashlib,warnings
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,confusion_matrix,classification_report
warnings.filterwarnings('ignore',category=UserWarning)
ROOT=Path(__file__).resolve().parents[1];ARD=ROOT/'01_Arduino_Upload/TyreLabExpanded';HERE=Path(__file__).parent
subprocess.run(['g++','-O2','-std=c++11',str(HERE/'generate.cpp'),'-o',str(HERE/'generate')],check=True)
with (HERE/'synthetic_features.csv').open('w') as fp:subprocess.run([str(HERE/'generate'),'200'],stdout=fp,check=True)
a=np.loadtxt(HERE/'synthetic_features.csv',delimiter=',');x=a[:,5:];group=a[:,0];train=group<140;val=(group>=140)&(group<170);test=group>=170
export={};report={'data_origin':'Entirely synthetic. Research guides mechanisms/features; no measured author dataset is used.','split':'Rig groups 0-139 train; 140-169 validation; 170-199 untouched test. No window from a test rig appears in train.','windows':len(a),'sample_rate_hz':99.84,'samples_per_window':256,'road_labels':['Smooth asphalt','Rough asphalt','Concrete','Gravel'],'condition_labels':['Normal','Imbalance-like periodic vibration','Other periodic abnormality','Impact'],'models':{}}
# Condition uses only axial features and observed speed, deliberately avoiding surface identifiers.
for name,labels,cols,eligible in [('condition',a[:,2].astype(int),list(range(8)),np.ones(len(a),dtype=bool)),('road',a[:,1].astype(int),list(range(7,22)),a[:,1]<4)]:
 tr=train&eligible;va=val&eligible;te=test&eligible;sc=StandardScaler().fit(x[tr][:,cols]);net=MLPClassifier(hidden_layer_sizes=(16,),activation='relu',solver='adam',max_iter=650,random_state=23,early_stopping=False,alpha=.02).fit(sc.transform(x[tr][:,cols]),labels[tr]);
 pv=net.predict_proba(sc.transform(x[va][:,cols]));pt=net.predict_proba(sc.transform(x[te][:,cols]));
 # Select conservative rejection threshold on validation only; no tuning to test.
 threshold=.65
 for th in [.65,.7,.75,.8]:
  accepted=(pv.max(1)>=th)&(np.sort(pv,axis=1)[:,-1]-np.sort(pv,axis=1)[:,-2]>=.15)
  if accepted.mean()>=.65 and (pv.argmax(1)[accepted]==labels[va][accepted]).mean()>=.93:threshold=th;break
 pred=pt.argmax(1);accepted=(pt.max(1)>=threshold)&(np.sort(pt,axis=1)[:,-1]-np.sort(pt,axis=1)[:,-2]>=.15)
 export[name]={'columns':cols,'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'w1':net.coefs_[0].tolist(),'b1':net.intercepts_[0].tolist(),'w2':net.coefs_[1].tolist(),'b2':net.intercepts_[1].tolist(),'threshold':threshold,'feature_min':x[tr][:,cols].min(0).tolist(),'feature_max':x[tr][:,cols].max(0).tolist()}
 report['models'][name]={'test_windows':int(te.sum()),'binary_or_multiclass_accuracy':float(accuracy_score(labels[te],pred)),'accepted_accuracy':float((pred[accepted]==labels[te][accepted]).mean()),'coverage':float(accepted.mean()),'decision_success_uncertain_counts_wrong':float(((pred==labels[te])&accepted).mean()),'threshold':threshold,'confusion_matrix':confusion_matrix(labels[te],pred).tolist(),'class_report':classification_report(labels[te],pred,output_dict=True)}
 print(name,report['models'][name],flush=True)
canonical=json.dumps(export,sort_keys=True,separators=(',',':'));model_id=int(hashlib.sha256(canonical.encode()).hexdigest()[:8],16);export['model_id']=model_id
(ROOT/'02_Friend_Demo/model_manifest.json').write_text(json.dumps({'model_id':model_id,'report':report},indent=2));(HERE/'models.json').write_text(json.dumps(export));(HERE/'training_report.json').write_text(json.dumps(report,indent=2))
def arr(v):
 if isinstance(v,list):return '{'+','.join(arr(e) for e in v)+'}'
 return f'{float(v):.9e}f'
s='#pragma once\n#include <math.h>\n#include <stdint.h>\nnamespace tyre {\nconst uint32_t MODEL_ID='+str(model_id)+'u;\n'
for name in ['condition','road']:
 m=export[name];p=name.upper();d=len(m['columns']);s+=f'const int {p}_D={d};\nconst int {p}_COLS[{d}]={{'+','.join(map(str,m['columns']))+'};\n'
 for key,dim in [('mean',f'[{d}]'),('scale',f'[{d}]'),('w1',f'[{d}][16]'),('b1','[16]'),('w2','[16][4]'),('b2','[4]')]:s+=f'const float {p}_{key.upper()}{dim}='+arr(m[key])+';\n'
 s+=f'const float {p}_THRESHOLD={m["threshold"]}f;\ninline void infer_{name}(const float *features,float *scores){{float h[16];for(int j=0;j<16;j++){{float v={p}_B1[j];for(int i=0;i<{d};i++)v+=(features[{p}_COLS[i]]-{p}_MEAN[i])/{p}_SCALE[i]*{p}_W1[i][j];h[j]=fmaxf(v,0);}}float maxv=-1e30f;for(int k=0;k<4;k++){{float v={p}_B2[k];for(int j=0;j<16;j++)v+=h[j]*{p}_W2[j][k];scores[k]=v;maxv=fmaxf(v,maxv);}}float sum=0;for(int k=0;k<4;k++){{scores[k]=expf(scores[k]-maxv);sum+=scores[k];}}for(int k=0;k<4;k++)scores[k]/=sum;}}\n'
s+='}\n';(ARD/'model.h').write_text(s)
