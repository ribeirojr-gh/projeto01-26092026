# Etapa 00-R1 — Correção GPAW/MPI

## Por que esta correção existe?

A instalação original concluiu corretamente os ambientes `structures`, `mlip` e `analysis`.
Entretanto, o log mostrou que o pacote instalado para GPAW tinha o build:

```text
gpaw-25.7.0-py311_nompi_omp_3
```

Portanto, o teste anterior com `mpi4py` demonstrava que quatro processos Python eram lançados, mas não comprovava que o próprio GPAW estava compilado com MPI.

A correção R1:

1. preserva `structures`, `mlip` e `analysis`;
2. remove apenas `.envs/gpaw`;
3. instala explicitamente uma variante `mpi_openmpi` do GPAW;
4. executa `gpaw info`;
5. verifica `gpaw.mpi.world.size` com 4 processos;
6. executa `gpaw test` serial;
7. executa `mpiexec -n 4 gpaw test`.

## Instalação no projeto existente

Copie esta pasta para a raiz do projeto, ficando por exemplo:

```text
petrobras_upb_project/
├── .envs/
├── .tools/
├── scripts/
├── step00_environment/
├── step00_R1/
└── step01_structures/
```

Depois:

```bash
chmod +x step00_R1/*.sh
./step00_R1/run-step00-R1.sh
```

A saída será salva em:

```text
step00_R1/saida-step00-R1.txt
```

## Validação adicional de todos os ambientes

Depois da correção:

```bash
./step00_R1/00_check_environments_R1.sh |& tee step00_R1/saida-check-R1.txt
```

## Resultado esperado para GPAW

O trecho decisivo deve mostrar quatro linhas do tipo:

```text
GPAW rank=0/4
GPAW rank=1/4
GPAW rank=2/4
GPAW rank=3/4
```

O número após a barra deve ser `4`. Isso verifica o mundo MPI interno do GPAW, e não apenas o `mpi4py`.
