#!/usr/bin/env python3
"""
Etapa 2b — Séries de cotas (tab X_2) e rentabilidade (tab X_3) por classe/série,
e download do IPCA (BCB/SGS série 433) para deflacionamento.

A tab X_2 permite decompor o passivo de cada veículo em cotas sênior,
mezanino e subordinada júnior (valor = quantidade x valor da cota), insumo
do indicador de subordinação. Classificação por prefixo do campo
TAB_X_CLASSE_SERIE ("Subclasse Senior...", "Subclasse Subordinada Mezanino",
"Subclasse Subordinada..." e, no layout ICVM 489, "Sênior"/"Subordinada").

Reprodução: python3 scripts/02b_build_series_classes.py
"""
import glob
import json
import os
import re
import sys
import unicodedata

import duckdb
import pandas as pd
import requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXTRACT = os.environ.get("FIDC_EXTRACT_DIR", os.path.join(ROOT, "data", "raw", "extracted"))
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def classify_serie(s: str) -> str:
    if not isinstance(s, str):
        return "nao_informado"
    t = strip_accents(s).upper()
    if "MEZANINO" in t:
        return "mezanino"
    if "SUBORDINADA" in t:
        return "subordinada"
    if "SENIOR" in t:
        return "senior"
    if "UNICA" in t:
        return "classe_unica"
    return "outra"


def read_csv(path):
    return pd.read_csv(path, sep=";", encoding="latin1", dtype=str, quoting=3)


def files_for(tab):
    pat = re.compile(rf"inf_mensal_fidc_tab_{tab}_(\d{{4,6}})\.csv$")
    return [f for f in sorted(glob.glob(os.path.join(EXTRACT, "*.csv")))
            if pat.search(os.path.basename(f))]


def main() -> int:
    frames = []
    for f in files_for("X_2"):
        df = read_csv(f)
        if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
            df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
        df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
        for c in ("TAB_X_QT_COTA", "TAB_X_VL_COTA"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["VL_SERIE"] = df["TAB_X_QT_COTA"] * df["TAB_X_VL_COTA"]
        df["TIPO_COTA"] = df["TAB_X_CLASSE_SERIE"].map(classify_serie)
        frames.append(df[["CNPJ", "DT_COMPTC", "TAB_X_CLASSE_SERIE", "TIPO_COTA",
                          "TAB_X_QT_COTA", "TAB_X_VL_COTA", "VL_SERIE"]])
    series = pd.concat(frames, ignore_index=True)

    rent = []
    for f in files_for("X_3"):
        df = read_csv(f)
        if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
            df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
        df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
        df["TAB_X_VL_RENTAB_MES"] = pd.to_numeric(df["TAB_X_VL_RENTAB_MES"], errors="coerce")
        df["TIPO_COTA"] = df["TAB_X_CLASSE_SERIE"].map(classify_serie)
        rent.append(df[["CNPJ", "DT_COMPTC", "TAB_X_CLASSE_SERIE", "TIPO_COTA",
                        "TAB_X_VL_RENTAB_MES"]])
    rentab = pd.concat(rent, ignore_index=True)

    # IPCA (BCB/SGS 433, variação % mensal)
    url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
           "?formato=json&dataInicial=01/12/2012&dataFinal=01/08/2026")
    ipca = pd.DataFrame(json.loads(requests.get(url, timeout=60).text))
    ipca["data"] = pd.to_datetime(ipca["data"], format="%d/%m/%Y")
    ipca["valor"] = pd.to_numeric(ipca["valor"])
    ipca["indice"] = (1 + ipca["valor"] / 100).cumprod()
    ipca.to_csv(os.path.join(OUT, "ipca_sgs433.csv"), index=False)

    con = duckdb.connect(DB)
    con.execute("CREATE OR REPLACE TABLE series_cotas AS SELECT * FROM series")
    con.execute("CREATE OR REPLACE TABLE rentab_cotas AS SELECT * FROM rentab")
    con.register("ipca_df", ipca)
    con.execute("CREATE OR REPLACE TABLE ipca AS SELECT * FROM ipca_df")
    con.execute(f"COPY series_cotas TO '{OUT}/series_cotas.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"COPY rentab_cotas TO '{OUT}/rentab_cotas.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print("series_cotas:", con.execute("SELECT COUNT(*) FROM series_cotas").fetchone())
    print("rentab_cotas:", con.execute("SELECT COUNT(*) FROM rentab_cotas").fetchone())
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
