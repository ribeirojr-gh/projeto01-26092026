# Etapa 00 — Preparação automática dos ambientes

Esta etapa instala, de forma local ao projeto, o gerenciador `micromamba` e quatro ambientes Python independentes.

## Ambientes

| Ambiente | Finalidade |
|---|---|
| `structures` | busca, leitura, construção e análise cristalográfica |
| `mlip` | CHGNet, MACE e PyTorch |
| `gpaw` | GPAW + ASE + MPI para DFT e NEB |
| `analysis` | pós-processamento, ajuste, difusão, figuras e phonopy |

Todos usam Python 3.11 para manter uma base conservadora de compatibilidade.

## Execução

A partir da raiz do projeto:

```bash
chmod +x step00_environment/*.sh scripts/env_manager.sh
./step00_environment/run-step00.sh
```

Toda a saída é exibida no terminal e salva em:

```text
step00_environment/saida-step00.txt
```

### Recriar completamente os ambientes

```bash
./step00_environment/run-step00.sh --force
```

## Instalação local

Os arquivos são instalados em:

```text
.tools/micromamba
.micromamba/
.envs/structures/
.envs/mlip/
.envs/gpaw/
.envs/analysis/
```

Não é necessário instalar Anaconda/Miniconda globalmente e não é necessário ativar manualmente nenhum ambiente.

## GPU

O instalador verifica `nvidia-smi` e, no ambiente `mlip`, testa:

```python
torch.cuda.is_available()
```

A ausência de GPU funcional não interrompe a instalação: CHGNet/MACE continuam disponíveis em CPU.

O script não altera nem instala o driver NVIDIA do sistema operacional.

## GPAW/MPI

O ambiente `gpaw` é instalado a partir do `conda-forge`, incluindo `gpaw-data`, `mpi4py` e `openmpi`.

Ao final é executado um teste de importação e um teste MPI com 4 processos.

## Uso automático nos próximos passos

Todos os wrappers `run-stepXX.sh` devem carregar:

```bash
source "${PROJECT_ROOT}/scripts/env_manager.sh"
```

e executar o programa com:

```bash
run_in_upb_env NOME_DO_AMBIENTE comando ...
```

Exemplo da Etapa 01:

```bash
run_in_upb_env structures python 01_busca_estruturas.py
```

Assim, o usuário nunca precisa executar `conda activate`, `micromamba activate` ou `source venv/bin/activate`.
