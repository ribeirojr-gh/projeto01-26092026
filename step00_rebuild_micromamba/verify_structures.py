#!/usr/bin/env python3
import sys
import numpy, scipy, pandas, yaml, requests, ase, pymatgen, spglib, seekpath
from mp_api.client import MPRester
print("Python:", sys.version.replace("\n", " "))
print("ASE:", ase.__version__)
print("NumPy:", numpy.__version__)
print("SciPy:", scipy.__version__)
print("structures: OK")
