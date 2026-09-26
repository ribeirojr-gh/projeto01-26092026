#!/usr/bin/env python3
"""
ETAPA 01-R2 — Seleção final das referências cristalográficas.

Correções em relação ao R1:
1. Usa ElementComparator para comparar estruturas provenientes de fontes
   que codificam diferentemente estados de oxidação.
2. Mantém a calcita experimental COD 1010928.
3. Substitui a dolomita COD 1517797 (refinamento de 1925) por COD 1517796,
   refinamento de 1983 com melhor qualidade cristalográfica.
4. Gera células primitivas e convencionais finais para a Etapa 02.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Dict, List

import numpy as np
import requests
from pymatgen.analysis.structure_matcher import (
    ElementComparator,
    SpeciesComparator,
    StructureMatcher,
)
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
STEP01 = PROJECT_ROOT / "step01_structures"
STEP01_R1 = PROJECT_ROOT / "step01_R1_validation"

OLD_STRUCT = STEP01 / "estruturas"
R1_STRUCT = STEP01_R1 / "estruturas_R1"

OUT_STRUCT = ROOT / "referencias_finais"
OUT_TABLE = ROOT / "tabelas_R2"

COD_URL = "https://www.crystallography.net/cod/{cod_id}.cif"

SYSTEMS = {
    "calcita": {
        "formula": "CaCO3",
        "cod_id": "1010928",
        "mp_id": "mp-3953",
        "expected_sg": 167,
        "cod_note": "Elliott (1937), JACS",
    },
    "dolomita": {
        "formula": "CaMg(CO3)2",
        "cod_id": "1517796",
        "mp_id": "mp-6459",
        "expected_sg": 148,
        "cod_note": "Effenberger, Kirfel & Will (1983), TMPM",
    },
}


def ensure_dirs() -> None:
    OUT_STRUCT.mkdir(exist_ok=True)
    OUT_TABLE.mkdir(exist_ok=True)


def download_text(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    text = r.text
    if "_atom_site" not in text or "_cell_length_a" not in text:
        raise RuntimeError(f"Resposta inválida ao baixar {url}")
    return text


def get_cod(mineral: str, cod_id: str) -> Path:
    candidates = [
        R1_STRUCT / f"{mineral}_experimental_COD_{cod_id}.cif",
        R1_STRUCT / f"{mineral}_COD_{cod_id}.cif",
        OLD_STRUCT / f"{mineral}_COD_{cod_id}.cif",
    ]

    out = OUT_STRUCT / f"{mineral}_COD_{cod_id}_raw.cif"

    for src in candidates:
        if src.exists():
            out.write_bytes(src.read_bytes())
            print(f"[LOCAL COD] {src}")
            return out

    url = COD_URL.format(cod_id=cod_id)
    print(f"[DOWNLOAD COD] {url}")
    out.write_text(download_text(url), encoding="utf-8")
    return out


def get_mp(mineral: str, mp_id: str) -> Path:
    candidates = [
        OLD_STRUCT / f"{mineral}_MP_{mp_id}.cif",
        R1_STRUCT / f"{mineral}_MP_{mp_id}.cif",
    ]
    out = OUT_STRUCT / f"{mineral}_MP_{mp_id}_raw.cif"

    for src in candidates:
        if src.exists():
            out.write_bytes(src.read_bytes())
            print(f"[LOCAL MP] {src}")
            return out

    api_key = os.environ.get("MP_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            f"Não encontrei {mineral}_MP_{mp_id}.cif e MP_API_KEY não está definida."
        )

    from mp_api.client import MPRester

    print(f"[DOWNLOAD MP] {mp_id}")
    with MPRester(api_key) as mpr:
        structure = mpr.get_structure_by_material_id(mp_id)
    structure.to(filename=str(out), fmt="cif")
    return out


def sga(struct: Structure) -> SpacegroupAnalyzer:
    return SpacegroupAnalyzer(struct, symprec=1.0e-3, angle_tolerance=5.0)


def formula_units(struct: Structure) -> float:
    _, factor = struct.composition.get_reduced_composition_and_factor()
    return float(factor)


def summarize(label: str, source: str, path: Path) -> Dict[str, object]:
    st = Structure.from_file(path)
    analyzer = sga(st)
    lat = st.lattice
    fu = formula_units(st)

    return {
        "label": label,
        "fonte": source,
        "arquivo": path.name,
        "formula": st.composition.reduced_formula,
        "n_sitios": len(st),
        "formula_units": fu,
        "spacegroup": analyzer.get_space_group_symbol(),
        "spacegroup_number": analyzer.get_space_group_number(),
        "a_A": lat.a,
        "b_A": lat.b,
        "c_A": lat.c,
        "alpha_deg": lat.alpha,
        "beta_deg": lat.beta,
        "gamma_deg": lat.gamma,
        "volume_A3": lat.volume,
        "volume_por_fu_A3": lat.volume / fu,
        "densidade_g_cm3": float(st.density),
    }


def matcher(
    s1: Structure,
    s2: Structure,
    comparator,
    scale: bool,
) -> Dict[str, object]:
    sm = StructureMatcher(
        ltol=0.20,
        stol=0.30,
        angle_tol=5.0,
        primitive_cell=True,
        scale=scale,
        attempt_supercell=False,
        comparator=comparator,
    )

    fit = sm.fit(s1, s2, symmetric=True)
    rms = maxdist = np.nan
    if fit:
        result = sm.get_rms_dist(s1, s2)
        if result is not None:
            rms, maxdist = result

    return {
        "comparador": type(comparator).__name__,
        "scale": scale,
        "match": bool(fit),
        "rms_normalizado": rms,
        "maxdist_normalizado": maxdist,
    }


def nearest_o_stats(st: Structure, symbol: str, n: int) -> Dict[str, object]:
    values: List[float] = []
    sites_o = [site for site in st if site.specie.symbol == "O"]

    for site in st:
        if site.specie.symbol != symbol:
            continue
        d = sorted(site.distance(o) for o in sites_o)
        values.extend(d[:n])

    arr = np.asarray(values, dtype=float)
    return {
        "elemento": symbol,
        "n_ligacoes": len(arr),
        "min_A": float(arr.min()),
        "media_A": float(arr.mean()),
        "max_A": float(arr.max()),
    }


def write_csv(rows: List[Dict[str, object]], filename: str) -> Path:
    out = OUT_TABLE / filename
    keys: List[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    return out


def write_final_cells(mineral: str, source: str, st: Structure) -> Dict[str, str]:
    analyzer = sga(st)
    primitive = analyzer.get_primitive_standard_structure()
    conventional = analyzer.get_conventional_standard_structure()

    p_prim = OUT_STRUCT / f"{mineral}_ref_{source}_primitiva.cif"
    p_conv = OUT_STRUCT / f"{mineral}_ref_{source}_convencional.cif"

    primitive.to(filename=str(p_prim), fmt="cif")
    conventional.to(filename=str(p_conv), fmt="cif")

    return {
        "primitiva": p_prim.name,
        "convencional": p_conv.name,
    }


def main() -> None:
    ensure_dirs()

    summaries = []
    comparisons = []
    coordination = []
    manifest = {
        "purpose": "Referências finais para Etapa 02",
        "comparison_policy": (
            "ElementComparator para equivalência geométrica entre bases; "
            "SpeciesComparator mantido apenas como diagnóstico de metadados "
            "de estados de oxidação."
        ),
        "systems": {},
    }

    print("=" * 82)
    print("ETAPA 01-R2 — SELEÇÃO FINAL DAS REFERÊNCIAS CRISTALOGRÁFICAS")
    print("=" * 82)

    for mineral, meta in SYSTEMS.items():
        print(f"\n--- {mineral.upper()} ---")
        cod_path = get_cod(mineral, meta["cod_id"])
        mp_path = get_mp(mineral, meta["mp_id"])

        cod = Structure.from_file(cod_path)
        mp = Structure.from_file(mp_path)

        cod_sg = sga(cod).get_space_group_number()
        mp_sg = sga(mp).get_space_group_number()

        print(f"COD SG: {cod_sg}; MP SG: {mp_sg}")

        if cod_sg != meta["expected_sg"]:
            raise RuntimeError(
                f"{mineral}: COD SG={cod_sg}; esperado {meta['expected_sg']}"
            )
        if mp_sg != meta["expected_sg"]:
            raise RuntimeError(
                f"{mineral}: MP SG={mp_sg}; esperado {meta['expected_sg']}"
            )

        summaries.append(summarize(f"{mineral}_COD", "COD", cod_path))
        summaries.append(summarize(f"{mineral}_MP", "MaterialsProject", mp_path))

        for comp in (SpeciesComparator(), ElementComparator()):
            for scale in (True, False):
                row = matcher(cod, mp, comp, scale)
                row.update(
                    {
                        "mineral": mineral,
                        "COD": meta["cod_id"],
                        "MP": meta["mp_id"],
                    }
                )
                comparisons.append(row)
                print(
                    f"{type(comp).__name__:18s} scale={str(scale):5s} "
                    f"match={row['match']}"
                )

        elements = {el.symbol for el in cod.composition.elements}
        for source, st in (("COD", cod), ("MP", mp)):
            for symbol, nneigh in (("Ca", 6), ("Mg", 6), ("C", 3)):
                if symbol not in elements:
                    continue
                row = nearest_o_stats(st, symbol, nneigh)
                row.update({"mineral": mineral, "fonte": source})
                coordination.append(row)

        exp_files = write_final_cells(mineral, "experimental", cod)
        mp_files = write_final_cells(mineral, "MP", mp)

        manifest["systems"][mineral] = {
            "formula": meta["formula"],
            "experimental_reference": {
                "database": "COD",
                "id": meta["cod_id"],
                "note": meta["cod_note"],
                "files": exp_files,
            },
            "dft_database_reference": {
                "database": "Materials Project",
                "id": meta["mp_id"],
                "files": mp_files,
            },
            "step02_starting_structure": exp_files["primitiva"],
            "step02_validation_target": exp_files["convencional"],
        }

    p1 = write_csv(summaries, "resumo_referencias_finais.csv")
    p2 = write_csv(comparisons, "comparacao_elementos_vs_especies.csv")
    p3 = write_csv(coordination, "coordenacao_referencias_finais.csv")

    manifest_path = OUT_TABLE / "manifesto_referencias_finais.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 82)
    print("ETAPA 01-R2 CONCLUÍDA")
    print(f"Resumo:      {p1}")
    print(f"Comparação:  {p2}")
    print(f"Coordenação: {p3}")
    print(f"Manifesto:   {manifest_path}")
    print(f"CIFs finais: {OUT_STRUCT}")
    print("=" * 82)


if __name__ == "__main__":
    main()
