#!/usr/bin/env python3
"""
STEP 02-R3 — Convergência refinada de energia de corte GPAW/PBE.

Mudanças em relação ao R2:
- usa PW(ecut, dedecut='estimate') para correção do Pulay stress;
- mantém k = 5x5x5, já demonstrado como conservador no R2;
- estende o cutoff até 1600 eV;
- não considera automaticamente o maior cutoff como "convergido";
- exige dois intervalos consecutivos dentro dos critérios;
- grava checkpoint após cada ponto.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from ase.io import read
from gpaw import GPAW, PW
from gpaw.mpi import world
from gpaw.setup_data import SetupData

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step02_R3 import (
    ECUT_VALUES_EV,
    ENERGY_TOL_MEV_ATOM,
    FERMI_WIDTH_EV,
    KGRID,
    OUT_DIR,
    REQUIRED_CONSECUTIVE_PASSES,
    STRESS_TOL_GPA,
    SYSTEMS,
    XC,
)

EV_A3_TO_GPA = 160.21766208
STRESS_KEYS = (
    "stress_xx_GPa",
    "stress_yy_GPa",
    "stress_zz_GPa",
    "stress_yz_GPa",
    "stress_xz_GPa",
    "stress_xy_GPa",
)


def ensure_inputs() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    missing = [str(path) for path in SYSTEMS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Estruturas da Etapa 01-R2 não encontradas:\n  "
            + "\n  ".join(missing)
        )


def verify_paw_datasets() -> None:
    required = ("Ca", "C", "O", "Mg")
    errors = []

    for symbol in required:
        try:
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
        except Exception as exc:
            errors.append(f"{symbol}.PBE: {exc}")

    if errors:
        raise RuntimeError(
            "Falha nos datasets PAW PBE:\n  " + "\n  ".join(errors)
        )


def checkpoint_path() -> Path:
    return OUT_DIR / "convergencia_cutoff_R3_checkpoint.csv"


def final_csv_path() -> Path:
    return OUT_DIR / "convergencia_cutoff_R3.csv"


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return

    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def load_checkpoint() -> list[dict]:
    path = checkpoint_path()
    if not path.exists():
        return []

    rows: list[dict] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            converted = dict(row)

            for key in ("ecut_eV", "kgrid", "n_atoms"):
                converted[key] = int(float(converted[key]))

            for key in (
                "energy_eV",
                "energy_eV_atom",
                "fmax_eV_A",
                *STRESS_KEYS,
                "stress_max_abs_GPa",
                "tempo_s",
            ):
                converted[key] = float(converted[key])

            rows.append(converted)

    return rows


def find_checkpoint(
    rows: list[dict],
    mineral: str,
    ecut: int,
) -> dict | None:
    for row in rows:
        if (
            row["mineral"] == mineral
            and int(row["ecut_eV"]) == int(ecut)
            and int(row["kgrid"]) == KGRID
        ):
            return dict(row)
    return None


def stress_vector(row: dict) -> np.ndarray:
    return np.asarray([float(row[key]) for key in STRESS_KEYS], dtype=float)


def run_point(mineral: str, atoms, ecut: int) -> dict:
    txt = OUT_DIR / f"{mineral}_R3_ecut{ecut}_k{KGRID}.txt"

    calc = GPAW(
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
    atoms.calc = calc

    if world.rank == 0:
        print(
            f"[{mineral}] ecut={ecut} eV | "
            f"k={KGRID}x{KGRID}x{KGRID} | "
            "Pulay stress: dedecut='estimate'",
            flush=True,
        )

    t0 = time.perf_counter()
    energy = atoms.get_potential_energy()
    forces = np.asarray(atoms.get_forces(), dtype=float)
    stress = np.asarray(atoms.get_stress(voigt=True), dtype=float)
    elapsed = time.perf_counter() - t0

    stress_gpa = stress * EV_A3_TO_GPA

    row = {
        "mineral": mineral,
        "xc": XC,
        "ecut_eV": int(ecut),
        "kgrid": int(KGRID),
        "pulay_correction": "dedecut=estimate",
        "n_atoms": len(atoms),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "fmax_eV_A": float(np.linalg.norm(forces, axis=1).max()),
        "stress_xx_GPa": float(stress_gpa[0]),
        "stress_yy_GPa": float(stress_gpa[1]),
        "stress_zz_GPa": float(stress_gpa[2]),
        "stress_yz_GPa": float(stress_gpa[3]),
        "stress_xz_GPa": float(stress_gpa[4]),
        "stress_xy_GPa": float(stress_gpa[5]),
        "stress_max_abs_GPa": float(np.max(np.abs(stress_gpa))),
        "tempo_s": float(elapsed),
        "gpaw_txt": txt.name,
    }

    atoms.calc = None
    del calc
    world.barrier()
    return row


def add_adjacent_deltas(rows: list[dict]) -> None:
    rows.sort(key=lambda r: int(r["ecut_eV"]))

    for idx, row in enumerate(rows):
        row["deltaE_prev_meV_atom"] = ""
        row["deltaStress_prev_GPa"] = ""
        row["interval_pass"] = ""

        if idx == 0:
            continue

        prev = rows[idx - 1]
        dE = (
            abs(
                float(row["energy_eV_atom"])
                - float(prev["energy_eV_atom"])
            )
            * 1000.0
        )
        dS = float(
            np.max(
                np.abs(
                    stress_vector(row)
                    - stress_vector(prev)
                )
            )
        )

        row["deltaE_prev_meV_atom"] = dE
        row["deltaStress_prev_GPa"] = dS
        row["interval_pass"] = bool(
            dE <= ENERGY_TOL_MEV_ATOM
            and dS <= STRESS_TOL_GPA
        )


def convergence_recommendation(rows: list[dict]) -> dict:
    ordered = sorted(rows, key=lambda r: int(r["ecut_eV"]))
    add_adjacent_deltas(ordered)

    pass_streak = 0

    for idx in range(1, len(ordered)):
        if ordered[idx]["interval_pass"] is True:
            pass_streak += 1
        else:
            pass_streak = 0

        if pass_streak >= REQUIRED_CONSECUTIVE_PASSES:
            # Ex.: intervalos 1200->1400 e 1400->1600 passam.
            # O cutoff de 1400 é certificado por um ponto superior.
            recommended_idx = idx - REQUIRED_CONSECUTIVE_PASSES + 1
            recommended = ordered[recommended_idx]
            return {
                "converged": True,
                "ecut_recomendado_eV": int(recommended["ecut_eV"]),
                "maior_ecut_calculado_eV": int(ordered[-1]["ecut_eV"]),
                "criterio_energia_meV_atom": ENERGY_TOL_MEV_ATOM,
                "criterio_stress_GPa": STRESS_TOL_GPA,
                "intervalos_consecutivos_exigidos": REQUIRED_CONSECUTIVE_PASSES,
            }

    return {
        "converged": False,
        "ecut_recomendado_eV": "",
        "maior_ecut_calculado_eV": int(ordered[-1]["ecut_eV"]),
        "criterio_energia_meV_atom": ENERGY_TOL_MEV_ATOM,
        "criterio_stress_GPa": STRESS_TOL_GPA,
        "intervalos_consecutivos_exigidos": REQUIRED_CONSECUTIVE_PASSES,
    }


def main() -> None:
    ensure_inputs()
    verify_paw_datasets()

    checkpoint_rows = load_checkpoint()

    if world.rank == 0:
        print("=" * 82)
        print("STEP 02-R3 — CONVERGÊNCIA REFINADA DE CUTOFF GPAW/PBE")
        print("=" * 82)
        print("MPI world size:", world.size)
        print("k-grid fixo:", f"{KGRID}x{KGRID}x{KGRID}")
        print("Cutoffs:", ECUT_VALUES_EV)
        print("Pulay stress:", "PW(..., dedecut='estimate')")
        print(
            "Critérios:",
            f"ΔE <= {ENERGY_TOL_MEV_ATOM} meV/átomo;",
            f"Δstress <= {STRESS_TOL_GPA} GPa;",
            f"{REQUIRED_CONSECUTIVE_PASSES} intervalos consecutivos.",
        )
        print("Checkpoint existente:", len(checkpoint_rows), "pontos")
        print("=" * 82)

    if world.size != 4:
        raise RuntimeError(
            f"Esta etapa requer 4 processos MPI; world.size={world.size}."
        )

    all_rows: list[dict] = []
    recommendations: list[dict] = []

    for mineral, input_path in SYSTEMS.items():
        atoms0 = read(input_path)
        rows: list[dict] = []

        for ecut in ECUT_VALUES_EV:
            cached = find_checkpoint(checkpoint_rows, mineral, ecut)

            if cached is not None:
                rows.append(cached)
                if world.rank == 0:
                    print(
                        f"[{mineral}] ecut={ecut} eV: reutilizando checkpoint",
                        flush=True,
                    )
                world.barrier()
                continue

            row = run_point(
                mineral,
                atoms0.copy(),
                ecut=ecut,
            )
            rows.append(row)
            checkpoint_rows.append(dict(row))

            if world.rank == 0:
                save_csv(checkpoint_rows, checkpoint_path())

            world.barrier()

        add_adjacent_deltas(rows)
        rec = convergence_recommendation(rows)
        rec["mineral"] = mineral
        rec["kgrid"] = KGRID
        rec["xc"] = XC
        recommendations.append(rec)

        if world.rank == 0:
            all_rows.extend(rows)
            print(
                f"[{mineral}] convergência de cutoff:",
                "OK" if rec["converged"] else "NÃO ATINGIDA",
                "| recomendado:",
                rec["ecut_recomendado_eV"] or "nenhum",
                flush=True,
            )

        world.barrier()

    if world.rank == 0:
        save_csv(all_rows, final_csv_path())
        save_csv(
            recommendations,
            OUT_DIR / "recomendacoes_cutoff_R3.csv",
        )

        converged = [r for r in recommendations if r["converged"]]
        common_cutoff = (
            max(int(r["ecut_recomendado_eV"]) for r in converged)
            if len(converged) == len(recommendations)
            else None
        )

        final_params = {
            "xc": XC,
            "paw_datasets": "PBE oficiais GPAW",
            "kgrid_primitiva": [KGRID, KGRID, KGRID],
            "pulay_stress": "dedecut=estimate",
            "energy_tolerance_meV_atom": ENERGY_TOL_MEV_ATOM,
            "stress_tolerance_GPa": STRESS_TOL_GPA,
            "required_consecutive_passes": REQUIRED_CONSECUTIVE_PASSES,
            "all_systems_converged": common_cutoff is not None,
            "common_cutoff_eV": common_cutoff,
            "individual_recommendations": recommendations,
        }

        (OUT_DIR / "parametros_finais_R3.json").write_text(
            json.dumps(final_params, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\n" + "=" * 82)
        print("STEP 02-R3 CONCLUÍDO")
        print("Tabela:", final_csv_path())
        print("Recomendações:", OUT_DIR / "recomendacoes_cutoff_R3.csv")
        print("Parâmetros:", OUT_DIR / "parametros_finais_R3.json")

        if common_cutoff is None:
            print(
                "ATENÇÃO: o cutoff ainda não foi certificado para todos os sistemas."
            )
        else:
            print(
                f"Cutoff comum certificado: {common_cutoff} eV; "
                f"k-grid primitiva: {KGRID}x{KGRID}x{KGRID}"
            )
        print("=" * 82)


if __name__ == "__main__":
    main()
