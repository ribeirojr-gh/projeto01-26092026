#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from ase.constraints import FixAtoms
from ase.dft.kpoints import mindistance2monkhorstpack
from ase.io import read, write
from ase.optimize import BFGS
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step05B import *


def req(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


mineral = req("UPB_PBCA_HOST")
nreq = int(req("UPB_PBCA_NATOMS"))

if mineral not in SUPERCELLS or nreq not in SUPERCELLS[mineral]:
    raise ValueError("Caso inválido.")

for d in (RESULTS, LOGS, RELAX):
    d.mkdir(parents=True, exist_ok=True)

structure = SUPERCELLS[mineral][nreq]
if not structure.exists():
    raise FileNotFoundError(structure)

for symbol in ("Ca", "C", "O"):
    p = HOST_PAW_DIR / f"{symbol}.PBEsol"
    if not p.exists():
        raise FileNotFoundError(p)

if mineral == "dolomita":
    p = HOST_PAW_DIR / "Mg.PBEsol"
    if not p.exists():
        raise FileNotFoundError(p)

if not (PB_PAW_DIR / "Pb.PBEsol").exists():
    raise FileNotFoundError(PB_PAW_DIR / "Pb.PBEsol")

setup_paths.insert(0, str(HOST_PAW_DIR.resolve()))
setup_paths.insert(0, str(PB_PAW_DIR.resolve()))

host = read(structure)
if len(host) != nreq:
    raise RuntimeError(f"N esperado {nreq}, obtido {len(host)}")

kmesh_final = tuple(
    int(x)
    for x in mindistance2monkhorstpack(
        host,
        min_distance=KPT_MIN_DISTANCE_FINAL_A,
        maxperdim=8,
        even=False,
    )
)

kmesh_original = tuple(
    int(x)
    for x in mindistance2monkhorstpack(
        host,
        min_distance=KPT_MIN_DISTANCE_DIAGNOSTIC_A,
        maxperdim=8,
        even=False,
    )
)

tag = f"{mineral}_{nreq}"

if world.rank == 0:
    print(
        f"[05B-R1] {tag}: "
        f"mesh original 24A={kmesh_original} "
        f"(Nk={int(np.prod(kmesh_original))}); "
        f"mesh final 16A={kmesh_final} "
        f"(Nk={int(np.prod(kmesh_final))})",
        flush=True,
    )


def calculator(txt, kmesh):
    return GPAW(
        mode=PW(ECUT_EV, dedecut="estimate"),
        xc=XC,
        kpts={"size": tuple(kmesh), "gamma": True},
        occupations={
            "name": "fermi-dirac",
            "width": SMEARING_EV,
        },
        random=False,
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        eigensolver={"name": "dav", "niter": 4},
        txt=str(txt),
    )


# ------------------------------------------------------------------
# Matched pristine host: only the final sampling used for the size gate.
# ------------------------------------------------------------------
host.calc = calculator(
    LOGS / f"{tag}_host_finalk_gpaw.txt",
    kmesh_final,
)
e_host_finalk = host.get_potential_energy()
f_host_finalk = host.get_forces()

host_record = {
    "status": "converged",
    "step": "05B-R1-host",
    "mineral": mineral,
    "natoms": len(host),
    "ecut_eV": ECUT_EV,
    "kmesh_original_24A": list(kmesh_original),
    "kmesh_final_16A": list(kmesh_final),
    "Nk_original_reducible": int(np.prod(kmesh_original)),
    "Nk_final_reducible": int(np.prod(kmesh_final)),
    "energy_finalk_eV": float(e_host_finalk),
    "max_force_finalk_eV_A": float(
        np.max(np.linalg.norm(f_host_finalk, axis=1))
    ),
}

world.barrier()
if world.rank == 0:
    (RESULTS / f"{tag}_host.json").write_text(
        json.dumps(host_record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
world.barrier()


# ------------------------------------------------------------------
# Central Ca site
# ------------------------------------------------------------------
scaled = host.get_scaled_positions(wrap=True)
cell = np.asarray(host.cell)
ca_indices = [
    i for i, s in enumerate(host.get_chemical_symbols())
    if s == "Ca"
]
scores = []
for i in ca_indices:
    ds = scaled[i] - 0.5
    ds -= np.round(ds)
    scores.append((float(np.linalg.norm(ds @ cell)), i))
scores.sort()
center_distance, pb_index = scores[0]

initial = host.copy()
initial[pb_index].symbol = "Pb"

# ------------------------------------------------------------------
# Gamma-only relaxation
# ------------------------------------------------------------------
defect = initial.copy()
defect.calc = calculator(
    LOGS / f"{tag}_PbCa_gamma_relax_gpaw.txt",
    (1, 1, 1),
)

e_unrel_gamma = defect.get_potential_energy()

distances = defect.get_distances(
    pb_index,
    np.arange(len(defect)),
    mic=True,
)
fixed = [
    i for i, d in enumerate(distances)
    if d > LOCAL_RELAX_RADIUS_A and i != pb_index
]

defect.set_constraint(FixAtoms(indices=fixed))
opt_local = BFGS(
    defect,
    logfile=str(LOGS / f"{tag}_PbCa_local_gamma.log"),
    trajectory=str(RELAX / f"{tag}_PbCa_local_gamma.traj"),
    maxstep=0.15,
)
local_ok = bool(
    opt_local.run(
        fmax=LOCAL_FMAX_EV_A,
        steps=MAX_LOCAL_STEPS,
    )
)

defect.set_constraint()
opt_gamma = BFGS(
    defect,
    logfile=str(LOGS / f"{tag}_PbCa_full_gamma.log"),
    trajectory=str(RELAX / f"{tag}_PbCa_full_gamma.traj"),
    maxstep=0.12,
)
gamma_ok = bool(
    opt_gamma.run(
        fmax=GAMMA_FINAL_FMAX_EV_A,
        steps=MAX_GAMMA_STEPS,
    )
)

e_rel_gamma = defect.get_potential_energy()
gamma_relaxation_energy = float(
    e_rel_gamma - e_unrel_gamma
)

# ------------------------------------------------------------------
# Final sampling single point; conditionally relax a few more steps
# if its forces expose significant k-point dependence of geometry.
# ------------------------------------------------------------------
defect.calc = calculator(
    LOGS / f"{tag}_PbCa_finalk_gpaw.txt",
    kmesh_final,
)
e_def_finalk = defect.get_potential_energy()
forces_finalk = defect.get_forces()
fmax_finalk = float(
    np.max(np.linalg.norm(forces_finalk, axis=1))
)

dense_correction_used = False
dense_ok = True

if fmax_finalk > DENSE_RELAX_TRIGGER_EV_A:
    dense_correction_used = True
    opt_dense = BFGS(
        defect,
        logfile=str(LOGS / f"{tag}_PbCa_dense_correction.log"),
        trajectory=str(RELAX / f"{tag}_PbCa_dense_correction.traj"),
        maxstep=0.10,
    )
    dense_ok = bool(
        opt_dense.run(
            fmax=DENSE_FINAL_FMAX_EV_A,
            steps=MAX_DENSE_STEPS,
        )
    )
    e_def_finalk = defect.get_potential_energy()
    forces_finalk = defect.get_forces()
    fmax_finalk = float(
        np.max(np.linalg.norm(forces_finalk, axis=1))
    )

symbols = defect.get_chemical_symbols()
o_indices = [
    i for i, s in enumerate(symbols)
    if s == "O"
]
pbo6 = sorted(
    float(defect.get_distance(pb_index, i, mic=True))
    for i in o_indices
)[:6]

si = initial.get_scaled_positions(wrap=True)
sf = defect.get_scaled_positions(wrap=True)
displacements = []
for i in range(len(defect)):
    ds = sf[i] - si[i]
    ds -= np.round(ds)
    displacements.append(
        float(np.linalg.norm(ds @ np.asarray(defect.cell)))
    )

out_traj = RELAX / f"{tag}_PbCa_relaxed_R1.traj"
out_cif = RELAX / f"{tag}_PbCa_relaxed_R1.cif"
write(out_traj, defect)
write(out_cif, defect)

record = {
    "status": (
        "converged"
        if gamma_ok and dense_ok
        else "not_fully_converged"
    ),
    "step": "05B-R1-PbCa",
    "mineral": mineral,
    "natoms": len(defect),
    "defect": "Pb2+_on_Ca2+",
    "charge_state": 0,
    "pb_atom_index": int(pb_index),
    "selected_Ca_distance_from_fractional_center_A":
        float(center_distance),
    "ecut_eV": ECUT_EV,
    "relaxation_kpts": [1, 1, 1],
    "final_kmesh": list(kmesh_final),
    "diagnostic_original_24A_kmesh": list(kmesh_original),
    "Nk_final_reducible": int(np.prod(kmesh_final)),
    "Nk_original_24A_reducible": int(np.prod(kmesh_original)),
    "energy_host_finalk_eV": float(e_host_finalk),
    "energy_defect_finalk_eV": float(e_def_finalk),
    "raw_substitution_energy_eV":
        float(e_def_finalk - e_host_finalk),
    "gamma_relaxation_energy_eV":
        gamma_relaxation_energy,
    "local_stage_converged": local_ok,
    "gamma_full_stage_converged": gamma_ok,
    "dense_correction_used": dense_correction_used,
    "dense_correction_converged": dense_ok,
    "max_force_finalk_eV_A": fmax_finalk,
    "PbO_first6_A": pbo6,
    "PbO6_mean_A": float(np.mean(pbo6)),
    "PbO6_std_A": float(np.std(pbo6)),
    "maximum_atomic_displacement_A":
        float(max(displacements)),
    "relaxed_traj": str(out_traj),
    "relaxed_cif": str(out_cif),
    "note": (
        "raw_substitution_energy is used only for the finite-size "
        "difference.  It is not a formation energy."
    ),
}

world.barrier()
if world.rank == 0:
    (RESULTS / f"{tag}_PbCa.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
world.barrier()
