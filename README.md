# Panorama Auditável do Mercado Brasileiro de FIDCs

Corte: **30/06/2026** · Extração: 17/08/2026 · Fonte primária: CVM Dados Abertos.

**Painel reconstruído (v2):** `relatorio/painel_fidc_v2.html` — seis telas, nove
lentes de exposição, 46 sinais de atenção e evidência auditável em cada número.

| Entregável | Onde |
|---|---|
| 0. Auditoria forense do painel anterior | `AUDITORIA_PAINEL_FIDC.md` |
| 0b. Arquitetura analítica | `ARQUITETURA_ANALITICA_FIDC.md` |
| 0c. Dicionário de dados (gerado) | `DICIONARIO_DADOS_FIDC.md` |
| 0d. Matriz de fontes e cobertura | `MATRIZ_FONTES_COBERTURA.csv` |
| 0e. Changelog de schema (gerado) | `SCHEMA_CHANGELOG.md` |
| 0f. Metodologia de red flags | `docs/METODOLOGIA_RED_FLAGS.md` |
| 0g. Backtest dos sinais | `BACKTEST_RED_FLAGS.md` |
| 0h. Metodologia de recuperação judicial | `docs/METODOLOGIA_RECUPERACAO_JUDICIAL.md` |
| 0i. Base normativa | `docs/BASE_NORMATIVA_FIDC.md` |
| 0j. Limitações e riscos jurídicos | `docs/LIMITACOES_E_RISCOS_JURIDICOS.md` |
| 0k. Changelog do redesign | `CHANGELOG_REDESIGN.md` |
| 0l. Validação humana pendente | `VALIDACAO_HUMANA_PENDENTE.md` |
| 1. Relatório executivo | `relatorio/relatorio_executivo.md` |
| 2. Base analítica (CSV/Parquet) | `data/analytic/` |
| 3. Livro de evidências | `auditoria/livro_evidencias.csv` |
| 4. Código reproduzível | `scripts/01`…`06` + `docs/metodologia.md` |
| 5. Especificação do painel | `docs/painel_executivo.md` |
| 6. Auditoria (testes, espelhos, parecer) | `data/analytic/testes_auditoria.csv`, `auditoria/` |
| 7. Red flags v2 (46 sinais, 8 pilares) | `data/analytic/rf2_*.csv` + `docs/METODOLOGIA_RED_FLAGS.md` |
| Manifesto de fontes (URL+SHA-256) | `manifesto_fontes.csv` |

## Reprodução

```bash
pip install pandas duckdb pyarrow requests
python3 scripts/01_download.py             # ~170 MB da CVM + manifesto
python3 scripts/02_build.py                # DuckDB + parquet
python3 scripts/02b_build_series_classes.py
python3 scripts/03_analytics.py            # séries, rankings, alertas
python3 scripts/04_cedentes_nomes.py       # resolução de entidades
python3 scripts/05_testes_auditoria.py     # 18 testes obrigatórios
python3 scripts/06_livro_evidencias.py
python3 scripts/11_tab_viii_sacados.py      # concentração por devedor (tab VIII)
python3 scripts/11b_tabelas_faltantes.py    # tabs III, IX, X_6, X_7
python3 scripts/12_monitor_rj.py            # recuperação judicial (DataJud + cadastro)
python3 scripts/13_red_flags_v2.py          # 46 sinais em 8 pilares
python3 scripts/14_lentes_exposicao.py      # nove lentes de exposição
python3 scripts/15_matriz_fontes_schema.py  # matriz de fontes + schema changelog
python3 scripts/16_painel_dados.py          # compila indicadores + evidências
python3 scripts/17_painel_v2.py             # renderiza o painel
python3 scripts/18_backtest.py              # backtest dos sinais
python3 scripts/19_dicionario_dados.py      # dicionário de dados
```

A taxonomia de red flags v2 (`scripts/13_red_flags_v2.py`) substitui a triagem
de 5 sinais de `scripts/10_red_flags.py`. Ela é **experimental**: os pesos por
severidade não foram validados por backtest, e score alto não significa
irregularidade — ver o aviso e a seção de limitações em
`docs/METODOLOGIA_RED_FLAGS.md`.

Os dados brutos (`data/raw/`, `data/duckdb/`) não são versionados; o manifesto
com SHA-256 garante reprodutibilidade bit a bit contra o portal da CVM
(observação: a CVM substitui arquivos em reapresentações — o manifesto
registra a versão utilizada).
