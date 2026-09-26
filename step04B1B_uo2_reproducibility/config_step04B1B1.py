#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

UO2_STRUCTURE = (
    PROJECT_ROOT
    / "step04B_compound_screening"
    / "estruturas"
    / "UO2_fluorite_exp.traj"
)

MATRIX_PBESOL_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

U_NC6_PBESOL_DIR = (
    PROJECT_ROOT
    / "step04_u_pb_paw_validation"
    / "paw_candidates"
    / "U_R5_pseudization"
    / "U14_nc6"
    / "PBEsol"
)

RESULTS_DIR = SCRIPT_DIR / "resultados_step04B1B1"
LOGS_DIR = SCRIPT_DIR / "logs"
RESTART_DIR = RESULTS_DIR / "restart"

ECUT_EV = 1400.0
KPTS = (3, 3, 3)
NBANDS = 80

# Shortlist construída a partir do Step04B1A-R5:
# 2.5 eV refina o intervalo entre 2 e 3 eV;
# 3.0 eV foi o melhor caso do protocolo comum;
# 4.0 eV é o controle estrutural (stress muito pequeno na célula experimental).
UEFF_GRID_EV = (2.5, 3.0, 4.0)

# Três domínios 1-k AFM equivalentes por simetria cúbica sem SOC.
AFM_DOMAINS = {
    "kz": (1.0, -1.0, -1.0, 1.0),
    "kx": (1.0, 1.0, -1.0, -1.0),
    "ky": (1.0, -1.0, 1.0, -1.0),
}

INITIAL_U_MOMENT_MUB = 2.0

# Guias experimentais usados somente para triagem.
GAP_TARGET_MIN_EV = 2.0
GAP_TARGET_MAX_EV = 2.5
MOMENT_TARGET_MUB = 1.74

# Gate de reprodutibilidade entre domínios AFM equivalentes.
MAX_DOMAIN_ENERGY_SPREAD_MEV_ATOM = 2.0
MAX_DOMAIN_GAP_SPREAD_EV = 0.10
MAX_DOMAIN_MOMENT_SPREAD_MUB = 0.05
