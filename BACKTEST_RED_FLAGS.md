# BACKTEST_RED_FLAGS — os sinais estavam acesos antes do evento?

Executado por `scripts/18_backtest.py` em 18/08/2026. Resultados brutos em
`data/analytic/backtest_resumo.csv` e `backtest_detalhe.csv` (6.699 observações
veículo-mês).

## Desenho

- **Casos positivos**: veículos ligados a eventos confirmados por fonte oficial
  (`casos_regulatorios.csv`), vinculados por **CNPJ do prestador** ou do fundo.
- **Controles negativos**: veículos sem evento conhecido, pareados por faixa de
  patrimônio na mesma competência, amostragem determinística.
- **Anti-vazamento**: para um evento em T, só se lê competência ≤ T−1 mês.
  Janela observada: 12 meses.
- **Critério de disparo**: o veículo "acendeu" se o sinal apareceu em qualquer
  mês da janela. Ausência de dado ⇒ *não avaliável* (entra na cobertura),
  jamais "não disparou".
- **Lift** = taxa de disparo em positivos ÷ taxa em controles. Lift 1,0
  significa que o sinal não distingue nada.

## Resultado — CR023: liquidação extrajudicial do administrador (BCB, 15/01/2026)

151 veículos administrados pela entidade na competência anterior ao evento;
453 controles pareados.

| Sinal | Positivos | Controles | **Lift** | Antecedência mediana | Cobertura |
|---|---:|---:|---:|---:|---:|
| S5 — estrutura fechada (cotistas de interesse único) | 95,4% | 21,2% | **4,50** | 4 meses | 100% |
| S3 — subordinação abaixo de 5% | 83,3% | 32,2% | **2,59** | 0 mês | 99% |
| S1 — inadimplência ≈ zero com cedente concentrado | 27,6% | 15,5% | **1,77** | 2 meses | 38% |
| S4 — variação abrupta de patrimônio | 42,3% | 35,9% | 1,18 | 8 meses | 99% |
| S6 — cedente único acima de 80% | 30,5% | 44,7% | **0,68** | 1 mês | 39% |
| S2 — rolagem (recompra + substituição) | 0,0% | 7,0% | **0,00** | — | 87% |

## Leitura honesta destes números

**Dois sinais discriminam, dois não discriminam e dois funcionam ao contrário.**

- **S5 e S3 têm lift alto — e é aí que mora a maior armadilha do backtest.**
  "Cotistas de interesse único" e "subordinação baixa" descrevem o *modelo de
  negócio* dos veículos daquele administrador, que operava predominantemente
  estruturas fechadas. Um sinal pode ter lift alto por descrever a natureza do
  portfólio e não por antecipar o evento. **Não se pode afirmar poder preditivo
  a partir deste resultado.** O que se pode dizer é mais modesto e ainda útil:
  a carteira do administrador liquidado era estruturalmente mais fechada e menos
  capitalizada em subordinação que o mercado comparável — e isso era observável
  em dado público meses antes da liquidação.
- **S6 tem lift 0,68**: disparou *menos* nos casos positivos que nos controles.
  Como sinal isolado de risco, é contraproducente neste evento. Mantê-lo com
  peso positivo num score agregado degradaria o resultado.
- **S2 não disparou em nenhum positivo.** A rolagem de créditos, que é o
  mecanismo clássico de ocultação de atraso, não aparece neste caso — o que é
  coerente com o fato de o evento ter sido de natureza societária e de conduta
  do prestador, não de deterioração de carteira.
- **S1 é o único sinal com lastro documental externo**: no PAS CVM
  19957.006858/2019-25, a própria defesa atribuiu ao "reduzidíssimo histórico de
  inadimplências" a demora na detecção. O lift de 1,77 é modesto, mas a
  cobertura é baixa (38%) — o sinal só é avaliável onde há cedente declarado.

## Falso negativo documentado — CR024: stop order (CVM, 20/05/2026)

Três veículos vinculados. **Nenhum sinal disparou em nenhum mês da janela.**
O painel não teria antecipado esse evento. Registrado deliberadamente: um
backtest que só mostra acertos não é backtest.

## Caso não testável — CR022: liquidação de banco (BCB, 18/11/2025)

Nenhum veículo foi vinculado por denominação. É uma falha do *método de vínculo*
(busca por nome), não do sinal — e confirma a decisão de migrar o casamento para
CNPJ de prestador e vínculo societário documentado.

## Limitações que impedem declarar a metodologia validada

1. **Um único evento com vínculo robusto.** Um caso não sustenta inferência
   estatística. Intervalos de confiança seriam largos a ponto de inúteis.
2. **Confusão entre característica estrutural e precursor**, descrita acima.
   Corrigir exige pareamento por segmento, tipo de veículo e público-alvo — não
   apenas por faixa de patrimônio.
3. **Eventos históricos fora de alcance.** Os casos de 2012-2016 (Cruzeiro do
   Sul, Silverado) antecedem a existência de várias tabelas do informe: a de
   concentração de devedores começa em 2025, os campos de cedente em nov/2019.
   Não é possível reconstruir o conjunto completo de sinais para eles.
4. **Viés de sobrevivência e de reporte.** Veículos que param de informar sumem
   da série; a interrupção do reporte é, ela própria, informação — e passou a
   ser tratada como sinal separado depois deste exercício.
5. **Sem amostra fora do tempo.** Todos os eventos utilizáveis são recentes;
   não há partição temporal treino/teste.

## Conclusão

A metodologia permanece **EXPERIMENTAL**. O backtest não autoriza afirmar que os
sinais preveem eventos. Autoriza três coisas: (i) descartar S6 e S2 como sinais
isolados de risco no score agregado; (ii) manter S5, S3 e S1 como indicadores
descritivos de estrutura, com a advertência de que descrevem modelo de negócio;
(iii) exigir que qualquer publicação de score venha acompanhada de cobertura,
materialidade e força da evidência — nunca de um número único.

Próximo passo para validação real: ampliar a biblioteca de eventos com vínculo
por CNPJ (não por nome), incluir eventos de deterioração de carteira além dos de
conduta do prestador, e repetir com pareamento por segmento.
