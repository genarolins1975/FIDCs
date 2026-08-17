# Metodologia, dicionário de dados e controles

Data de corte: **30/06/2026** (última competência com cobertura completa nas
fontes primárias; a competência 07/2026 já está publicada, mas com ~120
informantes a menos que 06/2026, e é usada apenas como observação parcial).
Data de extração: **17/08/2026** (UTC), registrada arquivo a arquivo em
`manifesto_fontes.csv` com URL, SHA-256, tamanho e Last-Modified do servidor.

## 1. Fontes

| Nível | Fonte | Uso |
|---|---|---|
| 1 | CVM — Informe Mensal de FIDC (dados abertos), 2013-01 a 2026-07 | tamanho, evolução, carteiras, inadimplência, cedentes, cotistas, negócios, liquidez, SCR |
| 1 | CVM — Cadastro de fundos (`cad_fi.csv`) e Registro fundo/classe/subclasse (RCVM 175) | papéis institucionais (gestor, custodiante, controlador, auditor), situação, mapeamento classe→fundo |
| 1 | Resoluções CVM 175 (consolidada), 200 e 240 (textos oficiais) | perímetro regulatório |
| 1 | BCB/SGS série 433 (IPCA) | deflacionamento |
| 2 | ANBIMA (boletins e notícias oficiais) | validação externa de PL e captação |
| 3 | Receita Federal via minhareceita.org | razão social/CNAE de cedentes (resolução de entidades) |

## 2. Unidade de análise e a transição ICVM 489 → RCVM 175

O informe mensal era entregue **por fundo** até a adaptação à RCVM 175 e
passa a ser entregue **por classe** (campo `TP_FUNDO_CLASSE`). O prazo de
adaptação dos FIDCs foi 29/11/2024 (RCVM 200, art. 134), e a migração do
reporte ocorreu de forma escalonada entre dez/2024 e mar/2026 (em jun/2026
restam 19 informes em nível de fundo).

Unidade do painel canônico: **veículo informante** (fundo no regime antigo;
fundo OU classe no novo). Regras de dedupe aplicadas por competência:

1. CNPJ presente como `Fundo` e `Classe` na mesma competência → prevalece `Classe`;
2. linha `Fundo` cujo fundo tem classes com CNPJ próprio informando na mesma
   competência → excluída (sobreposição medida: R$ 0,13 bi em 06/2026, 3 casos).

Como ~95% dos FIDCs opera com classe única (CNPJ da classe = CNPJ do fundo),
a série número de veículos é aproximadamente comparável ao longo da transição;
a contagem de "classes" propriamente ditas só existe no regime novo.

## 3. Métricas e fórmulas

- **PL total** = Σ `TAB_IV_A_VL_PL` do painel canônico (tab IV do informe).
- **Direitos creditórios** = `TAB_I2A_VL_DIRCRED_RISCO` (aquisição substancial
  de riscos e benefícios) + `TAB_I2B_VL_DIRCRED_SEM_RISCO` (sem aquisição
  substancial — retenção de risco no cedente).
- **Circularidade intramercado** = Σ (`TAB_I2H_VL_COTA_FIDC` +
  `TAB_I2I_VL_COTA_FIDC_NP`): cotas de FIDC detidas por veículos do próprio
  universo. "PL líquido de circularidade" = PL total − essa parcela.
- **Inadimplência (medida abrangente)** = `TAB_V_B_VL_DIRCRED_INAD` +
  `TAB_VI_B_VL_DIRCRED_INAD` (parcelas vencidas e não pagas, todas as faixas)
  sobre `TAB_V_A + TAB_VI_A` (DC por prazo de vencimento). A medida da tab I
  (`TAB_I2A21`) cobre apenas parcelas vencidas de créditos "a vencer" e é
  reportada separadamente.
- **Subordinação** = Σ séries subordinadas+mezanino / Σ todas as séries
  (tab X_2, valor = quantidade × valor da cota).
- **Captação líquida** = captações − resgates − amortizações (tab X_4), após
  filtro de sanidade (operação ≤ 3×max(PL do mês, PL do mês anterior)+R$ 100 mi;
  descartes contados em `captacao_liquida_anual.csv`). Medida **bruta de
  dupla contagem intramercado** (subscrições de FIC-FIDC em FIDCs) e sujeita a
  integralizações em ativos; usada como ordem de grandeza.
- **Exposição estimada por cedente** = Σ sobre veículos de
  (`PR_CEDENTE`/100 × valor do bucket de DC correspondente), tab I, apenas
  top-9 cedentes por veículo, percentuais entre 0 e 100. É **estimativa
  inferior** (cauda além do top-9 não observável) e **indicador calculado**,
  não valor contábil.
- **Série real**: deflator IPCA (SGS 433), base jun/2026.
- **HHI** = Σ s², s = participação no PL do corte.

## 4. Resolução de entidades

- Prestadores: CNPJ + razão social conforme informe/registro CVM (sem fusão
  por grupo econômico, salvo indicação explícita; visões por entidade jurídica).
- Cedentes: CNPJ do informe (com zeros à esquerda restaurados), razão social,
  CNAE e situação cadastral da base pública do CNPJ (Receita Federal, via
  minhareceita.org). CPFs de cedentes pessoa física NÃO são resolvidos.
- Fundos multirregistro (gestor substituído): prevalece o registro ativo mais
  recente ("Em Funcionamento Normal" > "Em Liquidação" > demais; depois data).

## 5. Controles contra dupla contagem

| Risco | Controle |
|---|---|
| fundo × classe | regras 1-2 da seção 2; teste T3 (zero duplicatas) |
| FIDC investindo em FIDC | coluna separada `cotas_fidc_detidas`; PL líquido de circularidade |
| co-gestão / multirregistro | registro ativo mais recente; cobertura do ranking = 100,0% do PL |
| reapresentações | usa-se o arquivo vigente no portal (última versão publicada) |
| captação intramercado | declarada como limitação da métrica X_4 |

## 6. Limitações principais

1. **Sacados**: o informe público não identifica devedores individualmente
   (apenas distribuição de risco SCR por classe AA-H). Concentração por sacado:
   *não identificável com segurança nas fontes públicas consultadas*.
2. **Cotistas**: apenas contagens por categoria (não valores por cotista, nem
   identidade). Quem detém as cotas subordinadas em valor: parcialmente
   inferível (nº de cotistas), não confirmável em valor.
3. **Cedentes**: cobertura limitada ao top-9 por veículo e ao bucket informado;
   percentual reportado pelo administrador, sem auditoria individual.
4. **Gestor histórico**: o registro CVM é fotografia atual; mudanças de gestor
   não são rastreadas retroativamente (afeta variações 12/36/60m por gestor —
   por isso não publicadas).
5. **Dados autodeclarados**: informes contêm erros de preenchimento
   (documentados em `alertas.csv` e nos filtros de sanidade).
6. **Companhias com cotas de FIDC no balanço** (Par 6 do mandato): exigiria
   leitura de notas explicativas de DFP/ITR (não estruturadas em dados
   abertos); tratado como lacuna declarada nesta versão — ver relatório,
   seção Limitações.
7. **ANBIMA**: perímetro distinto (cobertura associativa); divergência
   documentada no teste T14.

## 7. Reprodução

```bash
python3 scripts/01_download.py            # baixa fontes + manifesto SHA-256
python3 scripts/02_build.py               # constrói DuckDB + parquet
python3 scripts/02b_build_series_classes.py
python3 scripts/03_analytics.py           # séries, rankings, alertas
python3 scripts/04_cedentes_nomes.py      # resolução de entidades (cedentes)
python3 scripts/05_testes_auditoria.py    # testes obrigatórios
```

Dependências: Python 3.11, pandas, duckdb, pyarrow, requests.
Ambiente de execução da versão publicada: Linux x86-64, 17/08/2026.
