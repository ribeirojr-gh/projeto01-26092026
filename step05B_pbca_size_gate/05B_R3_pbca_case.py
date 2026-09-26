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

from config_step05B_R3 import *


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


mineral = req("UPB_PBCA_HOST")
nreq = int(req("UPB_PBCA_NATOMS"))

if world.size != MPI_PROCESSES:
    raise RuntimeError(
        f"Step05B-R3 requer {MPI_PROCESSES} MPI ranks; world.size={world.size}"
    )

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

tag = f"{mineral}_{nreq}"


def gamma_calc(txt):
    return GPAW(
        mode=PW(ECUT_EV, dedecut="estimate"),
        xc=XC,
        kpts={"size": (1, 1, 1), "gamma": True},
        nbands=NBANDS,
        occupations={"name": "fermi-dirac", "width": SMEARING_EV},
        random=False,
        parallel={
            "domain": world.size,
            "band": 1,
            "kpt": 1,
            "sl_auto": True,
        },
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        eigensolver={"name": "dav", "niter": 4},
        txt=str(txt),
    )


def dense80_calc(txt, kmesh):
    # Only used for the 80-atom k-point calibration.
    return GPAW(
        mode=PW(ECUT_EV, dedecut="estimate"),
        xc=XC,
        kpts={"size": tuple(kmesh), "gamma": True},
        nbands=NBANDS,
        occupations={"name": "fermi-dirac", "width": SMEARING_EV},
        random=False,
        parallel={"sl_auto": True},
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        eigensolver={"name": "dav", "niter": 4},
        txt=str(txt),
    )


# Matched pristine Gamma reference.
host.calc = gamma_calc(LOGS / f"{tag}_host_gamma.txt")
e_host_gamma = host.get_potential_energy()
f_host_gamma = host.get_forces()

# Deterministic Ca site nearest fractional center.
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

defect = initial.copy()
defect.calc = gamma_calc(LOGS / f"{tag}_PbCa_gamma.txt")
e_unrel_gamma = defect.get_potential_energy()

# Local pre-relaxation.
distances = defect.get_distances(
    pb_index, np.arange(len(defect)), mic=True
)
fixed = [
    i for i, d in enumerate(distances)
    if d > LOCAL_RELAX_RADIUS_A and i != pb_index
]
defect.set_constraint(FixAtoms(indices=fixed))

opt_local = BFGS(
    defect,
    logfile=str(LOGS / f"{tag}_local_gamma.log"),
    trajectory=str(RELAX / f"{tag}_local_gamma.traj"),
    maxstep=0.15,
)
local_ok = bool(
    opt_local.run(
        fmax=LOCAL_FMAX_EV_A,
        steps=MAX_LOCAL_STEPS,
    )
)

# Full ionic relaxation, fixed cell.
defect.set_constraint()
opt_full = BFGS(
    defect,
    logfile=str(LOGS / f"{tag}_full_gamma.log"),
    trajectory=str(RELAX / f"{tag}_full_gamma.traj"),
    maxstep=0.12,
)
full_ok = bool(
    opt_full.run(
        fmax=FINAL_FMAX_EV_A,
        steps=MAX_FINAL_STEPS,
    )
)

e_def_gamma = defect.get_potential_energy()
f_def_gamma = defect.get_forces()

o_indices = [
    i for i, s in enumerate(defect.get_chemical_symbols())
    if s == "O"
]
pbo6 = sorted(
    float(defect.get_distance(pb_index, i, mic=True))
    for i in o_indices
)[:6]

dense = None
if nreq == 80:
    kmesh = tuple(
        int(x)
        for x in mindistance2monkhorstpack(
            host,
            min_distance=KPT_CALIBRATION_MIN_DISTANCE_A,
            maxperdim=8,
            even=False,
        )
    )

    host_dense = read(structure)
    host_dense.calc = dense80_calc(
        LOGS / f"{tag}_host_dense80.txt",
        kmesh,
    )
    e_host_dense = host_dense.get_potential_energy()

    defect_dense = defect.copy()
    defect_dense.calc = dense80_calc(
        LOGS / f"{tag}_PbCa_dense80.txt",
        kmesh,
    )
    e_def_dense = defect_dense.get_potential_energy()

    raw_gamma = float(e_def_gamma - e_host_gamma)
    raw_dense = float(e_def_dense - e_host_dense)

    dense = {
        "kmesh": list(kmesh),
        "Nk_reducible": int(np.prod(kmesh)),
        "energy_host_eV": float(e_host_dense),
        "energy_defect_eV": float(e_def_dense),
        "raw_substitution_energy_eV": raw_dense,
        "gamma_to_dense_raw_delta_eV":
            abs(raw_dense - raw_gamma),
    }

out_traj = RELAX / f"{tag}_PbCa_relaxed_R3.traj"
out_cif = RELAX / f"{tag}_PbCa_relaxed_R3.cif"
write(out_traj, defect)
write(out_cif, defect)

record = {
    "status": "converged" if full_ok else "not_fully_converged",
    "step": "05B-R3-PbCa",
    "mineral": mineral,
    "natoms": len(defect),
    "defect": "Pb2+_on_Ca2+",
    "charge_state": 0,
    "ecut_eV": ECUT_EV,
    "nbands": NBANDS,
    "mpi_world_size": int(world.size),
    "parallelization": {
        "domain": int(world.size),
        "band": 1,
        "kpt": 1,
        "sl_auto": True,
    },
    "pb_atom_index": int(pb_index),
    "selected_Ca_distance_from_fractional_center_A":
        float(center_distance),
    "energy_host_gamma_eV": float(e_host_gamma),
    "energy_defect_unrelaxed_gamma_eV": float(e_unrel_gamma),
    "energy_defect_relaxed_gamma_eV": float(e_def_gamma),
    "raw_substitution_energy_gamma_eV":
        float(e_def_gamma - e_host_gamma),
    "relaxation_energy_gamma_eV":
        float(e_def_gamma - e_unrel_gamma),
    "local_stage_converged": local_ok,
    "full_stage_converged": full_ok,
    "host_max_force_gamma_eV_A": float(
        np.max(np.linalg.norm(f_host_gamma, axis=1))
    ),
    "defect_max_force_gamma_eV_A": float(
        np.max(np.linalg.norm(f_def_gamma, axis=1))
    ),
    "PbO_first6_A": pbo6,
    "PbO6_mean_A": float(np.mean(pbo6)),
    "PbO6_std_A": float(np.std(pbo6)),
    "dense80_calibration": dense,
    "relaxed_traj": str(out_traj),
    "relaxed_cif": str(out_cif),
    "note": (
        "Gamma energies are used only for the finite-size gate. "
        "The 80-atom cell has an independent denser-k calibration. "
        "These are not defect formation energies."
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
