# Step04A-R6 — retomada dos gates

O R5 aprovou o candidato U14_poly6 (PBE e PBEsol) no `check_all()`.

A interrupção seguinte foi apenas de interface de linha de comando:
`gpaw python` interpretou `--label`, `--xc`, etc. como opções da própria CLI
GPAW. A R6 passa essa configuração por variáveis de ambiente herdadas pelos
quatro processos MPI.

Se os PAWs/seleção R5 já estiverem presentes, a geração não é repetida.

Execução:

```bash
bash executar_pacote_upb.sh
```

Compartilhar ao final:

```text
step04_u_pb_paw_validation/saida-step04A.txt
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_official.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_generated.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBEsol_generated.json
```
