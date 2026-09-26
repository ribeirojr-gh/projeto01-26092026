#!/usr/bin/env python3
"""
ETAPA 01-R1 — Validação das referências cristalográficas.

Objetivos:
1. Reavaliar a referência de calcita do COD, pois a entrada 9007286 é
   teoricamente derivada.
2. Adicionar uma referência experimental do COD (1010928).
3. Investigar por que COD 1517797 e MP mp-6459 para dolomita não foram
   reconhecidos como equivalentes pelo StructureMatcher padrão.
4. Gerar tabelas quantitativas antes da escolha das células de referência.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import requests
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
STEP01 = PROJECT_ROOT / "step01_structures"
OLD_STRUCT = STEP01 / "estruturas"

OUT_STRUCT = ROOT / "estruturas_R1"
OUT_TABLE = ROOT / "tabelas_R1"

COD_URL = "https://www.crystallography.net/cod/{cod_id}.cif"

SYSTEMS = {
    "calcita": {
        "formula": "CaCO3",
        "mp_id": "mp-3953",
        "cod_original": "9007286",
        "cod_experimental": "1010928",
        "sg": 167,
    },
    "dolomita": {
        "formula": "CaMg(CO3)2",
        "mp_id": "mp-6459",
        "cod_original": "1517797",
        "sg": 148,
    },
}


def ensure_dirs() -> None:
    OUT_STRUCT.mkdir(exist_ok=True)
    OUT_TABLE.mkdir(exist_ok=True)


def copy_or_download_existing(filename: str, url: str | None = None) -> Path:
    src = OLD_STRUCT / filename
    dst = OUT_STRUCT / filename

    if src.exists():
        dst.write_bytes(src.read_bytes())
        print(f"[LOCAL] {filename}")
        return dst

    if url is None:
        raise FileNotFoundError(
            f"Não encontrei {src}. Execute primeiro o Step 01 ou forneça o arquivo."
        )

    print(f"[DOWNLOAD] {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dst.write_text(r.text, encoding="utf-8")
    return dst


def download_cod(cod_id: str, tag: str) -> Path:
    filename = f"{tag}_COD_{cod_id}.cif"
    return copy_or_download_existing(
        filename,
        COD_URL.format(cod_id=cod_id),
    )


def obtain_mp(mineral: str, mp_id: str) -> Path:
    filename = f"{mineral}_MP_{mp_id}.cif"
    src = OLD_STRUCT / filename
    dst = OUT_STRUCT / filename

    if src.exists():
        dst.write_bytes(src.read_bytes())
        print(f"[LOCAL] {filename}")
        return dst

    key = os.environ.get("MP_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            f"{filename} não existe e MP_API_KEY não está definida."
        )

    from mp_api.client import MPRester

    print(f"[MP] Baixando {mp_id}")
    with MPRester(key) as mpr:
        structure = mpr.get_structure_by_material_id(mp_id)
    structure.to(filename=str(dst), fmt="cif")
    return dst


def standardize(path: Path, stem: str) -> tuple[Path, Path]:
    s = Structure.from_file(path)
    sga = SpacegroupAnalyzer(s, symprec=1e-3, angle_tolerance=5.0)

    conv = sga.get_conventional_standard_structure()
    prim = sga.get_primitive_standard_structure()

    pconv = OUT_STRUCT / f"{stem}_convencional.cif"
    pprim = OUT_STRUCT / f"{stem}_primitiva.cif"

    conv.to(filename=str(pconv), fmt="cif")
    prim.to(filename=str(pprim), fmt="cif")
    return pconv, pprim


def formula_units(structure: Structure) -> float:
    _, factor = structure.composition.get_reduced_composition_and_factor()
    return float(factor)


def summarize(label: str, source: str, path: Path) -> dict:
    s = Structure.from_file(path)
    sga = SpacegroupAnalyzer(s, symprec=1e-3, angle_tolerance=5.0)
    fu = formula_units(s)
    lat = s.lattice

    return {
        "label": label,
        "fonte": source,
        "arquivo": path.name,
        "formula": s.composition.reduced_formula,
        "n_sitios": len(s),
        "formula_units": fu,
        "spacegroup": sga.get_space_group_symbol(),
        "spacegroup_number": sga.get_space_group_number(),
        "a_A": lat.a,
        "b_A": lat.b,
        "c_A": lat.c,
        "alpha_deg": lat.alpha,
        "beta_deg": lat.beta,
        "gamma_deg": lat.gamma,
        "volume_A3": lat.volume,
        "volume_por_fu_A3": lat.volume / fu,
        "densidade_g_cm3": float(s.density),
    }


def matcher_result(
    label: str,
    s1: Structure,
    s2: Structure,
    *,
    ltol: float = 0.2,
    stol: float = 0.3,
    angle_tol: float = 5.0,
    scale: bool = True,
    symmetric: bool = True,
) -> dict:
    matcher = StructureMatcher(
        ltol=ltol,
        stol=stol,
        angle_tol=angle_tol,
        primitive_cell=True,
        scale=scale,
        attempt_supercell=False,
    )

    fit = matcher.fit(s1, s2, symmetric=symmetric)
    rms = maxdist = None
    if fit:
        result = matcher.get_rms_dist(s1, s2)
        if result is not None:
            rms, maxdist = result

    return {
        "comparacao": label,
        "ltol": ltol,
        "stol": stol,
        "angle_tol_deg": angle_tol,
        "scale": scale,
        "symmetric": symmetric,
        "match": bool(fit),
        "rms_normalizado": rms,
        "maxdist_normalizado": maxdist,
    }


def tolerance_scan(label: str, s1: Structure, s2: Structure) -> list[dict]:
    rows: list[dict] = []
    for ltol in (0.05, 0.10, 0.15, 0.20, 0.30):
        for stol in (0.10, 0.20, 0.30, 0.40, 0.50):
            for angle in (1.0, 2.0, 5.0, 10.0):
                row = matcher_result(
                    label,
                    s1,
                    s2,
                    ltol=ltol,
                    stol=stol,
                    angle_tol=angle,
                    scale=True,
                    symmetric=True,
                )
                if row["match"]:
                    rows.append(row)
    rows.sort(key=lambda r: (r["stol"], r["ltol"], r["angle_tol_deg"]))
    return rows


def nearest_o_stats(s: Structure, element: str, n_o: int) -> dict:
    values: list[float] = []

    for site in s:
        if site.specie.symbol != element:
            continue

        dists = sorted(
            site.distance(o)
            for o in s
            if o.specie.symbol == "O" and o is not site
        )
        values.extend(dists[:n_o])

    if not values:
        return {
            "elemento_central": element,
            "n_ligacoes": 0,
            "dist_min_A": np.nan,
            "dist_media_A": np.nan,
            "dist_max_A": np.nan,
        }

    arr = np.asarray(values, dtype=float)
    return {
        "elemento_central": element,
        "n_ligacoes": len(arr),
        "dist_min_A": float(arr.min()),
        "dist_media_A": float(arr.mean()),
        "dist_max_A": float(arr.max()),
    }


def coordination_rows(label: str, s: Structure) -> list[dict]:
    rows: list[dict] = []
    for element, n_o in (("Ca", 6), ("Mg", 6), ("C", 3)):
        if element not in {el.symbol for el in s.composition.elements}:
            continue
        r = nearest_o_stats(s, element, n_o)
        r["estrutura"] = label
        rows.append(r)
    return rows


def save_csv(rows: list[dict], filename: str) -> Path:
    if not rows:
        raise RuntimeError(f"Nenhum dado para {filename}")
    out = OUT_TABLE / filename
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    return out


def main() -> None:
    ensure_dirs()

    print("=" * 80)
    print("ETAPA 01-R1 — VALIDAÇÃO DAS REFERÊNCIAS CRISTALOGRÁFICAS")
    print("=" * 80)

    # Calcita: original COD (teórico), experimental COD e MP
    calc_cod_old = download_cod("9007286", "calcita")
    calc_cod_exp = download_cod("1010928", "calcita_experimental")
    calc_mp = obtain_mp("calcita", "mp-3953")

    # Dolomita: experimental COD e MP
    dolo_cod = download_cod("1517797", "dolomita")
    dolo_mp = obtain_mp("dolomita", "mp-6459")

    raw = {
        "calcita_COD_9007286": calc_cod_old,
        "calcita_COD_1010928_exp": calc_cod_exp,
        "calcita_MP_mp-3953": calc_mp,
        "dolomita_COD_1517797": dolo_cod,
        "dolomita_MP_mp-6459": dolo_mp,
    }

    summaries = []
    coord = []
    structs = {}

    for label, path in raw.items():
        source = "MaterialsProject" if "_MP_" in label else "COD"
        summaries.append(summarize(label, source, path))
        structs[label] = Structure.from_file(path)
        coord.extend(coordination_rows(label, structs[label]))
        standardize(path, label)

    comparisons = []
    pairs = [
        (
            "calcita_COD9007286_vs_MP3953",
            structs["calcita_COD_9007286"],
            structs["calcita_MP_mp-3953"],
        ),
        (
            "calcita_COD1010928exp_vs_MP3953",
            structs["calcita_COD_1010928_exp"],
            structs["calcita_MP_mp-3953"],
        ),
        (
            "dolomita_COD1517797_vs_MP6459",
            structs["dolomita_COD_1517797"],
            structs["dolomita_MP_mp-6459"],
        ),
    ]

    for label, s1, s2 in pairs:
        comparisons.append(
            matcher_result(label, s1, s2, scale=True, symmetric=True)
        )
        comparisons.append(
            matcher_result(label, s1, s2, scale=False, symmetric=True)
        )

    # Diagnóstico adicional da dolomita
    d1 = structs["dolomita_COD_1517797"]
    d2 = structs["dolomita_MP_mp-6459"]

    scan = tolerance_scan("dolomita_COD1517797_vs_MP6459", d1, d2)

    anon_matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5.0,
        primitive_cell=True,
        scale=True,
    )
    anonymous_fit = anon_matcher.fit_anonymous(d1, d2)
    anonymous_mapping = (
        anon_matcher.get_best_electronegativity_anonymous_mapping(d1, d2)
        if anonymous_fit
        else None
    )

    print()
    print("[DOLOMITA] StructureMatcher padrão:",
          comparisons[-2]["match"])
    print("[DOLOMITA] Anonymous fit:", anonymous_fit)
    print("[DOLOMITA] Anonymous mapping:", anonymous_mapping)

    if scan:
        best = scan[0]
        print(
            "[DOLOMITA] Primeiro match encontrado no scan:",
            f"ltol={best['ltol']}, stol={best['stol']}, "
            f"angle={best['angle_tol_deg']}°",
        )
    else:
        print("[DOLOMITA] Nenhum match encontrado no scan de tolerâncias.")

    p1 = save_csv(summaries, "referencias_cristalograficas_R1.csv")
    p2 = save_csv(comparisons, "comparacoes_R1.csv")
    p3 = save_csv(coord, "coordenacao_R1.csv")

    if scan:
        p4 = save_csv(scan, "dolomita_scan_tolerancias_R1.csv")
    else:
        p4 = OUT_TABLE / "dolomita_scan_tolerancias_R1.csv"
        p4.write_text(
            "resultado\nnenhum_match_no_intervalo_testado\n",
            encoding="utf-8",
        )

    print()
    print("=" * 80)
    print("ETAPA 01-R1 CONCLUÍDA")
    print(f"Referências: {p1}")
    print(f"Comparações: {p2}")
    print(f"Coordenação: {p3}")
    print(f"Scan dolomita: {p4}")
    print("=" * 80)


if __name__ == "__main__":
    main()
