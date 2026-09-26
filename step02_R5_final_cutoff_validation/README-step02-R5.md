# Step 02-R5 — Validação final de cutoff

## Resultado do R4

1200 eV foi rejeitado para os dois minerais.

### Calcita — 1200 vs 1400 eV

```text
máx. diferença relativa dos parâmetros de rede = 0.2327 %
diferença relativa do volume                    = 0.4299 %
máx. diferença de ligação média                 = 0.00391 Å
```

### Dolomita — 1200 vs 1400 eV

```text
máx. diferença relativa dos parâmetros de rede = 0.2576 %
diferença relativa do volume                    = 0.4764 %
máx. diferença de ligação média                 = 0.00420 Å
```

As ligações já passam pelo critério de 0.005 Å, mas parâmetros de rede e
volume ainda não passam.

A mudança estrutural caiu fortemente de 1000->1200 para 1200->1400 eV,
portanto a próxima verificação apropriada é 1400->1600 eV, e não uma nova
varredura extensa.

## Estratégia R5

Para cada mineral:

1. lê a estrutura final de 1400 eV do R4;
2. re-refina 1400 eV com tolerância mais estrita;
3. usa o 1400 eV refinado como estrutura inicial de 1600 eV;
4. compara diretamente 1400 versus 1600 eV.

Parâmetros:

```text
XC                 PBE
PAW                PBE oficial GPAW
k-grid             5x5x5
Pulay correction   dedecut='estimate'
MPI                4 processos
OMP_NUM_THREADS    1

fmax célula        0.005 eV/Å
fmax átomos        0.003 eV/Å
```

## Critérios finais

1400 eV será adotado somente se, para calcita e dolomita:

```text
máx. diferença relativa em a,b,c <= 0.10 %
diferença relativa de volume      <= 0.20 %
máx. diferença de ligação média   <= 0.005 Å
```

## Execução

Descompacte na raiz do projeto:

```bash
chmod +x scripts/env_manager.sh step02_R5_final_cutoff_validation/*.sh
./step02_R5_final_cutoff_validation/run-step02-R5.sh
```

Toda a saída será salva em:

```text
step02_R5_final_cutoff_validation/saida-step02-R5.txt
```

## Checkpoint

Cada relaxação concluída gera um CIF e JSON. Se houver interrupção, execute
novamente o mesmo comando e o resultado já concluído será reutilizado.

## Arquivos a compartilhar

```text
saida-step02-R5.txt
resultados_R5/geometrias_1400_1600_R5.csv
resultados_R5/convergencia_1400_vs_1600_R5.csv
resultados_R5/decisao_final_cutoff_R5.json
resultados_R5/PBE_1600_vs_experimento_R5.csv
```
