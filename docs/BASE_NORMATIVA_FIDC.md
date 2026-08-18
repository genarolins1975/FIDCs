# Base normativa vigente do mercado de FIDCs

**Data de referência:** 18/08/2026
**Autoria:** frente jurídico-regulatória (CVM / PLD-FTP) da força-tarefa do painel de FIDCs
**Regra editorial:** só entra neste documento o que tem fonte pública citada por URL. Onde a
pesquisa não localizou fonte primária, o texto diz expressamente
*"não localizado em fonte pública consultada"*.

Cada seção termina com um bloco **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**, que é a
ponte entre a norma e as decisões de modelagem do painel.

---

## 0. Mapa rápido das normas

| Norma | Data | Vigência / marco | Objeto | Relevância para o painel |
|---|---|---|---|---|
| Resolução CVM 175 | 23/12/2022 | dispositivos gerais em vigor desde 02/10/2023; adaptação do estoque escalonada pela RCVM 200 | Marco geral de fundos de investimento | Alta — define fundo/classe/subclasse |
| Anexo Normativo II da RCVM 175 | 23/12/2022 | idem | Regime específico dos FIDC | Máxima |
| Resolução CVM 181 | 28/03/2023 | — | Ajustes no Anexo II (custódia, partes relacionadas, agente de cobrança) | Média |
| Resolução CVM 187 | 27/09/2023 | — | Ajustes no Anexo II (cotas seniores, verificação de lastro por terceiros) | Média |
| Resolução CVM 200 | 06/03/2024 (publicada 12/03/2024) | prazos definitivos | Prorroga prazos de adaptação à RCVM 175 | Alta — define a data em que a série vira "classe" |
| Resolução CVM 240 | 05/03/2026 | efeitos a partir de 06/03/2026 | Créditos de empresas em recuperação judicial/extrajudicial | Alta — muda a classificação DC padronizado/não-padronizado |
| Resolução CVM 50 | 31/08/2021 | publicada 02/09/2021 | PLD/FTP no mercado de valores mobiliários | Alta |
| Resolução CVM 245 | 01/07/2026 | em vigor desde 15/07/2026 | Altera a RCVM 50 (diligência reforçada GAFI) | Alta — norma mais nova do conjunto |
| Resolução CVM 160 | 13/07/2022 | publicada 14/07/2022 | Ofertas públicas de distribuição | Média-alta |
| Ofício-Circular CVM/SSE 8/2025 | 17/11/2025 | interpretativo | Anexos II, III e VI da RCVM 175 | Alta |
| Ofício-Circular Conjunto CVM/SIN/SSE 1/2025 | 01/12/2025 | interpretativo | Parte geral e Anexos I–V | Média |
| Ofício-Circular CVM/SSE 9/2025 | 15/12/2025 | vigente desde 02/01/2026 | Informe Mensal de FIDC v6.6 | Máxima (é a fonte do dado) |
| Plano Bienal de SBR 2025-2026 | aprovado pelo CGR em 04/09/2024 | biênio 2025-2026 | Supervisão baseada em risco | Alta |

---

## 1. Resolução CVM 175 — parte geral

**Fonte:** <https://conteudo.cvm.gov.br/legislacao/resolucoes/resol175.html>
**Texto consolidado (PDF):** <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol175consolid.pdf>

- Resolução de **23/12/2022**, publicada no DOU em 28/12/2022, com republicação/retificação em
  31/03/2023.
- Substitui o regime anterior de fundos (para FIDC, revoga a Instrução CVM 356/2001 — fato
  registrado no relatório do PAS 19957.006858/2019-25, nota de rodapé 5).
- Estrutura em **parte geral + 12 Anexos Normativos**. O Anexo Normativo II é o dos FIDC; o
  Anexo Normativo XII trata de FIDC de projetos de interesse social.
- Alterações posteriores listadas na própria página da CVM: **Resoluções 181/23, 184/23, 187/23,
  200/24, 206/24, 209/24, 214/24 e 240/26**.

### 1.1 A mudança estrutural: fundo → classe → subclasse

A RCVM 175 substitui o fundo monolítico por uma arquitetura de três níveis:

- **Fundo** — o veículo, titular do CNPJ-mãe e do regulamento;
- **Classe de cotas** — o **patrimônio segregado**, com política de investimento própria,
  patrimônio líquido próprio e prestadores próprios. É a unidade que efetivamente investe;
- **Subclasse** — recorte da classe, diferenciável por público-alvo, taxas, prazos e, no FIDC,
  também **"por outros direitos econômicos e políticos"** (art. 3º do Anexo II).

No FIDC as cotas **seniores** e **subordinadas** são subclasses. O art. 8º do Anexo II, na
redação dada pela RCVM 187/2023, determina que **as cotas seniores devem ser emitidas em uma
única subclasse**, veda subordinação entre diferentes subclasses de cotas subordinadas e admite
séries de seniores e de mezanino em classe fechada, diferenciadas apenas por prazo e índice.

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **A unidade reportante deixa de ser o fundo e passa a ser a classe.** Séries históricas
>    construídas por CNPJ de fundo e séries construídas por classe **não são comparáveis** sem
>    tratamento. Toda comparação que atravesse a virada de regime precisa de um teste de quebra
>    de série e de nota metodológica explícita.
> 2. Um mesmo CNPJ de fundo pode abrigar **múltiplas classes** com PL, carteira, inadimplência e
>    subordinação independentes. Somar classes de um mesmo fundo produz um agregado que não
>    corresponde a nenhum patrimônio real; a segregação patrimonial é jurídica, não contábil.
> 3. Índice de subordinação e razão sênior/subordinada **só fazem sentido no nível da classe**.
> 4. Rankings de administrador/gestor devem declarar se contam veículos (fundos) ou classes — os
>    dois números divergem e a divergência cresce ao longo de 2024-2026.

---

## 2. Anexo Normativo II da RCVM 175 — o regime dos FIDC

**Fonte (texto consolidado, PDF oficial):**
<https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol175consolid_Anexo02.pdf>

Os dispositivos abaixo foram extraídos diretamente do PDF consolidado da CVM.

### 2.1 O que é direito creditório (art. 2º, XII)

São direitos creditórios:
- (a) direitos e títulos representativos de crédito;
- (b) valores mobiliários representativos de crédito;
- (c) certificados de recebíveis e outros valores mobiliários de securitização, **desde que não
  lastreados em direitos creditórios não-padronizados**;
- (d) por equiparação, **cotas de FIDC**.

### 2.2 Direitos creditórios não-padronizados (art. 2º, XIII)

É não-padronizado o direito creditório com ao menos uma destas características:
- (a) vencido e pendente de pagamento na cessão;
- (b) decorrente de receitas públicas da União, Estados, DF, Municípios, autarquias e fundações;
- (c) resultante de ação judicial ou arbitral em curso, objeto de litígio, penhorado ou dado em
  garantia;
- (d) cuja constituição ou validade jurídica da cessão seja fator preponderante de risco;
- (e) **o devedor seja sociedade empresária em recuperação judicial ou extrajudicial** — redação
  dada pela **Resolução CVM 240, de 05/03/2026** (a redação anterior dizia "o devedor **ou
  coobrigado**");
- (f) e seguintes, conforme o texto consolidado.

**Exceções (art. 2º, § 1º)** — *não* são considerados não-padronizados:
- **I** — direitos creditórios cedidos por sociedade empresária em recuperação judicial ou
  extrajudicial, desde que não originados por contratos mercantis de compra e venda para entrega
  futura. A exigência de **plano de recuperação homologado em juízo** (antiga alínea "b") foi
  **revogada pela Resolução CVM 240/2026**;
- **II** — precatórios federais sem impugnação e já expedidos e remetidos ao TRF competente.

### 2.3 Público-alvo, varejo e restrições de distribuição

**Art. 13 — distribuição junto ao público em geral (varejo)** exige, cumulativamente:
- **I** — o público em geral **não pode adquirir cotas subordinadas**;
- **II** — o regulamento deve estipular cronograma de amortização ou distribuição de rendimentos;
- **III** — em classe aberta, carência + prazo entre pedido de resgate e pagamento não pode
  superar **180 dias**;
- **IV** — a política de investimento **não pode admitir**:
  - (a) direitos creditórios originados por contratos mercantis de compra e venda de produtos,
    mercadorias e serviços **para entrega ou prestação futura** (o chamado "risco de performance"),
    salvo cedentes que sejam concessionárias de serviço público ou companhias de projeto de
    infraestrutura/PD&I prioritário;
  - (b) direitos creditórios **originados ou cedidos pelo administrador, gestor, consultoria
    especializada, custodiante, entidade registradora e suas partes relacionadas**;
- **V** — a subclasse de cotas seniores deve ter **classificação de risco por agência registrada
  na CVM**.

**Art. 15** — classes que admitam **direitos creditórios não-padronizados** são de subscrição
**exclusiva de investidores profissionais**, ressalvada a subscrição de cotas subordinadas pelo
cedente e suas partes relacionadas.

**Art. 46** — em classe destinada ao público em geral, a aplicação em precatórios federais está
limitada a **20% do PL por precatório**.

### 2.4 Subordinação, resgate e integralização

- **Art. 14** — só em **classes restritas** a integralização de cotas seniores e mezanino pode ser
  feita em direitos creditórios.
- **Art. 16** — resgate e amortização de subordinadas e mezanino são admitidos **desde que o
  índice de subordinação não seja comprometido**.
- **Art. 20, § 1º** — o índice de subordinação de cada subclasse mezanino e da subclasse
  subordinada **deve ser expresso no regulamento como taxa percentual do PL da classe**.

### 2.5 Verificação de lastro — o coração do risco de fraude

Há **duas** verificações distintas, com responsáveis distintos:

**(i) Verificação na aquisição — responsabilidade do GESTOR (art. 36)**
> "No âmbito das diligências relacionadas à aquisição de direitos creditórios, o gestor deve
> verificar a **existência, integridade e titularidade** do lastro dos direitos e títulos
> representativos de crédito referidos na alínea 'a' do inciso XII do art. 2º."

- § 1º — pode ser **individualizada ou por amostragem**, com "modelo estatístico consistente e
  passível de verificação", nos parâmetros do regulamento (art. 20, VII);
- § 2º — as regras da amostragem devem ficar **públicas** na mesma página das informações
  periódicas da classe;
- § 3º — se o **reduzido valor médio** dos créditos não justificar nem a amostragem, o regulamento
  **pode dispensar** a verificação, especificando os parâmetros de diversificação, quantidade e
  valor médio que ensejam a dispensa;
- § 4º (redação da RCVM 187/2023) — o gestor pode **contratar terceiros** (inclusive entidade
  registradora, custodiante ou consultoria especializada) para a verificação;
- § 5º — se contratar, **deve fiscalizar** a atuação do contratado.

**(ii) Verificação periódica — responsabilidade do CUSTODIANTE (art. 38)**
> Considerando a totalidade do lastro, **trimestralmente** ou em periodicidade compatível com o
> prazo médio ponderado da carteira (o que for maior), o custodiante deve verificar existência,
> integridade e titularidade do lastro dos créditos **que ingressaram no período a título de
> substituição** e dos **créditos vencidos e não pagos** no mesmo período.

- § 1º — o regulamento pode atribuir essa verificação ao **administrador**, desde que este não
  seja parte relacionada ao gestor nem à consultoria especializada;
- § 2º — pode-se usar informação da entidade registradora, verificada a consistência.

**Interpretação da SSE (Ofício-Circular CVM/SSE 8/2025, itens 9-12):** o art. 36 alcança apenas
os direitos creditórios da alínea "a" do art. 2º, XII. Os **valores mobiliários representativos
de crédito** (alínea "b" — p. ex. debêntures e notas comerciais objeto de oferta pública
registrada) **estão fora do escopo do art. 36**. O grau de verificação deve ser calibrado pelo
gestor conforme a modalidade do crédito (recebíveis, créditos vencidos, precatórios).

### 2.6 Registro, custódia e guarda de documentos

**Art. 30** — o administrador deve contratar, em nome do fundo:
- **I** — **registro dos direitos creditórios em entidade registradora autorizada pelo BCB**, que
  **não pode ser parte relacionada ao gestor ou à consultoria especializada**;
- **II** — **custódia** (o custodiante também não pode ser parte relacionada ao gestor ou à
  consultoria) — redação dada pela RCVM 181/2023;
- **III** — custódia de valores mobiliários, se for o caso;
- **IV** — **guarda da documentação que constitui o lastro** (física ou eletrônica);
- **V** — liquidação física/eletrônica e financeira dos direitos creditórios.
- § 5º (incluído pela RCVM 181/2023) — se a política admitir a aquisição de créditos originados
  ou cedidos pelo administrador, gestor, consultoria ou partes relacionadas, o custodiante **não
  pode ser parte relacionada ao gestor ou à consultoria**; § 6º dispensa a exigência em classe
  exclusivamente de investidores profissionais.

**Art. 37** — se a classe aplicar em direitos creditórios **não passíveis de registro**, o
administrador **deve** contratar custódia da carteira. Dispensa-se o registro se o crédito estiver
registrado em mercado organizado de balcão autorizado pela CVM ou depositado em depositário
central autorizado pela CVM ou pelo BCB (parágrafo único incluído pela RCVM 181/2023).

**Art. 40** — subcontratados do custodiante **não podem ser** originador, cedente, gestor,
consultoria especializada ou partes relacionadas.

### 2.7 Vedações e conflito de interesses (arts. 41 a 43)

- **Art. 41** — **é vedado a qualquer prestador de serviços receber ou orientar o recebimento de
  depósito em conta corrente que não seja de titularidade da classe ou conta-vinculada.**
- **Art. 42** — é vedada a aquisição de direitos creditórios **originados ou cedidos pelo
  administrador, gestor, consultoria especializada ou partes relacionadas**. O regulamento pode
  afastar a vedação se (I) gestor, entidade registradora e custodiante não forem partes
  relacionadas entre si e (II) registradora e custodiante não forem partes relacionadas ao
  originador ou cedente. O inciso I não se aplica a classe exclusivamente de investidores
  profissionais.
- **Art. 43** — vedado aceitar que garantias em favor da classe sejam formalizadas em nome de
  terceiros que não representem o fundo.

**Exceção do art. 52, III + interpretação da SSE (OC SSE 8/2025, itens 13-15):** em classe
destinada exclusivamente a **investidores profissionais**, o regulamento pode prever que os
recursos da liquidação dos direitos creditórios sejam recebidos **pelo cedente em conta corrente
de livre movimentação**, para posterior repasse. A SSE esclareceu que essa prerrogativa
**subsiste mesmo quando o cedente acumula a função de agente de cobrança**, mas **não se estende
a outros prestadores** — permanece vedado, por exemplo, o recebimento pela consultoria
especializada, salvo se ela figurar como cedente.

### 2.8 Coobrigação e limites de concentração

- **Art. 45** — a aplicação em direitos creditórios e outros ativos **de responsabilidade ou
  coobrigação de um mesmo devedor** está limitada a **20% do PL da classe**.
  - § 1º — devedores do **mesmo grupo econômico** contam como um único devedor;
  - § 3º — em classes para **investidores qualificados** o limite pode ser elevado quando o
    devedor/coobrigado for companhia aberta, instituição financeira ou entidade com DFs
    auditadas por auditor registrado na CVM (alínea "c" com redação da RCVM 181/2023);
  - § 5º — os percentuais são apurados **mensalmente**, com base no PL do fim do mês anterior;
  - § 6º — a elevação do limite **não se aplica** a créditos de responsabilidade ou coobrigação de
    **prestadores de serviços e suas partes relacionadas**;
  - § 7º — dispensa do artigo se os cotistas forem exclusivamente (I) sociedades do mesmo grupo
    econômico e seus administradores/controladores pessoas naturais ou (II) **investidores
    profissionais**;
  - § 8º — créditos de receitas públicas e de empresas controladas pelo poder público **não** se
    submetem ao limite por emissor.
- **Art. 47** — aplicações em cotas de uma mesma classe não podem exceder **25% do PL** da classe
  investidora (a classe restrita pode disciplinar a extrapolação).
- **Art. 44** — em até **180 dias** do início das atividades, a classe deve ter **mais de 50% do
  PL em direitos creditórios**; a classe de investimento em cotas, **no mínimo 67% em cotas de
  outros FIDC**. É **vedada** a aplicação em direitos creditórios e ativos de liquidez **no
  exterior** (§ 3º).
- **Art. 21, V** — a política de investimento deve fixar limites para aplicação em créditos
  originados/cedidos pelo administrador, gestor, consultoria e partes relacionadas, e para ativos
  de liquidez que envolvam **retenção de risco** por essas mesmas partes.

### 2.9 Retenção de risco

O Anexo II **define** retenção de risco (art. 2º, XXI):
> "qualquer obrigação contratual ou mecanismo existente no âmbito da operação de securitização,
> por meio do qual o **cedente ou terceiro retenha, total ou parcialmente, o risco de crédito**
> decorrente da exposição à variação do fluxo de caixa dos direitos creditórios da carteira."

**Importante:** a norma **define** e **exige disciplina em regulamento** (arts. 21, V, "b" e 22,
II) da retenção de risco por administrador/gestor e partes relacionadas, mas **não foi localizado,
no texto consolidado do Anexo Normativo II, um percentual mínimo obrigatório de retenção de risco
("skin in the game") imposto ao cedente/originador** nos moldes do regime europeu. O ancoramento
econômico do cedente ocorre por outras vias: subscrição de cotas subordinadas, coobrigação e
índice de subordinação regulamentar. Registre-se como **não localizado em fonte pública
consultada** qualquer percentual mínimo legal de retenção.

### 2.10 Deveres do gestor e do administrador (arts. 31 e 33)

**Gestor (art. 33)** — estruturar o fundo; executar a política de investimento, o que inclui
validar elegibilidade e requisitos de composição/diversificação, individualizadamente ou por
amostragem com modelo estatístico consistente; registrar os créditos ou entregá-los ao
custodiante; diligenciar para que a substituição de créditos não altere a relação risco/retorno;
formalizar corretamente a cessão; e **monitorar (VI)** o índice de subordinação, a adimplência da
carteira e a **taxa de retorno dos direitos creditórios, considerando pagamentos, pré-pagamentos e
inadimplência**.

**Administrador (art. 31)** — manter registros separados de **toda negociação entre
administrador/gestor/custodiante/registradora/consultoria e partes relacionadas, de um lado, e a
classe, de outro** (inciso I); **encaminhar ao SCR do Banco Central** os dados individualizados de
risco de crédito de cada operação, **mensalmente, em até 10 dias úteis** após o fim do mês
(inciso II e parágrafo único).

### 2.11 Informações periódicas — a origem dos dados do painel (art. 27)

O administrador é responsável por:
- **III** — encaminhar o **informe mensal** à CVM, conforme o **Suplemento G**, em até **15 dias**
  após o fim do mês;
- **IV** — encaminhar o **demonstrativo de composição e diversificação** das classes de
  investimento em cotas, mensalmente, em até 15 dias;
- **V** — encaminhar o **demonstrativo trimestral** em até **45 dias** após o fim do trimestre
  civil, evidenciando:
  - (a) os **resultados da última verificação de lastro pelo custodiante (art. 38)**, explicitando
    **a quantidade e a relevância dos créditos inexistentes porventura encontrados**;
  - (b) os resultados do **registro** dos créditos quanto a origem, existência e exigibilidade,
    explicitando **quantidade e relevância dos créditos não aceitos para registro**;
  - (c) o ajuizamento de ação de cobrança ou processo administrativo/judicial/arbitral envolvendo
    a classe, com o percentual do patrimônio envolvido e em risco;
  - (d) as informações do relatório trimestral do gestor (§ 3º).

O **relatório trimestral do gestor (§ 3º)**, entregue ao administrador em até 40 dias, deve conter,
entre outros: critérios de concessão de crédito **dos originadores que representem individualmente
10% ou mais da carteira**; alterações nas garantias; **forma como se operou a cessão, incluindo a
indicação do caráter definitivo ou não da cessão**; impacto de pré-pagamentos; **condições e
motivação de alienação de direitos creditórios**; impacto de eventual descontinuidade da originação
ou cessão; e fatos que afetaram a regularidade dos fluxos financeiros.

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **O informe mensal (Suplemento G) é a espinha dorsal do painel.** Prazo legal de 15 dias
>    após o mês de referência ⇒ o mês corrente é sempre incompleto; qualquer corte deve descartar
>    ou sinalizar os últimos 45 dias.
> 2. **Existe um campo regulatório de "créditos inexistentes encontrados na verificação de
>    lastro"** (art. 27, V, "a") e outro de **"créditos não aceitos para registro"** (alínea "b").
>    São **indicadores diretos e oficiais de lastro problemático** — muito mais fortes que
>    qualquer proxy estatístico. Se o painel não os coleta, deve declarar a lacuna.
> 3. **Inadimplência ≈ 0 com cedente concentrado é anomalia de primeira ordem**: o art. 33, VI
>    obriga o gestor a monitorar adimplência; o caso Silverado (PAS 19957.006858/2019-25) mostrou
>    que "reduzidíssimo histórico de inadimplências" foi exatamente o que mascarou a fraude.
> 4. **O limite de 20% por devedor (art. 45) tem exceções amplas** — investidores profissionais
>    (§ 7º), receitas públicas (§ 8º), qualificados com devedor de baixo risco (§ 3º). Um alerta
>    de "extrapolação de 20%" **só é válido depois de checar público-alvo e natureza do devedor**;
>    caso contrário produz falso positivo em massa.
> 5. O limite do art. 45 é **por devedor/coobrigado**, não por cedente. Concentração por **cedente**
>    não tem teto geral na norma — é matéria de regulamento (art. 21). Logo, alerta de concentração
>    por cedente é **risco de mercado**, não presunção de ilegalidade.
> 6. **Dado de partes relacionadas existe por obrigação legal** (art. 31, I). Cruzamentos
>    gestor↔cedente↔custodiante↔registradora são leitura direta das vedações dos arts. 30, 40 e 42.
> 7. **Art. 44 (>50% em direitos creditórios em 180 dias)** dá um teste de enquadramento
>    computável a partir da carteira. A SSE (OC SSE 8/2025, itens 16-20) reconhece que o
>    recebimento de garantias executadas pode gerar **desenquadramento passivo**, sujeito ao art.
>    90 da parte geral — ou seja, **desenquadramento nem sempre é irregularidade**.
> 8. **Fundos com classes exclusivas de investidores profissionais operam sob regime aliviado**
>    (arts. 15, 30 §6º, 42 §2º, 45 §7º, 52 III). Um painel que aplique a régua do varejo a esses
>    veículos gera alarme falso. Segmentar por público-alvo é obrigatório.

---

## 3. Resolução CVM 200/2024 — prazos de adaptação

**Fontes:**
- Notícia oficial: <https://www.gov.br/cvm/pt-br/assuntos/noticias/2024/cvm-prorroga-prazos-de-adaptacao-a-nova-regulamentacao-de-fundos>
- Página da norma: <https://conteudo.cvm.gov.br/legislacao/resolucoes/resol175.html> (lista a RCVM 200/24 entre as alterações)

Aprovada em **06/03/2024** e divulgada em **12/03/2024**. O que mudou:

| Item | Prazo original | Prazo novo (definitivo) |
|---|---|---|
| Adaptação dos **FIDC** em funcionamento | 01/04/2024 | **29/11/2024** |
| Adaptação dos **demais fundos** em funcionamento | 31/12/2024 | **30/06/2025** |
| Art. 140, §§ 2º e 4º (estrutura de classes e subclasses) | 01/04/2024 | **01/10/2024** |
| Art. 140, § 1º (segregação de taxas) | 01/04/2024 | **01/11/2024** |

A CVM declarou que os prazos foram estabelecidos **"em caráter definitivo e não serão objeto de
nova prorrogação"**, motivando a prorrogação por desafios operacionais ligados à reforma
tributária dos fundos. A RCVM 200 também fez ajustes pontuais no Anexo Normativo III (FII/FIAGRO).

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> - **29/11/2024 é a data de corte do regime FIDC.** Antes dela, o estoque de FIDC ainda podia
>   operar sob a estrutura da ICVM 356/2001; depois dela, todo FIDC em funcionamento deveria estar
>   sob a RCVM 175.
> - **01/10/2024 é a data em que "classe/subclasse" passa a ser a unidade reportante** para o
>   universo geral de fundos (art. 140, §§ 2º e 4º).
> - Portanto o painel deve tratar **jul/2023 – nov/2024 como janela de transição**, com
>   convivência de dois regimes de reporte. Toda variação brusca de contagem de veículos, de PL
>   médio ou de número de classes nessa janela é **candidata a artefato regulatório, não a evento
>   econômico** — e deve ser testada como tal antes de virar narrativa.
> - Séries de "número de FIDCs" que cruzem 01/10/2024 sem ajuste **superestimam o crescimento**,
>   porque um fundo pré-existente pode passar a reportar N classes.

---

## 4. Resolução CVM 240/2026 — créditos de empresas em recuperação judicial

**Fontes:**
- Notícia oficial: <https://www.gov.br/cvm/pt-br/assuntos/noticias/2026/cvm-edita-norma-com-ajustes-pontuais-no-anexo-ii-da-resolucao-175-sobre-fidc>
- Texto refletido no Anexo II consolidado: <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol175consolid_Anexo02.pdf>

Resolução de **05/03/2026**, com efeitos **a partir de 06/03/2026**. Duas mudanças, ambas
flexibilizadoras, ambas no Anexo Normativo II:

1. **Fim da exigência de homologação judicial do plano.** A alínea "b" do inciso I do § 1º do
   art. 2º — que exigia que a sociedade estivesse "sujeita a plano de recuperação homologado em
   juízo" para que seus créditos performados fossem tratados como **padronizados** — foi
   **REVOGADA**. Passa a bastar que os créditos cedidos por empresa em recuperação judicial ou
   extrajudicial **não sejam originados por contratos mercantis de compra e venda para entrega ou
   prestação futura**.
2. **Coobrigação deixa de contaminar.** A alínea "e" do inciso XIII do art. 2º passou de
   "o devedor **ou coobrigado** seja sociedade empresária em recuperação judicial ou
   extrajudicial" para **"o devedor seja sociedade empresária em recuperação judicial ou
   extrajudicial"**. Ou seja, a **coobrigação assumida por sociedade em recuperação** deixou de,
   por si só, qualificar o direito creditório como não-padronizado.

A CVM informa que a norma **não passou por Análise de Impacto Regulatório nem por consulta
pública**, dado seu caráter pontual e flexibilizador, e que o objetivo é remover entraves à cessão
de recebíveis por empresas em recuperação, ampliando o acesso dessas empresas a recursos via FIDC.

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **06/03/2026 é uma quebra de definição, não de comportamento.** Uma carteira idêntica pode
>    mudar de classificação (não-padronizado → padronizado) da noite para o dia. Qualquer série de
>    "% de DC não-padronizado" que cruze essa data precisa de nota e, idealmente, de recálculo
>    retroativo sob definição constante.
> 2. **Efeito esperado no público-alvo:** como o art. 15 restringe classes com DC não-padronizado
>    a investidores profissionais, a reclassificação **amplia o universo de investidores elegíveis**
>    para créditos de empresas em RJ. Migração de classes de "profissional" para outros públicos a
>    partir de mar/2026 deve ser lida à luz da RCVM 240 antes de qualquer interpretação de
>    apetite a risco.
> 3. **Cuidado interpretativo obrigatório:** um aumento de exposição a créditos de empresas em RJ
>    após mar/2026 é, em primeira leitura, **resposta a incentivo regulatório** — e não evidência
>    de deterioração de crédito nem de má-fé. O painel deve dizer isso explicitamente.
> 4. Manter uma **flag de vintage normativo** (`regime_dc_np`) por observação: `pre_240` /
>    `pos_240`.

---

## 5. Resolução CVM 50 — PLD/FTP aplicável a administradores e gestores de FIDC

**Fontes:**
- Página da norma: <https://conteudo.cvm.gov.br/legislacao/resolucoes/resol050.html>
- Texto consolidado (PDF): <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/001/resol050consolid.pdf>
- Nota explicativa: <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/notas-explicativas/anexos/nota_resol050.pdf>

Resolução de **31/08/2021**, publicada em **02/09/2021**. Revogou a Instrução CVM 617/2019 e sua
nota explicativa. **Alterada pelas Resoluções CVM 179/2023 e 245/2026.**

### 5.1 Quem está sujeito (art. 3º)

Sujeitam-se às obrigações, **no limite de suas atribuições**:
- **I** — pessoas naturais ou jurídicas que prestem, em caráter permanente ou eventual, serviços
  de **distribuição, custódia, intermediação ou administração de carteiras** — o que alcança
  **administradores fiduciários, gestores e custodiantes de FIDC**;
- **II** — entidades administradoras de mercados organizados e operadoras de infraestrutura;
- **III** — escrituradores, consultores de valores mobiliários, agências de rating,
  representantes de investidores não residentes e **companhias securitizadoras**;
- **IV** — **auditores independentes**.

### 5.2 Política de PLD/FTP e abordagem baseada em risco (arts. 4º a 7º)

- **Art. 4º** — política escrita, aprovada pela alta administração e mantida atualizada, contendo
  governança, metodologia de tratamento e mitigação de riscos, diretrizes de **conhecimento
  contínuo do cliente**, diretrizes para **identificação do beneficiário final**, monitoramento e
  detecção de atipicidades, e critérios de **indicadores de efetividade**. A atualização cadastral
  de clientes ativos observa **intervalo máximo de 5 anos** (inciso III).
- **Art. 5º — avaliação interna de risco.** As pessoas dos incisos I a III do art. 3º devem
  identificar, analisar, compreender e mitigar os riscos de LD/FTP, devendo:
  - **I** — elencar **todos os produtos, serviços, canais de distribuição e ambientes de
    negociação e registro**, segmentando-os em **baixo, médio e alto risco**;
  - **II** — **classificar os clientes por grau de risco**, em baixo, médio e alto.
  - § 2º — **pessoas expostas politicamente (PEP)**, seus familiares e estreitos colaboradores
    (Anexo A), e **organizações sem fins lucrativos**, exigem tratamento específico.
- **Art. 6º — relatório anual da avaliação interna de risco**, elaborado pelo diretor do art. 8º e
  encaminhado à alta administração **até o último dia útil de abril**, contendo obrigatoriamente
  tabela com: (a) número de operações e situações atípicas detectadas por hipótese do art. 20;
  (b) número de análises realizadas (art. 21); (c) **número de comunicações de operações suspeitas
  reportadas ao COAF** (art. 22); (d) data do reporte da **declaração negativa** (art. 23).
- **Art. 7º** — regras, procedimentos e controles internos **escritos, passíveis de verificação e
  disponíveis para consulta da CVM**; treinamento contínuo.
- **Art. 8º** — indicação de **diretor estatutário responsável**, comunicada à CVM em **7 dias
  úteis** da investidura; a função pode ser acumulada desde que sem conflito com as áreas de
  negócio.
- **Art. 9º** — a alta administração é responsável pela aprovação e adequação da política, da
  avaliação interna de risco e dos controles.

### 5.3 Beneficiário final (art. 13)

> As informações cadastrais de clientes pessoa jurídica e demais entidades "devem abranger as
> pessoas naturais autorizadas a representá-los, **todos seus controladores, diretos e indiretos**,
> e as pessoas naturais que sobre eles tenham **influência significativa**, até alcançar a pessoa
> natural caracterizada como **beneficiário final**".

- **§ 1º** — a instituição define em sua política o percentual mínimo que caracteriza controle
  direto ou indireto, **observado que não pode ser superior a 25%**.
- **§ 2º** — dispensa de identificar o beneficiário final para: companhia aberta no Brasil;
  **fundos e clubes de investimento nacionais registrados** (desde que não exclusivos, com gestão
  discricionária e CPF/CNPJ de todos os cotistas informados à RFB); instituições autorizadas pelo
  BCB; seguradoras e entidades de previdência; e investidores não residentes qualificados
  (bancos centrais, organismos multilaterais, companhias abertas, etc.).
- **§ 3º** — mesmo dispensado, deve-se observar se a jurisdição de origem é classificada pelo
  **GAFI** como não cooperante ou com deficiências estratégicas.

### 5.4 Monitoramento, análise e comunicação (arts. 20 a 23)

**Art. 20 — monitoramento contínuo e situações que exigem atenção especial.** As atipicidades
que, após detecção e análise, podem configurar indícios de LD/FTP incluem:

- **I — derivadas da identificação do cliente:**
  - (a) impossibilidade de manter **cadastro atualizado**;
  - (b) **impossibilidade de identificar o beneficiário final**;
  - (c) impossibilidade de concluir as diligências do Capítulo IV;
  - (d) operações incompatíveis com ocupação, rendimentos ou situação patrimonial (PF);
  - (e) **incompatibilidade da atividade econômica, do objeto social ou do faturamento informados
    com o padrão operacional de clientes do mesmo perfil** (PJ).
- **II — relacionadas a operações no mercado de valores mobiliários:**
  - (a) operações **entre as mesmas partes ou em benefício das mesmas partes** com seguidos ganhos
    ou perdas para algum dos envolvidos;
  - (b) **oscilação significativa** de volume ou frequência de negócios;
  - (c) desdobramentos que possam constituir **artifício para burla da identificação dos efetivos
    envolvidos e beneficiários**;
  - (d) atuação contumaz **em nome de terceiros**;
  - (e) **mudança repentina e objetivamente injustificada** da modalidade operacional usual;
  - (f) grau de complexidade e risco incompatível com o perfil do cliente **e com o porte e o
    objeto social do cliente**;
  - (g) operações com aparente finalidade de gerar perda ou ganho **sem fundamento econômico ou
    legal**;
  - (h) **transferências privadas de recursos e de valores mobiliários sem motivação aparente**;
  - (i) **depósitos ou transferências realizadas por terceiros** para liquidar operação de cliente;
  - (j) **pagamentos a terceiros** por conta de liquidação ou resgate de garantias;
  - (k) operações **fora de preço de mercado**.
- **III** — situações ligadas a terrorismo/FPADM e a sanções do CSNU (Lei 13.810/2019) e a
  Lei 13.260/2016;
- **IV** — operações com pessoas ou entidades sediadas em jurisdições que **não aplicam ou aplicam
  insuficientemente as recomendações do GAFI**, ou com **tributação favorecida / regime fiscal
  privilegiado** (listas da RFB);
- **V** — outras hipóteses a critério da pessoa obrigada.

**Art. 21 — análise.** Procedimento regular e tempestivo de análise das situações detectadas,
observando a política de PLD/FTP e a avaliação interna de risco.

**Art. 22 — comunicação ao COAF.** Devem comunicar ao COAF, **mediante análise fundamentada**,
todas as situações e operações detectadas, ou propostas de operações, que possam constituir-se em
**sérios indícios de LD/FTP**. A comunicação deve conter, no mínimo: data de início do
relacionamento; **explicação fundamentada dos sinais de alerta**; descrição e detalhamento das
operações; informações das diligências do art. 17, inclusive se se trata de PEP; e a **conclusão
fundamentada da análise**.
- **§ 2º — vedação absoluta de "tipping off"**: abster-se de dar ciência do ato a qualquer pessoa,
  inclusive ao comunicado.
- **§ 3º — prazo de 24 horas** a contar da conclusão da análise que caracterizou a suspeição.
- **§ 4º** — comunicações de boa-fé não acarretam responsabilidade civil ou administrativa.

**Art. 23 — declaração negativa.** Se nada houver a comunicar no ano civil anterior, comunicar à
CVM **anualmente, até o último dia útil de abril**.

**Art. 25** — manter registro de **toda operação com valores mobiliários, independentemente do
valor**.

### 5.5 Resolução CVM 245/2026 — atualização pós-avaliação do GAFI

**Fontes:**
- Notícia oficial: <https://www.gov.br/cvm/pt-br/assuntos/noticias/2026/cvm-altera-pontualmente-resolucao-50-sobre-pld-ftp>
- Texto: <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/200/resol245.pdf>

Publicada em **01/07/2026**, **em vigor desde 15/07/2026**. Decorre da avaliação mútua do Brasil
pelo GAFI e visa alinhamento à **Recomendação 19 do GAFI**. Duas mudanças:

1. **Novo art. 17-A** — **diligência reforçada para investidores não residentes** de jurisdições
   listadas pelo GAFI. Os deveres alcançam administradores fiduciários, gestores, distribuidores,
   custodiantes, consultores, securitizadoras e demais pessoas do art. 3º, e se aplicam também a
   clientes — residentes ou não — cuja **estrutura societária, cadeia de controle, beneficiários
   finais ou representantes** estejam direta ou indiretamente vinculados às jurisdições listadas.
2. **Ajuste no art. 16, § 1º, I** — quando **não for possível identificar o beneficiário final**, o
   monitoramento do investidor deve ser **contínuo e reforçado**, com procedimentos mais rigorosos
   de seleção de operações.

A CVM registra que a norma foi dispensada de AIR e consulta pública e que **não se confunde com a
revisão mais ampla das Resoluções 13 e 50 prevista na agenda regulatória de 2026**.

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **A RCVM 50 opera sobre PRESTADORES, não sobre fundos.** Um FIDC não é sujeito obrigado; seu
>    **administrador e seu gestor** são. Portanto qualquer leitura PLD do painel deve ser
>    endereçada ao prestador, nunca ao veículo. Isso é decisivo para não imputar conduta a fundos.
> 2. **Boa parte dos "red flags" do painel tem correspondência textual no art. 20.** Ex.:
>    - operações entre as mesmas partes / em benefício das mesmas partes → art. 20, II, "a";
>    - oscilação significativa de volume → art. 20, II, "b" (equivale a saltos de PL/captação);
>    - mudança repentina e injustificada de modalidade operacional → art. 20, II, "e";
>    - incompatibilidade entre **faturamento/objeto social do cedente** e o padrão operacional →
>      art. 20, I, "e" (equivale ao cruzamento cedente × CNAE × porte);
>    - **recebimento por terceiros / pagamento a terceiros** → art. 20, II, "i" e "j" (dialoga
>      diretamente com a vedação do art. 41 do Anexo II);
>    - contraparte em jurisdição GAFI ou de tributação favorecida → art. 20, IV.
>    **Isso permite fundamentar cada red flag em texto normativo em vez de em intuição** — e é a
>    melhor defesa jurídica do painel. Recomenda-se que cada regra do painel carregue o campo
>    `fundamento_normativo`.
> 3. **A dispensa de beneficiário final para fundos registrados (art. 13, § 2º, II) tem condições**
>    — não pode ser fundo exclusivo, precisa de gestão discricionária e de CPF/CNPJ de todos os
>    cotistas na RFB. Logo, **"cotista fundo exclusivo" é, por desenho normativo, um caso de
>    diligência ampliada**, não de dispensa.
> 4. **Cotista único / dois cotistas / interesse único** conecta-se à exceção de fundo exclusivo do
>    art. 13, § 2º, II, "a" e ao art. 45, § 7º do Anexo II. É um marcador legítimo de perfil, não
>    uma acusação.
> 5. **CPF/CNPJ inválido ou com dígitos repetidos deixou de ser aceito no informe mensal a partir
>    de 02/01/2026** (OC SSE 9/2025, ver seção 6). Isso significa que **a qualidade do campo de
>    identificação melhora abruptamente em jan/2026** — uma quebra de série de qualidade de dado,
>    não de comportamento de mercado.
> 6. Após **15/07/2026**, a dimensão "jurisdição do investidor não residente" ganha peso
>    supervisório. Se o painel tiver detentores não residentes, vale cruzar com a lista GAFI.

---

## 6. Ofícios Circulares recentes da SIN/SSE sobre FIDC

### 6.1 Ofício-Circular nº 8/2025/CVM/SSE — 17/11/2025

**PDF oficial:** <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/oficios-circulares/sse1/anexos/oc-sse-0825.pdf>
**Página:** <https://conteudo.cvm.gov.br/legislacao/oficios-circulares/sse1/oc-sse-0825.html>
**Notícia:** <https://www.gov.br/cvm/pt-br/assuntos/noticias/2025/area-tecnica-da-cvm-orienta-sobre-anexos-normativos-a-resolucao-cvm-175-relacionados-a-fidc-fii-e-fiagro>

Dirigido a administradores e gestores de FIDC, FIAGRO e FII. Entendimentos relevantes:

| # | Tema | Entendimento da SSE |
|---|---|---|
| I | FIAGRO equiparado a FIDC | Cotas de FIAGRO só se equiparam a cotas de FIDC se o **regulamento** fixar política de **mínimo 50% em direitos creditórios** (art. 44 do Anexo II). Aplicam-se aos FIAGRO os limites máximos por modalidade, emissor, devedor e coobrigado. |
| II | Verificação de lastro (art. 36) | O gestor calibra o grau de verificação conforme a modalidade do crédito. **Valores mobiliários representativos de crédito (art. 2º, XII, "b") ofertados publicamente com registro na CVM estão fora do escopo do art. 36.** |
| III | Conta de livre movimentação (arts. 41 e 52, III) | A exceção do art. 52, III subsiste quando o **cedente acumula a função de agente de cobrança** (art. 32, § 2º), mas **não se estende a outros prestadores** — vedado o recebimento pela consultoria especializada, salvo se figurar como cedente. |
| IV | Recebimento de garantias (art. 43) | Ativos recebidos por execução de garantia (p. ex. imóveis) podem não ser direitos creditórios e gerar **desenquadramento passivo** do mínimo de 50%, sujeitando o gestor ao art. 90 da parte geral; deve haver **plano de alienação e reenquadramento**. O tratamento tributário (Res. CMN 5.111) é **paralelo e distinto** do enquadramento da RCVM 175. |
| V | FII investindo em FIDC | O FII pode acessar créditos imobiliários indiretamente via CRI ou **cotas de FIDC**, desde que o FIDC investido tenha política restrita a atividades permitidas ao FII. |

### 6.2 Ofício-Circular-Conjunto nº 1/2025/CVM/SIN/SSE — 01/12/2025

**PDF oficial:** <https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/oficios-circulares/sin/anexos/occ-sin-sse-0125.pdf>
**Notícia:** <https://www.gov.br/cvm/pt-br/assuntos/noticias/2025/area-tecnica-da-cvm-divulga-oficio-circular-com-interpretacoes-de-dispositivos-da-resolucao-cvm-175>

Trata de **transparência de taxas**. SIN e SSE reconhecem a **Plataforma de Transparência de
Taxas da ANBIMA** como instrumento centralizado substituto da divulgação no site de cada gestor.
A partir da adoção da Plataforma, ficam **dispensadas** (i) a disponibilização do Sumário de
Remuneração nos canais do gestor e (ii) a atualização e envio pelo **Sistema Fundos.Net para FII,
FIDC e FIAGRO**. Os administradores devem dar publicidade por comunicado ao mercado no Fundos.Net,
informando o link. Referências anteriores a "Sumário de Remuneração" devem ser reinterpretadas
como correspondendo à Plataforma ANBIMA. Antecedentes citados: OC SIN 3/2024 (11/07/2024) e
Ofício nº 20/2024/CVM/SSE (22/11/2024).

### 6.3 Ofício-Circular nº 9/2025/CVM/SSE — 15/12/2025 *(o mais relevante para o pipeline)*

**Página:** <https://conteudo.cvm.gov.br/legislacao/oficios-circulares/sse1/oc-sse-0925.html>
**Notícia:** <https://www.gov.br/cvm/pt-br/assuntos/noticias/2025/area-tecnica-da-cvm-divulga-melhorias-no-informe-mensal-de-fidc-no-sistema-fundos.net>

Comunica aos administradores de FIDC que, **a partir de 02/01/2026**, está disponível no Sistema
Fundos.Net a **versão 6.6 do Informe Mensal de FIDC**, com três mudanças:

1. **Tabela X** — possibilidade de inclusão de **subclasse sem estrutura de subordinação**;
2. **Tabela X** — inclusão de **identificador único para cada subclasse**;
3. **Tabelas I e VIII (campos a.11 e b.11)** — **não serão aceitos CPF ou CNPJ inválidos ou com
   dígitos repetidos**.

### 6.4 Ofício de fevereiro de 2026 sobre informações periódicas e multas cominatórias

**Notícia:** <https://www.gov.br/cvm/pt-br/assuntos/noticias/2026/area-tecnica-orienta-sobre-envio-de-informacoes-periodicas-e-multas-cominatorias-ordinarias-pelos-atrasos>
(06/02/2026) — esclarece dúvidas recorrentes de administradores de **FIDC, FII e FIAGRO** sobre
envio de informações periódicas e multas cominatórias ordinárias por atraso. O número exato do
ofício **não foi localizado em fonte pública consultada** nesta pesquisa; usar a notícia como
referência e confirmar o número na página de ofícios circulares da SSE antes de citar.

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **A partir de 02/01/2026 o Informe Mensal ganha identificador único de subclasse** (Tabela X).
>    Isso torna possível, pela primeira vez, rastrear subclasses de forma estável — mas **só a
>    partir de jan/2026**. Antes disso, o casamento subclasse↔série depende de heurística e deve
>    ser declarado como tal.
> 2. **"Subclasse sem estrutura de subordinação" passou a ser um caso previsto**. Um índice de
>    subordinação nulo/ausente após jan/2026 pode ser **estrutura legítima**, não dado faltante.
> 3. **A validação de CPF/CNPJ nas Tabelas I e VIII a partir de 02/01/2026 cria uma
>    descontinuidade de qualidade de dado.** Qualquer métrica de cobertura ou de resolução de
>    entidades de cedentes/cotistas que atravesse dez/2025→jan/2026 vai melhorar por razão
>    administrativa. Isso deve ser dito no painel, sob pena de se interpretar saneamento cadastral
>    como mudança de mercado.
> 4. **A dispensa de envio do Sumário de Remuneração pelo Fundos.Net (OCC 1/2025)** significa que
>    séries de taxas extraídas do Fundos.Net podem **secar** a partir da adoção da Plataforma
>    ANBIMA. Se o painel usa taxas, precisa de fonte alternativa e de nota de descontinuidade.
> 5. A existência de **multas cominatórias por atraso** significa que atraso de entrega é evento
>    administrativo comum e **não deve ser tratado como sinal de risco de fraude**.

---

## 7. Resolução CVM 160 — ofertas públicas, no que se aplica a FIDC

**Fonte:** <https://conteudo.cvm.gov.br/legislacao/resolucoes/resol160.html>

Resolução de **13/07/2022**, publicada no DOU em **14/07/2022**, com retificação do art. 81
republicada em 02/12/2022 e retificação do texto no DOU em 05/12/2022. **Revogou** as Instruções
CVM 400, 471, 476 e 530 e as Deliberações CVM 476, 533, 809, 818 e 850. **Alterada** pelas
Resoluções CVM 173/22, 180/23, 183/23, 208/24 e 226/25.

O que importa para FIDC:

- **Fim do regime da ICVM 476.** A dicotomia "oferta registrada (400) vs. esforços restritos (476)"
  foi substituída por **rito de registro automático** e **rito de registro ordinário** (com análise
  prévia da CVM).
- O **rito automático** dispensa análise prévia e pode ser usado em ofertas de cotas destinadas a
  **investidores profissionais ou qualificados**; para investidores profissionais, o registro
  ocorre automaticamente com a apresentação do pedido. Pode também ser adotado para oferta ao
  público em geral quando se tratar de **oferta subsequente sem alteração de política de
  investimento nem ampliação do público-alvo** desde a última oferta registrada.
- Com o rito automático deixam de existir: limite máximo de investidores acessados/alocados,
  **lock-up de 90 dias** para negociação secundária e a restrição de **4 meses** para nova oferta
  do mesmo valor mobiliário.
- A RCVM 160 estabeleceu **modelo específico de lâmina/prospecto para FIDC**, distinto do modelo
  dos demais fundos fechados.
- **Art. 70 — suspensão de oferta (stop order).** É a base legal usada pela SRE para suspender
  ofertas irregulares. Caso concreto de 2026: suspensão de quatro ofertas do **Multiplike Plus
  FIDC** em 20/05/2026, "nos termos das Resoluções CVM 160 e 175", com prazo até 19/06/2026 e
  ameaça de retirada das ofertas e cancelamento dos registros —
  <https://www.gov.br/cvm/pt-br/assuntos/noticias/2026/suspensas-quatro-ofertas-publicas-de-distribuicao-de-cotas-do-multiplike-plus-fidc>

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **Séries de emissão/distribuição de cotas quebram em 2023.** O desaparecimento das ofertas
>    "476" e a criação do rito automático mudam a contagem de ofertas registradas — variação em
>    torno de 2023 é, em boa medida, **mudança de regime de registro**.
> 2. **Ausência de lock-up e de intervalo mínimo entre ofertas** ⇒ maior frequência de ofertas por
>    fundo. Frequência elevada de emissões, isoladamente, **não é anomalia** pós-RCVM 160.
> 3. **Stop orders (art. 70) são eventos públicos, datados e atribuíveis** — excelente insumo para
>    a biblioteca de eventos de backtest. Mas são **medida cautelar e saneadora**, não decisão de
>    mérito: o status processual correto é "suspensão cautelar / prazo para saneamento", jamais
>    "condenação".
> 4. Cruzar o cadastro de ofertas com o painel permite identificar **veículos em captação ativa** —
>    variável de contexto útil para interpretar saltos de PL.

---

## 8. Plano Bienal de Supervisão Baseada em Risco (SBR) 2025-2026

**Fontes:**
- PDF oficial: <https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/acoes-e-programas/plano-de-supervisao-baseada-em-risco/2025-2026-1/plano-bienal-sbr-cvm-2025-2026.pdf>
- Página do programa: <https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/acoes-e-programas/plano-de-supervisao-baseada-em-risco>
- Notícia de lançamento: <https://www.gov.br/cvm/pt-br/assuntos/noticias/2024/cvm-lanca-plano-bienal-de-supervisao-baseada-em-risco-2025-2026>

### 8.1 FIDC é prioridade? **Sim.**

Os riscos e eventos foram **aprovados pelo Comitê de Gestão de Riscos (CGR) da CVM em
04/09/2024**, nos termos da Resolução CVM 53/2021. O plano abarca **10 riscos prioritários** e
**4 supervisões temáticas**.

O **Risco CVM nº 2 — PLD/FTP** é o segundo risco estrutural prioritário e desdobra-se em quatro
eventos, um deles dedicado a FIDC:

| ID | Área | Evento de risco | Score | Meta | Constava no SBR 2023-2024? |
|---|---|---|---|---|---|
| SMI 8 | SMI | Falhas nos processos de PLD/FTP dos intermediários nos mercados organizados | 120 | — | — |
| SIN 15 | SIN | Falhas nos processos de PLD/FTP por administradores de recursos e prestadores de serviço da indústria de gestão de recursos de terceiros | 128 | — | — |
| SIN 28 | SIN | Falhas nos processos de PLD/FTP para investidores não residentes | 128 | — | — |
| **SSE 21** | **SSE** | **Falhas na supervisão de PLD/FTP pela indústria de FIDCs** | **120** | **Reduzir** | **NÃO — evento novo** |

### 8.2 Ações de tratamento do evento SSE 21

Conforme o quadro de ações do plano:
- "Efetuar **verificações da aderência da Política de PLD/FTP em relação à Resolução CVM nº
  50/2021 para gestores de FIDCs**, selecionados com base em critérios de priorização, sendo,
  preferencialmente, **gestores de alto risco**."
- "Realizar supervisões em **gestores de FIDCs do grupo mais representativo (classificados como
  alto potencial de dano)**, a partir de critérios de priorização definidos pela SSE."
- Regulados supervisionados: **"Gestores de FIDC de alto risco e, residualmente, gestores de FIDC
  de médio risco."**
- Fontes de risco declaradas: **externalidades, falha operacional e conflito de interesses**.
  Mandatos legais impactados: **fiscalização e punição** e **proteção dos investidores**.
- Distribuição de peso das ações: Grupo 1 (intensidade alta) **90%**; Grupo 2 (média) 5%; Grupo 3
  (baixa) 5%.

### 8.3 Supervisão temática "PLD/FTP em FIPs e FIDCs"

O plano institui, entre as quatro supervisões temáticas, a de **PLD/FTP em FIPs e FIDCs**, com:
- **Justificativa:** "Necessidade de aprimorar a supervisão da CVM no que diz respeito às condutas
  dos gestores de recursos de terceiros no âmbito de suas políticas de PLD/FTP."
- **Objetivo:** abordagem estratégica e transversal do processo de supervisão e fiscalização,
  "avaliando inclusive o eventual uso e desenvolvimento de **ferramentas de análise de dados**", com
  "ações de supervisão e de fiscalização nos administradores e gestores de FIPs e FIDCs, inclusive
  com possibilidade de **inspeções presenciais**".
- **Resultados planejados:** consolidação dos dados coletados para subsidiar SIN, SSE e ASA na
  **mensuração do nível de risco** das atividades.
- **Esta supervisão temática NÃO constava do SBR 2023-2024.**

### 8.4 Fator limitador declarado

O plano registra que "a CVM continua a enfrentar **severas restrições de recursos**" e que o
concurso público de 2024 não resolveu integralmente a restrição de pessoal, com "impacto
operacional não desprezível nas atividades conduzidas pelas áreas técnicas".

> **→ O QUE ISSO IMPLICA PARA A ANÁLISE DE DADOS**
> 1. **O painel está alinhado à prioridade declarada do regulador.** O evento SSE 21 é **novo** no
>    biênio 2025-2026 e a unidade supervisionada é o **gestor de FIDC**, não o fundo. Rankings de
>    risco devem, portanto, ser construídos **no nível do gestor** para espelhar a lógica da CVM.
> 2. A CVM explicitamente estratifica gestores por **potencial de dano** e concentra **90% do peso
>    das ações no Grupo 1**. Isso legitima uma abordagem de **priorização por materialidade
>    (PL sob gestão)** combinada com risco — e não uma lista indiscriminada.
> 3. A própria CVM declara que avaliará o **"uso e desenvolvimento de ferramentas de análise de
>    dados"**. O painel se posiciona como instrumento auxiliar de triagem, **não como substituto de
>    supervisão** — e deve dizê-lo.
> 4. **A restrição de recursos declarada é um argumento de utilidade pública do painel**, mas
>    também um alerta: ausência de ação supervisória sobre uma entidade **não é atestado de
>    regularidade**. Nunca inferir "não fiscalizado ⇒ regular", nem "fiscalizado ⇒ irregular".
> 5. As três fontes de risco declaradas (externalidades, falha operacional, **conflito de
>    interesses**) mapeiam bem os eixos do painel: contágio por prestador comum, falha de
>    gatekeeper e circularidade cedente↔gestor↔cotista.

---

## 9. Síntese: as sete decisões de modelagem que a norma impõe ao painel

1. **Unidade de análise = classe** a partir de 01/10/2024 (fundos) e 29/11/2024 (FIDC); antes
   disso, veículo. Toda série que cruze essas datas carrega quebra estrutural declarada.
2. **Segmentar sempre por público-alvo** (geral / qualificado / profissional), porque os limites
   dos arts. 15, 42, 45 e 52 mudam materialmente conforme o público.
3. **Flag de vintage normativo para DC não-padronizado** (`pre_240` / `pos_240`, corte 06/03/2026).
4. **Ancorar cada red flag em dispositivo** — art. 20 da RCVM 50 e arts. 36, 38, 41, 42, 45 do
   Anexo II. Campo `fundamento_normativo` obrigatório.
5. **Direcionar toda leitura de conduta ao prestador (administrador/gestor/custodiante)**, nunca ao
   fundo — a RCVM 50 vincula prestadores, e a segregação patrimonial protege o veículo.
6. **Tratar jan/2026 como quebra de qualidade de dado** (validação de CPF/CNPJ e identificador de
   subclasse, OC SSE 9/2025), não como mudança de mercado.
7. **Preferir, quando disponíveis, os campos regulatórios diretos** de créditos inexistentes na
   verificação de lastro e de créditos não aceitos para registro (art. 27, V, "a" e "b") a
   quaisquer proxies estatísticos.

---

## 10. Registro de lacunas

- **Percentual mínimo obrigatório de retenção de risco pelo cedente/originador em FIDC:** não
  localizado em fonte pública consultada. O Anexo II define o conceito (art. 2º, XXI) e exige que
  o regulamento discipline limites (arts. 21, V e 22, II), mas não foi identificado piso legal.
- **Número do Ofício-Circular de fevereiro de 2026 sobre informações periódicas e multas
  cominatórias:** não localizado em fonte pública consultada (apenas a notícia de 06/02/2026).
- **Índice consolidado de todos os Ofícios Circulares CVM/SSE:** a URL
  `conteudo.cvm.gov.br/legislacao/oficios-circulares/sse1.html` retornou **HTTP 410 Gone** na
  consulta de 18/08/2026; usar
  <https://conteudo.cvm.gov.br/legislacao/oficios-circulares.html> como ponto de entrada.
- **Ofícios Circulares CVM/SSE emitidos em 2026 especificamente sobre FIDC:** não localizados em
  fonte pública consultada além da notícia de 06/02/2026 acima.
