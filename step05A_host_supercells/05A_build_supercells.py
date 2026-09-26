#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
from ase.build import make_supercell
from ase.io import read, write

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step05A import (
    HOSTS, RESULTS, RELAX, SUPERCELLS, TARGET_DETERMINANTS,
)

SUPERCELLS.mkdir(parents=True, exist_ok=True)


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def shortest_translation(cell):
    best = float("inf")
    best_n = None
    for n in itertools.product(range(-2, 3), repeat=3):
        if n == (0, 0, 0):
            continue
        v = np.dot(np.asarray(n, float), cell)
        length = float(np.linalg.norm(v))
        if length < best:
            best = length
            best_n = n
    return best, best_n


def enumerate_hnf(det):
    # Upper-triangular integer matrices with exact determinant.
    for a in divisors(det):
        rem = det // a
        for d in divisors(rem):
            f = rem // d
            for b in range(d):
                for c in range(f):
                    for e in range(f):
                        yield np.array(
                            [[a, b, c],
                             [0, d, e],
                             [0, 0, f]],
                            dtype=int,
                        )


def score_matrix(P, cell):
    newcell = P @ cell
    shortest, coeff = shortest_translation(newcell)
    lengths = np.linalg.norm(newcell, axis=1)
    anisotropy = float(lengths.max() / lengths.min())
    # Prioridade: maior distância periódica mínima; desempate por isotropia.
    return shortest, -anisotropy, coeff, lengths


manifest = {
    "step": "05A-supercell-design",
    "policy": (
        "Near-isotropic HNF supercells are selected by maximizing the "
        "shortest lattice translation, reducing periodic defect-image "
        "interaction without assuming diagonal replication."
    ),
    "hosts": {},
}

for mineral in HOSTS:
    host_path = RELAX / f"{mineral}_PBEsol1400_relaxed.traj"
    if not host_path.exists():
        raise FileNotFoundError(host_path)

    atoms = read(host_path)
    cell = np.asarray(atoms.cell)

    host_rec = {
        "primitive_natoms": len(atoms),
        "candidates": [],
    }

    for det in TARGET_DETERMINANTS:
        best = None
        for P in enumerate_hnf(det):
            shortest, neg_aniso, coeff, lengths = score_matrix(P, cell)
            key = (shortest, neg_aniso)
            if best is None or key > best["key"]:
                best = {
                    "key": key,
                    "P": P.copy(),
                    "shortest": shortest,
                    "coeff": coeff,
                    "lengths": lengths,
                    "anisotropy": -neg_aniso,
                }

        P = best["P"]
        sc = make_supercell(atoms, P, wrap=True)

        traj = SUPERCELLS / f"{mineral}_det{det}_{len(sc)}atoms.traj"
        cif = SUPERCELLS / f"{mineral}_det{det}_{len(sc)}atoms.cif"
        write(traj, sc)
        write(cif, sc)

        host_rec["candidates"].append({
            "determinant": int(det),
            "natoms": len(sc),
            "matrix": P.tolist(),
            "shortest_periodic_translation_A":
                float(best["shortest"]),
            "shortest_translation_coefficients":
                list(best["coeff"]),
            "cell_vector_lengths_A":
                [float(x) for x in best["lengths"]],
            "basis_vector_anisotropy":
                float(best["anisotropy"]),
            "traj": str(traj),
            "cif": str(cif),
        })

    manifest["hosts"][mineral] = host_rec

(RESULTS / "supercell_manifest_step05A.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2, ensure_ascii=False))
