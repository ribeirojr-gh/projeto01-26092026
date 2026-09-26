#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

REF_DIR = (
    PROJECT_ROOT
    / "step01_R2_final_references"
    / "referencias_finais"
)

HOSTS = {
    "calcita": {
        "input": REF_DIR / "calcita_ref_experimental_primitiva.cif",
        "spacegroup": 167,
        "formula": "CaCO3",
    },
    "dolomita": {
        "input": REF_DIR / "dolomita_ref_experimental_primitiva.cif",
        "spacegroup": 148,
        "formula": "CaMg(CO3)2",
    },
}

PAW_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

RESULTS = SCRIPT_DIR / "resultados_step05A"
RELAX = RESULTS / "hosts_relaxed"
SUPERCELLS = RESULTS / "supercells"
LOGS = SCRIPT_DIR / "logs"

XC = "PBEsol"
ECUT_RELAX_EV = 1400.0
ECUT_VALIDATE_EV = 1600.0
KPTS_PRIMITIVE = (5, 5, 5)
SMEARING_EV = 0.05

FMAX_ATOMS_EV_A = 0.01
FMAX_CELL_EV_A = 0.015
SYMPREC_A = 0.01

# Determinantes das supercélulas candidatas.
# Para uma primitiva de 10 átomos: 80, 160 e 240 átomos.
TARGET_DETERMINANTS = (8, 16, 24)

# Gate apenas da preparação geométrica do host.
MAX_FINAL_FORCE_EV_A = 0.03
MAX_FINAL_STRESS_GPA = 0.30
