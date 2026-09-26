#!/usr/bin/env python3
"""
STEP 03 — Validação dos PAWs gerados e benchmark PBE/PBEsol.

Gate científico:
1. Os PAWs PBE gerados com gpaw-setup devem reproduzir a geometria obtida
   com os PAWs PBE oficiais do GPAW.
2. Somente se calcita e dolomita passarem esse gate, o benchmark PBEsol
   é executado.
3. PBEsol é testado em 1400 e 1600 eV para verificar a convergência
   estrutural com os mesmos critérios do Step 02.
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
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step03 import (
    ECUT_MAIN_EV,
    ECUT_VALIDATION_EV,
    FERMI_WIDTH_EV,
    FMAX_ATOMS_EV_A,
    FMAX_CELL_EV_A,
    KGRID,
    MAX_BOND_DIFF_A,
    MAX_LATTICE_REL_DIFF_PCT,
    MAX_STEPS_ATOMS,
    MAX_STEPS_CELL,
    MAX_VOLUME_REL_DIFF_PCT,
    OUT_DIR,
    PAW_PBE,
    PAW_PBESOL,
    SYSTEMS,
)

EV_A3_TO_GPA = 160.21766208
ORIGINAL_SETUP_PATHS = list(setup_paths)


def validate_inputs() -> None:
    missing = []

    for mineral, paths in SYSTEMS.items():
        for label, path in paths.items():
            if not path.exists():
                missing.append(f"{mineral}/{label}: {path}")

    for directory, xc in ((PAW_PBE, "PBE"), (PAW_PBESOL, "PBEsol")):
        for element in ("Ca", "Mg", "C", "O"):
            plain = directory / f"{element}.{xc}"
            gz = directory / f"{element}.{xc}.gz"
            if not (plain.exists() or gz.exists()):
                missing.append(f"PAW {element}.{xc}: {directory}")

    if missing:
        raise FileNotFoundError(
            "Entradas necessárias não encontradas:\n  "
            + "\n  ".join(missing)
        )


def set_generated_setup_path(directory: Path) -> None:
    setup_paths[:] = [str(directory)] + [
        path for path in ORIGINAL_SETUP_PATHS
        if str(path) != str(directory)
    ]


def calculator(xc: str, ecut: int, setup_dir: Path, txt: Path) -> GPAW:
    set_generated_setup_path(setup_dir)

    return GPAW(
        mode=PW(ecut, dedecut="estimate"),
        xc=xc,
        kpts={"size": (KGRID, KGRID, KGRID), "gamma": True},
        occupations={"name": "fermi-dirac", "width": FERMI_WIDTH_EV},
        convergence={
            "density": 1.0e-6,
            "forces": 1.0e-4,
        },
        txt=str(txt),
    )


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


def max_force(atoms) -> float:
    forces = np.asarray(atoms.get_forces(), dtype=float)
    return float(np.linalg.norm(forces, axis=1).max())


def stress_metrics(atoms) -> dict:
    stress = np.asarray(atoms.get_stress(voigt=True), dtype=float)
    gpa = stress * EV_A3_TO_GPA
    return {
        "stress_xx_GPa": float(gpa[0]),
        "stress_yy_GPa": float(gpa[1]),
        "stress_zz_GPa": float(gpa[2]),
        "stress_yz_GPa": float(gpa[3]),
        "stress_xz_GPa": float(gpa[4]),
        "stress_xy_GPa": float(gpa[5]),
        "stress_max_abs_GPa": float(np.max(np.abs(gpa))),
        "stress_mean_diag_GPa": float(np.mean(gpa[:3])),
    }


def nearest_bond_stats(atoms, central: str, n_neighbors: int) -> dict:
    symbols = atoms.get_chemical_symbols()
    o_indices = [i for i, symbol in enumerate(symbols) if symbol == "O"]

    values = []
    for i, symbol in enumerate(symbols):
        if symbol != central:
            continue

        dists = sorted(
            atoms.get_distance(i, j, mic=True)
            for j in o_indices
        )
        values.extend(dists[:n_neighbors])

    if not values:
        return {}

    arr = np.asarray(values, dtype=float)
    return {
        f"{central}_O_min_A": float(arr.min()),
        f"{central}_O_mean_A": float(arr.mean()),
        f"{central}_O_max_A": float(arr.max()),
    }


def geometry_metrics(path: Path) -> dict:
    atoms = read(path)
    row = {
        **cell_metrics(atoms),
    }

    symbols = set(atoms.get_chemical_symbols())
    for central, n in (("Ca", 6), ("Mg", 6), ("C", 3)):
        if central in symbols:
            row.update(nearest_bond_stats(atoms, central, n))

    return row


def summary_json(mineral: str, label: str) -> Path:
    return OUT_DIR / f"{mineral}_{label}_summary.json"


def final_cif(mineral: str, label: str) -> Path:
    return OUT_DIR / f"{mineral}_{label}_final.cif"


def load_cached(mineral: str, label: str) -> dict | None:
    js = summary_json(mineral, label)
    cif = final_cif(mineral, label)

    if not (js.exists() and cif.exists()):
        return None

    with js.open(encoding="utf-8") as f:
        return json.load(f)


def relax(
    *,
    mineral: str,
    label: str,
    xc: str,
    ecut: int,
    setup_dir: Path,
    start_path: Path,
) -> dict:
    cached = load_cached(mineral, label)
    if cached is not None:
        if world.rank == 0:
            print(f"[{mineral}] {label}: reutilizando resultado.", flush=True)
        world.barrier()
        return cached

    atoms = read(start_path)
    t0 = time.perf_counter()

    atoms.calc = calculator(
        xc,
        ecut,
        setup_dir,
        OUT_DIR / f"{mineral}_{label}_cell.txt",
    )

    filt = FrechetCellFilter(atoms)
    opt_cell = BFGS(
        filt,
        logfile=str(OUT_DIR / f"{mineral}_{label}_cell.log"),
        trajectory=str(OUT_DIR / f"{mineral}_{label}_cell.traj"),
    )

    if world.rank == 0:
        print(
            f"[{mineral}] {label}: XC={xc}, ecut={ecut} eV, "
            f"k={KGRID}x{KGRID}x{KGRID}",
            flush=True,
        )

    opt_cell.run(
        fmax=FMAX_CELL_EV_A,
        steps=MAX_STEPS_CELL,
    )

    atoms.calc = calculator(
        xc,
        ecut,
        setup_dir,
        OUT_DIR / f"{mineral}_{label}_atoms.txt",
    )

    opt_atoms = BFGS(
        atoms,
        logfile=str(OUT_DIR / f"{mineral}_{label}_atoms.log"),
        trajectory=str(OUT_DIR / f"{mineral}_{label}_atoms.traj"),
    )
    opt_atoms.run(
        fmax=FMAX_ATOMS_EV_A,
        steps=MAX_STEPS_ATOMS,
    )

    energy = float(atoms.get_potential_energy())
    elapsed = time.perf_counter() - t0

    out_cif = final_cif(mineral, label)
    write(out_cif, atoms, format="cif")

    row = {
        "mineral": mineral,
        "label": label,
        "xc": xc,
        "ecut_eV": int(ecut),
        "kgrid": int(KGRID),
        "setup_dir": str(setup_dir),
        "start_file": str(start_path),
        "n_atoms": len(atoms),
        "energy_eV": energy,
        "energy_eV_atom": energy / len(atoms),
        "fmax_eV_A": max_force(atoms),
        "cell_relax_steps": int(opt_cell.nsteps),
        "atoms_relax_steps": int(opt_atoms.nsteps),
        "tempo_s": float(elapsed),
        "final_cif": out_cif.name,
        **cell_metrics(atoms),
        **stress_metrics(atoms),
    }

    symbols = set(atoms.get_chemical_symbols())
    for central, n in (("Ca", 6), ("Mg", 6), ("C", 3)):
        if central in symbols:
            row.update(nearest_bond_stats(atoms, central, n))

    if world.rank == 0:
        summary_json(mineral, label).write_text(
            json.dumps(row, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    world.barrier()
    return row


def rel_diff_pct(a: float, b: float) -> float:
    return abs(float(a) - float(b)) / abs(float(b)) * 100.0


def compare_geometries(
    *,
    mineral: str,
    candidate: dict,
    reference: dict,
    candidate_label: str,
    reference_label: str,
) -> dict:
    lattice_diffs = [
        rel_diff_pct(candidate[key], reference[key])
        for key in ("a_A", "b_A", "c_A")
    ]
    angle_diffs = [
        abs(float(candidate[key]) - float(reference[key]))
        for key in ("alpha_deg", "beta_deg", "gamma_deg")
    ]

    bond_keys = sorted(
        key for key in candidate
        if key.endswith("_O_mean_A") and key in reference
    )
    bond_diffs = {
        key: abs(float(candidate[key]) - float(reference[key]))
        for key in bond_keys
    }

    result = {
        "mineral": mineral,
        "candidate": candidate_label,
        "reference": reference_label,
        "max_lattice_rel_diff_pct": max(lattice_diffs),
        "volume_rel_diff_pct": rel_diff_pct(
            candidate["volume_A3"],
            reference["volume_A3"],
        ),
        "max_angle_diff_deg": max(angle_diffs),
        "max_bond_mean_diff_A": (
            max(bond_diffs.values()) if bond_diffs else 0.0
        ),
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


def accuracy_vs_experiment(
    mineral: str,
    method_label: str,
    metrics: dict,
) -> dict:
    exp = geometry_metrics(SYSTEMS[mineral]["experimental"])

    row = {
        "mineral": mineral,
        "metodo": method_label,
        "a_error_pct": (
            (float(metrics["a_A"]) - exp["a_A"]) / exp["a_A"] * 100.0
        ),
        "b_error_pct": (
            (float(metrics["b_A"]) - exp["b_A"]) / exp["b_A"] * 100.0
        ),
        "c_error_pct": (
            (float(metrics["c_A"]) - exp["c_A"]) / exp["c_A"] * 100.0
        ),
        "volume_error_pct": (
            (float(metrics["volume_A3"]) - exp["volume_A3"])
            / exp["volume_A3"]
            * 100.0
        ),
    }

    bond_abs_errors = []
    for key in metrics:
        if key.endswith("_O_mean_A") and key in exp:
            value = abs(float(metrics[key]) - float(exp[key]))
            row[f"{key}_abs_error_A"] = value
            bond_abs_errors.append(value)

    row["max_bond_mean_abs_error_A"] = (
        max(bond_abs_errors) if bond_abs_errors else 0.0
    )
    row["mean_abs_lattice_error_pct"] = float(
        np.mean(
            [
                abs(row["a_error_pct"]),
                abs(row["b_error_pct"]),
                abs(row["c_error_pct"]),
            ]
        )
    )
    return row


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return

    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    validate_inputs()

    if world.size != 4:
        raise RuntimeError(
            f"Step 03 requer 4 processos MPI; world.size={world.size}."
        )

    if world.rank == 0:
        print("=" * 88)
        print("STEP 03 — VALIDAÇÃO PAW + BENCHMARK PBE/PBEsol")
        print("=" * 88)
        print("MPI world size:", world.size)
        print("PBE gerado:", PAW_PBE)
        print("PBEsol gerado:", PAW_PBESOL)
        print("ecut principal:", ECUT_MAIN_EV, "eV")
        print("ecut de validação:", ECUT_VALIDATION_EV, "eV")
        print("k-grid:", f"{KGRID}x{KGRID}x{KGRID}")
        print("=" * 88)

    generated_pbe_rows = []
    pbe_gate_rows = []

    # -----------------------------------------------------------------
    # Gate 1: PBE gerado deve reproduzir o PBE oficial do Step 02.
    # -----------------------------------------------------------------
    for mineral in SYSTEMS:
        generated = relax(
            mineral=mineral,
            label="PBE_generated_1400",
            xc="PBE",
            ecut=ECUT_MAIN_EV,
            setup_dir=PAW_PBE,
            start_path=SYSTEMS[mineral]["pbe_official_1400"],
        )
        generated_pbe_rows.append(generated)

        official_metrics = geometry_metrics(
            SYSTEMS[mineral]["pbe_official_1400"]
        )

        gate = compare_geometries(
            mineral=mineral,
            candidate=generated,
            reference=official_metrics,
            candidate_label="PBE_generated_1400",
            reference_label="PBE_official_1400",
        )
        pbe_gate_rows.append(gate)

        if world.rank == 0:
            print(
                f"[GATE PBE] {mineral}: "
                f"{'APROVADO' if gate['passes'] else 'REPROVADO'}",
                flush=True,
            )

        world.barrier()

    pbe_gate_pass = all(row["passes"] for row in pbe_gate_rows)

    if world.rank == 0:
        save_csv(
            generated_pbe_rows,
            OUT_DIR / "PBE_generated_relaxed.csv",
        )
        save_csv(
            pbe_gate_rows,
            OUT_DIR / "validacao_PBE_generated_vs_official.csv",
        )

    if not pbe_gate_pass:
        if world.rank == 0:
            decision = {
                "paw_generated_pbe_validated": False,
                "pbesol_executed": False,
                "reason": (
                    "Os PAWs PBE gerados não reproduziram os PAWs PBE oficiais "
                    "dentro dos critérios estruturais. PBEsol não foi executado."
                ),
                "pbe_gate": pbe_gate_rows,
            }
            (OUT_DIR / "decisao_step03.json").write_text(
                json.dumps(decision, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print("\nGATE PBE REPROVADO.")
            print("PBEsol NÃO será executado.")
        return

    # -----------------------------------------------------------------
    # Gate 2: PBEsol 1400 vs 1600 eV.
    # -----------------------------------------------------------------
    pbesol_rows = []
    pbesol_conv_rows = []

    for mineral in SYSTEMS:
        r1400 = relax(
            mineral=mineral,
            label="PBEsol_generated_1400",
            xc="PBEsol",
            ecut=ECUT_MAIN_EV,
            setup_dir=PAW_PBESOL,
            start_path=SYSTEMS[mineral]["experimental"],
        )

        r1600 = relax(
            mineral=mineral,
            label="PBEsol_generated_1600",
            xc="PBEsol",
            ecut=ECUT_VALIDATION_EV,
            setup_dir=PAW_PBESOL,
            start_path=final_cif(mineral, "PBEsol_generated_1400"),
        )

        pbesol_rows.extend([r1400, r1600])

        conv = compare_geometries(
            mineral=mineral,
            candidate=r1400,
            reference=r1600,
            candidate_label="PBEsol_generated_1400",
            reference_label="PBEsol_generated_1600",
        )
        pbesol_conv_rows.append(conv)

        if world.rank == 0:
            print(
                f"[CONV PBEsol] {mineral}: 1400 vs 1600 -> "
                f"{'APROVADO' if conv['passes'] else 'REPROVADO'}",
                flush=True,
            )

        world.barrier()

    pbesol_converged = all(row["passes"] for row in pbesol_conv_rows)

    if world.rank == 0:
        save_csv(pbesol_rows, OUT_DIR / "PBEsol_relaxed_1400_1600.csv")
        save_csv(
            pbesol_conv_rows,
            OUT_DIR / "convergencia_PBEsol_1400_vs_1600.csv",
        )

        # -------------------------------------------------------------
        # Benchmark estrutural contra experimento.
        # -------------------------------------------------------------
        accuracy_rows = []

        for mineral in SYSTEMS:
            pbe_official = geometry_metrics(
                SYSTEMS[mineral]["pbe_official_1400"]
            )
            accuracy_rows.append(
                accuracy_vs_experiment(
                    mineral,
                    "PBE_official_1400",
                    pbe_official,
                )
            )

            pbesol_1400 = next(
                row for row in pbesol_rows
                if row["mineral"] == mineral
                and row["label"] == "PBEsol_generated_1400"
            )
            accuracy_rows.append(
                accuracy_vs_experiment(
                    mineral,
                    "PBEsol_generated_1400",
                    pbesol_1400,
                )
            )

        save_csv(
            accuracy_rows,
            OUT_DIR / "benchmark_PBE_vs_PBEsol_experimento.csv",
        )

        # Sugestão baseada em erro estrutural, sem substituir revisão humana.
        pbesol_better_for_all = True
        improvements = []

        for mineral in SYSTEMS:
            pbe = next(
                row for row in accuracy_rows
                if row["mineral"] == mineral
                and row["metodo"] == "PBE_official_1400"
            )
            pbesol = next(
                row for row in accuracy_rows
                if row["mineral"] == mineral
                and row["metodo"] == "PBEsol_generated_1400"
            )

            better = (
                abs(pbesol["volume_error_pct"]) < abs(pbe["volume_error_pct"])
                and pbesol["mean_abs_lattice_error_pct"]
                < pbe["mean_abs_lattice_error_pct"]
            )
            pbesol_better_for_all &= better

            improvements.append(
                {
                    "mineral": mineral,
                    "pbesol_better_lattice_and_volume": better,
                    "PBE_volume_error_pct": pbe["volume_error_pct"],
                    "PBEsol_volume_error_pct": pbesol["volume_error_pct"],
                    "PBE_mean_abs_lattice_error_pct": (
                        pbe["mean_abs_lattice_error_pct"]
                    ),
                    "PBEsol_mean_abs_lattice_error_pct": (
                        pbesol["mean_abs_lattice_error_pct"]
                    ),
                }
            )

        decision = {
            "paw_generator": "gpaw-setup (old generator)",
            "paw_generated_pbe_validated": pbe_gate_pass,
            "pbesol_executed": True,
            "pbesol_1400_vs_1600_converged": pbesol_converged,
            "pbesol_structurally_better_than_pbe_for_all_systems": (
                pbesol_better_for_all
            ),
            "suggested_matrix_functional": (
                "PBEsol"
                if pbesol_converged and pbesol_better_for_all
                else "REVISAR_RESULTADOS"
            ),
            "pbe_gate": pbe_gate_rows,
            "pbesol_convergence": pbesol_conv_rows,
            "improvement_vs_experiment": improvements,
            "warning": (
                "A validação realizada é específica para Ca-Mg-C-O nas fases "
                "calcita/dolomita. Ela não valida transferibilidade para U ou Pb."
            ),
        }

        (OUT_DIR / "decisao_step03.json").write_text(
            json.dumps(decision, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\n" + "=" * 88)
        print("STEP 03 CONCLUÍDO")
        print("PAW PBE gerado:", "APROVADO")
        print(
            "PBEsol 1400 vs 1600:",
            "APROVADO" if pbesol_converged else "REPROVADO",
        )
        print(
            "Sugestão preliminar:",
            decision["suggested_matrix_functional"],
        )
        print("=" * 88)


if __name__ == "__main__":
    main()
