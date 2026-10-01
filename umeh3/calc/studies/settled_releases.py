import sys, os, json, collections, numpy as np
sys.path.insert(0,'.')
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb
from umeh2 import support as sp
sad=json.loads(sys.argv[2]); S=dict(geom.VARIANTS["AF"]["SADDLE"]); S.update(sad); geom.apply("AF", SADDLE=S); v=json.loads(sys.argv[1])
mp=nb.with_band(loads.mass_props(60), v["neck"])
C,link,info=ct.contact_set(v); model=nb.ModelN(C,link)
W_st=loads.static_wrench(mp)
cs=list(loads.cases(mp,"treadmill",n_grav=1,n_cable=1))
sd=sp.shakedown(model,W_st,[w for _,w in cs],seq="A",n_cyc=8,pads=ct.PADS)
st=sd["state"]; Ws=model._pad(W_st); bad=[]; whys=[]
for tag,W in cs:
    ok1,st1,_=model._ramp(Ws,model._pad(W),st,True,60,model.N_STEPS)
    if not ok1: bad.append(tag); whys.append(_[:90]); continue
    ok2,st2,_=model._ramp(model._pad(W),Ws,st1,True,60,model.N_STEPS)
    if not ok2: bad.append(tag)
m=ct.metrics(model.solve(W_st) if False else None, C, info) if False else None
model.base=(Ws, st); r0=model.solve(W_st); print("sustained root", round(ct.metrics(r0,C,info)["root_p"]))
print(v, sad, "fail in settled cycle", len(bad), "/", len(cs))
for k in ("acc","axis","omega","cable","g"):
    print(k, collections.Counter(str(np.round(t[k],2).tolist()) if isinstance(t[k],list) else str(t[k]) for t in bad).most_common(8))

print(collections.Counter(w.split('(')[0] for w in whys)); print(whys[:4])
