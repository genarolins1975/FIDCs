# Parecer do Agente Espelho — Par 4/5 (Carteira, Inadimplência e Cedentes)

**Data:** 17/08/2026 · **Competência auditada:** 2026-06 (corte 30/06/2026)
**Código próprio do espelho:** `/home/user/FIDCs/auditoria/espelho_par45_recalc.py` (pandas, leitura direta dos CSVs brutos da CVM em `data/raw/extracted/`, `latin-1`, `sep=';'`, `quoting=3`; nenhum script do executor foi reutilizado).
**Dedupe do espelho:** regra 1 da metodologia (CNPJ presente como `Fundo` e `Classe` → prevalece `Classe`) reimplementada de forma independente; a regra 2 (fundo cujo(s) classe(s) informam com CNPJ próprio) exige o registro RCVM 175 e foi **testada por atribuição** (ver §2.1).

---

## 1. Reproduções

### 1.1 Inadimplência total (tab V.b + VI.b) — Tarefa 1

Fórmula do espelho: `Σ TAB_V_B_VL_DIRCRED_INAD + Σ TAB_VI_B_VL_DIRCRED_INAD`; denominador `Σ TAB_V_A_VL_DIRCRED_PRAZO + Σ TAB_VI_A_VL_DIRCRED_PRAZO`. 4.328 informes em cada tabela; a regra 1 de dedupe não removeu nenhuma linha (não há pares Fundo/Classe com CNPJ idêntico em 06/2026).

| Métrica (R$) | Espelho | Executor (`inadimplencia_aging_serie.csv`, 2026-06-30) | Diferença |
|---|---:|---:|---:|
| DC com risco (V.a) | 446.626.415.605,98 | 446.615.096.604,97 | **+11.319.001,01** |
| Inad. com risco (V.b) | 49.936.364.937,11 | 49.936.364.937,11 | 0,00 |
| DC sem risco (VI.a) | 261.758.612.389,67 | 261.758.612.389,67 | 0,00 |
| Inad. sem risco (VI.b) | 14.740.658.839,80 | 14.740.658.839,80 | 0,00 |

Percentuais recalculados pelo espelho: **inadimplência total = 64,68 bi / 708,39 bi = 9,13%** do DC total (com risco: 11,18%; sem risco: 5,63%). Controle interno: a soma das faixas B1..B10 reproduz exatamente os totais B em ambas as tabelas (V: 49,936 bi; VI: 14,741 bi) — sem resíduo.

**Faixas, incluindo >180 dias (B7+B8+B9+B10):**

| Faixa (R$) | Espelho | Executor | Δ |
|---|---:|---:|---:|
| V até 30d | 8.489.131.265,43 | 8.489.131.265,43 | 0 |
| V 31–90d | 6.607.828.071,33 | 6.607.828.071,33 | 0 |
| V 91–180d | 5.667.430.659,84 | 5.667.430.659,84 | 0 |
| **V >180d** | **29.171.974.940,51** | **29.171.974.940,51** | 0 |
| VI até 30d | 5.284.284.513,00 | 5.284.284.513,00 | 0 |
| VI 31–90d | 1.815.069.318,25 | 1.815.069.318,25 | 0 |
| VI 91–180d | 1.377.553.998,12 | 1.377.553.998,12 | 0 |
| **VI >180d** | **6.263.751.010,43** | **6.263.751.010,43** | 0 |

Nota estrutural que o espelho confirma: **58,4% da inadimplência com risco está vencida há mais de 180 dias** (29,17/49,94 bi) — o aging é dominado por crédito velho, não por fluxo novo.

### 1.2 Cinco maiores segmentos da carteira (tab II, subitens) — Tarefa 2

O espelho somou apenas os 27 subitens (A, B, C1–C3, D1–D4, E, F1–F8, G, H1–H2, I1–I4, J, K), excluindo os subtotais C, D, F, H, I. Controle anti-dupla-contagem: Σ subitens = 773.062.051.772,56 = `Σ TAB_II_VL_CARTEIRA` (resíduo zero; C−(C1+C2+C3) = −1,5e-05, ruído de ponto flutuante).

| # | Campo | Espelho (R$) | Executor (R$) | Δ |
|---|---|---:|---:|---:|
| 1 | TAB_II_F8_VL_OUTRO (Financeiro – Outros) | 250.805.965.775,79 | 250.805.965.775,79 | 0 |
| 2 | TAB_II_C1_VL_COMERC (Comercial) | 114.033.916.032,65 | 114.033.916.032,65 | 0 |
| 3 | TAB_II_G_VL_CREDITO (Cartão de Crédito) | 78.589.843.711,39 | 78.589.843.711,39 | 0 |
| 4 | TAB_II_A_VL_INDUST (Industrial) | 77.323.926.716,41 | 77.323.926.716,41 | 0 |
| 5 | TAB_II_D1_VL_SERV (Serviços) | 46.565.204.289,74 | 46.565.204.289,74 | 0 |

Coincidência **ao centavo** nos 5 maiores (e nos 10 maiores, verificados). A escolha do executor de publicar subitens sem subtotais está correta e foi validada contra o total oficial da tabela.

### 1.3 Subordinação agregada (tab X_2) — Tarefa 3

Classificação do espelho, na ordem declarada: contém "Mezanino" → mezanino; senão "Subordinada" → subordinada; senão "Senior/Sênior" → senior; valor = `TAB_X_QT_COTA × TAB_X_VL_COTA`. **Zero séries ficaram sem classificação** (nenhum resíduo "outros").

| Tipo | Espelho (R$ / nº veíc.) | Executor (R$ / nº veíc.) | Δ valor |
|---|---:|---:|---:|
| senior | 685.111.729.373,05 / 4.328 | 685.104.188.565,24 / 4.327 | +7.540.807,81 |
| subordinada | 241.005.405.248,75 / 3.341 | 241.002.467.750,34 / 3.340 | +2.937.498,41 |
| mezanino | 73.832.965.811,41 / 970 | 73.832.965.811,41 / 970 | 0 |

Índice de subordinação (sub+mez)/total: espelho 31,485% vs executor 31,486% — idêntico ao 3º decimal.

### 1.4 Cedentes — top 5 do ranking estimado (tab I) — Tarefa 4a

Fórmula do espelho: `PR_CEDENTE/100 × valor do bucket` (`TAB_I2A_VL_DIRCRED_RISCO` para A, `TAB_I2B_VL_DIRCRED_SEM_RISCO` para B), somente `0 < PR ≤ 100`, top-9 por veículo, CNPJs com 14 dígitos (zeros à esquerda restaurados; colunas de documento lidas como *string* — leitura como float corrompe os dígitos, armadilha verificada e evitada).

| CNPJ | Espelho (R$) | Executor (R$) | Δ valor | nº veíc. (esp./exec.) |
|---|---:|---:|---:|---|
| 33000167000101 (Petrobras) | 55.377.736.586,41 | 55.377.736.586,41 | 0 | 2 / 2 |
| 18189547000142 (CloudWalk) | 8.921.466.045,14 | 8.921.466.045,14 | 0 | 5 / 5 |
| 05449127000106 (BRF Energia) | 7.112.653.874,80 | 7.112.653.874,80 | 0 | 1 / 1 |
| 32402502000135 (QI SCD) | 6.094.403.605,69 | 6.094.403.605,69 | 0 | **72 / 73** |
| 01027058000191 (Cielo) | 5.867.406.207,75 | 5.867.406.207,75 | 0 | 2 / 2 |

Valores idênticos ao centavo nos 5 (e nos 10 primeiros, verificados). A única divergência é de **contagem de veículos** (QI: 72 vs 73; BMP, 10º: 91 vs 92): o executor inclui na contagem veículos com PR=0 ou bucket=0 (exposição nula), o espelho não — ver ressalva R2.

### 1.5 Petrobras — teste anti-inferência — Tarefa 4b

Varredura de **todas** as 18 colunas de cedente da tab I (A1..A9, B1..B9), inclusive ocorrências com PR inválido e outras filiais da raiz 33.000.167: o CNPJ 33000167000101 aparece **exatamente 2 vezes** em todo o informe de 06/2026, e nenhuma outra filial Petrobras aparece.

| Veículo | Bucket | PR | Valor do bucket (R$) | Exposição (R$) |
|---|---|---:|---:|---:|
| 09.195.235/0001-50 — FIDC DO SISTEMA PETROBRAS | sem risco (B1) | 95,08% | 58.239.773.982,06 | 55.374.377.102,14 |
| 61.270.134/0001-17 — SANTA CATARINA FIDC RL | com risco (A1) | 15,01% | 22.381.640,69 | 3.359.484,27 |

Soma = 55.377.736.586,41 = valor publicado. **A regra de não-inferência foi respeitada**: a exposição deriva exclusivamente dos campos de cedente do informe; não há imputação por nome, grupo econômico ou fonte externa. O executor ainda segregou corretamente 99,99% do valor na coluna `exp_sem_risco` (retenção de risco no cedente — veículo cativo do sistema Petrobras), o que é a leitura econômica certa: não é risco de crédito pulverizado adquirido em mercado.

### 1.6 Resolução de entidades no top-20 — Tarefa 4c

Testes do espelho sobre `cedentes_ranking_nomes.csv` (20 primeiras linhas):
- **Dígitos verificadores**: os 50 primeiros CNPJs do ranking passam na validação de DV módulo-11 (nenhum placeholder tipo 9999…/0000… no topo).
- **Cedente que é fundo**: nenhum dos 20 CNPJs pertence ao universo de veículos informantes de 06/2026 e nenhuma razão social contém "FUNDO DE INVESTIMENTO"/"FIDC". **Não há FIDC listado como cedente no top-20.**
- **Verificação ao vivo (Receita/minhareceita.org, 17/08/2026)**: 33000167000101 → PETROLEO BRASILEIRO S A PETROBRAS; 05449127000106 → BRF ENERGIA S.A.; 18189547000142 → CLOUDWALK IP — idênticos ao arquivo do executor.
- Nenhum nome do top-20 é inconsistente com o CNPJ. Único achado (fora do top-20): o doc malformado **00000000000191** na posição ~222 do ranking completo (R$ 92,4 mi) — ver ressalva R3.

### 1.7 Falso positivo em alertas (>30% de parcelas inadimplentes) — Tarefa 5

Recalculado nos brutos: `TAB_I2A21_VL_TOTAL_PARCELA_INAD / TAB_I2A_VL_DIRCRED_RISCO` (tab I).

| Veículo (CNPJ) | Parcelas inad. (R$) | DC risco (R$) | % espelho | % executor |
|---|---:|---:|---:|---:|
| BS NP (12428086000137) | 156.764.977,75 | 109.437.213,31 | 143,246% | 143,246% |
| MUNDO NP (27984265000128) | 101.323.236,47 | 96.544.919,32 | 104,949% | 104,949% |
| ALLCON PRIME NP (27984240000124) | 96.193.818,80 | 96.285.353,29 | 99,905% | 99,905% |

**3/3 confirmados até o 13º decimal — nenhum falso positivo.** Dois casos têm razão >100% (parcelas inadimplentes maiores que o próprio estoque de DC), o que reforça a leitura do executor de que o alerta captura tanto estresse real quanto erro de preenchimento — coerente com a limitação 5 da metodologia.

### 1.8 Cobertura do top-9 de cedentes — Tarefa 6

Para cada veículo, o espelho somou os PR válidos (0<PR≤100, cap em 100) e ponderou pelo valor do bucket:

| Bucket | DC total (tab I, R$) | Coberto pelo top-9 (R$) | **Cobertura ponderada** |
|---|---:|---:|---:|
| Com risco | 447,62 bi | 123,24 bi | **27,5%** |
| Sem risco | 262,13 bi | 83,47 bi | **31,8%** |
| **Total** | **709,75 bi** | **206,72 bi** | **29,1%** |

Agravante: **1.664 dos 2.781 veículos com DC com risco (60%) não informam nenhum cedente válido** (idem 567 de 1.056 no bucket sem risco). Conclusão inequívoca: **o ranking de cedentes só pode ser lido como piso** (estimativa inferior), nunca como distribuição completa — ~71% do DC do corte não tem cedente identificado. A metodologia do executor declara isso qualitativamente ("estimativa inferior", limitação 3), mas **não publica o número de cobertura** (ver ressalva R1).

---

## 2. Divergências e materialidade

### 2.1 Única divergência de valor: R$ 11,3 mi no DC com risco (0,0025%)

A diferença de **+11.319.001,01** no DC com risco (§1.1) e as de **+7.540.807,81 / +2.937.498,41** na subordinação (§1.3) têm **uma única e mesma causa**, identificada pelo espelho por busca de subconjunto sobre os 19 informes remanescentes em nível de fundo: o **RIZA KRATOS FIDC RL (66.814.472/0001-96)**, cujo DC na tab V é exatamente 11.319.001,01 e cujas séries na X_2 (Senior: 7.427 × 1.015,32352363 = 7.540.807,84; Subordinada: 3.183 × 922,87100534 = 2.937.498,80) reproduzem exatamente os deltas. A **CLASSE I FECHADA DO RIZA KRATOS (66.814.473/0001-30)** informa as mesmíssimas séries na mesma competência — ou seja, o executor aplicou corretamente a **regra 2 de dedupe** (fundo com classe informante de CNPJ próprio → excluído), evitando dupla contagem que o espelho (que só reimplementou a regra 1) capturaria. **A divergência é imaterial (≤0,003%) e depõe A FAVOR do executor.** As contagens n_veiculos da subordinação (−1 em senior e subordinada) têm a mesma origem.

### 2.2 Ressalvas (não invalidantes)

- **R1 — Cobertura do top-9 não publicada.** A limitação é declarada em texto, mas o número (29,1% do DC; 60% dos veículos sem cedente informado) é material para o leitor do ranking e deveria constar de `concentracao_indicadores.csv` ou do relatório. Sem ele, um leitor desatento pode tratar o ranking como censo.
- **R2 — `n_veiculos` inconsistente com a regra de exposição.** O executor exclui PR fora de (0,100] do valor, mas conta na coluna `n_veiculos` veículos com PR=0 ou bucket=0 (QI: 73 vs 72; BMP: 92 vs 91). Efeito zero sobre valores; apenas inconsistência de definição entre colunas do mesmo arquivo.
- **R3 — Doc malformado no ranking completo.** `00000000000191` (posição ~222, R$ 92,4 mi) é um documento inválido publicado em `cedentes_ranking_estimado.csv` sem flag. Está fora do top-150 nomeado, mas o arquivo completo deveria marcar docs sem DV válido.
- **R4 — Denominadores heterogêneos declarados, mas dispersos.** A inadimplência usa DC da tab V/VI (708,4 bi) e os cedentes usam DC da tab I (709,75 bi) — gap de ~0,2% entre tabelas do mesmo informe (autodeclaração). Está implícito na metodologia; uma nota única de conciliação evitaria confusão.
- **Observação (não é erro):** o topo do ranking de cedentes é dominado por um veículo cativo (95,08% de um único bucket de 58,2 bi autodeclarado pelo FIDC do Sistema Petrobras). O executor tratou corretamente (coluna sem risco separada), mas qualquer manchete "Petrobras é o maior cedente" depende de um único campo autodeclarado de um único informe.

---

## 3. Notas (0–10)

| Dimensão | Nota | Justificativa |
|---|---:|---|
| Precisão | **10** | Todos os agregados reproduzidos ao centavo; única divergência (R$ 11,3 mi, 0,0025%) explicada e correta do lado do executor (dedupe regra 2). |
| Rastreabilidade | **9** | Metodologia explícita campo a campo e reproduzível; a regra 2 do dedupe exige base de registro não trivial de reproduzir e os 3 casos citados não são listados nominalmente. |
| Consistência conceitual | **9** | Subitens sem subtotais validados contra `TAB_II_VL_CARTEIRA` (resíduo zero); V.b+VI.b coerente com faixas; leve dispersão de denominadores entre tabelas (R4). |
| Tratamento das limitações | **8** | Top-9, estimativa-piso, CPFs não resolvidos e erros de preenchimento declarados; falta quantificar a cobertura de 29,1% (R1). |
| Resolução de entidades | **9** | Top-50 com DV válido; 3/3 conferidos ao vivo na Receita; nenhum FIDC como cedente no top-20; um doc inválido residual no arquivo completo (R3). |
| Utilidade econômica | **9** | Segmentação, aging (58% >180d) e separação com/sem risco nos cedentes permitem leitura econômica correta; a utilidade do ranking de cedentes é limitada pela cobertura de 29% — limitação dos dados-fonte, mitigada mas não quantificada pelo executor. |

---

## 4. Veredito

**APROVADO COM RESSALVAS.**

Os cinco produtos auditados (`inadimplencia_aging_serie.csv`, `carteira_segmentos.csv`, `subordinacao_agregada.csv`, `cedentes_ranking_estimado.csv`, `cedentes_ranking_nomes.csv`) foram **integralmente reproduzidos ao centavo** por código independente; a única divergência de valor encontrada é imaterial (0,0025%) e decorre de o executor ter aplicado corretamente um controle de dupla contagem que o espelho confirmou por atribuição exata. A regra de não-inferência nos cedentes foi respeitada (Petrobras: 2 ocorrências, ambas em campos do informe), os alertas testados não contêm falsos positivos e a metodologia declarada foi de fato aplicada. As ressalvas R1–R4 são de comunicação e higiene de arquivo, não de cálculo: a mais importante é publicar a cobertura de 29,1% do top-9, sem a qual o ranking de cedentes pode ser mal lido como completo quando é, comprovadamente, apenas um piso.

*Reprodução: `python3 /home/user/FIDCs/auditoria/espelho_par45_recalc.py` (saída JSON com todos os números deste parecer).*
