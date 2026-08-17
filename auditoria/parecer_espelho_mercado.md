# Parecer do Agente Espelho — Par 2/3 (mercado: tamanho, séries e rankings)

**Escopo auditado:** `serie_mercado_mensal.csv`, `ranking_administradores.csv`,
`ranking_gestores.csv`, `maiores_veiculos.csv`, `concentracao_indicadores.csv`,
contra os CSVs brutos da CVM em `data/raw/extracted/` e as regras declaradas em
`docs/metodologia.md`.
**Método:** reprodução independente, com código próprio (pandas), sem reutilizar
os scripts do executor. Os scripts do executor foram lidos apenas *a posteriori*,
para diagnosticar a causa-raiz das divergências já medidas.
**Data do parecer:** 17/08/2026.

---

## (a) O que foi reproduzido e com que código

### A1. PL total e nº de veículos no corte 30/06/2026 (Tarefas 1 e 2)

Apliquei eu mesmo as duas regras de dedup declaradas na metodologia (§2):
(i) CNPJ presente como `Fundo` e `Classe` na mesma competência → prevalece
`Classe`; (ii) linha `Fundo` cujo fundo tem classe com CNPJ próprio informando
na mesma competência → excluída (mapa fundo×classe construído por mim a partir
de `registro_fundo.csv` + `registro_classe.csv`, `Tipo_Fundo LIKE '%FIDC%'`,
chave `ID_Registro_Fundo`).

```python
import pandas as pd
RAW = "/home/user/FIDCs/data/raw/extracted/"
def rd(f): return pd.read_csv(RAW+f, sep=";", encoding="latin-1", quoting=3, dtype=str)
def digits(s): return s.str.replace(r"\D", "", regex=True).str.zfill(14)

t4 = rd("inf_mensal_fidc_tab_IV_202606.csv")
t4 = t4[t4.DT_COMPTC == "2026-06-30"].copy()
t4["cnpj"] = digits(t4.CNPJ_FUNDO_CLASSE)
t4["pl"] = pd.to_numeric(t4.TAB_IV_A_VL_PL, errors="coerce")

# regra (i)
both = set(t4.loc[t4.TP_FUNDO_CLASSE=="Fundo","cnpj"]) & set(t4.loc[t4.TP_FUNDO_CLASSE=="Classe","cnpj"])
t4 = t4[~((t4.TP_FUNDO_CLASSE=="Fundo") & t4.cnpj.isin(both))]

# regra (ii) — mapa fundo->classes via registro CVM
rf = rd("registro_fundo.csv"); rc = rd("registro_classe.csv")
rf = rf[rf.Tipo_Fundo.str.contains("FIDC", case=False, na=False)]
mapa = rc.merge(rf[["ID_Registro_Fundo","CNPJ_Fundo"]], on="ID_Registro_Fundo")
mapa["cf"] = digits(mapa.CNPJ_Fundo); mapa["cc"] = digits(mapa.CNPJ_Classe.fillna(""))
f2c = mapa.groupby("cf")["cc"].apply(set).to_dict()
infc = set(t4.loc[t4.TP_FUNDO_CLASSE=="Classe","cnpj"])
r2 = t4[(t4.TP_FUNDO_CLASSE=="Fundo")
        & t4.cnpj.map(lambda c: any(k!=c and k in infc for k in f2c.get(c,set())))]
t4 = t4.drop(r2.index)
print(len(t4), t4.pl.sum())
```

Resultado meu × executor (corte 30/06/2026):

| métrica | meu cálculo | executor | diferença |
|---|---|---|---|
| linhas brutas tab_IV | 4.328 (4.309 Classe + 19 Fundo) | — | — |
| regra (i) removida | 0 casos | — | — |
| regra (ii) removida | **1 caso** (RIZA KRATOS, CNPJ 66.814.472/0001-96), R$ 10.478.306,21 | — | — |
| **PL total** | **R$ 999.497.428.095,20** | R$ 999.497.428.095,20 | 0,0000% (1,2e-16) |
| n_veiculos | 4.327 | 4.327 | 0 |
| n_classes / n_fundos | 4.309 / 18 | 4.309 / 18 | 0 |

**No corte, o PL e as contagens batem ao centavo.** Tolerância de 0,1%: atendida
com folga de 12 ordens de grandeza.

### A2. Nº de veículos 2013-12 (Tarefa 2)

Meu cálculo direto do bruto (`inf_mensal_fidc_tab_IV_2013.csv`,
`DT_COMPTC=2013-12-31`, chave `CNPJ_FUNDO`): **430 linhas, 430 CNPJs únicos,
PL R$ 84.521.499.149,37**. Executor: **n_veiculos = 431** (PL igual ao meu).
**Divergência: +1 veículo fantasma.** Causa diagnosticada: a tab_I de 2013-12
tem o fundo BONSUCESSO CRÉDITO CONSIGNADO II (14.662.609/0001-30) em linha
duplicada; o `LEFT JOIN` da série com a tabela `ativo` (tab_I) sem dedup
multiplica a linha do painel (fan-out) — ver B1.

### A3. Ranking de administradores (Tarefa 3)

Código próprio: painel canônico (A1) + `CNPJ_ADMIN`/`ADMIN` da
`inf_mensal_fidc_tab_I_202606.csv` (4.328 linhas, 4.328 CNPJs únicos, zero
veículos sem administrador), soma de PL por CNPJ do administrador.

**Resultado: top-10 idêntico posição a posição, PL exato ao centavo em todas as
10 posições, mesmo nº de veículos.** (BTG Pactual Serviços R$ 160,99 bi/437;
QI CTVM R$ 141,69 bi/819; Oliveira Trust DTVM R$ 99,92 bi/159; Daycoval
R$ 61,81 bi/417; BB Gestão R$ 61,31 bi/3; BEM DTVM R$ 52,42 bi/47; CBSF DTVM
R$ 51,88 bi/84; Genial R$ 31,79 bi/86; Intrag R$ 29,69 bi/41; Hemera
R$ 25,13 bi/131.) Diferença máxima: 0,000000%.

### A4. Ranking de gestores (Tarefa 4)

Código próprio: veículo → fundo via `registro_classe` (CNPJ da classe → CNPJ do
fundo; senão o próprio CNPJ); gestor por fundo = registro ativo mais recente
("Em Funcionamento Normal" > "Em Liquidação" > demais; depois `Data_Registro`
desc), `Tipo_Fundo LIKE '%FIDC%'`.

```python
rff = rf.copy()
rff["cnpj_fundo"] = digits(rff.CNPJ_Fundo)
rff["prio"] = rff.Situacao.map({"Em Funcionamento Normal":0, "Em Liquidação":1}).fillna(2)
rff["dt"] = pd.to_datetime(rff.Data_Registro, errors="coerce")
rff = rff.sort_values(["cnpj_fundo","prio","dt"], ascending=[True,True,False])
gestor_fundo = rff.drop_duplicates("cnpj_fundo")[["cnpj_fundo","CPF_CNPJ_Gestor","Gestor"]]
c2f = (rc.merge(rf[["ID_Registro_Fundo","CNPJ_Fundo"]], on="ID_Registro_Fundo")
         .assign(cc=lambda d: digits(d.CNPJ_Classe.fillna("")), cf=lambda d: digits(d.CNPJ_Fundo))
         .query("cc != ''").drop_duplicates("cc").set_index("cc")["cf"].to_dict())
painel["cnpj_fundo"] = painel.cnpj.map(lambda c: c2f.get(c, c))
g = painel.merge(gestor_fundo, on="cnpj_fundo", how="left")
rkg = g.groupby(digits(g.CPF_CNPJ_Gestor.fillna(""))).agg(pl=("pl","sum"), n=("cnpj","size"))
```

**Resultado: top-10 idêntico posição a posição, PL exato ao centavo nas 10
posições** (Oliveira Trust Servicer R$ 76,26 bi/45; BB Gestão R$ 61,31 bi/2;
Bradesco R$ 40,62 bi/32; BTG Asset R$ 32,91 bi/50; CBSF Trust R$ 29,82 bi/19;
Solis R$ 27,55 bi/112; Banco BTG R$ 25,30 bi/9; Genial Gestão R$ 25,22 bi/44;
Tercon R$ 23,85 bi/230; BTG Gestora Alternativos R$ 23,38 bi/19).

**Teste de dupla atribuição (co-gestão/multirregistro):**
- Minha soma de PL por gestor = R$ 999.439.830.250,20 = **99,9942%** do PL total
  (3 veículos sem gestor mapeável, R$ 57,6 mi = 0,0058%). Nenhuma dupla
  atribuição no meu método.
- Executor: soma = **100,0029%** do PL total (`cobertura_ranking_gestores =
  1,0000289`), ou seja, **~R$ 28,9 mi atribuídos em duplicidade** — o `UNION ALL`
  do mapa classe→fundo do executor permite que um CNPJ case duas vezes
  (detectei 1 CNPJ de classe mapeando para mais de um fundo distinto).
  Materialidade: 0,003% do PL — **imaterial**, não altera nenhuma posição do
  top-10, mas contradiz o §5 da metodologia ("cobertura do ranking = 100,0%")
  se lido como igualdade estrita; o próprio executor publica o 1,0000289 em
  `concentracao_indicadores.csv`, o que é transparente.

### A5. Duplicidade nos resultados publicados (Tarefa 5)

- `maiores_veiculos.csv`: 30 linhas, **zero CNPJs duplicados**. OK.
- Rankings: agregados por CNPJ do prestador, sem duplicatas. OK.
- **Porém**, o artefato intermediário `pl.parquet` do executor contém CNPJs
  duplicados na mesma competência em **45 competências** (até 17 duplicatas/mês
  em 2025 — pares Fundo+Classe com o mesmo CNPJ e o mesmo PL, ex.: FIDC SIFRA
  STAR, 14.166.140/0001-49, 2×R$ 1,27 bi em 2025-06), e a série publicada
  **herda dupla contagem equivalente** (ver B1). O teste T3 do executor ("zero
  duplicatas, PASS") é verdadeiro apenas para a *view* `painel` deduplicada, não
  para a série publicada — dá falso conforto.

### A6. Circularidade FIC-FIDC nos top-3 administradores (Tarefa 6)

Cotas de FIDC detidas pelos veículos de cada administrador
(`TAB_I2H_VL_COTA_FIDC` + `TAB_I2I_VL_COTA_FIDC_NP` da tab_I, 2026-06,
somadas por mim sobre o painel canônico):

| administrador | PL (R$ bi) | cotas de FIDC detidas (R$ bi) | % do PL do admin |
|---|---|---|---|
| BTG Pactual Serviços Financeiros DTVM | 160,99 | **50,47** | **31,35%** |
| QI CTVM | 141,69 | **29,50** | **20,82%** |
| Oliveira Trust DTVM | 99,92 | 1,88 | 1,88% |
| (universo inteiro) | 999,50 | 161,64 | 16,17% |

**Resposta à hipótese alternativa:** sim — os PLs brutos dos dois maiores
administradores estão substancialmente inflados por dupla contagem intramercado
(FIC-FIDC dentro do universo): quase 1/3 do PL administrado pelo BTG e 1/5 do
da QI são cotas de outros FIDCs do próprio universo. Líquidos de circularidade,
BTG (R$ 110,5 bi) e QI (R$ 112,2 bi) praticamente empatam e a distância para a
Oliveira Trust (R$ 98,0 bi) cai muito. O executor **declara** o fenômeno
(coluna `cotas_fidc_detidas` na série — meu recálculo bate exato:
R$ 161.642.694.492 — e teste T11 = 16,17%), mas o `ranking_administradores.csv`
**não traz** a visão líquida de circularidade, e o ranking bruto é sensível a
ela. Ressalva de apresentação, não erro de cálculo.

### A7. Conferência de 5 veículos do `maiores_veiculos.csv` (Tarefa 7)

Contra o bruto `inf_mensal_fidc_tab_IV_202606.csv`, valor exato ao centavo:

| CNPJ | veículo | executor | bruto | igual |
|---|---|---|---|---|
| 09.195.235/0001-50 | FIDC do Sistema Petrobras | 61.254.971.563,01 | 61.254.971.563,01 | sim |
| 26.287.464/0001-14 | Tapso FIDC RL | 41.496.046.291,59 | 41.496.046.291,59 | sim |
| 65.473.848/0001-83 | Pan Auto FIDC RL | 17.971.763.062,82 | 17.971.763.062,82 | sim |
| 62.393.679/0001-83 | Cloudwalk Bela FIDC | 10.010.957.003,11 | 10.010.957.003,11 | sim |
| 53.263.761/0001-00 | Esperanza FIDC | 8.458.862.801,73 | 8.458.862.801,73 | sim |

5/5 exatos.

---

## (b) Divergências encontradas, com materialidade

### B1. [MATERIAL] Série histórica com dupla contagem em 29 competências (acima da tolerância de 0,1%)

Reproduzi a série completa (163 competências) com meu próprio código (mesma
lógica de A1, laço sobre os 97 arquivos tab_IV):

```python
for f in sorted(glob.glob("inf_mensal_fidc_tab_IV_*.csv")):
    t = rd(f); key = "CNPJ_FUNDO_CLASSE" if "CNPJ_FUNDO_CLASSE" in t.columns else "CNPJ_FUNDO"
    t["cnpj"] = digits(t[key]); t["pl"] = pd.to_numeric(t.TAB_IV_A_VL_PL, errors="coerce")
    for dt, d in t.groupby("DT_COMPTC"):
        # ... regras (i) e (ii) idênticas a A1 ...
        rows.append((dt, len(d), d.pl.sum()))
```

**30 competências divergem do executor em mais de 0,1% no PL.** Uma delas
(2016-05) é explicada e justificada: o executor excluiu o outlier INX SSPI
BONDS (R$ 101,63 bi de erro de preenchimento num fundo de R$ 25 mi), exclusão
documentada em `pl_saneamento_excluidos.csv`; aplicando a mesma exclusão, meu
número reconcilia com o dele em 4e-12. **As outras 29 são dupla contagem real
na série publicada**, sempre para cima. Extrato (meu nº × executor):

| competência | meu n | exec n | meu PL (R$) | exec PL (R$) | inflação |
|---|---|---|---|---|---|
| 2013-01-31 | 412 | 414 | 69.051.990.816 | 69.510.526.268 | **+0,664%** |
| 2013-06-30 | 415 | 417 | 93.007.240.020 | 93.447.558.063 | +0,473% |
| 2013-12-31 | 430 | 431 | 84.521.499.149 | 84.521.499.149 | 0% (só contagem) |
| 2023-12-31 | 2.404 | 2.405 | 485.359.225.502 | 486.333.590.093 | +0,201% |
| 2025-01-31 | 3.195 | 3.209 | 734.755.924.723 | 736.711.015.226 | +0,266% |
| 2025-06-30 | 3.592 | 3.607 | 857.924.084.455 | 860.314.900.078 | **+0,279% (R$ 2,39 bi)** |
| 2025-08-31 | 3.717 | 3.734 | 876.494.622.996 | 878.984.767.282 | +0,284% |
| 2025-12-31 | 4.013 | 4.027 | 919.272.959.226 | 922.411.453.702 | **+0,341% (R$ 3,14 bi)** |
| 2026-06-30 | 4.327 | 4.327 | 999.497.428.095 | 999.497.428.095 | 0,000% |

Padrão completo: 2013-01 a 2013-11 (+0,27% a +0,66%), meses esparsos de
2023-2024 (+0,12% a +0,23%), e **todo o ano de 2025** (+0,26% a +0,34%,
R$ 2,0-3,1 bi/mês). `n_veiculos` diverge em **39 competências** (até +17 em
2025-08; 431×430 em 2013-12). O corte 2026-06 e 2026-07 estão corretos
(2026-07: −1 veículo, −0,0005%, por diferença marginal de mapa na regra ii —
imaterial).

**Causa-raiz (diagnosticada lendo o SQL do executor após medir a divergência):**
a view `painel` em `scripts/03_analytics.py` aplica corretamente as regras
(i)-(ii), mas a query da série faz `LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND
a.DT_COMPTC=p.DT_COMPTC` **sem deduplicar `ativo`** (tab_I). Quando a tab_I tem
o mesmo CNPJ duas vezes (linhas literalmente duplicadas no regime antigo, ou
pares Fundo+Classe do mesmo CNPJ durante a migração RCVM 175 em 2025), o join
multiplica a linha do painel e o `SUM(p.VL_PL)` e o `COUNT(*)` contam o veículo
duas vezes — desfazendo a dedup que a própria view tinha feito. Prova ao
centavo: em 2013-01 a inflação da série (R$ 458.535.451,76) é **exatamente** a
soma dos PLs dos dois fundos com linha duplicada na tab_I (BONSUCESSO CRÉDITO
CONSIGNADO II e PARAMANA). Em 2025-06, os 15 pares Fundo+Classe de mesmo CNPJ
(SIFRA STAR, KINERET, SQUID, BARCELONA etc.) explicam R$ 2,36 bi dos R$ 2,39 bi.

**Efeitos colaterais:** as demais colunas da série nesses meses
(`dc_com_risco`, `dc_sem_risco`, `cotas_fidc_detidas`, `n_cotistas`,
`pl_total_real_jun26`) sofrem o mesmo fan-out; e a view `adm_pl` usa o mesmo
join, logo os `var_12m` do ranking de administradores (base 2025-06 inflada)
ficam levemente subestimados para administradores com fundos duplicados na
tab_I. Nenhuma posição do top-10 muda com R$ 2,4 bi distribuídos em ~15 fundos,
mas os percentuais de variação carregam o vício.

**Materialidade:** acima da tolerância de 0,1% em 29 dos 163 meses (18% da
série); pico +0,66%. Não afeta o corte, os rankings do corte, nem as conclusões
qualitativas de crescimento (o viés é pequeno e concentrado), mas a série
publicada **não é** o que a metodologia declara ("uma linha por veículo
informante", teste T3 "zero duplicatas").

### B2. [DOCUMENTAÇÃO] Número não reproduzível na metodologia (§2, regra 2)

A metodologia declara "sobreposição medida: **R$ 0,13 bi em 06/2026, 3 casos**".
Meu cálculo com a regra declarada: **1 caso** (RIZA KRATOS), **R$ 0,0105 bi**
(R$ 10.478.306,21) — e é exatamente esse valor que a série do executor de fato
excluiu no corte (bruto 999.507.906.401,41 − 10.478.306,21 = publicado
999.497.428.095,20). O "R$ 0,13 bi / 3 casos" não corresponde nem ao dado nem
ao próprio resultado do executor. Materialidade numérica nula (o número certo
foi usado); falha de rastreabilidade documental.

### B3. [MENOR] Duplicatas residuais do regime antigo não cobertas por regra

No bruto legado a própria tab_IV traz o mesmo CNPJ em linha duplicada em 4
competências (2013-03/07/08/09) e a tab_I em 25 competências (2013-2018,
2025-09). As regras declaradas (fundo×classe) não cobrem duplicata literal de
linha no regime antigo; nem o executor nem a regra declarada as removem da
tab_IV (ambos contamos 2× nesses 4 meses — ordem de centenas de milhões,
<0,5%). Recomendo regra explícita de dedup por (CNPJ, competência) também no
regime antigo.

### B4. [APRESENTAÇÃO] Ranking de administradores bruto de circularidade

Ver A6: 31% do PL do 1º colocado e 21% do 2º são cotas de outros FIDCs do
universo. O controle existe na série e no relatório (PL líquido de
circularidade), mas não no ranking por administrador, onde o efeito é mais
concentrado e muda a leitura competitiva do topo. Sugestão: coluna
`cotas_fidc_detidas` / `pl_liquido_circularidade` também em
`ranking_administradores.csv`.

---

## (c) Notas (0-10)

| dimensão | nota | justificativa |
|---|---|---|
| Completude | 9,0 | 163/163 competências, todos os artefatos prometidos, limitações declaradas; nada faltante no escopo auditado. |
| Precisão | 6,5 | Corte, rankings e top-veículos exatos ao centavo (5/5, 10/10, 10/10); mas 29 competências da série violam a tolerância de 0,1% (até +0,66%), e n_veiculos erra em 39 meses. |
| Rastreabilidade | 7,5 | Manifesto SHA-256, saneamento logado (2016-05 reconcilia em 4e-12), scripts públicos; porém o "R$ 0,13 bi / 3 casos" do §2 não é reproduzível e o T3 audita o objeto errado. |
| Consistência conceitual | 8,5 | Unidade "veículo informante" bem definida; circularidade conceituada e medida corretamente (meu recálculo bate exato); ressalva B4 de apresentação. |
| Reprodutibilidade | 9,0 | Com as regras declaradas e código independente cheguei ao centavo em tudo que está correto — a metodologia é reproduzível; a divergência da série é bug de implementação, não ambiguidade metodológica. |
| Tratamento de duplicidades | 5,0 | Regras corretas e efetivas no corte, mas a série reintroduz duplicatas via join (a falha é exatamente na dimensão que a metodologia diz controlar, com teste T3 dando falso conforto); duplicatas legadas sem regra. |

## (d) Veredito

**APROVADO COM RESSALVAS.**

Tudo o que se refere ao corte 30/06/2026 — PL total (R$ 999,50 bi), 4.327
veículos, ranking de administradores, ranking de gestores, maiores veículos e
indicadores de concentração — foi reproduzido por mim de forma independente ao
centavo, posição a posição. A metodologia declarada é sólida e reproduzível, e
os controles de circularidade estão corretos onde existem.

A ressalva principal é objetiva e corrigível: a série histórica publicada
contém dupla contagem de PL e de veículos em 29 competências (todo o ano de
2025 com +0,26% a +0,34%, R$ 2-3 bi/mês; 2013 com até +0,66%; 2013-12 com 431
veículos em vez de 430), causada por fan-out do `LEFT JOIN` com a tab_I não
deduplicada na query da série — o que contradiz o teste T3 e o §5 da
metodologia. Correção simples (deduplicar/agregar `ativo` por CNPJ+competência
antes do join, ou juntar por chave já agregada) e re-publicação da série são
condição para aprovação plena. Ressalvas secundárias: corrigir o número da
sobreposição fundo×classe no §2 da metodologia (1 caso, R$ 10,5 mi — não 3
casos, R$ 0,13 bi), declarar regra para duplicatas literais do regime antigo e
expor a circularidade também no ranking de administradores, cujos dois
primeiros colocados têm 31% e 21% do PL em cotas de outros FIDCs do universo.

*Todos os números deste parecer saíram de código próprio executado nesta
sessão sobre os brutos da CVM; nenhum foi copiado dos artefatos do executor.*
