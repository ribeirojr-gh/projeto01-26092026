# Step05A-R1 — correção geométrica das supercélulas

Os hosts pristinos do Step05A foram aprovados e não serão recalculados.

## Por que existe esta R1?

O algoritmo original enumerou HNFs e estimou a menor translação periódica
testando combinações inteiras apenas no intervalo `[-2,2]`.

Isso é seguro para bases compactas, mas as células det=16 e det=24
selecionadas ficaram muito cisalhadas. Exemplo: havia vetores de base de
60–150 Å mesmo com uma distância periódica mínima da ordem de 13–18 Å.

Uma célula pode representar a mesma rede periódica com uma base muito
mais compacta. Antes de calcular defeitos, precisamos remover essa
ambiguidade.

## Correção

Para cada HNF dos determinantes 8, 16 e 24:

1. construímos a rede candidata;
2. aplicamos `ase.geometry.minkowski_reduce`;
3. usamos a menor norma da base Minkowski-reduzida como distância
   periódica mínima;
4. maximizamos essa distância;
5. em caso de empate, escolhemos a métrica mais isotrópica;
6. escrevemos a supercélula usando a transformação inteira já reduzida.

A documentação do ASE define `minkowski_reduce` como uma redução que
produz uma base com os vetores de rede mais curtos e retorna a
transformação unimodular correspondente.

## Custo

Nenhum DFT é executado. É apenas geometria cristalográfica.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step05A_host_supercells/saida-step05A-R1.txt

step05A_host_supercells/resultados_step05A/
  supercell_manifest_step05A_R1.json
  decisao_step05A_R1.json

step05A_host_supercells/resultados_step05A/supercells_R1/
  *.traj
  *.cif
```

Se `ready_for_step05B=true`, usamos as células R1 de 80 e 160 átomos no
gate de tamanho com Pb_Ca neutro. A célula de 240 átomos permanece como
fallback.
