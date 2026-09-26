# Step 02-R4 — Convergência estrutural observável

## Motivação

O R3 mostrou:

### Energia
A 1200 eV, em relação a 1600 eV:

- calcita: diferença ≈ 0.367 meV/átomo;
- dolomita: diferença ≈ 0.369 meV/átomo.

A energia já está muito bem convergida.

### Forças
A diferença de `fmax` entre 1200 e 1600 eV é menor que
0.0006 eV/Å em ambos os minerais.

### Stress
O desvio restante é quase inteiramente hidrostático.

Entre 1200 e 1600 eV, a parte desviadora do tensor muda menos de
aproximadamente 0.0002 GPa, enquanto a componente média diagonal ainda
desloca cerca de 0.24–0.27 GPa.

Assim, perseguir apenas a componente hidrostática em uma geometria
experimental que ainda não é o mínimo PBE pode exigir cutoffs excessivos
sem demonstrar que a geometria relaxada muda de forma material.

## Objetivo

Comparar diretamente as estruturas PBE relaxadas em:

```text
1000 eV
1200 eV
1400 eV
```

com:

```text
k = 5x5x5
PAW = PBE oficial GPAW
Pulay correction = dedecut='estimate'
MPI = 4
```

## Relaxação

Para cada cutoff:

1. usa preferencialmente o CIF final do MACE como ponto de partida;
2. relaxa célula + átomos com `FrechetCellFilter`;
3. `BFGS`, `fmax = 0.01 eV/Å`;
4. refina/verifica as posições com célula fixa até `0.005 eV/Å`.

O uso do MACE aqui serve apenas para reduzir o número de passos DFT.
A energia final e a geometria são determinadas integralmente pelo GPAW/PBE.

## Critério de seleção

O candidato é 1200 eV e a referência é 1400 eV.

1200 eV será aprovado para ambos os minerais somente se:

```text
máxima diferença relativa em a,b,c <= 0.10 %
diferença relativa de volume <= 0.20 %
máxima diferença das ligações médias M-O/C-O <= 0.005 Å
```

Esses critérios testam diretamente as grandezas de interesse para a
relaxação estrutural.

## Execução

Descompacte na raiz do projeto:

```bash
chmod +x scripts/env_manager.sh step02_R4_structural_convergence/*.sh
./step02_R4_structural_convergence/run-step02-R4.sh
```

O ambiente `.envs/gpaw` é carregado automaticamente.

## Checkpoint

Cada relaxação finalizada produz um JSON e um CIF. Se a execução for
interrompida, basta executar novamente o mesmo comando; combinações
mineral/cutoff já concluídas serão reutilizadas.

## Saídas

```text
step02_R4_structural_convergence/saida-step02-R4.txt

step02_R4_structural_convergence/resultados_R4/
├── geometrias_relaxadas_R4.csv
├── convergencia_estrutural_1200_vs_1400.csv
├── decisao_step02_R4.json
├── calcita_PBE_*eV_final.cif
└── dolomita_PBE_*eV_final.cif
```

## Arquivos a compartilhar

```text
saida-step02-R4.txt
resultados_R4/geometrias_relaxadas_R4.csv
resultados_R4/convergencia_estrutural_1200_vs_1400.csv
resultados_R4/decisao_step02_R4.json
```
