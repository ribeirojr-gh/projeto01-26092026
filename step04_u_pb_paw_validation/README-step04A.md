# STEP 04A — PAWs de U/Pb: auditoria, geração e gate inicial

## Objetivo

Este pacote inicia o Step 04 sem autorizar prematuramente cálculos de defeitos.

O Step 03 aprovou a matriz Ca–Mg–C–O com PBEsol, 1400 eV e k-grid 5×5×5.
Agora precisamos validar os elementos pesados.

## Estratégia

### Pb

O conjunto oficial de PAWs do GPAW contém Pb/PBE. Assim:

1. gerar Pb/PBE com `gpaw-setup` (old generator);
2. comparar o setup gerado com o oficial em um single point fcc idêntico;
3. gerar Pb/PBEsol pelo mesmo old generator;
4. testar que o setup PBEsol carrega e executa com MPI.

O fcc Pb de `a=4.95 Å` é somente uma geometria fixa para o **gate PAW vs PAW**.
Não é ainda o benchmark químico de Pb(II).

### U

O conjunto oficial padrão do GPAW não fornece U/PBE.

No GPAW 25.7.0:
- `gpaw.atom.configurations` contém a configuração atômica de U;
- o old generator não contém parâmetros default para U;
- `generator2` possui um default explícito `U14` com 14 elétrons de valência:
  `6s,7s,6p,7p,6d,d,5f,f,G`, raio 2.5 Bohr.

Por isso o pacote usa:

```bash
gpaw dataset U -f PBE    -s -e 14 -w
gpaw dataset U -f PBEsol -s -e 14 -w
```

O `-s` ativa scalar relativity.

Importante: o pacote NÃO usa `-n`; portanto `generator2.check_all()` continua ativo.
Se o dataset reprovar as verificações internas, o Step04A para.

Mesmo que passe, o PAW de U continua classificado como **candidato**.
O GPAW documenta que generator2 está em desenvolvimento e recomenda sempre
comparação com referências all-electron/testes de aplicação.

## O que este Step04A NÃO faz

Ele ainda não:
- valida U(IV) em UO2;
- valida U(VI);
- valida Pb(II);
- escolhe U_eff;
- valida SOC;
- autoriza defeitos U/Pb em calcita/dolomita.

Esses itens pertencem ao Step04B.

## Instalação

Na raiz do projeto:

```bash
cd ~/SIMULACOES/petrobras/datacao/petrobras_upb_project

mkdir -p packages
# coloque o ZIP em packages/

rm -rf /tmp/upb_step04
mkdir -p /tmp/upb_step04

unzip packages/petrobras_upb_step04A_u_pb_paw_validation.zip \
    -d /tmp/upb_step04

cp -a /tmp/upb_step04/petrobras_upb_project/. .
rm -rf /tmp/upb_step04
```

Verifique:

```bash
test -f step04_u_pb_paw_validation/run-step04A.sh \
    && echo "OK: Step04A instalado" \
    || echo "ERRO: Step04A ausente"
```

Permissões:

```bash
chmod +x step04_u_pb_paw_validation/*.sh
```

## Execução

```bash
./step04_u_pb_paw_validation/run-step04A.sh
```

## Saídas

Compartilhe primeiro:

```text
step04_u_pb_paw_validation/saida-step04A.txt
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
step04_u_pb_paw_validation/resultados_step04A/auditoria_geradores.json
step04_u_pb_paw_validation/resultados_step04A/paw_load_test.json
```

Também são úteis:

```text
resultados_step04A/inventario_setups_instalados.csv
resultados_step04A/Pb_PBE_official.json
resultados_step04A/Pb_PBE_generated.json
resultados_step04A/Pb_PBEsol_generated.json
resultados_step04A/paw_sha256.txt
```

## Gate

Se o Step04A passar, a próxima entrega será o Step04B:
- Pb(II) em composto de referência;
- U(IV) em UO2;
- U(VI) em composto de referência adequado;
- benchmark PBEsol;
- triagem DFT+U para 5f;
- pequeno teste SOC antes da autorização de produção.
