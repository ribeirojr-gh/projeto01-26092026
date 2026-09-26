#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

STEP05A = PROJECT_ROOT / "step05A_host_supercells"
SC_DIR = STEP05A / "resultados_step05A" / "supercells_R1"

SUPERCELLS = {
    "calcita": {
        80: SC_DIR / "calcita_det8_80atoms_R1.traj",
        160: SC_DIR / "calcita_det16_160atoms_R1.traj",
        240: SC_DIR / "calcita_det24_240atoms_R1.traj",
    },
    "dolomita": {
        80: SC_DIR / "dolomita_det8_80atoms_R1.traj",
        160: SC_DIR / "dolomita_det16_160atoms_R1.traj",
        240: SC_DIR / "dolomita_det24_240atoms_R1.traj",
    },
}

HOST_PAW_DIR = (
    PROJECT_ROOT / "step03_paw_pbesol_benchmark"
    / "paw_generated" / "PBEsol"
)
PB_PAW_DIR = (
    PROJECT_ROOT / "step04_u_pb_paw_validation"
    / "paw_generated" / "Pb" / "PBEsol"
)

RESULTS = SCRIPT_DIR / "resultados_step05B_R1"
LOGS = SCRIPT_DIR / "logs_R1"
RELAX = RESULTS / "relax"

XC = "PBEsol"
ECUT_EV = 1400.0
SMEARING_EV = 0.05

# O protocolo original usou 24 A e, para a célula de 80 átomos,
# isso pode gerar uma malha com produto muito alto. O Linux encerrou
# o rank 0 com SIGKILL antes de qualquer resultado, compatível com OOM.
#
# R1:
#   - relaxação iônica: Gamma-only;
#   - energia final do gate: malha física com min_distance=16 A.
# O objetivo continua sendo apenas convergência de tamanho, não energia
# de formação final.
KPT_MIN_DISTANCE_DIAGNOSTIC_A = 24.0
KPT_MIN_DISTANCE_FINAL_A = 16.0

LOCAL_RELAX_RADIUS_A = 4.5
LOCAL_FMAX_EV_A = 0.05
GAMMA_FINAL_FMAX_EV_A = 0.025
MAX_LOCAL_STEPS = 100
MAX_GAMMA_STEPS = 180

# Se as forças na malha final forem altas, fazemos uma correção curta
# na mesma malha antes de registrar a energia.
DENSE_RELAX_TRIGGER_EV_A = 0.06
DENSE_FINAL_FMAX_EV_A = 0.04
MAX_DENSE_STEPS = 60

MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV = 0.10
MAX_DELTA_RELAXATION_ENERGY_EV = 0.10
MAX_DELTA_MEAN_PBO6_A = 0.05

MAX_FINAL_FORCE_EV_A = 0.05
MIN_PBO_A = 2.0
MAX_PBO_A = 3.5
