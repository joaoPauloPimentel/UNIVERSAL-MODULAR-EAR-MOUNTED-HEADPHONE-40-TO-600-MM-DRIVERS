import sys, os, json, numpy as np; sys.path.insert(0,'/home/user/UNIVERSAL-MODULAR-EAR-MOUNTED-HEADPHONE-40-TO-600-MM-DRIVERS/umeh3/calc')
import umeh3
from umeh3 import mass
from umeh2.massprops import read_stl
from scipy.spatial import cKDTree
def catmull(P, n=40):
    P=np.asarray(P,float); P=np.r_[[2*P[0]-P[1]],P,[2*P[-1]-P[-2]]]; out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1:i+3]
        t=lambda a,b,ti: ti+np.linalg.norm(b-a)**0.5
        t0=0;t1=t(p0,p1,t0);t2=t(p1,p2,t1);t3=t(p2,p3,t2)
        for tt in np.linspace(t1,t2,n,endpoint=False):
            A1=(t1-tt)/(t1-t0)*p0+(tt-t0)/(t1-t0)*p1; A2=(t2-tt)/(t2-t1)*p1+(tt-t1)/(t2-t1)*p2; A3=(t3-tt)/(t3-t2)*p2+(tt-t2)/(t3-t2)*p3
            B1=(t2-tt)/(t2-t0)*A1+(tt-t0)/(t2-t0)*A2; B2=(t3-tt)/(t3-t1)*A2+(tt-t1)/(t3-t1)*A3
            out.append((t2-tt)/(t2-t1)*B1+(tt-t1)/(t2-t1)*B2)
    out.append(P[-2]); return np.array(out)
def inside(tris, pts):
    d=np.array([0.577,0.5774,0.5771]); v0,v1,v2=tris[:,0],tris[:,1],tris[:,2]; e1=v1-v0; e2=v2-v0
    h=np.cross(d,e2); a=(e1*h).sum(1); ok=np.abs(a)>1e-12; f=np.where(ok,1/np.where(ok,a,1),0); res=[]
    for p in pts:
        s=p-v0; u=f*(s*h).sum(1); q=np.cross(s,e1); v=f*(q@d); t=f*(q*e2).sum(1)
        res.append(((u>=0)&(v>=0)&(u+v<=1)&(t>1e-9)&ok).sum()%2==1)
    return np.array(res)
band=json.load(open(sys.argv[1]))["_band"]; hw=band["hw"]; r=band["d"]/2
C=catmull(band["pts"])
# into right side frame: head (X,Y,Zb) -> side x=-Zb, y=Y, z=X-hw; only the right half
Cr=C[C[:,0]>=0]; S=np.c_[-Cr[:,2], Cr[:,1], Cr[:,0]-hw]
for p in sys.argv[2:]:
    T=(read_stl(os.path.join(mass.TMP,f"AF_D60_{p}.stl"))*1e3).reshape(-1,3,3)
    pts=np.r_[T.reshape(-1,3), T.mean(1)]; dist,_=cKDTree(pts).query(S)
    ins=inside(T,S); i=np.argmin(dist)
    print(f"{p:15s} min centreline-surface {dist.min():6.2f} mm (tube r {r}) at side {np.round(S[i],1)}  inside pts {ins.sum()}")
