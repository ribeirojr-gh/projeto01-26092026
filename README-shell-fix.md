# Correção do shell + validação final da Etapa 00

O problema observado no terminal foi causado pelo arquivo anterior
`scripts/env_manager.sh`, que continha:

```bash
set -euo pipefail
```

Como esse arquivo é carregado com `source`, essas opções eram aplicadas ao
shell interativo. Assim, um comando que retornasse código 1 podia encerrar
a sessão do terminal.

A versão corrigida de `env_manager.sh` não altera mais as opções do shell.
Os scripts `run-stepXX.sh` continuam usando `set -euo pipefail` internamente,
onde isso é desejável.

## Instalação

Na raiz do projeto, faça backup do arquivo antigo:

```bash
cp scripts/env_manager.sh scripts/env_manager.sh.bak
```

Depois substitua pelo arquivo corrigido deste pacote:

```bash
cp CAMINHO_DO_PACOTE/scripts/env_manager.sh scripts/env_manager.sh
chmod +x scripts/env_manager.sh
```

Copie também `step00_final/` para a raiz do projeto e execute:

```bash
chmod +x step00_final/*.sh step00_final/*.py
./step00_final/run-step00-final.sh |& tee step00_final/saida-step00-final.txt
```
