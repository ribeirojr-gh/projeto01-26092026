# Step05A — baseline de hosts e desenho de supercélulas

O Step04 foi encerrado com `production_authorization=true`.

Esta etapa ainda não introduz U ou Pb. Ela prepara um baseline novo e
auditável para calcita e dolomita antes dos defeitos.

## Hosts

Partimos das referências cristalográficas finais do Step01-R2 e relaxamos
novamente as primitivas com:

```text
PBEsol
PAWs Ca/Mg/C/O validados
1400 eV
5x5x5
```

A geometria é validada por single point em 1600 eV.

## Supercélulas

Em vez de assumir apenas 2x2x2, 3x3x2 etc., o script enumera matrizes
inteiras HNF de determinantes:

```text
8
16
24
```

e escolhe, em cada tamanho, a matriz que maximiza a menor translação
periódica da rede. Isso reduz a interação entre imagens periódicas de
defeitos para um número de átomos dado.

Para primitivas de 10 átomos, esperamos aproximadamente:

```text
det 8  -> 80 átomos
det 16 -> 160 átomos
det 24 -> 240 átomos
```

## Próximo gate

O Step05B utilizará Pb2+ substitucional em sítio Ca2+ como defeito piloto
neutro. A vantagem é que a comparação de tamanho pode ser feita antes de
entrarmos em correções de carga e compensação química do U.

Serão comparados os dois menores tamanhos selecionados. O terceiro fica
como fallback apenas se a energia de substituição ainda não estiver
convergida.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step05A_host_supercells/saida-step05A.txt

step05A_host_supercells/resultados_step05A/
  calcita_host_relax.json
  calcita_host_validate1600.json
  dolomita_host_relax.json
  dolomita_host_validate1600.json
  supercell_manifest_step05A.json
  decisao_step05A.json
```
