#!/usr/bin/env python3
import json,sys
from pathlib import Path
import numpy as np
from gpaw import GPAW,setup_paths
from gpaw.spinorbit import soc_eigenstates
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2C2 import *
setup_paths.insert(0,str(MATRIX_DIR.resolve())); setup_paths.insert(0,str(U_DIR.resolve()))
def gap(states):
    eig=np.asarray(states.eigenvalues(),float); ef=float(states.fermi_level)
    o=eig[eig<=ef]; u=eig[eig>ef]
    return None if o.size==0 or u.size==0 else float(max(0.0,np.min(u)-np.max(o)))
def ev(gpw,label,n2,scale):
    calc=GPAW(str(gpw)); st=soc_eigenstates(calc,n1=0,n2=n2,scale=scale)
    return {"label":label,"gpw":str(gpw),"n2":int(n2),"scale":float(scale),
            "indirect_gap_eV":gap(st),"fermi_level_eV":float(st.fermi_level),
            "band_energy_eV_cell":float(st.calculate_band_energy())}
g2=GPW/"gammaUO3_relaxed_1600_k222.gpw"; g3=GPW/"gammaUO3_relaxed_1600_k333.gpw"; gc=GPW/"gammaUO3_relaxed_1800_k222.gpw"
cases={}
for n2 in (160,192):
    for scale in (0.0,1.0):
        cases[f"central_n{n2}_scale{int(scale)}"]=ev(g2,"1600_k222",n2,scale)
for label,g in (("1600_k333",g3),("1800_k222",gc)):
    for scale in (0.0,1.0):
        cases[f"{label}_n192_scale{int(scale)}"]=ev(g,label,192,scale)
rec={"status":"completed","step":"04B2C2-final-SOC","system":"gamma-UO3-Fddd-relaxed",
     "method":"GPAW-25.7 soc_eigenstates non-self-consistent","cases":cases}
(RESULTS/"gammaUO3_relaxed_SOC_convergence.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(rec,indent=2,ensure_ascii=False))
