#!/usr/bin/env python3
"""
Etapa 2 — Construção da base analítica consolidada.

Lê os informes mensais de FIDC (2013-2026) e o cadastro CVM, normaliza as
duas gerações de layout (pré e pós-RCVM 175) e materializa tabelas
analíticas em Parquet (data/analytic/) e num banco DuckDB local.

Decisões metodológicas relevantes (documentadas no relatório):
  - Unidade de análise do painel: "veículo informante" = linha do informe
    mensal (fundo, no regime ICVM 489; fundo OU classe, no regime RCVM 175).
    O script materializa o campo TP_FUNDO_CLASSE para permitir os controles
    de dupla contagem fundo x classe.
  - Valores monetários em R$ correntes, como reportados.
  - Todas as colunas preservam o nome CVM original quando possível.

Reprodução: python3 scripts/02_build.py
"""
import glob
import os
import re
import sys
import zipfile

DEDUP_LOG = []


def dedup_veiculo(df, tabela):
    """Tabelas com uma linha por veículo/competência: remove duplicatas de
    (CNPJ, DT_COMPTC) — reapresentações repetidas nos zips da CVM — mantendo a
    última ocorrência, e registra a contagem para o log de auditoria."""
    n0 = len(df)
    df = df.drop_duplicates(subset=["CNPJ", "DT_COMPTC"], keep="last")
    DEDUP_LOG.append({"tabela": tabela, "linhas": n0, "duplicatas_removidas": n0 - len(df)})
    return df

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
EXTRACT = os.environ.get(
    "FIDC_EXTRACT_DIR",
    os.path.join(ROOT, "data", "raw", "extracted"),
)
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")

pd.options.mode.copy_on_write = True


def extract_all() -> None:
    os.makedirs(EXTRACT, exist_ok=True)
    for z in sorted(glob.glob(os.path.join(RAW, "inf_mensal_fidc_*.zip"))):
        with zipfile.ZipFile(z) as zf:
            for m in zf.namelist():
                dest = os.path.join(EXTRACT, m)
                if not os.path.exists(dest):
                    zf.extract(m, EXTRACT)
    with zipfile.ZipFile(os.path.join(RAW, "registro_fundo_classe.zip")) as zf:
        zf.extractall(EXTRACT)


def read_csv(path: str, usecols=None) -> pd.DataFrame:
    # CSVs da CVM: separador ';', latin-1, sem quoting (aspas soltas em
    # DENOM_SOCIAL quebrariam o parser com o quotechar padrão)
    return pd.read_csv(
        path, sep=";", encoding="latin1", dtype=str, quoting=3,
        usecols=(lambda c: c in usecols) if usecols else None,
    )


def norm_key(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza chaves entre layouts: CNPJ_FUNDO (≤ 2024) vs CNPJ_FUNDO_CLASSE (RCVM 175)."""
    if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
        df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
    if "TP_FUNDO_CLASSE" not in df.columns:
        df["TP_FUNDO_CLASSE"] = "Fundo"  # regime ICVM 489: informe por fundo
    df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
    return df


def to_num(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = pd.NA
    return df


def files_for(tab: str):
    """CSVs de uma tabela do informe, todas as competências. tab ex.: 'IV'."""
    pat = re.compile(rf"inf_mensal_fidc_tab_{tab}_(\d{{4,6}})\.csv$")
    return [f for f in sorted(glob.glob(os.path.join(EXTRACT, "*.csv")))
            if pat.search(os.path.basename(f))]


def build_pl() -> pd.DataFrame:
    frames = []
    for f in files_for("IV"):
        df = read_csv(f)
        df = norm_key(df)
        df = to_num(df, ["TAB_IV_A_VL_PL"])
        frames.append(df[["TP_FUNDO_CLASSE", "CNPJ", "DENOM_SOCIAL",
                          "DT_COMPTC", "TAB_IV_A_VL_PL"]])
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"TAB_IV_A_VL_PL": "VL_PL"})
    return out  # dedup de PL é feito no painel canônico (regras i-ii)


CED_RE = re.compile(r"TAB_I2[AB]1?2?_CPF_CNPJ_CEDENTE_(\d)")


def build_ativo_and_cedentes():
    ativo_frames, ced_frames = [], []
    num_cols = [
        "TAB_I_VL_ATIVO", "TAB_I2_VL_CARTEIRA",
        "TAB_I2A_VL_DIRCRED_RISCO", "TAB_I2B_VL_DIRCRED_SEM_RISCO",
        "TAB_I2A2_VL_CRED_VENC_INAD", "TAB_I2A21_VL_TOTAL_PARCELA_INAD",
        "TAB_I2A3_VL_CRED_INAD", "TAB_I2A4_VL_CRED_DIRCRED_PERFM",
        "TAB_I2A8_VL_CRED_ACAO_JUDIC", "TAB_I2A11_VL_REDUCAO_RECUP",
        "TAB_I2B2_VL_CRED_VENC_INAD", "TAB_I2B21_VL_TOTAL_PARCELA_INAD",
        "TAB_I2B3_VL_CRED_INAD", "TAB_I2B11_VL_REDUCAO_RECUP",
        "TAB_I2H_VL_COTA_FIDC", "TAB_I2I_VL_COTA_FIDC_NP",
        "TAB_I2C_VL_VLMOB", "TAB_I2D_VL_TITPUB_FED", "TAB_I2E_VL_CDB",
    ]
    keep = ["TP_FUNDO_CLASSE", "CNPJ", "DENOM_SOCIAL", "DT_COMPTC",
            "CNPJ_ADMIN", "ADMIN", "CONDOM", "FUNDO_EXCLUSIVO",
            "COTST_INTERESSE"] + num_cols
    for f in files_for("I"):
        df = read_csv(f)
        df = norm_key(df)
        df = to_num(df, num_cols)
        for c in keep:
            if c not in df.columns:
                df[c] = pd.NA
        ativo_frames.append(df[keep])
        # Cedentes: pares CPF_CNPJ_CEDENTE_n / PR_CEDENTE_n, em qualquer geração
        ced_cols = [c for c in df.columns if CED_RE.match(c)]
        if ced_cols:
            recs = []
            for c in ced_cols:
                n = CED_RE.match(c).group(1)
                prefix = c.rsplit("_CPF_CNPJ_CEDENTE_", 1)[0]
                pr = f"{prefix}_PR_CEDENTE_{n}"
                if pr not in df.columns:
                    continue
                bucket = ("com_risco" if "I2A" in prefix else "sem_risco")
                sub = df[["CNPJ", "DT_COMPTC", c, pr]].copy()
                sub.columns = ["CNPJ", "DT_COMPTC", "DOC_CEDENTE", "PR_CEDENTE"]
                sub["BUCKET"] = bucket
                sub["POSICAO"] = int(n)
                recs.append(sub)
            ced = pd.concat(recs, ignore_index=True)
            ced = ced[ced["DOC_CEDENTE"].notna() & (ced["DOC_CEDENTE"].str.strip() != "")]
            ced["PR_CEDENTE"] = pd.to_numeric(ced["PR_CEDENTE"], errors="coerce")
            ced_frames.append(ced)
    ativo = dedup_veiculo(pd.concat(ativo_frames, ignore_index=True), "ativo")
    ced = pd.concat(ced_frames, ignore_index=True)
    n0 = len(ced)
    ced = ced.drop_duplicates(subset=["CNPJ", "DT_COMPTC", "BUCKET", "POSICAO"], keep="last")
    DEDUP_LOG.append({"tabela": "cedentes", "linhas": n0, "duplicatas_removidas": n0 - len(ced)})
    return ativo, ced


def build_simple(tab: str, num_prefix: str, str_cols=()) -> pd.DataFrame:
    """Concatena uma tabela numérica do informe preservando todas as colunas TAB_*.

    str_cols: colunas textuais (ex.: TAB_X_CLASSE_SERIE) mantidas sem coerção
    numérica — necessárias como chave em tabelas com várias linhas por veículo.
    """
    frames = []
    for f in files_for(tab):
        df = read_csv(f)
        df = norm_key(df)
        tabs = [c for c in df.columns if c.startswith(num_prefix)]
        df = to_num(df, [c for c in tabs if c not in str_cols])
        frames.append(df[["TP_FUNDO_CLASSE", "CNPJ", "DT_COMPTC"] + tabs])
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    print("extraindo zips ...", flush=True)
    extract_all()

    con = duckdb.connect(DB)

    print("tab IV (PL) ...", flush=True)
    pl_df = build_pl()
    con.register("pl_df", pl_df)
    con.execute("CREATE OR REPLACE TABLE pl AS SELECT * FROM pl_df")

    print("tab I (ativo, admin, cedentes) ...", flush=True)
    ativo_df, cedentes_df = build_ativo_and_cedentes()
    con.register("ativo_df", ativo_df)
    con.register("cedentes_df", cedentes_df)
    con.execute("CREATE OR REPLACE TABLE ativo AS SELECT * FROM ativo_df")
    con.execute("CREATE OR REPLACE TABLE cedentes AS SELECT * FROM cedentes_df")

    print("tab II (carteira por segmento) ...", flush=True)
    seg = dedup_veiculo(build_simple("II", "TAB_II"), "carteira_segmento")
    con.execute("CREATE OR REPLACE TABLE carteira_segmento AS SELECT * FROM seg")

    print("tab V/VI (prazos e inadimplência) ...", flush=True)
    v = dedup_veiculo(build_simple("V", "TAB_V_"), "dc_risco_prazos")
    con.execute("CREATE OR REPLACE TABLE dc_risco_prazos AS SELECT * FROM v")
    vi = dedup_veiculo(build_simple("VI", "TAB_VI_"), "dc_semrisco_prazos")
    con.execute("CREATE OR REPLACE TABLE dc_semrisco_prazos AS SELECT * FROM vi")

    print("tab VII (aquisições, alienações, recompras, substituições) ...", flush=True)
    vii = dedup_veiculo(build_simple("VII", "TAB_VII"), "negocios")
    con.execute("CREATE OR REPLACE TABLE negocios AS SELECT * FROM vii")

    print("tab X_1/X_1_1 (cotistas) e X_5 (liquidez), X (SCR) ...", flush=True)
    x1 = build_simple("X_1", "TAB_X", str_cols=("TAB_X_CLASSE_SERIE",))
    n0 = len(x1)
    x1 = x1.drop_duplicates(keep="last")
    DEDUP_LOG.append({"tabela": "cotistas_serie", "linhas": n0, "duplicatas_removidas": n0 - len(x1)})
    con.execute("CREATE OR REPLACE TABLE cotistas_serie AS SELECT * FROM x1")
    x11 = dedup_veiculo(build_simple("X_1_1", "TAB_X_NR"), "cotistas_tipo")
    con.execute("CREATE OR REPLACE TABLE cotistas_tipo AS SELECT * FROM x11")
    x5 = dedup_veiculo(build_simple("X_5", "TAB_X_VL"), "liquidez")
    con.execute("CREATE OR REPLACE TABLE liquidez AS SELECT * FROM x5")
    x = dedup_veiculo(build_simple("X", "TAB_X_"), "scr")
    con.execute("CREATE OR REPLACE TABLE scr AS SELECT * FROM x")

    print("cadastro ...", flush=True)
    cad = read_csv(os.path.join(RAW, "cad_fi.csv"))
    con.execute("CREATE OR REPLACE TABLE cad_fi AS SELECT * FROM cad")
    for t in ("registro_fundo", "registro_classe", "registro_subclasse"):
        df = read_csv(os.path.join(EXTRACT, f"{t}.csv"))
        con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM df")

    # Parquet exports (painel completo)
    for t in ("pl", "ativo", "cedentes", "carteira_segmento", "negocios",
              "cotistas_tipo", "liquidez", "scr"):
        con.execute(f"COPY {t} TO '{OUT}/{t}.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)")

    pd.DataFrame(DEDUP_LOG).to_csv(os.path.join(OUT, "dedup_log.csv"), index=False)
    n = con.execute("SELECT COUNT(*), MIN(DT_COMPTC), MAX(DT_COMPTC) FROM pl").fetchall()
    print("painel PL:", n)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
