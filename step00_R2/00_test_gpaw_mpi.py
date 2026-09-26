#!/usr/bin/env python3
"""Teste mínimo do mundo MPI interno do GPAW."""

from gpaw.mpi import world

print(f"GPAW rank={world.rank}/{world.size}", flush=True)

if world.size != 4:
    raise SystemExit(
        f"ERRO: GPAW iniciou com world.size={world.size}; esperado 4."
    )

world.barrier()

if world.rank == 0:
    print("GPAW MPI: OK (4 processos).", flush=True)
