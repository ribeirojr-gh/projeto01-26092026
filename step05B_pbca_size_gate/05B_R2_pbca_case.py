#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
import numpy as np
from ase.constraints import FixAtoms
from ase.dft.kpoints import mindistance2monkhorstpack
from ase.io import read,write
from ase.optimize import BFGS
from gpaw import GPAW,PW,setup_paths
from gpaw.mpi import world
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step05B_R2 import *

def req(n):
    v=os.environ.get(n,"")
    if not v: raise RuntimeError(f"Variável obrigatória ausente: {n}")
    return v

mineral=req("UPB_PBCA_HOST"); nreq=int(req("UPB_PBCA_NATOMS"))
if mineral not in SUPERCELLS or nreq not in SUPERCELLS[mineral]: raise ValueError("Caso inválido")
for d in (RESULTS,LOGS,RELAX): d.mkdir(parents=True,exist_ok=True)
structure=SUPERCELLS[mineral][nreq]
if not structure.exists(): raise FileNotFoundError(structure)

for s in ("Ca","C","O"):
    if not (HOST_PAW_DIR/f"{s}.PBEsol").exists(): raise FileNotFoundError(HOST_PAW_DIR/f"{s}.PBEsol")
if mineral=="dolomita" and not (HOST_PAW_DIR/"Mg.PBEsol").exists(): raise FileNotFoundError(HOST_PAW_DIR/"Mg.PBEsol")
if not (PB_PAW_DIR/"Pb.PBEsol").exists(): raise FileNotFoundError(PB_PAW_DIR/"Pb.PBEsol")
setup_paths.insert(0,str(HOST_PAW_DIR.resolve())); setup_paths.insert(0,str(PB_PAW_DIR.resolve()))
host=read(structure)
tag=f"{mineral}_{nreq}"

def gamma_calc(txt):
    return GPAW(mode=PW(ECUT_EV,dedecut="estimate"),xc=XC,kpts={"size":(1,1,1),"gamma":True},
      nbands=NBANDS,occupations={"name":"fermi-dirac","width":SMEARING_EV},random=False,
      parallel={"domain":world.size,"band":1,"kpt":1,"sl_auto":True},
      convergence={"energy":1e-3,"density":1e-5,"eigenstates":1e-7,"bands":"occupied"},
      eigensolver={"name":"dav","niter":4},txt=str(txt))

def dense_calc(txt,k):
    return GPAW(mode=PW(ECUT_EV,dedecut="estimate"),xc=XC,kpts={"size":tuple(k),"gamma":True},
      nbands=NBANDS,occupations={"name":"fermi-dirac","width":SMEARING_EV},random=False,
      parallel={"sl_auto":True},
      convergence={"energy":1e-3,"density":1e-5,"eigenstates":1e-7,"bands":"occupied"},
      eigensolver={"name":"dav","niter":4},txt=str(txt))

host.calc=gamma_calc(LOGS/f"{tag}_host_gamma.txt")
ehost=host.get_potential_energy(); fhost=host.get_forces()

scaled=host.get_scaled_positions(wrap=True); cell=np.asarray(host.cell)
ca=[i for i,s in enumerate(host.get_chemical_symbols()) if s=="Ca"]
scores=[]
for i in ca:
    ds=scaled[i]-0.5; ds-=np.round(ds); scores.append((float(np.linalg.norm(ds@cell)),i))
scores.sort(); center_dist,pbidx=scores[0]

initial=host.copy(); initial[pbidx].symbol="Pb"
defect=initial.copy(); defect.calc=gamma_calc(LOGS/f"{tag}_PbCa_gamma.txt")
eun=defect.get_potential_energy()

dist=defect.get_distances(pbidx,np.arange(len(defect)),mic=True)
fixed=[i for i,d in enumerate(dist) if d>LOCAL_RELAX_RADIUS_A and i!=pbidx]
defect.set_constraint(FixAtoms(indices=fixed))
op1=BFGS(defect,logfile=str(LOGS/f"{tag}_local_gamma.log"),trajectory=str(RELAX/f"{tag}_local_gamma.traj"),maxstep=0.15)
ok1=bool(op1.run(fmax=LOCAL_FMAX_EV_A,steps=MAX_LOCAL_STEPS))
defect.set_constraint()
op2=BFGS(defect,logfile=str(LOGS/f"{tag}_full_gamma.log"),trajectory=str(RELAX/f"{tag}_full_gamma.traj"),maxstep=0.12)
ok2=bool(op2.run(fmax=FINAL_FMAX_EV_A,steps=MAX_FINAL_STEPS))

edef=defect.get_potential_energy(); fdef=defect.get_forces()
oids=[i for i,s in enumerate(defect.get_chemical_symbols()) if s=="O"]
pbo6=sorted(float(defect.get_distance(pbidx,i,mic=True)) for i in oids)[:6]

dense=None
if nreq==80:
    k=tuple(int(x) for x in mindistance2monkhorstpack(host,min_distance=KPT_CALIBRATION_MIN_DISTANCE_A,maxperdim=8,even=False))
    hd=read(structure); hd.calc=dense_calc(LOGS/f"{tag}_host_dense80.txt",k); ehd=hd.get_potential_energy()
    dd=defect.copy(); dd.calc=dense_calc(LOGS/f"{tag}_PbCa_dense80.txt",k); edd=dd.get_potential_energy()
    rawg=float(edef-ehost); rawd=float(edd-ehd)
    dense={"kmesh":list(k),"Nk_reducible":int(np.prod(k)),"raw_substitution_energy_eV":rawd,
           "gamma_to_dense_raw_delta_eV":abs(rawd-rawg)}

write(RELAX/f"{tag}_PbCa_relaxed_R2.traj",defect)
write(RELAX/f"{tag}_PbCa_relaxed_R2.cif",defect)

rec={"status":"converged" if ok2 else "not_fully_converged","step":"05B-R2-PbCa","mineral":mineral,"natoms":len(defect),
 "defect":"Pb2+_on_Ca2+","charge_state":0,"ecut_eV":ECUT_EV,"nbands":NBANDS,
 "pb_atom_index":int(pbidx),"selected_Ca_distance_from_fractional_center_A":float(center_dist),
 "energy_host_gamma_eV":float(ehost),"energy_defect_unrelaxed_gamma_eV":float(eun),"energy_defect_relaxed_gamma_eV":float(edef),
 "raw_substitution_energy_gamma_eV":float(edef-ehost),"relaxation_energy_gamma_eV":float(edef-eun),
 "local_stage_converged":ok1,"full_stage_converged":ok2,
 "host_max_force_gamma_eV_A":float(np.max(np.linalg.norm(fhost,axis=1))),
 "defect_max_force_gamma_eV_A":float(np.max(np.linalg.norm(fdef,axis=1))),
 "PbO_first6_A":pbo6,"PbO6_mean_A":float(np.mean(pbo6)),"PbO6_std_A":float(np.std(pbo6)),
 "dense80_calibration":dense,"relaxed_traj":str(RELAX/f"{tag}_PbCa_relaxed_R2.traj")}
world.barrier()
if world.rank==0:
    (RESULTS/f"{tag}_PbCa.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(rec,indent=2,ensure_ascii=False))
world.barrier()
