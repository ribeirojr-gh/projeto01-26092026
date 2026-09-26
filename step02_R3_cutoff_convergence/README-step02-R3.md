# Step 02-R3 — Convergência refinada de cutoff

## Por que esta etapa é necessária

O Step 02-R2 mostrou que a malha k já está bem convergida, mas o cutoff não.

Entre 600 e 700 eV, para as estruturas primitivas experimentais:

- calcita: ΔE ≈ 43.38 meV/átomo e Δstress ≈ 3.58 GPa;
- dolomita: ΔE ≈ 44.01 meV/átomo e Δstress ≈ 4.14 GPa.

Assim, 700 eV não pode ser aceito apenas porque era o maior valor do scan.

## Correção de Pulay stress

A R3 usa:

```python
PW(ecut, dedecut="estimate")
```

O parâmetro `dedecut` fornece uma estimativa de dE/dEcut usada pelo GPAW
para corrigir o Pulay stress. Isso é especialmente importante antes de
relaxações de célula.

## Malha k

Não repetimos o scan de k-points.

O R2 mostrou que 5x5x5 é conservador para os dois minerais:

- calcita: em relação a 7x7x7, ΔE ≈ 0.020 meV/átomo e
  Δstress ≈ 0.0068 GPa;
- dolomita: em relação a 7x7x7, ΔE ≈ 0.182 meV/átomo e
  Δstress ≈ 0.0263 GPa.

Portanto, adotamos provisoriamente 5x5x5 para as células primitivas.

## Scan de cutoff

```text
600
700
800
900
1000
1200
1400
1600 eV
```

O script exige simultaneamente:

```text
ΔE <= 1 meV/átomo
Δstress <= 0.05 GPa
```

em DOIS intervalos consecutivos antes de declarar convergência.

O maior cutoff nunca é considerado automaticamente convergido.

## SCF

```text
XC = PBE
PAW = PBE oficiais do GPAW
density convergence = 1e-6
forces convergence = 1e-4
Fermi-Dirac = 0.05 eV
MPI = 4 processos
OMP_NUM_THREADS = 1
```

## Execução

Descompacte na raiz do projeto e execute:

```bash
chmod +x scripts/env_manager.sh step02_R3_cutoff_convergence/*.sh
./step02_R3_cutoff_convergence/run-step02-R3.sh
```

Toda a saída será gravada em:

```text
step02_R3_cutoff_convergence/saida-step02-R3.txt
```

## Checkpoint

Cada ponto finalizado é salvo em:

```text
resultados_R3/convergencia_cutoff_R3_checkpoint.csv
```

Se houver interrupção, execute novamente o mesmo comando. Os pontos
concluídos serão reutilizados.

## Arquivos a compartilhar

```text
saida-step02-R3.txt
resultados_R3/convergencia_cutoff_R3.csv
resultados_R3/recomendacoes_cutoff_R3.csv
resultados_R3/parametros_finais_R3.json
```
