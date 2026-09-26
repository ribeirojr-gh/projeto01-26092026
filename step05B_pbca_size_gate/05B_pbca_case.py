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
from config_step05B import *

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
if len(host)!=nreq: raise RuntimeError(f"N esperado {nreq}, obtido {len(host)}")
kmesh=tuple(int(x) for x in mindistance2monkhorstpack(host,min_distance=KPT_MIN_DISTANCE_A,maxperdim=8,even=False))
tag=f"{mineral}_{nreq}"

def calc(txt):
    return GPAW(mode=PW(ECUT_EV,dedecut="estimate"),xc=XC,
      kpts={"size":kmesh,"gamma":True},
      occupations={"name":"fermi-dirac","width":SMEARING_EV},
      random=False,
      convergence={"energy":1e-3,"density":1e-5,"eigenstates":1e-7,"bands":"occupied"},
      eigensolver={"name":"dav","niter":4},txt=str(txt))

host.calc=calc(LOGS/f"{tag}_host_gpaw.txt")
ehost=host.get_potential_energy(); fhost=host.get_forces()
hrec={"status":"converged","step":"05B-host","mineral":mineral,"natoms":len(host),
 "structure":str(structure),"ecut_eV":ECUT_EV,"kpts":list(kmesh),"kpt_min_distance_A":KPT_MIN_DISTANCE_A,
 "energy_eV":float(ehost),"energy_eV_atom":float(ehost/len(host)),
 "max_force_eV_A":float(np.max(np.linalg.norm(fhost,axis=1))),"mpi_world_size":int(world.size)}
world.barrier()
if world.rank==0:
    (RESULTS/f"{tag}_host.json").write_text(json.dumps(hrec,indent=2,ensure_ascii=False),encoding="utf-8")
world.barrier()

scaled=host.get_scaled_positions(wrap=True); cell=np.asarray(host.cell)
ca=[i for i,s in enumerate(host.get_chemical_symbols()) if s=="Ca"]
scores=[]
for i in ca:
    ds=scaled[i]-0.5; ds-=np.round(ds); scores.append((float(np.linalg.norm(ds@cell)),i))
scores.sort(); center_dist,pbidx=scores[0]

initial=host.copy(); initial[pbidx].symbol="Pb"
defect=initial.copy(); defect.calc=calc(LOGS/f"{tag}_PbCa_gpaw.txt")
eun=defect.get_potential_energy()

dist=defect.get_distances(pbidx,np.arange(len(defect)),mic=True)
fixed=[i for i,d in enumerate(dist) if d>LOCAL_RELAX_RADIUS_A and i!=pbidx]
defect.set_constraint(FixAtoms(indices=fixed))
op1=BFGS(defect,logfile=str(LOGS/f"{tag}_PbCa_local.log"),trajectory=str(RELAX/f"{tag}_PbCa_local.traj"),maxstep=0.15)
ok1=bool(op1.run(fmax=LOCAL_FMAX_EV_A,steps=MAX_LOCAL_STEPS))

defect.set_constraint()
op2=BFGS(defect,logfile=str(LOGS/f"{tag}_PbCa_full.log"),trajectory=str(RELAX/f"{tag}_PbCa_full.traj"),maxstep=0.12)
ok2=bool(op2.run(fmax=FINAL_FMAX_EV_A,steps=MAX_FINAL_STEPS))

erel=defect.get_potential_energy(); forces=defect.get_forces()
oids=[i for i,s in enumerate(defect.get_chemical_symbols()) if s=="O"]
pbo=sorted(float(defect.get_distance(pbidx,i,mic=True)) for i in oids)[:6]
si=initial.get_scaled_positions(wrap=True); sf=defect.get_scaled_positions(wrap=True)
disp=[]
for i in range(len(defect)):
    ds=sf[i]-si[i]; ds-=np.round(ds); disp.append(float(np.linalg.norm(ds@np.asarray(defect.cell))))
write(RELAX/f"{tag}_PbCa_relaxed.traj",defect); write(RELAX/f"{tag}_PbCa_relaxed.cif",defect)

rec={"status":"converged" if ok2 else "not_fully_converged","step":"05B-PbCa","mineral":mineral,"natoms":len(defect),
 "defect":"Pb2+_on_Ca2+","charge_state":0,"formal_substitution":"Pb2+ -> Ca2+","pb_atom_index":int(pbidx),
 "selected_Ca_distance_from_fractional_center_A":float(center_dist),"ecut_eV":ECUT_EV,"kpts":list(kmesh),
 "kpt_min_distance_A":KPT_MIN_DISTANCE_A,"energy_host_eV":float(ehost),"energy_defect_unrelaxed_eV":float(eun),
 "energy_defect_relaxed_eV":float(erel),"raw_substitution_energy_eV":float(erel-ehost),
 "relaxation_energy_eV":float(erel-eun),"local_stage_converged":ok1,"full_stage_converged":ok2,
 "local_stage_free_atoms":len(defect)-len(fixed),"max_force_eV_A":float(np.max(np.linalg.norm(forces,axis=1))),
 "PbO_first6_A":pbo,"PbO6_mean_A":float(np.mean(pbo)),"PbO6_std_A":float(np.std(pbo)),
 "maximum_atomic_displacement_A":float(max(disp)),"relaxed_traj":str(RELAX/f"{tag}_PbCa_relaxed.traj"),
 "note":"Edef-Ehost is only a finite-size proxy, not a formation energy; chemical potentials are not included."}
world.barrier()
if world.rank==0:
    (RESULTS/f"{tag}_PbCa.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(rec,indent=2,ensure_ascii=False))
world.barrier()
