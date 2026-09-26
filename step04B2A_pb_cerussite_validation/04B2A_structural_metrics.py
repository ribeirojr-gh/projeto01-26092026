#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import spglib
from ase.io import read

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2A import (
    CERUSSITE_TRAJ,
    RESULTS_DIR,
    RELAX_DIR,
    EXP_A_A,
    EXP_B_A,
    EXP_C_A,
    EXP_VOLUME_A3,
    EXP_SPACEGROUP_NUMBER,
    EXP_CARBONATE_APLANARITY_A,
    MAX_LATTICE_ERROR_PERCENT,
    MAX_VOLUME_ERROR_PERCENT,
    MAX_ANGLE_ERROR_DEG,
    MAX_VALIDATION_FORCE_EV_A,
    MAX_VALIDATION_STRESS_GPA,
    MAX_CO_BOND_MEAN_REL_ERROR_PERCENT,
    MAX_PBO9_MEAN_REL_ERROR_PERCENT,
)


def pct(x, ref):
    return abs(x - ref) / abs(ref) * 100.0


def symmetry(atoms, symprec):
    cell = (
        np.asarray(atoms.cell),
        np.asarray(atoms.get_scaled_positions()),
        np.asarray(atoms.numbers),
    )
    ds = spglib.get_symmetry_dataset(
        cell,
        symprec=symprec,
    )
    return {
        "symprec_A": symprec,
        "number": int(ds.number),
        "international": str(ds.international),
        "hall": str(ds.hall),
    }


def chemistry_metrics(atoms):
    symbols = atoms.get_chemical_symbols()
    cidx = [i for i, s in enumerate(symbols) if s == "C"]
    oidx = [i for i, s in enumerate(symbols) if s == "O"]
    pbidx = [i for i, s in enumerate(symbols) if s == "Pb"]

    co = []
    aplanarity = []

    for ci in cidx:
        distances = []
        vectors = []
        for oi in oidx:
            d = atoms.get_distance(ci, oi, mic=True)
            vec = atoms.get_distance(ci, oi, mic=True, vector=True)
            distances.append((d, oi, np.asarray(vec)))
        nearest = sorted(distances, key=lambda x: x[0])[:3]
        co.extend([float(item[0]) for item in nearest])

        # C is at origin; three O vectors define the O3 plane.
        p1, p2, p3 = [item[2] for item in nearest]
        normal = np.cross(p2 - p1, p3 - p1)
        norm = np.linalg.norm(normal)
        if norm > 1e-12:
            distance = abs(np.dot(-p1, normal)) / norm
            aplanarity.append(float(distance))

    pbo9 = []
    for pi in pbidx:
        distances = [
            atoms.get_distance(pi, oi, mic=True)
            for oi in oidx
        ]
        pbo9.extend(
            float(x) for x in sorted(distances)[:9]
        )

    return {
        "CO_bonds_A": {
            "count": len(co),
            "mean": float(np.mean(co)),
            "std": float(np.std(co)),
            "min": float(np.min(co)),
            "max": float(np.max(co)),
        },
        "carbonate_C_to_O3_plane_A": {
            "count": len(aplanarity),
            "mean": float(np.mean(aplanarity)),
            "std": float(np.std(aplanarity)),
            "min": float(np.min(aplanarity)),
            "max": float(np.max(aplanarity)),
        },
        "PbO_nearest9_A": {
            "count": len(pbo9),
            "mean": float(np.mean(pbo9)),
            "std": float(np.std(pbo9)),
            "min": float(np.min(pbo9)),
            "max": float(np.max(pbo9)),
        },
    }


exp = read(CERUSSITE_TRAJ)
relaxed = read(RELAX_DIR / "PbCO3_relaxed_production.traj")

expchem = chemistry_metrics(exp)
relchem = chemistry_metrics(relaxed)

lengths = relaxed.cell.lengths()
angles = relaxed.cell.angles()

lattice = {
    "a_A": float(lengths[0]),
    "b_A": float(lengths[1]),
    "c_A": float(lengths[2]),
    "alpha_deg": float(angles[0]),
    "beta_deg": float(angles[1]),
    "gamma_deg": float(angles[2]),
    "volume_A3": float(relaxed.get_volume()),
}

errors = {
    "a_percent": pct(lattice["a_A"], EXP_A_A),
    "b_percent": pct(lattice["b_A"], EXP_B_A),
    "c_percent": pct(lattice["c_A"], EXP_C_A),
    "volume_percent": pct(
        lattice["volume_A3"],
        EXP_VOLUME_A3,
    ),
    "max_angle_error_deg": max(
        abs(lattice["alpha_deg"] - 90.0),
        abs(lattice["beta_deg"] - 90.0),
        abs(lattice["gamma_deg"] - 90.0),
    ),
    "CO_mean_percent": pct(
        relchem["CO_bonds_A"]["mean"],
        expchem["CO_bonds_A"]["mean"],
    ),
    "PbO9_mean_percent": pct(
        relchem["PbO_nearest9_A"]["mean"],
        expchem["PbO_nearest9_A"]["mean"],
    ),
}

symmetry_report = [
    symmetry(relaxed, 1.0e-2),
    symmetry(relaxed, 5.0e-2),
]

structure_pass = (
    max(
        errors["a_percent"],
        errors["b_percent"],
        errors["c_percent"],
    ) <= MAX_LATTICE_ERROR_PERCENT
    and errors["volume_percent"] <= MAX_VOLUME_ERROR_PERCENT
    and errors["max_angle_error_deg"] <= MAX_ANGLE_ERROR_DEG
    and errors["CO_mean_percent"]
    <= MAX_CO_BOND_MEAN_REL_ERROR_PERCENT
    and errors["PbO9_mean_percent"]
    <= MAX_PBO9_MEAN_REL_ERROR_PERCENT
    and any(
        item["number"] == EXP_SPACEGROUP_NUMBER
        for item in symmetry_report
    )
)

report = {
    "step": "04B2A-structural-metrics",
    "experimental_reference": {
        "source": (
            "Chevrier et al., Z. Kristallogr. 199 (1992) 67-74; "
            "neutron single-crystal refinement."
        ),
        "a_A": EXP_A_A,
        "b_A": EXP_B_A,
        "c_A": EXP_C_A,
        "volume_A3": EXP_VOLUME_A3,
        "spacegroup_number": EXP_SPACEGROUP_NUMBER,
        "carbonate_aplanarity_A":
            EXP_CARBONATE_APLANARITY_A,
    },
    "relaxed_lattice": lattice,
    "relative_errors": errors,
    "experimental_structure_chemistry": expchem,
    "relaxed_structure_chemistry": relchem,
    "symmetry": symmetry_report,
    "structural_gate_passes": bool(structure_pass),
}

(RESULTS_DIR / "structural_metrics_step04B2A.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(report, indent=2, ensure_ascii=False))
