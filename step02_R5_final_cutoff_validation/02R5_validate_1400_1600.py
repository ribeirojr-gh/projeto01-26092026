#!/usr/bin/env python3
"""
STEP 02-R5 — Validação final 1400 versus 1600 eV.

O R4 rejeitou 1200 eV porque parâmetros de rede e volume ainda mudavam
mais do que os critérios definidos. As ligações locais já haviam passado.

Nesta etapa:
1. refina a geometria de 1400 eV produzida no R4 com tolerância mais rígida;
2. usa a geometria refinada de 1400 eV como ponto inicial de 1600 eV;
3. compara diretamente 1400 vs 1600 eV;
4. mantém os mesmos critérios estruturais do R4.
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

from config_step02_R5 import (
    ECUT_REFERENCE_EV,
    ECUT_TEST_EV,
    FMAX_ATOMS_EV_A,
    FMAX_CELL_EV_A,
    FERMI_WIDTH_EV,
    KGRID,
    MAX_BOND_DIFF_A,
    MAX_LATTICE_REL_DIFF_PCT,
    MAX_STEPS_ATOMS,
    MAX_STEPS_CELL,
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


def validate_inputs() -> None:
    missing = []
    for mineral, paths in SYSTEMS.items():
        for label, path in paths.items():
            if not path.exists():
                missing.append(f"{mineral}/{label}: {path}")
    if missing:
        raise FileNotFoundError(
            "Entradas necessárias não encontradas:\n  "
            + "\n  ".join(missing)
        )


def calculator(ecut: int, txt: Path) -> GPAW:
    return GPAW(
        mode=PW(ecut, dedecut="estimate"),
        xc=XC,
        kpts={"size": (KGRID, KGRID, KGRID), "gamma": True},
        occupations={"name": "fermi-dirac", "width": FERMI_WIDTH_EV},
        convergence={
            "density": 1.0e-6,
            "forces": 1.0e-4,
        },
        txt=str(txt),
    )


def max_force(atoms) -> float:
    f = np.asarray(atoms.get_forces(), dtype=float)
    return float(np.linalg.norm(f, axis=1).max())


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


def nearest_bond_stats(atoms, central: str, n_neighbors: int) -> dict:
    symbols = atoms.get_chemical_symbols()
    o_indices = [i for i, s in enumerate(symbols) if s == "O"]

    values = []
    for i, symbol in enumerate(symbols):
        if symbol != central:
            continue
        dists = sorted(
            atoms.get_distance(i, j, mic=True)
            for j in o_indices
        )
        values.extend(dists[:n_neighbors])

    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return {}

    return {
        f"{central}_O_min_A": float(arr.min()),
        f"{central}_O_mean_A": float(arr.mean()),
        f"{central}_O_max_A": float(arr.max()),
    }


def summary_path(mineral: str, ecut: int) -> Path:
    return OUT_DIR / f"{mineral}_PBE_{ecut}eV_R5_summary.json"


def final_cif_path(mineral: str, ecut: int) -> Path:
    return OUT_DIR / f"{mineral}_PBE_{ecut}eV_R5_final.cif"


def load_cached(mineral: str, ecut: int) -> dict | None:
    js = summary_path(mineral, ecut)
    cif = final_cif_path(mineral, ecut)

    if not (js.exists() and cif.exists()):
        return None

    with js.open(encoding="utf-8") as f:
        return json.load(f)


def relax(mineral: str, ecut: int, start_path: Path) -> dict:
    cached = load_cached(mineral, ecut)
    if cached is not None:
        if world.rank == 0:
            print(
                f"[{mineral}] {ecut} eV: reutilizando resultado R5",
                flush=True,
            )
        world.barrier()
        return cached

    atoms = read(start_path)
    t0 = time.perf_counter()

    atoms.calc = calculator(
        ecut,
        OUT_DIR / f"{mineral}_{ecut}eV_R5_cell.txt",
    )
    filt = FrechetCellFilter(atoms)
    opt_cell = BFGS(
        filt,
        logfile=str(OUT_DIR / f"{mineral}_{ecut}eV_R5_cell.log"),
        trajectory=str(OUT_DIR / f"{mineral}_{ecut}eV_R5_cell.traj"),
    )

    if world.rank == 0:
        print(
            f"[{mineral}] {ecut} eV: célula + átomos "
            f"(fmax={FMAX_CELL_EV_A} eV/Å)",
            flush=True,
        )

    opt_cell.run(
        fmax=FMAX_CELL_EV_A,
        steps=MAX_STEPS_CELL,
    )

    # Refinamento final das coordenadas a célula fixa.
    atoms.calc = calculator(
        ecut,
        OUT_DIR / f"{mineral}_{ecut}eV_R5_atoms.txt",
    )
    opt_atoms = BFGS(
        atoms,
        logfile=str(OUT_DIR / f"{mineral}_{ecut}eV_R5_atoms.log"),
        trajectory=str(OUT_DIR / f"{mineral}_{ecut}eV_R5_atoms.traj"),
    )
    opt_atoms.run(
        fmax=FMAX_ATOMS_EV_A,
        steps=MAX_STEPS_ATOMS,
    )

    energy = float(atoms.get_potential_energy())
    elapsed = time.perf_counter() - t0

    out_cif = final_cif_path(mineral, ecut)
    write(out_cif, atoms, format="cif")

    row = {
        "mineral": mineral,
        "xc": XC,
        "ecut_eV": int(ecut),
        "kgrid": int(KGRID),
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
    for central, nneigh in (("Ca", 6), ("Mg", 6), ("C", 3)):
        if central in symbols:
            row.update(
                nearest_bond_stats(atoms, central, nneigh)
            )

    if world.rank == 0:
        summary_path(mineral, ecut).write_text(
            json.dumps(row, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    world.barrier()
    return row


def rel_diff_pct(a: float, b: float) -> float:
    return abs(float(a) - float(b)) / abs(float(b)) * 100.0


def compare(reference: dict, test: dict) -> dict:
    lattice = [
        rel_diff_pct(reference[key], test[key])
        for key in ("a_A", "b_A", "c_A")
    ]
    angles = [
        abs(float(reference[key]) - float(test[key]))
        for key in ("alpha_deg", "beta_deg", "gamma_deg")
    ]

    bond_keys = sorted(
        key for key in reference
        if key.endswith("_O_mean_A") and key in test
    )
    bond_diffs = {
        key: abs(float(reference[key]) - float(test[key]))
        for key in bond_keys
    }

    result = {
        "mineral": reference["mineral"],
        "ecut_candidato_eV": ECUT_REFERENCE_EV,
        "ecut_referencia_superior_eV": ECUT_TEST_EV,
        "max_lattice_rel_diff_pct": max(lattice),
        "volume_rel_diff_pct": rel_diff_pct(
            reference["volume_A3"],
            test["volume_A3"],
        ),
        "max_angle_diff_deg": max(angles),
        "max_bond_mean_diff_A": max(bond_diffs.values()) if bond_diffs else 0.0,
        "delta_energy_meV_atom": abs(
            float(reference["energy_eV_atom"])
            - float(test["energy_eV_atom"])
        ) * 1000.0,
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


def experimental_comparison(mineral: str, final_row: dict) -> dict:
    exp = read(SYSTEMS[mineral]["experimental"])
    exp_cell = cell_metrics(exp)

    return {
        "mineral": mineral,
        "cutoff_eV": int(final_row["ecut_eV"]),
        "delta_a_pct": (
            (float(final_row["a_A"]) - exp_cell["a_A"])
            / exp_cell["a_A"]
            * 100.0
        ),
        "delta_b_pct": (
            (float(final_row["b_A"]) - exp_cell["b_A"])
            / exp_cell["b_A"]
            * 100.0
        ),
        "delta_c_pct": (
            (float(final_row["c_A"]) - exp_cell["c_A"])
            / exp_cell["c_A"]
            * 100.0
        ),
        "delta_volume_pct": (
            (float(final_row["volume_A3"]) - exp_cell["volume_A3"])
            / exp_cell["volume_A3"]
            * 100.0
        ),
    }


def save_csv(rows: list[dict], path: Path) -> None:
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
    verify_paw_datasets()

    if world.size != 4:
        raise RuntimeError(
            f"Step 02-R5 requer 4 processos MPI; world.size={world.size}."
        )

    if world.rank == 0:
        print("=" * 84)
        print("STEP 02-R5 — VALIDAÇÃO FINAL 1400 vs 1600 eV")
        print("=" * 84)
        print("XC:", XC)
        print("k-grid:", f"{KGRID}x{KGRID}x{KGRID}")
        print("Refinamento 1400 eV -> teste 1600 eV")
        print("fmax célula:", FMAX_CELL_EV_A, "eV/Å")
        print("fmax átomos:", FMAX_ATOMS_EV_A, "eV/Å")
        print("=" * 84)

    rows = []
    comparisons = []
    experiment = []

    for mineral in SYSTEMS:
        # Re-refina o 1400 eV do R4 com critério mais estrito.
        r1400 = relax(
            mineral,
            ECUT_REFERENCE_EV,
            SYSTEMS[mineral]["r4_1400"],
        )

        # 1600 parte do mínimo de 1400 eV refinado.
        r1600 = relax(
            mineral,
            ECUT_TEST_EV,
            final_cif_path(mineral, ECUT_REFERENCE_EV),
        )

        rows.extend([r1400, r1600])

        comp = compare(r1400, r1600)
        comparisons.append(comp)
        experiment.append(
            experimental_comparison(mineral, r1600)
        )

        if world.rank == 0:
            print(
                f"[{mineral}] 1400 vs 1600 eV -> "
                f"{'APROVADO' if comp['passes'] else 'NÃO APROVADO'}",
                flush=True,
            )

        world.barrier()

    if world.rank == 0:
        save_csv(
            rows,
            OUT_DIR / "geometrias_1400_1600_R5.csv",
        )
        save_csv(
            comparisons,
            OUT_DIR / "convergencia_1400_vs_1600_R5.csv",
        )
        save_csv(
            experiment,
            OUT_DIR / "PBE_1600_vs_experimento_R5.csv",
        )

        all_pass = all(row["passes"] for row in comparisons)

        decision = {
            "xc": XC,
            "kgrid_primitiva": [KGRID, KGRID, KGRID],
            "candidate_cutoff_eV": ECUT_REFERENCE_EV,
            "upper_validation_cutoff_eV": ECUT_TEST_EV,
            "all_systems_pass": all_pass,
            "criteria": {
                "max_lattice_rel_diff_pct": MAX_LATTICE_REL_DIFF_PCT,
                "max_volume_rel_diff_pct": MAX_VOLUME_REL_DIFF_PCT,
                "max_bond_mean_diff_A": MAX_BOND_DIFF_A,
            },
            "individual": comparisons,
            "decision": (
                "ADOTAR_1400_eV"
                if all_pass
                else "CUT_OFF_AINDA_NAO_CERTIFICADO"
            ),
        }

        (OUT_DIR / "decisao_final_cutoff_R5.json").write_text(
            json.dumps(decision, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\n" + "=" * 84)
        print("STEP 02-R5 CONCLUÍDO")
        print(
            "Decisão:",
            "ADOTAR 1400 eV"
            if all_pass
            else "cutoff ainda não certificado",
        )
        print("=" * 84)


if __name__ == "__main__":
    main()
