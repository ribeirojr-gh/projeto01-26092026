# Step05B-R1 — correção para o SIGKILL no caso de 80 átomos

A execução original parou no primeiro caso, calcita/80 átomos, com:

```text
rank 0 ... exited on signal 9 (Killed)
```

Não houve traceback Python ou GPAW. Isso é compatível com encerramento
externo pelo sistema operacional, tipicamente pressão de memória.

O principal suspeito é a malha gerada por `min_distance=24 Å`: a célula
de 80 átomos tem distância periódica mínima de ~10 Å, então esse critério
pode exigir muitas k-points no BZ reduzível.

## R1

Antes de DFT, o pacote imprime as malhas para:

```text
24 Å  (protocolo original)
16 Å  (R1)
```

A estratégia passa a ser:

```text
relaxação Pb_Ca:
    Gamma-only
    1400 eV

energia do gate:
    host e Pb_Ca com a MESMA malha
    mindistance = 16 Å
    1400 eV
```

Se a força obtida na malha final exceder 0.06 eV/Å, o script executa
automaticamente uma correção iônica curta usando essa própria malha.

O valor usado para comparar 80, 160 e 240 átomos continua sendo:

```text
E(Pb_Ca) - E(host)
```

na mesma malha final para cada par host/defeito.

A energia de relaxação usada no gate é Gamma-only em todos os tamanhos,
logo também é comparável internamente.

## Importante

Esta etapa continua sendo apenas um gate de tamanho. Não produz energia
de formação final e não altera os parâmetros de produção definidos no
Step04.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Arquivos

```text
step05B_pbca_size_gate/saida-step05B-R1.txt

step05B_pbca_size_gate/resultados_step05B_R1/
  kpoint_preflight_step05B_R1.json
  fallback_request_step05B_R1.json
  decisao_step05B_R1.json
  ...
```
