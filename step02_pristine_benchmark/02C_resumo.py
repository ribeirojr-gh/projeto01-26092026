#!/usr/bin/env python3
"""
STEP 02C — Resumo consolidado do Step 02.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
from pymatgen.core import Structure

from config_step02 import (
    GPAW_DIR,
    INPUT_SNAPSHOT,
    MLIP_DIR,
    SUMMARY_DIR,
)


def lattice_metrics(path: Path) -> dict:
    s = Structure.from_file(path)
    lat = s.lattice
    return {
        "a_A": lat.a,
        "b_A": lat.b,
        "c_A": lat.c,
        "alpha_deg": lat.alpha,
        "beta_deg": lat.beta,
        "gamma_deg": lat.gamma,
        "volume_A3": lat.volume,
        "densidade_g_cm3": float(s.density),
    }


def pct(new: float, ref: float) -> float:
    return 100.0 * (new - ref) / ref


def main() -> None:
    SUMMARY_DIR.mkdir(exist_ok=True)

    mlip_csv = MLIP_DIR / "resumo_mlip.csv"
    conv_csv = GPAW_DIR / "convergencia_gpaw.csv"
    rec_csv = GPAW_DIR / "parametros_recomendados_gpaw.csv"

    for path in (mlip_csv, conv_csv, rec_csv):
        if not path.exists():
            raise FileNotFoundError(f"Arquivo necessário não encontrado: {path}")

    mlip = pd.read_csv(mlip_csv)
    conv = pd.read_csv(conv_csv)
    rec = pd.read_csv(rec_csv)

    comparison_rows = []

    for mineral in ("calcita", "dolomita"):
        ref_path = INPUT_SNAPSHOT / f"{mineral}_experimental_primitiva.cif"
        ref = lattice_metrics(ref_path)

        row_ref = {
            "mineral": mineral,
            "metodo": "Experimental",
            "arquivo": ref_path.name,
            **ref,
            "delta_volume_pct": 0.0,
        }
        comparison_rows.append(row_ref)

        for method in ("CHGNet", "MACE"):
            row = mlip[
                (mlip["mineral"] == mineral) & (mlip["metodo"] == method)
            ].iloc[0]

            out = {
                "mineral": mineral,
                "metodo": method,
                "arquivo": row["arquivo"],
                "a_A": row["a_A"],
                "b_A": row["b_A"],
                "c_A": row["c_A"],
                "alpha_deg": row["alpha_deg"],
                "beta_deg": row["beta_deg"],
                "gamma_deg": row["gamma_deg"],
                "volume_A3": row["volume_A3"],
                "densidade_g_cm3": None,
                "delta_volume_pct": pct(row["volume_A3"], ref["volume_A3"]),
            }
            comparison_rows.append(out)

    comp = pd.DataFrame(comparison_rows)
    comp.to_csv(SUMMARY_DIR / "comparacao_mlip_experimento.csv", index=False)

    rec.to_csv(SUMMARY_DIR / "parametros_gpaw_para_revisao.csv", index=False)

    # Resumo legível
    lines = [
        "STEP 02 — RESUMO PRELIMINAR",
        "=" * 72,
        "",
        "1. MLIP × estrutura experimental",
        comp.to_string(index=False),
        "",
        "2. Parâmetros GPAW sugeridos automaticamente",
        rec.to_string(index=False),
        "",
        "IMPORTANTE:",
        "Os parâmetros GPAW são sugestões automáticas baseadas nos critérios",
        "de energia e stress definidos no config_step02.py. A relaxação DFT",
        "não é iniciada nesta etapa; os resultados devem ser revisados antes.",
        "",
    ]

    out_txt = SUMMARY_DIR / "resumo_step02.txt"
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print("Resumo salvo em:", out_txt)


if __name__ == "__main__":
    main()
