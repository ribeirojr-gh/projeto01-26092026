#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

CERUSSITE_TRAJ = (
    PROJECT_ROOT
    / "step04B_compound_screening"
    / "estruturas"
    / "cerussite_exp.traj"
)

MATRIX_PBESOL_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

PB_PBESOL_DIR = (
    PROJECT_ROOT
    / "step04_u_pb_paw_validation"
    / "paw_generated"
    / "Pb"
    / "PBEsol"
)

RESULTS_DIR = SCRIPT_DIR / "resultados_step04B2A"
LOGS_DIR = SCRIPT_DIR / "logs"
RELAX_DIR = RESULTS_DIR / "relax"

# Neutron single-crystal refinement:
# Chevrier et al., Z. Kristallogr. 199 (1992) 67–74.
EXP_A_A = 5.179
EXP_B_A = 8.492
EXP_C_A = 6.141
EXP_VOLUME_A3 = EXP_A_A * EXP_B_A * EXP_C_A
EXP_SPACEGROUP_NUMBER = 62
EXP_CARBONATE_APLANARITY_A = 0.026

# Numerical matrix to validate.
PROD_ECUT_EV = 1400.0
VAL_ECUT_EV = 1600.0

PROD_KPTS = (3, 2, 3)
VAL_KPTS = (4, 3, 4)

SMEARING_EV = 0.05

# Numerical gate.
MAX_NUM_DELTA_ENERGY_MEV_ATOM = 1.0
MAX_NUM_DELTA_GAP_EV = 0.03
MAX_NUM_DELTA_HYDROSTATIC_STRESS_GPA = 0.10
MAX_NUM_DELTA_FORCE_EV_A = 0.02

# Structural gate after relaxation and validation single point.
MAX_LATTICE_ERROR_PERCENT = 2.0
MAX_VOLUME_ERROR_PERCENT = 4.0
MAX_ANGLE_ERROR_DEG = 0.50
MAX_VALIDATION_FORCE_EV_A = 0.03
MAX_VALIDATION_STRESS_GPA = 0.30
MAX_CO_BOND_MEAN_REL_ERROR_PERCENT = 3.0
MAX_PBO9_MEAN_REL_ERROR_PERCENT = 4.0

# Optimizer thresholds.
ATOM_FMAX_STAGE1 = 0.03
ATOM_FMAX_FINAL = 0.01

# StrainFilter generalized force = stress * volume.
# For V ~270 Å^3, 0.15 eV corresponds to ~0.09 GPa.
CELL_FMAX_STAGE1 = 0.15
CELL_FMAX_FINAL = 0.10
