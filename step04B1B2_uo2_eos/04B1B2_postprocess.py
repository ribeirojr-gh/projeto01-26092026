#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from ase.eos import EquationOfState
from ase.units import GPa

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1B2 import (
    CENTER_JSON,
    RESULTS_DIR,
    A_CENTER_A,
    A_EXP_HIGH_PRECISION_A,
    LATTICE_SCALE,
    UEFF_GRID_EV,
    ECUT_EOS_EV,
    ECUT_VALIDATION_EV,
    B0_EXP_GUIDE_GPA,
    MAX_CUTOFF_DE_MEV_ATOM,
    MAX_CUTOFF_DGAP_EV,
    MAX_CUTOFF_DMOMENT_MUB,
    MAX_CUTOFF_DSTRESS_GPA,
    MAX_LATTICE_ERROR_PERCENT,
    B0_GUIDE_MIN_GPA,
    B0_GUIDE_MAX_GPA,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def center_record(ueff: float):
    r = load_json(CENTER_JSON[ueff])
    if r.get("status") != "converged_tight":
        raise RuntimeError(
            f"Centro B1B1 não convergido para Ueff={ueff}"
        )
    # Padroniza campos necessários ao EOS.
    return {
        **r,
        "a_A": A_CENTER_A,
        "volume_A3": A_CENTER_A ** 3,
        "volume_A3_atom": A_CENTER_A ** 3 / 12.0,
    }


def eos_record_path(ueff: float, scale: float):
    u = str(ueff).replace(".", "p")
    s = f"{scale:.2f}".replace(".", "p")
    return RESULTS_DIR / f"UO2_nc6_U{u}_s{s}_1400.json"


def cutoff_record_path(ueff: float):
    u = str(ueff).replace(".", "p")
    return RESULTS_DIR / f"UO2_nc6_U{u}_center_1600.json"


all_eos = {}
eos_summary = {}
cutoff_summary = {}
failed = []

for ueff in UEFF_GRID_EV:
    records = []

    for scale in LATTICE_SCALE:
        if abs(scale - 1.0) < 1.0e-12:
            r = center_record(ueff)
        else:
            path = eos_record_path(ueff, scale)
            r = load_json(path)

        if r.get("status") != "converged_tight":
            failed.append({
                "kind": "EOS",
                "Ueff_eV": ueff,
                "scale": scale,
                "record": r,
            })
            continue

        records.append(r)

    all_eos[ueff] = records

    if len(records) == len(LATTICE_SCALE):
        records = sorted(records, key=lambda x: x["volume_A3"])
        volumes = np.array(
            [r["volume_A3"] for r in records],
            dtype=float,
        )
        energies = np.array(
            [r["energy_eV"] for r in records],
            dtype=float,
        )

        eos = EquationOfState(
            volumes,
            energies,
            eos="birchmurnaghan",
        )
        v0, e0, B_eVA3 = eos.fit()
        a0 = float(v0 ** (1.0 / 3.0))
        B0 = float(B_eVA3 / GPa)

        a_error = abs(
            a0 - A_EXP_HIGH_PRECISION_A
        ) / A_EXP_HIGH_PRECISION_A * 100.0

        structural_pass = (
            a_error <= MAX_LATTICE_ERROR_PERCENT
            and B0_GUIDE_MIN_GPA <= B0 <= B0_GUIDE_MAX_GPA
        )

        eos_summary[ueff] = {
            "Ueff_eV": ueff,
            "npoints": len(records),
            "v0_A3_cell": float(v0),
            "a0_A": a0,
            "e0_eV_cell": float(e0),
            "B0_GPa": B0,
            "a_exp_high_precision_A": A_EXP_HIGH_PRECISION_A,
            "lattice_error_percent": float(a_error),
            "B0_exp_guide_GPa": B0_EXP_GUIDE_GPA,
            "structural_guide_pass": bool(structural_pass),
        }
    else:
        eos_summary[ueff] = {
            "Ueff_eV": ueff,
            "npoints": len(records),
            "structural_guide_pass": False,
            "status": "incomplete_eos",
        }

    # Cutoff validation at the center.
    r1400 = center_record(ueff)
    r1600 = load_json(cutoff_record_path(ueff))

    if r1600.get("status") == "converged_tight":
        dE = abs(
            r1600["energy_eV_atom"] - r1400["energy_eV_atom"]
        ) * 1000.0

        gap1400 = r1400.get("band_gap_eV")
        gap1600 = r1600.get("band_gap_eV")
        dgap = (
            None
            if gap1400 is None or gap1600 is None
            else abs(gap1600 - gap1400)
        )

        dm = abs(
            r1600["U_abs_mean_moment_muB"]
            - r1400["U_abs_mean_moment_muB"]
        )

        ds = abs(
            r1600["max_abs_stress_GPa"]
            - r1400["max_abs_stress_GPa"]
        )

        passes = (
            dE <= MAX_CUTOFF_DE_MEV_ATOM
            and dgap is not None
            and dgap <= MAX_CUTOFF_DGAP_EV
            and dm <= MAX_CUTOFF_DMOMENT_MUB
            and ds <= MAX_CUTOFF_DSTRESS_GPA
        )

        cutoff_summary[ueff] = {
            "Ueff_eV": ueff,
            "delta_energy_meV_atom": float(dE),
            "delta_gap_eV": dgap,
            "delta_moment_muB": float(dm),
            "delta_max_stress_GPa": float(ds),
            "criteria": {
                "max_delta_energy_meV_atom":
                    MAX_CUTOFF_DE_MEV_ATOM,
                "max_delta_gap_eV":
                    MAX_CUTOFF_DGAP_EV,
                "max_delta_moment_muB":
                    MAX_CUTOFF_DMOMENT_MUB,
                "max_delta_max_stress_GPa":
                    MAX_CUTOFF_DSTRESS_GPA,
            },
            "passes": bool(passes),
        }
    else:
        cutoff_summary[ueff] = {
            "Ueff_eV": ueff,
            "passes": False,
            "status": "1600_eV_not_converged",
        }
        failed.append({
            "kind": "cutoff_1600",
            "Ueff_eV": ueff,
            "record": r1600,
        })


# Tabela EOS ponto a ponto.
rows = []
for ueff, records in all_eos.items():
    if not records:
        continue
    emin = min(r["energy_eV_atom"] for r in records)
    for r in sorted(records, key=lambda x: x["a_A"]):
        rows.append({
            "Ueff_eV": ueff,
            "a_A": r["a_A"],
            "volume_A3": r["volume_A3"],
            "energy_eV_atom": r["energy_eV_atom"],
            "deltaE_from_min_meV_atom":
                (r["energy_eV_atom"] - emin) * 1000.0,
            "band_gap_eV": r.get("band_gap_eV"),
            "U_abs_mean_moment_muB":
                r.get("U_abs_mean_moment_muB"),
            "max_abs_stress_GPa":
                r.get("max_abs_stress_GPa"),
        })

if rows:
    with (RESULTS_DIR / "UO2_EOS_points_B1B2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)


# Seleção final deste gate: primeiro exige convergência de cutoff e EOS.
eligible = []
for ueff in UEFF_GRID_EV:
    es = eos_summary.get(ueff, {})
    cs = cutoff_summary.get(ueff, {})
    if es.get("structural_guide_pass") and cs.get("passes"):
        eligible.append(ueff)

# Entre candidatos estruturalmente/numericamente aprovados, mantemos o
# resultado eletrônico do B1B1 como critério de desempate.
preferred = None
if eligible:
    # 3 eV é o candidato eletronicamente preferido do B1B1; só é escolhido
    # aqui se também passar EOS e cutoff.
    preferred = 3.0 if 3.0 in eligible else eligible[0]

decision = {
    "step": "04B1B2",
    "scope": (
        "UO2/nc6 EOS and 1400-versus-1600 eV validation for "
        "Ueff=3 and 4 eV."
    ),
    "experimental_guides": {
        "a0_high_precision_20C_A": A_EXP_HIGH_PRECISION_A,
        "B0_guide_GPa": B0_EXP_GUIDE_GPA,
    },
    "eos_summary": {
        str(k): v for k, v in eos_summary.items()
    },
    "cutoff_summary": {
        str(k): v for k, v in cutoff_summary.items()
    },
    "eligible_candidates": eligible,
    "preferred_Ueff_eV": preferred,
    "step04B1B2_passes": preferred is not None,
    "failed_runs": failed,
    "production_authorization": False,
    "next_gate": (
        "If Step04B1B2 passes: validate Pb(II) PBEsol by relaxing "
        "cerussite and then perform controlled SOC sensitivity for UO2. "
        "Only after compound-level U/Pb validation may carbonate defect "
        "production be authorized."
    ),
    "warning": (
        "The EOS uses a collinear 1-k AFM benchmark state without SOC. "
        "It does not replace the experimental non-collinear 3-k ground "
        "state."
    ),
}

(RESULTS_DIR / "decisao_step04B1B2.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1B2 — EOS / CUTOFF UO2")
print("=" * 80)
for ueff in UEFF_GRID_EV:
    print(f"Ueff={ueff:.1f} eV")
    print("  EOS:", eos_summary.get(ueff))
    print("  cutoff:", cutoff_summary.get(ueff))
print()
print("Elegíveis:", eligible)
print("Preferido:", preferred)
print(
    "STEP04B1B2:",
    "APROVADO" if decision["step04B1B2_passes"] else "REPROVADO",
)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
