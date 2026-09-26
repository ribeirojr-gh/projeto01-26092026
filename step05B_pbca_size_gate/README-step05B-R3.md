# Step05B-R3 — GPAW com 8 MPI

O diagnóstico confirmou que os SIGKILL anteriores foram eventos reais do
OOM killer do Linux.

O dry-run mostrou:

```text
4 MPI:
    domain decomposition = 1 x 2 x 2

8 MPI:
    domain decomposition = 2 x 2 x 2
```

Para o caso calcita/80, 8 MPI também reduz o armazenamento de projetores
por rank aproximadamente pela metade.

## Protocolo R3

```text
GPAW 25.7
PBEsol
PW 1400 eV
Gamma-only para o finite-size gate
nbands = -8
8 MPI
OMP_NUM_THREADS = 1
domain = 8
band = 1
kpt = 1
ScaLAPACK automático
```

A calibração de Gamma continua sendo feita em cada host de 80 átomos com
uma malha `mindistance=16 Å`.

## Monitoramento de memória

Cada caso grava:

```text
resultados_step05B_R3/memory_monitor/*.csv
```

com `MemAvailable` e `SwapFree` a cada 2 segundos.

O runner começa por:

```text
calcita 80
calcita 160
```

Se calcita/160 voltar a sofrer OOM mesmo com 8 MPI, o workflow para
imediatamente e os casos >=160 átomos devem ser movidos para o cluster,
sem reduzir arbitrariamente o cutoff.

## Execução

```bash
bash step05B_pbca_size_gate/run-step05B.sh
```

Saída principal:

```text
step05B_pbca_size_gate/saida-step05B-R3.txt
step05B_pbca_size_gate/resultados_step05B_R3/decisao_step05B_R3.json
```
