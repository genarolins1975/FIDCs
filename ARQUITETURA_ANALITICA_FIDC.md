# Arquitetura analítica — Panorama FIDC Brasil v2

Documento de arquitetura da reconstrução determinada pela `AUDITORIA_PAINEL_FIDC.md`.
Princípio de projeto: **manutenível por uma pessoa**. Sem microserviços, sem
orquestradores distribuídos, sem streaming. Python + DuckDB + Parquet + HTML
estático, tudo versionado em git.

## 1. Mudança conceitual: de tabela para grafo

O painel v1 era um conjunto de rankings. O v2 modela um **grafo de relações
econômicas** e apresenta recortes dele:

```
grupo econômico → empresa → operação → FIDC → classe → subclasse
                                        ↓
        direitos creditórios → cedente/originador → sacado/devedor
                                        ↓
                    cotistas → prestadores → eventos (CVM, BCB, judiciais)
```

**Nós (entidades) e a chave estável de cada um**

| Entidade | Chave | Fonte da chave | Observação |
|---|---|---|---|
| Fundo | CNPJ do fundo | registro_fundo | regime pré e pós RCVM 175 |
| Classe | CNPJ da classe | registro_classe | unidade reportante do informe hoje |
| Subclasse | ID_Subclasse | registro_subclasse | **não reporta informe próprio** — nunca somada |
| Gestor / Administrador / Custodiante / Controlador / Auditor | CNPJ | informe + registro | papéis distintos, nunca fundidos |
| Cedente / originador | CNPJ ou CPF | informe tab I | CPF **não** é resolvido nem exibido |
| Sacado / devedor | — | tab VIII | **sem identificador**: só concentração |
| Cotista | categoria | tabs X_1/X_1_1 | identidade não pública; valor por série em X_2 |
| Empresa / grupo econômico | CNPJ (raiz para grupo) | Receita Federal | agrupamento por raiz exige validação societária |
| Processo judicial | número CNJ | DataJud | casamento com empresa só por CNPJ |
| Processo sancionador | número do processo CVM | CVM | com status processual obrigatório |

**Arestas (relações)** carregam sempre: papel, período de vigência, valor (quando
aplicável), fonte, e nível de evidência.

## 2. Camadas do pipeline

```
data/raw/          ← imutável, com manifesto (URL + SHA-256 + timestamp)
   ↓  scripts/01_download.py            extração
data/raw/extracted/ ← descompactado
   ↓  scripts/02, 02b, 11b              carga (18 tabelas do informe + cadastro)
data/duckdb/fidc.db ← camada de integração (tabelas espelho + views canônicas)
   ↓  scripts/03, 09, 11, 13, 14        camada analítica
data/analytic/*.csv|*.parquet ← artefatos publicáveis, um por indicador
   ↓  scripts/05, 15                    testes e backtest
   ↓  scripts/07                        renderização estática
relatorio/painel_executivo.html ← artefato final (sem backend)
```

**Views canônicas** (definidas em `03_analytics.py`, reutilizadas por todos):
- `painel` — dedup fundo × classe (regras i-ii da metodologia);
- `pl_outliers` / `painel_saneado` — exclusão logada de erro grosseiro de preenchimento;
- `gestor_veiculo` — gestor vigente por veículo, com dedup **após** a união dos regimes.

## 3. Regras invioláveis da camada de dados

1. **Ausência ≠ zero.** Campo não reportado permanece `NULL`; indicadores que
   dependem dele marcam o veículo como *não avaliável* e isso entra na
   **cobertura**. Nenhum denominador recebe zero por conveniência
   (`CASE WHEN d > 0 THEN n/d END`, nunca `n/COALESCE(d,0)`).
2. **Unidade declarada.** Todo agregado declara se soma fundos, classes ou
   veículos informantes. Subclasses jamais entram na soma.
3. **Dedup antes de agregar.** Toda tabela 1-linha-por-veículo é deduplicada por
   (CNPJ, competência) com log; toda união de regimes deduplica **depois** da união.
4. **Casamento por identificador.** Entidades se ligam por CNPJ. Correspondência
   por nome, quando inevitável, é rotulada "requer validação humana" e não
   sustenta afirmação.
5. **Nada de literal numérico na apresentação.** Todo número exibido vem de um
   artefato calculado; teste automatizado falha se sobrar número escrito à mão.

## 4. As nove lentes de exposição

Substituem o ranking único de "maiores participantes". Cada lente tem ficha em
`data/analytic/lentes_catalogo.csv` com definição, numerador, denominador,
unidade, cobertura, limitação e **o que a lente não significa**.

| # | Lente | Unidade | Cobertura no corte |
|---|---|---|---|
| 1 | PL sob gestão | gestor | 100,0% do PL (491 entidades) |
| 2 | PL sob administração fiduciária | administrador | 100,0% do PL (52) |
| 3 | Exposição da carteira (direitos creditórios) | fundo/classe | 100% (4.327) |
| 4 | Exposição a cedente/originador | cedente (CNPJ) | 29,4% do estoque de DC |
| 5 | Exposição a sacado/devedor (concentração) | fundo/classe | 69,3% dos veículos |
| 6 | Exposição do cotista | série de cota | 100% |
| 7 | Dependência corporativa de FIDC | empresa/grupo | não é censo (8 entidades) |
| 8 | Exposição operacional (prestadores) | papel × entidade | varia por papel |
| 9 | Exposição em recuperação judicial | empresa × operação | ver monitor de RJ |

## 5. Red flags: taxonomia e score decomposto

Oito pilares (qualidade do ativo; estrutura e subordinação; concentração;
governança e conflitos; integridade de dados; risco judicial/regulatório;
inconsistências contábeis; PLD-FTP e lastro). Cada sinal tem ficha completa em
`docs/METODOLOGIA_RED_FLAGS.md` — incluindo **explicações benignas** e ação de
investigação recomendada.

O score **nunca** é um número único. São seis dimensões publicadas lado a lado:

| Dimensão | O que mede |
|---|---|
| Score de risco | soma ponderada por severidade dos sinais disparados |
| Materialidade financeira | R$ sob o sinal |
| Força da evidência | proporção de sinais de campo observado vs derivado |
| Cobertura de dados | % dos sinais avaliáveis para aquele veículo |
| Persistência | meses consecutivos |
| Atualidade | competência do sinal mais recente |

Veículos com cobertura < 50% são **"não classificáveis"** — jamais "baixo risco".
A metodologia é rotulada **experimental** enquanto o backtest não validar pesos.

## 6. Backtest

Biblioteca de casos confirmados por fonte oficial (PAS CVM, liquidações BCB,
falências). Regra anti-vazamento: para um evento em T, o sinal só pode usar
informação disponível até T−1. Métricas: precisão no topo do ranking,
antecedência mediana do sinal, taxa de falso positivo contra controles negativos
(veículos comparáveis sem evento), e estabilidade dos limiares.

## 7. Auditabilidade

Cada indicador publicado carrega um registro em `auditoria/livro_evidencias.csv`
(claim_id, definição, valor sem arredondamento, fórmula, numerador/denominador,
fonte, URL, tabela e campo, data-base, data de extração, hash do arquivo,
tratamento de ausências, cobertura, status observado/calculado/estimado/inferido,
nível de confiança). No painel, cada número abre a gaveta com esse conteúdo e
permite exportar os registros que o compõem.

## 8. Operação e atualização

- Cadência: mensal, disparada pela publicação do informe (a CVM republica o mês
  corrente por ~25 dias; ver `SCHEMA_CHANGELOG.md`).
- Snapshot versionado: cada execução grava manifesto próprio; diffs de hash
  identificam reapresentações silenciosas.
- Competência de referência: a **última completa**; competências ainda em janela
  de entrega entram apenas como observação parcial, com contagem de faltantes.
- Custo: execução completa em minutos, ~200 MB de dados brutos, zero serviços.
