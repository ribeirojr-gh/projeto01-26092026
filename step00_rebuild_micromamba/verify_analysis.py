#!/usr/bin/env python3
import sys
import numpy, scipy, pandas, matplotlib, h5py, yaml, tqdm
import uncertainties, phonopy, spglib, seekpath, ase
print("Python:", sys.version.replace("\n", " "))
print("ASE:", ase.__version__)
print("phonopy:", phonopy.__version__)
print("analysis: OK")
