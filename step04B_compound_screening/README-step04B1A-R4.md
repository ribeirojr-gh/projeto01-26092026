# Step04B1A-R4 — diagnóstico dirigido para UO2 DFT+U

## Evidência de entrada

A R2 mostrou:

- PbCO3: 1/1 convergido;
- delta-UO3: 2/2 convergidos;
- UO2 com Ueff=0: 2/2 convergidos;
- UO2 com Ueff=2–5 eV: 0/8 convergidos, mesmo após 500 e 700 ciclos.

Isso descarta uma falha geral do PAW, de MPI ou da estrutura. O problema
surge especificamente quando a correção Hubbard é ativada.

Os cálculos Ueff=0 também produziram `There are two Fermi-levels!` na rotina
de gap, consequência de `fixmagmom=True`.

## Hipótese testada

A R4 verifica, nesta ordem:

1. Ueff=4 eV normalizado, com o subgrupo magnético restaurado e sem
   `fixmagmom`;
2. Ueff=4 eV não normalizado (`:f,4.0,0`);
3. Ueff=4 eV com point group desligado, mas uma única distribuição de Fermi;
4. se todos falharem, rampa 0 → 0.5 → 1 → 2 → 3 → 4 eV preservando a
   densidade e as funções de onda entre os estágios.

A rampa modifica o objeto Hubbard armazenado nos setups do GPAW 25.7 e é
estritamente diagnóstica. Mesmo que funcione, a produção continuará
bloqueada até repetição por uma rota pública/reprodutível e validação
estrutural/eletrônica.

## Por que esta etapa é pequena?

Não repetimos toda a matriz. Testamos apenas Ueff=4 eV para `poly6` e `nc6`.
Se nenhuma rota convergir, novos scans de mixer serão interrompidos e a
metodologia passará a exigir controle explícito da matriz de ocupação (OMC)
ou outra implementação adequada para UO2.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B_compound_screening/saida-step04B1A-R4.txt
step04B_compound_screening/resultados_step04B1A_R4/decisao_step04B1A_R4.json
step04B_compound_screening/resultados_step04B1A_R4/UO2_poly6_diagnostic_R4.json
step04B_compound_screening/resultados_step04B1A_R4/UO2_nc6_diagnostic_R4.json
```

Os arquivos `.gpw` são preservados apenas para estratégias que convergirem.
