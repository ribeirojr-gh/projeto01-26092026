#!/usr/bin/env python3
import json,sys
from pathlib import Path
import numpy as np
from ase.constraints import FixSymmetry
from ase.filters import FrechetCellFilter
from ase.io import read,write
from ase.io.trajectory import Trajectory
from ase.optimize import BFGS
from ase.units import GPa
from gpaw import GPAW,PW,setup_paths
SCRIPT_DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2C2 import *
for d in (RESULTS,LOGS,RELAX): d.mkdir(parents=True,exist_ok=True)
for p in (EXP_PRIM,MATRIX_DIR/"O.PBEsol",U_DIR/"U.PBEsol"):
    if not p.exists(): raise FileNotFoundError(p)
setup_paths.insert(0,str(MATRIX_DIR.resolve())); setup_paths.insert(0,str(U_DIR.resolve()))
atoms=read(EXP_PRIM)
atoms.set_constraint(FixSymmetry(atoms,symprec=SYMPREC_RELAX_A,adjust_positions=True,adjust_cell=True))
atoms.calc=GPAW(mode=PW(ECUT_PROD_EV,dedecut="estimate"),xc=XC,
    kpts={"size":KPTS_PROD,"gamma":True},nbands=NBANDS_RELAX,random=False,
    setups={"U":f":f,{UEFF_EV:.8f}","default":"paw"},
    occupations={"name":"fermi-dirac","width":SMEARING_EV},
    eigensolver={"name":"dav","niter":5},
    convergence={"energy":1e-3,"density":1e-5,"eigenstates":1e-7,"bands":"occupied"},
    txt=str(LOGS/"gammaUO3_relax_gpaw.txt"))
stages=[]
def snap(name):
    f=atoms.get_forces(); s=atoms.get_stress(voigt=True)/GPa
    return {"stage":name,"energy_eV":float(atoms.get_potential_energy()),
      "max_force_eV_A":float(np.max(np.linalg.norm(f,axis=1))),
      "stress_GPa":[float(x) for x in s],"max_abs_stress_GPa":float(np.max(np.abs(s))),
      "volume_A3":float(atoms.get_volume()),"cell_lengths_A":[float(x) for x in atoms.cell.lengths()],
      "cell_angles_deg":[float(x) for x in atoms.cell.angles()]}
def atom_stage(name,fmax,steps):
    opt=BFGS(atoms,logfile=str(LOGS/f"{name}.log"),trajectory=str(RELAX/f"{name}.traj"),maxstep=0.15)
    ok=bool(opt.run(fmax=fmax,steps=steps)); r=snap(name)
    r.update({"type":"atomic_positions_fixed_cell","target_fmax_eV_A":fmax,"optimizer_steps":int(opt.nsteps),"converged":ok}); stages.append(r)
def coupled(name,fmax,steps):
    filt=FrechetCellFilter(atoms,mask=[1,1,1,1,1,1]); tr=Trajectory(str(RELAX/f"{name}.traj"),"w",atoms)
    opt=BFGS(filt,logfile=str(LOGS/f"{name}.log"),maxstep=0.10); opt.attach(tr.write,interval=1)
    ok=bool(opt.run(fmax=fmax,steps=steps)); tr.close(); r=snap(name)
    r.update({"type":"positions_plus_cell_FrechetCellFilter","target_filter_fmax_eV_A":fmax,"optimizer_steps":int(opt.nsteps),"converged":ok}); stages.append(r)
atom_stage("01_atoms_exp_cell",ATOM_FMAX_STAGE1_EV_A,180)
coupled("02_coupled_round1",COUPLED_FMAX_STAGE1_EV_A,220)
atom_stage("03_atoms_tight",ATOM_FMAX_STAGE2_EV_A,180)
coupled("04_coupled_final",COUPLED_FMAX_FINAL_EV_A,220)
final=atoms.copy(); final.set_constraint(); final.calc=atoms.calc
e=final.get_potential_energy(); f=final.get_forces(); s=final.get_stress(voigt=True)/GPa
write(RELAX/"gamma_UO3_relaxed_scalar.traj",final); write(RELAX/"gamma_UO3_relaxed_scalar_primitive.cif",final)
rec={"status":"completed","step":"04B2C2-relaxation","system":"gamma-UO3-Fddd",
 "matrix":{"dataset":"U14_nc6","xc":XC,"Ueff_eV":UEFF_EV,"ecut_eV":ECUT_PROD_EV,"kpts":list(KPTS_PROD),"spin_state":"nonmagnetic_5f0","SOC":False},
 "symmetry_constraint":{"class":"ase.constraints.FixSymmetry","symprec_A":SYMPREC_RELAX_A},
 "cell_filter":"ase.filters.FrechetCellFilter","stages":stages,"all_stages_converged":all(x["converged"] for x in stages),
 "energy_eV":float(e),"energy_eV_atom":float(e/len(final)),"max_force_eV_A":float(np.max(np.linalg.norm(f,axis=1))),
 "stress_GPa":[float(x) for x in s],"max_abs_stress_GPa":float(np.max(np.abs(s))),"volume_A3":float(final.get_volume())}
(RESULTS/"relaxation_step04B2C2.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(rec,indent=2,ensure_ascii=False))
