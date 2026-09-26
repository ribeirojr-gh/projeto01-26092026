#!/usr/bin/env python3
from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

PAW_ROOT = STEP_DIR / "paw_generated"
PB_PBE_DIR = PAW_ROOT / "Pb" / "PBE"
PB_PBESOL_DIR = PAW_ROOT / "Pb" / "PBEsol"
U_PBE_DIR = PAW_ROOT / "U" / "PBE"
U_PBESOL_DIR = PAW_ROOT / "U" / "PBEsol"

RESULTS_DIR = STEP_DIR / "resultados_step04A"
LOGS_DIR = STEP_DIR / "logs"

ECUT = 1400.0
KGRID_PB = (6, 6, 6)
PB_A_REFERENCE = 4.95  # Å; apenas geometria fixa para gate PAW-PBE oficial vs gerado

PB_ENERGY_GATE_MEV_ATOM = 0.5
PB_STRESS_GATE_GPA = 0.01
