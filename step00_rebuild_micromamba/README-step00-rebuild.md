# Step00-R — reconstrução dos ambientes micromamba no prefixo atual

Este pacote deve ser usado quando o diretório do projeto foi movido/copied para um
novo caminho e os ambientes `.envs`/`.micromamba` vieram junto.

## O que faz

- preserva todos os resultados científicos;
- move `.envs` e `.micromamba` antigos para `backup_envs_YYYYMMDD-HHMMSS/`;
- recria `structures`, `analysis`, `mlip` e `gpaw` no caminho atual;
- mantém a arquitetura micromamba oficial do projeto;
- valida GPAW serial e com 4 MPI;
- valida CHGNet/MACE;
- oferece um wrapper para retomar o Step 03.

## Instalação do pacote

Na raiz do projeto:

```bash
rm -rf /tmp/upb_rebuild
mkdir -p /tmp/upb_rebuild
unzip ~/Downloads/petrobras_upb_rebuild_micromamba_current_prefix.zip -d /tmp/upb_rebuild
cp -a /tmp/upb_rebuild/petrobras_upb_project/. .
rm -rf /tmp/upb_rebuild
```

Depois:

```bash
chmod +x scripts/env_manager.sh
chmod +x step00_rebuild_micromamba/*.sh
./step00_rebuild_micromamba/run-step00-rebuild.sh
```

Compartilhe primeiro:

```text
step00_rebuild_micromamba/saida-step00-rebuild.txt
```

Somente se terminar com `AMBIENTES MICROMAMBA VALIDADOS COM SUCESSO`, retome:

```bash
./step00_rebuild_micromamba/02_resume_step03.sh
```

O Step 03 reutilizará os PAWs já gerados.

Depois compartilhe:

```text
step03_paw_pbesol_benchmark/saida-step03.txt
```

Se o Step 03 completar, envie também:

```text
step03_paw_pbesol_benchmark/resultados_step03/decisao_step03.json
step03_paw_pbesol_benchmark/resultados_step03/validacao_PBE_generated_vs_official.csv
step03_paw_pbesol_benchmark/resultados_step03/benchmark_PBE_vs_PBEsol_experimento.csv
```
