# Metodologia — Recuperação Judicial, Falência e Vínculos com FIDCs

Documento de método do módulo `scripts/12_monitor_rj.py`. Descreve fontes, chave
de casamento, eventos monitorados, o tratamento jurídico do crédito e as
limitações conhecidas. Corte do universo de FIDCs: **2026-06-30**.

---

## 1. Advertência inicial (leia antes de qualquer conclusão)

**Estar em recuperação judicial não é evidência de irregularidade.** A
recuperação judicial é um instituto legal de preservação da empresa (art. 47 da
Lei 11.101/2005), destinado a viabilizar a superação de crise econômico-financeira
e a manutenção da atividade, do emprego e dos interesses dos credores. Uma empresa
em RJ é uma empresa que usou um mecanismo previsto em lei — não uma empresa
fraudulenta.

Do mesmo modo, **um FIDC aparecer na lista de credores de uma empresa em RJ não
significa que o fundo esteja quebrado, mal gerido ou irregular**. Significa que o
fundo é titular de crédito contra uma devedora em dificuldade. Fundos com
diversificação, subordinação, sobrecolateralização e limites de concentração
absorvem inadimplência isolada via provisionamento sem comprometer o veículo.

Nada neste módulo deve ser lido como imputação de conduta a qualquer empresa,
gestor, administrador ou fundo nominado.

---

## 2. Fontes

| # | Fonte | O que fornece | Papel aqui |
|---|---|---|---|
| 1 | **API Pública DataJud/CNJ** — `api-publica.datajud.cnj.jus.br` | Metadados processuais: número, classe, assunto, data de ajuizamento, órgão julgador, movimentos | *Denominador* judicial: quantas RJs/falências, onde e quando |
| 2 | **Cadastro CNPJ / Receita Federal** (espelho `minhareceita.org`) | Razão social, CNAE, situação cadastral, UF | Identificação de empresa por CNPJ; **detecção do sufixo legal de RJ** |
| 3 | **Informes mensais de FIDC / CVM** (base `data/duckdb/fidc.db`, tabela `cedentes`) | CPF/CNPJ dos cedentes por veículo e competência | Universo de cedentes a casar |
| 4 | **Imprensa especializada e fatos relevantes** (curadoria em `rj_casos_confirmados.csv`) | Nome, data do pedido/deferimento, tribunal, valor da dívida, natureza da ligação com FIDC | Casos confirmados, com URL e nível de evidência |

### 2.1 Chave pública do DataJud

A autenticação usa a chave pública documentada em
<https://datajud-wiki.cnj.jus.br/api-publica/acesso>, enviada como
`Authorization: APIKey <chave>`. A chave é pública e pode ser alterada pelo
CNJ a qualquer momento; o script aceita sobreposição por variável de ambiente
`DATAJUD_APIKEY`.

---

## 3. Viabilidade e limitações do DataJud (verificado empiricamente)

O acesso foi **testado de fato** neste ambiente, não presumido.

**Funciona:**

- Acesso HTTP à API: **sim**, HTTP 200 com a chave pública.
- Consulta por classe processual: **sim**, via `classe.codigo`.
- Filtro por período: **sim**, `range` sobre `dataAjuizamento`
  (formato `AAAAMMDDHHMMSS`, string).
- Cobertura por tribunal: índices separados por tribunal
  (`api_publica_tjsp`, `api_publica_tjrj`, …).
- Campos retornados por documento (14, sempre os mesmos):
  `id`, `tribunal`, `grau`, `numeroProcesso`, `dataAjuizamento`, `nivelSigilo`,
  `orgaoJulgador` (código, nome, código IBGE do município), `classe`
  (código, nome), `sistema`, `formato`, `dataHoraUltimaAtualizacao`,
  `@timestamp`, `movimentos` (código, nome, dataHora, complementos tabelados) e
  `assuntos` (código, nome).

**Correção importante sobre os códigos de classe.** A classe de Recuperação
Judicial é **129**, conforme esperado. Já **o código 130 não corresponde a
falência** e não retorna documento algum (`total = 0` em todos os tribunais
testados). A classe de falência empresarial na Tabela Processual Unificada do CNJ
é **108 — "Falência de Empresários, Sociedades Empresárias, Microempresas e
Empresas de Pequeno Porte"**. O código foi identificado por agregação de
`classe.codigo` sobre processos de varas de falência, e é o utilizado no script.
Classes correlatas úteis para trabalho futuro: 111 (Habilitação de Crédito),
114 (Impugnação de Crédito), 138 (Restituição de Coisa ou Dinheiro na Falência).

### 3.1 LIMITAÇÃO CRÍTICA — o DataJud público NÃO retorna as partes

**A API Pública do DataJud não expõe nome nem CPF/CNPJ de qualquer parte do
processo.** Não há campo de partes, polo ativo, polo passivo, advogados ou
litigantes. Verificações realizadas:

1. Varredura dos campos de 200 documentos de RJ do TJSP: **todos** apresentam
   exatamente as 14 chaves listadas acima. Nenhuma delas é de parte.
2. Consultas `exists` sobre `partes`, `poloAtivo`, `nomeParte`, `partes.nome` e
   `documento`: **0 documentos** em cada uma.
3. Busca textual livre por nome de empresa notória em todo o índice do TJSP:
   **0 resultados** — confirmando que nomes de empresa não estão indexados em
   lugar nenhum do documento.
4. O endpoint `_mapping` é bloqueado para a chave pública (HTTP 403,
   `security_exception`), então a confirmação é empírica, não declarativa.

**Consequência metodológica, declarada sem rodeios: é impossível casar processos
do DataJud com CNPJs de cedentes de FIDC.** Um processo de RJ obtido do DataJud é
anônimo do ponto de vista da empresa devedora. Qualquer tentativa de vincular um
número de processo a uma empresa exigiria consulta processo a processo aos portais
dos tribunais (fora do escopo desta API) ou a fonte comercial de dados judiciais.

Por isso, o DataJud é usado aqui **apenas como denominador agregado** — volume,
distribuição temporal e geográfica de RJs e falências — e nunca como fonte de
identificação de empresas. A identificação nominal vem das fontes 2 e 4.

### 3.2 Limitações operacionais adicionais

- **Ordenação:** apenas `dataAjuizamento` é ordenável. `_id`, `id` e
  `numeroProcesso` têm *fielddata* desabilitada, o que impede um desempate estável
  e portanto inviabiliza `search_after` clássico.
- **Janela de resultados:** `from + size` limitado a 10.000. O script contorna
  ambos os limites fatiando a coleta por classe e por trimestre, mantendo cada
  fatia bem abaixo do teto, e deduplicando por `id`.
- **Cobertura e defasagem de remessa:** o DataJud reflete o que cada tribunal
  remete ao CNJ. A defasagem é grande e foi medida nesta coleta (executada em
  18/08/2026): os meses de 2025-10 a 2026-06 trazem entre 138 e 241 processos
  cada, mas **2026-07 traz apenas 3 e 2026-08 nenhum**; o ajuizamento mais recente
  é de 07/07/2026. Ou seja, **os dois últimos meses são inutilizáveis para série
  temporal** — o aparente colapso de ajuizamentos é artefato de remessa, não
  queda real. Qualquer leitura de tendência deve descartar a cauda recente.
- **Sigilo:** processos com `nivelSigilo > 0` podem vir com metadados reduzidos.

---

## 4. Chave de casamento: CNPJ, e somente CNPJ

### 4.1 A regra

O casamento entre empresa em RJ/falência e cedente de FIDC é feito
**exclusivamente por CNPJ de 14 dígitos, comparado por igualdade exata**. Nunca
por semelhança, similaridade fonética, distância de edição ou correspondência
parcial de razão social.

Quando uma empresa é conhecida apenas pelo nome — porque a fonte pública não
divulgou o CNPJ — o registro é gravado com a marcação
`"correspondência por nome, requer validação humana"`, nível de evidência
`"dados insuficientes"` e papel `"relação apenas hipotética"`. **O vínculo não é
afirmado.**

### 4.2 Por que nome não basta

Razão social é uma chave péssima para identificar empresa no Brasil:

1. **Homonímia real.** Nomes como "Usina São João", "Comercial Silva" ou "Grupo
   Alpha" pertencem a dezenas de empresas distintas e não relacionadas, em
   estados diferentes. Casar por nome produz falso positivo que imputa RJ a
   empresa saudável — um erro com potencial de dano reputacional concreto.
2. **Grupos econômicos.** "Grupo X" na imprensa pode designar dezenas de CNPJs.
   O pedido de RJ pode alcançar apenas parte deles (litisconsórcio ativo), e a
   cedente do FIDC pode ser justamente uma controlada **não** incluída no
   processo.
3. **Grafia instável.** A mesma empresa aparece como "S.A.", "S/A", "SA", com e
   sem acentuação, com e sem o sufixo de RJ, com nome fantasia no lugar da razão
   social.
4. **Filiais.** Matriz e filiais compartilham a raiz de 8 dígitos mas têm CNPJs
   completos distintos. O informe de FIDC identifica o cedente pelo CNPJ completo.

Neste trabalho a raiz de 8 dígitos é usada **apenas para exploração** (localizar
candidatos do mesmo grupo econômico dentro da base). Quando um vínculo é afirmado
no resultado final, ele o é sobre o CNPJ completo, e a chave usada fica registrada
na coluna `chave_casamento` de cada linha.

### 4.3 A trilha mais forte: o sufixo legal na razão social

O **art. 69 da Lei 11.101/2005** obriga a empresa em recuperação judicial a
acrescentar ao seu nome empresarial a expressão *"em Recuperação Judicial"* em
todos os atos, contratos e documentos. Esse acréscimo é averbado no registro
empresarial e **se reflete na razão social do cadastro CNPJ da Receita Federal**.

Isso produz uma trilha de identificação de qualidade rara: partindo do **CNPJ do
cedente** informado no informe mensal do FIDC, consulta-se o cadastro CNPJ e
lê-se, na própria razão social oficial, a declaração do estado de recuperação
judicial. Não há inferência de nome envolvida — o CNPJ é a chave, e o estado
processual é atributo do registro. Analogamente, "Massa Falida de …" sinaliza
falência decretada.

Ressalvas honestas quanto a essa trilha:

- Ela indica que a empresa **está ou esteve** em RJ, mas o cadastro **não informa
  a data** do pedido nem do deferimento, nem o tribunal. Esses dados vêm da fonte 4.
- A baixa do sufixo após o encerramento da RJ (art. 63) **depende de averbação
  pela própria empresa** e frequentemente demora. Logo, presença do sufixo é
  evidência forte de RJ em algum momento, e não prova de RJ em curso hoje.
- A ausência do sufixo **não prova ausência de RJ**: recuperação extrajudicial
  (arts. 161 e ss.) não gera esse acréscimo, e há atraso de averbação.

Por isso o resultado combina as duas fontes: cadastro CNPJ para a âncora de
identidade, imprensa e fatos relevantes para data, tribunal, valores e status.

---

## 5. Eventos monitorados

O ciclo de um processo de insolvência é uma sequência de eventos com
consequências patrimoniais distintas. O campo `status_processual` registra em
qual deles cada caso se encontra:

| Evento | O que é | Por que importa para o FIDC |
|---|---|---|
| **Pedido** | Protocolo da petição inicial (art. 51) | Ainda não há efeito legal sobre credores; sinal antecedente de risco |
| **Deferimento do processamento** | Decisão do art. 52 | Dispara o *stay period* (art. 6º, §4º): suspende execuções e prescrições contra a devedora, em regra por 180 dias prorrogáveis |
| **Lista de credores** | Relação do art. 7º, §2º (AJ) e quadro-geral (art. 18) | Momento em que o FIDC se identifica como credor e a **classificação concursal/extraconcursal do seu crédito** é disputada |
| **Plano e aprovação** | Assembleia-geral de credores (arts. 45 e 56) e homologação (art. 58) | Define deságio, carência e prazo dos créditos **concursais** — impacta diretamente a marcação a mercado da carteira |
| **Convolação em falência** | Arts. 73 e 94 | Encerra a tentativa de soerguimento; muda o regime de realização do ativo e a ordem de pagamento (art. 83) |
| **Encerramento** | Art. 63 | Cumpridas as obrigações do plano; autoriza a baixa do sufixo do nome empresarial |

Para RJ **extrajudicial** (arts. 161 e ss.) o ciclo é distinto: pedido de
homologação, deferimento do processamento, homologação do plano. O caso da
Oncoclínicas, por exemplo, é de recuperação **extrajudicial** e está registrado
como tal — tratá-lo como RJ seria erro factual.

---

## 6. Crédito concursal x extraconcursal — e por que a classificação não segue o nome do credor

Esta é a distinção que mais importa economicamente e a que mais gera erro de
leitura.

### 6.1 A regra do art. 49

O **art. 49, *caput*, da Lei 11.101/2005** dispõe que estão sujeitos à
recuperação judicial **todos os créditos existentes na data do pedido, ainda que
não vencidos**. Esse é o crédito **concursal**: entra na fila, submete-se ao plano
e sofre o deságio, a carência e o alongamento nele aprovados.

O **art. 49, §3º** excepciona, entre outros, o credor titular da posição de
**proprietário fiduciário de bens móveis ou imóveis**, de **arrendador
mercantil**, de proprietário em contrato de venda com reserva de domínio e de
promitente vendedor de imóvel com irrevogabilidade. Esses créditos são
**extraconcursais**: não se submetem aos efeitos da recuperação e prevalecem os
direitos de propriedade e as condições contratuais — ressalvada a vedação de
venda ou retirada, durante o *stay period*, dos bens de capital essenciais à
atividade.

### 6.2 As duas variáveis que determinam a classificação

**(a) A natureza jurídica da operação, tal como contratada.** Em FIDC convivem
estruturas economicamente parecidas e juridicamente opostas:

- **Cessão definitiva (compra e venda) de recebíveis** — o crédito *sai* do
  patrimônio da cedente e passa a ser do fundo. O que o fundo tem a receber é do
  **sacado**, não da cedente. Se a **cedente** entra em RJ, o fundo em princípio
  não é credor concursal dela pelo recebível cedido, porque a titularidade já
  não é dela. O ponto de atenção desloca-se para a validade e a eficácia da
  cessão perante terceiros (notificação do devedor, art. 290 do Código Civil;
  registro) e para eventual **coobrigação**.
- **Cessão fiduciária de direitos creditórios em garantia** — há financiamento
  garantido por recebíveis, com propriedade fiduciária. O STJ consolidou que esse
  crédito é **extraconcursal** por força do art. 49, §3º, desde que constituída e
  registrada regularmente. O excedente eventualmente devido além do valor da
  garantia é habilitado como quirografário.
- **Operação com coobrigação / obrigação de recompra da cedente** — a pretensão
  do fundo *contra a cedente* nasce dessa obrigação pessoal. Ela tende a ser
  **concursal** se o fato gerador é anterior ao pedido, e a submissão ao plano é
  o desfecho usual.

**(b) A data do fato gerador em relação à data do pedido.** O art. 49 fixa o
marco na **existência do crédito na data do pedido**, não no vencimento e não na
data da cobrança. Crédito constituído **depois** do pedido é extraconcursal por
ser posterior ao marco (art. 67 trata do estímulo ao financiamento do devedor em
recuperação, e os créditos daí decorrentes recebem tratamento privilegiado).
Daí que **duas operações do mesmo fundo com a mesma empresa podem ter
classificações opostas** conforme tenham sido originadas antes ou depois do
protocolo.

### 6.3 A consequência prática

**Não se classifica crédito pelo nome do credor.** Saber que "o credor é um FIDC"
não diz absolutamente nada sobre concursalidade. A classificação depende do
contrato (cessão definitiva? cessão fiduciária? coobrigação?), do cumprimento das
formalidades de constituição e registro da garantia, e da data do fato gerador
frente ao pedido — e é, na prática, **matéria decidida no processo**, via
impugnação de crédito (art. 8º) e incidentes, com jurisprudência que evolui.

Por isso, **este módulo não classifica créditos como concursais ou
extraconcursais.** Fazê-lo a partir de dados cadastrais e notícias seria
inventar conclusão jurídica sem acesso aos contratos. O que o módulo faz é
registrar o **papel** observado do FIDC (abaixo) e sinalizar que a classificação
concursal é indeterminada a partir das fontes disponíveis.

---

## 7. Classificação do papel do FIDC

Taxonomia usada na coluna `papel_fidc`, com o significado de cada rótulo:

| Rótulo | Significado |
|---|---|
| `FIDC credor` | O fundo consta da lista de credores da empresa em RJ/falência (fonte pública o afirma) |
| `FIDC com exposição a cedente em RJ` | A empresa em RJ **cedeu** direitos creditórios ao fundo — risco de originação, de performance da carteira cedida e de eventual coobrigação |
| `FIDC com exposição a sacado em RJ` | A empresa em RJ é a **devedora dos recebíveis** adquiridos — risco direto de inadimplência da carteira |
| `empresa com coobrigação` | A cedente assumiu obrigação de recompra/coobrigação, o que cria pretensão do fundo contra ela |
| `relação apenas hipotética` | Há notícia de RJ, mas o vínculo com FIDC não está documentado ou o CNPJ não foi confirmado — **vínculo não afirmado** |

Cedente e sacado não são intercambiáveis: no primeiro caso o fundo comprou papel
*de* quem quebrou; no segundo comprou papel *contra* quem quebrou. As perdas
esperadas e os remédios contratuais diferem.

---

## 8. Efeito da Resolução CVM 240/2026

A **Resolução CVM 240, de 5 de março de 2026**, ajustou o **Anexo Normativo II**
da Resolução CVM 175 no tratamento dos direitos creditórios cedidos por empresas
em recuperação judicial ou extrajudicial. Está em vigor. As mudanças relevantes:

1. **Removeu a exigência de homologação judicial do plano de recuperação** como
   condição para que direitos creditórios **performados** cedidos por sociedade em
   recuperação sejam considerados **padronizados**. Antes, a cessão por empresa em
   recuperação empurrava a operação para a categoria de direitos creditórios **não
   padronizados** (FIDC-NP), com público-alvo restrito.
2. **Revisou o tratamento da coobrigação** assumida por sociedade em recuperação
   judicial ou extrajudicial na cessão de recebíveis: ela deixou de ser, por si
   só, elemento caracterizador de direito creditório não padronizado.

Note-se o alcance limitado: a flexibilização vale para direitos creditórios
**performados** — decorrentes de vendas ou serviços já entregues, com baixo risco
de cancelamento. Recebíveis a performar seguem fora dessa hipótese.

**Por que isso importa para a leitura desta base.** O efeito é que operações que
antes seriam classificadas como não padronizadas — e, portanto, confinadas a
FIDC-NP e a público mais restrito — podem passar a integrar carteiras de FIDCs
padronizados, inclusive de classes acessíveis ao varejo após a Resolução CVM 175.
Consequências metodológicas diretas:

- A fronteira estatística entre FIDC padronizado e FIDC-NP **muda de significado
  a partir de março de 2026**. Séries que cruzam essa data não são estritamente
  comparáveis: parte da variação pode ser reclassificação regulatória, não
  mudança de risco econômico.
- A presença de cedente em RJ numa carteira padronizada deixa de ser, por si só,
  anomalia regulatória — passa a ser possibilidade prevista em norma.
- Em contrapartida, cresce a importância de medir **exposição a cedente em RJ**
  como métrica própria, já que a classificação padronizado/NP deixou de capturá-la.

A norma amplia o uso do FIDC como funding de empresas em reestruturação. Isso é
uma escolha regulatória deliberada de política de crédito, não um indício de
irregularidade das operações que dela se valem.

---

## 9. Arquivos produzidos

| Arquivo | Conteúdo |
|---|---|
| `data/raw/datajud/<tribunal>_rj_falencia.json` | Retorno bruto da API, por tribunal |
| `data/analytic/rj_processos.csv` | Extrato normalizado dos processos (sem partes — ver §3.1) |
| `data/analytic/rj_processos_resumo.csv` | Contagem de processos por tribunal, classe e mês |
| `data/analytic/rj_casos_confirmados.csv` | Casos curados de fonte pública, com URL, `nivel_evidencia` e `status_processual` |
| `data/analytic/rj_matches_cedentes.csv` | Vínculos empresa-em-RJ × cedente de FIDC, com `chave_casamento` explícita |
| `data/raw/monitor_rj.log` | Log de execução, inclusive indisponibilidade de fonte |

### Níveis de evidência

- `fato confirmado por fonte primária` — cadastro CNPJ/RFB, fato relevante da
  companhia, decisão ou comunicado de tribunal.
- `indício forte` — imprensa especializada com dado quantificado e fonte nominada.
- `hipótese` — plausível, sem confirmação documental.
- `dados insuficientes` — CNPJ não confirmado; vínculo **não** afirmado.

### Resiliência

Se o DataJud estiver indisponível, `12_monitor_rj.py` registra a falha em
`data/raw/monitor_rj.log`, emite `rj_processos.csv` com o cabeçalho correto e sem
linhas, e retorna código 0. O pipeline não quebra e a ausência de dado fica
explícita em vez de silenciosa. O comportamento foi exercitado na prática: em uma
execução com erro HTTP 400 numa das consultas, o script produziu o CSV vazio,
logou o erro e seguiu.

---

## 10. O que este módulo deliberadamente não faz

- **Não** casa empresa e cedente por semelhança de nome.
- **Não** classifica crédito como concursal ou extraconcursal (ver §6.3).
- **Não** estima perda esperada de fundo a partir de exposição a cedente em RJ:
  a exposição medida é a participação do cedente na originação, não o saldo
  inadimplido, e não considera subordinação, garantias nem coobrigação.
- **Não** identifica cedentes pessoa física (CPF), para não reidentificar
  pessoas naturais.
- **Não** trata a presença de empresa em RJ na carteira como irregularidade.

---

## 11. Base legal e normativa citada

- Lei 11.101/2005, arts. 6º, §4º; 7º, §2º; 8º; 18; 47; 49 *caput* e §3º; 51; 52;
  56; 58; 63; 67; 69; 73; 83; 94; 161 e seguintes.
- Código Civil, art. 290 (notificação do devedor na cessão de crédito).
- Lei 10.931/2004, art. 42, e Código Civil, art. 1.361 (propriedade fiduciária).
- Resolução CVM 175, de 23/12/2022, e seu Anexo Normativo II (FIDC).
- Resolução CVM 240, de 05/03/2026 (cessão de direitos creditórios por empresas
  em recuperação) — comunicado oficial em
  <https://www.gov.br/cvm/pt-br/assuntos/noticias/2026/cvm-edita-norma-com-ajustes-pontuais-no-anexo-ii-da-resolucao-175-sobre-fidc>.
