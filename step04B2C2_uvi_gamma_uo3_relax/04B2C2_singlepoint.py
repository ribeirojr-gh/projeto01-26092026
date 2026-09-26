#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
import numpy as np
from ase.dft.bandgap import bandgap
from ase.io import read
from ase.units import GPa
from gpaw import GPAW,PW,setup_paths
from gpaw.mpi import world
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2C2 import *
def req(n):
    v=os.environ.get(n,"")
    if not v: raise RuntimeError(f"Variável obrigatória ausente: {n}")
    return v
ecut=float(req("UPB_B2C2_ECUT")); kpts=tuple(int(x) for x in req("UPB_B2C2_KPTS").split(","))
tag=req("UPB_B2C2_TAG"); out=Path(req("UPB_B2C2_OUT")); txt=Path(req("UPB_B2C2_TXT")); gpw=Path(req("UPB_B2C2_GPW"))
setup_paths.insert(0,str(MATRIX_DIR.resolve())); setup_paths.insert(0,str(U_DIR.resolve()))
atoms=read(RELAX/"gamma_UO3_relaxed_scalar.traj")
calc=GPAW(mode=PW(ecut,dedecut="estimate"),xc=XC,kpts={"size":kpts,"gamma":True},nbands=NBANDS_FINAL,
 random=False,setups={"U":f":f,{UEFF_EV:.8f}","default":"paw"},
 occupations={"name":"fermi-dirac","width":SMEARING_EV},eigensolver={"name":"dav","niter":5},
 convergence={"energy":5e-4,"density":5e-6,"eigenstates":5e-8,"bands":"occupied"},txt=str(txt))
atoms.calc=calc
e=atoms.get_potential_energy(); f=atoms.get_forces(); s=atoms.get_stress(voigt=True)/GPa
try: gap=float(bandgap(calc,output=None)[0]); ge=None
except Exception as exc: gap=None; ge=repr(exc)
calc.write(gpw)
rec={"status":"converged","step":"04B2C2-final-singlepoint","case":tag,"system":"gamma-UO3-Fddd-relaxed",
 "dataset":"U14_nc6","xc":XC,"Ueff_eV":UEFF_EV,"spin_state":"nonmagnetic_5f0","ecut_eV":ecut,"kpts":list(kpts),
 "nbands":NBANDS_FINAL,"energy_eV":float(e),"energy_eV_atom":float(e/len(atoms)),"band_gap_eV":gap,"band_gap_error":ge,
 "max_force_eV_A":float(np.max(np.linalg.norm(f,axis=1))),"stress_GPa":[float(x) for x in s],
 "hydrostatic_stress_GPa":float(np.mean(s[:3])),"max_abs_stress_GPa":float(np.max(np.abs(s))),
 "gpw_file":str(gpw),"mpi_world_size":int(world.size)}
world.barrier()
if world.rank==0:
    out.write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8"); print(json.dumps(rec,indent=2,ensure_ascii=False))
world.barrier()
