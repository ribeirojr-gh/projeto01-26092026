# Step04A-R8 — correção metodológica do gate de Pb

## Por que o R6 marcou Pb como reprovado?

O cálculo em `a = 4.95 Å` deu:

```text
PAW PBE oficial:  -3.704362176 eV/atom
PAW PBE gerado:   -3.701500639 eV/atom
diferença:         2.861537 meV/atom
```

enquanto a diferença de stress foi somente:

```text
0.00015977 GPa
```

O gate antigo usava `|ΔE absoluto| <= 0.5 meV/atom`.

Esse critério não é adequado para comparar dois PAW datasets diferentes.
No GPAW a energia total é referenciada à energia dos átomos de referência
associada ao setup. Dois setups podem portanto ter um deslocamento constante
de energia sem diferença física na curva E(V), forças ou stresses.

## Gate R8

Comparamos PAW-PBE oficial e gerado em cinco constantes de rede fcc:

```text
4.80  4.90  5.00  5.10  5.20 Å
```

Para cada ponto são calculados energia e stress com:

```text
PBE
1400 eV
6×6×6
4 MPI
```

Depois calculamos:

- curva relativa `E(a)-E(5.00 Å)`;
- variação do offset `E_generated-E_official`;
- diferença máxima de stress;
- ajuste Birch-Murnaghan;
- `a0` e `B0`.

Critérios:

```text
max diferença das curvas relativas <= 0.20 meV/atom
span do offset de energia          <= 0.20 meV/atom
max diferença de stress            <= 0.01 GPa
diferença de a0                     <= 0.05 %
diferença de B0                     <= 1.0 %
```

A energia absoluta isolada deixa de ser critério.

## Execução

Baixe o ZIP e, na raiz:

```bash
bash executar_pacote_upb.sh
```

O pacote não regenera PAWs.

## Saídas

```text
step04_u_pb_paw_validation/saida-step04A-R8.txt
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_eos_comparison_R8.csv
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_eos_summary_R8.json
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
```
