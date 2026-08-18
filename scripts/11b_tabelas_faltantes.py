#!/usr/bin/env python3
"""
Etapa 11b — Carga das tabelas do Informe Mensal ausentes da base (achado
crítico nº 1 da AUDITORIA_PAINEL_FIDC.md).

Carrega três tabelas que nunca haviam sido processadas, todas com cobertura
de 100% dos veículos informantes:

  tab IX  — taxas de desconto (aquisição) e taxas de juros dos direitos
            creditórios, mín./média ponderada/máx., na compra e na venda,
            separadas por DC com e sem aquisição substancial de risco,
            valores mobiliários e títulos públicos. Sinal forense: preço de
            aquisição fora de mercado.
  tab X_6 — desempenho ESPERADO × REAL por classe/série. Sinal forense:
            promessa não entregue.
  tab X_7 — garantias sobre os direitos creditórios (valor e percentual).

Princípio (correção do achado crítico nº 3): ausência de informação NUNCA é
convertida em zero. Campos numéricos ausentes permanecem nulos e são
reportados como cobertura, não como valor.

Reprodução: python3 scripts/11b_tabelas_faltantes.py
"""
import glob
import os
import re
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXTRACT = os.environ.get("FIDC_EXTRACT_DIR", os.path.join(ROOT, "data", "raw", "extracted"))
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"


def files_for(tab: str):
    pat = re.compile(rf"inf_mensal_fidc_tab_{tab}_(\d{{4,6}})\.csv$")
    return [f for f in sorted(glob.glob(os.path.join(EXTRACT, "*.csv")))
            if pat.search(os.path.basename(f))]


def read_norm(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="latin1", dtype=str, quoting=3)
    if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
        df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
    df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
    return df


def load(tab: str, num_prefix: str, str_cols=(), key_extra=()) -> pd.DataFrame:
    frames, dup_total = [], 0
    for f in files_for(tab):
        df = read_norm(f)
        num = [c for c in df.columns if c.startswith(num_prefix) and c not in str_cols]
        for c in num:
            df[c] = pd.to_numeric(df[c], errors="coerce")  # ausência -> NaN, não 0
        keep = ["CNPJ", "DT_COMPTC"] + list(str_cols) + num
        keep = [c for c in keep if c in df.columns]
        sub = df[keep]
        n0 = len(sub)
        sub = sub.drop_duplicates(subset=["CNPJ", "DT_COMPTC"] + list(key_extra), keep="last")
        dup_total += n0 - len(sub)
        frames.append(sub)
    out = pd.concat(frames, ignore_index=True)
    print(f"  tab {tab}: {len(out)} linhas, {dup_total} duplicatas removidas")
    return out


def main() -> int:
    con = duckdb.connect(DB)
    print("carregando tabelas ausentes ...")

    # ---- tab IX: taxas de desconto e de juros ----
    ix = load("IX", "TAB_IX")
    con.execute("CREATE OR REPLACE TABLE taxas AS SELECT * FROM ix")

    # ---- tab X_6: desempenho esperado x real (por série) ----
    x6 = load("X_6", "TAB_X", str_cols=("TAB_X_CLASSE_SERIE",),
              key_extra=("TAB_X_CLASSE_SERIE",))
    con.execute("CREATE OR REPLACE TABLE desempenho AS SELECT * FROM x6")

    # ---- tab III: passivo (habilita a identidade contábil Ativo - Passivo = PL) ----
    iii = load("III", "TAB_III")
    con.execute("CREATE OR REPLACE TABLE passivo AS SELECT * FROM iii")

    # ---- tab X_7: garantias ----
    x7 = load("X_7", "TAB_X")
    con.execute("CREATE OR REPLACE TABLE garantias AS SELECT * FROM x7")

    for t in ("taxas", "desempenho", "garantias", "passivo"):
        con.execute(f"COPY {t} TO '{OUT}/{t}.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")

    # ---------- indicadores derivados, com cobertura explícita ----------
    # Taxa média ponderada de aquisição (compra) dos DC com aquisição
    # substancial de risco: TAB_IX_A1_1_2_COMPRA_MEDIA (% a.a. ou a.m. conforme
    # declaração do administrador — ver limitação na metodologia).
    taxas_res = con.execute(f"""
    SELECT
      COUNT(*) n_veiculos,
      COUNT(TAB_IX_A1_1_2_COMPRA_MEDIA) n_com_taxa_desconto_compra,
      ROUND(100.0*COUNT(TAB_IX_A1_1_2_COMPRA_MEDIA)/COUNT(*),1) cobertura_pct,
      ROUND(median(TAB_IX_A1_1_2_COMPRA_MEDIA),3) mediana_desconto_compra,
      ROUND(quantile_cont(TAB_IX_A1_1_2_COMPRA_MEDIA, 0.05),3) p05,
      ROUND(quantile_cont(TAB_IX_A1_1_2_COMPRA_MEDIA, 0.95),3) p95,
      ROUND(median(TAB_IX_A2_1_2_COMPRA_MEDIA),3) mediana_juros_dc
    FROM taxas WHERE DT_COMPTC='{CORTE}'""").df()
    taxas_res.to_csv(f"{OUT}/taxas_resumo.csv", index=False)

    # Desempenho: gap entre real e esperado por série (apenas onde AMBOS existem)
    desemp = con.execute(f"""
    SELECT d.CNPJ, p.DENOM_SOCIAL, d.TAB_X_CLASSE_SERIE serie,
           d.TAB_X_PR_DESEMP_ESPERADO esperado, d.TAB_X_PR_DESEMP_REAL AS realizado,
           d.TAB_X_PR_DESEMP_REAL - d.TAB_X_PR_DESEMP_ESPERADO AS gap, p.VL_PL
    FROM desempenho d JOIN painel_saneado p ON p.CNPJ=d.CNPJ AND p.DT_COMPTC=d.DT_COMPTC
    WHERE d.DT_COMPTC='{CORTE}'
      AND d.TAB_X_PR_DESEMP_ESPERADO IS NOT NULL
      AND d.TAB_X_PR_DESEMP_REAL IS NOT NULL""").df()
    desemp.to_csv(f"{OUT}/desempenho_series.csv", index=False)
    desemp_res = con.execute(f"""
    SELECT COUNT(*) n_series_total,
           COUNT(*) FILTER (TAB_X_PR_DESEMP_ESPERADO IS NOT NULL
                            AND TAB_X_PR_DESEMP_REAL IS NOT NULL) n_avaliaveis,
           ROUND(100.0*COUNT(*) FILTER (TAB_X_PR_DESEMP_ESPERADO IS NOT NULL
                            AND TAB_X_PR_DESEMP_REAL IS NOT NULL)/COUNT(*),1) cobertura_pct
    FROM desempenho WHERE DT_COMPTC='{CORTE}'""").df()
    desemp_res["n_series_abaixo_do_esperado"] = int((desemp.gap < 0).sum())
    desemp_res["pct_abaixo_do_esperado"] = round(
        100.0 * (desemp.gap < 0).sum() / max(len(desemp), 1), 1)
    desemp_res.to_csv(f"{OUT}/desempenho_resumo.csv", index=False)

    # Garantias: % dos DC coberto por garantia (só onde informado)
    gar = con.execute(f"""
    SELECT COUNT(*) n_veiculos,
           COUNT(TAB_X_VL_GARANTIA_DIRCRED) n_com_garantia_informada,
           ROUND(100.0*COUNT(TAB_X_VL_GARANTIA_DIRCRED)/COUNT(*),1) cobertura_pct,
           ROUND(SUM(TAB_X_VL_GARANTIA_DIRCRED)/1e9,1) vl_garantias_bi,
           ROUND(median(TAB_X_PR_GARANTIA_DIRCRED),1) mediana_pct_garantido,
           COUNT(*) FILTER (TAB_X_VL_GARANTIA_DIRCRED > 0) n_com_garantia_positiva
    FROM garantias WHERE DT_COMPTC='{CORTE}'""").df()
    gar.to_csv(f"{OUT}/garantias_resumo.csv", index=False)

    # Identidade contábil: Ativo - Passivo = PL (tolerância R$ 0,01)
    ident = con.execute(f"""
    SELECT COUNT(*) n_avaliaveis,
           COUNT(*) FILTER (abs(a.TAB_I_VL_ATIVO - pv.TAB_III_VL_PASSIVO - p.VL_PL) > 0.01) n_divergentes,
           ROUND(MAX(abs(a.TAB_I_VL_ATIVO - pv.TAB_III_VL_PASSIVO - p.VL_PL)),2) maior_divergencia
    FROM painel_saneado p
    JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    JOIN passivo pv ON pv.CNPJ=p.CNPJ AND pv.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' AND a.TAB_I_VL_ATIVO IS NOT NULL
      AND pv.TAB_III_VL_PASSIVO IS NOT NULL""").df()
    ident.to_csv(f"{OUT}/identidade_contabil.csv", index=False)
    print("\nidentidade contábil Ativo-Passivo=PL:")
    print(ident.to_string(index=False))

    print("\ntaxas (corte):")
    print(taxas_res.to_string(index=False))
    print("\ndesempenho (corte):")
    print(desemp_res.to_string(index=False))
    print("\ngarantias (corte):")
    print(gar.to_string(index=False))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
