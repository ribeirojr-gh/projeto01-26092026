#!/usr/bin/env python3
import json,sys
from pathlib import Path
import numpy as np, spglib
from ase.io import read
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2C2 import *
def pct(x,r): return abs(x-r)/abs(r)*100.0
def spg(a,p):
    ds=spglib.get_symmetry_dataset((np.asarray(a.cell),np.asarray(a.get_scaled_positions()),np.asarray(a.numbers)),symprec=p)
    return {"symprec_A":p,"number":int(ds.number),"international":str(ds.international),"hall":str(ds.hall)}
def prof(a):
    sy=a.get_chemical_symbols(); us=[i for i,s in enumerate(sy) if s=="U"]; os=[i for i,s in enumerate(sy) if s=="O"]
    arr=np.array([sorted(a.get_distance(u,o,mic=True) for o in os)[:6] for u in us],float)
    return {"mean_first6_A":np.mean(arr,axis=0).tolist(),"shortest_UO_A":float(arr.min()),"mean_UO6_A":float(arr.mean())}
exp=read(EXP_PRIM); rel=read(RELAX/"gamma_UO3_relaxed_scalar.traj")
ep=prof(exp); rp=prof(rel); ea=np.array(ep["mean_first6_A"]); ra=np.array(rp["mean_first6_A"])
rms=float(np.sqrt(np.mean((ra-ea)**2))/np.mean(ea)*100)
pmg=AseAtomsAdaptor.get_structure(rel); sga=SpacegroupAnalyzer(pmg,symprec=0.03,angle_tolerance=0.5)
conv=sga.get_conventional_standard_structure()
cl=sorted(float(x) for x in conv.lattice.abc); el=sorted([EXP_A_A,EXP_B_A,EXP_C_A])
le=[pct(c,e) for c,e in zip(cl,el)]; ve=pct(float(conv.volume),EXP_VOLUME_A3); se=pct(rp["shortest_UO_A"],EXP_SHORTEST_UO_A)
sym=[spg(rel,p) for p in (0.01,0.03,0.05)]
ok=max(le)<=MAX_LATTICE_ERROR_PERCENT and ve<=MAX_VOLUME_ERROR_PERCENT and se<=MAX_SHORTEST_UO_ERROR_PERCENT and rms<=MAX_UO6_RMS_REL_ERROR_PERCENT and any(x["number"]==EXP_SPACEGROUP for x in sym)
conv.to(filename=str(RELAX/"gamma_UO3_relaxed_scalar_conventional.cif"))
rec={"step":"04B2C2-structural-metrics","experimental_conventional_cell_A":[EXP_A_A,EXP_B_A,EXP_C_A],
 "relaxed_conventional_cell_A":[float(x) for x in conv.lattice.abc],"sorted_lattice_errors_percent":le,
 "experimental_volume_A3":EXP_VOLUME_A3,"relaxed_conventional_volume_A3":float(conv.volume),"volume_error_percent":float(ve),
 "experimental_UO6_profile":ep,"relaxed_UO6_profile":rp,"shortest_UO_error_percent":float(se),
 "UO6_mean_profile_RMS_relative_error_percent":rms,"symmetry":sym,"structural_gate_passes":bool(ok)}
(RESULTS/"structural_metrics_step04B2C2.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(rec,indent=2,ensure_ascii=False))
