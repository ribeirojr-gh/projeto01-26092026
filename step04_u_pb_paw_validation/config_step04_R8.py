#!/usr/bin/env python3
# Configuração autocontida do gate EOS Pb-PBE — Step04A-R8

ECUT_EV = 1400.0
KGRID = (6, 6, 6)
SMEARING_EV = 0.05

# Célula convencional fcc. ASE bulk(..., 'fcc', a=a) retorna célula primitiva.
LATTICE_CONSTANTS_A = (4.80, 4.90, 5.00, 5.10, 5.20)
REFERENCE_A = 5.00

# Critérios para comparar PAW-PBE gerado vs PAW-PBE oficial.
# Energia absoluta NÃO é critério porque cada dataset tem energia atômica
# de referência própria no formalismo GPAW.
MAX_RELATIVE_CURVE_DIFF_MEV_ATOM = 0.20
MAX_OFFSET_SPAN_MEV_ATOM = 0.20
MAX_STRESS_COMPONENT_DIFF_GPA = 0.01
MAX_A0_REL_DIFF_PERCENT = 0.05
MAX_B0_REL_DIFF_PERCENT = 1.0
