import numpy as np, struct, zipfile, os
OUT="/root/asm/out"; DST="/root/asm/final"; os.makedirs(DST, exist_ok=True)
COL={"ring":"#4682B4","gasket_umi":"#32CD32","arm_saddle":"#FFA500","arm_temporal":"#FFA500","arm_mastoid":"#FFA500","arm_post":"#FFA500",
 "saddle_cap":"#696969","pad_temporal":"#696969","pad_mastoid":"#696969","pad_post":"#696969","cable_anchor":"#696969","cable_clip":"#505050",
 "saddle_liner":"#B22222","pad_face_temporal":"#B22222","pad_face_mastoid":"#B22222","baffle":"#F5DEB3","gasket_driver":"#303030",
 "driver_visual":"#2F2F2F","felt":"#F0E68C","cup":"#B0C4DE","cup_cap":"#A27449"}
def read(p):
    b=open(p,"rb").read()
    if b[:5]==b"solid" and b"facet" in b[:400]:
        v=[list(map(float,l.split()[1:4])) for l in b.decode().splitlines() if l.strip().startswith("vertex")]
        return np.array(v).reshape(-1,3,3)
    n=struct.unpack("<I",b[80:84])[0]
    a=np.frombuffer(b[84:84+50*n],dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]))
    return a["v"].reshape(-1,3,3).astype(float)
for D in (40,45,50,55,60):
    parts=[(p,read(f"{OUT}/{D}_{p}.stl")) for p in COL if os.path.exists(f"{OUT}/{D}_{p}.stl") and os.path.getsize(f"{OUT}/{D}_{p}.stl")>0]
    tri=np.concatenate([t for _,t in parts])
    with open(f"{DST}/UMEH-2_assembly_{D}mm_R.stl","wb") as f:
        f.write(b"UMEH-2 assembled right side, %d mm module".ljust(80,b" ") % D if False else (b"UMEH-2 assembled right side %d mm" % D).ljust(80,b" "))
        f.write(struct.pack("<I",len(tri)))
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); l=np.linalg.norm(n,axis=1,keepdims=True); l[l==0]=1; n/=l
        rec=np.zeros(len(tri),dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")])); rec["n"]=n; rec["v"]=tri.reshape(-1,9)
        f.write(rec.tobytes())
    # 3MF with one named, coloured object per part
    mats="".join(f'<base name="{p}" displaycolor="{COL[p]}"/>' for p,_ in parts)
    objs=[];items=[]
    for i,(p,t) in enumerate(parts):
        v,inv=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True); inv=inv.reshape(-1,3)
        vs="".join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a,b,c in v)
        ts="".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in inv if a!=b and b!=c and a!=c)
        objs.append(f'<object id="{i+2}" name="{p}" type="model" pid="1" pindex="{i}"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{i+2}"/>')
    model=('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
      f'<resources><basematerials id="1">{mats}</basematerials>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    with zipfile.ZipFile(f"{DST}/UMEH-2_assembly_{D}mm_R.3mf","w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model",model)
    print(D,len(parts),"parts",len(tri),"tris")
