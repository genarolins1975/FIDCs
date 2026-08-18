# Parecer do Auditor Espelho Independente — reconstrução do painel "Panorama FIDC Brasil"

**Objeto auditado:** `relatorio/painel_fidc_v2.html` (build de 18/08/2026 18:11 UTC,
md5 `96161b99…`), `data/analytic/painel_dados.json` (18:10 UTC, md5 `294ec348…`),
`BACKTEST_RED_FLAGS.md`, `docs/METODOLOGIA_RED_FLAGS.md`,
`docs/METODOLOGIA_RECUPERACAO_JUDICIAL.md`, `docs/LIMITACOES_E_RISCOS_JURIDICOS.md`,
`data/analytic/lente_*.csv`, `rf2_*.csv`, `rj_*.csv`, `backtest_*.csv`.

**Método:** recálculo independente a partir dos CSV brutos em `data/raw/extracted/`
(`latin-1`, `sep=';'`, `quoting=3`), com código próprio, **sem carregar nenhum
script auditado e sem tocar no DuckDB do projeto**; renderização do HTML em
Chromium headless (`/opt/pw-browsers/chromium-1194`, playwright-core) com extração
do texto efetivamente pintado na tela e comparação contra o JSON embutido.

**Congelamento:** os artefatos foram regenerados pelo agente construtor **durante**
a auditoria (JSON passou de 89 KB para 214 KB entre 18:02 e 18:10; o HTML mudou às
18:05 e às 18:11). Todos os achados abaixo foram **reconfirmados contra o build
corrente das 18:11** — nenhum foi corrigido no intervalo.

**Código desta auditoria:** `auditoria/espelho_reconstrucao_recalc.py` (recálculo)
e `auditoria/espelho_reconstrucao_probe.js` (sonda do navegador).

---

## (a) O que foi reproduzido, e com que código

### a.1 Painel canônico — reconstrução das regras de dedup do zero

Não confiei na view `painel_saneado`. Reimplementei as duas regras a partir do
bruto (`tab_IV_202606.csv`, `registro_classe.csv`, `registro_fundo.csv`):

```python
iv  = rd('inf_mensal_fidc_tab_IV_202606.csv')          # 4.328 linhas
iv['ord'] = (iv.TP_FUNDO_CLASSE != 'Classe').astype(int)
iv1 = iv.sort_values('ord').drop_duplicates(subset=['CNPJ'], keep='first')   # regra (i)
mapa = rc[['ID_Registro_Fundo','CNPJ_Classe']].merge(rf[['ID_Registro_Fundo','CNPJ_Fundo']],
                                                     on='ID_Registro_Fundo')
fundos_com_classe = set(mapa[mapa.cc.isin(set(iv.CNPJ))].cf)
pan = iv1[~((iv1.TP_FUNDO_CLASSE=='Fundo') & (iv1.CNPJ.isin(fundos_com_classe)))]  # regra (ii)
```

Resultado: regra (i) não remove nada (**0 CNPJ duplicado** na competência); regra
(ii) remove **exatamente 1** fundo do regime anterior cuja classe já informa.
Painel = **4.327** veículos, PL = **R$ 999.497.428.095,20**. Bate com o publicado
até o último centavo.

### a.2 Dezenove indicadores recalculados (tolerância exigida: 0,1 %)

| # | Indicador | Meu valor | Publicado | Dif. |
|---|---|---:|---:|---:|
| 1 | `pl_total` | 999.497.428.095,20 | 999.497.428.095,20 | **0,000000 %** |
| 2 | `n_veiculos` | 4.327 | 4.327 | **0,000000 %** |
| 3 | `pl_liquido` | 837.854.733.602,90 | 837.854.733.602,90 | **0,000000 %** |
| 4 | `circularidade` | 161.642.694.492,30 | 161.642.694.492,30 | **0,000000 %** |
| 5 | `dc_total` | 709.739.272.476,91 | 709.739.272.476,91 | **0,000000 %** |
| 6 | `dc_sem_risco` | 262.130.153.977,35 | 262.130.153.977,35 | **0,000000 %** |
| 7 | `inadimplencia` | 0,09130353506 | 0,09130353506 | **0,000000 %** |
| 8 | `atraso_180` | 0,05002405581 | 0,05002405581 | **0,000000 %** |
| 9 | `identidade_contabil` | 0 violações / 4.327 avaliáveis | 0 | **exato** |
| 10 | `sacado_cobertura_dc` | 0,7967534353 | 0,7967534353 | **0,000000 %** |
| 11 | `sacado_mediana_top1` | 0,17904240683 | 0,17904240683 | **0,000000 %** |
| 12 | `sacado_n_top1_50` | 877 | 877 | **exato** |
| 13 | `posicoes_cotistas` | 461.515 | 461.515 | **exato** |
| 14 | `serie_senior` | 685.104.188.565,24 | idem | **0,000000 %** |
| 15 | `serie_mezanino` | 73.832.965.811,41 | idem | **0,000000 %** |
| 16 | `serie_subordinada` | 241.002.467.750,34 | idem | **0,000000 %** |
| 17 | `subordinacao` | 0,31485444380 | 0,31485444380 | **0,000000 %** |
| 18 | `jul_ausentes` / `jul_pl_ausente` / `jul_same_store` | 232 / 73.324.035.329,37 / +2,0130 % | idem | **0,000000 %** |
| 19 | `series_abaixo_esperado` / `veiculos_com_garantia` | 979 / 28 | idem | **exato** |
| — | **`provisionamento`** | **9,116866** pela fórmula publicada | **0,978886** | **+831 %** ✗ |

Trechos do recálculo (íntegra em `espelho_reconstrucao_recalc.py`):

```python
# 7. inadimplência — tabs V e VI, restritas ao painel canônico
inad = num(v.TAB_V_B_VL_DIRCRED_INAD).sum() + num(vi.TAB_VI_B_VL_DIRCRED_INAD).sum()
dc   = num(v.TAB_V_A_VL_DIRCRED_PRAZO).sum() + num(vi.TAB_VI_A_VL_DIRCRED_PRAZO).sum()
inad/dc  # 0.09130353506301489

# 9. identidade contábil — Ativo (tab I) − Passivo (tab III) − PL (tab IV)
(np.abs(av.AT - av.PA - av.VL_PL) > 0.01*np.maximum(np.abs(av.VL_PL),1)).sum()   # 0

# 10. cobertura da tab VIII — DC dos veículos que entregam a tabela ÷ DC total
dcs[dcs.index.isin(set(t8p.CNPJ) & P)].sum() / dcs[dcs.index.isin(P)].sum()      # 0.7967534

# 14-16. estrutura de capital — X_2, com Mezanino testado ANTES de Subordinada
tipo = np.where(s.str.contains('Mezanino'),'mezanino',
        np.where(s.str.contains('Subordinada'),'subordinada',
        np.where(s.str.contains('Senior'),'senior','outro')))
```

### a.3 Testes estruturais executados

* **Dupla contagem (teste 4).** (a) PL recalculado do bruto = publicado, exato.
  (b) Subclasses **não podem** entrar em nenhuma soma: `registro_subclasse.csv`
  não possui coluna de CNPJ (chave é `ID_Subclasse`), e em `tab_X_1` há **0 pares
  (CNPJ, série) com mais de uma linha** — não há série contada duas vezes por
  subclasse. (c) Lente 1 soma **99,9937 %** do PL de mercado (2 veículos, R$ 62,5 mi,
  sem gestor identificado) e Lente 2 soma **100,0000 %** — **nenhuma excede o PL**.
  Soma das séries (X_2) = R$ 999.939.622.126,98 = **100,044 %** do PL.
* **Ausência nunca vira zero (teste 3).** Varredura de `coalesce`/`fillna` nos
  scripts 11, 11b, 13, 14, 16, 18 (resultado no item (b.4)). Verificação empírica:
  **os arquivos da CVM não contêm um único nulo** nas tabs I, V, VI, X_2 —
  nem em jun/26, nem em jun/25, jun/24, jan/21 ou jun/19. Os 1.135 veículos com
  `valor = 0` na lente 3 têm **os dois campos reportados como zero** na origem;
  nenhum zero foi fabricado. A ausência neste conjunto se manifesta como **linha
  faltante**, e aí o tratamento está correto (tab VIII: 2.999 de 4.327 veículos,
  os demais ficam fora, não entram como zero).
* **Não classificável nunca vira baixo risco (teste 3c).** Confirmado em
  `rf2_score_veiculo.csv`: 1.099 veículos com `cobertura_dados_pct < 50` recebem
  `não classificável` e **nenhum** aparece em `atenção baixa` / `sem sinal`.
  O problema é o **oposto** e está no item (b.6).
* **Navegador (teste 8).** 6 abas alternam corretamente (uma e só uma
  `section[role=tabpanel]` visível por vez); deep-link `#t4` funciona; gaveta de
  evidências abre com fórmula, fonte, campo, data-base, extração, status, confiança,
  cobertura, observação e claim; busca filtra (`btg` → 3 de 25 na lente 1; `itau` →
  2 de 25 nos detentores; `paranapanema` → 1 de 21 na tabela de RJ);
  "copiar CSV" grava o CSV completo no clipboard; **zero erro de console e zero
  pageerror** em ambos os temas; tema escuro funciona e é legível (contraste ≥ 4,2
  em todos os 15 seletores medidos).

---

## (b) Divergências, com materialidade

### b.1 — [CRÍTICO] Dez linhas da lente 5 são renderizadas **100× menores** que o dado

`cellFmt()` no HTML **adivinha a escala** de qualquer coluna cujo nome contenha
`pct`/`participacao`/`share`/`cobertura`:

```js
if(c.includes('pct')||c.includes('participacao')||c.includes('share')||c.includes('cobertura')) {
  return (Math.abs(v)<=1.5 ? nf.format(+(v*100).toFixed(1)) : nf.format(+v.toFixed(1)))+'%';
}
```

`pct_maior_sacado` é **fração** (mediana 0,179 = 17,9 %). As 10 primeiras linhas da
tabela publicada têm fração > 1,5 e escapam da multiplicação. O que aparece na tela:

| Linha | Renderizado | Valor real no JSON |
|---|---:|---:|
| G VALUE FIDC NP | **144,1 %** | 14.410,0 % |
| CITY-02 FIDC NP | **13,3 %** | 1.326,9 % |
| SAN MARINO | **8,7 %** | 872,4 % |
| … | … | … |
| ARAGUAIA (linha 10) | **1,6 %** | 156,1 % |
| MERCADO CRÉDITO (linha 11) | **129 %** | 129,0 % |

**Materialidade:** a tabela é ordenada decrescente e exibe `144,1 % → 13,3 % → … →
1,6 % → 129 % → 120,1 %`. Qualquer leitor vê que está quebrada; quem não vê lê um
fundo com concentração de 1.327 % como se fosse 13 %. Atinge as três colunas
(`pct_maior_sacado`, `pct_top5`, `pct_top10`) e **nomeia os fundos**.

### b.2 — [CRÍTICO] Três sinais do catálogo com cobertura renderizada **100× maior**

Mesmo heurístico, sinal invertido: `cobertura_universo_pct` está em **pontos
percentuais**; quando o valor é ≤ 1,5 ele é multiplicado por 100.

| Sinal | Cobertura real | Renderizado |
|---|---:|---:|
| JR-01 — Créditos em ação judicial de cobrança relevantes | **0,9 %** | **90 %** |
| PO-04 — Deságio anômalo em alienação a terceiros | **0,69 %** | **69 %** |

**Materialidade:** dois sinais rarríssimos aparecem no catálogo público como se
fossem quase universais. Inverte a leitura de relevância de dois dos 46 sinais.

### b.3 — [CRÍTICO] A gaveta de evidências do indicador `provisionamento` publica uma fórmula que **não reproduz o número**

Publicado: `valor = 0,978886` (mosaico "Atraso coberto por provisão" = **97,9 %**),
`formula = "(TAB_I2A11 + TAB_I2B11) ÷ parcelas inadimplentes"`, `campo = "tab I"`.

Recalculado literalmente da fórmula publicada:

```
prov  = Σ(TAB_I2A11 + TAB_I2B11)          = 63.311.460.294,64
parc  = Σ(TAB_I2A21 + TAB_I2B21)          =  6.944.432.669,20   → razão = 9,116866  (911,7 %)
inad  = Σ(TAB_V_B + TAB_VI_B)             = 64.677.023.776,91   → razão = 0,978886  (97,9 %)  ← é este
```

O denominador **não** é "parcelas inadimplentes" (tab I) e sim os direitos
creditórios inadimplentes por aging (**tabs V e VI**). `formula` **e** `campo` estão
errados. Um auditor que siga a evidência publicada obtém **911,7 % em vez de 97,9 %**.

**Materialidade: máxima.** A única promessa que diferencia este painel — *"Todo
número é clicável e abre a evidência que o sustenta"* — falha exatamente onde é
verificável, num indicador de capa da tela 2. Um erro de fórmula na gaveta é pior
que um erro no número, porque destrói a confiança em todos os outros 35.

Defeito da mesma classe, menor: `rf_atencao_alta` declara `"score ≥ p99 da
distribuição do próprio mercado"`, mas o corte é o p99 **dos classificáveis com ao
menos um disparo** (n = 1.301), não do mercado (n = 4.327). Pelo p99 do mercado
seriam 44 veículos, não 14. E o rótulo de `inadimplencia` diz "parcelas vencidas /
DC" quando o numerador é `TAB_V_B/TAB_VI_B` (DC inadimplente), não `I2A21/I2B21`
(parcelas) — a mesma confusão conceitual do item anterior.

### b.4 — "Ausência nunca vira zero": a regra vale nos denominadores, **não no backtest**

Varredura completa dos scripts:

* **Scripts 11 e 11b:** zero ocorrências de `coalesce`/`fillna`. Limpo.
* **Script 14 (lentes):** `COALESCE(...,0)` aparece **só em numeradores**
  (`dc_tot = COALESCE(I2A,0)+COALESCE(I2B,0)`); todo denominador é protegido por
  `CASE WHEN dc_tot > 0 THEN … END` → nulo, nunca zero. **Conforme.**
* **Script 13 (46 sinais):** todas as razões usam
  `np.where(denominador > 0, num/den, np.nan)`. Os `fillna(0)` que existem (linhas
  187, 214, 222) são somas de componentes reportados, e os dois que apareceriam em
  valor de sinal (ES-03 linha 532, PO-05 linha 1328) são **inalcançáveis**: a
  cláusula `avaliavel` exige `d.v_sub.notna()` e `d.pr_max.notna()`. **Conforme.**
* **Script 18 (backtest):** **NÃO conforme.**
  ```sql
  -- S3: subordinação baixa
  CASE WHEN s.v_tot IS NULL OR s.v_tot <= 0 THEN NULL
       WHEN coalesce(s.v_sub,0)/s.v_tot < 0.05 THEN 1 ELSE 0 END AS S3
  ```
  Veículo que informa séries mas **não tem linha de subordinada/mezanino** recebe
  `v_sub = NULL → 0` e **dispara S3**. O próprio `BACKTEST_RED_FLAGS.md` declara,
  na seção "Desenho": *"Ausência de dado ⇒ não avaliável, jamais 'não disparou'"*, e
  `METODOLOGIA_RED_FLAGS.md §1.1` intitula-se *"Ausente nunca vira zero"*.

  **Materialidade:** S3 é um dos **dois sinais que a conclusão do backtest manda
  manter** (lift 2,59; 125 disparos em 150 positivos). Economicamente a imputação
  até é defensável — um fundo só-sênior tem de fato 0 % de subordinação — mas
  então é uma **exceção que precisa ser declarada**, não um `coalesce` silencioso
  contra a regra que o documento anuncia duas páginas antes.

Registre-se ainda que a convenção `z = lambda c: d[c].fillna(0)` ("soma de
componentes reportados", script 13 linha 187) existe **só como comentário de
código** — não está em `METODOLOGIA_RED_FLAGS.md`.

### b.5 — Contradição dura entre a tela 3 e a tela 5

`lentes_catalogo.csv` (gerado 17:40) publica na tela 3:

> **Lente 9 — Exposição em recuperação judicial — n_entidades: 0**

A tela 5, do mesmo painel, publica `rj_casos = 21`, `rj_vinculos = 107` e
`rj_exposicao = R$ 4,6 bi` (arquivos `rj_*.csv` gerados 18:01). `lente_9_recuperacao_judicial.csv`
está **vazio** (só cabeçalho). O script 14 nunca foi reexecutado depois do 12b.

**Causa raiz:** não existe orquestrador com ordem de dependência; o README lista os
scripts em sequência linear, mas nada impede publicar com um estágio a montante
desatualizado. Sintomas irmãos do mesmo problema, todos visíveis no build corrente:

* Tela 6 exibe o chip **`T13 arquivos-fonte existentes 34/34`** e, três linhas
  abaixo, **"Arquivos-fonte no manifesto: 37"**. `manifesto_fontes.csv` tem 37 linhas
  — o teste está velho.
* Tela 6 exibe **`T15 … dif 0,04 % — "difere por veículos sem X_2"`**. Verifiquei:
  **todos os 4.327 veículos têm tab X_2** e nenhum tem quantidade ou valor de cota
  nulo. A explicação publicada para a diferença de reconciliação é **factualmente
  falsa**.
* Às 18:05 o HTML publicado estava dessincronizado do `painel_dados.json` das 18:10
  (tabela `fichas` no JSON, ausente no HTML). Nada no artefato permite detectar isso:
  `hash_manifesto` cobre as **fontes**, não o JSON compilado.
* README declara "Extração: 17/08/2026"; o painel declara 18/08/2026.

### b.6 — A tabela-título da tela de supervisão não mostra um único veículo classificado

`rf_score` é ordenada por `score_risco` desc. As 25 linhas publicadas são
**100 % "não classificável"**, **20 delas com PL = R$ 0** e 4 com PL negativo
(FC2–FC5, entre −R$ 0,3 mi e −R$ 0,65 mi). Cobertura de dados das 25: entre
**10,87 % e 21,74 %**.

Nenhum dos **14 veículos em "atenção alta"** — que existem, somam R$ 11,9 bi de PL e
incluem nomes com cobertura de 63 % a 87 % — aparece na tela.

**Materialidade:** o *warnbox* logo acima diz *"Cobertura insuficiente gera
classificação 'não classificável' — nunca 'baixo risco'"*. Verdade. Mas o painel
então **põe esses mesmos veículos no topo de uma tabela intitulada "Sinais de
atenção por veículo"**, sob um cartão que anuncia "14 veículos na faixa de atenção
alta". A tela ensina a regra certa e faz exatamente o contrário: transforma
*falta de informação* em *primeiro lugar do ranking de risco*, que é a leitura que
o documento de riscos jurídicos (`§ "Um ranking de risco é lido pelo público como
ranking de suspeitos"`) identifica como o pior desfecho possível. Além disso é
economicamente inútil: 20 dos 25 têm PL zero.

### b.7 — CNPJ renderizado errado na tela judicial

Os CNPJs da tabela `rj` estão no JSON como **float** (`60398369000479.0`) e caem no
formatador numérico genérico. Na tela:

| Razão social | Renderizado | CNPJ correto |
|---|---|---|
| PARANAPANEMA S.A. | `60.398.369.000.479` | 60.398.369/0004-79 |
| NASSAU ADMIN. E PARTICIPAÇÕES | `8.662.033.000.109` | **0**8.662.033/0001-09 |

O zero à esquerda foi **destruído** pela coerção numérica, e a máscara de milhar
finge ser um identificador. **Materialidade:** é a tela que associa empresas
nominadas a recuperação judicial e falência; publicar identificador malformado
(ou truncado) é a forma mais direta de atingir a **empresa errada** e o exato risco
que `docs/LIMITACOES_E_RISCOS_JURIDICOS.md` se propõe a evitar.

### b.8 — Linguagem e risco jurídico (teste 5)

O tratamento é, no geral, **acima da média do gênero**: cada caso traz
`status_processual` e `nivel_evidencia`; "investigação", "acusação", "condenação de
1ª instância" e "decisão definitiva" são distinguidos; o caso 25 (Operação Carbono
Oculto) chega a escrever *"Os valores e a caracterizacao do esquema provem de fontes
jornalisticas, nao de peca oficial consultada. Este registro NAO deve ser usado para
afirmar irregularidade do fundo."* Não encontrei **nenhuma** afirmação de fraude sem
decisão, nem red flag apresentado como prova, nem processo em curso apresentado como
condenação.

O que encontrei são **violações do próprio checklist** de `docs/LIMITACOES_E_RISCOS_JURIDICOS.md § 9`:

1. **Item "Toda condenação de 1ª instância vem acompanhada de 'cabe recurso ao CRSFN
   com efeito suspensivo'"** — descumprido em **8 dos 18** casos com status
   `condenacao`, todos com entidade nominada:
   `Trendbank S.A. Banco de Fomento`, `Banco Santander (Brasil) S.A.`,
   `Banco Finaxis S.A.`, `Planner Corretora de Valores S.A.`,
   `Oliveira Trust DTVM S.A.`, `Banco Bradesco S.A.`,
   `KPMG Auditores Independentes` e o controlador da Trendbank — todos publicados
   como `"condenacao (1a instancia administrativa)"`, seco, sem a ressalva de
   recurso com efeito suspensivo que o próprio manual torna obrigatória.
   *Materialidade: alta.* São instituições de grande porte apresentadas em tela
   pública como condenadas, sem informar que a decisão não é definitiva.
2. **Item "Toda menção a processo tem identificador, autoridade, data, status e
   URL"** — a tabela `casos` publicada no painel **descarta a coluna `fonte_url`**
   (existe em `casos_regulatorios.csv`, some em `16_painel_dados.py`). A tabela `rj`,
   de risco menor, publica a URL; a de casos sancionadores, de risco maior, não.
3. **Item "Nenhuma das cinco palavras de revisão obrigatória (fraude, lavagem,
   esquema, rombo, fantasma) aparece fora de citação de peça oficial devidamente
   atribuída"** — no caso 25 lê-se *"empresas apontadas como ligadas a esquema de
   lavagem de dinheiro"*, atribuído a *"Reportagens"*, não a peça oficial. Pela
   regra da própria linha 34 do manual ("se não houver ato de autoridade sobre o
   fundo: **não publicar**"), nomear `FIDC Gold Style` neste contexto é, no mínimo,
   limítrofe.
4. **Pessoa natural.** Formalmente cumprido — cinco pessoas naturais aparecem como
   "(pessoa natural - nome nao reproduzido no painel publico)". Materialmente,
   **a pseudonimização não funciona**: o registro traz cargo + gestora nominada +
   número do PAS + valor exato da multa (R$ 244.979.397,58) + a frase *"Nome integral
   consta da decisao publica da CVM referenciada na fonte"*. A pessoa é
   univocamente reidentificável em um clique. O checklist afirma um resultado que o
   conteúdo não entrega.
5. **Legado não removido.** `relatorio/painel_executivo.html` (painel v1, ainda no
   repositório) contém *"todos os casos de fraude documentados (Silverado, Cruzeiro
   do Sul, Reag)"* — três entidades nominadas em contexto de fraude, sem status
   processual. Se o repositório for publicado, é este arquivo, e não o v2, o de
   maior exposição.

### b.9 — Backtest: as conclusões vão além do que os números sustentam

Reproduzi `backtest_resumo.csv` linha a linha contra o markdown: **todas as seis
taxas, os seis lifts, as coberturas e o n = 151/453 conferem**, e as 6.699
observações veículo-mês existem. A descrição é fiel aos números. As objeções são de
inferência, não de aritmética.

**b.9.1 — Descartar S6 e manter S1 é uma decisão que os dados não distinguem.**
Calculei o teste exato de Fisher bicaudal que o documento não apresenta:

| Sinal | Positivos | Controles | Lift | **p (Fisher)** | Decisão do documento |
|---|---|---|---:|---:|---|
| S5 | 144/151 | 96/453 | 4,50 | **< 0,000001** | manter |
| S3 | 125/150 | 144/447 | 2,59 | **< 0,000001** | manter |
| S2 | 0/132 | 24/345 | 0,00 | **0,00060** | descartar |
| **S6** | 18/59 | 98/219 | 0,68 | **0,05399** | **descartar** |
| **S1** | 16/58 | 30/193 | 1,77 | **0,05174** | **manter** |
| S4 | 63/149 | 155/432 | 1,18 | 0,17063 | não discrimina |

S1 (p = 0,0517) e S6 (p = 0,0540) têm força estatística **indistinguível** e ambos
ficam **fora** do nível de 5 %. O documento mantém um e descarta o outro. A
justificativa dada para S1 é externa ao backtest (a defesa no PAS CVM
19957.006858/2019-25) — o que é legítimo como argumento, mas então a decisão sobre
S1 **não é uma conclusão do backtest**, e o texto a apresenta como se fosse
("Autoriza três coisas: (i) descartar S6 e S2…; (ii) manter S5, S3 e S1…").

**b.9.2 — Nenhum p-valor ou intervalo é publicado**, e a justificativa
("intervalos de confiança seriam largos a ponto de inúteis") é uma racionalização:
um intervalo largo **é** informação, e no caso de S5/S3 os intervalos seriam
estreitíssimos — publicá-los fortaleceria as duas conclusões que o documento
efetivamente sustenta e enfraqueceria as duas que ele não sustenta.

**b.9.3 — "Antecedência mediana" é publicada só para os positivos.** A coluna existe
também para os controles e é **maior em 5 dos 6 sinais** (S5: 11 meses nos controles
contra 4 nos positivos; S1: 10 contra 2; S3: 3 contra 0). Uma coluna intitulada
"Antecedência mediana" ao lado de uma coluna "Lift" é lida como *lead time*
preditivo; publicar só a metade favorável, num documento cuja tese central é a
honestidade metodológica, é a inconsistência mais séria do arquivo.

**b.9.4 — O falso negativo é tratado com honestidade parcial.** O texto afirma:
*"Três veículos vinculados. **Nenhum sinal disparou em nenhum mês da janela.**"*
No CSV, o grupo positivo de CR024 tem linha para **S2, S3, S4 e S5** — e **nenhuma
linha para S1 e S6**, porque nesses dois a cobertura foi zero. Ou seja: 4 sinais
foram avaliados e não dispararam; **2 sinais não eram avaliáveis**. O próprio
desenho, meia página acima, proíbe essa conflação ("Ausência de dado ⇒ não
avaliável, jamais 'não disparou'"). E S2 tinha n = 2, não 3.
*Materialidade: média.* A seção existe justamente para ser o teste de honestidade do
documento; ela precisa ser a mais precisa do arquivo, e não é.

**b.9.5 — Grupo de controle contaminado.** 56 pares (CNPJ, competência) aparecem
duas vezes em `backtest_detalhe.csv`: **2 veículos que são positivos em CR023
servem de controle em CR024** — 2 de 30 controles (6,7 %) daquele evento são
veículos com evento conhecido.

### b.10 — Divergências menores, registradas para completude

* Lente 1 declara `cobertura_pct = 100,0`; a cobertura real é **99,9937 %** (2 de
  4.327 veículos sem gestor identificado, R$ 62,5 mi). Na **mesma tela**, a lente 8
  reporta `Gestor · cobertura 0,99994` para a mesma grandeza. Duas coberturas
  diferentes para a mesma coisa, a dois cliques uma da outra.
* **Cobertura da lente 5 tem dois valores publicados e nenhum é o mais informativo.**
  Tela 3: `69,3 %` (= 2.999 veículos ÷ 4.327). Tela 4: `79,7 %` (= DC dos veículos
  com tab VIII ÷ DC total). Ambos corretos e ambos rotulados "cobertura", sem
  reconciliação. O número que o leitor procura — **quanto do estoque de DC as
  posições listadas efetivamente explicam** — é **45,3 %** (Σ tab VIII ÷ DC total,
  recalculado por mim) e não é publicado em lugar nenhum. Ler "79,7 % de cobertura"
  como "vejo 79,7 % da exposição a devedores" é o erro que o rótulo convida a cometer.
* **166 veículos com `pct_maior_sacado > 100 %`** (máximo: 2,18 × 10⁹, isto é, o
  maior devedor vale 218 bilhões de vezes a carteira declarada) — inconsistência
  interna entre tab VIII e tab I que domina o topo do ranking publicado, **sem uma
  linha de ressalva** na nota da tabela.
* `TAB_X_NR_COTST` soma **461.515** na tab X_1 e **461.521** na tab X_1_1: 6
  posições de diferença na própria fonte, não reconciliadas nem sinalizadas.
* **"Todo número é clicável e abre a evidência que o sustenta"** (subtítulo da capa)
  é falso: medi **37 links de evidência** contra **486 células numéricas de tabela
  sem gaveta** — 93 % dos números da página não são clicáveis.
* **Teclado quebrado na gaveta.** `Enter` sobre um link de evidência focado
  (`document.activeElement === a` confirmado) **não abre a gaveta** no Chromium; o
  `keydown` chega ao elemento e `openEv()` funciona quando chamado direto, mas o
  `<a role="button">` sem `href` provoca dupla invocação com o handler de clique e o
  `showModal()` não sobrevive. Único caminho de teclado para a evidência: inexistente.
* **Contraste WCAG AA (tema claro):** `footer` = **2,85** e `.tile .src` = **3,15**
  (mínimo 4,5 para texto pequeno). No tema escuro tudo passa (mínimo 4,2).
* Coerência dos cartões × tabelas, no que foi possível checar, está **correta**:
  sênior 68,5 % + mezanino 7,4 % + subordinada 24,1 % = 100 % da barra, e a soma
  das três séries reconcilia com o PL em +0,044 %.

---

## (c) Notas por dimensão do padrão

| # | Dimensão | Nota |
|---|---|:---:|
| 1 | Completude | **8** |
| 2 | Precisão | **5** |
| 3 | Rastreabilidade | **5** |
| 4 | Consistência conceitual | **6** |
| 5 | Reprodutibilidade | **7** |
| 6 | Tratamento de duplicidades | **9** |
| 7 | Resolução de entidades | **6** |
| 8 | Tratamento das limitações | **7** |
| 9 | Clareza | **6** |
| 10 | Utilidade econômica | **6** |

**Média: 6,5.**

Registre-se, porque é o achado mais importante deste parecer: a **camada analítica é
excelente**. Reproduzi 18 indicadores a partir dos CSV brutos com código próprio e
**todos bateram até a última casa decimal**; as regras de dedup, refeitas do zero,
devolvem exatamente 4.327 veículos e R$ 999,50 bi; nenhuma soma indevida de
subclasse; nenhum zero fabricado. **Tudo o que está reprovado abaixo está na camada
de apresentação e de rotulagem — não no cálculo.**

---

## (d) Para cada nota abaixo de 9

### 1. Completude — 8

* **Problema.** A lente 9 é publicada com 0 entidades na tela 3 enquanto a tela 5
  publica 21 casos e 107 vínculos; a tabela de casos regulatórios perde a coluna
  `fonte_url` na publicação; a cobertura **em valor** da tab VIII (45,3 %) não é
  publicada em lugar nenhum.
* **Materialidade.** Média. Não há número errado, há informação existente que não
  chega à tela — e uma delas produz contradição visível entre duas abas.
* **Evidência.** `data/analytic/lente_9_recuperacao_judicial.csv` (72 bytes, só
  cabeçalho, 17:40) × `rj_casos_confirmados.csv` (19 KB, 21 linhas, 18:01);
  `casos_regulatorios.csv` tem `fonte_url`, `painel_dados.json → tabelas.casos.colunas` não;
  Σ tab VIII ÷ DC = 0,4531.
* **Correção necessária.** Reexecutar o script 14 depois do 12b (ou fazer a lente 9
  ler `rj_matches_cedentes.csv`); acrescentar `fonte_url` às colunas publicadas de
  `casos`; publicar `sacado_cobertura_valor = 0,453` ao lado da cobertura por veículo.
* **Teste de validação.** Assertar em CI que
  `lentes_catalogo.loc[9,'n_entidades'] == len(rj_casos_confirmados)`; assertar
  `'fonte_url' in painel_dados['tabelas']['casos']['colunas']`.

### 2. Precisão — 5

* **Problema.** O renderizador adivinha a escala de colunas percentuais
  (`Math.abs(v)<=1.5 ? v*100 : v`), produzindo erro de 100× em 10 linhas da lente 5
  (para menos) e em 3 sinais do catálogo (para mais). Ver b.1 e b.2.
* **Materialidade.** **Crítica.** São números nominados, na tela, errados por duas
  ordens de grandeza, numa tabela ordenada que fica visivelmente incoerente
  (`1,6 %` acima de `129 %`). Nega o critério "nenhum número simulado" na prática:
  o número exibido não corresponde ao dado.
* **Evidência.** `painel_fidc_v2.html` linha 345; comparação renderizado × JSON na
  tabela do item b.1; `lente_5_sacados_concentracao.csv` com mediana 0,179 (fração).
* **Correção necessária.** Eliminar a heurística. Cada coluna deve declarar sua
  unidade no JSON (`{"col":"pct_maior_sacado","unidade":"fracao"}` /
  `{"col":"cobertura_universo_pct","unidade":"pp"}`) e `cellFmt` deve consumir a
  declaração, sem inferir nada de nome de coluna nem de magnitude.
* **Teste de validação.** Para toda coluna percentual, assertar em teste de
  navegador que `parse(texto_renderizado) == valor_esperado(json, unidade)` com
  tolerância de 0,05 pp, sobre **todas** as linhas de **todas** as tabelas — e
  incluir deliberadamente um caso com fração > 1,5 e um caso com pp < 1,5.

### 3. Rastreabilidade — 5

* **Problema.** A fórmula publicada de `provisionamento` não reproduz o valor
  publicado (911,7 % contra 97,9 %) e o `campo` aponta a tabela errada; a fórmula de
  `rf_atencao_alta` descreve a população errada; o rótulo de `inadimplencia` nomeia
  o campo errado; 93 % dos números da página não têm gaveta apesar do subtítulo
  prometer que todos têm; o caminho de teclado até a gaveta está quebrado.
* **Materialidade.** **Crítica.** A gaveta de evidências é a única coisa que este
  painel oferece e que os concorrentes não oferecem. Errada, vale menos que ausente:
  induz o auditor a um número 9,3× errado com aparência de verificação.
* **Evidência.** b.3, com o recálculo dos três denominadores candidatos;
  `scripts/13_red_flags_v2.py:1807-1809` (base = `cls & score>0`, n = 1.301);
  sonda do navegador: 37 `a.ev` × 486 `td.num`; `probe5.js` (Enter → `open: false`,
  chamada direta → `open: true`).
* **Correção necessária.** (i) Corrigir `formula` para
  `"(TAB_I2A11 + TAB_I2B11) ÷ (TAB_V_B + TAB_VI_B)"` e `campo` para `"tabs I, V e VI"`;
  (ii) corrigir a fórmula de `rf_atencao_alta` para
  `"score ≥ p99 entre classificáveis com ≥ 1 disparo (n=1.301)"`; (iii) corrigir o
  rótulo de `inadimplencia` para "DC inadimplente / DC"; (iv) ou tornar as células
  de tabela clicáveis, ou reescrever o subtítulo para "todo indicador de destaque é
  clicável"; (v) trocar `<a class="ev" role="button">` por `<button class="ev">` e
  guardar `if(!dlg.open) dlg.showModal()`.
* **Teste de validação.** Um teste que, para **cada** indicador do JSON, execute a
  `formula` publicada contra os CSV brutos e compare com `valor` (tolerância 0,1 %) —
  exatamente o que fiz à mão neste parecer, automatizado; e um teste de navegador que
  focalize cada `.ev` e verifique `dialog.open === true` após `Enter`.

### 4. Consistência conceitual — 6

* **Problema.** Duas coberturas diferentes para a lente 5 em duas telas, ambas
  rotuladas "cobertura"; duas coberturas diferentes para "gestor" na mesma tela
  (100,0 % na lente 1, 99,994 % na lente 8); a tela 6 publica 34 arquivos-fonte no
  chip T13 e 37 no cartão de meta; T15 publica uma explicação factualmente falsa
  para a diferença de reconciliação.
* **Materialidade.** Média-alta. Nada disso é um erro de conta, mas um painel que se
  vende como disciplina conceitual não pode contradizer-se entre duas abas.
* **Evidência.** `lentes_catalogo.csv` linha 5 (`69,3`) × `painel_dados.json →
  sacado_cobertura_dc` (`0,7967`); `lente_8_exposicao_operacional.csv` linha Gestor
  (`0,9999399`); `manifesto_fontes.csv` = 37 linhas × chip `T13 34/34`; recálculo
  próprio: 4.327 de 4.327 veículos têm tab X_2, logo a explicação de T15 é falsa.
* **Correção necessária.** Um único dicionário de coberturas, com nome próprio para
  cada uma (`cobertura_por_veiculo`, `cobertura_por_valor_do_dc`,
  `cobertura_valor_explicado`), consumido por todas as telas; regenerar
  `testes_auditoria.csv` no mesmo pipeline do painel; reescrever o detalhe de T15
  (a diferença de 0,044 % vem de marcação de cota × PL, não de veículos ausentes).
* **Teste de validação.** Assertar que nenhum par (grandeza, tela) apresenta dois
  valores de cobertura distintos; assertar
  `T13.resultado.split('/')[1] == len(manifesto_fontes)`.

### 5. Reprodutibilidade — 7

* **Problema.** Não há orquestrador com grafo de dependência: `lentes_catalogo.csv`
  (17:40) foi publicado junto de `rj_*.csv` (18:01), e o HTML (18:05) foi publicado
  contra um JSON que já mudara (18:10). O `hash_manifesto` cobre as fontes, não os
  derivados.
* **Materialidade.** Média. A base é reproduzível — eu a reproduzi —, mas o
  **artefato publicado** não tem garantia de corresponder a um único estado da base.
* **Evidência.** `ls --time-style` dos artefatos; tabela `fichas` presente no JSON
  das 18:10 e ausente do HTML das 18:05; README "Extração 17/08" × painel "18/08".
* **Correção necessária.** Um `make`/`runner` com dependências declaradas, e um
  `hash_dados` (SHA-256 de `painel_dados.json`) gravado dentro do HTML, checado no
  carregamento; data de extração lida do manifesto, nunca digitada.
* **Teste de validação.** No CI: rodar o pipeline duas vezes do zero e exigir HTML
  byte-idêntico; assertar que o `hash_dados` embutido no HTML é igual ao SHA-256 do
  `painel_dados.json` no disco.

### 6. Tratamento de duplicidades — 9

* **Problema.** Único achado: 2 veículos que são positivos de CR023 servem de
  controle em CR024 (6,7 % daquele grupo de controle).
* **Materialidade.** Baixa. Não afeta os resultados de CR023, que é o único evento
  com conclusões.
* **Evidência.** 56 pares (CNPJ, competência) duplicados em `backtest_detalhe.csv`,
  todos do cruzamento CR023-positivo × CR024-controle.
* **Correção necessária.** Excluir do pool de controles de qualquer evento os CNPJs
  que sejam positivos em qualquer outro evento da biblioteca.
* **Teste de validação.** `assert set(positivos_todos) & set(controles_todos) == set()`.

### 7. Resolução de entidades — 6

* **Problema.** CNPJ armazenado como float perde zeros à esquerda e é renderizado
  com máscara de milhar na tela judicial; a pseudonimização de pessoas naturais é
  reversível em um clique; a lente 1 declara 100 % de cobertura com 2 veículos sem
  gestor resolvido.
* **Materialidade.** **Alta** para o item do CNPJ: identificador errado ao lado de
  razão social em contexto de recuperação judicial e falência é o vetor mais direto
  de atingir a empresa errada, e é justamente o risco que o manual de limitações
  jurídicas foi escrito para evitar.
* **Evidência.** `painel_dados.json → tabelas.rj.linhas[2][1] = 8662033000109.0`
  (13 dígitos, zero perdido); renderizado como `8.662.033.000.109`; caso 1 da tabela
  `casos` (cargo + gestora + PAS + multa exata + ponteiro para a decisão).
* **Correção necessária.** Serializar todo documento como **string** com máscara
  correta na origem (`zfill(14)` + formatação `NN.NNN.NNN/NNNN-NN`); marcar as
  colunas de documento como não numéricas no renderizador; ou remover os
  identificadores individuais dos casos com pessoa natural, ou assumir a nominação
  com parecer jurídico — a via intermediária atual entrega o risco sem o benefício;
  publicar a cobertura da lente 1 com 4 casas (99,9937 %) e uma linha
  "gestor não identificado".
* **Teste de validação.** `assert all(re.fullmatch(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', c)
  for c in coluna_cnpj_renderizada)`; teste de reidentificação: dado apenas o texto
  publicado, um terceiro consegue nomear a pessoa natural? Se sim, reprovar.

### 8. Tratamento das limitações — 7

* **Problema.** O aparato de limitações é o melhor do conjunto, mas o produto viola
  o próprio checklist em três itens (CRSFN ausente em 8 de 18 condenações; sem URL
  na tabela de casos; "esquema de lavagem" atribuído a imprensa e não a peça
  oficial) e viola a regra "ausente nunca vira zero" no backtest (S3).
* **Materialidade.** **Alta.** Um manual descumprido pelo próprio produto é pior que
  a ausência de manual, porque documenta que o autor sabia da regra.
* **Evidência.** b.8 (lista nominal dos 8 casos); b.4 (`18_backtest.py:96`);
  `docs/LIMITACOES_E_RISCOS_JURIDICOS.md` linhas 34 e 360-370;
  `docs/METODOLOGIA_RED_FLAGS.md` §1.1.
* **Correção necessária.** Acrescentar a cláusula de recurso ao CRSFN aos 8 casos;
  publicar `fonte_url` na tabela `casos`; reescrever o trecho do caso 25 para
  eliminar "esquema" fora de citação oficial, ou remover a nominação do fundo;
  no script 18, trocar `coalesce(s.v_sub,0)` por uma cláusula explícita
  (`WHEN s.v_sub IS NULL AND <existe série sênior> THEN 0 ELSE NULL`) e **declarar a
  exceção** em `METODOLOGIA_RED_FLAGS.md §1.1`; documentar ali a convenção
  `z = fillna(0)` para somas de componentes.
* **Teste de validação.** Um linter de publicação que rode o checklist de 12 itens
  sobre o `painel_dados.json` antes de gerar o HTML e falhe o build: regex de
  "condena" sem "CRSFN"; regex das cinco palavras fora de aspas; coluna `fonte_url`
  obrigatória em toda tabela com `status_processual`.

### 9. Clareza — 6

* **Problema.** A lente 5 exibe uma tabela ordenada que na tela vai
  `144,1 % → 13,3 % → … → 1,6 % → 129 % → 120,1 %`; o subtítulo da capa promete que
  todo número é clicável e 93 % não são; `footer` e `.tile .src` reprovam em
  contraste WCAG AA no tema claro.
* **Materialidade.** Média-alta. A incoerência da lente 5 é o primeiro sinal que um
  leitor cético vê, e destrói a credibilidade das outras cinco telas.
* **Evidência.** Captura `aud/shot_lente5.png` e extração de texto do DOM;
  contraste medido: `footer` 2,85 (claro) / 4,60 (escuro); `.tile .src` 3,15 / 4,20.
* **Correção necessária.** As mesmas do item 2 (unidade declarada) resolvem a
  ordenação; ajustar `--muted` no tema claro de `#8A929C` para ≈ `#6B7280`;
  reescrever o subtítulo.
* **Teste de validação.** Assertar monotonicidade do valor **renderizado** em toda
  tabela ordenada; rodar um checador de contraste automático nos dois temas com
  limiar 4,5.

### 10. Utilidade econômica — 6

* **Problema.** A tela de supervisão — a de maior valor potencial — publica 25
  veículos, todos "não classificável", 20 deles com PL zero, e **nenhum** dos 14
  "atenção alta". A lente 5 é dominada por 166 razões acima de 100 % (erro de
  reporte), sem ressalva, tornando o ranking de concentração inutilizável.
* **Materialidade.** **Alta.** As duas telas que justificam o produto entregam,
  respectivamente, uma lista de fundos vazios e uma lista de erros de digitação.
* **Evidência.** `rf2_score_veiculo.csv`: 25 primeiras linhas com
  `classificacao = 'não classificável'`, `VL_PL = 0` em 20 delas,
  `cobertura_dados_pct ≤ 21,74`; os 14 de "atenção alta" começam na posição 42.
  `lente_5_*.csv`: 166 de 2.706 razões definidas acima de 1,0; máximo 2,18 × 10⁹.
* **Correção necessária.** Ordenar `rf_score` **dentro dos classificáveis**, por
  materialidade em R$ (ou publicar duas tabelas separadas e rotuladas: "veículos
  classificados" e "veículos sem cobertura suficiente para classificar", jamais no
  mesmo ranking); na lente 5, separar as razões > 100 % numa seção
  "inconsistências de reporte entre tab VIII e tab I" e mantê-las **fora** do
  ranking de concentração.
* **Teste de validação.** Assertar que a tabela `rf_score` publicada contém
  `≥ 1` veículo de cada faixa classificável e **0** veículos com
  `classificacao == 'não classificável'`; assertar que toda linha da lente 5 tem
  `pct_maior_sacado ≤ 1,0` ou carrega marca explícita de inconsistência.

---

## (e) Veredito

# REPROVADO

Reprovado **como artefato publicável**, não como trabalho analítico.

**A camada de dados passa com folga.** Recalculei dezenove indicadores a partir dos
CSV brutos da CVM com código independente e dezoito bateram **exatamente** —
zero diferença, não 0,1 %. Refiz as duas regras de dedup do zero e cheguei aos
mesmos 4.327 veículos e aos mesmos R$ 999.497.428.095,20. Nenhuma subclasse entra em
soma alguma; nenhuma lente excede o PL do mercado; nenhum zero foi fabricado a
partir de ausência nos denominadores; veículos "não classificáveis" nunca são
lidos como baixo risco; o painel não contém literal numérico escrito à mão. Sobre o
critério que originou a reconstrução, a resposta é: **sim, foi atendido.**

**A camada de apresentação reprova, e reprova por três defeitos que não admitem
publicação:**

1. **Dez linhas nominadas da lente 5 aparecem na tela com erro de 100×**, numa
   tabela ordenada que fica visivelmente absurda (`1,6 %` listado acima de `129 %`);
   três sinais do catálogo aparecem com cobertura 100× maior que a real. O painel
   não contém números inventados, mas **exibe números que não são os seus dados**.
2. **A gaveta de evidências de um indicador de capa publica uma fórmula que não
   reproduz o próprio número** — 911,7 % contra 97,9 % exibidos, fator 9,3, com a
   tabela de origem também errada. É o defeito mais grave do conjunto: a
   rastreabilidade é a razão de existir deste painel, e ela falha precisamente onde
   alguém a testaria.
3. **O produto descumpre o próprio manual jurídico** em oito condenações de primeira
   instância publicadas sem a ressalva obrigatória de recurso com efeito suspensivo,
   sobre entidades nominadas de grande porte, e renderiza CNPJ malformado — com zero
   à esquerda destruído — ao lado de razões sociais em contexto de recuperação
   judicial e falência.

Some-se a isso a contradição entre a tela 3 (lente 9 = 0 entidades) e a tela 5
(21 casos, 107 vínculos, R$ 4,6 bi), a tela de supervisão que não exibe um único dos
14 veículos que ela mesma classifica como atenção alta, e um backtest que, tendo
executado o exercício correto e reportado o falso negativo, ainda assim mantém S1
e descarta S6 com evidência estatística indistinguível (p = 0,052 contra p = 0,054),
publica só a metade favorável da coluna de antecedência e chama de "nenhum sinal
disparou" um caso em que dois dos seis sinais não eram avaliáveis.

**Nenhum desses defeitos é estrutural.** Todos são locais: uma função de formatação
que precisa parar de adivinhar unidade, três strings de fórmula, oito células de
status processual, uma serialização de CNPJ, uma ordenação de tabela e a
reexecução de um script na ordem certa. Estimo horas, não dias. Corrigidos os itens
1 a 3 acima e reexecutados os testes de validação da seção (d), o painel se torna,
na minha avaliação, o material público mais bem instrumentado que já vi sobre este
mercado — e eu reverto o veredito para **APROVADO COM RESSALVAS** sem hesitar.

Enquanto isso não acontecer, o painel exibe números errados por duas ordens de
grandeza e ensina o leitor a verificar por uma fórmula que não fecha. Não pode sair.

---

**Ressalva do auditor.** Os artefatos foram regenerados três vezes durante esta
auditoria (18:02, 18:05, 18:10/18:11). Todos os achados foram reconfirmados contra
o build das 18:11 (`painel_fidc_v2.html` md5 `96161b99…`). Achados posteriores a
esse build não estão cobertos por este parecer — em particular, a tabela `fichas`
("raio-X do veículo"), introduzida no JSON às 18:10, **não foi auditada**.

*Auditoria executada em 18/08/2026. Recálculo: `auditoria/espelho_reconstrucao_recalc.py`.
Sonda do navegador: `auditoria/espelho_reconstrucao_probe.js`.*
