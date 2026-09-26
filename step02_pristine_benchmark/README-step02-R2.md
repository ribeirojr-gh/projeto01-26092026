# Step 02-R2 — Correção dos datasets PAW e retomada

## Diagnóstico do R1

O lançamento MPI e o `PYTHONPATH` estão corrigidos.

A execução chegou ao primeiro cálculo real:

```text
calcita, ecut=400 eV, k=5x5x5
```

e parou antes do SCF porque o GPAW tentou localizar:

```text
Ca.PBEsol
```

O conjunto de PAW datasets distribuído oficialmente com GPAW não contém
uma família PBEsol. As famílias distribuídas incluem PBE, LDA, revPBE,
RPBE e GLLBSC.

## Decisão metodológica da R2

A convergência numérica de energia de corte e malha k será feita com:

```text
XC = PBE
PAW datasets = PBE oficiais do GPAW
```

Isso evita gerar automaticamente PAWs PBEsol não validados.

O benchmark PBEsol será tratado em uma etapa separada, após a convergência
numérica, com uma estratégia de datasets explicitamente validada.

## O que NÃO será repetido

O Step 02A (CHGNet + MACE) já foi concluído e não é executado pelo wrapper R2.

## Pré-checagem nova

Antes do primeiro SCF, o script verifica explicitamente a disponibilidade de:

```text
Ca.PBE
C.PBE
O.PBE
Mg.PBE
```

## Retomada

Sobrescreva os arquivos do diretório existente:

```text
step02_pristine_benchmark/
```

e execute:

```bash
chmod +x step02_pristine_benchmark/*.sh
./step02_pristine_benchmark/run-step02-R2-resume.sh
```

O log será:

```text
step02_pristine_benchmark/saida-step02-R2.txt
```

## Checkpoint

Depois de cada ponto GPAW concluído é atualizado:

```text
resultados_gpaw/convergencia_gpaw_checkpoint.csv
```

Portanto, uma interrupção posterior não exige repetir os pontos já finalizados.

## Arquivos a compartilhar

```text
saida-step02-R2.txt
resultados_mlip/resumo_mlip.csv
resultados_gpaw/convergencia_gpaw.csv
resultados_gpaw/parametros_recomendados_gpaw.csv
resumo_step02/resumo_step02.txt
```
