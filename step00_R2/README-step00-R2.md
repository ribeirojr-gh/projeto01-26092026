# Etapa 00-R2 — Validação corrigida do GPAW/MPI

A instalação R1 já está correta se `gpaw info` mostra:

```text
MPI enabled       yes
```

A paralisação observada no teste R1 não é evidência de falha do MPI.
Ela foi causada pelo uso de:

```bash
mpiexec -n 4 python - <<'PY'
...
PY
```

`python -` lê o programa de `stdin`, enquanto o Open MPI encaminha `stdin`
por padrão apenas ao rank 0. Em um programa MPI isso pode bloquear a
inicialização coletiva.

A R2 usa um arquivo Python físico e o launcher do GPAW:

```bash
mpiexec -n 4 gpaw python 00_test_gpaw_mpi.py
```

## Uso

Interrompa o comando R1 travado com:

```text
Ctrl+C
```

Copie a pasta `step00_R2` para a raiz do projeto e execute:

```bash
chmod +x step00_R2/*.sh
./step00_R2/run-step00-R2.sh
```

O log ficará em:

```text
step00_R2/saida-step00-R2.txt
```

O teste decisivo deverá conter:

```text
GPAW rank=0/4
GPAW rank=1/4
GPAW rank=2/4
GPAW rank=3/4
GPAW MPI: OK (4 processos).
```
