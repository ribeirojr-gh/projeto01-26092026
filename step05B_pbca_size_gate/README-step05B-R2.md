# Step05B-R2 — Gamma calibrado para contornar o limite de memória

## Diagnóstico do R1

O caso calcita/80 terminou com 6 k-points reduzíveis e convergiu.
O caso calcita/160 foi encerrado por SIGKILL mesmo usando somente
4 k-points reduzíveis.

Isso mostra que a memória não está sendo dominada apenas pelo número de
k-points; o crescimento do sistema e das wavefunctions PW a 1400 eV é
agora o gargalo principal.

## Estratégia R2

O finite-size gate passa a ser Gamma-only:

```text
80 -> 160 -> 240
```

com:

```text
PBEsol
1400 eV
nbands = -8
4 MPI
domain decomposition = 4
ScaLAPACK auto
```

`nbands=-8` mantém oito bandas vazias, reduzindo a memória em relação ao
default de aproximadamente 20% de bandas extras.

## Gamma não é aceito sem validação

Para cada host de 80 átomos, o mesmo defeito relaxado é recalculado com
uma malha mais densa (`mindistance=16 Å`).

Gate:

```text
|ΔEraw_Gamma - ΔEraw_dense| <= 0.10 eV
```

Só depois disso usamos Gamma para comparar 80, 160 e 240 átomos.

## Critérios de tamanho

```text
|ΔΔEraw|   <= 0.10 eV
|ΔErelax|  <= 0.10 eV
|Δ<Pb-O>6| <= 0.05 Å
```

A energia ainda é apenas um proxy de tamanho, não energia de formação.

## Execução

```bash
bash executar_pacote_upb.sh
```

Saída:

```text
step05B_pbca_size_gate/saida-step05B-R2.txt
step05B_pbca_size_gate/resultados_step05B_R2/decisao_step05B_R2.json
```
