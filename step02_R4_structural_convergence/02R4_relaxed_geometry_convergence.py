#!/usr/bin/env python3
"""
STEP 02-R4 — Convergência estrutural observável.

Em vez de perseguir indefinidamente a componente hidrostática do stress
em uma estrutura experimental fora do mínimo PBE, esta etapa compara
diretamente as geometrias relaxadas em 1000, 1200 e 1400 eV.

Para cada mineral/cutoff:
1. parte preferencialmente da estrutura pré-relaxada por MACE;
2. relaxa célula + posições com FrechetCellFilter;
3. verifica/refina posições com célula fixa;
4. grava estrutura final, energia, forças, stress e métricas de ligação.

A decisão automática compara 1200 eV contra 1400 eV.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from ase.filters import FrechetCellFilter
from ase.io import read, write
from ase.optimize import BFGS
from gpaw import GPAW, PW
from gpaw.mpi import world
from gpaw.setup_data import SetupData

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step02_R4 import (
    ECUT_VALUES_EV,
    FMAX_ATOMS_EV_A,
    FMAX_FULL_EV_A,
    FERMI_WIDTH_EV,
    KGRID,
    MAX_BOND_DIFF_A,
    MAX_LATTICE_REL_DIFF_PCT,
    MAX_STEPS_ATOMS,
    MAX_STEPS_FULL,
    MAX_VOLUME_REL_DIFF_PCT,
    OUT_DIR,
    SYSTEMS,
    XC,
)

EV_A3_TO_GPA = 160.21766208


def verify_paw_datasets() -> None:
    for symbol in ("Ca", "C", "O", "Mg"):
        data = SetupData.find_and_read_path(
            symbol,
            "PBE",
            setuptype="paw",
            world=world,
        )
        if world.rank == 0:
            print(
                f"[PAW] {symbol}.PBE: OK -> "
                f"{getattr(data, 'filename', 'localizado')}",
                flush=True,
            )


def choose_start(mineral: str) -> Path:
    mace = SYSTEMS[mineral]["mace"]
    experimental = SYSTEMS[mineral]["experimental"]

    if mace.exists():
        return mace
    if experimental.exists():
        return experimental

    raise FileNotFoundError(
        f"Nenhuma estrutura inicial encontrada para {mineral}."
    )


def calc_kwargs(ecut: int, txt: Path) -> dict:
    return {
        "mode": PW(ecut, dedecut="estimate"),
        "xc": XC,
        "kpts": {"size": (KGRID, KGRID, KGRID), "gamma": True},
        "occupations": {"name": "fermi-dirac", "width": FERMI_WIDTH_EV},
        "convergence": {
            "density": 1.0e-6,
            "forces": 1.0e-4,
        },
        "txt": str(txt),
    }


def max_force(atoms) -> float:
    forces = np.asarray(atoms.get_forces(), dtype=float)
    return float(np.linalg.norm(forces, axis=1).max())


def stress_data(atoms) -> tuple[list[float], float, float]:
    stress = np.asarray(atoms.get_stress(voigt=True), dtype=float)
    stress_gpa = stress * EV_A3_TO_GPA
    mean_diag = float(np.mean(stress_gpa[:3]))
    return (
        [float(x) for x in stress_gpa],
        float(np.max(np.abs(stress_gpa))),
        mean_diag,
    )


def element_symbols(atoms) -> set[str]:
    return set(atoms.get_chemical_symbols())


def nearest_bond_stats(atoms, central: str, n_neighbors: int) -> dict:
    syms = atoms.get_chemical_symbols()
    o_indices = [i for i, s in enumerate(syms) if s == "O"]

    values = []
    for i, s in enumerate(syms):
        if s != central:
            continue
        dists = sorted(atoms.get_distance(i, j, mic=True) for j in o_indices)
        values.extend(dists[:n_neighbors])

    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return {
            f"{central}_O_min_A": np.nan,
            f"{central}_O_mean_A": np.nan,
            f"{central}_O_max_A": np.nan,
        }

    return {
        f"{central}_O_min_A": float(arr.min()),
        f"{central}_O_mean_A": float(arr.mean()),
        f"{central}_O_max_A": float(arr.max()),
    }


def cell_metrics(atoms) -> dict:
    lengths = atoms.cell.lengths()
    angles = atoms.cell.angles()
    return {
        "a_A": float(lengths[0]),
        "b_A": float(lengths[1]),
        "c_A": float(lengths[2]),
        "alpha_deg": float(angles[0]),
        "beta_deg": float(angles[1]),
        "gamma_deg": float(angles[2]),
        "volume_A3": float(atoms.get_volume()),
    }


def result_path(mineral: str, ecut: int) -> Path:
    return OUT_DIR / f"{mineral}_PBE_{ecut}eV_final.cif"


def row_path(mineral: str, ecut: int) -> Path:
    return OUT_DIR / f"{mineral}_PBE_{ecut}eV_summary.json"


def load_cached_row(mineral: str, ecut: int) -> dict | None:
    path = row_path(mineral, ecut)
    cif = result_path(mineral, ecut)
    if not (path.exists() and cif.exists()):
        return None

    with path.open(encoding="utf-8") as f:
        return json.load(f)


def run_relaxation(mineral: str, ecut: int) -> dict:
    cached = load_cached_row(mineral, ecut)
    if cached is not None:
        if world.rank == 0:
            print(
                f"[{mineral}] {ecut} eV: reutilizando resultado completo",
                flush=True,
            )
        world.barrier()
        return cached

    start_path = choose_start(mineral)
    atoms = read(start_path)

    full_txt = OUT_DIR / f"{mineral}_{ecut}eV_full_relax.txt"
    atoms.calc = GPAW(**calc_kwargs(ecut, full_txt))

    full_log = OUT_DIR / f"{mineral}_{ecut}eV_full_relax.log"
    full_traj = OUT_DIR / f"{mineral}_{ecut}eV_full_relax.traj"

    filt = FrechetCellFilter(atoms)
    opt = BFGS(
        filt,
        logfile=str(full_log),
        trajectory=str(full_traj),
    )

    if world.rank == 0:
        print(
            f"[{mineral}] {ecut} eV: relaxação célula + átomos "
            f"(fmax={FMAX_FULL_EV_A} eV/Å)",
            flush=True,
        )

    t0 = time.perf_counter()
    opt.run(
        fmax=FMAX_FULL_EV_A,
        steps=MAX_STEPS_FULL,
    )

    # Verificação/refinamento com célula fixa.
    atoms.calc = GPAW(
        **calc_kwargs(
            ecut,
            OUT_DIR / f"{mineral}_{ecut}eV_atoms_verify.txt",
        )
    )

    opt_atoms = BFGS(
        atoms,
        logfile=str(OUT_DIR / f"{mineral}_{ecut}eV_atoms_verify.log"),
        trajectory=str(OUT_DIR / f"{mineral}_{ecut}eV_atoms_verify.traj"),
    )
    opt_atoms.run(
        fmax=FMAX_ATOMS_EV_A,
        steps=MAX_STEPS_ATOMS,
    )

    energy = float(atoms.get_potential_energy())
    fmax = max_force(atoms)
    stress, smax, mean_stress = stress_data(atoms)

    elapsed = time.perf_counter() - t0

    out_cif = result_path(mineral, ecut)
    write(out_cif, atoms, format="cif")

    row = {
        "mineral": mineral,
        "xc": XC,
        "ecut_eV": int(ecut),
        "kgrid": int(KGRID),
        "n_atoms": len(atoms),
        "start_file": str(start_path),
        "energy_eV": energy,
        "energy_eV_atom": energy / len(atoms),
        "fmax_eV_A": fmax,
        "stress_xx_GPa": stress[0],
        "stress_yy_GPa": stress[1],
        "stress_zz_GPa": stress[2],
        "stress_yz_GPa": stress[3],
        "stress_xz_GPa": stress[4],
        "stress_xy_GPa": stress[5],
        "stress_max_abs_GPa": smax,
        "stress_mean_diag_GPa": mean_stress,
        "full_relax_steps": int(opt.nsteps),
        "atoms_verify_steps": int(opt_atoms.nsteps),
        "tempo_s": elapsed,
        "final_cif": out_cif.name,
        **cell_metrics(atoms),
    }

    syms = element_symbols(atoms)
    for central, nneigh in (("Ca", 6), ("Mg", 6), ("C", 3)):
        if central in syms:
            row.update(nearest_bond_stats(atoms, central, nneigh))

    if world.rank == 0:
        row_path(mineral, ecut).write_text(
            json.dumps(row, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    world.barrier()
    return row


def rel_pct(a: float, b: float) -> float:
    return abs(a - b) / abs(b) * 100.0


def compare_1200_1400(rows: list[dict], mineral: str) -> dict:
    by_ecut = {
        int(r["ecut_eV"]): r
        for r in rows
        if r["mineral"] == mineral
    }

    r12 = by_ecut[1200]
    r14 = by_ecut[1400]

    lattice_diffs = [
        rel_pct(float(r12[key]), float(r14[key]))
        for key in ("a_A", "b_A", "c_A")
    ]
    angle_diffs = [
        abs(float(r12[key]) - float(r14[key]))
        for key in ("alpha_deg", "beta_deg", "gamma_deg")
    ]

    bond_keys = [
        key for key in r12
        if key.endswith("_O_mean_A") and key in r14
    ]
    bond_diffs = {
        key: abs(float(r12[key]) - float(r14[key]))
        for key in bond_keys
    }

    max_bond = max(bond_diffs.values()) if bond_diffs else 0.0

    result = {
        "mineral": mineral,
        "ecut_candidato_eV": 1200,
        "ecut_referencia_eV": 1400,
        "max_lattice_rel_diff_pct": max(lattice_diffs),
        "volume_rel_diff_pct": rel_pct(
            float(r12["volume_A3"]),
            float(r14["volume_A3"]),
        ),
        "max_angle_diff_deg": max(angle_diffs),
        "max_bond_mean_diff_A": max_bond,
        "criterion_lattice_pct": MAX_LATTICE_REL_DIFF_PCT,
        "criterion_volume_pct": MAX_VOLUME_REL_DIFF_PCT,
        "criterion_bond_A": MAX_BOND_DIFF_A,
    }

    result["passes"] = bool(
        result["max_lattice_rel_diff_pct"] <= MAX_LATTICE_REL_DIFF_PCT
        and result["volume_rel_diff_pct"] <= MAX_VOLUME_REL_DIFF_PCT
        and result["max_bond_mean_diff_A"] <= MAX_BOND_DIFF_A
    )

    return result


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
    OUT_DIR.mkdir(exist_ok=True)
    verify_paw_datasets()

    if world.size != 4:
        raise RuntimeError(
            f"Step 02-R4 requer 4 processos MPI; world.size={world.size}."
        )

    if world.rank == 0:
        print("=" * 84)
        print("STEP 02-R4 — CONVERGÊNCIA DAS GEOMETRIAS RELAXADAS")
        print("=" * 84)
        print("Cutoffs:", ECUT_VALUES_EV)
        print("k-grid:", f"{KGRID}x{KGRID}x{KGRID}")
        print("XC:", XC)
        print("Pulay correction: dedecut='estimate'")
        print("Start preferencial: MACE")
        print("=" * 84)

    rows = []
    for mineral in SYSTEMS:
        for ecut in ECUT_VALUES_EV:
            rows.append(run_relaxation(mineral, ecut))

    if world.rank == 0:
        save_csv(rows, OUT_DIR / "geometrias_relaxadas_R4.csv")

        decisions = [
            compare_1200_1400(rows, mineral)
            for mineral in SYSTEMS
        ]
        save_csv(
            decisions,
            OUT_DIR / "convergencia_estrutural_1200_vs_1400.csv",
        )

        common_pass = all(d["passes"] for d in decisions)

        final = {
            "xc": XC,
            "kgrid_primitiva": [KGRID, KGRID, KGRID],
            "candidate_cutoff_eV": 1200,
            "reference_cutoff_eV": 1400,
            "all_systems_pass": common_pass,
            "criteria": {
                "max_lattice_rel_diff_pct": MAX_LATTICE_REL_DIFF_PCT,
                "max_volume_rel_diff_pct": MAX_VOLUME_REL_DIFF_PCT,
                "max_bond_mean_diff_A": MAX_BOND_DIFF_A,
            },
            "individual": decisions,
        }

        (OUT_DIR / "decisao_step02_R4.json").write_text(
            json.dumps(final, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\n" + "=" * 84)
        print("STEP 02-R4 CONCLUÍDO")
        for d in decisions:
            print(
                f"{d['mineral']}: 1200 vs 1400 eV -> "
                f"{'APROVADO' if d['passes'] else 'NÃO APROVADO'}"
            )
        print(
            "Decisão comum:",
            "1200 eV pode ser adotado"
            if common_pass
            else "necessária revisão adicional",
        )
        print("=" * 84)


if __name__ == "__main__":
    main()
