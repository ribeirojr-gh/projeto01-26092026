# Etapa 01 v2 — Estruturas de referência

Esta versão foi preparada para o projeto após a validação da Etapa 00.

## Ambiente

A Etapa 01 usa exclusivamente:

```text
.envs/structures
```

O ambiente é carregado automaticamente por:

```text
scripts/env_manager.sh
```

Não execute `conda activate`, `micromamba activate` nem `source .venv/bin/activate`.

## Instalação do pacote

Descompacte o ZIP na raiz em que deseja atualizar o projeto.

O pacote contém:

```text
petrobras_upb_project/
├── scripts/
│   └── env_manager.sh
└── step01_structures/
    ├── 01_busca_estruturas.py
    ├── 00_check_step01_environment.sh
    ├── run-step01.sh
    └── README-step01.md
```

O `env_manager.sh` incluído é a versão corrigida que NÃO altera o shell
interativo com `set -euo pipefail`.

## Verificação opcional do ambiente

Na raiz do projeto:

```bash
chmod +x scripts/env_manager.sh step01_structures/*.sh
./step01_structures/00_check_step01_environment.sh \
    |& tee step01_structures/saida-step01-env.txt
```

## Chave do Materials Project

Antes da execução:

```bash
export MP_API_KEY="SUA_CHAVE_AQUI"
```

Sem a chave, o script continua processando o COD, mas não fará a comparação
com o Materials Project.

## Execução

Na raiz do projeto:

```bash
./step01_structures/run-step01.sh
```

O wrapper:

1. localiza automaticamente a raiz do projeto;
2. carrega `scripts/env_manager.sh`;
3. verifica se `.envs/structures` existe;
4. executa o Python dentro desse ambiente via micromamba;
5. mostra o Python e a versão efetivamente usados;
6. salva stdout + stderr em:

```text
step01_structures/saida-step01.txt
```

## Arquivos de saída

```text
step01_structures/estruturas/
step01_structures/tabelas/resumo_estruturas.csv
step01_structures/tabelas/comparacao_estrutural.csv
step01_structures/saida-step01.txt
```

Depois da execução, compartilhe:

```text
saida-step01.txt
tabelas/resumo_estruturas.csv
tabelas/comparacao_estrutural.csv
```
