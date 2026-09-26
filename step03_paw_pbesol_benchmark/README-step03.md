# Step 03 — Validação PAW e benchmark PBE/PBEsol

## Objetivo

O Step 02 estabeleceu para as células primitivas:

```text
Ecut = 1400 eV
k    = 5x5x5
XC   = PBE
PAW  = PBE oficial GPAW
```

O PBE é numericamente convergido, mas expande os volumes experimentais de
calcita e dolomita. O Step 03 testa se PBEsol melhora a estrutura.

## Por que os PAWs são gerados

A distribuição oficial de setups GPAW contém famílias PBE, LDA, revPBE,
RPBE e GLLBSC, mas não uma família PBEsol.

O Step 03 usa `gpaw-setup`, o gerador antigo. A documentação atual do GPAW
informa que os setup releases oficiais distribuídos são gerados com esse
gerador.

São produzidos localmente:

```text
paw_generated/PBE/
    Ca.PBE
    Mg.PBE
    C.PBE
    O.PBE

paw_generated/PBEsol/
    Ca.PBEsol
    Mg.PBEsol
    C.PBEsol
    O.PBEsol
```

Os arquivos são identificados por SHA-256 em:

```text
paw_generated/paw_sha256.csv
```

Mantenha esses arquivos arquivados com o projeto.

## Gate científico 1 — PBE gerado versus PBE oficial

Não usamos automaticamente os PAWs PBEsol.

Primeiro, os PAWs PBE gerados com o MESMO gerador são usados para relaxar
calcita e dolomita a partir das estruturas PBE oficiais do Step 02.

O PBE gerado precisa reproduzir o PBE oficial dentro de:

```text
máx. diferença relativa em a,b,c <= 0.10 %
diferença relativa de volume      <= 0.20 %
máx. diferença de ligação média   <= 0.005 Å
```

Se qualquer mineral falhar, o script grava a decisão e NÃO executa PBEsol.

## Gate científico 2 — convergência PBEsol

Se o Gate 1 passar, PBEsol é relaxado em:

```text
1400 eV
1600 eV
```

com:

```text
k                  5x5x5
MPI                4
Pulay correction   dedecut='estimate'
fmax célula        0.005 eV/Å
fmax átomos        0.003 eV/Å
```

O mesmo critério estrutural do Step 02 é usado para 1400 vs 1600 eV.

## Benchmark final

São comparados contra os CIFs experimentais:

```text
PBE oficial / 1400 eV
PBEsol gerado / 1400 eV
```

para:

- parâmetros de rede;
- volume;
- Ca-O;
- Mg-O;
- C-O.

O programa produz uma sugestão preliminar, mas a escolha final do funcional
será feita após revisão dos resultados.

## Limitação importante

Este Step 03 valida os PAWs apenas para o subespaço químico Ca-Mg-C-O e para
calcita/dolomita. Ele NÃO valida PAWs para U ou Pb.

## Execução

Descompacte na raiz do projeto:

```bash
chmod +x scripts/env_manager.sh
chmod +x step03_paw_pbesol_benchmark/*.sh

./step03_paw_pbesol_benchmark/run-step03.sh
```

Não ative manualmente o ambiente. O wrapper usa `.envs/gpaw`.

Toda a execução fica em:

```text
step03_paw_pbesol_benchmark/saida-step03.txt
```

## Checkpoint

As relaxações completas geram CIF + JSON. Uma reexecução reutiliza os
resultados concluídos.

Os PAWs já gerados também são reutilizados.

## Arquivos a compartilhar

```text
saida-step03.txt

paw_generated/paw_sha256.csv

resultados_step03/validacao_PBE_generated_vs_official.csv
resultados_step03/PBE_generated_relaxed.csv
resultados_step03/convergencia_PBEsol_1400_vs_1600.csv
resultados_step03/PBEsol_relaxed_1400_1600.csv
resultados_step03/benchmark_PBE_vs_PBEsol_experimento.csv
resultados_step03/decisao_step03.json
```

Se o Gate PBE falhar, os arquivos PBEsol posteriores não serão criados;
nesse caso, envie o log, a validação PBE e a decisão.
