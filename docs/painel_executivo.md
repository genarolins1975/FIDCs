# Entregável 5 — Especificação do Painel Executivo

Proposta de dashboards alimentados diretamente pelos artefatos de
`data/analytic/` (todos reproduzíveis pelos scripts). Cada indicador do painel
referencia o CSV/parquet de origem e o `claim_id` do livro de evidências —
trilha de evidência acessível em cada número.

## Páginas e componentes

### 1. Visão geral (home)
- Cartões: PL total (C001), PL líquido de circularidade (C004), nº de veículos
  (C002), nº de cotistas (C007), inadimplência (C016), subordinação (C015).
- Fonte: `serie_mercado_mensal.csv`, `subordinacao_agregada.csv`,
  `inadimplencia_aging_serie.csv`.

### 2. Evolução
- Série mensal 2013-2026 de PL nominal e real, nº de veículos, cotistas;
  marcação das quebras regulatórias (out/2023 vigência RCVM 175; 29/11/2024
  prazo de adaptação; 06/03/2026 RCVM 240).
- Captação líquida anual com nota metodológica (filtro de sanidade).
- Fonte: `serie_mercado_mensal.csv`, `captacao_liquida_anual.csv`.

### 3. Rankings
- Administradores, gestores, custodiantes, controladores, auditores — tabela
  padrão (posição, entidade, CNPJ, papel, valor, participação, Δ12/36/60m,
  nº de veículos), com unidade de análise e cobertura declaradas no rodapé.
- Fonte: `ranking_*.csv`.

### 4. Carteira e setores
- Treemap de segmentos (tab II); série de participação por segmento;
  aging de inadimplência (1-30/31-90/91-180/>180); distribuição SCR.
- Fonte: `carteira_segmentos.csv`, `inadimplencia_aging_serie.csv`,
  `scr_rating_operacoes.csv`.

### 5. Cedentes e originadores
- Ranking de cedentes identificados (CNPJ, razão social, CNAE, nº de veículos,
  exposição estimada com selo "estimativa-piso"); recorrência temporal.
- Fonte: `cedentes_ranking_nomes.csv`, `cedentes_recorrencia.csv`.

### 6. Risco e alertas
- Lista nominal de alertas (PL negativo, ativo>5×PL, inadimplência>30%,
  saltos>30%, alienações a cedentes); filtros por administrador/gestor.
- Fonte: `alertas.csv`, `saltos_pl_12m.csv`, `pl_saneamento_excluidos.csv`.

### 7. Fichas individuais
- Por veículo: série de PL, subordinação (X_2), inadimplência, cedentes
  declarados, prestadores, alertas — drill-down a partir de qualquer ranking.
- Fonte: parquets (`pl`, `ativo`, `series_cotas`, `cedentes`).

## Regras de exibição (herdadas do mandato)
- Todo número exibe tooltip com fonte, arquivo/campo, fórmula e data-base.
- Rankings declaram unidade de análise, universo, exclusões e cobertura.
- Valores estimados recebem selo visual distinto dos confirmados.
- Atualização: mensal, disparada pela publicação do informe na CVM
  (rodar scripts 01→06; diffs de manifesto identificam reapresentações).
