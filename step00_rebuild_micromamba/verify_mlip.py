#!/usr/bin/env python3
import sys, torch, chgnet, mace
from chgnet.model import CHGNet
from mace.calculators import mace_mp
print("Python:", sys.version.replace("\n", " "))
print("torch:", torch.__version__)
print("chgnet:", getattr(chgnet, "__version__", "unknown"))
print("mace:", getattr(mace, "__version__", "unknown"))
print("CUDA disponível:", torch.cuda.is_available())
print("CUDA runtime:", torch.version.cuda)
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("capability:", torch.cuda.get_device_capability(0))
_ = CHGNet.load()
print("CHGNet.load(): OK")
print("MACE import: OK")
