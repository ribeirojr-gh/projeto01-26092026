#!/usr/bin/env python3
"""
STEP 02A — Pré-relaxação das estruturas pristinas com CHGNet -> MACE.

Execução:
    ambiente mlip
    processo único na GPU
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import torch
from ase.filters import FrechetCellFilter
from ase.io import write
from ase.optimize import FIRE
from pymatgen.io.ase import AseAtomsAdaptor

from config_step02 import (
    FMAX_MLIP,
    INPUT_SNAPSHOT,
    MACE_DEVICE,
    MACE_DTYPE,
    MACE_MODEL,
    MAX_STEPS_MLIP,
    MLIP_DIR,
    SYSTEMS,
)


GPA_TO_EV_A3 = 1.0 / 160.21766208
EV_A3_TO_GPA = 160.21766208


def validate_inputs() -> None:
    missing = [str(p) for p in SYSTEMS.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Estruturas finais da Etapa 01-R2 não encontradas:\n  "
            + "\n  ".join(missing)
        )


def snapshot_inputs() -> None:
    INPUT_SNAPSHOT.mkdir(exist_ok=True)
    for mineral, path in SYSTEMS.items():
        shutil.copy2(path, INPUT_SNAPSHOT / f"{mineral}_experimental_primitiva.cif")


def cell_dict_from_pmg(structure) -> dict:
    lat = structure.lattice
    return {
        "a_A": float(lat.a),
        "b_A": float(lat.b),
        "c_A": float(lat.c),
        "alpha_deg": float(lat.alpha),
        "beta_deg": float(lat.beta),
        "gamma_deg": float(lat.gamma),
        "volume_A3": float(lat.volume),
    }


def stress_max_gpa_from_ase(atoms) -> float:
    stress = np.asarray(atoms.get_stress(voigt=True), dtype=float)
    return float(np.max(np.abs(stress)) * EV_A3_TO_GPA)


def max_force(atoms) -> float:
    f = np.asarray(atoms.get_forces(), dtype=float)
    return float(np.linalg.norm(f, axis=1).max())


def run_chgnet(mineral: str, input_path: Path):
    from chgnet.model import StructOptimizer
    from pymatgen.core import Structure

    print(f"\n[{mineral}] CHGNet — relaxação completa de célula + átomos")
    structure = Structure.from_file(input_path)

    relaxer = StructOptimizer(use_device="cuda")
    t0 = time.perf_counter()
    result = relaxer.relax(
        structure,
        fmax=FMAX_MLIP,
        steps=MAX_STEPS_MLIP,
        relax_cell=True,
        ase_filter="FrechetCellFilter",
        verbose=True,
    )
    dt = time.perf_counter() - t0

    final_structure = result["final_structure"]
    out_cif = MLIP_DIR / f"{mineral}_chgnet_relax.cif"
    final_structure.to(filename=str(out_cif), fmt="cif")

    traj = result.get("trajectory")
    energy = None
    nsteps = None
    if traj is not None:
        energies = getattr(traj, "energies", None)
        if energies is not None and len(energies) > 0:
            energy = float(energies[-1])
            nsteps = len(energies) - 1

    atoms = AseAtomsAdaptor.get_atoms(final_structure)
    # Calculadora CHGNet reaplicada apenas para diagnóstico final.
    atoms.calc = relaxer.calculator
    fmax = max_force(atoms)
    smax = stress_max_gpa_from_ase(atoms)

    return final_structure, {
        "mineral": mineral,
        "metodo": "CHGNet",
        "modelo": "CHGNet-pretrained",
        "energia_eV": energy,
        "fmax_eV_A": fmax,
        "stress_max_abs_GPa": smax,
        "nsteps": nsteps,
        "tempo_s": dt,
        **cell_dict_from_pmg(final_structure),
        "arquivo": out_cif.name,
    }


def build_mace_calculator():
    from mace.calculators import mace_mp

    kwargs = dict(
        model=MACE_MODEL,
        device=MACE_DEVICE,
        default_dtype=MACE_DTYPE,
        dispersion=False,
    )
    try:
        return mace_mp(**kwargs)
    except TypeError:
        # Compatibilidade defensiva com versões em que algum argumento
        # opcional tenha assinatura diferente.
        kwargs.pop("default_dtype", None)
        return mace_mp(**kwargs)


def run_mace(mineral: str, chgnet_structure):
    print(f"\n[{mineral}] MACE — relaxação completa a partir do resultado CHGNet")
    atoms = AseAtomsAdaptor.get_atoms(chgnet_structure)

    calc = build_mace_calculator()
    atoms.calc = calc

    filt = FrechetCellFilter(atoms)
    traj_path = MLIP_DIR / f"{mineral}_mace_relax.traj"
    log_path = MLIP_DIR / f"{mineral}_mace_relax.log"

    opt = FIRE(
        filt,
        trajectory=str(traj_path),
        logfile=str(log_path),
    )

    t0 = time.perf_counter()
    opt.run(fmax=FMAX_MLIP, steps=MAX_STEPS_MLIP)
    dt = time.perf_counter() - t0

    final_energy = float(atoms.get_potential_energy())
    final_fmax = max_force(atoms)
    final_smax = stress_max_gpa_from_ase(atoms)

    final_structure = AseAtomsAdaptor.get_structure(atoms)
    out_cif = MLIP_DIR / f"{mineral}_mace_relax.cif"
    write(out_cif, atoms, format="cif")

    return {
        "mineral": mineral,
        "metodo": "MACE",
        "modelo": MACE_MODEL,
        "energia_eV": final_energy,
        "fmax_eV_A": final_fmax,
        "stress_max_abs_GPa": final_smax,
        "nsteps": int(opt.nsteps),
        "tempo_s": dt,
        **cell_dict_from_pmg(final_structure),
        "arquivo": out_cif.name,
    }


def save_rows(rows: list[dict]) -> None:
    out = MLIP_DIR / "resumo_mlip.csv"
    keys = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    meta = {
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "mace_model": MACE_MODEL,
        "mace_dtype": MACE_DTYPE,
        "fmax_eV_A": FMAX_MLIP,
        "max_steps": MAX_STEPS_MLIP,
    }
    (MLIP_DIR / "metadata_mlip.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    validate_inputs()
    MLIP_DIR.mkdir(exist_ok=True)
    snapshot_inputs()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA não está disponível no ambiente MLIP. "
            "A Etapa 00 havia validado GPU; interrompendo para evitar "
            "execução acidental em CPU."
        )

    print("=" * 80)
    print("STEP 02A — PRÉ-RELAXAÇÃO MLIP")
    print("=" * 80)
    print("GPU:", torch.cuda.get_device_name(0))
    print("PyTorch:", torch.__version__)
    print("CUDA:", torch.version.cuda)
    print("MACE:", MACE_MODEL, "| dtype:", MACE_DTYPE)
    print("fmax:", FMAX_MLIP, "eV/Å")
    print("=" * 80)

    rows: list[dict] = []

    for mineral, input_path in SYSTEMS.items():
        chgnet_structure, row_chg = run_chgnet(mineral, input_path)
        rows.append(row_chg)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        row_mace = run_mace(mineral, chgnet_structure)
        rows.append(row_mace)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    save_rows(rows)

    print("\nSTEP 02A concluído.")
    print("Resumo:", MLIP_DIR / "resumo_mlip.csv")


if __name__ == "__main__":
    main()
