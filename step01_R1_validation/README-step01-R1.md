# Etapa 01-R1 — Validação das referências cristalográficas

Esta etapa é um diagnóstico complementar ao Step 01.

Ela foi criada porque:

1. COD `9007286` da calcita é uma estrutura teoricamente derivada e não deve
   ser usada como referência experimental principal.
2. A comparação COD `1517797` × MP `mp-6459` da dolomita retornou
   `StructureMatcher=False`, apesar de ambas apresentarem grupo espacial R-3.

## O que a R1 faz

- preserva e analisa COD `9007286`;
- adiciona COD `1010928` como referência experimental de calcita;
- compara as duas referências de calcita com MP `mp-3953`;
- investiga COD `1517797` × MP `mp-6459`;
- testa `StructureMatcher` com e sem escalonamento de volume;
- executa scan de tolerâncias para a dolomita;
- testa correspondência anônima;
- compara ambientes locais Ca-O, Mg-O e C-O;
- gera células convencionais e primitivas padronizadas.

## Ambiente

O wrapper usa automaticamente:

```text
.envs/structures
```

via `scripts/env_manager.sh`.

## Instalação

Descompacte o pacote sobre a raiz do projeto atual, mantendo:

```text
petrobras_upb_project/
├── scripts/
├── step01_structures/
└── step01_R1_validation/
```

## Execução

```bash
chmod +x scripts/env_manager.sh step01_R1_validation/*.sh
./step01_R1_validation/run-step01-R1.sh
```

O log será salvo em:

```text
step01_R1_validation/saida-step01-R1.txt
```

## Arquivos a enviar depois

```text
saida-step01-R1.txt
tabelas_R1/referencias_cristalograficas_R1.csv
tabelas_R1/comparacoes_R1.csv
tabelas_R1/coordenacao_R1.csv
tabelas_R1/dolomita_scan_tolerancias_R1.csv
```
