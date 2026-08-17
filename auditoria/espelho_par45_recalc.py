#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGENTE ESPELHO — Par 4/5. Recalculo independente (nao reutiliza scripts do executor).
Fontes: CSVs brutos CVM em data/raw/extracted, competencia 2026-06.
"""
import pandas as pd, numpy as np, re, json

RAW = "/home/user/FIDCs/data/raw/extracted"
ANA = "/home/user/FIDCs/data/analytic"

def load(tab, usecols=None):
    return pd.read_csv(f"{RAW}/inf_mensal_fidc_tab_{tab}_202606.csv",
                       sep=";", encoding="latin-1", quoting=3,
                       usecols=usecols, low_memory=False)

def norm_cnpj(s):
    return s.astype(str).str.replace(r"\D", "", regex=True).str.zfill(14)

def dedupe_rule1(df):
    """Regra 1 da metodologia: CNPJ presente como Fundo E Classe -> prevalece Classe."""
    df = df.copy()
    df["cnpj"] = norm_cnpj(df["CNPJ_FUNDO_CLASSE"])
    both = set(df.loc[df.TP_FUNDO_CLASSE.eq("Fundo"), "cnpj"]) & \
           set(df.loc[df.TP_FUNDO_CLASSE.eq("Classe"), "cnpj"])
    dropped = df[df.TP_FUNDO_CLASSE.eq("Fundo") & df.cnpj.isin(both)]
    return df[~(df.TP_FUNDO_CLASSE.eq("Fundo") & df.cnpj.isin(both))], dropped

out = {}

# ============ 1. INADIMPLENCIA (tab V.b + VI.b) ============
v = load("V"); vi = load("VI")
for name, df in [("V", v), ("VI", vi)]:
    d, dr = dedupe_rule1(df)
    out[f"tab{name}_rows_raw"] = len(df); out[f"tab{name}_rows_dedup"] = len(d)
    out[f"tab{name}_dropped_rule1"] = len(dr)
    if name == "V": v_d = d
    else: vi_d = d

def agg_inad(df, p):
    faixas = {f"{p}_B{i}": df[f"TAB_{p}_B{i}_VL_INAD_{s}"].sum()
              for i, s in zip(range(1, 11), ["30","60","90","120","150","180","360","720","1080","MAIOR_1080"])}
    return {"DC": df[f"TAB_{p}_A_VL_DIRCRED_PRAZO"].sum(),
            "INAD": df[f"TAB_{p}_B_VL_DIRCRED_INAD"].sum(), **faixas}

for tag, dv, dvi in [("raw", v, vi), ("dedup", v_d, vi_d)]:
    av, avi = agg_inad(dv, "V"), agg_inad(dvi, "VI")
    out[f"inad_{tag}"] = {
        "dc_com_risco": av["DC"], "inad_com_risco": av["INAD"],
        "dc_sem_risco": avi["DC"], "inad_sem_risco": avi["INAD"],
        "dc_total": av["DC"] + avi["DC"], "inad_total": av["INAD"] + avi["INAD"],
        "pct_inad_total": (av["INAD"] + avi["INAD"]) / (av["DC"] + avi["DC"]) * 100,
        "v_maior_180": sum(av[f"V_B{i}"] for i in (7, 8, 9, 10)),
        "vi_maior_180": sum(avi[f"VI_B{i}"] for i in (7, 8, 9, 10)),
        "v_i30": av["V_B1"], "v_i31_90": av["V_B2"] + av["V_B3"],
        "v_i91_180": av["V_B4"] + av["V_B5"] + av["V_B6"],
        "vi_i30": avi["VI_B1"], "vi_i31_90": avi["VI_B2"] + avi["VI_B3"],
        "vi_i91_180": avi["VI_B4"] + avi["VI_B5"] + avi["VI_B6"],
        "soma_faixas_v": sum(av[f"V_B{i}"] for i in range(1, 11)),
        "soma_faixas_vi": sum(avi[f"VI_B{i}"] for i in range(1, 11)),
    }

# comparacao com o executor
ex = pd.read_csv(f"{ANA}/inadimplencia_aging_serie.csv")
out["executor_inad_202606"] = ex[ex.DT_COMPTC.eq("2026-06-30")].iloc[0].to_dict()

# ============ 2. CARTEIRA POR SEGMENTO (tab II, subitens) ============
SUBITENS = ["TAB_II_A_VL_INDUST","TAB_II_B_VL_IMOBIL",
    "TAB_II_C1_VL_COMERC","TAB_II_C2_VL_VAREJO","TAB_II_C3_VL_ARREND",
    "TAB_II_D1_VL_SERV","TAB_II_D2_VL_SERV_PUBLICO","TAB_II_D3_VL_SERV_EDUC","TAB_II_D4_VL_ENTRET",
    "TAB_II_E_VL_AGRONEG",
    "TAB_II_F1_VL_CRED_PESSOA","TAB_II_F2_VL_CRED_PESSOA_CONSIG","TAB_II_F3_VL_CRED_CORP",
    "TAB_II_F4_VL_MIDMARKET","TAB_II_F5_VL_VEICULO","TAB_II_F6_VL_IMOBIL_EMPRESA",
    "TAB_II_F7_VL_IMOBIL_RESID","TAB_II_F8_VL_OUTRO",
    "TAB_II_G_VL_CREDITO","TAB_II_H1_VL_PESSOA","TAB_II_H2_VL_CORP",
    "TAB_II_I1_VL_PRECAT","TAB_II_I2_VL_TRIBUT","TAB_II_I3_VL_ROYALTIES","TAB_II_I4_VL_OUTRO",
    "TAB_II_J_VL_JUDICIAL","TAB_II_K_VL_MARCA"]
t2 = load("II")
t2_d, _ = dedupe_rule1(t2)
for tag, df in [("raw", t2), ("dedup", t2_d)]:
    s = df[SUBITENS].sum().sort_values(ascending=False)
    out[f"segmentos_top10_{tag}"] = s.head(10).to_dict()
    # checagem de consistencia subtotal vs subitens
    out[f"check_subtotais_{tag}"] = {
        "C_vs_C123": float(df["TAB_II_C_VL_COMERC"].sum() - df[["TAB_II_C1_VL_COMERC","TAB_II_C2_VL_VAREJO","TAB_II_C3_VL_ARREND"]].sum().sum()),
        "F_vs_F18": float(df["TAB_II_F_VL_FINANC"].sum() - df[[c for c in SUBITENS if c.startswith("TAB_II_F")]].sum().sum()),
        "soma_subitens": float(df[SUBITENS].sum().sum()),
        "TAB_II_VL_CARTEIRA": float(df["TAB_II_VL_CARTEIRA"].sum()),
    }
ex_seg = pd.read_csv(f"{ANA}/carteira_segmentos.csv")
out["executor_segmentos_202606_top5"] = (ex_seg[ex_seg.DT_COMPTC.eq("2026-06-30")]
    .sort_values("valor", ascending=False).head(5)[["campo","valor","segmento"]].to_dict("records"))

# ============ 3. SUBORDINACAO (tab X_2) ============
x2 = load("X_2")
x2_d, _ = dedupe_rule1(x2)
def classify(s):
    s = str(s)
    up = s.upper()
    # regra declarada: contem 'Mezanino' -> mezanino; senao 'Subordinada' -> subordinada; senao 'Senior' -> senior
    if "MEZANINO" in up: return "mezanino"
    if "SUBORDINADA" in up: return "subordinada"
    if "SENIOR" in up or "SÊNIOR" in up: return "senior"
    return "outros"
for tag, df in [("raw", x2), ("dedup", x2_d)]:
    df = df.copy()
    df["tipo"] = df["TAB_X_CLASSE_SERIE"].map(classify)
    df["valor"] = df["TAB_X_QT_COTA"] * df["TAB_X_VL_COTA"]
    g = df.groupby("tipo").agg(valor=("valor", "sum"),
                               n_veiculos=("CNPJ_FUNDO_CLASSE", "nunique"))
    out[f"subord_{tag}"] = g.reset_index().to_dict("records")
    tot = df["valor"].sum()
    sub = df.loc[df.tipo.isin(["subordinada", "mezanino"]), "valor"].sum()
    out[f"subord_ratio_{tag}"] = sub / tot * 100
    out[f"subord_classes_nao_classificadas_{tag}"] = df.loc[df.tipo.eq("outros"), "TAB_X_CLASSE_SERIE"].value_counts().head(10).to_dict()
out["executor_subord"] = pd.read_csv(f"{ANA}/subordinacao_agregada.csv").to_dict("records")

# ============ 4. CEDENTES ============
ced_cols = (["TP_FUNDO_CLASSE","CNPJ_FUNDO_CLASSE","DENOM_SOCIAL","DT_COMPTC",
             "TAB_I2A_VL_DIRCRED_RISCO","TAB_I2B_VL_DIRCRED_SEM_RISCO",
             "TAB_I2A21_VL_TOTAL_PARCELA_INAD","TAB_I2B21_VL_TOTAL_PARCELA_INAD"]
            + [f"TAB_I2A12_CPF_CNPJ_CEDENTE_{i}" for i in range(1,10)]
            + [f"TAB_I2A12_PR_CEDENTE_{i}" for i in range(1,10)]
            + [f"TAB_I2B12_CPF_CNPJ_CEDENTE_{i}" for i in range(1,10)]
            + [f"TAB_I2B12_PR_CEDENTE_{i}" for i in range(1,10)])
t1 = pd.read_csv(f"{RAW}/inf_mensal_fidc_tab_I_202606.csv", sep=";", encoding="latin-1",
                 quoting=3, usecols=ced_cols, low_memory=False,
                 dtype={f"TAB_I2{ab}12_CPF_CNPJ_CEDENTE_{i}": str for ab in "AB" for i in range(1, 10)})
t1_d, _ = dedupe_rule1(t1)

def cedentes_long(df):
    recs = []
    for bucket, vcol, pref in [("com_risco", "TAB_I2A_VL_DIRCRED_RISCO", "TAB_I2A12"),
                               ("sem_risco", "TAB_I2B_VL_DIRCRED_SEM_RISCO", "TAB_I2B12")]:
        for i in range(1, 10):
            doc = df[f"{pref}_CPF_CNPJ_CEDENTE_{i}"]
            pr = pd.to_numeric(df[f"{pref}_PR_CEDENTE_{i}"], errors="coerce")
            val = pd.to_numeric(df[vcol], errors="coerce")
            m = doc.notna() & pr.notna() & (pr > 0) & (pr <= 100) & val.notna()
            sub = pd.DataFrame({
                "veiculo": df.loc[m, "CNPJ_FUNDO_CLASSE"],
                "denom": df.loc[m, "DENOM_SOCIAL"],
                "doc": doc[m].astype(str).str.replace(r"\D", "", regex=True),
                "pr": pr[m], "bucket": bucket,
                "exp": pr[m] / 100.0 * val[m],
                "vl_bucket": val[m]})
            recs.append(sub)
    lg = pd.concat(recs, ignore_index=True)
    # normalizacao de documento: 14 digitos = CNPJ (zfill), 11 = CPF
    lg["doc_norm"] = lg["doc"].where(lg["doc"].str.len() > 11,
                                     lg["doc"].str.zfill(11))
    lg.loc[lg["doc"].str.len().between(12, 14), "doc_norm"] = lg.loc[lg["doc"].str.len().between(12, 14), "doc"].str.zfill(14)
    return lg

lg = cedentes_long(t1_d)
out["cedentes_obs_validas"] = len(lg)
rank = (lg[lg.doc_norm.str.len().eq(14)]
        .groupby("doc_norm")
        .agg(exp=("exp", "sum"), n_veic=("veiculo", "nunique"))
        .sort_values("exp", ascending=False))
out["cedentes_top10_espelho"] = rank.head(10).reset_index().to_dict("records")
out["executor_cedentes_top5"] = pd.read_csv(f"{ANA}/cedentes_ranking_estimado.csv").head(5).to_dict("records")

# 4b — Petrobras
pet = lg[lg.doc_norm.eq("33000167000101")]
out["petrobras_detalhe"] = pet[["veiculo","denom","bucket","pr","vl_bucket","exp"]].to_dict("records")

# 4c — top-20: cedentes que sao eles proprios FIDC/fundos (nome contem FUNDO DE INVESTIMENTO / FIDC)
nomes = pd.read_csv(f"{ANA}/cedentes_ranking_nomes.csv", dtype={"doc_cedente": str})
top20 = nomes.head(20).copy()
univ_cnpj = set(norm_cnpj(t1["CNPJ_FUNDO_CLASSE"]))
top20["doc14"] = top20["doc_cedente"].str.zfill(14)
top20["eh_veiculo_do_universo"] = top20["doc14"].isin(univ_cnpj)
top20["nome_sugere_fundo"] = top20["razao_social"].fillna("").str.upper().str.contains("FUNDO DE INVESTIMENTO|FIDC|FIC ")
out["top20_flags"] = top20[["doc14","razao_social","eh_veiculo_do_universo","nome_sugere_fundo"]].to_dict("records")

# ============ 5. FALSO POSITIVO EM ALERTAS (>30% parcelas inadimplentes) ============
al = pd.read_csv(f"{ANA}/alertas.csv", dtype={"CNPJ": str})
al30 = al[al.alerta.str.contains("Parcelas inadimplentes")].copy()
t1["cnpj"] = norm_cnpj(t1["CNPJ_FUNDO_CLASSE"])
checks = []
for _, r in al30.head(3).iterrows():
    cn = str(r["CNPJ"]).zfill(14)
    rows = t1[t1.cnpj.eq(cn)]
    for _, q in rows.iterrows():
        parc = pd.to_numeric(q["TAB_I2A21_VL_TOTAL_PARCELA_INAD"], errors="coerce")
        dc = pd.to_numeric(q["TAB_I2A_VL_DIRCRED_RISCO"], errors="coerce")
        checks.append({"cnpj": cn, "denom": q["DENOM_SOCIAL"], "tp": q["TP_FUNDO_CLASSE"],
                       "parcela_inad_A21": float(parc) if pd.notna(parc) else None,
                       "dc_risco_A": float(dc) if pd.notna(dc) else None,
                       "ratio_espelho": float(parc / dc) if pd.notna(parc) and pd.notna(dc) and dc else None,
                       "ratio_executor": float(r["valor"])})
out["alertas_check"] = checks

# ============ 6. COBERTURA DO TOP-9 ============
def cobertura(df):
    res = {}
    for bucket, vcol, pref in [("com_risco", "TAB_I2A_VL_DIRCRED_RISCO", "TAB_I2A12"),
                               ("sem_risco", "TAB_I2B_VL_DIRCRED_SEM_RISCO", "TAB_I2B12")]:
        val = pd.to_numeric(df[vcol], errors="coerce").fillna(0)
        prs = pd.DataFrame({i: pd.to_numeric(df[f"{pref}_PR_CEDENTE_{i}"], errors="coerce") for i in range(1, 10)})
        prs = prs.where((prs > 0) & (prs <= 100))
        soma_pr = prs.sum(axis=1).clip(upper=100)  # soma dos percentuais validos, cap 100
        cob_valor = (soma_pr / 100.0 * val).sum()
        res[bucket] = {"dc_total": float(val.sum()), "coberto": float(cob_valor),
                       "cobertura_pct": float(cob_valor / val.sum() * 100),
                       "veic_com_dc": int((val > 0).sum()),
                       "veic_sem_nenhum_cedente": int(((val > 0) & soma_pr.fillna(0).eq(0)).sum())}
    tot = res["com_risco"]["dc_total"] + res["sem_risco"]["dc_total"]
    cob = res["com_risco"]["coberto"] + res["sem_risco"]["coberto"]
    res["total"] = {"dc_total": tot, "coberto": cob, "cobertura_pct": cob / tot * 100}
    return res
out["cobertura_top9"] = cobertura(t1_d)

class NpEnc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        return super().default(o)

print(json.dumps(out, indent=2, ensure_ascii=False, cls=NpEnc, default=str))
