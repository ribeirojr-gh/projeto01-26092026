# Projeto — U-Pb em Carbonatos / Petrobras

## Fluxo computacional

```text
Etapa 00  Ambientes e validação de software
Etapa 01  Estruturas de referência (calcita/dolomita)
Etapa 02  Relaxações e benchmark MLIP/DFT
Etapas DFT/NEB  ambiente gpaw
Pós-processamento/difusão  ambiente analysis
```

## Regra de execução

Os scripts `run-stepXX.sh` carregam automaticamente o ambiente correto através de:

```text
scripts/env_manager.sh
```

Não faça ativação manual de ambientes antes de executar as etapas.

## Primeira execução

```bash
chmod +x step00_environment/*.sh step01_structures/*.sh scripts/*.sh
./step00_environment/run-step00.sh
```

Depois:

```bash
export MP_API_KEY="SUA_CHAVE_AQUI"
./step01_structures/run-step01.sh
```
