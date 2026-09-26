#!/usr/bin/env python3
from gpaw.mpi import world
print(f"GPAW rank={world.rank}/{world.size}", flush=True)
if world.size != 4:
    raise SystemExit(f"ERRO: esperado world.size=4, obtido {world.size}")
world.barrier()
if world.rank == 0:
    print("GPAW MPI: OK (4 processos)", flush=True)
