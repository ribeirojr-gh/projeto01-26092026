# Etapa 01-R2 — Referências cristalográficas finais

## Motivação

A Etapa 01-R1 mostrou que a dolomita COD 1517797 e o Materials Project
mp-6459 têm a mesma topologia quando a correspondência é feita de forma
anônima, mas falham no `StructureMatcher` padrão.

A causa principal a testar/corrigir é a diferença de representação das
espécies: CIFs do COD podem conter estados de oxidação explícitos
(`Ca2+`, `Mg2+`, `C4+`, `O2-`), enquanto a estrutura do Materials Project
pode estar representada apenas por elementos.

O `StructureMatcher` padrão usa `SpeciesComparator`; esta R2 compara também
com `ElementComparator`, que ignora estados de oxidação para a comparação
geométrica.

## Referências adotadas

### Calcita
- Experimental: COD 1010928 — Elliott (1937)
- DFT/database: Materials Project mp-3953

### Dolomita
- Experimental: COD 1517796 — Effenberger, Kirfel & Will (1983)
- DFT/database: Materials Project mp-6459

A entrada COD 1517797 (1925) é mantida apenas no histórico do Step 01-R1 e
não será usada como referência primária da Etapa 02.

## Execução

Descompacte na raiz do projeto:

```bash
chmod +x step01_R2_final_references/*.sh
./step01_R2_final_references/run-step01-R2.sh
```

O ambiente `.envs/structures` é carregado automaticamente.

## Saídas a enviar

```text
step01_R2_final_references/saida-step01-R2.txt
step01_R2_final_references/tabelas_R2/resumo_referencias_finais.csv
step01_R2_final_references/tabelas_R2/comparacao_elementos_vs_especies.csv
step01_R2_final_references/tabelas_R2/coordenacao_referencias_finais.csv
step01_R2_final_references/tabelas_R2/manifesto_referencias_finais.json
```

Os CIFs finais são gravados em:

```text
step01_R2_final_references/referencias_finais/
```

A célula primitiva experimental será a estrutura inicial da Etapa 02.
