# Step 02 — Pré-relaxação MLIP e convergência GPAW

## Objetivo

Esta etapa NÃO executa ainda a relaxação DFT final.

Ela faz:

1. pré-relaxação das estruturas experimentais pristinas com CHGNet;
2. refinamento da geometria CHGNet com MACE;
3. convergência sistemática de `ecut` e malha k com GPAW/PBEsol;
4. geração de um resumo para decidir os parâmetros da relaxação DFT.

Essa separação evita iniciar uma relaxação DFT longa antes de validar os
parâmetros numéricos.

## Entradas

A etapa lê automaticamente:

```text
step01_R2_final_references/referencias_finais/
├── calcita_ref_experimental_primitiva.cif
└── dolomita_ref_experimental_primitiva.cif
```

## Ambientes automáticos

- CHGNet/MACE: `.envs/mlip`, 1 processo, GPU.
- GPAW: `.envs/gpaw`, 4 processos MPI.
- Consolidação: `.envs/structures`.

Nenhuma ativação manual de ambiente é necessária.

## Modelos e parâmetros

### CHGNet

- relaxação de célula + átomos;
- `FrechetCellFilter`;
- `fmax = 0.02 eV/Å`;
- máximo de 500 passos;
- GPU CUDA.

### MACE

- modelo explicitamente fixado: `medium-mpa-0`;
- GPU CUDA;
- precisão `float64`;
- sem correção D3;
- relaxação de célula + átomos;
- `FrechetCellFilter`;
- FIRE;
- `fmax = 0.02 eV/Å`.

O MACE parte da geometria final do CHGNet.

### GPAW

- 4 processos MPI;
- modo PW;
- `xc = PBEsol`;
- Fermi-Dirac 0.05 eV;
- convergência da densidade SCF: `1e-6`.

Scan de energia de corte:

```text
400, 500, 600, 700 eV
```

com `5x5x5`.

Scan de k-points:

```text
3x3x3
4x4x4
5x5x5
6x6x6
7x7x7
```

com 600 eV.

Critérios preliminares de recomendação:

```text
ΔE <= 1 meV/átomo
Δstress <= 0.05 GPa
```

A recomendação automática NÃO é adotada cegamente. Os resultados serão
analisados antes da relaxação DFT.

## Execução

Na raiz do projeto:

```bash
chmod +x scripts/env_manager.sh step02_pristine_benchmark/*.sh
./step02_pristine_benchmark/run-step02.sh
```

Toda a saída (stdout + stderr) é mostrada no terminal e salva em:

```text
step02_pristine_benchmark/saida-step02.txt
```

## Resultados

### MLIP

```text
resultados_mlip/resumo_mlip.csv
resultados_mlip/metadata_mlip.json
resultados_mlip/*_chgnet_relax.cif
resultados_mlip/*_mace_relax.cif
resultados_mlip/*_mace_relax.traj
resultados_mlip/*_mace_relax.log
```

### GPAW

```text
resultados_gpaw/convergencia_gpaw.csv
resultados_gpaw/parametros_recomendados_gpaw.csv
resultados_gpaw/*.txt
```

### Resumo

```text
resumo_step02/comparacao_mlip_experimento.csv
resumo_step02/parametros_gpaw_para_revisao.csv
resumo_step02/resumo_step02.txt
```

## Arquivos a compartilhar após a execução

```text
saida-step02.txt
resultados_mlip/resumo_mlip.csv
resultados_gpaw/convergencia_gpaw.csv
resultados_gpaw/parametros_recomendados_gpaw.csv
resumo_step02/resumo_step02.txt
```

Após a análise desses arquivos serão definidos os parâmetros DFT definitivos
e preparada a relaxação PBE/PBEsol para o benchmark contra os dados
experimentais.
