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

RESULTS = SCRIPT_DIR / "resultados_step05B_R3"
LOGS = SCRIPT_DIR / "logs_R3"
RELAX = RESULTS / "relax"

XC = "PBEsol"
ECUT_EV = 1400.0
SMEARING_EV = 0.05

# Validated: 4 MPI for 80-atom memory safety on local workstation, 8 MPI for cluster
MPI_PROCESSES = 4
NBANDS = -8

# Gamma is used only for the finite-size sequence.  Each 80-atom host
# receives an independent matched denser-k calibration.
KPT_CALIBRATION_MIN_DISTANCE_A = 16.0

LOCAL_RELAX_RADIUS_A = 4.5
LOCAL_FMAX_EV_A = 0.05
FINAL_FMAX_EV_A = 0.025
MAX_LOCAL_STEPS = 100
MAX_FINAL_STEPS = 180

MAX_GAMMA_TO_DENSE_RAW_DELTA_EV = 0.10
MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV = 0.10
MAX_DELTA_RELAXATION_ENERGY_EV = 0.10
MAX_DELTA_MEAN_PBO6_A = 0.05

MAX_FINAL_FORCE_EV_A = 0.04
MIN_PBO_A = 2.0
MAX_PBO_A = 3.5

# Safety preflight.  This is not a scientific convergence criterion.
MIN_AVAILABLE_MEMORY_GIB = 20.0
