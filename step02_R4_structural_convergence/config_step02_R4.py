"""Configuração do Step 02-R4."""

from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

REF_DIR = (
    PROJECT_ROOT
    / "step01_R2_final_references"
    / "referencias_finais"
)

MLIP_DIR = (
    PROJECT_ROOT
    / "step02_pristine_benchmark"
    / "resultados_mlip"
)

SYSTEMS = {
    "calcita": {
        "experimental": REF_DIR / "calcita_ref_experimental_primitiva.cif",
        "mace": MLIP_DIR / "calcita_mace_relax.cif",
    },
    "dolomita": {
        "experimental": REF_DIR / "dolomita_ref_experimental_primitiva.cif",
        "mace": MLIP_DIR / "dolomita_mace_relax.cif",
    },
}

OUT_DIR = STEP_DIR / "resultados_R4"

XC = "PBE"
KGRID = 5

# Teste direto da convergência das grandezas estruturais.
ECUT_VALUES_EV = [1000, 1200, 1400]

FERMI_WIDTH_EV = 0.05

# Otimização completa com FrechetCellFilter.
FMAX_FULL_EV_A = 0.01
MAX_STEPS_FULL = 220

# Verificação final das posições com célula fixa.
FMAX_ATOMS_EV_A = 0.005
MAX_STEPS_ATOMS = 120

# Critérios para decidir se 1200 eV reproduz 1400 eV em grandezas observáveis.
MAX_LATTICE_REL_DIFF_PCT = 0.10
MAX_VOLUME_REL_DIFF_PCT = 0.20
MAX_BOND_DIFF_A = 0.005
