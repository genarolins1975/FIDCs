# Parecer do Auditor-Chefe Independente (Agente 0E)

**Objeto:** "Panorama Auditável do Mercado Brasileiro de FIDCs" — relatório, metodologia,
bases analíticas e trilha de auditoria no repositório `/home/user/FIDCs`
(estado auditado: commit `cbe2022`, "Correções da auditoria espelho", 17/08/2026).
**Data do parecer:** 17/08/2026.
**Independência:** este auditor não produziu nenhum número, ranking ou texto do
trabalho auditado. Todos os testes abaixo foram executados com código próprio
(pandas, leitura direta dos CSVs brutos da CVM em `data/raw/extracted/`), sem
reutilizar os scripts do executor nem os códigos dos espelhos.

---

## 1. Escopo do exame

1. `relatorio/relatorio_executivo.md` (versão pós-correções);
2. `docs/metodologia.md`;
3. `data/analytic/testes_auditoria.csv` (18 testes re-executados);
4. Pareceres dos dois agentes espelho (`parecer_espelho_mercado.md`,
   `parecer_espelho_carteiras.md`), ambos "aprovado com ressalvas", e a
   verificação de que as ressalvas materiais foram efetivamente corrigidas;
5. `manifesto_fontes.csv` e `auditoria/livro_evidencias.csv`;
6. Amostra de claims do livro de evidências recalculada contra os brutos;
7. Diff do commit de correção (`git show cbe2022`) para confirmar que as
   correções declaradas correspondem a mudanças reais de código e de dados.

## 2. Testes realizados por este auditor (com resultados)

### 2.1 Reprodução integral da série mensal (163 competências)

Reimplementei do zero as regras declaradas na metodologia (dedup por
CNPJ×competência com prevalência de `Classe`; regra fundo-com-classe-informante
via `registro_fundo`/`registro_classe`; exclusão do outlier logado em
`pl_saneamento_excluidos.csv`) e recalculei PL e nº de veículos para **todas as
163 competências** diretamente dos 97 arquivos `tab_IV` da CVM.

- **PL: 0 de 163 competências divergem além da tolerância de 0,1%** da série
  publicada (`serie_mercado_mensal.csv`); divergência máxima: **0,0011%**.
- **nº de veículos: idêntico em 161 de 163 meses**; ±1 veículo em 2026-05 e
  2026-07, atribuível a diferença marginal de mapa na regra (ii) — imaterial.
- Pontos citados pelos espelhos, reconferidos por mim: dez/2013 = **430
  veículos / R$ 84.521.499.149,37**; jun/2025 = 3.592 / R$ 857,92 bi;
  dez/2025 = **4.013 / R$ 919.272.959.225,64**; corte jun/2026 = **4.327 /
  R$ 999.497.428.095,20** — todos exatos contra a série publicada.

**Conclusão: o fan-out do join (ressalva material B1 do espelho de mercado) foi
eliminado na raiz.** A série publicada agora coincide com a contagem direta dos
brutos sob as regras declaradas.

### 2.2 Verificação das quatro correções pós-espelho

| Correção exigida | Verificação deste auditor | Status |
|---|---|---|
| (a) fan-out da série / dedup na origem | Teste 2.1 (0/163 fora da tolerância); `dedup_log.csv` publicado (211 duplicatas em `ativo`, 504 em `cedentes` etc.); diff de `scripts/02_build.py` mostra `dedup_veiculo()` por (CNPJ, DT_COMPTC) e registro explícito dos DataFrames (`con.register("pl_df",…)`), eliminando o name-shadowing do `CREATE OR REPLACE TABLE x AS SELECT * FROM x` | **Aplicada** |
| (b) sobreposição fundo×classe na metodologia | `docs/metodologia.md` §2 e relatório §3 agora dizem "1 caso, R$ 10,5 mi" (antes: "3 casos, R$ 0,13 bi"); consistente com o RIZA KRATOS identificado pelos dois espelhos | **Aplicada** |
| (c) cobertura do ranking de cedentes | `cedentes_cobertura.csv` publicado (208,81 bi / 709,74 bi = 29,42%); **recalculei com código próprio: 29,42% exato** com a regra declarada (0<PR≤100, doc ≥11 dígitos); número incorporado ao relatório §8 e à metodologia §3 | **Aplicada** |
| (d) dupla atribuição de co-gestão | `cobertura_ranking_gestores` = 1,0000000000000009 (antes 1,0000289); os 3 veículos sem gestor mapeável (R$ 57,6 mi) aparecem como linha sem rótulo no ranking, sem dupla contagem | **Aplicada** |

### 2.3 Amostra de claims do livro de evidências (recalculados dos brutos)

Recalculei 5 claims (acima do mínimo de 3 exigido), com código próprio:

| Claim | Publicado | Meu recálculo | Resultado |
|---|---|---|---|
| C003 circularidade intramercado | R$ 161,6 bi | R$ 161.642.694.492,30 | **confere ao centavo** |
| C010 PL em veículos exclusivos | R$ 153,0 bi | R$ 152.989.756.579,13 (+ interesse único R$ 135,8 bi) | **confere** |
| C007 nº de cotistas | 461,5 mil | 461.515 | **confere exato** |
| C015 estrutura de capital | 68,5% / 7,4% / 24,1% | 68,5% / 7,4% / 24,1% (R$ 685,1 / 73,8 / 241,0 bi) | **confere** |
| C020 aquisições de DCs 2025 | R$ 1.874 bi | R$ 1.873,9 bi | **confere** |

Adicionalmente: top-6 do ranking de cedentes reproduzido ao centavo (Petrobras
R$ 55.377.736.586, CloudWalk, BRF Energia, QI SCD, Cielo, Marée); SCR
(AA+A = 79,9%, H = 3,8%), liquidez (≤30d = R$ 130,3 bi; >360d = R$ 179,5 bi),
cotistas por categoria (todas as 10 contagens citadas no relatório §9),
tabela do relatório §4 (todas as 8 linhas × 4 colunas contra a série),
captação líquida anual, HHI de veículos (0,007448) e razões de crescimento
(11,8× nominal; 5,9× real; +16,5% 12m — atualizado corretamente após o
conserto da série) — todos conferem com os artefatos.

### 2.4 Manifesto e integridade

- 34/34 arquivos-fonte presentes em `data/raw/`;
- **SHA-256 recalculado por mim em amostra de 6 arquivos: 6/6 conferem** com o
  manifesto (incl. `inf_mensal_fidc_202606.zip` e `registro_fundo_classe.zip`);
- `testes_auditoria.csv`: 18 testes, 15 PASS e 3 WARN (T4 cancelados, T5 PL
  negativo, T14 ANBIMA), 0 FAIL; os WARN estão tratados no relatório.

### 2.5 Critérios de reprovação do mandato — checagem explícita

- *Número sem fonte*: não encontrado em nível material (ver ressalvas §6 para
  3 casos menores de amarração relatório×artefato);
- *Entidade sem CNPJ*: rankings e cedentes carregam CNPJ de 14 dígitos; nomes
  do top-30 do relatório conferidos por mim contra `cedentes_ranking_nomes.csv`
  (Vale, J&F, GM, Stellantis, Hyundai, Gazin, BMG, Creditas, SumUp etc. — todos
  presentes com CNPJ e razão social da Receita);
- *Confusão de papéis*: não encontrada — administrador, gestor, custodiante,
  cedente e cotista têm fontes e tabelas distintas, e o relatório distingue
  explicitamente (ex.: "QI/BMP concentram originação, não gestão");
- *Dupla contagem material não tratada*: não encontrada após as correções
  (série, fundo×classe, circularidade, co-gestão — todas verificadas);
- *Associação por nome de fundo*: a única inferência por denominação (flag
  "NP") está marcada como **[I]**; a exposição Petrobras deriva de campo de
  CNPJ do informe (anti-inferência confirmada pelo espelho de carteiras e
  compatível com meu recálculo);
- *Rankings não reproduzíveis*: reproduzi cedentes e concentração; os espelhos
  reproduziram administradores, gestores e maiores veículos ao centavo;
- *Divergências relevantes omitidas*: ANBIMA (+17,2%) declarada como [CF] com
  decomposição de perímetro; quebra RCVM 175 declarada.

**Nenhum critério de reprovação está configurado.**

## 3. Cobertura das bases

- 163 competências (jan/2013–jul/2026), ~234 mil observações veículo-mês;
  corte 30/06/2026 com 4.327 veículos (4.309 classes + 18 fundos legado);
- Cedentes: cobertura de **29,4% do estoque de DCs** (agora publicada e
  declarada como piso; 60% dos veículos sem cedente válido informado);
- Gestores: 100,0% do PL atribuído (3 veículos residuais sem gestor, 0,006%);
- SCR: subconjunto reportado (R$ 362 bi), corretamente rotulado como parcial;
- Par 6 do mandato (cotas de FIDC em balanços de companhias): **não executado**,
  declarado como lacuna — tratamento correto (declarar, não estimar).

## 4. Limitações (avaliação do tratamento)

As limitações declaradas na metodologia §6 (sacados não identificáveis;
valores por cotista não públicos; cedentes top-9 como piso; gestor histórico
não rastreado; dados autodeclarados; perímetro ANBIMA) são reais, corretamente
classificadas ([NI]/[CF]/[I] no relatório) e — ponto decisivo — **nenhuma
conclusão do relatório depende de dado declarado como não disponível**. As
perguntas do mandato sem resposta pública (Q3 valores de subordinada por
detentor, Q5 baixa contábil, Q10) são respondidas com "[NI]", não com estimativa
disfarçada.

## 5. Divergências conhecidas e seu tratamento

- **CVM × ANBIMA (+17,2%)**: declarada em T14 (WARN), no relatório §4 e §14, com
  explicação de perímetro (FIC-FIDC + cobertura associativa) e classificação
  [CF]. Tratamento adequado; ver §7 sobre arquivamento.
- **Captação líquida CVM × ANBIMA**: declarada como bruta de dupla contagem
  intramercado, "ordem de grandeza". Adequado.
- **Denominadores heterogêneos** (DC da tab I = 709,7 bi × tab V/VI = 708,4 bi,
  gap ~0,2%): implícito na metodologia; o espelho de carteiras recomendou nota
  única de conciliação — permanece disperso (menor).

## 6. Erros corrigidos durante o trabalho (achados do processo espelho→correção)

O ciclo executor→espelho→correção funcionou como desenhado e deve ser registrado
como parte do resultado:

1. **Fan-out do join da série** (achado material do espelho de mercado): a query
   da série fazia `LEFT JOIN` com a tab_I sem dedup, reintroduzindo dupla
   contagem em 29/163 competências (até +0,66%; todo o ano de 2025 com
   +R$ 2–3 bi/mês). Corrigido na raiz: dedup por (CNPJ, competência) nas tabelas
   de 1 linha/veículo no build, com log público (`dedup_log.csv`). **Verificado
   por mim: série agora bate com a contagem direta em 163/163 meses.**
2. **Bug de name-shadowing no DuckDB**: `CREATE OR REPLACE TABLE x AS SELECT *
   FROM x` resolvia `x` para a tabela antiga do banco, não para o DataFrame
   homônimo — o rebuild silenciosamente preservava dados velhos. Corrigido com
   `con.register()` explícito de DataFrames com nomes distintos. Achado de
   processo relevante: sem os espelhos, esse bug seria invisível aos testes
   (T3 auditava a view correta e dava falso conforto).
3. **Sobreposição fundo×classe** na metodologia: corrigida para o valor
   reproduzível (1 caso, R$ 10,5 mi).
4. **Dupla atribuição de co-gestão** (~R$ 28,9 mi): eliminada; cobertura do
   ranking de gestores agora é exatamente 100%.

## 7. Riscos residuais e pontos não verificáveis

**Ressalvas deste auditor (nenhuma bloqueante):**

- **R1 — Dois HHIs do relatório não amarram ao artefato.** Relatório §11 diz
  HHI por administrador = 0,079 e por gestor = 0,017; `concentracao_indicadores.csv`
  (e meu recálculo a partir dos rankings publicados) dá **0,0754** e **0,0209**.
  A leitura qualitativa ("moderado"/"baixo") não muda, mas os números impressos
  não são reproduzíveis dos artefatos. Corrigir antes de distribuição ampla.
- **R2 — Contagens de veículos de cedentes desatualizadas no relatório.** Após a
  correção da regra (PR>0), o CSV diz QI SCD = **72** e BMP SCD = **91**
  veículos; o relatório cita 73 e 92 em três passagens (§1.6, §8 tabela, §8
  texto). Diferença de ±1, imaterial, mas inconsistente com o artefato publicado.
- **R3 — Recompras 2025**: relatório §10 diz "R$ 29,6 bi"; artefato e livro de
  evidências (C021) dizem R$ 29,5 bi. Arredondamento defasado.
- **R4 — Arquivamento incompleto de fontes não-CVM.** O manifesto SHA-256 cobre
  apenas os 34 arquivos CVM. Resoluções 175/200/240, IPCA/SGS e o dado ANBIMA
  (R$ 852,7 bi, obtido "via imprensa") não têm arquivo com hash; as URLs de
  C023–C025 no livro de evidências apontam genericamente para o diretório de
  dados da CVM. **O número ANBIMA não é verificável por este auditor** — está
  corretamente rotulado [CF] e usado só como validação externa, mas deveria ser
  arquivado com fonte precisa.
- **R5 — Higiene de artefatos**: (i) doc malformado `00000000000191` (R$ 92,4
  mi, posição ~222) segue sem flag em `cedentes_ranking_estimado.csv` (fora do
  top-150 nomeado); (ii) `negocios_anual.csv` traz recompras de 2013 =
  R$ 292 trilhões — erro de preenchimento do bruto sem filtro de sanidade
  (não citado no relatório, mas o artefato pode induzir erro de leitor);
  (iii) um FIDC aparece como cedente na posição ~47 do ranking de nomes
  (legítimo, porém sem marcação de que é veículo do próprio universo).
- **R6 — Ranking de administradores bruto de circularidade** (ressalva B4 do
  espelho, não implementada): 31% do PL do 1º colocado (BTG) e 21% do 2º (QI)
  são cotas de outros FIDCs do universo; a visão líquida existe no agregado,
  mas não por administrador. Ressalva de apresentação — a leitura competitiva
  do topo muda na visão líquida.

**Pontos estruturalmente não verificáveis** (limitação de fonte, não do
trabalho): identidade de sacados; valores por cotista; retenção subordinada por
grupo econômico em valor; percentuais de cedente autodeclarados sem auditoria
individual (a manchete "Petrobras maior cedente" depende de um único campo
autodeclarado de um único informe — corretamente marcada [FS], não [C]).

## 8. Notas nas 10 dimensões do mandato (0–10)

| # | Dimensão | Nota | Fundamento |
|---|---|---:|---|
| 1 | Completude | 9,0 | 163/163 competências; todos os artefatos prometidos; Par 6 declarado como lacuna em vez de estimado. |
| 2 | Precisão | 9,0 | Série 163/163 dentro da tolerância (máx 0,0011%); corte, rankings e 5 claims ao centavo; residuais R1–R3 imateriais. |
| 3 | Rastreabilidade | 8,0 | Manifesto SHA-256 (6/6 na minha amostra), livro de evidências, logs de dedup e saneamento; descontos por R1 e R4 (fontes não-CVM sem hash, URLs genéricas em 3 claims). |
| 4 | Consistência conceitual | 9,0 | Papéis nunca confundidos; unidade "veículo informante" bem definida; circularidade conceituada e medida; denominadores heterogêneos declarados. |
| 5 | Reprodutibilidade | 9,5 | Reproduzi série, corte, cobertura e claims com código independente só a partir da metodologia declarada; pipeline público e determinístico. |
| 6 | Tratamento de duplicidades | 9,0 | Fan-out corrigido na raiz e verificado; dedup logado; fundo×classe, co-gestão e circularidade controlados; resta apresentação (R6). |
| 7 | Resolução de entidades | 9,0 | CNPJ 14 dígitos + Receita; DV validado (espelho) e nomes do top-30 conferidos por mim; 1 doc inválido residual sem flag (R5). |
| 8 | Tratamento das limitações | 9,0 | Cobertura de 29,4% publicada; classificação C/FS/I/NI/CF usada com disciplina; nenhuma conclusão apoiada em dado indisponível. |
| 9 | Clareza | 9,0 | Relatório hierarquizado, tabelas amarradas a artefatos nomeados, sinais de confiança em cada claim. |
| 10 | Utilidade econômica | 9,0 | Distingue funding × transferência de risco, mede circularidade e retenção de primeiro risco, responde as 12 perguntas do mandato (ou declara NI); agenda de monitoramento acionável. |

**Média: 9,0.**

## 9. OPINIÃO FINAL

# APROVADO COM RESSALVAS

O trabalho **pode ser publicado**. As duas ressalvas materiais dos agentes
espelho (dupla contagem na série histórica por fan-out de join e o número não
reproduzível de sobreposição fundo×classe) foram **corrigidas na raiz e
verificadas de forma independente por este auditor**, que reproduziu a série
completa (163/163 competências dentro da tolerância), o corte ao centavo, a
cobertura de cedentes (29,42% exato) e uma amostra de cinco claims do livro de
evidências, além de conferir a integridade do manifesto por hash. Nenhum
critério de reprovação do mandato está configurado.

As ressalvas remanescentes (R1–R6 do §7) são de amarração fina relatório×
artefato, arquivamento de fontes acessórias e higiene de arquivos — nenhuma
altera conclusão, ranking ou ordem de grandeza. Recomenda-se saná-las na
primeira revisão, priorizando: (i) os dois HHIs do §11 do relatório; (ii) as
contagens 73/92 → 72/91; (iii) o arquivamento com hash das fontes ANBIMA,
resoluções e IPCA; e (iv) a visão líquida de circularidade no ranking de
administradores.

*Todos os números deste parecer foram recalculados nesta sessão com código
próprio sobre os brutos da CVM; nenhum foi aceito por afirmação do executor ou
dos espelhos sem verificação.*
