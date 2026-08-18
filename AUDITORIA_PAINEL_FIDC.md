# AUDITORIA FORENSE DO PAINEL "PANORAMA FIDC BRASIL"

**Objeto:** painel publicado (`relatorio/painel_executivo.html`, v4/v5) e a cadeia
analítica que o alimenta (`scripts/01`–`10`, `data/analytic/*`).
**Data da auditoria:** 18/08/2026 · **Auditor:** força-tarefa (Fase 0)
**Regra aplicada:** nenhuma alteração de código antes da conclusão desta auditoria.

Método: (i) inventário de todas as seções e métricas exibidas; (ii) rastreio de
cada número até a fórmula e o campo de origem; (iii) confronto do que o painel
declara com o que as fontes efetivamente oferecem; (iv) execução de consultas de
verificação sobre a própria base para medir a materialidade de cada problema.
Todo achado abaixo foi **verificado com consulta executada**, não inferido.

---

## 1. Inventário do painel auditado

| # | Seção | Elementos | Fonte declarada |
|---|---|---|---|
| 1 | Cartões de topo | 7 KPIs (PL, PL líq. circularidade, veículos, cotistas, inadimplência, subordinação, provisionamento) | informe mensal, tabs I/IV/V/VI/X_1/X_2 |
| 2 | Evolução do PL | série mensal 2013-2026, nominal e real, tooltip com crosshair | tab IV + IPCA/SGS 433 |
| 3 | Carteira por segmento | 10 maiores segmentos | tab II |
| 4 | Administradores e gestores | 2 rankings top-8 | tab I (CNPJ_ADMIN) e registro CVM |
| 5 | Estrutura de capital | barra 100% sênior/mezanino/subordinada | tab X_2 |
| 6 | Qualidade de crédito | aging 4 faixas + SCR AA-H | tabs V/VI e X.8 |
| 7 | Cedentes identificados | tabela top-10 com CNPJ resolvido | tab I (campos de cedente) + base CNPJ |
| 8 | Balanços corporativos | 8 entidades com chips de confiança | DFs + análise externa |
| 9 | Supervisão e integridade | 3 KPIs, gestores detentores (CDA), sparkline CBSF, triagem RF1-RF5, casos, gestores sinalizados, detentores dos sinalizados | CDA, tabs diversas, imprensa/BCB |
| 10 | Auditoria | 19 chips de teste | testes_auditoria.csv |

---

## 2. Tabela-mestre de achados

| Sev. | Tela | Elemento | Problema | Evidência (verificada) | Impacto analítico | Correção recomendada | Validação humana |
|---|---|---|---|---|---|---|---|
| **Crítico** | Todas | Cobertura de fontes | **4 das 18 tabelas do Informe Mensal nunca foram processadas**: VIII (25 maiores devedores), IX (taxas de desconto/juros de compra e venda), X_6 (desempenho esperado × real por série), X_7 (garantias sobre os direitos creditórios) | `ls data/raw/extracted/*tab_VIII*` retorna 202501→202607; tab VIII no corte tem 2.999 veículos e R$ 321,6 bi; IX, X_6 e X_7 têm 4.328 veículos cada (100% do universo) | O painel declara "concentração por sacado: não identificável em fonte pública" (relatório §12.10 e limitação 1) — **afirmação incorreta**: a concentração existe na tab VIII desde jan/2025, sem identidade mas com valores. Perdem-se ainda os melhores sinais forenses disponíveis (preço de aquisição fora de mercado; promessa × entrega por série; colateral) | Processar as 4 tabelas; reescrever a limitação para "valores de concentração disponíveis, identidade do sacado indisponível" | Não |
| **Crítico** | Cartões | "Cotistas 462 mil" | Rótulo afirma número de investidores; o valor é a **soma de posições por veículo** (tab X_1). Um investidor presente em 10 fundos é contado 10 vezes | `SELECT SUM(TAB_X_NR_COTST) … = 461.523` sobre 11.580 linhas / 4.328 veículos | Superestima a base de investidores por fator desconhecido; alimenta a narrativa de "democratização" com número não comparável a "pessoas" | Renomear para "posições de cotistas" e declarar que não mede pessoas únicas | Não |
| **Crítico** | Supervisão (RF3) | Triagem "subordinação < 5%" | `coalesce(v_sub/v_tot, 0) < 0.05` converte **ausência de dado em zero**, disparando alerta para veículos que simplesmente não reportaram séries | 16 dos 64 alertas RF3 têm `subord` nulo — **25% dos alertas**, R$ 11,36 bi de PL | Falso positivo por construção; contamina o ranking "quem tem mais red flags" e a contagem exibida (64) | Ausência ⇒ sinal "não avaliável"; entra no cálculo de cobertura, nunca como disparo | Não |
| **Crítico** | Todas | 13 números hardcoded no gerador | Percentuais escritos no HTML (52,6%; 24,1%; 97,9%; 51%; 29,4%; 47%; 31%; 21%; 17,2%; "100% do PL") não são derivados dos CSVs | `grep` em `scripts/07_painel_html.py` linhas 357-359, 361-362, 380-381, 388, 509, 529 | Na próxima atualização da base, o painel exibirá **números falsos apresentados como reais**, sem qualquer aviso — viola o critério de aceitação nº 1 | Todo número exibido deve vir de artefato calculado; teste automático que falhe se sobrar literal numérico em texto | Não |
| **Crítico** | Administradores/Gestores | Rankings lado a lado | PL sob administração e PL sob gestão exibidos como métricas equivalentes, sem definição de que administrador **não assume risco econômico** | Seção 4 do painel; nota fala em circularidade, não em natureza da métrica | Leitor conclui "maior administrador = maior exposto"; erro conceitual que o prompt classifica como inaceitável | Separar em lentes nomeadas, cada uma com definição, numerador/denominador, cobertura e o que **não** significa | Não |
| **Crítico** | Supervisão | Cartão "Ecossistema ex-Reag no corte" | Grupo sob investigação nomeado em cartão de destaque; o status processual só aparece em nota fora do elemento | Seção 9 do painel | Risco jurídico e de leitura acusatória; um print do cartão isolado imputa irregularidade | Renomear para descrição factual do vínculo ("veículos com prestador em liquidação extrajudicial — BCB, 15/01/2026"), com status processual no próprio elemento e no tooltip | **Sim** — revisão jurídica |
| **Alto** | Supervisão | RF6 (exposição a liquidações) | Casamento por **substring de nome** (`LIKE '%MASTER%'`), não por CNPJ | Confirmado 1 veículo capturado por "master" em nome de estrutura ("REAG MASTER FEEDER") | Método frágil: gera falso positivo em qualquer fundo cujo nome contenha o termo; não escala | Casar por CNPJ do prestador (ex.: 34.829.992/0001-86) e por vínculo societário documentado | Não |
| **Alto** | Todas | Score de red flags | Ranking por **contagem bruta** de sinais; sem severidade, materialidade, cobertura, persistência ou atualidade | `red_flags_regulatorios.csv` não tem essas colunas | Veículo com 2 sinais leves aparece pior que um com 1 sinal crítico; ausência de dado reduz artificialmente o score | Score decomposto em 6 dimensões, com "não classificável" para cobertura insuficiente | Não |
| **Alto** | Supervisão | Sinais sem backtest | Nenhum sinal foi testado contra casos históricos; limiares escolhidos por julgamento (15%, 50%, 150%, 80%) | `METODOLOGIA_RED_FLAGS.md` inexistente até esta data | Não se sabe a precisão nem a antecedência dos alertas; risco de falsa confiança | Backtest com casos confirmados e controles negativos, sem vazamento de informação futura; rotular metodologia como experimental | Não |
| **Alto** | Todas | Auditabilidade | Números têm tooltip com fonte, mas **não são clicáveis**; não há fórmula, chave de registro, hash, versão do arquivo nem download dos registros | Inspeção do HTML: `data-tip` textual apenas | Não atende ao critério "todo número relevante auditável" | Gaveta de evidências por indicador, com manifesto e exportação | Não |
| **Alto** | Todas | Filtros e busca | Não há filtros globais nem busca por fundo, CNPJ, gestor, empresa ou grupo | Inspeção do HTML | Painel é leitura passiva; impossível investigar uma entidade específica | Filtros persistentes + busca + drill-down | Não |
| **Alto** | Anatomia | Subclasses | 9.430 subclasses registradas, das quais **2.170 pertencem a classes de FIDC** — nunca declaradas nem analisadas no painel | `registro_subclasse` × `registro_classe` filtrado por Tipo_Fundo FIDC | Unidade de análise incompleta; risco de leitor supor que "classe" é o nível final | Declarar a existência, explicar que subclasses não reportam informe próprio (por isso não são somadas) e exibir a contagem | Não |
| **Alto** | Qualidade de crédito | Rentabilidade | `rentab_cotas` (tab X_3) está na base com 12.206 linhas no corte, mas **nunca é exibida** | `SELECT COUNT(*) FROM rentab_cotas` | Falta a dimensão desempenho (e, com a tab X_6, a comparação prometido × entregue) | Incluir rentabilidade por tipo de cota e o gap esperado × real | Não |
| **Alto** | Supervisão | Detentores | Só cobre a indústria de fundos (CDA); bancos, empresas e pessoas físicas ficam fora, e a cobertura não é quantificada no elemento | `09_cda_detentores.py` | Leitor pode ler R$ 164 bi como "todos os detentores" | Exibir cobertura da lente e o que está fora dela | Não |
| **Médio** | Evolução | Data-base | Escolha de 30/06 sobre 31/07 explicada em nota longa; competência de julho ainda em janela de entrega (prazo regulamentar) não é evidenciada | Nota da seção 2 | Usuário não especialista não entende por que o painel "atrasa" um mês | Bloco "por que este corte" com a contagem de informantes faltantes | Não |
| **Médio** | Todas | "O que mudou" | Não há comparação com a atualização anterior | — | Impossível ver deterioração/melhora entre ciclos | Seção de deltas com alertas novos, agravados e encerrados | Não |
| **Médio** | Todas | Exportação | Nenhuma tabela exporta dados | — | Não reproduzível pela interface | Exportar CSV + manifesto por tabela | Não |
| **Médio** | Todas | Didática por métrica | Tooltips explicam o número, mas não há "o que é / por que importa / como interpretar / limitação" por métrica, nem glossário | — | Barreira para não especialista | Ficha didática por métrica e glossário contextual | Não |
| **Baixo** | Supervisão | Cores | Vermelho/âmbar usados em chips de teste e badges; risco de leitura de "risco" onde é "ressalva metodológica" | — | Ruído interpretativo | Reservar vermelho a sinais críticos sustentados | Não |

**Resumo:** 6 achados críticos, 8 altos, 4 médios, 1 baixo.

---

## 3. O que sobrevive à auditoria (preservar)

Nem tudo deve ser reconstruído. Verificado e mantido:

- **Painel canônico deduplicado** (fundo × classe, regras i-ii) — testado (T3: zero duplicatas) e reproduzido ao centavo por dois espelhos independentes.
- **Reconciliação com Medidas CVM/FIE** — diferença zero em 4.314 CNPJs (99,0% do PL). É a melhor validação interna disponível e deve ser mantida como teste recorrente.
- **Saneamento de outlier documentado** (INX SSPI, mai/2016) com log versionado.
- **Manifesto de fontes com SHA-256** (37 arquivos) e livro de evidências (31 claims).
- **Medida de circularidade** via campos I2H/I2I (universo completo), superior à alternativa via CDA.
- **Resolução de entidades de cedentes** por CNPJ com razão social/CNAE da base pública.
- **Separação de papéis** (gestor ≠ administrador ≠ custodiante ≠ cedente ≠ cotista) — conceitualmente correta na base, ainda que mal comunicada na interface.
- **Advertências jurídicas** já presentes (sinal ≠ irregularidade; patrimônio segregado) — devem ser reforçadas e movidas para dentro dos elementos.

---

## 4. Conclusão da Fase 0

O painel atual é **correto naquilo que mede** (os agregados resistiram a auditoria
independente) e **insuficiente naquilo que se propõe a ser**: uma ferramenta de
supervisão. Os três problemas estruturais são (i) subutilização da fonte primária
— um quinto das tabelas do informe está fora, incluindo a que responde à pergunta
declarada como impossível; (ii) tratamento de ausência de informação como valor,
que fabrica alertas; e (iii) ausência de camada de auditabilidade e de navegação,
que impede o uso investigativo.

A reconstrução está autorizada nos termos da seção seguinte do trabalho.
