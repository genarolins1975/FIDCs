# Panorama Auditável do Mercado Brasileiro de FIDCs
**Data de corte: 30/06/2026 · Data de extração: 17/08/2026 · Fontes primárias: CVM (Dados Abertos)**

> Todos os números deste relatório têm trilha de auditoria: fonte, arquivo, campo,
> fórmula e teste, registrados em `manifesto_fontes.csv`, `docs/metodologia.md`,
> `auditoria/livro_evidencias.csv` e `data/analytic/testes_auditoria.csv` (18 testes,
> 0 falhas). Rankings e séries são reproduzíveis pelos scripts em `scripts/`.
> Classificação de confiança: **[C]** Confirmado (documental direto) · **[FS]**
> Fortemente suportado · **[I]** Indiciário · **[NI]** Não identificável em fonte
> pública · **[CF]** Conflitante.

---

## 1. Sumário executivo

1. **Tamanho.** O mercado brasileiro de FIDCs atingiu **R$ 999,5 bilhões de
   patrimônio líquido em 30/06/2026**, distribuídos por **4.327 veículos
   informantes** (4.309 classes sob a RCVM 175 e 18 fundos remanescentes do
   regime anterior) **[C]** (CVM, Informe Mensal FIDC, tab. IV). Desse total,
   **R$ 161,6 bi (16,2%) são cotas de FIDC detidas por outros veículos do
   próprio universo** (FIC-FIDC e FIDCs que investem em FIDCs); o **PL líquido
   dessa circularidade é R$ 837,9 bi** — a medida mais fiel do financiamento
   efetivo à economia **[C]**.
2. **Crescimento.** O PL cresceu **11,8× em termos nominais desde dez/2013**
   (R$ 84,5 bi → R$ 999,5 bi) e **5,9× em termos reais** (IPCA), um CAGR real de
   **15,3% a.a.** — o segmento mais dinâmico da indústria de fundos. Nos 12 meses
   até o corte, +16,2% **[C]**.
3. **Democratização recente.** O número de cotistas saltou de **9,4 mil (2013)
   para 461,5 mil (jun/2026)** — quase 50× — com aceleração após a RCVM 175
   permitir acesso do investidor de varejo a FIDCs **[C]**.
4. **Carteira.** Os direitos creditórios somam **R$ 709,7 bi** (71% do PL):
   R$ 447,6 bi adquiridos **com** aquisição substancial de riscos e benefícios e
   R$ 262,1 bi **sem** (risco econômico retido no cedente) **[C]**. Predominam
   recebíveis do segmento financeiro (32% da carteira segmentada), comercial
   (17%, incl. varejo), cartão de crédito (10%) e industrial (10%) **[C]**.
5. **Quem intermedeia.** A administração fiduciária é concentrada: **os 5 maiores
   administradores respondem por 52,6% do PL** (BTG Pactual Serviços Financeiros,
   QI CTVM, Oliveira Trust, Banco Daycoval e BB Gestão/DTVM). A gestão é muito
   mais pulverizada: 493 gestores, top-5 = 24,1% **[C]**.
6. **Quem cede.** Os cedentes identificáveis (CNPJs declarados nos informes)
   revelam três motores: (i) grandes corporações estruturando fundos próprios
   (Petrobras — R$ 55,4 bi estimados via FIDC do Sistema Petrobras; BRF Energia;
   montadoras); (ii) fintechs e SCDs originando crédito digital (QI SCD em 73
   veículos, BMP SCD em 92, CloudWalk, Stone, Cielo); (iii) bancos médios e
   financeiras (Votorantim, Volkswagen, Santander Financiamentos) **[FS]**
   (estimativa-piso: informes cobrem apenas os 9 maiores cedentes por veículo).
7. **Quem retém o risco.** A estrutura agregada de capital é **68,5% cotas
   sênior, 7,4% mezanino e 24,1% subordinadas** **[C]**. O número de cotistas
   subordinados é dominado por categorias típicas de originadores e partes
   ligadas (PJ não financeiras, "outros", corretoras/distribuidoras) **[I]** —
   os valores por cotista não são públicos **[NI]**.
8. **Qualidade de crédito.** Parcelas vencidas e não pagas somam **9,1% dos
   direitos creditórios** no corte — 5,0 p.p. em atraso superior a 180 dias.
   Pela classificação SCR dos devedores (subconjunto reportado), 79,9% do valor
   está em ratings AA-A e 3,8% em H **[C]**. A inadimplência caiu de ~17-20%
   (2021-2023) para ~9% — em parte por composição (entrada de carteiras novas
   de consignado/cartão) e não necessariamente por melhora das safras antigas
   **[I]**.
9. **Exclusividade e originação própria.** R$ 153,0 bi (15,3% do PL) estão em
   veículos exclusivos e R$ 135,8 bi em veículos cujos cotistas são vinculados
   por interesse único e indissociável **[C]** — proxy do uso de FIDC como
   veículo cativo de balanço.
10. **Riscos mapeados.** 39 veículos com PL negativo, 19 informes com ativo
    >5× PL (erros de preenchimento), 10 veículos grandes com inadimplência
    >30%, 508 saltos de PL >30% m/m em 12 meses, e R$ 2,1 bi de alienações de
    DCs a cedentes/prestadores em 12m (sinal de partes relacionadas) — lista
    nominal em `data/analytic/alertas.csv` **[C]**.

---

## 2. Escopo, fontes e reprodutibilidade

- **Universo**: todos os FIDCs (padronizados e NP), FIC-FIDCs e suas classes
  que entregaram o Informe Mensal à CVM entre jan/2013 e jun/2026 — 163
  competências, 233,6 mil observações veículo-mês.
- **Fontes primárias**: Portal de Dados Abertos da CVM (informes mensais de
  FIDC; cadastro `cad_fi`; registro fundo/classe/subclasse da RCVM 175);
  resoluções CVM 175, 200 e 240; BCB/SGS (IPCA). **Validação**: ANBIMA
  (boletins). **Resolução de entidades**: base pública do CNPJ (Receita
  Federal, via minhareceita.org).
- **Trilha**: cada arquivo com URL, SHA-256, tamanho e timestamp em
  `manifesto_fontes.csv` (34 arquivos). Scripts numerados `01`-`05` reproduzem
  o pipeline de ponta a ponta.
- **Data de corte**: 30/06/2026 — última competência completa (jul/2026 já
  publicada, porém com ~120 informantes a menos; usada apenas como parcial).

## 3. Estrutura regulatória e transição

- A **Resolução CVM 175** (em vigor desde out/2023) reorganizou os fundos em
  **fundo → classes (patrimônio segregado) → subclasses**, e seu **Anexo
  Normativo II** rege os FIDCs: substituiu a ICVM 356/489, admitiu o investidor
  de varejo em classes que atendam a requisitos (registro dos recebíveis,
  vedação a coobrigação de cedente-varejo etc.), formalizou papéis (gestor
  passa a poder contratar consultoria especializada; custódia e registro
  redesenhados) e disciplinou a retenção de riscos.
- A **Resolução CVM 200 (12/03/2024)** fixou o prazo de adaptação dos FIDCs em
  **29/11/2024** (art. 134) — demais fundos, 30/06/2025 **[C]**. A migração do
  reporte por fundo para por classe ocorreu de forma escalonada entre dez/2024
  e mar/2026 e é a única quebra de série relevante; os controles de dupla
  contagem fundo×classe estão descritos na metodologia (sobreposição residual
  medida: R$ 0,13 bi, 3 casos, 06/2026).
- A **Resolução CVM 240 (06/03/2026)** alterou o Anexo II para facilitar a
  cessão por empresas em recuperação judicial (créditos performados deixam de
  ser automaticamente "não padronizados"; coobrigação de sociedade em RJ
  deixa de caracterizar NP) **[C]** — vetor provável de crescimento de FIDCs
  de special situations.

## 4. Tamanho e evolução (2013-2026)

| Dez | Veículos | PL (R$ bi) | PL real jun/26 (R$ bi) | Cotistas (mil) |
|---|---|---|---|---|
| 2013 | 431 | 84,5 | 169,5 | 9,4 |
| 2015 | 527 | 84,7 | 148,8 | 12,5 |
| 2017 | 751 | 115,3 | 185,8 | 16,1 |
| 2019 | 1.042 | 237,4 | 352,0 | 25,8 |
| 2021 | 1.547 | 308,9 | 398,4 | 31,6 |
| 2023 | 2.405 | 486,3 | 555,6 | 62,1 |
| 2024 | 3.140 | 731,8 | 796,8 | 148,6 |
| 2025 | 4.027 | 922,4 | 947,5 | 387,7 |
| **jun/2026** | **4.327** | **999,5** | **999,5** | **461,5** |

Fonte: CVM, informes mensais (tab. IV, X.1), painel canônico deduplicado; IPCA/BCB. **[C]**

- **Captação líquida** (tab. X_4, após filtro de sanidade): R$ 58 bi (2023),
  R$ 273 bi (2024), R$ 180 bi (2025), R$ 128 bi (1S2026). Medida **bruta de
  dupla contagem intramercado** (inclui subscrições de FIC-FIDC em FIDCs e
  integralizações em ativos); a ANBIMA, com perímetro e método próprios,
  reporta R$ 57,6 bi em 2025 e R$ 30,6 bi no 1S2026 **[CF — divergência de
  perímetro documentada; usar como ordem de grandeza]**.
- O crescimento é **estrutural, não apenas reprecificação**: número de veículos
  ×10, cotistas ×49, e a carteira de DCs acompanha o PL (~71%).

## 5. Mapa do ecossistema no corte

**Administradores (52 ativos; top-5 = 52,6% do PL) [C]**

| # | Administrador | PL (R$ bi) | Veículos | Share | Δ12m |
|---|---|---|---|---|---|
| 1 | BTG Pactual Serviços Financeiros DTVM | 161,0 | 437 | 16,1% | +42% |
| 2 | QI CTVM | 141,7 | 819 | 14,2% | +34% |
| 3 | Oliveira Trust DTVM | 99,9 | 159 | 10,0% | +22% |
| 4 | Banco Daycoval | 61,8 | 417 | 6,2% | +34% |
| 5 | BB Gestão de Recursos DTVM | 61,3 | 3 | 6,1% | −22% |

**Gestores (493 ativos; top-5 = 24,1%) [C]**: Oliveira Trust Servicer (R$ 76,3 bi),
BB Gestão de Recursos (R$ 61,3 bi — dominado pelo FIDC do Sistema Petrobras),
Banco Bradesco (R$ 40,6 bi), BTG Pactual Asset Management (R$ 32,9 bi), CBSF
Trust (R$ 29,8 bi). Cauda longa: gestores independentes de crédito (Solis,
Tercon, Genial, Empírica, Captalys etc.).

**Custodiantes** (registro CVM, classes FIDC): BTG Pactual (R$ 162,5 bi),
QI CTVM (R$ 138,7 bi), Oliveira Trust (R$ 119,5 bi), Daycoval (R$ 68,5 bi),
Banco do Brasil (R$ 61,2 bi). **Auditores**: PwC (R$ 210,4 bi), Next (R$ 174,5 bi),
EY (R$ 150,7 bi). **[C]**

A verticalização é a marca do mercado: os mesmos grupos (BTG, QI, Oliveira
Trust, Daycoval) aparecem como administrador, custodiante e controlador de
grande parte dos veículos — eficiente, mas fonte de risco operacional
correlacionado (seção 10).

## 6. Maiores veículos

| # | Veículo | PL (R$ bi) | Administrador | Exclusivo |
|---|---|---|---|---|
| 1 | FIDC do Sistema Petrobras | 61,2 | BB DTVM | Sim |
| 2 | Tapso FIDC | 41,5 | Oliveira Trust | Não |
| 3 | Pan Auto FIDC | 18,0 | BTG Pactual | Não |
| 4 | CloudWalk Bela FIDC | 10,0 | BEM DTVM (Bradesco) | Não |
| 5 | Alepo FIDC | 8,8 | CBSF | Sim |
| 6 | Itaú Crédito Privado FIDC | 8,7 | Intrag (Itaú) | Sim |
| 7 | Esperanza FIDC | 8,5 | CBSF | Não |
| 8 | Classe Consignado Privado MT Global | 8,3 | BTG Pactual | Não |

Concentração por veículo é baixa: HHI = 0,0074; top-10 = 18% do PL. **[C]**

## 7. Composição das carteiras (jun/2026)

Carteira segmentada (tab. II, subitens, % da carteira classificada): **[C]**

- Financeiro — outros: 32,4% (R$ 250,8 bi) — inclui crédito originado por
  fintechs/SCDs não classificado nas subcategorias
- Comercial + varejo + arrendamento: 17,0% (R$ 130,8 bi + 16,8 bi varejo)
- Cartão de crédito: 10,2% (R$ 78,6 bi)
- Industrial: 10,0% (R$ 77,3 bi)
- Serviços (incl. públicos, educacionais): ~7,0%
- Crédito corporativo: 4,2% · Consignado: 4,1% · Crédito pessoal: 3,9%
- Precatórios: 4,1% (R$ 31,4 bi) · Ações judiciais: 4,0% (R$ 30,8 bi)
- Agronegócio: 1,2% · Veículos: 0,5% · Middle market: 0,3%

**Prazo e liquidez** (tab. X.5): R$ 130,3 bi liquidáveis em ≤30 dias; R$ 179,5
bi acima de 360 dias. **Giro elevado**: aquisições de DCs somaram R$ 1,88
trilhão em 2025 (~2,6× o estoque) — o FIDC é infraestrutura de capital de giro
de ciclo curto (duplicatas, cartão, antecipações). **[C]**

**Retenção de risco na cessão**: 36,9% do estoque de DCs foi adquirido **sem**
transferência substancial de riscos e benefícios — ou seja, mais de um terço do
mercado mantém o risco econômico no cedente (coobrigação/recompra), com o FIDC
como veículo de funding e não de transferência de risco. **[C]**

## 8. Cedentes e originadores identificáveis

Metodologia: CNPJs dos 9 maiores cedentes por veículo × % declarado × valor do
bucket (tab. I) — **estimativa-piso**, cobre a cabeça da distribuição; nomes
resolvidos na base pública do CNPJ. Ranking completo: `cedentes_ranking_nomes.csv`.

| # | Cedente (grupo) | Exposição estimada (R$ bi) | Veículos | Setor |
|---|---|---|---|---|
| 1 | Petrobras | 55,4 | 2 | petróleo (fundo cativo do sistema) |
| 2 | CloudWalk (InfinitePay) | 8,9 | 5 | adquirência/fintech |
| 3 | BRF Energia | 7,1 | 1 | energia |
| 4 | QI SCD | 6,1 | 73 | banking-as-a-service |
| 5 | Cielo | 5,9 | 2 | adquirência |
| 6 | Marée SCD | 4,1 | 1 | SCD |
| 7 | Banco Votorantim | 4,0 | 4 | banco |
| 8 | Stone IP | 3,5 | 2 | adquirência |
| 9 | Banco Volkswagen | 3,5 | 2 | financeira de montadora |
| 10 | BMP SCD | 3,3 | 92 | banking-as-a-service |

Também no top-30: Renault, GM, Stellantis, Hyundai (financiamento de
concessionárias/fornecedores), Havan, Gazin (varejo), Vale, J&F, Santander
Financiamentos, BMG, Creditas, SumUp, Capital Consig. **[FS]**

**Padrões econômicos**: (i) *fundos cativos corporativos* — a empresa cede a um
FIDC exclusivo do próprio grupo (Petrobras: cedente e cotista via subsidiárias
— securitização interna, sem financiamento externo novo **[FS]**); (ii)
*originação digital* — SCDs cedem diariamente a dezenas de FIDCs de terceiros
(QI em 73, BMP em 92 veículos): o FIDC é o balanço do crédito fintech
brasileiro **[C]**; (iii) *recebíveis de adquirência* (CloudWalk, Stone,
Cielo); (iv) *montadoras e varejo* — antecipação de recebíveis comerciais.

**Recorrência** (`cedentes_recorrencia.csv`): centenas de cedentes aparecem
por ≥12 meses consecutivos — uso estrutural, não pontual, de FIDC como funding.

## 9. Passivo: quem investe e quem retém o primeiro risco

- Estrutura de capital agregada: **sênior 68,5% · mezanino 7,4% ·
  subordinada 24,1%** (R$ 241,0 bi) **[C]**. Subordinação mediana por veículo
  em `subordinacao_por_veiculo.csv`.
- Cotistas sênior (número): fundos de investimento (183,0 mil), pessoas
  físicas (82,0 mil — varejo pós-RCVM 175), "outros" (51,3 mil). Cotistas
  subordinados: "outros" (61,3 mil), corretoras/distribuidoras (27,2 mil),
  fundos (19,3 mil), PF (12,8 mil), PJ não financeiras (1,8 mil) **[C]** —
  contagens, não valores **[NI para valores por categoria]**.
- A leitura conjunta (24% de cotas subordinadas + 37% de DCs sem transferência
  de risco + 15% de PL exclusivo) indica que **a retenção de primeiro risco
  pelo ecossistema originador é a espinha dorsal do mercado** — coerente com o
  desenho regulatório, mas exige monitoramento de partes relacionadas **[FS]**.

## 10. Qualidade de crédito, desempenho e alertas

- **Inadimplência (parcelas vencidas/DC)**: 9,1% no corte; composição: 1,9%
  (1-30d), 1,2% (31-90d), 1,0% (91-180d), **5,0% (>180d)** — o atraso longo
  domina, típico de estoques NP e safras deterioradas **[C]**.
- Série (dez): 2019: 24%, 2021: 19%, 2023: 17%, 2024: 10%, 2025: 8,4%. A queda
  é fortemente influenciada pela **composição** (crescimento acelerado de
  carteiras novas); veículos com nome "não padronizado" rodam a 12,3% vs 8,7%
  dos demais **[I — flag por denominação]**.
- **SCR** (subconjunto reportado ao BCB): AA 53,1%, A 26,8%, B 12,0%, C-G
  4,2%, **H 3,8%** **[C]**.
- **Recompras e substituições** (tab. VII): R$ 29,6 bi recomprados e R$ 1,6 bi
  substituídos em 2025 — mecanismos que podem mascarar inadimplência ao
  devolver créditos problemáticos ao cedente antes do atraso aparecer;
  monitorar por veículo **[C dados; I interpretação]**.
- **Alertas nominais** (`alertas.csv`, `saltos_pl_12m.csv`): 39 PL negativos;
  19 ativos >5× PL (erros de informe — ex.: PRASS FIDC II reportou ativo de
  R$ 1,3 tri em jun/26 com PL de R$ 234 mi); 10 veículos com inadimplência
  >30% e DC >R$ 50 mi; 508 saltos >30% m/m; 22 veículos alienaram DCs a
  cedentes/prestadores (R$ 2,1 bi/12m). **Estes são sinais de atenção, não
  imputação de irregularidade.**

## 11. Concentração e competição

| Métrica | Valor |
|---|---|
| HHI por veículo | 0,0074 (baixo) |
| HHI por administrador | 0,079 (moderado) |
| HHI por gestor | 0,017 (baixo) |
| Top-5 administradores | 52,6% |
| Top-5 gestores | 24,1% |
| Top-10 veículos | 18,0% |

A infraestrutura fiduciária (administração/custódia/controladoria) é o ponto
de estrangulamento competitivo — e de risco sistêmico operacional: falha de um
administrador top-3 afetaria centenas de veículos simultaneamente. **[C]**

## 12. Respostas às perguntas obrigatórias

1. **Crescimento: crédito novo ou reestruturação?** Ambos, com predominância de
   originação nova (giro anual de aquisições ~2,6× estoque; cedentes fintech
   dominam por contagem). A parcela "reestruturação de balanço" é material:
   15,3% do PL em exclusivos e casos como Petrobras/Vale/J&F **[FS]**.
2. **PL em estruturas cativas**: R$ 153,0 bi exclusivos + R$ 135,8 bi de
   cotistas de interesse único (sobreposição parcial) — ordem de 15-20% **[C]**.
3. **Quem retém o subordinado**: por contagem, PJs ligadas à originação e
   "outros"; por valor, **[NI]** — o informe não abre valores por categoria.
4. **Cessão × financiamento efetivo**: R$ 262,1 bi (37% dos DCs) sem
   transferência substancial de risco — financiamento garantido, não venda
   definitiva **[C]**.
5. **Baixa contábil vs envolvimento continuado**: exige DFP/ITR das cedentes;
   **[NI nesta versão — lacuna declarada]** (agenda, seção 14).
6. **Exposição a instituições financeiras**: bancos/financeiras aparecem como
   cedentes (Votorantim, VW, Santander Fin., BMG…), administradores e
   custodiantes; cotistas bancários: 1,2 mil posições subordinadas (contagem)
   **[C parcial; valores NI]**.
7. **Circularidade**: R$ 161,6 bi (16,2% do PL) — mensurada e descontada na
   visão consolidada **[C]**.
8. **Gestores concentrados em poucos grupos**: os fundos monocedente-exclusivos
   (Petrobras/BB DTVM; Alepo/CBSF; Itaú Crédito Privado/Intrag) por construção;
   gestores de plataforma (QI, BMP como cedentes recorrentes) concentram
   originação, não gestão **[FS]**.
9. **Deterioração**: lista nominal dos 10 piores em inadimplência e 508 saltos
   em `alertas.csv`/`saltos_pl_12m.csv` **[C]**.
10. **Relevante mas não comprovável publicamente**: identidade dos sacados;
    valores por cotista; retenção subordinada por grupo econômico; balanços de
    companhias fechadas **[NI]**.
11. **Transparência que falta**: valores (não só contagem) de cotistas por
    categoria; abertura padronizada de recompras por parte relacionada;
    identificação de cedentes além do top-9; rating por classe no informe.
12. **Parcela do mercado associável a entidades identificadas**: cedentes
    top-9 cobrem a maior parte dos buckets com % declarado; ~R$ 200+ bi de
    exposição estimada atribuída a CNPJs nominados no corte (piso) **[FS]**.

## 13. Casos representativos (8 modelos)

1. **FIDC do Sistema Petrobras** — fundo cativo: cedentes e cotistas do mesmo
   grupo; R$ 61,2 bi; gestão de caixa/recebíveis intragrupo, não financiamento
   externo **[FS]**.
2. **Pan Auto FIDC** (R$ 18,0 bi) — banco médio securitizando financiamento de
   veículos; funding de varejo bancário via mercado de capitais **[C estrutura;
   FS economia]**.
3. **CloudWalk Bela FIDC** (R$ 10,0 bi) — fintech de adquirência: recebíveis de
   cartão de ciclo curtíssimo, cedente único, crescimento rápido **[C]**.
4. **FIDCs multissacado de plataforma (QI SCD / BMP SCD)** — dezenas de fundos
   de terceiros comprando crédito originado por SCDs white-label: o "atacado"
   do crédito fintech **[C]**.
5. **Tapso FIDC** (R$ 41,5 bi, Oliveira Trust) — veículo de crédito estruturado
   de grande porte, não exclusivo **[C dados; economia subjacente NI]**.
6. **Precatórios e ações judiciais** (R$ 62,2 bi somados) — special situations;
   inadimplência formal não mede risco (fluxo depende de tribunal/tesouro);
   beneficiados pela RCVM 240 **[C]**.
7. **Consignado privado** (MT Global e classes semelhantes; segmento de R$ 31,5
   bi) — folha de pagamento como colateral; crescimento pós-2024 **[C]**.
8. **FIC-FIDC / masters-feeders** (R$ 161,6 bi de cotas intramercado) —
   estruturas em camadas para segregar risco e distribuir; motivo pelo qual
   toda soma de PL deve ser lida consolidada **[C]**.

## 14. Limitações e agenda

**Limitações** (detalhadas em `docs/metodologia.md`): dados autodeclarados;
sacados não identificáveis; valores por cotista não públicos; gestor histórico
não rastreado (registro é fotografia); cedentes = piso (top-9); divergência de
perímetro com ANBIMA (+17,2%, decomposta: FIC-FIDC + cobertura associativa);
inferência NP por denominação é indiciária; **Par 6 do mandato (cotas de FIDC
em balanços de companhias) não executado nesta versão** — exige mineração de
notas explicativas DFP/ITR, declarado como lacuna, não estimado.

**Agenda de monitoramento**: (i) mensal — série PL/captação/inadimplência e
alertas; (ii) trimestral — ranking de prestadores e cedentes; (iii) anual —
casos e concentração; (iv) próxima iteração — DFP/ITR (Par 6), demonstrações
financeiras dos fundos (pareceres modificados), eventos societários.

## 15. Conclusão

O FIDC deixou de ser nicho e tornou-se **a infraestrutura central de
securitização e de funding do crédito não-bancário no Brasil**: R$ 1 trilhão
bruto, R$ 838 bi consolidados, crescimento real de 15% a.a. por 12 anos,
461 mil investidores e um papel insubstituível no financiamento de PMEs
(duplicatas, factoring, middle market), do crédito digital (SCDs/adquirência)
e de teses de special situations. Seus riscos estruturais não são de
concentração de crédito (HHI baixo), mas de **infraestrutura fiduciária
concentrada, retenção de risco em partes ligadas, circularidade em camadas e
qualidade heterogênea de informação** — exatamente os pontos onde a agenda de
transparência da CVM 175/240 e o monitoramento contínuo proposto agregam valor.

---
*Relatório produzido sob arquitetura executor/espelho com auditoria
independente; ver `auditoria/` para pareceres e nota final.*
