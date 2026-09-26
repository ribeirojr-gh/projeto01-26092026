#!/usr/bin/env python3
"""
STEP 02B — Convergência de energia de corte e malha k com GPAW/PBEsol.

Executar com:
    mpiexec -n 4 gpaw python 02B_gpaw_convergence.py

Esta etapa NÃO relaxa a estrutura por DFT. Ela determina parâmetros
numéricos para a relaxação DFT da próxima etapa.
"""

from __future__ import annotations

import csv
import math
import time
from pathlib import Path

import numpy as np
from ase.io import read
from gpaw import GPAW, PW
from gpaw.mpi import world

from config_step02 import (
    ECUT_KGRID,
    ECUT_VALUES_EV,
    ENERGY_TOL_MEV_ATOM,
    FERMI_WIDTH_EV,
    GPAW_DIR,
    INPUT_SNAPSHOT,
    KGRID_ECUT_EV,
    KGRID_VALUES,
    STRESS_TOL_GPA,
    SYSTEMS,
    XC_CONVERGENCE,
)


EV_A3_TO_GPA = 160.21766208


def ensure_inputs() -> None:
    GPAW_DIR.mkdir(exist_ok=True)
    INPUT_SNAPSHOT.mkdir(exist_ok=True)

    for mineral, src in SYSTEMS.items():
        snap = INPUT_SNAPSHOT / f"{mineral}_experimental_primitiva.cif"
        if not snap.exists():
            if not src.exists():
                raise FileNotFoundError(
                    f"Não encontrei a estrutura de entrada para {mineral}: {src}"
                )
            snap.write_bytes(src.read_bytes())


def run_static(mineral: str, atoms, ecut: int, k: int, tag: str) -> dict:
    txt = GPAW_DIR / f"{mineral}_{tag}_ecut{ecut}_k{k}.txt"

    calc = GPAW(
        mode=PW(ecut),
        xc=XC_CONVERGENCE,
        kpts={"size": (k, k, k), "gamma": True},
        occupations={"name": "fermi-dirac", "width": FERMI_WIDTH_EV},
        convergence={"density": 1.0e-6},
        txt=str(txt),
    )
    atoms.calc = calc

    if world.rank == 0:
        print(
            f"[{mineral}] {tag}: ecut={ecut} eV | "
            f"k={k}x{k}x{k} | XC={XC_CONVERGENCE}",
            flush=True,
        )

    t0 = time.perf_counter()
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True)
    dt = time.perf_counter() - t0

    fmax = float(np.linalg.norm(forces, axis=1).max())
    stress_gpa = np.asarray(stress) * EV_A3_TO_GPA

    row = {
        "mineral": mineral,
        "scan": tag,
        "xc": XC_CONVERGENCE,
        "ecut_eV": int(ecut),
        "kgrid": int(k),
        "n_atoms": len(atoms),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "fmax_eV_A": fmax,
        "stress_xx_GPa": float(stress_gpa[0]),
        "stress_yy_GPa": float(stress_gpa[1]),
        "stress_zz_GPa": float(stress_gpa[2]),
        "stress_yz_GPa": float(stress_gpa[3]),
        "stress_xz_GPa": float(stress_gpa[4]),
        "stress_xy_GPa": float(stress_gpa[5]),
        "stress_max_abs_GPa": float(np.max(np.abs(stress_gpa))),
        "tempo_s": dt,
        "gpaw_txt": txt.name,
    }

    # Libera explicitamente a associação para reduzir uso de memória
    atoms.calc = None
    del calc
    world.barrier()

    return row


def stress_vector(row: dict) -> np.ndarray:
    return np.array(
        [
            row["stress_xx_GPa"],
            row["stress_yy_GPa"],
            row["stress_zz_GPa"],
            row["stress_yz_GPa"],
            row["stress_xz_GPa"],
            row["stress_xy_GPa"],
        ],
        dtype=float,
    )


def add_reference_deltas(rows: list[dict], scan: str) -> None:
    subset = [r for r in rows if r["scan"] == scan]
    if not subset:
        return

    if scan == "ecut":
        ref = max(subset, key=lambda r: r["ecut_eV"])
    else:
        ref = max(subset, key=lambda r: r["kgrid"])

    for row in subset:
        row["deltaE_ref_meV_atom"] = (
            abs(row["energy_eV_atom"] - ref["energy_eV_atom"]) * 1000.0
        )
        row["deltaStress_ref_GPa"] = float(
            np.max(np.abs(stress_vector(row) - stress_vector(ref)))
        )


def recommend(rows: list[dict], scan: str) -> int:
    subset = [r for r in rows if r["scan"] == scan]
    key = "ecut_eV" if scan == "ecut" else "kgrid"
    subset.sort(key=lambda r: r[key])

    for row in subset:
        if (
            row["deltaE_ref_meV_atom"] <= ENERGY_TOL_MEV_ATOM
            and row["deltaStress_ref_GPa"] <= STRESS_TOL_GPA
        ):
            return int(row[key])

    return int(subset[-1][key])


def save_csv(rows: list[dict], path: Path) -> None:
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ensure_inputs()

    if world.rank == 0:
        print("=" * 80)
        print("STEP 02B — CONVERGÊNCIA GPAW/PBEsol")
        print("=" * 80)
        print("MPI world size:", world.size)
        print("Cutoffs:", ECUT_VALUES_EV, "eV")
        print("k fixo no scan de cutoff:", ECUT_KGRID)
        print("k-grids:", KGRID_VALUES)
        print("cutoff fixo no scan k:", KGRID_ECUT_EV, "eV")
        print(
            "Critérios de recomendação:",
            f"{ENERGY_TOL_MEV_ATOM} meV/átomo e {STRESS_TOL_GPA} GPa",
        )
        print("=" * 80)

    if world.size != 4:
        raise RuntimeError(
            f"Esta etapa foi projetada para 4 processos MPI; world.size={world.size}."
        )

    all_rows: list[dict] = []
    recommendations: list[dict] = []

    for mineral in SYSTEMS:
        input_path = INPUT_SNAPSHOT / f"{mineral}_experimental_primitiva.cif"
        atoms0 = read(input_path)

        rows: list[dict] = []

        # Scan de energia de corte
        for ecut in ECUT_VALUES_EV:
            atoms = atoms0.copy()
            rows.append(
                run_static(
                    mineral,
                    atoms,
                    ecut=ecut,
                    k=ECUT_KGRID,
                    tag="ecut",
                )
            )

        # Scan de k-points. Quando o ponto (ecut, k) já foi calculado
        # no scan de cutoff, reutilizamos o resultado para evitar custo duplicado.
        for k in KGRID_VALUES:
            reusable = next(
                (
                    r for r in rows
                    if r["scan"] == "ecut"
                    and r["ecut_eV"] == KGRID_ECUT_EV
                    and r["kgrid"] == k
                ),
                None,
            )

            if reusable is not None:
                reused = dict(reusable)
                reused["scan"] = "kgrid"
                reused["gpaw_txt"] = reusable["gpaw_txt"] + " [reutilizado]"
                rows.append(reused)
                if world.rank == 0:
                    print(
                        f"[{mineral}] kgrid: reutilizando ecut={KGRID_ECUT_EV} eV, "
                        f"k={k}x{k}x{k}",
                        flush=True,
                    )
                continue

            atoms = atoms0.copy()
            rows.append(
                run_static(
                    mineral,
                    atoms,
                    ecut=KGRID_ECUT_EV,
                    k=k,
                    tag="kgrid",
                )
            )

        add_reference_deltas(rows, "ecut")
        add_reference_deltas(rows, "kgrid")

        if world.rank == 0:
            rec_ecut = recommend(rows, "ecut")
            rec_k = recommend(rows, "kgrid")
            recommendations.append(
                {
                    "mineral": mineral,
                    "xc": XC_CONVERGENCE,
                    "ecut_recomendado_eV": rec_ecut,
                    "kgrid_recomendado": rec_k,
                    "criterio_energia_meV_atom": ENERGY_TOL_MEV_ATOM,
                    "criterio_stress_GPa": STRESS_TOL_GPA,
                    "observacao": (
                        "Recomendação automática preliminar; revisar tabela "
                        "antes da relaxação DFT."
                    ),
                }
            )
            all_rows.extend(rows)

        world.barrier()

    if world.rank == 0:
        out = GPAW_DIR / "convergencia_gpaw.csv"
        save_csv(all_rows, out)
        rec = GPAW_DIR / "parametros_recomendados_gpaw.csv"
        save_csv(recommendations, rec)

        print("\nSTEP 02B concluído.")
        print("Convergência:", out)
        print("Recomendações:", rec)


if __name__ == "__main__":
    main()
