# Step05B — gate de tamanho Pb2+_Ca

O Step05A-R1 selecionou supercélulas Minkowski-reduzidas de 80, 160 e
240 átomos. Esta etapa usa Pb2+ substitucional em Ca2+ como defeito piloto
neutro, antes de introduzir U e compensação de carga.

Energia usada apenas no gate:
```text
ΔEraw(N) = E[Pb_Ca,N] - E[host,N]
```
Não é energia de formação. A diferença entre tamanhos é válida porque a
mesma troca -Ca +Pb aparece em todos os tamanhos.

K-points são gerados com
`ase.dft.kpoints.mindistance2monkhorstpack(min_distance=24 Å, even=False)`,
um critério baseado em distância real e independente da representação da
base da célula.

Relaxação:
1. vizinhança até 4.5 Å do Pb;
2. todos os átomos, célula fixa;
3. fmax final 0.025 eV/Å.

Gate 80 -> 160:
```text
|ΔΔEraw|   <= 0.10 eV
|ΔErelax|  <= 0.10 eV
|Δ<Pb-O>6| <= 0.05 Å
força      <= 0.04 eV/Å
```
Se falhar, 240 átomos é executado automaticamente somente para o host
necessário e o teste passa a ser 160 -> 240.

Execução:
```bash
bash executar_pacote_upb.sh
```

Saída principal:
```text
step05B_pbca_size_gate/saida-step05B.txt
step05B_pbca_size_gate/resultados_step05B/decisao_step05B.json
```
