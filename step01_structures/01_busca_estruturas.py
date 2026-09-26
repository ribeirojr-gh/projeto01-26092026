#!/usr/bin/env python3
"""
ETAPA 01 — Busca, download, padronização e comparação inicial das
estruturas cristalinas de calcita e dolomita.

Ambiente esperado:
    structures

Fontes:
    - Materials Project (MP): requer MP_API_KEY
    - Crystallography Open Database (COD): acesso público

Saídas:
    estruturas/
    tabelas/resumo_estruturas.csv
    tabelas/comparacao_estrutural.csv
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

ROOT = Path(__file__).resolve().parent
OUT_STRUCT = ROOT / "estruturas"
OUT_TABLE = ROOT / "tabelas"

TARGETS = {
    "calcita": {
        "formula": "CaCO3",
        "mp_id": "mp-3953",
        "cod_id": "9007286",
        "expected_sg_number": 167,
        "expected_sg_symbol": "R-3c",
    },
    "dolomita": {
        "formula": "CaMg(CO3)2",
        "mp_id": "mp-6459",
        "cod_id": "1517797",
        "expected_sg_number": 148,
        "expected_sg_symbol": "R-3",
    },
}

COD_URL = "https://www.crystallography.net/cod/{cod_id}.cif"


def ensure_dirs() -> None:
    OUT_STRUCT.mkdir(exist_ok=True)
    OUT_TABLE.mkdir(exist_ok=True)


def download_cod(name: str, cod_id: str) -> Path:
    url = COD_URL.format(cod_id=cod_id)
    out = OUT_STRUCT / f"{name}_COD_{cod_id}.cif"

    print(f"[COD] Baixando {name}: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    text = response.text
    if "_cell_length_a" not in text or "_atom_site" not in text:
        raise RuntimeError(
            f"O arquivo recebido para COD {cod_id} não parece ser um CIF válido."
        )

    out.write_text(text, encoding="utf-8")
    print(f"[COD] Salvo: {out.name}")
    return out


def download_mp(name: str, mp_id: str) -> Path | None:
    api_key = os.environ.get("MP_API_KEY", "").strip()
    if not api_key:
        print(
            f"[MP] MP_API_KEY não definida: download de {name} ({mp_id}) "
            "será ignorado nesta execução."
        )
        return None

    from mp_api.client import MPRester

    print(f"[MP] Baixando {name}: {mp_id}")
    with MPRester(api_key) as mpr:
        structure = mpr.get_structure_by_material_id(mp_id)

    out = OUT_STRUCT / f"{name}_MP_{mp_id}.cif"
    structure.to(filename=str(out), fmt="cif")
    print(f"[MP] Salvo: {out.name}")
    return out


def standardize_structure(
    path: Path,
    name: str,
    source_tag: str,
) -> Tuple[Path, Path]:
    structure = Structure.from_file(path)
    sga = SpacegroupAnalyzer(
        structure,
        symprec=1.0e-3,
        angle_tolerance=5.0,
    )

    conventional = sga.get_conventional_standard_structure()
    primitive = sga.get_primitive_standard_structure()

    conv_path = OUT_STRUCT / f"{name}_{source_tag}_convencional.cif"
    prim_path = OUT_STRUCT / f"{name}_{source_tag}_primitiva.cif"

    conventional.to(filename=str(conv_path), fmt="cif")
    primitive.to(filename=str(prim_path), fmt="cif")

    print(f"[STD] Convencional: {conv_path.name}")
    print(f"[STD] Primitiva:    {prim_path.name}")

    return conv_path, prim_path


def structure_summary(
    name: str,
    source: str,
    source_id: str,
    path: Path,
) -> Dict[str, object]:
    structure = Structure.from_file(path)
    sga = SpacegroupAnalyzer(
        structure,
        symprec=1.0e-3,
        angle_tolerance=5.0,
    )
    lat = structure.lattice

    return {
        "mineral": name,
        "fonte": source,
        "id_fonte": source_id,
        "arquivo": path.name,
        "formula_reduzida": structure.composition.reduced_formula,
        "n_sitios": len(structure),
        "grupo_espacial": sga.get_space_group_symbol(),
        "numero_grupo_espacial": sga.get_space_group_number(),
        "a_A": lat.a,
        "b_A": lat.b,
        "c_A": lat.c,
        "alpha_deg": lat.alpha,
        "beta_deg": lat.beta,
        "gamma_deg": lat.gamma,
        "volume_A3": lat.volume,
        "densidade_g_cm3": structure.density,
    }


def save_csv(rows: List[Dict[str, object]], filename: str) -> Path:
    if not rows:
        raise RuntimeError("Nenhuma linha disponível para salvar.")

    out = OUT_TABLE / filename
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out


def compare_sources(
    name: str,
    cod_path: Path,
    mp_path: Path | None,
) -> Dict[str, object]:
    if mp_path is None:
        return {
            "mineral": name,
            "comparacao": "COD_vs_MP",
            "mp_disponivel": False,
            "structure_matcher": "",
            "rms": "",
            "max_dist": "",
        }

    cod = Structure.from_file(cod_path)
    mp = Structure.from_file(mp_path)

    matcher = StructureMatcher(
        ltol=0.20,
        stol=0.30,
        angle_tol=5.0,
        primitive_cell=True,
        scale=True,
        attempt_supercell=False,
    )

    is_match = matcher.fit(cod, mp)
    rms = ""
    max_dist = ""

    if is_match:
        result = matcher.get_rms_dist(cod, mp)
        if result is not None:
            rms, max_dist = result

    return {
        "mineral": name,
        "comparacao": "COD_vs_MP",
        "mp_disponivel": True,
        "structure_matcher": bool(is_match),
        "rms": rms,
        "max_dist": max_dist,
    }


def validate_expected_symmetry(
    name: str,
    path: Path,
    expected_number: int,
) -> None:
    structure = Structure.from_file(path)
    sga = SpacegroupAnalyzer(
        structure,
        symprec=1.0e-3,
        angle_tolerance=5.0,
    )
    number = sga.get_space_group_number()
    symbol = sga.get_space_group_symbol()

    print(f"[CHECK] {name}: grupo espacial detectado = {symbol} ({number})")

    if number != expected_number:
        print(
            f"[AVISO] {name}: esperado SG #{expected_number}, "
            f"mas foi detectado SG #{number}."
        )


def main() -> int:
    ensure_dirs()

    summaries: List[Dict[str, object]] = []
    comparisons: List[Dict[str, object]] = []

    print("=" * 78)
    print("ETAPA 01 — BUSCA E PADRONIZAÇÃO DE ESTRUTURAS")
    print("=" * 78)
    print(f"Python: {sys.executable}")
    print(f"Diretório: {ROOT}")
    print()

    for name, meta in TARGETS.items():
        print(f"--- {name.upper()} ({meta['formula']}) ---")

        cod_path = download_cod(name, meta["cod_id"])
        validate_expected_symmetry(
            f"{name} / COD",
            cod_path,
            meta["expected_sg_number"],
        )
        summaries.append(
            structure_summary(name, "COD", meta["cod_id"], cod_path)
        )
        standardize_structure(
            cod_path,
            name,
            f"COD_{meta['cod_id']}",
        )

        mp_path = download_mp(name, meta["mp_id"])
        if mp_path is not None:
            validate_expected_symmetry(
                f"{name} / MP",
                mp_path,
                meta["expected_sg_number"],
            )
            summaries.append(
                structure_summary(
                    name,
                    "MaterialsProject",
                    meta["mp_id"],
                    mp_path,
                )
            )
            standardize_structure(
                mp_path,
                name,
                f"MP_{meta['mp_id']}",
            )

        comparisons.append(
            compare_sources(name, cod_path, mp_path)
        )
        print()

    summary_path = save_csv(
        summaries,
        "resumo_estruturas.csv",
    )
    comparison_path = save_csv(
        comparisons,
        "comparacao_estrutural.csv",
    )

    print("=" * 78)
    print("ETAPA 01 CONCLUÍDA")
    print(f"Resumo:     {summary_path}")
    print(f"Comparação: {comparison_path}")
    print(f"Estruturas: {OUT_STRUCT}")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        raise
