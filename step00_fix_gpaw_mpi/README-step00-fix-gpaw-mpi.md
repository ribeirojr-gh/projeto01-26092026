# Step00-FIX — GPAW MPI

## Problema identificado

O teste:

```text
mpiexec -n 4 gpaw python verify_gpaw_mpi.py
```

lançava quatro processos, mas cada processo via:

```text
world.size = 1
```

Isso ocorre quando o ambiente contém o build `nompi` do GPAW.

O erro foi introduzido pela especificação:

```text
gpaw=25.7.0=*mpi*
```

porque a substring `mpi` também aparece em:

```text
nompi
```

Assim, o solver podia selecionar:

```text
py311_nompi_omp_3
```

## Correção

Este pacote força explicitamente:

```text
gpaw=25.7.0=py311_mpi_openmpi_omp_3
mpi=1.0=openmpi
openmpi
mpi4py
```

Não recria os outros ambientes e não altera resultados científicos.

## Instalação

Na raiz do projeto:

```bash
rm -rf /tmp/upb_fix_gpaw
mkdir -p /tmp/upb_fix_gpaw

unzip packages/petrobras_upb_step00_fix_gpaw_mpi.zip \
    -d /tmp/upb_fix_gpaw

cp -a /tmp/upb_fix_gpaw/petrobras_upb_project/. .
rm -rf /tmp/upb_fix_gpaw

chmod +x step00_fix_gpaw_mpi/*.sh
```

## Execução

```bash
./step00_fix_gpaw_mpi/run-step00-fix-gpaw-mpi.sh
```

## Saída

Compartilhe:

```text
step00_fix_gpaw_mpi/saida-step00-fix-gpaw-mpi.txt
```

O resultado esperado inclui:

```text
GPAW rank=0/4
GPAW rank=1/4
GPAW rank=2/4
GPAW rank=3/4
GPAW MPI: OK (4 processos)
GPAW MPI CORRIGIDO E VALIDADO
```
