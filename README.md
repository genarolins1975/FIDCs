# Panorama Auditável do Mercado Brasileiro de FIDCs

Corte: **30/06/2026** · Extração: 17/08/2026 · Fonte primária: CVM Dados Abertos.

| Entregável | Onde |
|---|---|
| 1. Relatório executivo | `relatorio/relatorio_executivo.md` |
| 2. Base analítica (CSV/Parquet) | `data/analytic/` |
| 3. Livro de evidências | `auditoria/livro_evidencias.csv` |
| 4. Código reproduzível | `scripts/01`…`06` + `docs/metodologia.md` |
| 5. Especificação do painel | `docs/painel_executivo.md` |
| 6. Auditoria (testes, espelhos, parecer) | `data/analytic/testes_auditoria.csv`, `auditoria/` |
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
```

Os dados brutos (`data/raw/`, `data/duckdb/`) não são versionados; o manifesto
com SHA-256 garante reprodutibilidade bit a bit contra o portal da CVM
(observação: a CVM substitui arquivos em reapresentações — o manifesto
registra a versão utilizada).
