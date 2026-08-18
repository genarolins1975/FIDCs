# Metodologia das red flags de FIDC — taxonomia v2 (oito pilares)

> **AVISO — METODOLOGIA EXPERIMENTAL.** Os pesos por severidade e os cortes das faixas de atenção são julgamento de especialista informado pela distribuição do mercado, **não** um modelo calibrado. Enquanto não houver backtest contra eventos realizados (liquidação extrajudicial, inadimplemento de série sênior, intervenção do regulador, processo sancionador), o score serve para **ordenar atenção supervisória** e nada mais. Score alto **não** é indício de irregularidade: é indício de que o veículo se afasta do padrão do mercado em dimensões que, em episódios públicos passados, precederam problemas — e também é o que se espera de fundos cujo mandato é justamente comprar crédito problemático.

- Data de corte: **2026-06-30**
- Universo canônico: **4.327 veículos** informantes na competência de corte (view `painel_saneado`)
- Janela de avaliação (persistência): **13 competências** (2025-06-30 a 2026-06-30)
- Janela de dados carregada: **25 competências** (2024-06-30 a 2026-06-30), para permitir defasagem de 12 meses e janelas móveis anuais
- Sinais implementados: **46**, distribuídos em 8 pilares
- Reprodução: `python3 scripts/13_red_flags_v2.py`

## 1. Regras de construção

**1.1 Ausente nunca vira zero.** Cada sinal declara explicitamente sua condição de avaliabilidade. Se o campo necessário é nulo — ou se o denominador é nulo ou zero, situação que no informe mensal da CVM é indistinguível de 'não reportado', porque o leiaute preenche zeros — o sinal é **não avaliável** para aquele veículo naquele mês. Não avaliável entra no denominador da cobertura; jamais é convertido em 'não disparou'.

**1.2 Limiar ancorado na distribuição do próprio mercado.** Todo limiar percentílico é recalculado em tempo de execução sobre o grupo de comparação do sinal, no mês de corte, e gravado no catálogo junto com o percentil usado, o n do grupo e a mediana observada. Números redondos só aparecem em sinais de **ocorrência** (identidade contábil violada, PL negativo, situação cadastral 'Em Liquidação'), onde não há distribuição contínua a percentilar, e em três limiares de definição contábil (deságio de 50%, tolerância de 0,5% em identidades, 1% do PL em débito tributário), sempre identificados como tais na coluna `limiar_origem`.

**1.3 Grupo de comparação explícito.** Comparar um FIDC-NP de precatórios com um FIDC de consignado é o erro metodológico mais comum na leitura desses dados. Cada sinal declara seu grupo — normalmente definido por porte de carteira e por existência efetiva da estrutura testada (só faz sentido medir subordinação em fundo que tem sênior **e** subordinada).

**1.4 Materialidade.** Cada sinal declara o porte mínimo abaixo do qual não vale a pena disparar. Um fundo de R$ 2 mi com inadimplência de 90% não é um problema de mercado.

**1.5 Persistência.** Cada sinal declara quantos meses **consecutivos**, terminando no corte, o disparo precisa aparecer para contar no score. Sinais de evento (colapso de PL, lacuna de reporte) exigem 1 mês; sinais de estado estrutural exigem 2 ou 3. A coluna `persistencia_atendida` em `rf2_sinais.csv` separa o disparo pontual do disparo persistente — ambos ficam no arquivo, por transparência.

**1.6 Nada de nota única.** `rf2_score_veiculo.csv` traz seis dimensões **separadas**, porque elas respondem a perguntas diferentes:

| Coluna | Pergunta que responde |
|---|---|
| `score_risco` (0-100) | Quanto do peso de severidade **avaliável** para este veículo efetivamente disparou de forma persistente? |
| `materialidade_max_rs` / `materialidade_soma_rs` | Quantos reais estão expostos ao maior sinal disparado (e à soma bruta de todos)? |
| `forca_evidencia` (0-1) | Que fração dos sinais disparados vem de campo **observado** no informe, e não de razão/variação **derivada**? |
| `cobertura_dados_pct` | Para que fração dos 46 sinais este veículo era sequer avaliável? |
| `persistencia_media_meses` | Há quantos meses, em média, os sinais estão acesos? |
| `atualidade` | Qual a competência mais recente com disparo? |

**1.7 Fórmula do score.**

```
score_risco = 100 x  Σ peso(sinais disparados E persistentes)
                     ---------------------------------------------
                       Σ peso(sinais avaliáveis para o veículo)
```

Pesos por severidade: `baixa` = 1, `média` = 3, `alta` = 6, `crítica` = 10. A normalização pelo peso **avaliável** (e não pelo peso total do catálogo) impede que baixa cobertura seja lida como baixo risco.

**1.8 Não classificável.** Veículo com cobertura de dados abaixo de 50% recebe `classificacao = 'não classificável'` e **nunca** é reportado como baixo risco. Ausência de sinal em veículo opaco é ausência de informação, não ausência de risco.

**1.9 Faixas de atenção.** Também definidas por percentil do próprio score, entre os veículos classificáveis com ao menos um disparo: `atenção alta` a partir de p99 (18.71), `atenção média` a partir de p90 (9.00), `atenção baixa` para qualquer score positivo abaixo disso.

## 2. Resumo por pilar

| Pilar | Sinais | Cobertura média | Veículos-sinal disparados | …dos quais persistentes |
|---|---:|---:|---:|---:|
| 1. Qualidade do ativo | 6 | 22.2% | 337 | 222 |
| 2. Estrutura e subordinação | 5 | 48.1% | 442 | 322 |
| 3. Concentração | 5 | 70.1% | 1010 | 855 |
| 4. Governança e conflitos | 5 | 94.5% | 373 | 363 |
| 5. Integridade dos dados e reportes | 7 | 68.7% | 672 | 574 |
| 6. Risco judicial e regulatório | 5 | 39.1% | 347 | 303 |
| 7. Inconsistências contábeis e econômicas | 6 | 69.3% | 139 | 93 |
| 8. PLD/FTP, lastro e movimentação | 7 | 55.4% | 225 | 209 |

## 3. Catálogo completo

### Pilar 1. Qualidade do ativo

#### QA-01 — Inadimplência abrangente no topo do mercado

**Definição.** Parcelas vencidas e não pagas (tabs V.B + VI.B) sobre o total de direitos creditórios por prazo (V.A + V.B + VI.A + VI.B) acima do percentil 95 do mercado entre veículos com carteira material.

**Fórmula.** `tx_inad = (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD) / (TAB_V_A_VL_DIRCRED_PRAZO + TAB_V_B_VL_DIRCRED_INAD + TAB_VI_A_VL_DIRCRED_PRAZO + TAB_VI_B_VL_DIRCRED_INAD)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC (tab I) >= R$ 50 mi e denominador de inadimplência > 0 (n = 1533) |
| Limiar | `>= 0.359344` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=1533, mediana=0.003347); dispara >= |
| Severidade | **alta** (peso 6) |
| Materialidade | DC (tab I) >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 35.43% do universo (1533 de 4327 veículos avaliáveis) |
| Veículos que disparam | 77 (53 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC-NP e FIDC de crédito judicial compram carteira JÁ vencida: inadimplência alta é o modelo de negócio, não deterioração. Fundos em amortização/liquidação concentram o estoque residual vencido. Consignado com atraso administrativo alto e baixa perda final também aparece aqui.

**Ação de investigação.** Cruzar com o segmento da carteira (tab II), a classificação SCR (X.8) e a série de 24 meses do próprio veículo: o que importa é a TENDÊNCIA e a cobertura por provisão, não o nível absoluto.

#### QA-02 — Deterioração acelerada da inadimplência em 12 meses

**Definição.** Variação em pontos percentuais da taxa de inadimplência abrangente contra a mesma competência do ano anterior, acima do p95 das variações.

**Fórmula.** `d_inad_12 = tx_inad(t) - tx_inad(t-12m)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC >= R$ 50 mi e tx_inad computável em t e em t-12m (n = 1258) |
| Limiar | `>= 0.144787` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=1258, mediana=0); dispara >= |
| Severidade | **alta** (peso 6) |
| Materialidade | DC (tab I) >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 29.07% do universo (1258 de 4327 veículos avaliáveis) |
| Veículos que disparam | 63 (35 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Fundo que entrou em amortização deixa de comprar crédito novo: o denominador encolhe e a taxa sobe sem que nada tenha piorado no estoque. Mudança de política de write-off também produz salto contábil sem evento econômico.

**Ação de investigação.** Verificar se o denominador (DC por prazo) caiu junto — decomposição numerador/denominador separa deterioração real de efeito de base.

#### QA-03 — Provisão nula diante de inadimplência material

**Definição.** Redução ao valor recuperável (I2A11 + I2B11) igual a zero, ou abaixo do p10 do mercado, com estoque inadimplente relevante.

**Fórmula.** `cob_prov = (TAB_I2A11_VL_REDUCAO_RECUP + TAB_I2B11_VL_REDUCAO_RECUP) / (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com estoque inadimplente >= R$ 10 mi (n = 658) |
| Limiar | `<= 0` |
| Origem do limiar | p10 da distribuição observada no grupo de comparação em 2026-06-30 (n=658, mediana=0.7516); dispara <= |
| Severidade | **alta** (peso 6) |
| Materialidade | inadimplência >= R$ 10 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 15.21% do universo (658 de 4327 veículos avaliáveis) |
| Veículos que disparam | 77 (46 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Crédito com coobrigação plena do cedente ou seguro de crédito não exige provisão no fundo. Carteira sem aquisição substancial de risco (tab I.2.B) tem a perda retida no cedente. Recompra automática contratual no atraso também dispensa provisão.

**Ação de investigação.** Ler o regulamento quanto a coobrigação/recompra e cruzar com a tab VII.D (recompras efetivas): se o cedente não recompra de fato, a ausência de provisão não se sustenta.

#### QA-04 — Inadimplência exatamente zero em carteira grande e concentrada

**Definição.** Carteira grande, cedente único dominante e ZERO parcela vencida reportada — o padrão de lastro 'bom demais' observado nos casos públicos de fraude de recebíveis antes do colapso.

**Fórmula.** `inad = 0 AND dc_tabI >= p90(mercado) AND pr_max >= 50`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC >= p90 do mercado e cedente declarado válido (n = 62) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | DC >= R$ 428 mi (p90 do mercado) e cedente máximo >= 50% |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 38.04% do universo (1646 de 4327 veículos avaliáveis) |
| Veículos que disparam | 26 (22 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Carteira de consignado público/INSS ou de recebíveis de utilities com desconto em folha tem inadimplência estruturalmente próxima de zero. Fundo recém-constituído ainda não tem safra vencida. Recompra automática do cedente no primeiro dia de atraso zera o estoque vencido por desenho contratual — e é lícita.

**Ação de investigação.** Testar lastro: pedir a conciliação de recebíveis do custodiante, verificar registro em registradora autorizada (Res. BCB 5.021) e conferir se a tab VII.D mostra recompras compatíveis com o 'zero'.

#### QA-05 — Inadimplência integralmente envelhecida (> 360 dias)

**Definição.** Fração do estoque inadimplente nas faixas B7 a B10 (acima de 360 dias) no p90 ou acima — crédito parado, com recuperação improvável.

**Fórmula.** `aging = (V_B7+V_B8+V_B9+V_B10 + VI_B7+VI_B8+VI_B9+VI_B10) / (V_B + VI_B)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com estoque inadimplente >= R$ 10 mi (n = 658) |
| Limiar | `>= 1` |
| Origem do limiar | p90 da distribuição observada no grupo de comparação em 2026-06-30 (n=658, mediana=0.3284); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | inadimplência >= R$ 10 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 15.21% do universo (658 de 4327 veículos avaliáveis) |
| Veículos que disparam | 94 (66 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC de crédito judicial e de precatórios opera por natureza com ativos de maturação plurianual: 100% do estoque acima de 360 dias é o esperado. Fundo em liquidação carrega apenas o resíduo antigo.

**Ação de investigação.** Confrontar com a provisão (QA-03): estoque velho e provisão baixa é a combinação relevante; estoque velho já provisionado é apenas resíduo.

#### QA-06 — Direitos creditórios performados não informados

**Definição.** Campo de créditos performados (I.2.A.4) não preenchido, impedindo separar risco de performance (obrigação do cedente ainda por cumprir) de risco de crédito puro.

**Fórmula.** `perf_share = TAB_I2A4_VL_CRED_DIRCRED_PERFM / TAB_I2A_VL_DIRCRED_RISCO`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC com aquisição de risco > 0 (n = 0) |
| Limiar | não calculável (grupo insuficiente) |
| Origem do limiar | grupo insuficiente (n=0) para percentilar |
| Severidade | **baixa** (peso 1) |
| Materialidade | DC com risco >= R$ 50 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 0.00% do universo (0 de 4327 veículos avaliáveis) |
| Veículos que disparam | 0 (0 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** O campo foi efetivamente descontinuado no layout pós-RCVM 175 — cobertura ~0% desde 2023. A não informação é falha de layout, não conduta do administrador.

**Ação de investigação.** Nenhuma ação sobre o veículo: registrar como LACUNA DE INFORMAÇÃO estrutural do informe mensal e endereçá-la ao regulador.

### Pilar 2. Estrutura e subordinação

#### ES-01 — Subordinação no fundo da distribuição do mercado

**Definição.** Colchão de subordinação (séries subordinadas + mezanino sobre o total das séries) abaixo do p5 do mercado entre estruturas que de fato têm sênior e subordinada.

**Fórmula.** `subord = SUM(VL_SERIE onde TIPO_COTA in ('subordinada','mezanino')) / SUM(VL_SERIE)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com série sênior > 0 E série subordinada/mezanino > 0 (n = 1010) |
| Limiar | `<= 0.0330676` |
| Origem do limiar | p5 da distribuição observada no grupo de comparação em 2026-06-30 (n=1010, mediana=0.3383); dispara <= |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 35.73% do universo (1546 de 4327 veículos avaliáveis) |
| Veículos que disparam | 51 (42 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Carteira de risco muito baixo (consignado público, crédito com garantia real líquida) suporta subordinação fina por desenho, validado por agência de rating. Estruturas com seguro de crédito ou carta de fiança bancária substituem colchão por garantia externa.

**Ação de investigação.** Comparar a subordinação com a inadimplência esperada da própria carteira (ES-03) e com o rating da série sênior; verificar gatilhos de recomposição no regulamento.

#### ES-02 — Erosão da subordinação em 12 meses

**Definição.** Queda em pontos percentuais do índice de subordinação contra a mesma competência do ano anterior, no p5 inferior das variações.

**Fórmula.** `d_subord_12 = subord(t) - subord(t-12m)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com sênior e subordinada em t e em t-12m (n = 809) |
| Limiar | `<= -0.310181` |
| Origem do limiar | p5 da distribuição observada no grupo de comparação em 2026-06-30 (n=809, mediana=9.605e-05); dispara <= |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 26.60% do universo (1151 de 4327 veículos avaliáveis) |
| Veículos que disparam | 41 (25 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Emissão programada de nova série sênior dilui o percentual subordinado sem consumo de colchão — é crescimento, não perda. Amortização de subordinada prevista em cronograma também reduz o índice de forma planejada.

**Ação de investigação.** Separar o efeito 'numerador' (subordinada encolheu: consumo de perda) do 'denominador' (sênior cresceu: alavancagem da estrutura) usando a tab X.2 em nível de série.

#### ES-03 — Colchão subordinado menor que a inadimplência líquida de provisão

**Definição.** Valor das séries subordinadas e mezanino inferior ao estoque de parcelas vencidas JÁ DEDUZIDA a provisão constituída: se a perda residual se materializar, a série sênior é atingida.

**Fórmula.** `v_sub < (V_B + VI_B) - (I2A11 + I2B11)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com série sênior > 0 e inadimplência líquida >= R$ 10 mi (n = 214) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **crítica** (peso 10) |
| Materialidade | inadimplência líquida de provisão >= R$ 10 mi e sênior emitida |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 4.95% do universo (214 de 4327 veículos avaliáveis) |
| Veículos que disparam | 74 (53 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Nem todo estoque vencido vira perda: taxas de recuperação de 60-90% são comuns em duplicatas e consignado, e o sinal compara estoque bruto de recuperação com colchão — é conservador por construção. Coobrigação do cedente devolve a perda ao originador. A base de disparo é alta (perto de um terço do grupo), o que reforça que o sinal só tem valor combinado a QA-01/QA-03.

**Ação de investigação.** Refazer o teste com a taxa de recuperação histórica da própria carteira e com a coobrigação contratada; se ainda assim o colchão não cobre, é caso de exame do enquadramento da sênior.

#### ES-04 — Patrimônio líquido nulo ou negativo

**Definição.** PL reportado na tab IV menor ou igual a zero — o veículo consumiu todo o capital dos cotistas.

**Fórmula.** `VL_PL <= 0`

| Campo | Valor |
|---|---|
| Grupo de comparação | Todos os veículos do painel canônico (n = 4327) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **crítica** (peso 10) |
| Materialidade | sem porte mínimo — PL negativo é relevante em qualquer escala |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 100.00% do universo (4327 de 4327 veículos avaliáveis) |
| Veículos que disparam | 189 (189 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Fundo encerrado que já distribuiu todo o patrimônio reporta PL zero na competência de fechamento. Veículo em fase pré-operacional ainda não integralizado também aparece com PL nulo.

**Ação de investigação.** Checar a situação cadastral (registro CVM) e a tab X.4: PL zero com resgate integral no mês é encerramento; PL negativo com carteira viva é insolvência.

#### ES-05 — Rentabilidade negativa na cota sênior

**Definição.** Pior rentabilidade mensal entre as séries sêniores abaixo do p5 do mercado — a classe que deveria estar protegida absorveu perda.

**Fórmula.** `rent_sen_min = MIN(TAB_X_VL_RENTAB_MES onde TIPO_COTA='senior')`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com série sênior efetivamente emitida (VL_SERIE > 0) (n = 1733) |
| Limiar | `<= -3.562` |
| Origem do limiar | p5 da distribuição observada no grupo de comparação em 2026-06-30 (n=1733, mediana=1.25); dispara <= |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 73.03% do universo (3160 de 4327 veículos avaliáveis) |
| Veículos que disparam | 87 (13 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Série sênior indexada a IPCA ou a ativo marcado a mercado tem rentabilidade nominal negativa em mês de fechamento de curva sem qualquer perda de crédito. Séries em amortização com ajuste de marcação também apresentam meses negativos.

**Ação de investigação.** Ver se a queda é isolada (marcação) ou persistente (perda de crédito) e se a subordinada já foi zerada — sênior negativa com subordinada positiva no mesmo mês é anomalia de cascata.

### Pilar 3. Concentração

#### CN-01 — Cedente único dominante

**Definição.** Maior percentual declarado de um único cedente (tab I) no p90 ou acima do mercado: o fundo é, na prática, um veículo de um originador só.

**Fórmula.** `pr_max = MAX(PR_CEDENTE) por veículo, com PR_CEDENTE em [0,100]`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos que declaram ao menos um cedente com percentual válido (n = 743) |
| Limiar | `>= 98.836` |
| Origem do limiar | p90 da distribuição observada no grupo de comparação em 2026-06-30 (n=743, mediana=53.78); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | DC >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 39.70% do universo (1718 de 4327 veículos avaliáveis) |
| Veículos que disparam | 75 (46 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC corporativo monocedente (fornecedores de uma indústria, financeira do próprio grupo) é a estrutura padrão do segmento e plenamente lícita. O que o sinal mede é dependência, não conduta.

**Ação de investigação.** Avaliar a solidez do cedente (rating, balanço) e a existência de coobrigação: concentração em cedente sólido é risco de crédito corporativo; em cedente frágil, é risco de fraude de lastro.

#### CN-02 — Índice HHI de cedentes no topo

**Definição.** Herfindahl-Hirschman calculado sobre os percentuais declarados dos até nove cedentes informados, no p90 ou acima.

**Fórmula.** `hhi_ced = SUM(PR_CEDENTE^2) sobre PR_CEDENTE em [0,100]`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos que declaram cedentes com percentual válido (n = 743) |
| Limiar | `>= 9774.09` |
| Origem do limiar | p90 da distribuição observada no grupo de comparação em 2026-06-30 (n=743, mediana=3752); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | DC >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 39.70% do universo (1718 de 4327 veículos avaliáveis) |
| Veículos que disparam | 75 (45 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** O informe só exige os nove maiores cedentes: um fundo pulverizado que declara apenas os nove maiores tem HHI subestimado, e um fundo monocedente tem HHI corretamente máximo. O viés é conservador, mas existe. Fundo cativo de grupo econômico é HHI 10.000 por desenho.

**Ação de investigação.** Confrontar com a cobertura declarada (soma dos percentuais): HHI alto com soma perto de 100% é concentração real; com soma baixa, é artefato do recorte top-9.

#### CN-03 — Base de cotistas mínima em veículo de porte

**Definição.** Até dois cotistas somados em todas as séries, num veículo com PL acima do p75 do mercado — não há verificação de preço por terceiros.

**Fórmula.** `n_cotistas = SUM(TAB_X_NR_COTST) por veículo (tab X.1)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Todos os veículos com número de cotistas informado (n = 1084) |
| Limiar | `<= 2` |
| Origem do limiar | limiar fixo 2 (<=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=1084) |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 156 mi (p75 do mercado) |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 100.00% do universo (4327 de 4327 veículos avaliáveis) |
| Veículos que disparam | 319 (298 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC exclusivo de tesouraria de um banco, de uma seguradora ou de uma EFPC tem legitimamente um cotista. FIC-FIDC master-feeder também tem cotista único (o feeder). Nada disso é irregular.

**Ação de investigação.** Verificar se o cotista único é parte relacionada ao cedente (GV-01): cotista único INDEPENDENTE do originador é estrutura de tesouraria; cotista único LIGADO é veículo espelho do próprio originador.

#### CN-04 — Carteira monossegmento

**Definição.** Um único segmento econômico (tab II, categorias A a K) responde por praticamente toda a carteira segmentada.

**Fórmula.** `mono_seg = MAX(TAB_II_[A..K]) / SUM(TAB_II_[A..K])`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira segmentada (tab II) > 0 (n = 606) |
| Limiar | `>= 0.999` |
| Origem do limiar | limiar fixo 0.999 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=606) |
| Severidade | **baixa** (peso 1) |
| Materialidade | DC >= R$ 200 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 74.76% do universo (3235 de 4327 veículos avaliáveis) |
| Veículos que disparam | 433 (389 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Praticamente todo FIDC é temático por regulamento: agro, consignado, veículos, judicial. Monossegmento é a regra do mercado, não a exceção — por isso a severidade é baixa e o sinal só serve combinado a outros do mesmo pilar.

**Ação de investigação.** Usar apenas como contexto para interpretar QA-01 e JR-03; isoladamente não justifica diligência.

#### CN-05 — Ativo composto quase inteiramente por cotas de outros FIDCs

**Definição.** Cotas de FIDC e de FIDC-NP (I.2.H + I.2.I) acima do p95 da razão sobre o ativo total — circularidade intramercado.

**Fórmula.** `circ = (TAB_I2H_VL_COTA_FIDC + TAB_I2I_VL_COTA_FIDC_NP) / TAB_I_VL_ATIVO`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com ativo total > 0 (n = 2159) |
| Limiar | `>= 0.996847` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=2159, mediana=0); dispara >= |
| Severidade | **baixa** (peso 1) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 96.46% do universo (4174 de 4327 veículos avaliáveis) |
| Veículos que disparam | 108 (77 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIC-FIDC é uma categoria regulada e comum: investir só em cotas de FIDC é exatamente o mandato. O sinal serve para medir DUPLA CONTAGEM de PL no agregado do mercado, e só vira alerta quando o fundo detido é do mesmo grupo (aí é CN-05 + GV-01).

**Ação de investigação.** Rastrear os FIDCs detidos via CDA (bloco BLC_2) e verificar se emissor e detentor pertencem ao mesmo grupo (flag EMISSOR_LIGADO).

### Pilar 4. Governança e conflitos

#### GV-01 — Cotista de interesse em fundo não exclusivo com base pulverizada

**Definição.** O administrador declara existência de cotista com relação de interesse (COTST_INTERESSE='S') num fundo que NÃO é exclusivo e que tem base de cotistas relevante — parte relacionada convivendo com investidores de fora.

**Fórmula.** `COTST_INTERESSE='S' AND FUNDO_EXCLUSIVO='N' AND n_cotistas >= 10`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com as flags de interesse e exclusividade preenchidas (n = 2159) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 100.00% do universo (4327 de 4327 veículos avaliáveis) |
| Veículos que disparam | 26 (22 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Gestor que investe capital próprio na subordinada é considerado ALINHAMENTO de interesses pelo mercado (skin in the game) e é prática recomendada. Sponsor que retém a subordinada por exigência de rating cai no mesmo caso.

**Ação de investigação.** Identificar QUAL classe a parte relacionada detém: subordinada = alinhamento; sênior comprada de si mesmo, ou subordinada mínima com sênior vendida ao varejo = conflito.

#### GV-02 — Gestor e administrador na mesma pessoa jurídica

**Definição.** CNPJ do gestor idêntico ao CNPJ do administrador no registro CVM: acumulação das funções de decisão de investimento e de controle.

**Fórmula.** `cnpj_gestor = CNPJ_ADMIN (registro_fundo x tab I)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com gestor e administrador identificados no registro (n = 2157) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 98.89% do universo (4279 de 4327 veículos avaliáveis) |
| Veículos que disparam | 24 (24 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** A RCVM 175 permite a administração fiduciária e a gestão pela mesma instituição, com segregação interna (chinese wall). Grandes bancos operam assim há décadas sem qualquer irregularidade.

**Ação de investigação.** Verificar se há custodiante e controlador independentes (GV-05) — a acumulação só é preocupante quando TODAS as funções de controle estão no mesmo grupo.

#### GV-03 — Troca de administrador nos últimos 12 meses

**Definição.** CNPJ do administrador informado na tab I difere do informado 12 competências antes.

**Fórmula.** `CNPJ_ADMIN(t) != CNPJ_ADMIN(t-12m)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com CNPJ_ADMIN informado em t e em t-12m (n = 1768) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **baixa** (peso 1) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 74.69% do universo (3232 de 4327 veículos avaliáveis) |
| Veículos que disparam | 223 (223 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Consolidação do setor de administração fiduciária, migração societária e reorganização de grupo produzem trocas em massa sem qualquer conteúdo de risco. Troca pode até ser SAUDÁVEL quando o administrador anterior está sob medida do regulador.

**Ação de investigação.** Só é relevante em conjunto: troca de administrador + queda de PL (IC-04) + salto de inadimplência (QA-02) no mesmo semestre.

#### GV-04 — Vínculo nominal com grupo alcançado por medida do BCB/CVM

**Definição.** Denominação do veículo, do administrador ou do gestor contém a marca de grupo econômico objeto de liquidação extrajudicial ou regime especial noticiado em fonte pública.

**Fórmula.** `UPPER(DENOM_SOCIAL || ADMIN || Gestor) LIKE qualquer termo da lista curada GRUPOS_MEDIDA`

| Campo | Valor |
|---|---|
| Grupo de comparação | Todos os veículos com denominação informada (n = 4327) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | sem porte mínimo |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 100.00% do universo (4327 de 4327 veículos avaliáveis) |
| Veículos que disparam | 47 (47 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Casamento por STRING é grosseiro: 'MASTER' aparece em razões sociais sem qualquer relação com o Banco Master. A troca do prestador já ocorrida não altera a denominação histórica do veículo. O sinal é uma PISTA de busca, jamais uma imputação.

**Ação de investigação.** Confirmar o vínculo societário no registro CVM e nos atos do BCB antes de qualquer uso; descartar homonímias uma a uma.

#### GV-05 — Auditor independente ou custodiante ausente no registro

**Definição.** Registro da classe (RCVM 175) sem auditor independente ou sem custodiante identificado — falha nos controles obrigatórios.

**Fórmula.** `Auditor IS NULL OR Custodiante IS NULL (registro_classe)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com registro de classe localizado (n = 2157) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 98.96% do universo (4282 de 4327 veículos avaliáveis) |
| Veículos que disparam | 53 (47 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Defasagem do cadastro é a explicação mais provável: o prestador existe e o campo não foi atualizado. Classes em fase pré-operacional legitimamente ainda não contrataram auditor.

**Ação de investigação.** Confirmar contra o formulário de informações periódicas e as demonstrações financeiras auditadas do exercício antes de tratar como ausência real.

### Pilar 5. Integridade dos dados e reportes

#### DI-01 — Percentuais de cedentes inconsistentes

**Definição.** Soma dos percentuais declarados de cedentes acima de 100,5%, ou existência de percentual fora do intervalo [0,100].

**Fórmula.** `pr_soma > 100.5 OR n_ced_invalido > 0`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos que declaram ao menos um cedente (n = 826) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **média** (peso 3) |
| Materialidade | DC >= R$ 50 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 44.21% do universo (1913 de 4327 veículos avaliáveis) |
| Veículos que disparam | 112 (112 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Alguns administradores preenchem o campo com o VALOR cedido em reais em vez do percentual, ou declaram percentual por bucket (com risco e sem risco) que soma mais de 100 quando agregado. É erro de preenchimento, não de conduta — mas invalida o dado.

**Ação de investigação.** Excluir o veículo das estatísticas de concentração por cedente e pedir reapresentação do informe.

#### DI-02 — Divergência entre direitos creditórios da tab I e das tabs V/VI

**Definição.** Distância relativa entre o estoque de DC do balanço (tab I) e o somatório por prazo de vencimento (tabs V e VI), acima do p95.

**Fórmula.** `desc_tabV = |dc_tabI - (V_A+V_B+VI_A+VI_B)| / dc_tabI`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC (tab I) >= R$ 50 mi (n = 1533) |
| Limiar | `>= 0.401747` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=1533, mediana=0.0005475); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | DC >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 35.43% do universo (1533 de 4327 veículos avaliáveis) |
| Veículos que disparam | 77 (62 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** A tab I reporta VALOR CONTÁBIL (líquido de ajuste a valor presente e de provisão) e as tabs V/VI reportam o FLUXO NOMINAL a vencer. Em carteiras de longo prazo com desconto relevante, a diferença é aritmética e esperada, não erro.

**Ação de investigação.** Estimar a taxa de desconto implícita na diferença: se ela for compatível com o prazo médio da carteira, é ajuste a valor presente; se não for, é inconsistência de reporte.

#### DI-03 — Cedentes não declarados em carteira de direitos creditórios material

**Definição.** Nenhum cedente com percentual válido informado na tab I, apesar de o veículo carregar estoque relevante de direitos creditórios: o pilar de concentração fica cego para esse veículo.

**Fórmula.** `pr_max IS NULL (nenhum PR_CEDENTE em [0,100] declarado) com dc_tabI >= R$ 200 mi`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC (tab I) >= R$ 200 mi (n = 606) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **baixa** (peso 1) |
| Materialidade | DC >= R$ 200 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 14.01% do universo (606 de 4327 veículos avaliáveis) |
| Veículos que disparam | 347 (288 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** A não declaração é ENDÊMICA — cerca de 57% dos veículos com DC acima de R$ 200 mi não informam cedente válido no corte. Por isso o sinal discrimina pouco entre veículos e recebe severidade baixa: ele documenta uma lacuna do informe mensal, não um desvio individual. FIDC que compra crédito originado por si (crédito direto) pode legitimamente não ter cedente terceiro a declarar.

**Ação de investigação.** Tratar como marcador de NÃO AVALIABILIDADE do pilar 3 para o veículo, e buscar a concentração por outra via (regulamento, relatório do custodiante, CDA).

#### DI-04 — Soma das séries de cotas incompatível com o patrimônio líquido

**Definição.** Somatório de quantidade x valor da cota de todas as séries (tab X.2) distante do PL da tab IV além do p99 do mercado.

**Fórmula.** `ser_vs_pl = |SUM(TAB_X_QT_COTA * TAB_X_VL_COTA) - VL_PL| / VL_PL`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com PL > 0 e séries informadas (n = 3424) |
| Limiar | `>= 0.105335` |
| Origem do limiar | p99 da distribuição observada no grupo de comparação em 2026-06-30 (n=3424, mediana=3.982e-12); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 10 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 95.63% do universo (4138 de 4327 veículos avaliáveis) |
| Veículos que disparam | 35 (11 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Amortização declarada entre a data da cota e o fechamento, ou séries encerradas ainda listadas, produzem descolamento temporário. Erro de arredondamento em fundos com cota de valor muito alto também aparece.

**Ação de investigação.** Reconciliar série a série com a tab X.4 (captações, amortizações e resgates) do mesmo mês.

#### DI-05 — Lacuna de reporte na série mensal

**Definição.** Competência sem informe entre a primeira e a última competência observadas do veículo na janela de 25 meses — descontinuidade que não se explica por entrada ou saída do universo.

**Fórmula.** `mês ausente com ord_ini < ord < ord_fim na grade CNPJ x competência`

| Campo | Valor |
|---|---|
| Grupo de comparação | Todos os veículos do painel canônico (n = 3424) |
| Limiar | `>= 1` |
| Origem do limiar | limiar fixo 1 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=3424) |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 100.00% do universo (4327 de 4327 veículos avaliáveis) |
| Veículos que disparam | 50 (50 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Reapresentação de informe fora do zip da competência, migração fundo->classe na adaptação à RCVM 175 e mudança de CNPJ informante geram lacuna aparente sem inadimplemento de dever.

**Ação de investigação.** Conferir o CNPJ da classe e do fundo no mapa de adaptação antes de tratar como falta de entrega.

#### DI-06 — Carteira estagnada ao centavo por três meses ou mais

**Definição.** Valor da carteira (tab I.2) idêntico ao centavo em três ou mais competências consecutivas — indício de reporte repetido em vez de reapurado.

**Fórmula.** `carteira(t) = carteira(t-1) por >= 3 meses consecutivos`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira > 0 informada (n = 3431) |
| Limiar | `>= 3` |
| Origem do limiar | limiar fixo 3 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=3431) |
| Severidade | **média** (peso 3) |
| Materialidade | carteira >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 95.82% do universo (4146 de 4327 veículos avaliáveis) |
| Veículos que disparam | 45 (45 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Fundo com carteira única de um contrato longo, sem amortização no período, legitimamente reporta o mesmo valor. Ativo bloqueado por decisão judicial também congela o saldo.

**Ação de investigação.** Verificar se PL e rentabilidade também estão congelados: carteira parada com PL variando é convivência normal; tudo parado é reporte automático não reapurado.

#### DI-07 — Componentes do ativo excedem a carteira declarada

**Definição.** Soma dos componentes identificáveis da carteira (DC com e sem risco, cotas de FIDC, valores mobiliários, títulos públicos, CDB) maior que a carteira total informada — impossibilidade aritmética.

**Fórmula.** `(I2A + I2B + I2H + I2I + I2C + I2D + I2E) > 1.005 * TAB_I2_VL_CARTEIRA`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira (tab I.2) > 0 (n = 3431) |
| Limiar | `>= 1.005` |
| Origem do limiar | limiar fixo 1.005 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=3431) |
| Severidade | **alta** (peso 6) |
| Materialidade | carteira >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | derivado |
| Cobertura | 95.82% do universo (4146 de 4327 veículos avaliáveis) |
| Veículos que disparam | 6 (6 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Dupla classificação de um mesmo ativo em duas rubricas (por exemplo, cota de FIDC contabilizada também como valor mobiliário) explica excedentes pequenos. Acima de poucos por cento, não há explicação contábil.

**Ação de investigação.** Solicitar a composição analítica da carteira ao administrador e conciliar rubrica a rubrica.

### Pilar 6. Risco judicial e regulatório

#### JR-01 — Créditos em ação judicial de cobrança relevantes

**Definição.** Valor de direitos creditórios em ação judicial (I.2.A.8) material em termos absolutos — a recuperação depende do Judiciário.

**Fórmula.** `TAB_I2A8_VL_CRED_ACAO_JUDIC >= R$ 5 mi`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos que reportam valor positivo no campo I.2.A.8 (n = 36) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | créditos em ação judicial >= R$ 5 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 0.90% do universo (39 de 4327 veículos avaliáveis) |
| Veículos que disparam | 36 (34 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Cobrança judicial é a etapa NORMAL do ciclo de recuperação de qualquer carteira de crédito madura; sua ausência é que seria estranha. O campo é preenchido por menos de 1% dos veículos, logo o sinal mede tanto litígio quanto disposição a reportar.

**Ação de investigação.** Comparar o valor em ação judicial com a provisão já constituída e com o estoque vencido acima de 360 dias (QA-05).

#### JR-02 — Carteira concentrada em créditos judiciais e precatórios

**Definição.** Créditos judiciais (tab II.J) somados a precatórios (tab II.I.1) acima do p90 da razão sobre a carteira segmentada.

**Fórmula.** `jud_seg = (TAB_II_J_VL_JUDICIAL + TAB_II_I1_VL_PRECAT) / TAB_II_VL_CARTEIRA`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira segmentada (tab II) > 0 (n = 1642) |
| Limiar | `>= 0.917219` |
| Origem do limiar | p90 da distribuição observada no grupo de comparação em 2026-06-30 (n=1642, mediana=0); dispara >= |
| Severidade | **baixa** (peso 1) |
| Materialidade | carteira segmentada >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 74.76% do universo (3235 de 4327 veículos avaliáveis) |
| Veículos que disparam | 165 (147 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC-NP de precatórios e de crédito judicial é categoria regulada, destinada a investidor profissional, e sua carteira É judicial por definição. O sinal descreve o mandato, não um desvio.

**Ação de investigação.** Tratar como marcador de SEGMENTO para escolher o grupo de comparação correto nos demais sinais, principalmente QA-01 e QA-05.

#### JR-03 — Classificação SCR concentrada em faixas E a H

**Definição.** Parcela das operações reportadas ao SCR classificadas entre E e H (Res. CMN 2.682) acima do p95 do mercado.

**Fórmula.** `scr_eh = (E+F+G+H) / (AA+A+B+C+D+E+F+G+H) sobre TAB_X_SCR_RISCO_OPER_*`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com DC >= R$ 50 mi e bloco X.8 preenchido (total > 0) (n = 832) |
| Limiar | `>= 0.149663` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=832, mediana=0); dispara >= |
| Severidade | **alta** (peso 6) |
| Materialidade | DC >= R$ 50 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 19.23% do universo (832 de 4327 veículos avaliáveis) |
| Veículos que disparam | 42 (18 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** O bloco X.8 cobre apenas crédito de origem financeira rastreável no SCR: duplicatas mercantis, precatórios e crédito judicial ficam de fora por construção, e um fundo com pouca base no SCR pode ter percentual E-H alto sobre uma amostra pequena e não representativa.

**Ação de investigação.** Checar a razão entre o total classificado no SCR e o DC do fundo: percentual E-H sobre menos de 20% da carteira não é conclusivo.

#### JR-04 — Classe ou fundo em liquidação com patrimônio relevante

**Definição.** Situação cadastral 'Em Liquidação' no registro CVM da classe ou do fundo, com PL ainda material.

**Fórmula.** `registro_classe.Situacao = 'Em Liquidação' OR registro_fundo.Situacao = 'Em Liquidação'`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com registro CVM localizado (n = 3422) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 98.96% do universo (4282 de 4327 veículos avaliáveis) |
| Veículos que disparam | 51 (51 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Liquidação ORDINÁRIA por decurso de prazo do regulamento é o encerramento normal de um FIDC de prazo determinado e não indica problema algum. O registro não distingue liquidação ordinária de liquidação por deliberação de assembleia em crise.

**Ação de investigação.** Ler a ata de assembleia que deliberou a liquidação e verificar se a amortização das sêniores está sendo honrada no cronograma.

#### JR-05 — Débito tributário declarado relevante

**Definição.** Campo de débito tributário do bloco X.8 positivo e acima de 1% do patrimônio líquido.

**Fórmula.** `TAB_X_DEBITO_TRIBUT / VL_PL >= 0.01, com TAB_X_DEBITO_TRIBUT > 0`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com PL > 0 e campo de débito tributário preenchido (n = 63) |
| Limiar | `>= 0.01` |
| Origem do limiar | limiar fixo 0.01 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=63) |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 10 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 1.59% do universo (69 de 4327 veículos avaliáveis) |
| Veículos que disparam | 53 (53 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** A semântica do campo é ambígua no leiaute: em vários informes o valor excede o próprio PL, o que sugere que parte dos administradores reporta o ESTOQUE DE CRÉDITOS COM DÉBITO TRIBUTÁRIO associado, e não uma obrigação do fundo. Enquanto a ambiguidade não for resolvida, o sinal mede reporte, não passivo.

**Ação de investigação.** Confirmar o significado do campo com o administrador e contra as demonstrações financeiras antes de qualquer uso — este sinal NÃO deve ser usado isoladamente.

### Pilar 7. Inconsistências contábeis e econômicas

#### IC-01 — Identidade patrimonial violada

**Definição.** Carteira maior que o ativo total, ou patrimônio líquido maior que o ativo total — impossibilidades contábeis diretas.

**Fórmula.** `carteira > 1.005*TAB_I_VL_ATIVO OR VL_PL > 1.005*TAB_I_VL_ATIVO`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com ativo total > 0 (n = 3471) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **crítica** (peso 10) |
| Materialidade | ativo total >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | derivado |
| Cobertura | 96.46% do universo (4174 de 4327 veículos avaliáveis) |
| Veículos que disparam | 1 (1 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Erro de digitação de casa decimal em um único campo produz o efeito sem qualquer irregularidade econômica; a tolerância de 0,5% já absorve arredondamento.

**Ação de investigação.** Pedir reapresentação do informe da competência e verificar se o erro se repete nos meses vizinhos.

#### IC-02 — Rentabilidade da cota sênior implausivelmente alta

**Definição.** Melhor rentabilidade mensal entre as séries sêniores acima do p99 do mercado — sênior é a classe de retorno-alvo limitado.

**Fórmula.** `rent_sen_max = MAX(TAB_X_VL_RENTAB_MES onde TIPO_COTA='senior')`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com série sênior emitida (VL_SERIE > 0) (n = 1733) |
| Limiar | `>= 4.5804` |
| Origem do limiar | p99 da distribuição observada no grupo de comparação em 2026-06-30 (n=1733, mediana=1.33); dispara >= |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 73.03% do universo (3160 de 4327 veículos avaliáveis) |
| Veículos que disparam | 18 (5 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Reversão de provisão excessiva, recebimento de crédito antes baixado e recomposição de série após período negativo produzem meses excepcionais legítimos. Séries de valor pequeno amplificam percentuais.

**Ação de investigação.** Verificar se o retorno excepcional é compatível com o resultado da carteira no mesmo mês; retorno de sênior descolado do resultado do fundo sugere marcação inadequada da cota.

#### IC-03 — Resultado positivo na sênior com inadimplência alta e provisão nula

**Definição.** Sênior rendendo positivo no mês enquanto a taxa de inadimplência está no quartil superior do mercado e nenhuma provisão foi constituída — resultado sem reconhecimento de perda.

**Fórmula.** `rent_sen_min > 0 AND tx_inad >= p75(mercado) AND prov = 0`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com sênior emitida, tx_inad computável e inadimplência > 0 (n = 554) |
| Limiar | `>= 1` |
| Origem do limiar | ocorrência binária: não há distribuição contínua a percentilar |
| Severidade | **alta** (peso 6) |
| Materialidade | inadimplência >= R$ 10 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 35.94% do universo (1555 de 4327 veículos avaliáveis) |
| Veículos que disparam | 36 (20 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Coobrigação plena do cedente ou seguro de crédito transferem a perda para fora do fundo, e nesse caso resultado positivo sem provisão é correto. Fundo sem aquisição substancial de risco (I.2.B) está no mesmo caso.

**Ação de investigação.** Ler a cláusula de coobrigação e conferir na tab VII.D se as recompras efetivamente ocorreram no volume compatível com o estoque vencido.

#### IC-04 — Colapso de patrimônio líquido em um único mês

**Definição.** Variação mensal do PL no p1 inferior da distribuição do mercado, partindo de base relevante.

**Fórmula.** `var_pl_m = VL_PL(t)/VL_PL(t-1) - 1`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com PL do mês anterior >= R$ 10 mi (n = 3359) |
| Limiar | `<= -0.492463` |
| Origem do limiar | p1 da distribuição observada no grupo de comparação em 2026-06-30 (n=3359, mediana=0.01217); dispara <= |
| Severidade | **alta** (peso 6) |
| Materialidade | PL do mês anterior >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | derivado |
| Cobertura | 77.63% do universo (3359 de 4327 veículos avaliáveis) |
| Veículos que disparam | 34 (34 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Amortização programada de série sênior, resgate de cotista único e encerramento ordenado do fundo produzem quedas abruptas totalmente planejadas. Cisão de classe também transfere PL sem perda.

**Ação de investigação.** Cruzar com a tab X.4: queda acompanhada de amortização/resgate equivalente é devolução de capital; queda sem contrapartida de pagamento é perda.

#### IC-05 — Crescimento explosivo do patrimônio em 12 meses

**Definição.** Crescimento do PL contra a mesma competência do ano anterior acima do p98 do mercado, partindo de base relevante.

**Fórmula.** `cresc_12 = VL_PL(t)/VL_PL(t-12m) - 1`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com PL de 12 meses antes >= R$ 10 mi (n = 1233) |
| Limiar | `>= 4.49861` |
| Origem do limiar | p98 da distribuição observada no grupo de comparação em 2026-06-30 (n=1233, mediana=0.1742); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | PL de 12m antes >= R$ 10 mi e PL atual >= R$ 100 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 61.84% do universo (2676 de 4327 veículos avaliáveis) |
| Veículos que disparam | 25 (16 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Fundo em ramp-up após a constituição cresce muitas vezes seu tamanho por desenho. Captação de nova série sênior de um investidor institucional produz salto legítimo. Incorporação de outro veículo também.

**Ação de investigação.** Verificar se o crescimento do PL veio acompanhado de crescimento proporcional da carteira e de diversificação de cedentes; crescimento com cedente único e sem carteira nova é o padrão de carrossel.

#### IC-06 — Descolamento entre patrimônio e carteira em 12 meses

**Definição.** Diferença entre o crescimento logarítmico do PL e o da carteira em 12 meses acima do p98: o patrimônio cresce sem que o ativo de crédito acompanhe.

**Fórmula.** `desloc_12 = ln(PL(t)/PL(t-12m)) - ln(carteira(t)/carteira(t-12m))`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com PL e carteira > 0 em t e em t-12m (n = 1241) |
| Limiar | `>= 0.238118` |
| Origem do limiar | p98 da distribuição observada no grupo de comparação em 2026-06-30 (n=1241, mediana=-0.0001928); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | PL >= R$ 100 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 70.81% do universo (3064 de 4327 veículos avaliáveis) |
| Veículos que disparam | 25 (17 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Fundo que captou e ainda não alocou mantém caixa em títulos públicos: PL cresce, carteira de crédito não. É prudência de alocação, não anomalia. Mudança de estratégia para renda fixa também produz o efeito.

**Ação de investigação.** Ver onde está o ativo não alocado (I.2.C a I.2.E): caixa em título público é benigno; ativo não identificado no informe merece exame.

### Pilar 8. PLD/FTP, lastro e movimentação

#### PO-01 — Giro anual da carteira no extremo do mercado

**Definição.** Aquisições de direitos creditórios em 12 meses sobre a carteira média do período, acima do p98 — volume de movimentação desproporcional ao estoque.

**Fórmula.** `aq_giro = SUM_12m(VII_A1_2 + VII_A2_2) / MEDIA_12m(TAB_I2_VL_CARTEIRA)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira média 12m > 0 e >= 10 das 12 competências (n = 1871) |
| Limiar | `>= 9.06809` |
| Origem do limiar | p98 da distribuição observada no grupo de comparação em 2026-06-30 (n=1871, mediana=0.1931); dispara >= |
| Severidade | **média** (peso 3) |
| Materialidade | carteira média 12m >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 80.45% do universo (3481 de 4327 veículos avaliáveis) |
| Veículos que disparam | 38 (37 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Duplicata mercantil de 30 dias gira 12 vezes ao ano por definição aritmética; antecipação de cartão gira ainda mais. Giro alto é a assinatura do factoring legítimo, não de lavagem.

**Ação de investigação.** Comparar o giro com o prazo médio declarado nas tabs V/VI: giro incompatível com o prazo médio da própria carteira é que é anômalo.

#### PO-02 — Rolagem elevada por recompra e substituição

**Definição.** Recompras (VII.D) somadas a substituições (VII.C) em 12 meses sobre a carteira média, acima do p95 — mecanismo clássico de mascarar atraso trocando o papel vencido por papel novo.

**Fórmula.** `roll_giro = SUM_12m(TAB_VII_C_2_VL_SUBST + TAB_VII_D_2_VL_RECOMPRA) / MEDIA_12m(TAB_I2_VL_CARTEIRA)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira média 12m > 0 e >= 10 das 12 competências (n = 1871) |
| Limiar | `>= 0.382235` |
| Origem do limiar | p95 da distribuição observada no grupo de comparação em 2026-06-30 (n=1871, mediana=0); dispara >= |
| Severidade | **alta** (peso 6) |
| Materialidade | carteira média 12m >= R$ 50 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | derivado |
| Cobertura | 80.45% do universo (3481 de 4327 veículos avaliáveis) |
| Veículos que disparam | 94 (88 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Substituição contratual de duplicata com vício formal (erro de emissão, divergência de valor) é obrigação do cedente prevista em regulamento e ocorre em volume relevante em carteiras pulverizadas. Recompra por coobrigação é a estrutura funcionando como desenhada.

**Ação de investigação.** Cruzar recompra com inadimplência: recompra alta com inadimplência reportada nula é a assinatura de rolagem; recompra alta com inadimplência também alta é coobrigação atuando.

#### PO-03 — Alienação de direitos creditórios a partes relacionadas

**Definição.** Venda de créditos ao próprio cedente ou a prestadores de serviço do fundo em 12 meses, em montante relevante frente à carteira.

**Fórmula.** `ali_rel_giro = SUM_12m(TAB_VII_B1_2_VL_CEDENTE + TAB_VII_B2_2_VL_PREST) / MEDIA_12m(carteira) >= 0.01`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira média 12m > 0 e >= 10 das 12 competências (n = 2953) |
| Limiar | `>= 0.01` |
| Origem do limiar | limiar fixo 0.01 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=2953) |
| Severidade | **alta** (peso 6) |
| Materialidade | carteira média 12m >= R$ 10 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 80.45% do universo (3481 de 4327 veículos avaliáveis) |
| Veículos que disparam | 10 (10 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Devolução de crédito ao cedente por vício de origem, ou exercício de opção de recompra prevista, aparece nesta rubrica sem qualquer conflito. O campo é preenchido por pouquíssimos veículos, o que torna o sinal raro e de alta especificidade, mas de baixa cobertura.

**Ação de investigação.** Obter o preço de venda e compará-lo ao valor contábil (PO-04): alienação a parte relacionada abaixo do valor contábil transfere valor do fundo para o originador.

#### PO-04 — Deságio anômalo em alienação a terceiros

**Definição.** Preço obtido na venda de créditos a terceiros sobre o valor contábil dos mesmos créditos, abaixo do p5 do mercado.

**Fórmula.** `desagio_terc = TAB_VII_B3_2_VL_TERCEIRO / TAB_VII_B3_3_VL_CONTAB_TERCEIRO <= 0,50 (deságio superior a 50% do valor contábil)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com alienação a terceiros e valor contábil ambos > 0 (n = 13) |
| Limiar | `<= 0.5` |
| Origem do limiar | limiar fixo 0.5 (<=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=13) |
| Severidade | **média** (peso 3) |
| Materialidade | alienação a terceiros >= R$ 1 mi |
| Persistência mínima | 1 mês (disparo pontual conta) |
| Tipo de evidência | observado |
| Cobertura | 0.69% do universo (30 de 4327 veículos avaliáveis) |
| Veículos que disparam | 5 (5 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Venda de carteira já vencida e provisionada acontece a poucos centavos por real e é exatamente o preço de mercado do ativo. Deságio profundo é esperado em cessão de carteira em recuperação.

**Ação de investigação.** Verificar se o crédito vendido já estava provisionado: deságio sobre ativo provisionado é realização de perda já reconhecida; sobre ativo não provisionado, é perda escondida até aquele momento.

#### PO-05 — Cedente pessoa física com participação relevante

**Definição.** Documento de cedente com 11 dígitos (CPF) associado a percentual declarado de 20% ou mais da carteira — originação por pessoa física em escala, ponto de atenção de PLD/FTP.

**Fórmula.** `pr_max_cpf >= 20, com pr_max_cpf = MAX(PR_CEDENTE) sobre length(digits(DOC_CEDENTE)) = 11`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos que declaram cedentes com percentual válido (n = 1293) |
| Limiar | `>= 20` |
| Origem do limiar | limiar fixo 20 (>=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=1293) |
| Severidade | **média** (peso 3) |
| Materialidade | DC >= R$ 10 mi |
| Persistência mínima | 3 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 39.70% do universo (1718 de 4327 veículos avaliáveis) |
| Veículos que disparam | 17 (11 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** FIDC do agronegócio compra CPR de produtor rural pessoa física, e FIDC de precatórios compra crédito de credor pessoa física: nos dois casos o cedente PF é o modelo de negócio. Também há preenchimento errado de CNPJ truncado a 11 dígitos.

**Ação de investigação.** Verificar o segmento (tab II) antes de qualquer leitura de PLD; se não for agro nem judicial, identificar a pessoa física e sua capacidade econômica de originar o volume declarado.

#### PO-06 — Aquisição relevante de créditos já vencidos ou inadimplentes

**Definição.** Compras de direitos creditórios vencidos e inadimplentes (VII.A.4 e VII.A.5) em 12 meses sobre a carteira média, acima do p99.

**Fórmula.** `aq_ruim_giro = SUM_12m(TAB_VII_A4_2 + TAB_VII_A5_2) / MEDIA_12m(carteira)`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos com carteira média 12m > 0 e >= 10 das 12 competências (n = 2953) |
| Limiar | `>= 0.700747` |
| Origem do limiar | p99 da distribuição observada no grupo de comparação em 2026-06-30 (n=2953, mediana=0); dispara >= |
| Severidade | **baixa** (peso 1) |
| Materialidade | carteira média 12m >= R$ 10 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 80.45% do universo (3481 de 4327 veículos avaliáveis) |
| Veículos que disparam | 30 (28 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** É literalmente o mandato do FIDC-NP: comprar crédito não performado e inadimplente com deságio para recuperar. O sinal só é informativo quando o veículo se apresenta como FIDC padronizado.

**Ação de investigação.** Confirmar o tipo do fundo (padronizado x NP) no registro: aquisição de crédito podre por fundo PADRONIZADO é que exige explicação.

#### PO-07 — Liquidez de curto prazo nula em condomínio aberto

**Definição.** Ativos conversíveis em caixa em até 30 dias (X.5) iguais a zero num fundo de condomínio ABERTO, onde o cotista pode pedir resgate.

**Fórmula.** `(TAB_X_VL_LIQUIDEZ_0 + TAB_X_VL_LIQUIDEZ_30) = 0 AND CONDOM='ABERTO'`

| Campo | Valor |
|---|---|
| Grupo de comparação | Veículos de condomínio aberto com PL > 0 (n = 927) |
| Limiar | `<= 0` |
| Origem do limiar | limiar fixo 0.0 (<=) — ancorado em definição contábil/regulatória, não em percentil (grupo de comparação com n=927) |
| Severidade | **alta** (peso 6) |
| Materialidade | PL >= R$ 10 mi |
| Persistência mínima | 2 meses consecutivos |
| Tipo de evidência | observado |
| Cobertura | 25.81% do universo (1117 de 4327 veículos avaliáveis) |
| Veículos que disparam | 31 (30 com persistência atendida) |

**Explicações benignas (falsos positivos estruturais).** Condomínio aberto com prazo de carência longo e janela de resgate anual não precisa de liquidez diária. Muitos administradores simplesmente não preenchem o bloco X.5, e zero ali significa 'não informado' — por isso o sinal exige que ao menos um dos dois campos esteja presente.

**Ação de investigação.** Ler a política de resgate no regulamento (carência e prazo de pagamento) antes de concluir por descasamento.

## 4. Limitações e falsos positivos conhecidos

**4.1 O score não mede irregularidade.** Ele mede distância do padrão do mercado em dimensões associadas, em episódios públicos, a problemas posteriores. A lista dos maiores scores é povoada por fundos cujo **mandato declarado** é comprar crédito vencido — distressed, precatórios, crédito judicial. Para esses, quase todo o pilar 1 dispara por desenho. Ler o score sem ler o segmento produz acusação sem base.

**4.2 Zero e ausente são indistinguíveis no informe.** O leiaute da CVM preenche zeros em campos não aplicáveis. A regra 1.1 protege contra o erro mais grave (tratar ausência como valor bom), mas não consegue recuperar a informação perdida: um zero legítimo e um zero de não-preenchimento entram no mesmo balde.

**4.3 Cobertura é baixa em campos decisivos.** O campo de créditos performados (I.2.A.4) está descontinuado desde 2023 — cobertura 0%, e o sinal QA-06 existe para documentar essa lacuna, não para disparar. O bloco X.8 (SCR) cobre metade do estoque de crédito. Cerca de 57% dos veículos com carteira acima de R$ 200 mi não declaram cedente válido, o que cega o pilar 3 para eles (é o que o sinal DI-03 registra).

**4.4 O ranking de cedentes é um piso.** O informe exige apenas os nove maiores cedentes. HHI e concentração máxima são subestimados em fundos pulverizados e corretos em fundos monocedentes — viés conservador, mas viés.

**4.5 Percentis do corte aplicados à série inteira.** Os limiares são fixados na distribuição de 2026-06-30 e aplicados aos 13 meses de avaliação. Isso é deliberado — persistência medida contra bar móvel não significa nada —, mas implica que uma piora generalizada do mercado ao longo do ano não é capturada como piora relativa.

**4.6 Sinais correlacionados somam duas vezes.** QA-01, QA-03, QA-05 e ES-03 leem o mesmo fenômeno econômico por ângulos diferentes; um fundo deteriorado dispara os quatro. O score não desconta essa correlação, o que o torna convexo em deterioração de crédito. A leitura por pilar em `rf2_sinais.csv` é o antídoto.

**4.7 GV-04 é casamento por string.** A busca nominal por grupos sob medida do BCB/CVM produz homônimos (a palavra 'MASTER' aparece em razões sociais sem qualquer relação com o Banco Master) e não capta vínculo societário não refletido no nome. É pista de busca, jamais imputação.

**4.8 A materialidade financeira não é perda esperada.** É o montante **exposto** ao fenômeno que o sinal aponta (estoque inadimplente, valor da sênior sem colchão, PL do veículo). Não incorpora taxa de recuperação, coobrigação nem garantia. Somar materialidades **entre sinais** dupla-conta o mesmo real — por isso a coluna principal é o `máximo`, não a soma. Somar **entre veículos** é pior ainda: parte dos sinais mede estoque (carteira, PL, inadimplência) e parte mede fluxo anual (aquisições, rolagem), e as duas grandezas não se somam. O total de materialidade do mercado inteiro não é um número com significado.

**4.9 Sem validação externa.** Nada aqui foi confrontado com processos sancionadores, atas de assembleia, regulamentos ou demonstrações financeiras auditadas. Cada ficha traz uma **ação de investigação** justamente porque o sinal é o começo da diligência, não o fim.

## 5. Arquivos gerados

| Arquivo | Conteúdo | Linhas |
|---|---|---:|
| `data/analytic/rf2_catalogo.csv` | Fichas dos sinais | 46 |
| `data/analytic/rf2_sinais.csv` | Veículo x sinal disparado no corte | 3.545 |
| `data/analytic/rf2_score_veiculo.csv` | Perfil multidimensional por veículo | 4.327 |
