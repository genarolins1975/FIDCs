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

---
---

# REVALIDAÇÃO — segunda passada (build de 18/08/2026 18:35 UTC)

**Objeto:** `relatorio/painel_fidc_v2.html` (md5 `e2d6a2d1dcf1a4b8b4da7d2741c6b537`),
`data/analytic/painel_dados.json` (md5 `5cdeb6ca5028dbb73fc909b12b74ab1e`),
`BACKTEST_RED_FLAGS.md`, `data/analytic/*.csv`. Commit `8391baf` ("Correções do
parecer espelho: os três bloqueantes e os achados materiais").

**Método:** os mesmos scripts da primeira passada, reexecutados contra o build novo
(`auditoria/espelho_reconstrucao_recalc.py`), mais sondas de navegador novas para a
aba **Ficha do veículo**, que não existia. O JSON embutido no HTML e o
`painel_dados.json` do disco foram comparados campo a campo: **idênticos** em
`indicadores` e em `tabelas` — a dessincronia da primeira passada não se repetiu.

**Recálculo independente:** os 18 indicadores continuam batendo com **diferença de
0,000000%** (PL R$ 999.497.428.095,20; 4.327 veículos; inadimplência 0,09130353506;
identidade contábil 0 violações em 4.327 avaliáveis; cobertura da tab VIII 0,7967534;
séries sênior/mezanino/subordinada; 232 ausentes em julho; 979 séries abaixo do
esperado; 28 veículos com garantia). Zero erro de console e zero `pageerror` nas
sete abas, em tema claro e escuro.

## R.1 — Situação dos três bloqueantes

### BLOQUEANTE 1 (erro de escala de 100×) — **CORRIGIDO**

O renderizador deixou de adivinhar. Cada tabela carrega `unidades` paralelo a
`colunas` e `cellFmt(col, v, unidade)` faz `switch` sobre a unidade declarada, sem
inspecionar magnitude nem nome de coluna. Verifiquei **célula a célula** o valor
pintado contra o JSON sob a unidade declarada:

* **Lente 5** — as 25 linhas renderizam exatamente o esperado. O topo agora é
  `101,7% → 100,4% → 100,3% → 100,1% → … → 100%`, monotônico. A inversão
  `1,6%` acima de `129%` desapareceu.
* **Catálogo de sinais** — `JR-01` renderiza **0,9%** (era 90%) e `PO-04`
  renderiza **0,7%** (era 69%). Corretos.
* Varri as 13 tabelas: nenhuma coluna percentual, monetária ou de índice
  diverge do JSON. **Achado encerrado.**

### BLOQUEANTE 2 (fórmula que não fechava) — **PARCIALMENTE CORRIGIDO**

* `provisionamento` — **corrigido e reproduzido.** A fórmula publicada é agora
  `(TAB_I2A11 + TAB_I2B11) ÷ (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD)`
  e o campo `"tabs I (numerador), V e VI (denominador)"`. Executei a fórmula
  literalmente sobre os CSV brutos: **0,978886** contra **0,978886** publicado.
* `rf_atencao_alta` — **ainda não reproduz.** A fórmula passou de uma população
  errada para outra. Diz agora *"p99 da distribuição entre os veículos
  CLASSIFICÁVEIS (cobertura ≥ 50%), não do universo completo"*. Seguindo isso ao
  pé da letra:

  | base | n | p99 | veículos ≥ p99 |
  |---|---:|---:|---:|
  | universo (formulação antiga) | 4.327 | 23,86 | 44 |
  | **classificáveis (formulação atual)** | **3.228** | **16,39** | **41** |
  | classificáveis **com ≥ 1 disparo** (o que o código faz) | 1.301 | 18,71 | **14** |

  O valor publicado é 14. A fórmula publicada devolve 41 — fator ~3. O corte real
  está em `scripts/13_red_flags_v2.py:1807` (`base_sc = sc.loc[cls & (sc.score_risco > 0)]`)
  e a condição `score_risco > 0` continua fora da fórmula.
* **Achado novo, da mesma família:** `rf_sem_sinal` publica
  `formula = "COUNT(n_disparos = 0)"` e `valor = 1927`. `COUNT(n_disparos = 0)`
  sobre `rf2_score_veiculo.csv` devolve **2.534**. A definição efetiva é
  `cobertura ≥ 50% E score = 0`, que dá exatamente 1.927. Diferença de **607
  veículos**. Atenuante: `rf_sem_sinal` não é renderizado em nenhuma tela — o
  defeito está no JSON publicado, não na página.
* **Menor, mas na mesma inspeção:** `sacado_n_top1_50` publica
  `formula = "contagem sobre veículos com razão definida"`, que não menciona o
  limiar de 50% — o único lugar onde ele aparece é o rótulo.

Conclusão: dos quatro indicadores cuja fórmula testei exaustivamente nesta passada,
**um foi corrigido, um continua sem reproduzir, um novo foi encontrado sem
reproduzir e um está incompleto**. O bloqueante não pode ser considerado sanado:
a auditoria por fórmula publicada ainda falha em 2 de 36 indicadores.

### BLOQUEANTE 3 (manual jurídico) — **PARCIALMENTE CORRIGIDO, COM REGRESSÃO**

Corrigido:

* **CRSFN — 16 de 16.** Todas as condenações de 1ª instância trazem agora
  *"cabe recurso ao CRSFN com efeito suspensivo"*. Verifiquei linha a linha.
* **CNPJ — corrigido.** Serializado como string com `zfill(14)`:
  `"08662033000109"` chega íntegro à tela, com o zero à esquerda preservado.
  (Sugestão cosmética, não achado: aplicar a máscara `08.662.033/0001-09`.)
* **`fonte_url` — de volta** à tabela de casos.
* **Pessoas naturais — agregadas** em três linhas
  (*"N pessoa(s) natural(is) acusada(s) — identificação suprimida nesta
  apresentação; consulte a fonte oficial"*), sem cargo e sem gestora.

Não corrigido / regressão:

* **A agregação é incompleta.** A linha 5 publica, como nome de entidade:
  *"Acusados do PAS CVM 19957.006858/2019-25 (gestora, **seu diretor**, **Santander
  Securities** e **seu diretor**)"*. Cargo + empresa nominada + número do processo
  identifica univocamente duas pessoas naturais, exatamente o padrão que as outras
  três linhas passaram a evitar. A reversibilidade que apontei apenas mudou de
  linha.
* **REGRESSÃO: a coluna `descricao_irregularidade` foi removida da tabela
  publicada.** Ela continua em `casos_regulatorios.csv`, mas saiu de
  `painel_dados.json → tabelas.casos.colunas`. Consequências, ambas ruins:
  1. Quinze entidades nominadas — **Banco Bradesco, Banco Santander, KPMG,
     Deutsche Bank, BNY Mellon, Oliveira Trust, Planner, Finaxis, Gradual,
     Trendbank, Regen** — aparecem agora na tela assim, e só assim:
     `Banco Bradesco S.A. | custodiante | PAS | 2015-10-20 | condenacao (1ª
     instância administrativa; cabe recurso ao CRSFN com efeito suspensivo) |
     fato confirmado por fonte primária | URL`.
     **Nominar como condenada uma instituição sem dizer por qual conduta é mais
     lesivo, não menos.** A descrição era justamente o que qualificava a imputação
     (*"na qualidade de administradora, por falha no dever de diligência…"*).
  2. **O identificador do processo sumiu da tela.** O número do PAS vivia na
     descrição. Hoje `19957.006858/2019-25` aparece uma única vez na página
     inteira — por acidente, dentro do nome da linha 5. O item do checklist
     *"Toda menção a processo tem identificador, autoridade, data, status e URL"*
     (`docs/LIMITACOES_E_RISCOS_JURIDICOS.md §9`) continua descumprido: a correção
     trocou a violação do "URL" pela violação do "identificador".

## R.2 — Achado NOVO e bloqueante: a aba "Ficha do veículo"

A aba não existia na primeira passada. Auditei-a integralmente.

**O que está certo.** A ficha **não** usa `renderTable`: tem formatadores próprios
(`brl()`, `pct()`) que devolvem `—` para `null`. Distingue explicitamente zero
reportado de ausência — exibe **"R$ 0 (reportado)"**, o que é uma boa prática e
merece registro. Conferi no bruto que os zeros exibidos são zeros de fonte: os 41
veículos com `pct_maior_sacado = 0` têm linha na tab VIII com `VALOR = 0,00`, e os
126 com `inad_pct = 0` têm `TAB_V_B = 0` com `TAB_V_A > 0`. **Nenhum zero
fabricado.** Busca por nome e por CNPJ funciona; seleção sem resultado devolve
mensagem; zero erro de console.

**O que reprova.** A ficha exibe, no campo "Sinais de atenção", ou os códigos
disparados, ou o chip **verde** `nenhum disparado`. Cruzei as 400 fichas com
`rf2_score_veiculo.csv`:

| classificação do veículo | fichas que exibem "nenhum disparado" |
|---|---:|
| `sem sinal disparado` (cobertura ≥ 50%) | 47 |
| **`não classificável` (cobertura < 50%)** | **14** |

Esses 14 veículos somam **R$ 16.071.657.327,79 de patrimônio líquido** e incluem
EXPERT III (R$ 3,5 bi), Solis Capital Antares Advisory (R$ 2,1 bi), FIC RED P
(R$ 1,7 bi), Ouro Preto FIC (R$ 1,3 bi) e Solis Capital Antares (R$ 1,3 bi) —
todos com `cobertura_dados_pct = 45,65%`.

Reproduzido na tela (busca "EXPERT III"):

```
EXPERT III FUNDO DE INVESTIMENTO EM DIREITOS CREDITÓRIOS DE RESPONSABILIDADE ILIMITADA
CNPJ 53073485000100 · Classe
Patrimônio líquido            R$ 3,5 bi
Direitos creditórios          R$ 0 (reportado)
Sinais de atenção             [chip verde] nenhum disparado
```

**Materialidade: crítica.** O *warnbox* da tela 4, duas abas antes, diz:
*"Cobertura insuficiente gera classificação 'não classificável' — nunca 'baixo
risco'."* A tabela `rf_score` foi corretamente saneada nesta rodada para honrar
essa regra. **A aba nova a viola no formato mais grave possível**: não um rótulo
neutro, mas um **chip verde**, que é o vocabulário visual de atestado de
conformidade, sobre fundos **nominados**, de bilhões de reais, cuja informação
pública não permite concluir coisa alguma. E a ficha **não exibe cobertura em
nenhum campo** — o leitor não tem como suspeitar. É a mesma falha que motivou a
reprovação anterior, migrada da tela 4 para a aba 5 e agravada pela cor.

Achados secundários da ficha, não bloqueantes: o `<select>` lista apenas **200 dos
400** veículos enquanto a busca está vazia (`slice(0,200)`), sem avisar; e os
códigos de sinal (`CN-04`, `QA-04`…) aparecem sem nome nem link para o catálogo.

## R.3 — Achados materiais: o que foi corrigido

Todos verificados por recálculo próprio:

* **Lente 9 — corrigida.** Passou de 0 para **21 entidades**, batendo com
  `rj_casos = 21` da tela 5. A contradição entre telas acabou.
* **`rf_score` — corrigida.** A tabela publica agora **14 "atenção alta" + 11
  "atenção média"**, todos classificáveis, com PL e materialidade reais
  (SPDA Habitação, ABC I, NPL II, C3E Créditos Judiciais…). Nenhuma linha com
  PL zero. A nota explicita que os não classificáveis ficam fora e são contados
  no cartão próprio. Exatamente a correção pedida.
* **Lente 5 — exclusão implementada e reproduzida.** Reimplementei o filtro:
  `top25 / dc_total > 1,05` marca **307** veículos (idêntico ao publicado), restam
  **932** elegíveis com PL > R$ 100 mi, e o top-25 que reproduzi é **exatamente** o
  publicado. *Ressalva:* a nota diz que foram excluídos os veículos "em que a soma
  dos 25 maiores devedores **excede** a carteira", mas o critério aplicado é
  "excede em **mais de 5%**" — e por isso 9 das 25 linhas publicadas ainda têm
  maior devedor acima de 100% da carteira (até 101,7%). A nota descreve um
  critério mais estrito do que o executado.
* **T13 — corrigido:** `37/37`, coerente com `n_arquivos_manifesto = 37`.
* **T15 — corrigido:** o detalhe agora lê *"0 veículos sem X_2 no corte; a
  diferença residual vem de defasagem de marcação"*, que é precisamente o que eu
  havia apurado.
* **Backtest — correções substantivas, todas reproduzidas.** Recalculei o teste
  exato de Fisher **unilateral** para os seis sinais e obtive os seis valores
  publicados até a quarta casa:

  | Sinal | Positivos | Controles | Lift (meu = pub) | p (meu = pub) |
  |---|---|---|---:|---:|
  | S5 | 144/151 | 96/453 | 4,5000 | 0,0000 |
  | S3 | 125/150 | 126/444 | 2,9365 | 0,0000 |
  | S1 | 16/58 | 30/193 | 1,7747 | **0,0328** |
  | S4 | 63/149 | 155/432 | 1,1784 | 0,0983 |
  | S6 | 18/59 | 98/219 | 0,6818 | **0,9839** |
  | S2 | 0/132 | 24/345 | 0,0000 | 1,0000 |

  **Retiro formalmente minha objeção b.9.1.** Sob o teste unilateral na direção
  da hipótese — que é o enquadramento correto para "positivos disparam mais" —
  S1 (p = 0,033) e S6 (p = 0,984) **não** são estatisticamente indistinguíveis:
  são opostos. Manter S1 e descartar S6 passou a ser uma decisão sustentada pelos
  números, e o descarte adicional de S4 (p = 0,098) é coerente com o mesmo
  critério. A coluna `n_nao_avaliavel` foi separada de `n_disparou`, e o
  `coalesce(v_sub,0)` de S3 foi removido — o que mudou o grupo de controle de
  S3 e elevou o lift de 2,59 para 2,94. **Objeção b.4 encerrada.**
* **Falso negativo CR024 — corrigido.** O texto agora diz: *"Dos seis sinais,
  quatro foram avaliáveis e nenhum disparou; dois (S1 e S6) ficaram não
  avaliáveis por ausência de cedente declarado — e 'não avaliável' não é 'não
  disparou'."* É exatamente a distinção que faltava. **Objeção b.9.4 encerrada.**
* **Teclado — corrigido.** `Enter` sobre o link de evidência focado abre a gaveta;
  `Escape` fecha. Contraste do `footer` no tema claro também foi corrigido.

## R.4 — Achados materiais que NÃO foram corrigidos

1. **`BACKTEST_RED_FLAGS.md` publica uma linha com números de duas execuções
   diferentes.** A tabela de CR023 lista `S3 — Controles **32,2%**`, valor da
   execução anterior; o `backtest_resumo.csv` do mesmo build diz **28,4%**
   (126/444). Na mesma linha, o lift **2,94** já é o novo (83,3 / 28,4 = 2,94;
   83,3 / 32,2 daria 2,59). Isto é o sintoma exato que apontei em b.5 — artefato
   derivado publicado sem reexecução — reaparecendo no arquivo que mais depende de
   consistência interna.
2. **Contaminação do grupo de controle do backtest — não corrigida.** Continuam
   56 pares (CNPJ, competência) duplicados em `backtest_detalhe.csv`, envolvendo 7
   CNPJs, entre eles veículos **positivos em CR023 usados como controle em CR024**.
3. **Lente 1 declara cobertura 100,0%** com 492 gestores, 4.325 de 4.327 veículos e
   soma de 99,9937% do PL — enquanto a lente 8, na **mesma tela**, publica
   `Gestor · cobertura 0,99994` para a mesma grandeza.
4. **Cobertura da lente 5 continua com dois valores** (69,3% na tela 3; 79,7% na
   tela 4) sem reconciliação, e a cobertura **em valor** — 45,3% do estoque de DC
   efetivamente explicado pelas posições listadas, que recalculei — segue não
   publicada.
5. **"Todo número é clicável e abre a evidência que o sustenta"** continua no
   subtítulo da capa. Medi neste build: **37 elementos `.ev`** contra **406 células
   `td.num` sem gaveta**.
6. **Contraste `.tile .src`**: 3,15 no tema claro e 4,20 no escuro (mínimo AA para
   texto pequeno: 4,5). O chip âmbar no tema claro fica em 4,48.

## R.5 — Resposta à pergunta em aberto: antecedência dos controles

**Sim, a omissão induz a erro. Publique as duas colunas. Não é bloqueante.**

A coluna se chama "Antecedência mediana" e fica numa tabela em que todas as demais
colunas são comparativas (positivos, controles, lift, p). O leitor infere que é uma
propriedade preditiva do sinal — *"S5 acende 4 meses antes"*. Os dados do próprio
`backtest_resumo.csv` desmentem essa leitura:

| Sinal | Antecedência positivos | Antecedência **controles** |
|---|---:|---:|
| S5 | 4 | **11** |
| S3 | 0 | **5** |
| S1 | 2 | **10** |
| S6 | 1 | **9** |
| S2 | — | **8** |
| S4 | **8** | 5 |

Em **cinco dos seis sinais os controles acendem mais cedo que os positivos**. Ou
seja: a "antecedência" mede sobretudo em que ponto da janela de 12 meses o sinal
costuma aparecer, não antecipação do evento. Publicada só a metade favorável, ela
sugere o contrário.

Por que **não** é bloqueante: o documento em nenhum lugar afirma poder preditivo —
ao contrário, a conclusão nega explicitamente ("*O backtest não autoriza afirmar que
os sinais preveem eventos*"), e a seção de armadilhas antecipa o problema do
confundimento estrutural. A omissão enfraquece um documento que já é
autolimitado, mas não afirma nada falso. **Correção:** acrescentar a coluna de
controles e uma linha de leitura — *"em 5 dos 6 sinais os controles acendem antes:
a coluna mede posição na janela, não antecipação"*. **Teste:** assertar que toda
métrica publicada por grupo tenha as duas colunas.

## R.6 — Notas revistas

| # | Dimensão | 1ª passada | **Revalidação** | Movimento |
|---|---|:---:|:---:|---|
| 1 | Completude | 8 | **8** | lente 9 e `fonte_url` de volta, ficha nova; mas `descricao_irregularidade` removida e cobertura-em-valor ainda ausente |
| 2 | Precisão | 5 | **9** | erro de 100× eliminado; todas as células conferidas contra o JSON |
| 3 | Rastreabilidade | 5 | **6** | `provisionamento` e teclado corrigidos; `rf_atencao_alta` ainda não reproduz, `rf_sem_sinal` novo, identificador do processo saiu da tela |
| 4 | Consistência conceitual | 6 | **7** | T13, T15, `rf_score`, lente 9 corrigidos; persistem dupla cobertura, lente 1×lente 8 e a linha mista do backtest |
| 5 | Reprodutibilidade | 7 | **7** | HTML e JSON sincronizados; segue sem orquestrador — e o `BACKTEST_RED_FLAGS.md` prova que artefato velho passou de novo |
| 6 | Duplicidades | 9 | **9** | inalterado; contaminação do controle não corrigida |
| 7 | Resolução de entidades | 6 | **8** | CNPJ íntegro como string; agregação de pessoas naturais quase completa (linha 5 ainda reversível) |
| 8 | Tratamento das limitações | 7 | **7** | backtest muito melhor (Fisher, não avaliáveis, falso negativo honesto, S3 sem `coalesce`); mas a ficha viola a regra-mãe e a descrição sumiu |
| 9 | Clareza | 6 | **7** | lente 5 coerente, teclado e rodapé corrigidos; "todo número é clicável" ainda falso |
| 10 | Utilidade econômica | 6 | **7** | `rf_score` e lente 9 passaram a ser úteis, ficha é um ganho real; mas o chip verde engana sobre R$ 16 bi |

**Média: 7,5** (era 6,5).

## R.7 — Veredito da revalidação

# REPROVADO

Reprovado por margem estreita, e por instrução expressa: persiste defeito
bloqueante. Reconheço que a rodada foi séria — sete dos dez achados materiais e
dois dos três bloqueantes foram genuinamente resolvidos, e o backtest melhorou a
ponto de eu retirar duas objeções formalmente. A camada de dados segue impecável:
18 indicadores reproduzidos com diferença de 0,000000%.

**Três defeitos impedem a publicação:**

1. **[NOVO] A aba "Ficha do veículo" exibe chip verde "nenhum disparado" para 14
   veículos não classificáveis que somam R$ 16,07 bi de PL**, sem mostrar cobertura
   em campo algum. É a regra-mãe do produto — *cobertura insuficiente nunca é baixo
   risco* — violada em fundos nominados, com o vocabulário visual do atestado de
   conformidade. Corrigida na tela 4, reintroduzida na aba nova.
   **Correção:** substituir o chip por `cobertura insuficiente para concluir
   (45,7% dos sinais avaliáveis)`, em cor neutra, e acrescentar uma linha fixa
   "Cobertura de dados" a toda ficha. **Teste:** assertar que nenhuma ficha com
   `cobertura_dados_pct < 50` renderize `class="chip ok"`.
2. **A fórmula de `rf_atencao_alta` continua sem reproduzir o valor** (41 pela
   fórmula publicada, 14 publicado) e um caso novo apareceu (`rf_sem_sinal`: 2.534
   pela fórmula, 1.927 publicado). O bloqueante 2 foi tratado indicador a
   indicador, não sistemicamente.
   **Correção:** acrescentar `E score_risco > 0` à fórmula de `rf_atencao_alta` e
   `cobertura ≥ 50% E score = 0` à de `rf_sem_sinal`. **Teste — o que resolve a
   classe inteira:** um teste que, para **cada** um dos 36 indicadores, execute a
   `formula` publicada contra os CSV e falhe o build se divergir de `valor` em mais
   de 0,1%. Enquanto esse teste não existir, este achado voltará.
3. **A remoção de `descricao_irregularidade` é uma regressão jurídica.** Quinze
   instituições nominadas aparecem como condenadas em 1ª instância **sem que a
   página diga por qual conduta e sem o número do processo** — o identificador
   saiu da tela junto com a descrição, descumprindo o mesmo checklist que a
   correção pretendia atender. E a linha 5 ainda identifica duas pessoas naturais
   por cargo + empresa + número do PAS.
   **Correção:** devolver `descricao_irregularidade` às colunas publicadas (é o que
   qualifica a imputação) e reescrever a linha 5 no padrão agregado das linhas
   22-24. **Teste:** o linter de publicação que já recomendei — falhar o build se
   houver linha com `status_processual` contendo "condena" sem número de processo
   visível na linha, ou com cargo de pessoa natural associado a empresa nominada.

Não bloqueiam, mas devem entrar na mesma rodada: a linha `S3 — Controles 32,2%` do
`BACKTEST_RED_FLAGS.md`, que mistura duas execuções; a coluna de antecedência dos
controles (R.5); a contaminação do grupo de controle de CR024; a cobertura da
lente 1 (100,0% × 99,9937%); a cobertura em valor da lente 5 (45,3%); e o subtítulo
"Todo número é clicável", falso para 406 dos 443 números da página.

Corrigidos os três itens acima e implementado o teste automático de fórmulas do
item 2 — que é o único que impede a reincidência —, **aprovo com ressalvas**. O
trabalho está a uma rodada curta disso.

*Revalidação executada em 18/08/2026, 18:35–18:45 UTC, sobre o commit `8391baf`.*

---

# R.8 — Terceira passada (build de 18/08/2026 19:12 UTC) — veredito definitivo

**Objeto:** commits `b6f91c3` (código/docs) e `68d782a` (artefatos via orquestrador).
`painel_fidc_v2.html` md5 `8f4b7be1…`, `painel_dados.json` md5 `8c119ba0…`.
Escopo: confirmar ou negar a resolução dos achados das passadas 1 e 2, mais os
dois módulos novos (bloco "O que mudou no mês" e aba "Raio-X da empresa").

## R.8.1 — Os três bloqueantes: verificação item a item

**Bloqueante 1 (ficha × regra-mãe) — RESOLVIDO.** A tabela `fichas` agora carrega
`cobertura_dados_pct`, `classificacao`, `score_risco`, `n_avaliaveis` e
`n_disparos`. Cruzei as 400 fichas com `rf2_score_veiculo.csv`: **zero** fichas com
cobertura < 50% fora de "não classificável". No navegador, EXPERT III (cobertura
45,6%) exibe **chip neutro** `cobertura insuficiente para concluir (45,6% dos
sinais avaliáveis)` — classe CSS `.chip.na`, cor `--neutral`, sem vocabulário de
conformidade — e toda ficha tem a linha fixa "Cobertura de dados". Li o código
gerado: o chip verde só é alcançável para veículo classificável, e mesmo então
carrega a cobertura no texto (`nenhum disparado (cobertura X%)`). O teste
`regra_mae_fichas` existe no gate e passou (400/0).

**Bloqueante 2 (teste sistêmico de fórmulas) — RESOLVIDO.** `scripts/20_teste_formulas.py`
é o teste que exigi: executei-o eu mesmo — **49/49 OK, exit 0** — e conferi o
contrato no código: indicador sem verificador **falha o build** (verifiquei por
diferença de conjuntos: os 47 indicadores do JSON têm verificador; os 2
verificadores extras são os linters). O orquestrador `00_atualizar.py` encadeia
05 e 20 como gates antes do 17 — o painel não é gerado se falharem. As fórmulas
que não fechavam agora fecham: `rf_atencao_alta` declara *"CLASSIFICÁVEIS …
COM ao menos um sinal disparado (score > 0)"* e `rf_sem_sinal` declara
`COUNT(cobertura ≥ 50 E score = 0)` — ambas reproduzem 14 e 1.927. A divergência
máxima nas 47 verificações é da ordem de 1e-13 (ruído de ponto flutuante).
*Nota de desenho, não de falha:* os verificadores recomputam dos artefatos
intermediários e do DuckDB, não do CSV bruto — é um gate de consistência, não uma
reprodução independente. A reprodução independente do bruto é a que este parecer
fez (18 indicadores, dif 0,000000%), e as duas camadas juntas cobrem o risco.

**Bloqueante 3 (regressão jurídica) — RESOLVIDO.** `descricao_irregularidade`
voltou às colunas publicadas. Verifiquei linha a linha na tela renderizada:
**16 condenações**, todas com "cabe recurso ao CRSFN com efeito suspensivo" **e**
com número de processo visível (inclusive o formato antigo `RJ2017/02029` no caso
Trendbank). A antiga linha 5 foi reescrita no padrão agregado ("Proponentes de
termo de compromisso no PAS CVM 19957.006858/2019-25 — 2 instituições e 2
pessoa(s) natural(is), identificação … suprimida"), sem cargo. As sanitizações de
Finaxis e Planner ("Pessoa natural também foi multada…") conferem — e registro a
favor do processo que o linter jurídico pegou dois casos que **eu não havia
listado**. Nenhuma ocorrência de "seu diretor"/"sua diretora" no HTML publicado.

## R.8.2 — Não bloqueantes da rodada: verificação

* **`BACKTEST_RED_FLAGS.md` regenerado entre marcadores — confirmado.** Conferi as
  6 linhas da tabela contra `backtest_resumo.csv` célula a célula: taxas, lifts,
  p-valores, não-avaliáveis e as **duas** colunas de antecedência — tudo bate
  (S3 controles agora 28,4%, a linha mista morreu). Recalculei o Fisher unilateral
  dos seis sinais: idêntico até a 4ª casa. A linha de leitura da antecedência que
  pedi está publicada.
* **Pool de controle descontaminado — confirmado.** Interseção entre CNPJs
  positivos e controles, em todos os eventos: **0**. Restam 6 CNPJs que servem de
  controle em **dois** eventos distintos (48 pares veículo-mês) — controle
  compartilhado entre eventos é legítimo; sem objeção.
* **Lente 1 — corrigido:** cobertura publicada 99,99%.
* **Subtítulo — corrigido:** "Cada **indicador** desta página abre, ao clique, a
  gaveta de evidência…" — afirmação agora verdadeira.
* **Aba Auditoria** renderiza a tabela `verificacao` (49 linhas). Observação: a
  tabela existe no HTML e não no `painel_dados.json` do disco — é injetada pelo
  17 depois do gate 20, por desenho (o delta entre HTML e JSON é exatamente ela).
  Aceitável; documentar.
* **Módulos novos.** "O que mudou no mês": os 12 indicadores novos (var_1m/3m/6m,
  aquisições/captações/resgates, entrantes/saíntes, sinais novos/persistentes)
  passaram no gate; `mudou_sinais_encerrados` publicado como **nulo declarado**
  ("não computável até haver snapshot") em vez de zero — exatamente a disciplina
  certa, e o orquestrador versiona o snapshot que o tornará computável. "Raio-X da
  empresa": 60 cedentes, nota adequada (estoque atribuído ≠ dívida; RJ ≠
  irregularidade), CNPJ como string. Sete abas navegam; **zero erro de console**.

## R.8.3 — Achado NOVO desta passada (a ressalva principal)

**A "cobertura em valor" da lente 5 — o número que eu pedi — foi publicada
errada: 62,5% onde o correto é 42,1%.**

A ficha da lente 5 (tela 3) diz: *"as posições listadas (top-25 por veículo)
explicam **62.5%** do estoque total de DC"*. Reproduzi a consulta de
`14_lentes_exposicao.py:196`:

```sql
SUM(LEAST(s.top25, dc.v)) / SUM(dc.v)   -- s vem de LEFT JOIN
```

Em DuckDB, `LEAST(NULL, v)` **ignora o NULL e devolve `v`** (verifiquei:
`SELECT LEAST(NULL, 5)` → `5`). Para os 1.328 veículos **sem** tab VIII, `s.top25`
é NULL e o veículo entra no numerador **com o próprio DC inteiro** — ou seja, a
carteira não observada é contada como observada. Prova aritmética:
42,1% (correto) + 20,3% (DC dos não cobertos) = 62,5% (publicado), fecha exato.
O valor correto de Σ LEAST(top25, dc) ÷ DC total é **0,4213**; sem o cap,
Σ top25 ÷ DC = 0,4531 (meu 45,3% da 2ª passada). Registro ainda que a mensagem da
coordenação citou "45,7%" — **três números em circulação para a mesma grandeza, e
o publicado não é nenhum dos recalculáveis**.

Duas lições que viram ressalvas: (i) a correção — `FILTER (s.CNPJ IS NOT NULL)`
no numerador — é uma linha; (ii) mais importante, o número vive em **texto de
nota**, fora de `indicadores`, e portanto **fora do alcance do gate 20**: é
exatamente o ponto cego pelo qual o único número errado desta passada passou.

## R.8.4 — Notas finais

| # | Dimensão | 1ª | 2ª | **3ª** |
|---|---|:---:|:---:|:---:|
| 1 | Completude | 8 | 8 | **9** |
| 2 | Precisão | 5 | 9 | **9** |
| 3 | Rastreabilidade | 5 | 6 | **9** |
| 4 | Consistência conceitual | 6 | 7 | **8** |
| 5 | Reprodutibilidade | 7 | 7 | **9** |
| 6 | Duplicidades | 9 | 9 | **9** |
| 7 | Resolução de entidades | 6 | 8 | **8** |
| 8 | Tratamento das limitações | 7 | 7 | **9** |
| 9 | Clareza | 6 | 7 | **8** |
| 10 | Utilidade econômica | 6 | 7 | **8** |

**Média: 8,6** (era 6,5 → 7,5).

## R.8.5 — VEREDITO DEFINITIVO

# APROVADO COM RESSALVAS

O critério que enunciei na revalidação — os três bloqueantes corrigidos **e** o
teste automático de fórmulas implementado — foi cumprido, e cumprido de forma
verificável: eu mesmo executei o gate (49/49), reproduzi a tabela do backtest
célula a célula, cruzei as 400 fichas contra o score, li o código do chip e
percorri as 16 condenações na tela. A camada de dados nunca esteve em questão
(18 indicadores reproduzidos do bruto com diferença zero em três passadas); a
camada de apresentação agora tem gate, orquestrador com ordem de dependência e
linter jurídico — as três ausências estruturais que produziram os defeitos das
passadas anteriores.

**Ressalvas, em ordem de prioridade:**

1. **[CORREÇÃO OBRIGATÓRIA na primeira reedição] O 62,5% da ficha da lente 5 está
   errado; o correto é 42,1%** (bug `LEAST`/NULL, R.8.3). Uma linha de SQL. E
   estender o gate 20 aos números embutidos em notas e fichas de lente — o único
   erro desta passada viveu exatamente nesse ponto cego. Enquanto não corrigir,
   qualquer leitura externa da lente 5 superestima em 20 p.p. o quanto do risco
   de devedor é observável.
2. **O gate é de consistência, não de reprodução independente**: os verificadores
   partilham os artefatos intermediários com o compilador. Declarar isso no
   cabeçalho do `verificacao_formulas.csv` e, idealmente, migrar 3-4 verificadores
   âncora (pl_total, inadimplência, identidade contábil) para leitura direta do
   CSV bruto.
3. **Backtest**: pareamento por segmento/tipo de veículo pendente (o próprio MD o
   declara); a biblioteca segue com um único evento robusto; se novos eventos
   entrarem, a exclusão de positivos de todos os pools precisa ser regra do
   código de ingestão de eventos, não do build atual (risco de recontaminação).
4. **Lente 4**: cobertura em valor análoga à da lente 5 (piso de 29,4%) ainda sem
   decomposição veículos × DC × valor explicado.
5. **Cosméticos**: `false`/`None` de `cotista_corporativo`/`status_judicial`
   renderizam como literais na aba Raio-X; o seletor da ficha lista 200 de 400
   veículos sem aviso; CNPJ sem máscara `NN.NNN.NNN/NNNN-NN`; contraste do chip
   âmbar 4,48 no tema claro (alvo 4,5); "encerrados" dependerá de disciplina de
   snapshot entre edições.

Nenhuma ressalva envolve número de capa, entidade nominada ou risco jurídico — a
classe de defeito que motivou as duas reprovações está extinta neste build e, mais
importante, tem agora contenção automática contra reincidência. O painel está apto
a circular com a ressalva 1 corrigida na próxima regeneração.

*Terceira passada executada em 18/08/2026, 19:13–19:25 UTC, sobre `68d782a`.
Recálculo e testes: `auditoria/espelho_reconstrucao_recalc.py` (seção 3ª passada).*

---

# R.9 — Verificação do fechamento das ressalvas (build `09ab150`, 18/08/2026)

Verificação curta e final. HTML md5 `03428487…`, JSON md5 `0390ae02…`.
Gate reexecutado por mim: **51/51 OK, exit 0**. Zero erro de console; 8 abas navegam.

**Ressalva 1 (62,5% → 42,1% na lente 5) — FECHADA** (já em `e80b44e`). A nota
publica **42,1%**, que é o valor que recalculei na 3ª passada; o gate agora extrai
os três percentuais do texto da nota e os recomputa com
`LEAST(...) FILTER (s.CNPJ IS NOT NULL)` — o ponto cego (número em texto de nota)
foi coberto para as lentes 4 e 5.

**Ressalva 2 (gate parcialmente circular) — FECHADA.** `painel_canonico_do_bruto()`
existe e é, linha por linha, a mesma reimplementação independente que fiz na 1ª
passada (tab IV bruta + registro classe/fundo, dedup próprio, sem DuckDB); cobre
`pl_total`, `n_veiculos`, `inadimplencia` e `identidade_contabil` — exatamente os
âncoras que pedi. A coluna `base` do `verificacao_formulas.csv` distingue
`bruto` (4) × `intermediário` (47), e a aba Auditoria documenta a distinção **e**
o delta HTML×JSON ("é, por desenho, o único conteúdo do HTML que não consta de
painel_dados.json"). Conferido no cabeçalho do script, no CSV e na tela.

**Ressalva 3 (backtest) — FECHADA.** Pareamento por veículo (mesmo
`TP_FUNDO_CLASSE`, PL 0,5x–2x, até 3 por positivo) implementado; 416 controles em
CR023. Recalculei o Fisher unilateral dos seis sinais contra o novo
`backtest_resumo.csv`: **idêntico até a 4ª casa** (S1 p=0,0407; S4 p=0,1658; S6
p=0,9982). A partição de significância é a mesma do desenho anterior e o MD
registra a robustez com os lifts corretos (4,46/3,85/1,70/1,13/0,61/0,00). A
descontaminação virou **invariante com `raise AssertionError`** antes da gravação
— vale para ingestão futura, como pedi. Interseção positivos×controles: **0**
(verificada). Varri a prosa do MD à caça de números da execução antiga (32,2 /
2,59 / 2,94 / 447 / 453 / 0,033 / 1,18 / 1,77 / 0,68): **nenhum stale** — todos os
números da prosa correspondem ao CSV corrente, incluindo o "~38%" de cobertura de
S1/S6 (CSV: 38,4% / 39,1%). Pendência de pareamento por público-alvo/segmento
corretamente reescrita como limitação, com a advertência certa sobre parear pelas
variáveis-sinal.

**Ressalva 4 (lente 4) — FECHADA.** A nota decompõe as três coberturas
(38,2% / 44,7% / 29,4%) e o gate as recomputa (`lente4_coberturas_na_nota`,
51/51). *Observação de redação, sem exigência:* a nota diz "declaram **ao menos um
cedente**", mas a definição executada é "cedente com percentual **válido**
(0 < PR ≤ 100)" — contando qualquer documento não vazio, o número seria ~44%.
Vale explicitar "com percentual válido" na nota numa edição futura.

**Ressalva 5 (cosméticos) — FECHADA.** Verificado no navegador: CNPJ mascarado
(`60.398.369/0004-79`, `08.662.033/0001-09` — zero à esquerda preservado sob a
máscara) nas tabelas, na ficha e no Raio-X; seletor da ficha lista **400/400**;
iterei **as 60 empresas** do Raio-X por script e não encontrei literais
`false`/`None`/`NaN`/`undefined` em nenhum caminho; `--warn` do tema claro é
`#A05910` — medi contraste 4,84 / 5,11 / 5,34 sobre os três fundos, todos ≥ 4,5
(AA). O tema escuro mantém `#C0762C`, correto para fundo escuro.

## Notas finais (ajuste sobre R.8.4)

Rastreabilidade **9 → 10** (âncoras do bruto dentro do gate + delta HTML×JSON
documentado — não resta nada que eu tenha pedido); consistência conceitual
**8 → 9** (decomposição das três coberturas nas duas lentes, verificada por gate;
retém a observação de redação da lente 4); clareza **8 → 9** (máscara de CNPJ,
literais eliminados, contraste AA). Demais dimensões inalteradas.
**Média final: 9,0.**

## Situação final

# APROVADO COM RESSALVAS — todas as ressalvas de R.8 FECHADAS

O que resta são pendências declaradas, não defeitos: a validação do backtest
continua limitada a um evento robusto (limitação honesta e escrita no próprio MD);
o pareamento por público-alvo/segmento é trabalho futuro; "sinais encerrados"
depende da disciplina de snapshot entre edições; e a observação de redação da
lente 4 acima. Nenhuma condiciona a publicação. O veredito de R.8.5 fica mantido
com as ressalvas dadas por cumpridas — na prática, o mais próximo de uma aprovação
plena que este auditor emite para um artefato vivo.

*Verificação executada em 18/08/2026 sobre `09ab150`. Gate reexecutado
independentemente (51/51); Fisher e coberturas recalculados; navegador varrido
nas 8 abas e nas 60 fichas de empresa.*
