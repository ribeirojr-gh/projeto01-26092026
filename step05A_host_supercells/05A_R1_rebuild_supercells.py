#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
from ase.build import make_supercell
from ase.cell import Cell
from ase.geometry import is_minkowski_reduced, minkowski_reduce
from ase.io import read, write

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

RESULTS = SCRIPT_DIR / "resultados_step05A"
SUPERCELLS = RESULTS / "supercells_R1"

OLD_MANIFEST = RESULTS / "supercell_manifest_step05A.json"
OLD_DECISION = RESULTS / "decisao_step05A.json"

HOSTS = {
    "calcita": (
        RESULTS
        / "hosts_relaxed"
        / "calcita_PBEsol1400_relaxed.traj"
    ),
    "dolomita": (
        RESULTS
        / "hosts_relaxed"
        / "dolomita_PBEsol1400_relaxed.traj"
    ),
}

DETERMINANTS = (8, 16, 24)

SUPERCELLS.mkdir(parents=True, exist_ok=True)

for path in [OLD_MANIFEST, OLD_DECISION, *HOSTS.values()]:
    if not path.exists():
        raise FileNotFoundError(path)

old_manifest = json.loads(
    OLD_MANIFEST.read_text(encoding="utf-8")
)
old_decision = json.loads(
    OLD_DECISION.read_text(encoding="utf-8")
)


def divisors(n: int):
    return [d for d in range(1, n + 1) if n % d == 0]


def enumerate_hnf(det: int):
    """Todas as HNF 3D upper-triangular com determinante positivo det."""
    for a in divisors(det):
        rem = det // a
        for d in divisors(rem):
            f = rem // d
            for b in range(d):
                for c in range(f):
                    for e in range(f):
                        yield np.array(
                            [
                                [a, b, c],
                                [0, d, e],
                                [0, 0, f],
                            ],
                            dtype=int,
                        )


def compact_candidate(P: np.ndarray, primitive_cell: np.ndarray):
    raw_cell = P @ primitive_cell

    # Redução exata da base da rede. Segundo a API ASE, rcell é uma base
    # Minkowski-reduzida e op é unimodular:
    #     rcell = op @ raw_cell
    rcell, op = minkowski_reduce(raw_cell, pbc=True)
    rcell = np.asarray(rcell, dtype=float)
    op = np.asarray(op, dtype=int)

    P_reduced = op @ P

    det_reduced = int(round(np.linalg.det(P_reduced)))
    if det_reduced < 0:
        P_reduced[0] *= -1
        rcell[0] *= -1
        det_reduced = -det_reduced

    if det_reduced != int(round(np.linalg.det(P))):
        raise RuntimeError(
            f"Determinante alterado pela redução: "
            f"{np.linalg.det(P)} -> {det_reduced}"
        )

    if not is_minkowski_reduced(rcell, pbc=True):
        raise RuntimeError("ASE não reconheceu a célula final como reduzida.")

    lengths = np.linalg.norm(rcell, axis=1)
    shortest = float(np.min(lengths))
    anisotropy = float(np.max(lengths) / np.min(lengths))

    volume = abs(float(np.linalg.det(rcell)))
    scale2 = volume ** (2.0 / 3.0)
    gram = rcell @ rcell.T

    # Desvio métrico adimensional em relação a uma célula ortogonal
    # isotrópica de mesmo volume. Usado somente para desempate.
    metric_deviation = float(
        np.linalg.norm(
            gram / scale2 - np.eye(3)
        )
    )

    angles = Cell(rcell).angles()

    return {
        "P_raw": P,
        "P_reduced": P_reduced,
        "rcell": rcell,
        "shortest": shortest,
        "lengths": lengths,
        "angles": angles,
        "anisotropy": anisotropy,
        "metric_deviation": metric_deviation,
    }


manifest = {
    "step": "05A-R1-supercell-design",
    "reason_for_revision": (
        "The original Step05A ranked highly sheared HNF bases using a "
        "short lattice-vector search restricted to integer coefficients "
        "[-2,2].  For the det=16/24 cells this produced basis vectors of "
        "tens to >100 A and made the minimum-image estimate unsafe. "
        "R1 ranks the lattice only after exact ASE Minkowski reduction."
    ),
    "method": {
        "enumeration": "all 3D HNF sublattices for determinants 8,16,24",
        "reduction": "ase.geometry.minkowski_reduce",
        "primary_score": "maximize shortest vector of Minkowski-reduced basis",
        "tie_break": "minimize normalized metric deviation",
    },
    "hosts": {},
}

for mineral, host_path in HOSTS.items():
    atoms = read(host_path)
    primitive_cell = np.asarray(atoms.cell, dtype=float)

    host_out = {
        "primitive_natoms": len(atoms),
        "candidates": [],
    }

    for det in DETERMINANTS:
        best = None
        ntested = 0

        for P in enumerate_hnf(det):
            cand = compact_candidate(P, primitive_cell)
            ntested += 1

            # Arredondar a distância evita que ruído ~1e-14 decida
            # entre redes degeneradas.
            key = (
                round(cand["shortest"], 10),
                -cand["metric_deviation"],
            )

            if best is None or key > best["key"]:
                best = {
                    "key": key,
                    **cand,
                }

        P_final = best["P_reduced"]
        sc = make_supercell(
            atoms,
            P_final,
            wrap=True,
        )

        expected_natoms = len(atoms) * det
        if len(sc) != expected_natoms:
            raise RuntimeError(
                f"{mineral} det={det}: "
                f"{len(sc)} átomos != {expected_natoms}"
            )

        # make_supercell deve gerar a mesma métrica reduzida.
        final_cell = np.asarray(sc.cell, dtype=float)
        reduced_check, _ = minkowski_reduce(final_cell, pbc=True)
        reduced_check = np.asarray(reduced_check, dtype=float)
        check_lengths = np.linalg.norm(reduced_check, axis=1)

        shortest_check = float(np.min(check_lengths))
        if abs(shortest_check - best["shortest"]) > 1.0e-8:
            raise RuntimeError(
                f"{mineral} det={det}: verificação da menor "
                "translação falhou."
            )

        traj = (
            SUPERCELLS
            / f"{mineral}_det{det}_{len(sc)}atoms_R1.traj"
        )
        cif = (
            SUPERCELLS
            / f"{mineral}_det{det}_{len(sc)}atoms_R1.cif"
        )

        write(traj, sc)
        write(cif, sc)

        old_candidate = next(
            x
            for x in old_manifest["hosts"][mineral]["candidates"]
            if int(x["determinant"]) == det
        )

        host_out["candidates"].append({
            "determinant": det,
            "natoms": len(sc),
            "hnf_candidates_tested": ntested,
            "raw_HNF_matrix": best["P_raw"].tolist(),
            "minkowski_reduced_matrix": P_final.tolist(),
            "shortest_periodic_translation_A":
                best["shortest"],
            "reduced_cell_vector_lengths_A":
                [float(x) for x in best["lengths"]],
            "reduced_cell_angles_deg":
                [float(x) for x in best["angles"]],
            "reduced_basis_anisotropy":
                best["anisotropy"],
            "metric_deviation":
                best["metric_deviation"],
            "is_minkowski_reduced": True,
            "old_step05A": {
                "matrix": old_candidate["matrix"],
                "reported_shortest_translation_A":
                    old_candidate[
                        "shortest_periodic_translation_A"
                    ],
                "reported_basis_vector_lengths_A":
                    old_candidate["cell_vector_lengths_A"],
            },
            "traj": str(traj),
            "cif": str(cif),
        })

    manifest["hosts"][mineral] = host_out

manifest_path = RESULTS / "supercell_manifest_step05A_R1.json"
manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

hosts_decision = {}
overall = bool(old_decision.get("step05A_passes", False))

for mineral, data in manifest["hosts"].items():
    candidates = data["candidates"]

    monotonic = all(
        candidates[i + 1]["shortest_periodic_translation_A"]
        >= candidates[i]["shortest_periodic_translation_A"] - 1.0e-8
        for i in range(len(candidates) - 1)
    )

    compact = all(
        x["reduced_basis_anisotropy"] <= 2.0
        for x in candidates
    )

    valid = monotonic and compact
    overall = overall and valid

    hosts_decision[mineral] = {
        "host_gate_from_original_step05A": (
            old_decision["hosts"][mineral][
                "host_relaxation_passes"
            ]
        ),
        "supercell_geometry_gate_passes": valid,
        "shortest_translation_monotonic": monotonic,
        "all_reduced_basis_anisotropy_le_2": compact,
        "selected_for_step05B": candidates[:2],
        "fallback": candidates[2],
    }

decision = {
    "step": "05A-R1",
    "purpose": (
        "Correct and validate the periodic supercell lattice geometry "
        "before any Pb/U defect DFT calculation."
    ),
    "original_host_relaxation_step05A_passes":
        bool(old_decision.get("step05A_passes", False)),
    "hosts": hosts_decision,
    "step05A_R1_passes": bool(overall),
    "ready_for_step05B": bool(overall),
    "defect_DFT_executed_in_this_patch": False,
    "next_gate": (
        "Step05B: Pb2+ on Ca2+ neutral substitution finite-size gate "
        "using the R1 80- and 160-atom supercells.  The 240-atom cell "
        "is used only if 80->160 atoms is not converged."
    ),
}

(RESULTS / "decisao_step05A_R1.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 05A-R1 — SUPERCÉLULAS MINKOWSKI-REDUZIDAS")
print("=" * 80)

for mineral, data in manifest["hosts"].items():
    print(f"\n{mineral.upper()}")
    for c in data["candidates"]:
        print(
            f"  det={c['determinant']:2d} "
            f"N={c['natoms']:3d} "
            f"dmin={c['shortest_periodic_translation_A']:.6f} A "
            f"anis={c['reduced_basis_anisotropy']:.4f}"
        )

print()
print(
    "STEP05A-R1:",
    "APROVADO" if overall else "REPROVADO",
)
print(
    "READY FOR STEP05B:",
    bool(overall),
)
print("=" * 80)

if not overall:
    raise SystemExit(62)
