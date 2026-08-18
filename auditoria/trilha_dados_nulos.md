# Trilha de auditoria — nulos convertidos em zero

Varredura de `scripts/03_analytics.py`, `scripts/09_cda_detentores.py` e
`scripts/10_red_flags.py` atrás de `coalesce(x,0)`, `.fillna(0)` e equivalentes
que transformem **ausência de informação** em **zero** dentro de numeradores,
denominadores, razões ou limiares de indicadores.

Data da varredura: 2026-08-18. Corte de referência das medições: **2026-06-30**.
Todos os números abaixo foram medidos na base `data/duckdb/fidc.db`; nenhum é
estimado.

---

## Premissa que torna a distinção verificável

O informe mensal da CVM **distingue zero reportado de campo em branco**. No
arquivo `inf_mensal_fidc_tab_I_202606.csv` (4.328 linhas):

| Campo | Em branco | Preenchido | Observação |
|---|---:|---:|---|
| `TAB_I2H_VL_COTA_FIDC` | 0 | 4.328 | informantes escrevem explicitamente `0.00` quando não há |
| `TAB_I2I_VL_COTA_FIDC_NP` | **4.328 (100%)** | 0 | coluna existe no layout e nunca é preenchida |

Ou seja: quando o informante quer dizer zero, ele escreve `0.00`. Campo em
branco significa **não informado**. Logo, `coalesce(campo, 0)` não é uma
conveniência sintática — é uma afirmação sobre o mundo, e nem sempre verdadeira.

**Critério de classificação usado aqui**

- **LEGÍTIMO** — somar componentes de um agregado em que a ausência do
  componente significa que o componente não existe (ex.: um FIDC sem parcela
  mezanino), e o agregado é um numerador de soma, não uma razão.
- **ILEGÍTIMO** — ausência de *reporte* tratada como zero em (a) denominador,
  (b) razão/indicador, (c) limiar de classificação ou (d) numerador cuja
  leitura pública é "o valor é zero" em vez de "não sabemos".
- **LATENTE** — o padrão é ilegítimo por construção, mas o impacto medido no
  corte atual é nulo porque, hoje, não há nulos naquele campo. Vira erro real
  na primeira competência em que aparecer nulo, sem aviso.

---

## Quadro-síntese

| # | Arquivo | Linha | Expressão | Classe | Impacto medido |
|---|---|---:|---|---|---|
| 1 | 03_analytics.py | 139 | `SUM(COALESCE(TAB_I2H,0)+COALESCE(TAB_I2I,0))` | **ILEGÍTIMO** | subestima cotas de FIDC detidas; campo I2I 100% em branco desde 2024 |
| 2 | 03_analytics.py | 140 | `SUM(VL_PL) - SUM(COALESCE(...)+COALESCE(...))` | **ILEGÍTIMO** | superestima `pl_liquido_circular`; subestima circularidade |
| 3 | 03_analytics.py | 403 | `coalesce(pa.pr_tot,0)*coalesce(b.dc_a,0)` | LEGÍTIMO (numerador de cobertura) + LATENTE (`dc_a`) | R$ 392,34 bi de DC sem cedente contam como cobertura zero — leitura correta |
| 4 | 03_analytics.py | 404 | `SUM(coalesce(b.dc_a,0)+coalesce(b.dc_b,0)) dc_total` | **ILEGÍTIMO (denominador)** / LATENTE | 0 linhas com DC nulo no corte; superestimaria a cobertura se houvesse |
| 5 | 03_analytics.py | 471 | `3*GREATEST(coalesce(VL_PL,0),coalesce(pl_ant,0))+1e8` | **ILEGÍTIMO (limiar)** / LATENTE | 48.088 operações com PL faltante; 7 descartadas, todas genuinamente absurdas |
| 6 | 03_analytics.py | 250, 253 | `adm["pl"].clip(lower=0)` | ILEGÍTIMO (truncamento, não nulo) | PL negativo vira 0 no denominador do HHI |
| 7 | 09_cda_detentores.py | 51-52 | `.agg(vl_cotas_fidc=(..., "sum"))` (pandas ignora NaN) | LEGÍTIMO na prática | 0 valores não-numéricos em `VL_MERC_POS_FINAL` (81.893 linhas) |
| 8 | 09_cda_detentores.py | 53 | `(s == "S").sum()` sobre `EMISSOR_LIGADO` | **ILEGÍTIMO (desconhecido→não)** | 91 nulos no arquivo; 1 posição nas cotas de FIDC, R$ 0,00 bi |
| 9 | 10_red_flags.py | 45-46 | `coalesce(TAB_V_A,0)+coalesce(TAB_VI_A,0)` e idem inadimplência | **ILEGÍTIMO (numerador de razão)** / LATENTE | 0 dos 62 sinalizados em RF1 têm lado ausente no corte |
| 10 | 10_red_flags.py | 49 | `WHERE v.DT_COMPTC='...'` anula o `FULL JOIN` | Defeito de nulo correlato / LATENTE | 0 veículos só na tab VI no corte (4.328 em ambas) |
| 11 | 10_red_flags.py | 67 | `SUM(coalesce(RECOMPRA,0)+coalesce(SUBST,0))` | LEGÍTIMO | 0 componentes nulos em 47.997 linhas da janela 12m |
| 12 | 10_red_flags.py | 71 | `AVG(coalesce(DIRCRED_RISCO,0)+coalesce(SEM_RISCO,0)) dc_medio` | **ILEGÍTIMO (denominador)** | 2 de 47.997 linhas com componente nulo |
| 13 | 10_red_flags.py | 98 | `coalesce(s.v_sub/nullif(s.v_tot,0),0) < 0.05` | **ILEGÍTIMO (razão→classificação)** | 16 dos 64 sinalizados em RF3, R$ 11,36 bi de PL, entram por razão INDEFINIDA |
| 14 | 10_red_flags.py | 169 | `.fillna(0).astype(int)` em `n_flags` | LEGÍTIMO | conjunto completo por construção |
| 15 | 10_red_flags.py | 200 | `/ max(posf.VL_MERC_POS_FINAL.sum(), 1)` | **ILEGÍTIMO (guarda de denominador)** / LATENTE | soma > 0 no corte; devolveria 0% em vez de indefinido |
| — | 03_analytics.py | 434, 437 | `.../NULLIF(TAB_I2A_VL_DIRCRED_RISCO,0)` | **REFERÊNCIA CORRETA** | denominador zero produz NULO, e o alerta não dispara |

---

## Detalhamento dos casos ilegítimos

### 1-2 — `cotas_fidc_detidas` e `pl_liquido_circular` (03_analytics.py, L139-140)

```sql
SUM(COALESCE(a.TAB_I2H_VL_COTA_FIDC,0)+COALESCE(a.TAB_I2I_VL_COTA_FIDC_NP,0)) cotas_fidc_detidas,
SUM(p.VL_PL) - SUM(COALESCE(a.TAB_I2H_VL_COTA_FIDC,0)+COALESCE(a.TAB_I2I_VL_COTA_FIDC_NP,0)) pl_liquido_circular,
```

`TAB_I2I_VL_COTA_FIDC_NP` (cotas de FIDC **não-padronizado** em carteira) está
**em branco em 100% das linhas desde 2024** — 4.328 de 4.328 no corte. A coluna
não foi removida do layout: ela continua no cabeçalho do CSV, e simplesmente
ninguém preenche. Quando ainda era reportada, valia R$ 8,98 bi (2020), R$ 10,91 bi
(2021) e R$ 10,48 bi (2022) — mesma ordem de grandeza do campo I2H no período.

| Ano (dez) | `TAB_I2H` (R$ bi) | `TAB_I2I` (R$ bi) |
|---|---:|---:|
| 2020 | 11,35 | 8,98 |
| 2021 | 9,34 | 10,91 |
| 2022 | 13,73 | 10,48 |
| 2023 | 38,61 | 0,00 |
| 2024 | 97,11 | *(em branco)* |
| 2025 | 169,51 | *(em branco)* |

**Impacto:** `cotas_fidc_detidas` no corte soma R$ 161,64 bi contra um PL de
R$ 999,50 bi. A parcela não-padronizada está fora dessa conta e é declarada como
zero. Portanto:
- **subestima** a circularidade da indústria (cotas de FIDC dentro de FIDC);
- **superestima** `pl_liquido_circular`, que é justamente a medida "limpa" de
  tamanho do mercado apresentada no painel;
- a série 2013→2026 sofre **quebra metodológica silenciosa em 2023/2024**: a
  queda de I2I de R$ 10,48 bi para zero é ausência de reporte, e hoje é lida
  como desaparecimento real de posições.

**Correção recomendada:** somar apenas o que é informado e publicar a cobertura
ao lado; ou manter I2I fora da soma e **renomear** a coluna para
`cotas_fidc_padronizado_detidas`, deixando explícito que a parcela NP não é
observável a partir de 2024. Nunca apresentar a série como contínua sem a nota.

### 13 — Subordinação ausente vira subordinação zero (10_red_flags.py, L98)

```sql
AND a.COTST_INTERESSE='S' AND coalesce(s.v_sub/nullif(s.v_tot,0),0) < 0.05
```

O `nullif(s.v_tot,0)` está correto: protege a divisão. O `coalesce(...,0)`
externo **desfaz a proteção**: converte "índice de subordinação desconhecido"
em "índice de subordinação igual a zero", e zero satisfaz `< 0.05`. O veículo é
então incluído numa red flag cuja descrição publicada é
*"1-2 cotistas + interesse único + subordinação <5%"* — uma afirmação sobre a
estrutura de capital que os dados não sustentam.

**Impacto medido no corte:** dos 64 veículos sinalizados em RF3 (R$ 62,38 bi de
PL), **16 entram com a razão indefinida** (R$ 11,36 bi de PL, 18,2% do PL
sinalizado por RF3).

**Atenuante verificado, que não salva o padrão:** inspecionando esses 16, todos
têm linhas em `series_cotas` e todas as suas séries são do tipo `senior` — o
`v_sub` é nulo porque o filtro `TIPO_COTA IN ('subordinada','mezanino')` não
encontra nada, e a subordinação é de fato zero. No corte de junho/2026 o
resultado é acidentalmente correto. O universo de `TIPO_COTA` tem exatamente
três valores (`senior` 6.670, `subordinada` 3.362, `mezanino` 2.143), sem
categoria residual, então a classificação não está vazando.

Mas o mesmo `coalesce` também sinalizaria um veículo **sem nenhuma linha em
`series_cotas`** — ausência total de informação — com a mesma etiqueta. Hoje
isso não ocorre (0 dos 4.327 veículos do painel estão sem linha em
`series_cotas` no corte), e por isso o caso é ilegítimo-mas-inativo. A forma
correta separa as duas situações:

```sql
-- em vez de coalesce(razão, 0) < 0.05:
AND s.v_tot > 0 AND s.v_sub IS NOT NULL AND s.v_sub/s.v_tot < 0.05
-- e uma segunda categoria explícita: "sem série reportada" (não é red flag)
```

### 12 — `dc_medio` como denominador de RF2 (10_red_flags.py, L71)

```sql
AVG(coalesce(TAB_I2A_VL_DIRCRED_RISCO,0)+coalesce(TAB_I2B_VL_DIRCRED_SEM_RISCO,0)) dc_medio
...
AND n.roll_12m/nullif(d.dc_medio,0) > 0.15
```

Um componente nulo dentro de uma linha reduz o DC daquele mês, puxa a média
para baixo e **infla** `razao_rolagem` — que é o critério de disparo da red
flag. Direção do erro: **falsos positivos**. Impacto medido: 2 linhas em 47.997
na janela de 12 meses têm componente nulo; efeito material hoje é desprezível,
mas o sinal do erro é sistemático (nunca cria falso negativo, sempre falso
positivo).

### 9-10 — RF1 e o `FULL JOIN` que não é full (10_red_flags.py, L45-49)

```sql
coalesce(v.TAB_V_B_VL_DIRCRED_INAD,0)+coalesce(vi.TAB_VI_B_VL_DIRCRED_INAD,0) inad
...
FROM dc_risco_prazos v FULL JOIN dc_semrisco_prazos vi ON ...
WHERE v.DT_COMPTC='2026-06-30'
```

Dois problemas encadeados:

1. A inadimplência não reportada vira zero **no numerador de uma razão** cuja
   condição de disparo é `inad/dc < 0.001`. Um veículo que simplesmente não
   preenche a coluna de inadimplência é classificado como
   *"inadimplência ~zero"* — exatamente o padrão de fraude de lastro que a RF1
   quer capturar. Ausência de reporte viraria evidência de reporte perfeito.
2. O `WHERE v.DT_COMPTC = ...` filtra pela tabela do lado esquerdo, o que
   **descarta as linhas em que `v` é nulo** e reduz o `FULL JOIN` a um
   `LEFT JOIN`. Veículos que só reportam direitos creditórios sem risco (tab VI)
   sairiam da triagem sem aparecer em lugar nenhum.

**Impacto medido no corte: nulo nos dois pontos.** Os 62 veículos sinalizados
em RF1 (R$ 125,17 bi de PL) têm ambos os lados presentes, e tabs V e VI cobrem
os mesmos 4.328 veículos. É risco latente, não erro corrente — mas o código
depende de uma coincidência de cobertura que ninguém está monitorando.

### 5 — Limiar de descarte de captações (03_analytics.py, L471)

```sql
(c.TAB_X_VL_TOTAL > 3*GREATEST(coalesce(p2.VL_PL,0),coalesce(p2.pl_ant,0))+1e8) descartada
```

Com PL desconhecido, o limiar de plausibilidade colapsa para R$ 100 mi e a
operação é descartada por ser "grande demais" para um patrimônio que na verdade
não se sabe qual é.

**Impacto medido:** 48.088 operações têm PL ou PL anterior faltante; destas,
**7 são efetivamente descartadas**. Auditadas uma a uma, todas as 7 têm o PL
corrente presente (só o `pl_ant` falta, por ser o primeiro mês do veículo) e
valores absurdos por larga margem — a maior é R$ 725,0 **trilhões** de captação
num veículo de R$ 290 mi de PL. Nenhum descarte indevido no acervo atual.
Padrão latente: bastaria um veículo novo com captação inicial legítima acima de
R$ 100 mi para perdê-la silenciosamente.

### 8 — `EMISSOR_LIGADO` nulo lido como "não ligado" (09_cda_detentores.py, L53)

`(s == "S").sum()` classifica NaN como "não é emissor ligado". A leitura correta
de um flag de parte relacionada em branco é **desconhecido**, não **não**.
Direção do erro: **subestima** a exposição a partes relacionadas.
Impacto medido: 91 nulos em 81.893 linhas do arquivo CDA; dentro do recorte de
posições em cotas de FIDC, **1 posição, valor arredondado R$ 0,00 bi**, contra
R$ 76,80 bi declarados como ligados de um total de R$ 163,89 bi. Materialmente
irrelevante hoje; erro de semântica a corrigir.

### 6 — `clip(lower=0)` nos rankings (03_analytics.py, L250, L253)

Não é nulo→zero, é **negativo→zero**, mas contamina o mesmo tipo de indicador:
o PL negativo de um administrador/gestor é zerado antes de virar participação e
HHI. O denominador (soma das participações) cresce, e todas as participações
individuais ficam ligeiramente menores. Impacto de segunda ordem, listado por
completude e porque a correção é a mesma família: tratar o caso anômalo
explicitamente em vez de silenciá-lo com um valor neutro.

---

## Casos legítimos (registrados para não serem "corrigidos" por engano)

| Local | Por que é legítimo |
|---|---|
| 10_red_flags.py L67 — `coalesce(RECOMPRA,0)+coalesce(SUBST,0)` | soma de dois componentes de negócios do mês; ausência de recompra significa que não houve recompra. Verificado: 0 nulos em 47.997 linhas da janela. |
| 10_red_flags.py L169 — `.fillna(0)` em `n_flags` | o conjunto de veículos sinalizados é completo por construção; quem não está na lista tem, de fato, zero flags. |
| 03_analytics.py L403 (numerador) | métrica de **cobertura**: um veículo sem cedente identificado tem, corretamente, cobertura zero. R$ 392,34 bi de DC (55,3% dos R$ 709,74 bi) estão em 2.676 veículos que não reportam nenhum cedente, e a cobertura resultante de 29,4% é a leitura certa — desde que o indicador continue rotulado como cobertura, e nunca como concentração. |
| 09_cda_detentores.py L51-52 — soma pandas | `VL_MERC_POS_FINAL` não tem nenhum valor não-numérico em 81.893 linhas. |

---

## Padrão de referência adotado em `scripts/11_tab_viii_sacados.py`

A etapa 11 (concentração de sacados) foi escrita já sob a regra correta, e serve
de modelo para a correção das anteriores:

```sql
s.top1  / NULLIF(dc.dc_total, 0) AS top1_sobre_dc,
(dc.dc_total IS NULL OR dc.dc_total = 0) AS denominador_indisponivel,
```

- o denominador é `TAB_I2A + TAB_I2B` **em soma estrita** (nula se qualquer
  componente for nulo), nunca `coalesce(...,0)`;
- `NULLIF(...,0)` garante que denominador zero produza **NULO**, jamais zero;
- veículos sem denominador utilizável são **contados e publicados** (293 no
  corte, com tab VIII preenchida mas DC nulo ou zero) em vez de aparecerem como
  concentração zero e diluírem as estatísticas de mercado;
- a inconsistência entre fontes (soma dos 25 maiores maior que o DC informado na
  tab I) é **marcada** em `inconsistencia_viii_vs_i` (307 veículos), não
  corrigida nem descartada, e as estatísticas são publicadas nos dois recortes.

---

## Nulo por omissão de reporte: a tab VIII está encolhendo

Achado colateral da etapa 11, do mesmo gênero e com risco maior que qualquer
`coalesce` do código: a cobertura da tabela VIII **cai de forma monotônica**.

| Competência | Veículos no painel | Com tab VIII | % do DC coberto |
|---|---:|---:|---:|
| 2025-01-31 | 3.195 | 3.029 | 99,3% |
| 2025-06-30 | 3.592 | 3.356 | 98,6% |
| 2025-12-31 | 4.013 | 3.315 | 91,3% |
| 2026-03-31 | 4.154 | 3.189 | 87,6% |
| 2026-06-30 | 4.327 | 2.999 | **79,7%** |
| 2026-07-31 | 4.206 | 2.563 | **74,6%** |

O painel cresce e o número de informantes da tab VIII cai em termos absolutos
(3.559 em nov/2025 → 2.999 em jun/2026). Um agregado de mercado de concentração
de sacados construído por soma direta trataria os R$ 144,25 bi de direitos
creditórios sem tab VIII (20,3% do total) como **zero de exposição a sacados** —
o mesmo erro de categoria auditado acima, só que na fonte em vez do código. Por
isso a etapa 11 publica a cobertura junto com todo indicador e não emite
nenhum total de mercado de exposição por sacado.

## Recomendações, em ordem de materialidade

1. **Corrigir 03_analytics.py L139-140** e republicar a série de
   `pl_liquido_circular` com nota de quebra em 2023/2024. É o único caso desta
   varredura que altera um número de manchete do painel.
2. **Corrigir 10_red_flags.py L98**, separando "subordinação < 5%" de
   "subordinação não reportada". Hoje o resultado é acidentalmente correto; a
   etiqueta pública, não.
3. Trocar `coalesce(x,0)` por soma estrita nos denominadores das linhas 404 (03)
   e 71 (10), e substituir `max(sum,1)` por `NULLIF(sum,0)` na linha 200 (10).
4. Corrigir o `WHERE` do `FULL JOIN` em 10_red_flags.py L49
   (`WHERE coalesce(v.DT_COMPTC, vi.DT_COMPTC) = ...`).
5. Ler `EMISSOR_LIGADO` nulo como desconhecido e publicar a contagem.
6. Instituir teste de regressão: para cada indicador do painel, contar as linhas
   em que o denominador é nulo ou zero e falhar a construção se essa contagem
   mudar entre competências sem registro no log. Os casos LATENTES desta tabela
   viram erros reais sem nenhum sinal visível.
