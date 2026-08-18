# SCHEMA_CHANGELOG — Informe Mensal de FIDC

Gerado automaticamente por `scripts/15_matriz_fontes_schema.py` comparando os
cabeçalhos de cada tabela entre competências consecutivas. Toda mudança abaixo
foi detectada nos arquivos publicados pela CVM, não em documentação.

## Quebras de série de origem regulatória (não detectáveis por header)

| Data | Evento | Efeito analítico |
|---|---|---|
| 01/10/2024 | Classe/subclasse passa a ser a unidade reportante (RCVM 175, art. 140 §§ 2º e 4º, com prorrogação da RCVM 200) | muda a unidade de análise da série |
| 29/11/2024 | Prazo final de adaptação dos FIDC em funcionamento (RCVM 200, art. 134) | fim da convivência de regimes |
| 06/03/2026 | RCVM 240 altera a **definição** de direito creditório não-padronizado (revoga exigência de plano de RJ homologado; coobrigação de empresa em recuperação deixa de contaminar) | aumento de exposição a créditos de empresas em RJ após esta data é **resposta a incentivo regulatório**, não deterioração de carteira |
| 02/01/2026 | OC SSE 9/2025: Informe Mensal v6.6 passa a rejeitar CPF/CNPJ inválidos ou com dígitos repetidos (tabs I e VIII) e cria identificador único de subclasse | melhora administrativa na qualidade da resolução de entidades — quebra de comparabilidade na contagem de documentos válidos |

## Lacuna estrutural de fonte

O **demonstrativo trimestral** (Anexo II, art. 27, V, "a" e "b") obriga o
administrador a informar a **quantidade e a relevância dos créditos inexistentes
encontrados na verificação de lastro** e dos créditos não aceitos para registro.
Verificado em 18/08/2026: o Portal de Dados Abertos publica **apenas**
`FIDC/DOC/INF_MENSAL` — o demonstrativo trimestral não é distribuído em formato
estruturado, existindo somente como documento individual. É a informação pública
mais próxima de uma medida direta de fraude de lastro, e nenhum painel construído
sobre dados abertos consegue usá-la. Consta da agenda de recomendações
regulatórias.

**17 mudanças de layout detectadas** em 18 tabelas, entre 2013 e 202607.

## tab I — ativo, carteira, cedentes, circularidade, exclusividade (lentes 3,4)

**2019-11**
- criadas (55): `PRAZO_CONVERSAO_COTA`, `PRAZO_PAGTO_RESGATE`, `TAB_I2A12_CPF_CNPJ_CEDENTE_1`, `TAB_I2A12_CPF_CNPJ_CEDENTE_2`, `TAB_I2A12_CPF_CNPJ_CEDENTE_3`, `TAB_I2A12_CPF_CNPJ_CEDENTE_4`, `TAB_I2A12_CPF_CNPJ_CEDENTE_5`, `TAB_I2A12_CPF_CNPJ_CEDENTE_6`, `TAB_I2A12_CPF_CNPJ_CEDENTE_7`, `TAB_I2A12_CPF_CNPJ_CEDENTE_8`, `TAB_I2A12_CPF_CNPJ_CEDENTE_9`, `TAB_I2A12_PR_CEDENTE_1`, …
- removidas (18): `TAB_I2B1_CPF_CNPJ_CEDENTE_1`, `TAB_I2B1_CPF_CNPJ_CEDENTE_2`, `TAB_I2B1_CPF_CNPJ_CEDENTE_3`, `TAB_I2B1_CPF_CNPJ_CEDENTE_4`, `TAB_I2B1_CPF_CNPJ_CEDENTE_5`, `TAB_I2B1_CPF_CNPJ_CEDENTE_6`, `TAB_I2B1_CPF_CNPJ_CEDENTE_7`, `TAB_I2B1_CPF_CNPJ_CEDENTE_8`, `TAB_I2B1_CPF_CNPJ_CEDENTE_9`, `TAB_I2B1_PR_CEDENTE_1`, `TAB_I2B1_PR_CEDENTE_2`, `TAB_I2B1_PR_CEDENTE_3`, …

**2020-11**
- criadas (6): `CLASSE`, `CLASSE_UNICA`, `CNPJ_CLASSE`, `CNPJ_FUNDO_CLASSE`, `TAB_I2C5_VL_COTA_FIF`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab V — DC com risco: prazos e inadimplência

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab II — carteira por segmento econômico

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab IV — patrimônio líquido — base de todos os agregados (lentes 1,2)

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab IX — taxas de desconto e juros — preço de aquisição

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab VI — DC sem risco: prazos e inadimplência

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab III — passivo e derivativos — identidade contábil Ativo−Passivo=PL

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab VII — aquisições, alienações, recompras e substituições

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_1 — número de cotistas por série (lente 6)

**2023-10**
- criadas (3): `CNPJ_FUNDO_CLASSE`, `ID_SUBCLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_2 — valor por série de cota — subordinação (lente 6)

**2023-10**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_3 — rentabilidade mensal por série

**2023-10**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_4 — captações, resgates e amortizações

**2023-10**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_5 — liquidez por prazo

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_6 — desempenho esperado × realizado por série

**2023-10**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_7 — garantias sobre os direitos creditórios

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`

## tab X_1_1 — cotistas por categoria de investidor

**2020-11**
- criadas (2): `CNPJ_FUNDO_CLASSE`, `TP_FUNDO_CLASSE`
- removidas (1): `CNPJ_FUNDO`
