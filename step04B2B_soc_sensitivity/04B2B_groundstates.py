#!/usr/bin/env python3
from __future__ import annotations
import gc, json, os, sys
from pathlib import Path
import numpy as np
from ase.dft.bandgap import bandgap
from ase.io import read
from gpaw import GPAW, PW, MixerDif, KohnShamConvergenceError, restart, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from config_step04B2B import *

RESULTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
GPW.mkdir(parents=True, exist_ok=True)

def get_gap(calc):
    try:
        return float(bandgap(calc, output=None)[0]), None
    except Exception as exc:
        return None, repr(exc)

def pbco3():
    setup_paths.insert(0, str(MATRIX_DIR.resolve()))
    setup_paths.insert(0, str(PB_DIR.resolve()))
    atoms = read(PBCO3_RELAXED)
    gpw = GPW / "PbCO3_scalar_1600_k434_all.gpw"
    calc = GPAW(
        mode=PW(PB_ECUT, dedecut="estimate"), xc="PBEsol",
        kpts={"size": PB_KPTS, "gamma": True},
        setups={"Pb": "paw", "default": "paw"},
        occupations={"name": "fermi-dirac", "width": SMEAR},
        convergence={"energy": 5e-4, "density": 5e-6,
                     "eigenstates": 5e-8, "bands": "occupied"},
        eigensolver={"name": "dav", "niter": 4},
        random=False, txt=str(LOGS / "PbCO3_scalar_1600_k434.txt"))
    atoms.calc = calc
    energy = atoms.get_potential_energy()
    gap, err = get_gap(calc)
    calc.write(gpw, mode="all")
    return {"status": "converged", "system": "PbCO3",
            "energy_eV": float(energy), "energy_eV_atom": float(energy/len(atoms)),
            "scalar_gap_eV": gap, "scalar_gap_error": err,
            "ecut_eV": PB_ECUT, "kpts": list(PB_KPTS),
            "gpw_file": str(gpw), "mpi_world_size": int(world.size)}

def u_atoms():
    atoms = read(UO2_STRUCTURE)
    atoms.set_cell([(U_A,0,0),(0,U_A,0),(0,0,U_A)], scale_atoms=True)
    uidx = [i for i,s in enumerate(atoms.get_chemical_symbols()) if s=="U"]
    m = np.zeros(len(atoms))
    for i, sign in zip(uidx, U_SIGNS):
        m[i] = U_M0 * sign
    atoms.set_initial_magnetic_moments(m)
    return atoms

def attempts():
    return [
        ("lcao_0p10", 0.10, 800,
         MixerDif(beta=0.03,nmaxold=8,weight=100,
                  beta_m=0.05,nmaxold_m=5,weight_m=50)),
        ("lcao_0p15_damped", 0.15, 1100,
         MixerDif(beta=0.015,nmaxold=8,weight=120,
                  beta_m=0.03,nmaxold_m=6,weight_m=80)),
    ]

def make_ucalc(name,width,maxiter,mixer,txt):
    return GPAW(
        mode=PW(U_ECUT, dedecut="estimate"), xc="PBEsol",
        kpts={"size": U_KPTS, "gamma": True}, nbands=U_NBANDS,
        random=False, spinpol=True,
        symmetry={"point_group": False, "time_reversal": True},
        setups={"U": f":f,{U_UEFF:.8f}", "default": "paw"},
        occupations={"name": "fermi-dirac", "width": width},
        mixer=mixer, eigensolver={"name":"dav","niter":5},
        convergence={"energy":1e-3,"density":1e-5,
                     "eigenstates":1e-7,"bands":"occupied"},
        maxiter=maxiter, verbose=1, txt=str(txt))

def uo2():
    setup_paths.insert(0, str(MATRIX_DIR.resolve()))
    setup_paths.insert(0, str(U_DIR.resolve()))
    pre = GPW / "UO2_scalar_1600_pre_all.gpw"
    final = GPW / "UO2_scalar_1600_U3_all.gpw"
    failures=[]; ok=None
    for n,(name,width,maxiter,mixer) in enumerate(attempts(),1):
        atoms=u_atoms()
        calc=make_ucalc(name,width,maxiter,mixer,
                        LOGS/f"UO2_scalar_attempt{n}_{name}.txt")
        atoms.calc=calc
        try:
            atoms.get_potential_energy()
            calc.write(pre, mode="all")
            ok={"strategy":name,"iterations":int(calc.scf.niter)}
            break
        except KohnShamConvergenceError as exc:
            failures.append({"attempt":n,"strategy":name,
                             "iterations":int(calc.scf.niter),"error":repr(exc)})
        finally:
            atoms.calc=None
            del calc
            gc.collect()
    if ok is None:
        return {"status":"failed_preconvergence","system":"UO2","failures":failures}
    atoms,calc=restart(str(pre),txt=str(LOGS/"UO2_scalar_tight_0p05.txt"))
    calc.set(occupations={"name":"fermi-dirac","width":SMEAR},
             eigensolver={"name":"dav","niter":5},
             convergence={"energy":5e-4,"density":5e-6,
                          "eigenstates":5e-8,"bands":"occupied"})
    try:
        energy=atoms.get_potential_energy()
        gap,err=get_gap(calc)
        calc.write(final, mode="all")
        mm=atoms.get_magnetic_moments()
        uidx=[i for i,s in enumerate(atoms.get_chemical_symbols()) if s=="U"]
        um=[float(mm[i]) for i in uidx]
        return {"status":"converged","system":"UO2","dataset":"U14_nc6",
                "Ueff_eV":U_UEFF,"ecut_eV":U_ECUT,"kpts":list(U_KPTS),
                "energy_eV":float(energy),"energy_eV_atom":float(energy/len(atoms)),
                "scalar_gap_eV":gap,"scalar_gap_error":err,
                "U_local_moments_muB":um,
                "U_abs_mean_moment_muB":float(np.mean(np.abs(um))),
                "gpw_file":str(final),"preconvergence":ok,
                "failures_before_success":failures,
                "mpi_world_size":int(world.size)}
    finally:
        atoms.calc=None
        del calc
        gc.collect()

def main():
    system=os.environ.get("UPB_SOC_SYSTEM","")
    if system=="PbCO3":
        rec=pbco3(); name="PbCO3_scalar_groundstate.json"
    elif system=="UO2":
        rec=uo2(); name="UO2_scalar_groundstate.json"
    else:
        raise ValueError("UPB_SOC_SYSTEM deve ser PbCO3 ou UO2")
    world.barrier()
    if world.rank==0:
        (RESULTS/name).write_text(json.dumps(rec,indent=2,ensure_ascii=False),
                                  encoding="utf-8")
        print(json.dumps(rec,indent=2,ensure_ascii=False))
    world.barrier()

if __name__=="__main__":
    main()
