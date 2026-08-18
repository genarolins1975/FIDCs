#!/usr/bin/env python3
"""
Etapa 13 — Taxonomia de red flags v2 (oito pilares).

Substitui a triagem de 5 sinais de `scripts/10_red_flags.py` por um catálogo
estruturado de 46 sinais em 8 pilares, com ficha completa por sinal (definição,
fórmula, limiar e sua origem, grupo de comparação, severidade, materialidade,
persistência, explicações benignas, ação de investigação, cobertura).

Princípios de construção
------------------------
1. LIMIAR ANCORADO NA DISTRIBUIÇÃO DO PRÓPRIO MERCADO. Todo limiar percentílico
   é calculado em tempo de execução sobre o grupo de comparação do sinal, no
   mês de corte, e gravado no catálogo com o percentil, o n do grupo e o valor
   observado. Números redondos só aparecem em sinais de OCORRÊNCIA (identidade
   contábil violada, PL <= 0, situação cadastral) — onde não existe distribuição
   a percentilar, apenas um evento binário.
2. AUSENTE NUNCA É ZERO. Cada sinal declara sua condição de avaliabilidade. Se
   o campo necessário é nulo — ou se o denominador é nulo/zero, o que no informe
   da CVM é indistinguível de "não reportado" — o sinal é NÃO AVALIÁVEL para
   aquele veículo-mês e entra no denominador da cobertura, jamais como "não
   disparou".
3. SEPARAÇÃO DE DIMENSÕES. Não existe nota única de caixa-preta: score,
   materialidade financeira, força de evidência, cobertura de dados,
   persistência e atualidade saem em colunas separadas.
4. EXPERIMENTAL. Os pesos por severidade são um julgamento de especialista,
   não um modelo calibrado. Sem backtest contra eventos realizados (liquidação,
   inadimplemento de sênior, intervenção), o score ordena atenção supervisória
   — não mede probabilidade de irregularidade.

Saídas
------
  data/analytic/rf2_catalogo.csv      — fichas dos 46 sinais
  data/analytic/rf2_sinais.csv        — veículo x sinal disparado
  data/analytic/rf2_score_veiculo.csv — perfil multidimensional por veículo
  docs/METODOLOGIA_RED_FLAGS.md       — catálogo legível, gerado a partir dos CSVs

Reprodução: python3 scripts/13_red_flags_v2.py
"""
from __future__ import annotations

import os
import re
import sys

import duckdb
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "analytic")
DOCS = os.path.join(ROOT, "docs")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")

CORTE = "2026-06-30"
# 25 competências: 13 de avaliação (persistência) + 12 de defasagem (lags 12m).
MESES = [
    "2024-06-30", "2024-07-31", "2024-08-31", "2024-09-30", "2024-10-31",
    "2024-11-30", "2024-12-31", "2025-01-31", "2025-02-28", "2025-03-31",
    "2025-04-30", "2025-05-31", "2025-06-30", "2025-07-31", "2025-08-31",
    "2025-09-30", "2025-10-31", "2025-11-30", "2025-12-31", "2026-01-31",
    "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31", "2026-06-30",
]
MESES_AVAL = MESES[-13:]           # 2025-06-30 .. 2026-06-30

PESO_SEV = {"baixa": 1, "média": 3, "alta": 6, "crítica": 10}

# Grupos empresariais alcançados por medida do BCB/CVM noticiada em fonte
# pública (liquidação extrajudicial / regime especial), usados no sinal GV-04.
# Lista CURADA MANUALMENTE — ver auditoria/casos_uso_indevido_fidc.md.
GRUPOS_MEDIDA = ["REAG", "GOLD STYLE", "BANCO MASTER", "MASTER S.A"]


# ---------------------------------------------------------------------------
# 1. Painel de indicadores
# ---------------------------------------------------------------------------
def carregar(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    lst = "','".join(MESES)
    q = f"""
    WITH ced AS (
      SELECT CNPJ, DT_COMPTC,
        MAX(CASE WHEN PR_CEDENTE BETWEEN 0 AND 100 THEN PR_CEDENTE END) pr_max,
        SUM(CASE WHEN PR_CEDENTE BETWEEN 0 AND 100 THEN PR_CEDENTE*PR_CEDENTE END) hhi_ced,
        SUM(CASE WHEN PR_CEDENTE BETWEEN 0 AND 100 THEN PR_CEDENTE END) pr_soma,
        COUNT(*) n_ced_decl,
        SUM(CASE WHEN PR_CEDENTE IS NULL OR PR_CEDENTE<0 OR PR_CEDENTE>100 THEN 1 ELSE 0 END) n_ced_invalido,
        MAX(CASE WHEN length(regexp_replace(DOC_CEDENTE,'\\D','','g'))=11
                  AND PR_CEDENTE BETWEEN 0 AND 100 THEN PR_CEDENTE END) pr_max_cpf
      FROM cedentes WHERE DT_COMPTC IN ('{lst}') GROUP BY 1,2),
    cot AS (
      SELECT CNPJ, DT_COMPTC, SUM(TAB_X_NR_COTST) n_cotistas
      FROM cotistas_serie WHERE DT_COMPTC IN ('{lst}') GROUP BY 1,2),
    ser AS (
      SELECT CNPJ, DT_COMPTC, SUM(VL_SERIE) v_tot,
        SUM(CASE WHEN TIPO_COTA IN ('subordinada','mezanino') THEN VL_SERIE END) v_sub,
        SUM(CASE WHEN TIPO_COTA='senior' THEN VL_SERIE END) v_sen,
        COUNT(*) n_series
      FROM series_cotas WHERE DT_COMPTC IN ('{lst}') GROUP BY 1,2),
    ren AS (
      SELECT CNPJ, DT_COMPTC,
        MIN(CASE WHEN TIPO_COTA='senior' THEN TAB_X_VL_RENTAB_MES END) rent_sen_min,
        MAX(CASE WHEN TIPO_COTA='senior' THEN TAB_X_VL_RENTAB_MES END) rent_sen_max,
        MIN(CASE WHEN TIPO_COTA='subordinada' THEN TAB_X_VL_RENTAB_MES END) rent_jr_min
      FROM rentab_cotas WHERE DT_COMPTC IN ('{lst}') GROUP BY 1,2)
    SELECT p.CNPJ, p.DT_COMPTC, p.DENOM_SOCIAL, p.TP_FUNDO_CLASSE, p.VL_PL,
      a.CNPJ_ADMIN, a.ADMIN, a.CONDOM, a.FUNDO_EXCLUSIVO, a.COTST_INTERESSE,
      a.TAB_I_VL_ATIVO ativo_tot, a.TAB_I2_VL_CARTEIRA carteira,
      a.TAB_I2A_VL_DIRCRED_RISCO dc_risco, a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc_semrisco,
      a.TAB_I2A21_VL_TOTAL_PARCELA_INAD i2a21, a.TAB_I2B21_VL_TOTAL_PARCELA_INAD i2b21,
      a.TAB_I2A11_VL_REDUCAO_RECUP prov_a, a.TAB_I2B11_VL_REDUCAO_RECUP prov_b,
      a.TAB_I2A4_VL_CRED_DIRCRED_PERFM perform, a.TAB_I2A8_VL_CRED_ACAO_JUDIC judic,
      a.TAB_I2H_VL_COTA_FIDC cota_fidc, a.TAB_I2I_VL_COTA_FIDC_NP cota_fidc_np,
      a.TAB_I2C_VL_VLMOB vlmob, a.TAB_I2D_VL_TITPUB_FED titpub, a.TAB_I2E_VL_CDB cdb,
      v.TAB_V_A_VL_DIRCRED_PRAZO dcp_r, v.TAB_V_B_VL_DIRCRED_INAD inad_r,
      v.TAB_V_C_VL_DIRCRED_ANTECIPADO ant_r,
      coalesce(v.TAB_V_B7_VL_INAD_360,0)+coalesce(v.TAB_V_B8_VL_INAD_720,0)
        +coalesce(v.TAB_V_B9_VL_INAD_1080,0)+coalesce(v.TAB_V_B10_VL_INAD_MAIOR_1080,0) inad_r_long,
      w.TAB_VI_A_VL_DIRCRED_PRAZO dcp_s, w.TAB_VI_B_VL_DIRCRED_INAD inad_s,
      w.TAB_VI_C_VL_DIRCRED_ANTECIPADO ant_s,
      coalesce(w.TAB_VI_B7_VL_INAD_360,0)+coalesce(w.TAB_VI_B8_VL_INAD_720,0)
        +coalesce(w.TAB_VI_B9_VL_INAD_1080,0)+coalesce(w.TAB_VI_B10_VL_INAD_MAIOR_1080,0) inad_s_long,
      n.TAB_VII_A1_2_VL_DIRCRED_RISCO aq_risco, n.TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO aq_semrisco,
      n.TAB_VII_A4_2_VL_DIRCRED_VENC_INAD aq_venc_inad, n.TAB_VII_A5_2_VL_DIRCRED_INAD aq_inad,
      n.TAB_VII_B1_2_VL_CEDENTE ali_ced, n.TAB_VII_B2_2_VL_PREST ali_prest,
      n.TAB_VII_B3_2_VL_TERCEIRO ali_terc, n.TAB_VII_B3_3_VL_CONTAB_TERCEIRO ali_terc_cont,
      n.TAB_VII_C_2_VL_SUBST subst, n.TAB_VII_D_2_VL_RECOMPRA recompra,
      l.TAB_X_VL_LIQUIDEZ_0 liq0, l.TAB_X_VL_LIQUIDEZ_30 liq30,
      s.TAB_X_SCR_RISCO_OPER_AA scr_aa, s.TAB_X_SCR_RISCO_OPER_A scr_a,
      s.TAB_X_SCR_RISCO_OPER_B scr_b, s.TAB_X_SCR_RISCO_OPER_C scr_c,
      s.TAB_X_SCR_RISCO_OPER_D scr_d, s.TAB_X_SCR_RISCO_OPER_E scr_e,
      s.TAB_X_SCR_RISCO_OPER_F scr_f, s.TAB_X_SCR_RISCO_OPER_G scr_g,
      s.TAB_X_SCR_RISCO_OPER_H scr_h, s.TAB_X_DEBITO_TRIBUT deb_trib,
      g.TAB_II_VL_CARTEIRA cart_seg, g.TAB_II_A_VL_INDUST sg_a, g.TAB_II_B_VL_IMOBIL sg_b,
      g.TAB_II_C_VL_COMERC sg_c, g.TAB_II_D_VL_SERV sg_d, g.TAB_II_E_VL_AGRONEG sg_e,
      g.TAB_II_F_VL_FINANC sg_f, g.TAB_II_G_VL_CREDITO sg_g, g.TAB_II_H_VL_FACTOR sg_h,
      g.TAB_II_I_VL_SETOR_PUBLICO sg_i, g.TAB_II_J_VL_JUDICIAL sg_j, g.TAB_II_K_VL_MARCA sg_k,
      g.TAB_II_I1_VL_PRECAT seg_precat,
      c.pr_max, c.hhi_ced, c.pr_soma, c.n_ced_decl, c.n_ced_invalido, c.pr_max_cpf,
      ct.n_cotistas, se.v_tot, se.v_sub, se.v_sen, se.n_series,
      re.rent_sen_min, re.rent_sen_max, re.rent_jr_min
    FROM painel_saneado p
    LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN dc_risco_prazos v ON v.CNPJ=p.CNPJ AND v.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN dc_semrisco_prazos w ON w.CNPJ=p.CNPJ AND w.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN negocios n ON n.CNPJ=p.CNPJ AND n.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN liquidez l ON l.CNPJ=p.CNPJ AND l.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN scr s ON s.CNPJ=p.CNPJ AND s.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN carteira_segmento g ON g.CNPJ=p.CNPJ AND g.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN ced c ON c.CNPJ=p.CNPJ AND c.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN cot ct ON ct.CNPJ=p.CNPJ AND ct.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN ser se ON se.CNPJ=p.CNPJ AND se.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN ren re ON re.CNPJ=p.CNPJ AND re.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC IN ('{lst}')
    """
    df = con.execute(q).df()

    reg = con.execute("""
    SELECT regexp_replace(rc.CNPJ_Classe,'\\D','','g') CNPJ,
           rc.Situacao sit_classe, rc.Auditor, rc.Custodiante,
           regexp_replace(coalesce(rc.CNPJ_Custodiante,''),'\\D','','g') cnpj_custod,
           rf.Gestor, regexp_replace(coalesce(rf.CPF_CNPJ_Gestor,''),'\\D','','g') cnpj_gestor,
           regexp_replace(coalesce(rf.CNPJ_Administrador,''),'\\D','','g') cnpj_adm_reg,
           rf.Situacao sit_fundo
    FROM registro_classe rc
    LEFT JOIN registro_fundo rf ON rf.ID_Registro_Fundo=rc.ID_Registro_Fundo
    """).df().drop_duplicates("CNPJ")
    return df, reg


def derivar(df: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    """Grade completa CNPJ x competência + indicadores derivados.

    A grade é completada com linhas vazias nas competências em que o veículo
    não informou: isso permite distinguir LACUNA (mês faltante entre a primeira
    e a última competência observadas) de ENTRADA/SAÍDA do universo, e mantém
    a defasagem de 12 meses alinhada ao calendário, não à ordem das linhas.
    """
    df = df.copy()
    df["_obs"] = True
    idx = pd.MultiIndex.from_product([sorted(df.CNPJ.unique()), MESES],
                                     names=["CNPJ", "DT_COMPTC"])
    d = df.set_index(["CNPJ", "DT_COMPTC"]).reindex(idx).reset_index()
    d["_obs"] = d["_obs"].fillna(False)
    d = d.sort_values(["CNPJ", "DT_COMPTC"]).reset_index(drop=True)
    d = d.merge(reg, on="CNPJ", how="left")

    z = lambda c: d[c].fillna(0)  # noqa: E731  soma de componentes reportados

    # --- ativo e crédito ---------------------------------------------------
    d["dc_tabI"] = z("dc_risco") + z("dc_semrisco")
    d["dcp"] = z("dcp_r") + z("dcp_s")
    d["inad"] = z("inad_r") + z("inad_s")
    d["inad_long"] = z("inad_r_long") + z("inad_s_long")
    d["prov"] = z("prov_a") + z("prov_b")
    d["ant"] = z("ant_r") + z("ant_s")
    d["base_inad"] = d.dcp + d.inad
    d["tx_inad"] = np.where(d.base_inad > 0, d.inad / d.base_inad, np.nan)
    d["cob_prov"] = np.where(d.inad > 0, d.prov / d.inad, np.nan)
    d["aging"] = np.where(d.inad > 0, d.inad_long / d.inad, np.nan)
    d["tx_ant"] = np.where(d.dcp > 0, d.ant / d.dcp, np.nan)
    d["soma_comp"] = (z("dc_risco") + z("dc_semrisco") + z("cota_fidc")
                      + z("cota_fidc_np") + z("vlmob") + z("titpub") + z("cdb"))
    d["exc_comp"] = np.where(d.carteira > 0, d.soma_comp / d.carteira, np.nan)
    d["circ"] = np.where(d.ativo_tot > 0,
                         (z("cota_fidc") + z("cota_fidc_np")) / d.ativo_tot, np.nan)
    d["jud_share"] = np.where(d.dc_tabI > 0, z("judic") / d.dc_tabI, np.nan)

    # --- estrutura de cotas ------------------------------------------------
    d["subord"] = np.where(d.v_tot > 0, z("v_sub") / d.v_tot, np.nan)
    d["ser_vs_pl"] = np.where(d.VL_PL > 0, (d.v_tot - d.VL_PL).abs() / d.VL_PL, np.nan)

    # --- SCR ---------------------------------------------------------------
    sc = ["scr_" + x for x in "aa a b c d e f g h".split()]
    d["scr_tot"] = d[sc].fillna(0).sum(axis=1)
    d["scr_eh"] = np.where(d.scr_tot > 0,
                           d[["scr_e", "scr_f", "scr_g", "scr_h"]].fillna(0).sum(axis=1)
                           / d.scr_tot, np.nan)

    # --- segmentos ---------------------------------------------------------
    sg = ["sg_" + x for x in "a b c d e f g h i j k".split()]
    d["sg_max"] = d[sg].max(axis=1)
    d["sg_soma"] = d[sg].fillna(0).sum(axis=1)
    d["mono_seg"] = np.where(d.sg_soma > 0, d.sg_max / d.sg_soma, np.nan)
    d["jud_seg"] = np.where(d.cart_seg > 0,
                            (z("sg_j") + z("seg_precat")) / d.cart_seg, np.nan)
    d["desc_tabII"] = np.where(d.dc_tabI > 0,
                               (d.cart_seg - d.dc_tabI).abs() / d.dc_tabI, np.nan)
    d["desc_tabV"] = np.where(d.dc_tabI > 0,
                              (d.dc_tabI - d.base_inad).abs() / d.dc_tabI, np.nan)

    # --- negócios (fluxos mensais) ----------------------------------------
    d["aq"] = z("aq_risco") + z("aq_semrisco")
    d["roll"] = z("subst") + z("recompra")
    d["ali_rel"] = z("ali_ced") + z("ali_prest")
    d["aq_ruim"] = z("aq_venc_inad") + z("aq_inad")
    d["desagio_terc"] = np.where((d.ali_terc > 0) & (d.ali_terc_cont > 0),
                                 d.ali_terc / d.ali_terc_cont, np.nan)

    # --- liquidez ----------------------------------------------------------
    d["liq_curta"] = np.where(d.VL_PL > 0, (z("liq0") + z("liq30")) / d.VL_PL, np.nan)

    g = d.groupby("CNPJ", sort=False)

    # --- defasagens 12m (calendário) --------------------------------------
    for c in ["VL_PL", "tx_inad", "subord", "carteira", "CNPJ_ADMIN"]:
        d[c + "_l12"] = g[c].shift(12)
    d["VL_PL_l1"] = g["VL_PL"].shift(1)

    d["d_inad_12"] = d.tx_inad - d.tx_inad_l12
    d["d_subord_12"] = d.subord - d.subord_l12
    d["var_pl_m"] = np.where(d.VL_PL_l1 > 0, d.VL_PL / d.VL_PL_l1 - 1, np.nan)
    d["cresc_12"] = np.where(d.VL_PL_l12 > 0, d.VL_PL / d.VL_PL_l12 - 1, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        d["desloc_12"] = np.where(
            (d.VL_PL_l12 > 0) & (d.VL_PL > 0) & (d.carteira_l12 > 0) & (d.carteira > 0),
            np.log(d.VL_PL.clip(lower=1) / d.VL_PL_l12.clip(lower=1))
            - np.log(d.carteira.clip(lower=1) / d.carteira_l12.clip(lower=1)), np.nan)

    # --- janelas móveis de 12 meses ---------------------------------------
    # Exige >= 10 das 12 competências informadas; a soma é reescalada para
    # base anual (soma / n_obs * 12) para não punir janelas quase completas.
    def roll12(col):
        s = g[col].rolling(12, min_periods=10).sum().reset_index(level=0, drop=True)
        n = g[col].rolling(12, min_periods=10).count().reset_index(level=0, drop=True)
        return np.where(n >= 10, s / n * 12, np.nan)

    for col in ["aq", "roll", "ali_rel", "aq_ruim"]:
        d[col + "_12m"] = roll12(col)
    cm = g["carteira"].rolling(12, min_periods=10).mean().reset_index(level=0, drop=True)
    d["cart_med12"] = cm.values
    for col in ["aq", "roll", "ali_rel", "aq_ruim"]:
        d[col + "_giro"] = np.where(d.cart_med12 > 0, d[col + "_12m"] / d.cart_med12, np.nan)

    # --- integridade de reporte -------------------------------------------
    d["troca_adm"] = np.where(d.CNPJ_ADMIN.notna() & d.CNPJ_ADMIN_l12.notna(),
                              (d.CNPJ_ADMIN != d.CNPJ_ADMIN_l12).astype(float), np.nan)
    # lacuna: mês não informado situado entre a 1ª e a última competência
    d["_ord"] = d.groupby("CNPJ", sort=False).cumcount()
    obs_ord = d.loc[d._obs, ["CNPJ", "_ord"]]
    lim = obs_ord.groupby("CNPJ")._ord.agg(["min", "max"]).rename(
        columns={"min": "ord_ini", "max": "ord_fim"})
    d = d.merge(lim, on="CNPJ", how="left")
    interno = (~d._obs) & (d._ord > d.ord_ini) & (d._ord < d.ord_fim)
    d["lacuna_ac"] = interno.groupby(d.CNPJ).cumsum()
    # estagnação: carteira idêntica ao centavo em relação ao mês anterior
    d["cart_l1"] = d.groupby("CNPJ", sort=False)["carteira"].shift(1)
    igual = (d.carteira.notna() & d.cart_l1.notna() & (d.carteira > 0)
             & (d.carteira == d.cart_l1))
    grp = (~igual).cumsum()
    d["meses_estagnado"] = igual.groupby([d.CNPJ, grp]).cumsum()
    d["meses_estagnado"] = np.where(d.carteira.notna(), d["meses_estagnado"], np.nan)

    # --- prestador sob medida regulatória ---------------------------------
    txt = (d.DENOM_SOCIAL.fillna("") + "|" + d.ADMIN.fillna("")
           + "|" + d.Gestor.fillna("")).str.upper()
    pat = "|".join(re.escape(t) for t in GRUPOS_MEDIDA)
    d["grupo_medida"] = np.where(d.DENOM_SOCIAL.notna(),
                                 txt.str.contains(pat, regex=True).astype(float), np.nan)

    d["em_liquidacao"] = np.where(
        d.sit_classe.notna() | d.sit_fundo.notna(),
        ((d.sit_classe.fillna("") == "Em Liquidação")
         | (d.sit_fundo.fillna("") == "Em Liquidação")).astype(float), np.nan)
    d["gestor_eq_adm"] = np.where(
        (d.cnpj_gestor.fillna("") != "") & (d.CNPJ_ADMIN.notna()),
        (d.cnpj_gestor == d.CNPJ_ADMIN.fillna("").str.replace(r"\D", "", regex=True)
         ).astype(float), np.nan)
    d["sem_prestador"] = np.where(
        d.sit_classe.notna(),
        (d.Auditor.isna() | d.Custodiante.isna()).astype(float), np.nan)
    return d


# ---------------------------------------------------------------------------
# 2. Catálogo de sinais
# ---------------------------------------------------------------------------
# Cada ficha traz:
#   grupo      -> f(d) máscara booleana: universo de comparação do sinal
#   avaliavel  -> f(d) máscara booleana: campos necessários efetivamente presentes
#   valor      -> f(d) série numérica com o indicador (NaN onde não avaliável)
#   material   -> f(d) máscara booleana: porte mínimo para o sinal valer
#   limiar     -> ('pct', q, sentido) | ('fixo', valor, sentido) | ('ocorrencia',)
#                 sentido: '>=' dispara acima do limiar; '<=' abaixo
#   mat_rs     -> f(d) série: R$ expostos ao risco que o sinal aponta
#   evidencia  -> 'observado' (campo reportado direto / flag cadastral)
#                 'derivado'  (razão, percentil, variação temporal, janela móvel)
S = []


def sinal(**kw):
    S.append(kw)



# ---------------- PILAR 1 — QUALIDADE DO ATIVO -----------------------------
sinal(
    id="QA-01", pilar="1. Qualidade do ativo",
    nome="Inadimplência abrangente no topo do mercado",
    definicao="Parcelas vencidas e não pagas (tabs V.B + VI.B) sobre o total de "
              "direitos creditórios por prazo (V.A + V.B + VI.A + VI.B) acima do "
              "percentil 95 do mercado entre veículos com carteira material.",
    formula="tx_inad = (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD) / "
            "(TAB_V_A_VL_DIRCRED_PRAZO + TAB_V_B_VL_DIRCRED_INAD + "
            "TAB_VI_A_VL_DIRCRED_PRAZO + TAB_VI_B_VL_DIRCRED_INAD)",
    grupo="Veículos com DC (tab I) >= R$ 50 mi e denominador de inadimplência > 0",
    grupo_f=lambda d: (d.dc_tabI >= 5e7) & (d.base_inad > 0),
    avaliavel=lambda d: d._obs & d.base_inad.gt(0) & d.tx_inad.notna(),
    valor=lambda d: d.tx_inad,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC (tab I) >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="alta", persistencia=3,
    mat_rs=lambda d: d.inad, evidencia="derivado",
    benigno="FIDC-NP e FIDC de crédito judicial compram carteira JÁ vencida: "
            "inadimplência alta é o modelo de negócio, não deterioração. Fundos "
            "em amortização/liquidação concentram o estoque residual vencido. "
            "Consignado com atraso administrativo alto e baixa perda final também "
            "aparece aqui.",
    acao="Cruzar com o segmento da carteira (tab II), a classificação SCR (X.8) e "
         "a série de 24 meses do próprio veículo: o que importa é a TENDÊNCIA e a "
         "cobertura por provisão, não o nível absoluto.",
)
sinal(
    id="QA-02", pilar="1. Qualidade do ativo",
    nome="Deterioração acelerada da inadimplência em 12 meses",
    definicao="Variação em pontos percentuais da taxa de inadimplência abrangente "
              "contra a mesma competência do ano anterior, acima do p95 das variações.",
    formula="d_inad_12 = tx_inad(t) - tx_inad(t-12m)",
    grupo="Veículos com DC >= R$ 50 mi e tx_inad computável em t e em t-12m",
    grupo_f=lambda d: (d.dc_tabI >= 5e7) & d.d_inad_12.notna(),
    avaliavel=lambda d: d._obs & d.d_inad_12.notna(),
    valor=lambda d: d.d_inad_12,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC (tab I) >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.d_inad_12.clip(lower=0) * d.base_inad, evidencia="derivado",
    benigno="Fundo que entrou em amortização deixa de comprar crédito novo: o "
            "denominador encolhe e a taxa sobe sem que nada tenha piorado no "
            "estoque. Mudança de política de write-off também produz salto "
            "contábil sem evento econômico.",
    acao="Verificar se o denominador (DC por prazo) caiu junto — decomposição "
         "numerador/denominador separa deterioração real de efeito de base.",
)
sinal(
    id="QA-03", pilar="1. Qualidade do ativo",
    nome="Provisão nula diante de inadimplência material",
    definicao="Redução ao valor recuperável (I2A11 + I2B11) igual a zero, ou "
              "abaixo do p10 do mercado, com estoque inadimplente relevante.",
    formula="cob_prov = (TAB_I2A11_VL_REDUCAO_RECUP + TAB_I2B11_VL_REDUCAO_RECUP) "
            "/ (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD)",
    grupo="Veículos com estoque inadimplente >= R$ 10 mi",
    grupo_f=lambda d: d.inad >= 1e7,
    avaliavel=lambda d: d._obs & d.inad.ge(1e7) & d.cob_prov.notna(),
    valor=lambda d: d.cob_prov,
    material=lambda d: d.inad >= 1e7,
    material_txt="inadimplência >= R$ 10 mi",
    limiar=("pct", 0.10, "<="), severidade="alta", persistencia=3,
    mat_rs=lambda d: (d.inad - d.prov).clip(lower=0), evidencia="derivado",
    benigno="Crédito com coobrigação plena do cedente ou seguro de crédito não "
            "exige provisão no fundo. Carteira sem aquisição substancial de risco "
            "(tab I.2.B) tem a perda retida no cedente. Recompra automática "
            "contratual no atraso também dispensa provisão.",
    acao="Ler o regulamento quanto a coobrigação/recompra e cruzar com a tab VII.D "
         "(recompras efetivas): se o cedente não recompra de fato, a ausência de "
         "provisão não se sustenta.",
)
sinal(
    id="QA-04", pilar="1. Qualidade do ativo",
    nome="Inadimplência exatamente zero em carteira grande e concentrada",
    definicao="Carteira grande, cedente único dominante e ZERO parcela vencida "
              "reportada — o padrão de lastro 'bom demais' observado nos casos "
              "públicos de fraude de recebíveis antes do colapso.",
    formula="inad = 0 AND dc_tabI >= p90(mercado) AND pr_max >= 50",
    grupo="Veículos com DC >= p90 do mercado e cedente declarado válido",
    grupo_f=lambda d: (d.dc_tabI > 0) & d.pr_max.notna(),
    avaliavel=lambda d: d._obs & d.base_inad.gt(0) & d.pr_max.notna(),
    valor=lambda d: np.where(d.base_inad > 0, (d.inad == 0).astype(float), np.nan),
    material=lambda d: (d.dc_tabI >= 4.28e8) & (d.pr_max >= 50),
    material_txt="DC >= R$ 428 mi (p90 do mercado) e cedente máximo >= 50%",
    limiar=("ocorrencia",), severidade="alta", persistencia=3,
    mat_rs=lambda d: d.dc_tabI, evidencia="derivado",
    benigno="Carteira de consignado público/INSS ou de recebíveis de utilities "
            "com desconto em folha tem inadimplência estruturalmente próxima de "
            "zero. Fundo recém-constituído ainda não tem safra vencida. Recompra "
            "automática do cedente no primeiro dia de atraso zera o estoque "
            "vencido por desenho contratual — e é lícita.",
    acao="Testar lastro: pedir a conciliação de recebíveis do custodiante, "
         "verificar registro em registradora autorizada (Res. BCB 5.021) e "
         "conferir se a tab VII.D mostra recompras compatíveis com o 'zero'.",
)
sinal(
    id="QA-05", pilar="1. Qualidade do ativo",
    nome="Inadimplência integralmente envelhecida (> 360 dias)",
    definicao="Fração do estoque inadimplente nas faixas B7 a B10 (acima de 360 "
              "dias) no p90 ou acima — crédito parado, com recuperação improvável.",
    formula="aging = (V_B7+V_B8+V_B9+V_B10 + VI_B7+VI_B8+VI_B9+VI_B10) / "
            "(V_B + VI_B)",
    grupo="Veículos com estoque inadimplente >= R$ 10 mi",
    grupo_f=lambda d: d.inad >= 1e7,
    avaliavel=lambda d: d._obs & d.inad.ge(1e7) & d.aging.notna(),
    valor=lambda d: d.aging,
    material=lambda d: d.inad >= 1e7,
    material_txt="inadimplência >= R$ 10 mi",
    limiar=("pct", 0.90, ">="), severidade="média", persistencia=3,
    mat_rs=lambda d: d.inad_long, evidencia="derivado",
    benigno="FIDC de crédito judicial e de precatórios opera por natureza com "
            "ativos de maturação plurianual: 100% do estoque acima de 360 dias é "
            "o esperado. Fundo em liquidação carrega apenas o resíduo antigo.",
    acao="Confrontar com a provisão (QA-03): estoque velho e provisão baixa é a "
         "combinação relevante; estoque velho já provisionado é apenas resíduo.",
)
sinal(
    id="QA-06", pilar="1. Qualidade do ativo",
    nome="Direitos creditórios performados não informados",
    definicao="Campo de créditos performados (I.2.A.4) não preenchido, impedindo "
              "separar risco de performance (obrigação do cedente ainda por "
              "cumprir) de risco de crédito puro.",
    formula="perf_share = TAB_I2A4_VL_CRED_DIRCRED_PERFM / TAB_I2A_VL_DIRCRED_RISCO",
    grupo="Veículos com DC com aquisição de risco > 0",
    grupo_f=lambda d: d.dc_risco > 0,
    avaliavel=lambda d: d._obs & d.dc_risco.gt(0) & d.perform.notna() & d.perform.gt(0),
    valor=lambda d: np.where(d.dc_risco > 0, d.perform / d.dc_risco, np.nan),
    material=lambda d: d.dc_risco >= 5e7,
    material_txt="DC com risco >= R$ 50 mi",
    limiar=("pct", 0.10, "<="), severidade="baixa", persistencia=1,
    mat_rs=lambda d: d.dc_risco, evidencia="observado",
    benigno="O campo foi efetivamente descontinuado no layout pós-RCVM 175 — "
            "cobertura ~0% desde 2023. A não informação é falha de layout, não "
            "conduta do administrador.",
    acao="Nenhuma ação sobre o veículo: registrar como LACUNA DE INFORMAÇÃO "
         "estrutural do informe mensal e endereçá-la ao regulador.",
)

# ---------------- PILAR 2 — ESTRUTURA E SUBORDINAÇÃO -----------------------
sinal(
    id="ES-01", pilar="2. Estrutura e subordinação",
    nome="Subordinação no fundo da distribuição do mercado",
    definicao="Colchão de subordinação (séries subordinadas + mezanino sobre o "
              "total das séries) abaixo do p5 do mercado entre estruturas que de "
              "fato têm sênior e subordinada.",
    formula="subord = SUM(VL_SERIE onde TIPO_COTA in ('subordinada','mezanino')) "
            "/ SUM(VL_SERIE)",
    grupo="Veículos com série sênior > 0 E série subordinada/mezanino > 0",
    grupo_f=lambda d: (d.v_sen > 0) & (d.v_sub > 0),
    avaliavel=lambda d: d._obs & d.v_sen.gt(0) & d.v_sub.gt(0) & d.subord.notna(),
    valor=lambda d: d.subord,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("pct", 0.05, "<="), severidade="alta", persistencia=3,
    mat_rs=lambda d: d.v_sen.fillna(0), evidencia="derivado",
    benigno="Carteira de risco muito baixo (consignado público, crédito com "
            "garantia real líquida) suporta subordinação fina por desenho, "
            "validado por agência de rating. Estruturas com seguro de crédito ou "
            "carta de fiança bancária substituem colchão por garantia externa.",
    acao="Comparar a subordinação com a inadimplência esperada da própria "
         "carteira (ES-03) e com o rating da série sênior; verificar gatilhos de "
         "recomposição no regulamento.",
)
sinal(
    id="ES-02", pilar="2. Estrutura e subordinação",
    nome="Erosão da subordinação em 12 meses",
    definicao="Queda em pontos percentuais do índice de subordinação contra a "
              "mesma competência do ano anterior, no p5 inferior das variações.",
    formula="d_subord_12 = subord(t) - subord(t-12m)",
    grupo="Veículos com sênior e subordinada em t e em t-12m",
    grupo_f=lambda d: (d.v_sen > 0) & (d.v_sub > 0) & d.d_subord_12.notna(),
    avaliavel=lambda d: d._obs & d.d_subord_12.notna() & d.v_sen.gt(0),
    valor=lambda d: d.d_subord_12,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("pct", 0.05, "<="), severidade="alta", persistencia=2,
    mat_rs=lambda d: (-d.d_subord_12).clip(lower=0) * d.v_tot.fillna(0),
    evidencia="derivado",
    benigno="Emissão programada de nova série sênior dilui o percentual "
            "subordinado sem consumo de colchão — é crescimento, não perda. "
            "Amortização de subordinada prevista em cronograma também reduz o "
            "índice de forma planejada.",
    acao="Separar o efeito 'numerador' (subordinada encolheu: consumo de perda) "
         "do 'denominador' (sênior cresceu: alavancagem da estrutura) usando a "
         "tab X.2 em nível de série.",
)
sinal(
    id="ES-03", pilar="2. Estrutura e subordinação",
    nome="Colchão subordinado menor que a inadimplência líquida de provisão",
    definicao="Valor das séries subordinadas e mezanino inferior ao estoque de "
              "parcelas vencidas JÁ DEDUZIDA a provisão constituída: se a perda "
              "residual se materializar, a série sênior é atingida.",
    formula="v_sub < (V_B + VI_B) - (I2A11 + I2B11)",
    grupo="Veículos com série sênior > 0 e inadimplência líquida >= R$ 10 mi",
    grupo_f=lambda d: (d.v_sen > 0) & ((d.inad - d.prov) >= 1e7),
    avaliavel=lambda d: d._obs & d.v_sen.gt(0) & d.v_sub.notna() & d.inad.gt(0),
    valor=lambda d: np.where((d.v_sen > 0) & (d.inad > 0),
                             (d.v_sub.fillna(0) < (d.inad - d.prov)).astype(float),
                             np.nan),
    material=lambda d: ((d.inad - d.prov) >= 1e7) & (d.v_sen > 0),
    material_txt="inadimplência líquida de provisão >= R$ 10 mi e sênior emitida",
    limiar=("ocorrencia",), severidade="crítica", persistencia=2,
    mat_rs=lambda d: (d.inad - d.prov - d.v_sub.fillna(0)).clip(lower=0),
    evidencia="derivado",
    benigno="Nem todo estoque vencido vira perda: taxas de recuperação de 60-90% "
            "são comuns em duplicatas e consignado, e o sinal compara estoque "
            "bruto de recuperação com colchão — é conservador por construção. "
            "Coobrigação do cedente devolve a perda ao originador. A base de "
            "disparo é alta (perto de um terço do grupo), o que reforça que o "
            "sinal só tem valor combinado a QA-01/QA-03.",
    acao="Refazer o teste com a taxa de recuperação histórica da própria carteira "
         "e com a coobrigação contratada; se ainda assim o colchão não cobre, é "
         "caso de exame do enquadramento da sênior.",
)
sinal(
    id="ES-04", pilar="2. Estrutura e subordinação",
    nome="Patrimônio líquido nulo ou negativo",
    definicao="PL reportado na tab IV menor ou igual a zero — o veículo consumiu "
              "todo o capital dos cotistas.",
    formula="VL_PL <= 0",
    grupo="Todos os veículos do painel canônico",
    grupo_f=lambda d: d._obs,
    avaliavel=lambda d: d._obs & d.VL_PL.notna(),
    valor=lambda d: np.where(d.VL_PL.notna(), (d.VL_PL <= 0).astype(float), np.nan),
    material=lambda d: pd.Series(True, index=d.index),
    material_txt="sem porte mínimo — PL negativo é relevante em qualquer escala",
    limiar=("ocorrencia",), severidade="crítica", persistencia=1,
    mat_rs=lambda d: d.VL_PL.abs(), evidencia="observado",
    benigno="Fundo encerrado que já distribuiu todo o patrimônio reporta PL zero "
            "na competência de fechamento. Veículo em fase pré-operacional ainda "
            "não integralizado também aparece com PL nulo.",
    acao="Checar a situação cadastral (registro CVM) e a tab X.4: PL zero com "
         "resgate integral no mês é encerramento; PL negativo com carteira viva é "
         "insolvência.",
)
sinal(
    id="ES-05", pilar="2. Estrutura e subordinação",
    nome="Rentabilidade negativa na cota sênior",
    definicao="Pior rentabilidade mensal entre as séries sêniores abaixo do p5 do "
              "mercado — a classe que deveria estar protegida absorveu perda.",
    formula="rent_sen_min = MIN(TAB_X_VL_RENTAB_MES onde TIPO_COTA='senior')",
    grupo="Veículos com série sênior efetivamente emitida (VL_SERIE > 0)",
    grupo_f=lambda d: d.v_sen > 0,
    avaliavel=lambda d: d._obs & d.v_sen.gt(0) & d.rent_sen_min.notna(),
    valor=lambda d: d.rent_sen_min,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("pct", 0.05, "<="), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.v_sen.fillna(0), evidencia="observado",
    benigno="Série sênior indexada a IPCA ou a ativo marcado a mercado tem "
            "rentabilidade nominal negativa em mês de fechamento de curva sem "
            "qualquer perda de crédito. Séries em amortização com ajuste de "
            "marcação também apresentam meses negativos.",
    acao="Ver se a queda é isolada (marcação) ou persistente (perda de crédito) e "
         "se a subordinada já foi zerada — sênior negativa com subordinada "
         "positiva no mesmo mês é anomalia de cascata.",
)

# ---------------- PILAR 3 — CONCENTRAÇÃO -----------------------------------
sinal(
    id="CN-01", pilar="3. Concentração",
    nome="Cedente único dominante",
    definicao="Maior percentual declarado de um único cedente (tab I) no p90 ou "
              "acima do mercado: o fundo é, na prática, um veículo de um "
              "originador só.",
    formula="pr_max = MAX(PR_CEDENTE) por veículo, com PR_CEDENTE em [0,100]",
    grupo="Veículos que declaram ao menos um cedente com percentual válido",
    grupo_f=lambda d: d.pr_max.notna(),
    avaliavel=lambda d: d._obs & d.pr_max.notna(),
    valor=lambda d: d.pr_max,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC >= R$ 50 mi",
    limiar=("pct", 0.90, ">="), severidade="média", persistencia=3,
    mat_rs=lambda d: d.pr_max / 100.0 * d.dc_tabI, evidencia="observado",
    benigno="FIDC corporativo monocedente (fornecedores de uma indústria, "
            "financeira do próprio grupo) é a estrutura padrão do segmento e "
            "plenamente lícita. O que o sinal mede é dependência, não conduta.",
    acao="Avaliar a solidez do cedente (rating, balanço) e a existência de "
         "coobrigação: concentração em cedente sólido é risco de crédito "
         "corporativo; em cedente frágil, é risco de fraude de lastro.",
)
sinal(
    id="CN-02", pilar="3. Concentração",
    nome="Índice HHI de cedentes no topo",
    definicao="Herfindahl-Hirschman calculado sobre os percentuais declarados dos "
              "até nove cedentes informados, no p90 ou acima.",
    formula="hhi_ced = SUM(PR_CEDENTE^2) sobre PR_CEDENTE em [0,100]",
    grupo="Veículos que declaram cedentes com percentual válido",
    grupo_f=lambda d: d.hhi_ced.notna(),
    avaliavel=lambda d: d._obs & d.hhi_ced.notna(),
    valor=lambda d: d.hhi_ced,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC >= R$ 50 mi",
    limiar=("pct", 0.90, ">="), severidade="média", persistencia=3,
    mat_rs=lambda d: d.dc_tabI, evidencia="derivado",
    benigno="O informe só exige os nove maiores cedentes: um fundo pulverizado "
            "que declara apenas os nove maiores tem HHI subestimado, e um fundo "
            "monocedente tem HHI corretamente máximo. O viés é conservador, mas "
            "existe. Fundo cativo de grupo econômico é HHI 10.000 por desenho.",
    acao="Confrontar com a cobertura declarada (soma dos percentuais): HHI alto "
         "com soma perto de 100% é concentração real; com soma baixa, é artefato "
         "do recorte top-9.",
)
sinal(
    id="CN-03", pilar="3. Concentração",
    nome="Base de cotistas mínima em veículo de porte",
    definicao="Até dois cotistas somados em todas as séries, num veículo com PL "
              "acima do p75 do mercado — não há verificação de preço por terceiros.",
    formula="n_cotistas = SUM(TAB_X_NR_COTST) por veículo (tab X.1)",
    grupo="Todos os veículos com número de cotistas informado",
    grupo_f=lambda d: d.n_cotistas.notna(),
    avaliavel=lambda d: d._obs & d.n_cotistas.notna(),
    valor=lambda d: d.n_cotistas,
    material=lambda d: d.VL_PL >= 1.56e8,
    material_txt="PL >= R$ 156 mi (p75 do mercado)",
    limiar=("fixo", 2, "<="), severidade="média", persistencia=3,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="FIDC exclusivo de tesouraria de um banco, de uma seguradora ou de "
            "uma EFPC tem legitimamente um cotista. FIC-FIDC master-feeder também "
            "tem cotista único (o feeder). Nada disso é irregular.",
    acao="Verificar se o cotista único é parte relacionada ao cedente (GV-01): "
         "cotista único INDEPENDENTE do originador é estrutura de tesouraria; "
         "cotista único LIGADO é veículo espelho do próprio originador.",
)
sinal(
    id="CN-04", pilar="3. Concentração",
    nome="Carteira monossegmento",
    definicao="Um único segmento econômico (tab II, categorias A a K) responde "
              "por praticamente toda a carteira segmentada.",
    formula="mono_seg = MAX(TAB_II_[A..K]) / SUM(TAB_II_[A..K])",
    grupo="Veículos com carteira segmentada (tab II) > 0",
    grupo_f=lambda d: d.sg_soma > 0,
    avaliavel=lambda d: d._obs & d.sg_soma.gt(0) & d.mono_seg.notna(),
    valor=lambda d: d.mono_seg,
    material=lambda d: d.dc_tabI >= 2e8,
    material_txt="DC >= R$ 200 mi",
    limiar=("fixo", 0.999, ">="), severidade="baixa", persistencia=3,
    mat_rs=lambda d: d.sg_max, evidencia="derivado",
    benigno="Praticamente todo FIDC é temático por regulamento: agro, consignado, "
            "veículos, judicial. Monossegmento é a regra do mercado, não a "
            "exceção — por isso a severidade é baixa e o sinal só serve combinado "
            "a outros do mesmo pilar.",
    acao="Usar apenas como contexto para interpretar QA-01 e JR-03; isoladamente "
         "não justifica diligência.",
)
sinal(
    id="CN-05", pilar="3. Concentração",
    nome="Ativo composto quase inteiramente por cotas de outros FIDCs",
    definicao="Cotas de FIDC e de FIDC-NP (I.2.H + I.2.I) acima do p95 da razão "
              "sobre o ativo total — circularidade intramercado.",
    formula="circ = (TAB_I2H_VL_COTA_FIDC + TAB_I2I_VL_COTA_FIDC_NP) / TAB_I_VL_ATIVO",
    grupo="Veículos com ativo total > 0",
    grupo_f=lambda d: d.ativo_tot > 0,
    avaliavel=lambda d: d._obs & d.ativo_tot.gt(0) & d.circ.notna(),
    valor=lambda d: d.circ,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="baixa", persistencia=3,
    mat_rs=lambda d: (d.cota_fidc.fillna(0) + d.cota_fidc_np.fillna(0)),
    evidencia="observado",
    benigno="FIC-FIDC é uma categoria regulada e comum: investir só em cotas de "
            "FIDC é exatamente o mandato. O sinal serve para medir DUPLA CONTAGEM "
            "de PL no agregado do mercado, e só vira alerta quando o fundo detido "
            "é do mesmo grupo (aí é CN-05 + GV-01).",
    acao="Rastrear os FIDCs detidos via CDA (bloco BLC_2) e verificar se emissor "
         "e detentor pertencem ao mesmo grupo (flag EMISSOR_LIGADO).",
)

# ---------------- PILAR 4 — GOVERNANÇA E CONFLITOS -------------------------
sinal(
    id="GV-01", pilar="4. Governança e conflitos",
    nome="Cotista de interesse em fundo não exclusivo com base pulverizada",
    definicao="O administrador declara existência de cotista com relação de "
              "interesse (COTST_INTERESSE='S') num fundo que NÃO é exclusivo e "
              "que tem base de cotistas relevante — parte relacionada convivendo "
              "com investidores de fora.",
    formula="COTST_INTERESSE='S' AND FUNDO_EXCLUSIVO='N' AND n_cotistas >= 10",
    grupo="Veículos com as flags de interesse e exclusividade preenchidas",
    grupo_f=lambda d: d.COTST_INTERESSE.notna() & d.FUNDO_EXCLUSIVO.notna(),
    avaliavel=lambda d: (d._obs & d.COTST_INTERESSE.notna()
                         & d.FUNDO_EXCLUSIVO.notna() & d.n_cotistas.notna()),
    valor=lambda d: np.where(
        d.COTST_INTERESSE.notna() & d.FUNDO_EXCLUSIVO.notna() & d.n_cotistas.notna(),
        ((d.COTST_INTERESSE == "S") & (d.FUNDO_EXCLUSIVO == "N")
         & (d.n_cotistas >= 10)).astype(float), np.nan),
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("ocorrencia",), severidade="alta", persistencia=3,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Gestor que investe capital próprio na subordinada é considerado "
            "ALINHAMENTO de interesses pelo mercado (skin in the game) e é prática "
            "recomendada. Sponsor que retém a subordinada por exigência de rating "
            "cai no mesmo caso.",
    acao="Identificar QUAL classe a parte relacionada detém: subordinada = "
         "alinhamento; sênior comprada de si mesmo, ou subordinada mínima com "
         "sênior vendida ao varejo = conflito.",
)
sinal(
    id="GV-02", pilar="4. Governança e conflitos",
    nome="Gestor e administrador na mesma pessoa jurídica",
    definicao="CNPJ do gestor idêntico ao CNPJ do administrador no registro CVM: "
              "acumulação das funções de decisão de investimento e de controle.",
    formula="cnpj_gestor = CNPJ_ADMIN (registro_fundo x tab I)",
    grupo="Veículos com gestor e administrador identificados no registro",
    grupo_f=lambda d: d.gestor_eq_adm.notna(),
    avaliavel=lambda d: d._obs & d.gestor_eq_adm.notna(),
    valor=lambda d: d.gestor_eq_adm,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("ocorrencia",), severidade="média", persistencia=3,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="A RCVM 175 permite a administração fiduciária e a gestão pela mesma "
            "instituição, com segregação interna (chinese wall). Grandes bancos "
            "operam assim há décadas sem qualquer irregularidade.",
    acao="Verificar se há custodiante e controlador independentes (GV-05) — a "
         "acumulação só é preocupante quando TODAS as funções de controle estão "
         "no mesmo grupo.",
)
sinal(
    id="GV-03", pilar="4. Governança e conflitos",
    nome="Troca de administrador nos últimos 12 meses",
    definicao="CNPJ do administrador informado na tab I difere do informado 12 "
              "competências antes.",
    formula="CNPJ_ADMIN(t) != CNPJ_ADMIN(t-12m)",
    grupo="Veículos com CNPJ_ADMIN informado em t e em t-12m",
    grupo_f=lambda d: d.troca_adm.notna(),
    avaliavel=lambda d: d._obs & d.troca_adm.notna(),
    valor=lambda d: d.troca_adm,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("ocorrencia",), severidade="baixa", persistencia=1,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Consolidação do setor de administração fiduciária, migração "
            "societária e reorganização de grupo produzem trocas em massa sem "
            "qualquer conteúdo de risco. Troca pode até ser SAUDÁVEL quando o "
            "administrador anterior está sob medida do regulador.",
    acao="Só é relevante em conjunto: troca de administrador + queda de PL "
         "(IC-04) + salto de inadimplência (QA-02) no mesmo semestre.",
)
sinal(
    id="GV-04", pilar="4. Governança e conflitos",
    nome="Vínculo nominal com grupo alcançado por medida do BCB/CVM",
    definicao="Denominação do veículo, do administrador ou do gestor contém a "
              "marca de grupo econômico objeto de liquidação extrajudicial ou "
              "regime especial noticiado em fonte pública.",
    formula="UPPER(DENOM_SOCIAL || ADMIN || Gestor) LIKE qualquer termo da lista "
            "curada GRUPOS_MEDIDA",
    grupo="Todos os veículos com denominação informada",
    grupo_f=lambda d: d.DENOM_SOCIAL.notna(),
    avaliavel=lambda d: d._obs & d.grupo_medida.notna(),
    valor=lambda d: d.grupo_medida,
    material=lambda d: pd.Series(True, index=d.index),
    material_txt="sem porte mínimo",
    limiar=("ocorrencia",), severidade="alta", persistencia=1,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Casamento por STRING é grosseiro: 'MASTER' aparece em razões sociais "
            "sem qualquer relação com o Banco Master. A troca do prestador já "
            "ocorrida não altera a denominação histórica do veículo. O sinal é "
            "uma PISTA de busca, jamais uma imputação.",
    acao="Confirmar o vínculo societário no registro CVM e nos atos do BCB antes "
         "de qualquer uso; descartar homonímias uma a uma.",
)
sinal(
    id="GV-05", pilar="4. Governança e conflitos",
    nome="Auditor independente ou custodiante ausente no registro",
    definicao="Registro da classe (RCVM 175) sem auditor independente ou sem "
              "custodiante identificado — falha nos controles obrigatórios.",
    formula="Auditor IS NULL OR Custodiante IS NULL (registro_classe)",
    grupo="Veículos com registro de classe localizado",
    grupo_f=lambda d: d.sem_prestador.notna(),
    avaliavel=lambda d: d._obs & d.sem_prestador.notna(),
    valor=lambda d: d.sem_prestador,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("ocorrencia",), severidade="média", persistencia=3,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Defasagem do cadastro é a explicação mais provável: o prestador "
            "existe e o campo não foi atualizado. Classes em fase pré-operacional "
            "legitimamente ainda não contrataram auditor.",
    acao="Confirmar contra o formulário de informações periódicas e as "
         "demonstrações financeiras auditadas do exercício antes de tratar como "
         "ausência real.",
)

# ---------------- PILAR 5 — INTEGRIDADE DOS DADOS --------------------------
sinal(
    id="DI-01", pilar="5. Integridade dos dados e reportes",
    nome="Percentuais de cedentes inconsistentes",
    definicao="Soma dos percentuais declarados de cedentes acima de 100,5%, ou "
              "existência de percentual fora do intervalo [0,100].",
    formula="pr_soma > 100.5 OR n_ced_invalido > 0",
    grupo="Veículos que declaram ao menos um cedente",
    grupo_f=lambda d: d.n_ced_decl.notna(),
    avaliavel=lambda d: d._obs & d.n_ced_decl.notna(),
    valor=lambda d: np.where(d.n_ced_decl.notna(),
                             ((d.pr_soma.fillna(0) > 100.5)
                              | (d.n_ced_invalido.fillna(0) > 0)).astype(float), np.nan),
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC >= R$ 50 mi",
    limiar=("ocorrencia",), severidade="média", persistencia=1,
    mat_rs=lambda d: d.dc_tabI, evidencia="observado",
    benigno="Alguns administradores preenchem o campo com o VALOR cedido em reais "
            "em vez do percentual, ou declaram percentual por bucket (com risco e "
            "sem risco) que soma mais de 100 quando agregado. É erro de "
            "preenchimento, não de conduta — mas invalida o dado.",
    acao="Excluir o veículo das estatísticas de concentração por cedente e pedir "
         "reapresentação do informe.",
)
sinal(
    id="DI-02", pilar="5. Integridade dos dados e reportes",
    nome="Divergência entre direitos creditórios da tab I e das tabs V/VI",
    definicao="Distância relativa entre o estoque de DC do balanço (tab I) e o "
              "somatório por prazo de vencimento (tabs V e VI), acima do p95.",
    formula="desc_tabV = |dc_tabI - (V_A+V_B+VI_A+VI_B)| / dc_tabI",
    grupo="Veículos com DC (tab I) >= R$ 50 mi",
    grupo_f=lambda d: d.dc_tabI >= 5e7,
    avaliavel=lambda d: d._obs & d.dc_tabI.gt(0) & d.desc_tabV.notna(),
    valor=lambda d: d.desc_tabV,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="média", persistencia=3,
    mat_rs=lambda d: (d.dc_tabI - d.base_inad).abs(), evidencia="derivado",
    benigno="A tab I reporta VALOR CONTÁBIL (líquido de ajuste a valor presente e "
            "de provisão) e as tabs V/VI reportam o FLUXO NOMINAL a vencer. Em "
            "carteiras de longo prazo com desconto relevante, a diferença é "
            "aritmética e esperada, não erro.",
    acao="Estimar a taxa de desconto implícita na diferença: se ela for "
         "compatível com o prazo médio da carteira, é ajuste a valor presente; se "
         "não for, é inconsistência de reporte.",
)
sinal(
    id="DI-03", pilar="5. Integridade dos dados e reportes",
    nome="Cedentes não declarados em carteira de direitos creditórios material",
    definicao="Nenhum cedente com percentual válido informado na tab I, apesar de "
              "o veículo carregar estoque relevante de direitos creditórios: o "
              "pilar de concentração fica cego para esse veículo.",
    formula="pr_max IS NULL (nenhum PR_CEDENTE em [0,100] declarado) com dc_tabI "
            ">= R$ 200 mi",
    grupo="Veículos com DC (tab I) >= R$ 200 mi",
    grupo_f=lambda d: d.dc_tabI >= 2e8,
    avaliavel=lambda d: d._obs & d.dc_tabI.ge(2e8),
    valor=lambda d: np.where(d.dc_tabI >= 2e8, d.pr_max.isna().astype(float), np.nan),
    material=lambda d: d.dc_tabI >= 2e8,
    material_txt="DC >= R$ 200 mi",
    limiar=("ocorrencia",), severidade="baixa", persistencia=3,
    mat_rs=lambda d: d.dc_tabI, evidencia="observado",
    benigno="A não declaração é ENDÊMICA — cerca de 57% dos veículos com DC acima "
            "de R$ 200 mi não informam cedente válido no corte. Por isso o sinal "
            "discrimina pouco entre veículos e recebe severidade baixa: ele "
            "documenta uma lacuna do informe mensal, não um desvio individual. "
            "FIDC que compra crédito originado por si (crédito direto) pode "
            "legitimamente não ter cedente terceiro a declarar.",
    acao="Tratar como marcador de NÃO AVALIABILIDADE do pilar 3 para o veículo, e "
         "buscar a concentração por outra via (regulamento, relatório do "
         "custodiante, CDA).",
)
sinal(
    id="DI-04", pilar="5. Integridade dos dados e reportes",
    nome="Soma das séries de cotas incompatível com o patrimônio líquido",
    definicao="Somatório de quantidade x valor da cota de todas as séries (tab "
              "X.2) distante do PL da tab IV além do p99 do mercado.",
    formula="ser_vs_pl = |SUM(TAB_X_QT_COTA * TAB_X_VL_COTA) - VL_PL| / VL_PL",
    grupo="Veículos com PL > 0 e séries informadas",
    grupo_f=lambda d: (d.VL_PL > 0) & d.v_tot.notna(),
    avaliavel=lambda d: d._obs & d.VL_PL.gt(0) & d.ser_vs_pl.notna(),
    valor=lambda d: d.ser_vs_pl,
    material=lambda d: d.VL_PL >= 1e7,
    material_txt="PL >= R$ 10 mi",
    limiar=("pct", 0.99, ">="), severidade="média", persistencia=2,
    mat_rs=lambda d: (d.v_tot - d.VL_PL).abs(), evidencia="derivado",
    benigno="Amortização declarada entre a data da cota e o fechamento, ou séries "
            "encerradas ainda listadas, produzem descolamento temporário. Erro de "
            "arredondamento em fundos com cota de valor muito alto também aparece.",
    acao="Reconciliar série a série com a tab X.4 (captações, amortizações e "
         "resgates) do mesmo mês.",
)
sinal(
    id="DI-05", pilar="5. Integridade dos dados e reportes",
    nome="Lacuna de reporte na série mensal",
    definicao="Competência sem informe entre a primeira e a última competência "
              "observadas do veículo na janela de 25 meses — descontinuidade que "
              "não se explica por entrada ou saída do universo.",
    formula="mês ausente com ord_ini < ord < ord_fim na grade CNPJ x competência",
    grupo="Todos os veículos do painel canônico",
    grupo_f=lambda d: d._obs,
    avaliavel=lambda d: d._obs,
    valor=lambda d: d.lacuna_ac.astype(float),
    material=lambda d: d.VL_PL >= 1e7,
    material_txt="PL >= R$ 10 mi",
    limiar=("fixo", 1, ">="), severidade="média", persistencia=1,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Reapresentação de informe fora do zip da competência, migração "
            "fundo->classe na adaptação à RCVM 175 e mudança de CNPJ informante "
            "geram lacuna aparente sem inadimplemento de dever.",
    acao="Conferir o CNPJ da classe e do fundo no mapa de adaptação antes de "
         "tratar como falta de entrega.",
)
sinal(
    id="DI-06", pilar="5. Integridade dos dados e reportes",
    nome="Carteira estagnada ao centavo por três meses ou mais",
    definicao="Valor da carteira (tab I.2) idêntico ao centavo em três ou mais "
              "competências consecutivas — indício de reporte repetido em vez de "
              "reapurado.",
    formula="carteira(t) = carteira(t-1) por >= 3 meses consecutivos",
    grupo="Veículos com carteira > 0 informada",
    grupo_f=lambda d: d.carteira > 0,
    avaliavel=lambda d: d._obs & d.carteira.notna(),
    valor=lambda d: d.meses_estagnado,
    material=lambda d: d.carteira >= 1e7,
    material_txt="carteira >= R$ 10 mi",
    limiar=("fixo", 3, ">="), severidade="média", persistencia=1,
    mat_rs=lambda d: d.carteira, evidencia="observado",
    benigno="Fundo com carteira única de um contrato longo, sem amortização no "
            "período, legitimamente reporta o mesmo valor. Ativo bloqueado por "
            "decisão judicial também congela o saldo.",
    acao="Verificar se PL e rentabilidade também estão congelados: carteira "
         "parada com PL variando é convivência normal; tudo parado é reporte "
         "automático não reapurado.",
)
sinal(
    id="DI-07", pilar="5. Integridade dos dados e reportes",
    nome="Componentes do ativo excedem a carteira declarada",
    definicao="Soma dos componentes identificáveis da carteira (DC com e sem "
              "risco, cotas de FIDC, valores mobiliários, títulos públicos, CDB) "
              "maior que a carteira total informada — impossibilidade aritmética.",
    formula="(I2A + I2B + I2H + I2I + I2C + I2D + I2E) > 1.005 * TAB_I2_VL_CARTEIRA",
    grupo="Veículos com carteira (tab I.2) > 0",
    grupo_f=lambda d: d.carteira > 0,
    avaliavel=lambda d: d._obs & d.carteira.gt(0) & d.exc_comp.notna(),
    valor=lambda d: d.exc_comp,
    material=lambda d: d.carteira >= 1e7,
    material_txt="carteira >= R$ 10 mi",
    limiar=("fixo", 1.005, ">="), severidade="alta", persistencia=1,
    mat_rs=lambda d: (d.soma_comp - d.carteira).clip(lower=0), evidencia="derivado",
    benigno="Dupla classificação de um mesmo ativo em duas rubricas (por exemplo, "
            "cota de FIDC contabilizada também como valor mobiliário) explica "
            "excedentes pequenos. Acima de poucos por cento, não há explicação "
            "contábil.",
    acao="Solicitar a composição analítica da carteira ao administrador e "
         "conciliar rubrica a rubrica.",
)

# ---------------- PILAR 6 — RISCO JUDICIAL E REGULATÓRIO -------------------
sinal(
    id="JR-01", pilar="6. Risco judicial e regulatório",
    nome="Créditos em ação judicial de cobrança relevantes",
    definicao="Valor de direitos creditórios em ação judicial (I.2.A.8) material "
              "em termos absolutos — a recuperação depende do Judiciário.",
    formula="TAB_I2A8_VL_CRED_ACAO_JUDIC >= R$ 5 mi",
    grupo="Veículos que reportam valor positivo no campo I.2.A.8",
    grupo_f=lambda d: d.judic > 0,
    avaliavel=lambda d: d._obs & d.judic.notna() & d.judic.gt(0),
    valor=lambda d: np.where(d.judic > 0, d.judic, np.nan),
    material=lambda d: d.judic >= 5e6,
    material_txt="créditos em ação judicial >= R$ 5 mi",
    limiar=("ocorrencia",), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.judic, evidencia="observado",
    benigno="Cobrança judicial é a etapa NORMAL do ciclo de recuperação de "
            "qualquer carteira de crédito madura; sua ausência é que seria "
            "estranha. O campo é preenchido por menos de 1% dos veículos, logo o "
            "sinal mede tanto litígio quanto disposição a reportar.",
    acao="Comparar o valor em ação judicial com a provisão já constituída e com o "
         "estoque vencido acima de 360 dias (QA-05).",
)
sinal(
    id="JR-02", pilar="6. Risco judicial e regulatório",
    nome="Carteira concentrada em créditos judiciais e precatórios",
    definicao="Créditos judiciais (tab II.J) somados a precatórios (tab II.I.1) "
              "acima do p90 da razão sobre a carteira segmentada.",
    formula="jud_seg = (TAB_II_J_VL_JUDICIAL + TAB_II_I1_VL_PRECAT) / TAB_II_VL_CARTEIRA",
    grupo="Veículos com carteira segmentada (tab II) > 0",
    grupo_f=lambda d: d.cart_seg > 0,
    avaliavel=lambda d: d._obs & d.cart_seg.gt(0) & d.jud_seg.notna(),
    valor=lambda d: d.jud_seg,
    material=lambda d: d.cart_seg >= 5e7,
    material_txt="carteira segmentada >= R$ 50 mi",
    limiar=("pct", 0.90, ">="), severidade="baixa", persistencia=3,
    mat_rs=lambda d: (d.sg_j.fillna(0) + d.seg_precat.fillna(0)), evidencia="observado",
    benigno="FIDC-NP de precatórios e de crédito judicial é categoria regulada, "
            "destinada a investidor profissional, e sua carteira É judicial por "
            "definição. O sinal descreve o mandato, não um desvio.",
    acao="Tratar como marcador de SEGMENTO para escolher o grupo de comparação "
         "correto nos demais sinais, principalmente QA-01 e QA-05.",
)
sinal(
    id="JR-03", pilar="6. Risco judicial e regulatório",
    nome="Classificação SCR concentrada em faixas E a H",
    definicao="Parcela das operações reportadas ao SCR classificadas entre E e H "
              "(Res. CMN 2.682) acima do p95 do mercado.",
    formula="scr_eh = (E+F+G+H) / (AA+A+B+C+D+E+F+G+H) sobre TAB_X_SCR_RISCO_OPER_*",
    grupo="Veículos com DC >= R$ 50 mi e bloco X.8 preenchido (total > 0)",
    grupo_f=lambda d: (d.dc_tabI >= 5e7) & (d.scr_tot > 0),
    avaliavel=lambda d: d._obs & d.scr_tot.gt(0) & d.scr_eh.notna(),
    valor=lambda d: d.scr_eh,
    material=lambda d: d.dc_tabI >= 5e7,
    material_txt="DC >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="alta", persistencia=3,
    mat_rs=lambda d: d.scr_eh * d.scr_tot, evidencia="observado",
    benigno="O bloco X.8 cobre apenas crédito de origem financeira rastreável no "
            "SCR: duplicatas mercantis, precatórios e crédito judicial ficam de "
            "fora por construção, e um fundo com pouca base no SCR pode ter "
            "percentual E-H alto sobre uma amostra pequena e não representativa.",
    acao="Checar a razão entre o total classificado no SCR e o DC do fundo: "
         "percentual E-H sobre menos de 20% da carteira não é conclusivo.",
)
sinal(
    id="JR-04", pilar="6. Risco judicial e regulatório",
    nome="Classe ou fundo em liquidação com patrimônio relevante",
    definicao="Situação cadastral 'Em Liquidação' no registro CVM da classe ou do "
              "fundo, com PL ainda material.",
    formula="registro_classe.Situacao = 'Em Liquidação' OR registro_fundo.Situacao "
            "= 'Em Liquidação'",
    grupo="Veículos com registro CVM localizado",
    grupo_f=lambda d: d.em_liquidacao.notna(),
    avaliavel=lambda d: d._obs & d.em_liquidacao.notna(),
    valor=lambda d: d.em_liquidacao,
    material=lambda d: d.VL_PL >= 1e7,
    material_txt="PL >= R$ 10 mi",
    limiar=("ocorrencia",), severidade="alta", persistencia=1,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Liquidação ORDINÁRIA por decurso de prazo do regulamento é o "
            "encerramento normal de um FIDC de prazo determinado e não indica "
            "problema algum. O registro não distingue liquidação ordinária de "
            "liquidação por deliberação de assembleia em crise.",
    acao="Ler a ata de assembleia que deliberou a liquidação e verificar se a "
         "amortização das sêniores está sendo honrada no cronograma.",
)
sinal(
    id="JR-05", pilar="6. Risco judicial e regulatório",
    nome="Débito tributário declarado relevante",
    definicao="Campo de débito tributário do bloco X.8 positivo e acima de 1% do "
              "patrimônio líquido.",
    formula="TAB_X_DEBITO_TRIBUT / VL_PL >= 0.01, com TAB_X_DEBITO_TRIBUT > 0",
    grupo="Veículos com PL > 0 e campo de débito tributário preenchido",
    grupo_f=lambda d: (d.VL_PL > 0) & d.deb_trib.notna() & (d.deb_trib > 0),
    avaliavel=lambda d: d._obs & d.VL_PL.gt(0) & d.deb_trib.notna() & d.deb_trib.gt(0),
    valor=lambda d: np.where((d.VL_PL > 0) & (d.deb_trib > 0), d.deb_trib / d.VL_PL, np.nan),
    material=lambda d: d.VL_PL >= 1e7,
    material_txt="PL >= R$ 10 mi",
    limiar=("fixo", 0.01, ">="), severidade="média", persistencia=2,
    mat_rs=lambda d: d.deb_trib, evidencia="observado",
    benigno="A semântica do campo é ambígua no leiaute: em vários informes o valor "
            "excede o próprio PL, o que sugere que parte dos administradores "
            "reporta o ESTOQUE DE CRÉDITOS COM DÉBITO TRIBUTÁRIO associado, e não "
            "uma obrigação do fundo. Enquanto a ambiguidade não for resolvida, o "
            "sinal mede reporte, não passivo.",
    acao="Confirmar o significado do campo com o administrador e contra as "
         "demonstrações financeiras antes de qualquer uso — este sinal NÃO deve "
         "ser usado isoladamente.",
)

# ---------------- PILAR 7 — INCONSISTÊNCIAS CONTÁBEIS E ECONÔMICAS ---------
sinal(
    id="IC-01", pilar="7. Inconsistências contábeis e econômicas",
    nome="Identidade patrimonial violada",
    definicao="Carteira maior que o ativo total, ou patrimônio líquido maior que "
              "o ativo total — impossibilidades contábeis diretas.",
    formula="carteira > 1.005*TAB_I_VL_ATIVO OR VL_PL > 1.005*TAB_I_VL_ATIVO",
    grupo="Veículos com ativo total > 0",
    grupo_f=lambda d: d.ativo_tot > 0,
    avaliavel=lambda d: d._obs & d.ativo_tot.gt(0) & d.VL_PL.notna() & d.carteira.notna(),
    valor=lambda d: np.where(
        (d.ativo_tot > 0) & d.VL_PL.notna() & d.carteira.notna(),
        ((d.carteira > 1.005 * d.ativo_tot) | (d.VL_PL > 1.005 * d.ativo_tot)).astype(float),
        np.nan),
    material=lambda d: d.ativo_tot >= 1e7,
    material_txt="ativo total >= R$ 10 mi",
    limiar=("ocorrencia",), severidade="crítica", persistencia=1,
    mat_rs=lambda d: (d[["carteira", "VL_PL"]].max(axis=1) - d.ativo_tot).clip(lower=0),
    evidencia="derivado",
    benigno="Erro de digitação de casa decimal em um único campo produz o efeito "
            "sem qualquer irregularidade econômica; a tolerância de 0,5% já "
            "absorve arredondamento.",
    acao="Pedir reapresentação do informe da competência e verificar se o erro se "
         "repete nos meses vizinhos.",
)
sinal(
    id="IC-02", pilar="7. Inconsistências contábeis e econômicas",
    nome="Rentabilidade da cota sênior implausivelmente alta",
    definicao="Melhor rentabilidade mensal entre as séries sêniores acima do p99 "
              "do mercado — sênior é a classe de retorno-alvo limitado.",
    formula="rent_sen_max = MAX(TAB_X_VL_RENTAB_MES onde TIPO_COTA='senior')",
    grupo="Veículos com série sênior emitida (VL_SERIE > 0)",
    grupo_f=lambda d: d.v_sen > 0,
    avaliavel=lambda d: d._obs & d.v_sen.gt(0) & d.rent_sen_max.notna(),
    valor=lambda d: d.rent_sen_max,
    material=lambda d: d.VL_PL >= 5e7,
    material_txt="PL >= R$ 50 mi",
    limiar=("pct", 0.99, ">="), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.v_sen.fillna(0), evidencia="observado",
    benigno="Reversão de provisão excessiva, recebimento de crédito antes baixado "
            "e recomposição de série após período negativo produzem meses "
            "excepcionais legítimos. Séries de valor pequeno amplificam "
            "percentuais.",
    acao="Verificar se o retorno excepcional é compatível com o resultado da "
         "carteira no mesmo mês; retorno de sênior descolado do resultado do fundo "
         "sugere marcação inadequada da cota.",
)
sinal(
    id="IC-03", pilar="7. Inconsistências contábeis e econômicas",
    nome="Resultado positivo na sênior com inadimplência alta e provisão nula",
    definicao="Sênior rendendo positivo no mês enquanto a taxa de inadimplência "
              "está no quartil superior do mercado e nenhuma provisão foi "
              "constituída — resultado sem reconhecimento de perda.",
    formula="rent_sen_min > 0 AND tx_inad >= p75(mercado) AND prov = 0",
    grupo="Veículos com sênior emitida, tx_inad computável e inadimplência > 0",
    grupo_f=lambda d: (d.v_sen > 0) & d.tx_inad.notna() & (d.inad > 0),
    avaliavel=lambda d: (d._obs & d.v_sen.gt(0) & d.tx_inad.notna()
                         & d.rent_sen_min.notna() & d.inad.gt(0)),
    valor=lambda d: np.where(
        (d.v_sen > 0) & d.tx_inad.notna() & d.rent_sen_min.notna() & (d.inad > 0),
        ((d.rent_sen_min > 0) & (d.tx_inad >= 0.1319) & (d.prov <= 0)).astype(float),
        np.nan),
    material=lambda d: d.inad >= 1e7,
    material_txt="inadimplência >= R$ 10 mi",
    limiar=("ocorrencia",), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.inad, evidencia="derivado",
    benigno="Coobrigação plena do cedente ou seguro de crédito transferem a perda "
            "para fora do fundo, e nesse caso resultado positivo sem provisão é "
            "correto. Fundo sem aquisição substancial de risco (I.2.B) está no "
            "mesmo caso.",
    acao="Ler a cláusula de coobrigação e conferir na tab VII.D se as recompras "
         "efetivamente ocorreram no volume compatível com o estoque vencido.",
)
sinal(
    id="IC-04", pilar="7. Inconsistências contábeis e econômicas",
    nome="Colapso de patrimônio líquido em um único mês",
    definicao="Variação mensal do PL no p1 inferior da distribuição do mercado, "
              "partindo de base relevante.",
    formula="var_pl_m = VL_PL(t)/VL_PL(t-1) - 1",
    grupo="Veículos com PL do mês anterior >= R$ 10 mi",
    grupo_f=lambda d: d.VL_PL_l1 >= 1e7,
    avaliavel=lambda d: d._obs & d.var_pl_m.notna(),
    valor=lambda d: d.var_pl_m,
    material=lambda d: d.VL_PL_l1 >= 1e7,
    material_txt="PL do mês anterior >= R$ 10 mi",
    limiar=("pct", 0.01, "<="), severidade="alta", persistencia=1,
    mat_rs=lambda d: (d.VL_PL_l1 - d.VL_PL).clip(lower=0), evidencia="derivado",
    benigno="Amortização programada de série sênior, resgate de cotista único e "
            "encerramento ordenado do fundo produzem quedas abruptas totalmente "
            "planejadas. Cisão de classe também transfere PL sem perda.",
    acao="Cruzar com a tab X.4: queda acompanhada de amortização/resgate "
         "equivalente é devolução de capital; queda sem contrapartida de "
         "pagamento é perda.",
)
sinal(
    id="IC-05", pilar="7. Inconsistências contábeis e econômicas",
    nome="Crescimento explosivo do patrimônio em 12 meses",
    definicao="Crescimento do PL contra a mesma competência do ano anterior acima "
              "do p98 do mercado, partindo de base relevante.",
    formula="cresc_12 = VL_PL(t)/VL_PL(t-12m) - 1",
    grupo="Veículos com PL de 12 meses antes >= R$ 10 mi",
    grupo_f=lambda d: d.VL_PL_l12 >= 1e7,
    avaliavel=lambda d: d._obs & d.cresc_12.notna(),
    valor=lambda d: d.cresc_12,
    material=lambda d: (d.VL_PL_l12 >= 1e7) & (d.VL_PL >= 1e8),
    material_txt="PL de 12m antes >= R$ 10 mi e PL atual >= R$ 100 mi",
    limiar=("pct", 0.98, ">="), severidade="média", persistencia=2,
    mat_rs=lambda d: (d.VL_PL - d.VL_PL_l12).clip(lower=0), evidencia="derivado",
    benigno="Fundo em ramp-up após a constituição cresce muitas vezes seu "
            "tamanho por desenho. Captação de nova série sênior de um investidor "
            "institucional produz salto legítimo. Incorporação de outro veículo "
            "também.",
    acao="Verificar se o crescimento do PL veio acompanhado de crescimento "
         "proporcional da carteira e de diversificação de cedentes; crescimento "
         "com cedente único e sem carteira nova é o padrão de carrossel.",
)
sinal(
    id="IC-06", pilar="7. Inconsistências contábeis e econômicas",
    nome="Descolamento entre patrimônio e carteira em 12 meses",
    definicao="Diferença entre o crescimento logarítmico do PL e o da carteira em "
              "12 meses acima do p98: o patrimônio cresce sem que o ativo de "
              "crédito acompanhe.",
    formula="desloc_12 = ln(PL(t)/PL(t-12m)) - ln(carteira(t)/carteira(t-12m))",
    grupo="Veículos com PL e carteira > 0 em t e em t-12m",
    grupo_f=lambda d: d.desloc_12.notna(),
    avaliavel=lambda d: d._obs & d.desloc_12.notna(),
    valor=lambda d: d.desloc_12,
    material=lambda d: d.VL_PL >= 1e8,
    material_txt="PL >= R$ 100 mi",
    limiar=("pct", 0.98, ">="), severidade="média", persistencia=2,
    mat_rs=lambda d: (d.VL_PL - d.carteira).clip(lower=0), evidencia="derivado",
    benigno="Fundo que captou e ainda não alocou mantém caixa em títulos "
            "públicos: PL cresce, carteira de crédito não. É prudência de "
            "alocação, não anomalia. Mudança de estratégia para renda fixa também "
            "produz o efeito.",
    acao="Ver onde está o ativo não alocado (I.2.C a I.2.E): caixa em título "
         "público é benigno; ativo não identificado no informe merece exame.",
)

# ---------------- PILAR 8 — PLD/FTP, LASTRO E MOVIMENTAÇÃO -----------------
sinal(
    id="PO-01", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Giro anual da carteira no extremo do mercado",
    definicao="Aquisições de direitos creditórios em 12 meses sobre a carteira "
              "média do período, acima do p98 — volume de movimentação "
              "desproporcional ao estoque.",
    formula="aq_giro = SUM_12m(VII_A1_2 + VII_A2_2) / MEDIA_12m(TAB_I2_VL_CARTEIRA)",
    grupo="Veículos com carteira média 12m > 0 e >= 10 das 12 competências",
    grupo_f=lambda d: d.aq_giro.notna(),
    avaliavel=lambda d: d._obs & d.aq_giro.notna(),
    valor=lambda d: d.aq_giro,
    material=lambda d: d.cart_med12 >= 5e7,
    material_txt="carteira média 12m >= R$ 50 mi",
    limiar=("pct", 0.98, ">="), severidade="média", persistencia=2,
    mat_rs=lambda d: d.aq_12m, evidencia="derivado",
    benigno="Duplicata mercantil de 30 dias gira 12 vezes ao ano por definição "
            "aritmética; antecipação de cartão gira ainda mais. Giro alto é a "
            "assinatura do factoring legítimo, não de lavagem.",
    acao="Comparar o giro com o prazo médio declarado nas tabs V/VI: giro "
         "incompatível com o prazo médio da própria carteira é que é anômalo.",
)
sinal(
    id="PO-02", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Rolagem elevada por recompra e substituição",
    definicao="Recompras (VII.D) somadas a substituições (VII.C) em 12 meses "
              "sobre a carteira média, acima do p95 — mecanismo clássico de "
              "mascarar atraso trocando o papel vencido por papel novo.",
    formula="roll_giro = SUM_12m(TAB_VII_C_2_VL_SUBST + TAB_VII_D_2_VL_RECOMPRA) "
            "/ MEDIA_12m(TAB_I2_VL_CARTEIRA)",
    grupo="Veículos com carteira média 12m > 0 e >= 10 das 12 competências",
    grupo_f=lambda d: d.roll_giro.notna(),
    avaliavel=lambda d: d._obs & d.roll_giro.notna(),
    valor=lambda d: d.roll_giro,
    material=lambda d: d.cart_med12 >= 5e7,
    material_txt="carteira média 12m >= R$ 50 mi",
    limiar=("pct", 0.95, ">="), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.roll_12m, evidencia="derivado",
    benigno="Substituição contratual de duplicata com vício formal (erro de "
            "emissão, divergência de valor) é obrigação do cedente prevista em "
            "regulamento e ocorre em volume relevante em carteiras pulverizadas. "
            "Recompra por coobrigação é a estrutura funcionando como desenhada.",
    acao="Cruzar recompra com inadimplência: recompra alta com inadimplência "
         "reportada nula é a assinatura de rolagem; recompra alta com "
         "inadimplência também alta é coobrigação atuando.",
)
sinal(
    id="PO-03", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Alienação de direitos creditórios a partes relacionadas",
    definicao="Venda de créditos ao próprio cedente ou a prestadores de serviço "
              "do fundo em 12 meses, em montante relevante frente à carteira.",
    formula="ali_rel_giro = SUM_12m(TAB_VII_B1_2_VL_CEDENTE + TAB_VII_B2_2_VL_PREST) "
            "/ MEDIA_12m(carteira) >= 0.01",
    grupo="Veículos com carteira média 12m > 0 e >= 10 das 12 competências",
    grupo_f=lambda d: d.ali_rel_giro.notna(),
    avaliavel=lambda d: d._obs & d.ali_rel_giro.notna(),
    valor=lambda d: d.ali_rel_giro,
    material=lambda d: d.cart_med12 >= 1e7,
    material_txt="carteira média 12m >= R$ 10 mi",
    limiar=("fixo", 0.01, ">="), severidade="alta", persistencia=1,
    mat_rs=lambda d: d.ali_rel_12m, evidencia="observado",
    benigno="Devolução de crédito ao cedente por vício de origem, ou exercício de "
            "opção de recompra prevista, aparece nesta rubrica sem qualquer "
            "conflito. O campo é preenchido por pouquíssimos veículos, o que "
            "torna o sinal raro e de alta especificidade, mas de baixa cobertura.",
    acao="Obter o preço de venda e compará-lo ao valor contábil (PO-04): "
         "alienação a parte relacionada abaixo do valor contábil transfere valor "
         "do fundo para o originador.",
)
sinal(
    id="PO-04", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Deságio anômalo em alienação a terceiros",
    definicao="Preço obtido na venda de créditos a terceiros sobre o valor "
              "contábil dos mesmos créditos, abaixo do p5 do mercado.",
    formula="desagio_terc = TAB_VII_B3_2_VL_TERCEIRO / TAB_VII_B3_3_VL_CONTAB_TERCEIRO "
            "<= 0,50 (deságio superior a 50% do valor contábil)",
    grupo="Veículos com alienação a terceiros e valor contábil ambos > 0",
    grupo_f=lambda d: d.desagio_terc.notna(),
    avaliavel=lambda d: d._obs & d.desagio_terc.notna(),
    valor=lambda d: d.desagio_terc,
    material=lambda d: d.ali_terc >= 1e6,
    material_txt="alienação a terceiros >= R$ 1 mi",
    limiar=("fixo", 0.50, "<="), severidade="média", persistencia=1,
    mat_rs=lambda d: (d.ali_terc_cont.fillna(0) - d.ali_terc.fillna(0)).clip(lower=0),
    evidencia="observado",
    benigno="Venda de carteira já vencida e provisionada acontece a poucos "
            "centavos por real e é exatamente o preço de mercado do ativo. "
            "Deságio profundo é esperado em cessão de carteira em recuperação.",
    acao="Verificar se o crédito vendido já estava provisionado: deságio sobre "
         "ativo provisionado é realização de perda já reconhecida; sobre ativo "
         "não provisionado, é perda escondida até aquele momento.",
)
sinal(
    id="PO-05", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Cedente pessoa física com participação relevante",
    definicao="Documento de cedente com 11 dígitos (CPF) associado a percentual "
              "declarado de 20% ou mais da carteira — originação por pessoa "
              "física em escala, ponto de atenção de PLD/FTP.",
    formula="pr_max_cpf >= 20, com pr_max_cpf = MAX(PR_CEDENTE) sobre "
            "length(digits(DOC_CEDENTE)) = 11",
    grupo="Veículos que declaram cedentes com percentual válido",
    grupo_f=lambda d: d.pr_max.notna(),
    avaliavel=lambda d: d._obs & d.pr_max.notna(),
    valor=lambda d: d.pr_max_cpf.fillna(0),
    material=lambda d: d.dc_tabI >= 1e7,
    material_txt="DC >= R$ 10 mi",
    limiar=("fixo", 20, ">="), severidade="média", persistencia=3,
    mat_rs=lambda d: d.pr_max_cpf.fillna(0) / 100.0 * d.dc_tabI, evidencia="observado",
    benigno="FIDC do agronegócio compra CPR de produtor rural pessoa física, e "
            "FIDC de precatórios compra crédito de credor pessoa física: nos dois "
            "casos o cedente PF é o modelo de negócio. Também há preenchimento "
            "errado de CNPJ truncado a 11 dígitos.",
    acao="Verificar o segmento (tab II) antes de qualquer leitura de PLD; se não "
         "for agro nem judicial, identificar a pessoa física e sua capacidade "
         "econômica de originar o volume declarado.",
)
sinal(
    id="PO-06", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Aquisição relevante de créditos já vencidos ou inadimplentes",
    definicao="Compras de direitos creditórios vencidos e inadimplentes (VII.A.4 "
              "e VII.A.5) em 12 meses sobre a carteira média, acima do p99.",
    formula="aq_ruim_giro = SUM_12m(TAB_VII_A4_2 + TAB_VII_A5_2) / MEDIA_12m(carteira)",
    grupo="Veículos com carteira média 12m > 0 e >= 10 das 12 competências",
    grupo_f=lambda d: d.aq_ruim_giro.notna(),
    avaliavel=lambda d: d._obs & d.aq_ruim_giro.notna(),
    valor=lambda d: d.aq_ruim_giro,
    material=lambda d: d.cart_med12 >= 1e7,
    material_txt="carteira média 12m >= R$ 10 mi",
    limiar=("pct", 0.99, ">="), severidade="baixa", persistencia=2,
    mat_rs=lambda d: d.aq_ruim_12m, evidencia="observado",
    benigno="É literalmente o mandato do FIDC-NP: comprar crédito não performado "
            "e inadimplente com deságio para recuperar. O sinal só é informativo "
            "quando o veículo se apresenta como FIDC padronizado.",
    acao="Confirmar o tipo do fundo (padronizado x NP) no registro: aquisição de "
         "crédito podre por fundo PADRONIZADO é que exige explicação.",
)
sinal(
    id="PO-07", pilar="8. PLD/FTP, lastro e movimentação",
    nome="Liquidez de curto prazo nula em condomínio aberto",
    definicao="Ativos conversíveis em caixa em até 30 dias (X.5) iguais a zero "
              "num fundo de condomínio ABERTO, onde o cotista pode pedir resgate.",
    formula="(TAB_X_VL_LIQUIDEZ_0 + TAB_X_VL_LIQUIDEZ_30) = 0 AND CONDOM='ABERTO'",
    grupo="Veículos de condomínio aberto com PL > 0",
    grupo_f=lambda d: (d.CONDOM == "ABERTO") & (d.VL_PL > 0),
    avaliavel=lambda d: (d._obs & d.CONDOM.notna() & d.VL_PL.gt(0)
                         & (d.liq0.notna() | d.liq30.notna())),
    valor=lambda d: np.where(
        (d.CONDOM == "ABERTO") & (d.VL_PL > 0) & (d.liq0.notna() | d.liq30.notna()),
        d.liq_curta, np.nan),
    material=lambda d: d.VL_PL >= 1e7,
    material_txt="PL >= R$ 10 mi",
    limiar=("fixo", 0.0, "<="), severidade="alta", persistencia=2,
    mat_rs=lambda d: d.VL_PL, evidencia="observado",
    benigno="Condomínio aberto com prazo de carência longo e janela de resgate "
            "anual não precisa de liquidez diária. Muitos administradores "
            "simplesmente não preenchem o bloco X.5, e zero ali significa 'não "
            "informado' — por isso o sinal exige que ao menos um dos dois campos "
            "esteja presente.",
    acao="Ler a política de resgate no regulamento (carência e prazo de "
         "pagamento) antes de concluir por descasamento.",
)


# ---------------------------------------------------------------------------
# 3. Avaliação
# ---------------------------------------------------------------------------
def calcular_limiar(d_corte: pd.DataFrame, sg: dict) -> tuple:
    """Retorna (limiar, texto_origem, n_grupo)."""
    tipo = sg["limiar"][0]
    grupo = sg["grupo_f"](d_corte) & sg["avaliavel"](d_corte) & sg["material"](d_corte)
    n = int(grupo.sum())
    if tipo == "ocorrencia":
        return 1.0, "ocorrência binária: não há distribuição contínua a percentilar", n
    if tipo == "fixo":
        _, val, sent = sg["limiar"]
        return float(val), (f"limiar fixo {val} ({sent}) — ancorado em definição "
                            f"contábil/regulatória, não em percentil (grupo de "
                            f"comparação com n={n})"), n
    _, q, sent = sg["limiar"]
    v = pd.Series(sg["valor"](d_corte), index=d_corte.index)[grupo].astype(float).dropna()
    if len(v) < 30:
        return np.nan, f"grupo insuficiente (n={len(v)}) para percentilar", n
    lim = float(v.quantile(q))
    return lim, (f"p{int(q*100)} da distribuição observada no grupo de comparação "
                 f"em {CORTE} (n={len(v)}, mediana={v.median():.4g}); dispara {sent}"), n


def avaliar(d: pd.DataFrame) -> tuple:
    # universo canônico do corte: apenas veículos que efetivamente informaram
    # a competência 2026-06-30 (a grade completa carrega CNPJs que saíram antes)
    d_corte = d[(d.DT_COMPTC == CORTE) & d._obs]
    cat_rows, av_frames = [], []

    for sg in S:
        lim, origem, n_grp = calcular_limiar(d_corte, sg)
        sent = sg["limiar"][2] if sg["limiar"][0] != "ocorrencia" else ">="

        val = pd.Series(np.asarray(sg["valor"](d), dtype="float64"), index=d.index)
        aval = sg["avaliavel"](d).fillna(False).astype(bool)
        grp = sg["grupo_f"](d).fillna(False).astype(bool)
        mat = sg["material"](d)
        mat = (mat if isinstance(mat, pd.Series) else pd.Series(mat, index=d.index))
        mat = mat.fillna(False).astype(bool)

        aval = aval & grp & val.notna()
        if np.isnan(lim):
            disp = pd.Series(False, index=d.index)
        elif sent == ">=":
            disp = aval & mat & (val >= lim)
        else:
            disp = aval & mat & (val <= lim)

        av_frames.append(pd.DataFrame({
            "CNPJ": d.CNPJ, "DT_COMPTC": d.DT_COMPTC, "sinal_id": sg["id"],
            "valor": val.where(aval), "avaliavel": aval, "material": mat,
            "disparo": disp, "mat_rs": pd.Series(
                np.asarray(sg["mat_rs"](d), dtype="float64"), index=d.index).where(disp),
        }))

        # Cobertura medida no corte sobre o universo canônico (veículos que
        # informaram 2026-06-30). "Avaliável" = pertence ao grupo de comparação
        # do sinal E tem todos os campos necessários preenchidos. Veículo fora
        # do grupo conta como NÃO avaliável — é a leitura estrita: não sabemos
        # nada sobre a qualidade do ativo de um fundo que não reporta carteira
        # de crédito.
        n_av = int(aval.loc[d_corte.index].sum())
        n_mat = int((aval & mat).loc[d_corte.index].sum())
        cat_rows.append({
            "sinal_id": sg["id"], "pilar": sg["pilar"], "nome": sg["nome"],
            "definicao": sg["definicao"], "formula": sg["formula"],
            "grupo_comparacao": sg["grupo"],
            "limiar": lim, "limiar_sentido": sent, "limiar_origem": origem,
            "severidade": sg["severidade"], "peso": PESO_SEV[sg["severidade"]],
            "materialidade": sg["material_txt"],
            "persistencia_min_meses": sg["persistencia"],
            "tipo_evidencia": sg["evidencia"],
            "explicacoes_benignas": sg["benigno"],
            "acao_investigacao": sg["acao"],
            "n_grupo_comparacao": n_grp,
            "n_universo": len(d_corte),
            "n_avaliavel": n_av,
            "n_avaliavel_e_material": n_mat,
        })

    av = pd.concat(av_frames, ignore_index=True)
    cat = pd.DataFrame(cat_rows)
    cat["cobertura_universo_pct"] = (cat.n_avaliavel / cat.n_universo * 100).round(2)
    return cat, av


def persistencia(av: pd.DataFrame) -> pd.DataFrame:
    """Meses consecutivos com disparo terminando no corte, na janela de avaliação."""
    a = av[av.DT_COMPTC.isin(MESES_AVAL)].copy()
    a = a.sort_values(["CNPJ", "sinal_id", "DT_COMPTC"])
    ordem = {m: i for i, m in enumerate(MESES_AVAL)}
    a["ord"] = a.DT_COMPTC.map(ordem)
    fim = len(MESES_AVAL) - 1

    def streak(g):
        d = dict(zip(g["ord"], g["disparo"]))
        n = 0
        for i in range(fim, -1, -1):
            if d.get(i, False):
                n += 1
            else:
                break
        return n

    st = a.groupby(["CNPJ", "sinal_id"]).apply(streak, include_groups=False)
    st.name = "meses_consecutivos"
    # último mês com disparo (atualidade do sinal)
    ult = (a[a.disparo].groupby(["CNPJ", "sinal_id"]).DT_COMPTC.max()
           .rename("ultimo_mes_disparo"))
    nm = a.groupby(["CNPJ", "sinal_id"]).disparo.sum().rename("meses_com_disparo")
    return pd.concat([st, ult, nm], axis=1).reset_index()


# ---------------------------------------------------------------------------
# 4. Documentação
# ---------------------------------------------------------------------------
def gerar_doc(cat: pd.DataFrame, sig: pd.DataFrame, sc: pd.DataFrame,
              faixas: tuple) -> None:
    q90, q99 = faixas
    n_univ = int(cat.n_universo.iloc[0])
    L = []
    A = L.append

    A("# Metodologia das red flags de FIDC — taxonomia v2 (oito pilares)\n")
    A("> **AVISO — METODOLOGIA EXPERIMENTAL.** Os pesos por severidade e os "
      "cortes das faixas de atenção são julgamento de especialista informado "
      "pela distribuição do mercado, **não** um modelo calibrado. Enquanto não "
      "houver backtest contra eventos realizados (liquidação extrajudicial, "
      "inadimplemento de série sênior, intervenção do regulador, processo "
      "sancionador), o score serve para **ordenar atenção supervisória** e nada "
      "mais. Score alto **não** é indício de irregularidade: é indício de que o "
      "veículo se afasta do padrão do mercado em dimensões que, em episódios "
      "públicos passados, precederam problemas — e também é o que se espera de "
      "fundos cujo mandato é justamente comprar crédito problemático.\n")
    A(f"- Data de corte: **{CORTE}**")
    A(f"- Universo canônico: **{n_univ:,} veículos** informantes na competência "
      "de corte (view `painel_saneado`)".replace(",", "."))
    A(f"- Janela de avaliação (persistência): **{len(MESES_AVAL)} competências** "
      f"({MESES_AVAL[0]} a {MESES_AVAL[-1]})")
    A(f"- Janela de dados carregada: **{len(MESES)} competências** "
      f"({MESES[0]} a {MESES[-1]}), para permitir defasagem de 12 meses e "
      "janelas móveis anuais")
    A(f"- Sinais implementados: **{len(cat)}**, distribuídos em 8 pilares")
    A("- Reprodução: `python3 scripts/13_red_flags_v2.py`\n")

    A("## 1. Regras de construção\n")
    A("**1.1 Ausente nunca vira zero.** Cada sinal declara explicitamente sua "
      "condição de avaliabilidade. Se o campo necessário é nulo — ou se o "
      "denominador é nulo ou zero, situação que no informe mensal da CVM é "
      "indistinguível de 'não reportado', porque o leiaute preenche zeros — o "
      "sinal é **não avaliável** para aquele veículo naquele mês. Não avaliável "
      "entra no denominador da cobertura; jamais é convertido em 'não disparou'.\n")
    A("**1.2 Limiar ancorado na distribuição do próprio mercado.** Todo limiar "
      "percentílico é recalculado em tempo de execução sobre o grupo de "
      "comparação do sinal, no mês de corte, e gravado no catálogo junto com o "
      "percentil usado, o n do grupo e a mediana observada. Números redondos só "
      "aparecem em sinais de **ocorrência** (identidade contábil violada, PL "
      "negativo, situação cadastral 'Em Liquidação'), onde não há distribuição "
      "contínua a percentilar, e em três limiares de definição contábil "
      "(deságio de 50%, tolerância de 0,5% em identidades, 1% do PL em débito "
      "tributário), sempre identificados como tais na coluna `limiar_origem`.\n")
    A("**1.3 Grupo de comparação explícito.** Comparar um FIDC-NP de precatórios "
      "com um FIDC de consignado é o erro metodológico mais comum na leitura "
      "desses dados. Cada sinal declara seu grupo — normalmente definido por "
      "porte de carteira e por existência efetiva da estrutura testada (só faz "
      "sentido medir subordinação em fundo que tem sênior **e** subordinada).\n")
    A("**1.4 Materialidade.** Cada sinal declara o porte mínimo abaixo do qual "
      "não vale a pena disparar. Um fundo de R$ 2 mi com inadimplência de 90% "
      "não é um problema de mercado.\n")
    A("**1.5 Persistência.** Cada sinal declara quantos meses **consecutivos**, "
      "terminando no corte, o disparo precisa aparecer para contar no score. "
      "Sinais de evento (colapso de PL, lacuna de reporte) exigem 1 mês; sinais "
      "de estado estrutural exigem 2 ou 3. A coluna `persistencia_atendida` em "
      "`rf2_sinais.csv` separa o disparo pontual do disparo persistente — "
      "ambos ficam no arquivo, por transparência.\n")
    A("**1.6 Nada de nota única.** `rf2_score_veiculo.csv` traz seis dimensões "
      "**separadas**, porque elas respondem a perguntas diferentes:\n")
    A("| Coluna | Pergunta que responde |")
    A("|---|---|")
    A("| `score_risco` (0-100) | Quanto do peso de severidade **avaliável** para "
      "este veículo efetivamente disparou de forma persistente? |")
    A("| `materialidade_max_rs` / `materialidade_soma_rs` | Quantos reais estão "
      "expostos ao maior sinal disparado (e à soma bruta de todos)? |")
    A("| `forca_evidencia` (0-1) | Que fração dos sinais disparados vem de campo "
      "**observado** no informe, e não de razão/variação **derivada**? |")
    A("| `cobertura_dados_pct` | Para que fração dos 46 sinais este veículo era "
      "sequer avaliável? |")
    A("| `persistencia_media_meses` | Há quantos meses, em média, os sinais estão "
      "acesos? |")
    A("| `atualidade` | Qual a competência mais recente com disparo? |\n")
    A("**1.7 Fórmula do score.**\n")
    A("```\nscore_risco = 100 x  Σ peso(sinais disparados E persistentes)\n"
      "                     ---------------------------------------------\n"
      "                       Σ peso(sinais avaliáveis para o veículo)\n```\n")
    A("Pesos por severidade: " + ", ".join(f"`{k}` = {v}" for k, v in PESO_SEV.items())
      + ". A normalização pelo peso **avaliável** (e não pelo peso total do "
      "catálogo) impede que baixa cobertura seja lida como baixo risco.\n")
    A("**1.8 Não classificável.** Veículo com cobertura de dados abaixo de 50% "
      "recebe `classificacao = 'não classificável'` e **nunca** é reportado como "
      "baixo risco. Ausência de sinal em veículo opaco é ausência de informação, "
      "não ausência de risco.\n")
    A(f"**1.9 Faixas de atenção.** Também definidas por percentil do próprio "
      f"score, entre os veículos classificáveis com ao menos um disparo: "
      f"`atenção alta` a partir de p99 ({q99:.2f}), `atenção média` a partir de "
      f"p90 ({q90:.2f}), `atenção baixa` para qualquer score positivo abaixo "
      f"disso.\n")

    A("## 2. Resumo por pilar\n")
    r = cat.groupby("pilar").agg(
        sinais=("sinal_id", "count"),
        cobertura=("cobertura_universo_pct", "mean"),
        disparos=("n_veiculos_disparo", "sum"),
        persistentes=("n_veiculos_disparo_persistente", "sum")).reset_index()
    A("| Pilar | Sinais | Cobertura média | Veículos-sinal disparados | "
      "…dos quais persistentes |")
    A("|---|---:|---:|---:|---:|")
    for _, x in r.iterrows():
        A(f"| {x.pilar} | {x.sinais} | {x.cobertura:.1f}% | {int(x.disparos)} | "
          f"{int(x.persistentes)} |")
    A("")

    A("## 3. Catálogo completo\n")
    for pil in cat.pilar.unique():
        A(f"### Pilar {pil}\n")
        for _, x in cat[cat.pilar == pil].iterrows():
            A(f"#### {x.sinal_id} — {x.nome}\n")
            A(f"**Definição.** {x.definicao}\n")
            A(f"**Fórmula.** `{x.formula}`\n")
            lim = ("não calculável (grupo insuficiente)" if pd.isna(x.limiar)
                   else f"`{x.limiar_sentido} {x.limiar:.6g}`")
            A(f"| Campo | Valor |")
            A(f"|---|---|")
            A(f"| Grupo de comparação | {x.grupo_comparacao} (n = "
              f"{int(x.n_grupo_comparacao)}) |")
            A(f"| Limiar | {lim} |")
            A(f"| Origem do limiar | {x.limiar_origem} |")
            A(f"| Severidade | **{x.severidade}** (peso {int(x.peso)}) |")
            A(f"| Materialidade | {x.materialidade} |")
            A(f"| Persistência mínima | {int(x.persistencia_min_meses)} "
              f"{'mês' if x.persistencia_min_meses == 1 else 'meses'} consecutivos |")
            A(f"| Tipo de evidência | {x.tipo_evidencia} |")
            A(f"| Cobertura | {x.cobertura_universo_pct:.2f}% do universo "
              f"({int(x.n_avaliavel)} de {int(x.n_universo)} veículos avaliáveis) |")
            A(f"| Veículos que disparam | {int(x.n_veiculos_disparo)} "
              f"({int(x.n_veiculos_disparo_persistente)} com persistência atendida) |")
            A("")
            A(f"**Explicações benignas (falsos positivos estruturais).** "
              f"{x.explicacoes_benignas}\n")
            A(f"**Ação de investigação.** {x.acao_investigacao}\n")

    A("## 4. Limitações e falsos positivos conhecidos\n")
    A("**4.1 O score não mede irregularidade.** Ele mede distância do padrão do "
      "mercado em dimensões associadas, em episódios públicos, a problemas "
      "posteriores. A lista dos maiores scores é povoada por fundos cujo "
      "**mandato declarado** é comprar crédito vencido — distressed, precatórios, "
      "crédito judicial. Para esses, quase todo o pilar 1 dispara por desenho. "
      "Ler o score sem ler o segmento produz acusação sem base.\n")
    A("**4.2 Zero e ausente são indistinguíveis no informe.** O leiaute da CVM "
      "preenche zeros em campos não aplicáveis. A regra 1.1 protege contra o "
      "erro mais grave (tratar ausência como valor bom), mas não consegue "
      "recuperar a informação perdida: um zero legítimo e um zero de "
      "não-preenchimento entram no mesmo balde.\n")
    A("**4.3 Cobertura é baixa em campos decisivos.** O campo de créditos "
      "performados (I.2.A.4) está descontinuado desde 2023 — cobertura 0%, e o "
      "sinal QA-06 existe para documentar essa lacuna, não para disparar. O bloco "
      "X.8 (SCR) cobre metade do estoque de crédito. Cerca de 57% dos veículos "
      "com carteira acima de R$ 200 mi não declaram cedente válido, o que cega o "
      "pilar 3 para eles (é o que o sinal DI-03 registra).\n")
    A("**4.4 O ranking de cedentes é um piso.** O informe exige apenas os nove "
      "maiores cedentes. HHI e concentração máxima são subestimados em fundos "
      "pulverizados e corretos em fundos monocedentes — viés conservador, mas "
      "viés.\n")
    A("**4.5 Percentis do corte aplicados à série inteira.** Os limiares são "
      "fixados na distribuição de " + CORTE + " e aplicados aos 13 meses de "
      "avaliação. Isso é deliberado — persistência medida contra bar móvel não "
      "significa nada —, mas implica que uma piora generalizada do mercado ao "
      "longo do ano não é capturada como piora relativa.\n")
    A("**4.6 Sinais correlacionados somam duas vezes.** QA-01, QA-03, QA-05 e "
      "ES-03 leem o mesmo fenômeno econômico por ângulos diferentes; um fundo "
      "deteriorado dispara os quatro. O score não desconta essa correlação, o "
      "que o torna convexo em deterioração de crédito. A leitura por pilar em "
      "`rf2_sinais.csv` é o antídoto.\n")
    A("**4.7 GV-04 é casamento por string.** A busca nominal por grupos sob "
      "medida do BCB/CVM produz homônimos (a palavra 'MASTER' aparece em razões "
      "sociais sem qualquer relação com o Banco Master) e não capta vínculo "
      "societário não refletido no nome. É pista de busca, jamais imputação.\n")
    A("**4.8 A materialidade financeira não é perda esperada.** É o montante "
      "**exposto** ao fenômeno que o sinal aponta (estoque inadimplente, valor da "
      "sênior sem colchão, PL do veículo). Não incorpora taxa de recuperação, "
      "coobrigação nem garantia. Somar materialidades entre sinais dupla-conta o "
      "mesmo real — por isso a coluna principal é o **máximo**, não a soma.\n")
    A("**4.9 Sem validação externa.** Nada aqui foi confrontado com processos "
      "sancionadores, atas de assembleia, regulamentos ou demonstrações "
      "financeiras auditadas. Cada ficha traz uma **ação de investigação** "
      "justamente porque o sinal é o começo da diligência, não o fim.\n")

    A("## 5. Arquivos gerados\n")
    A("| Arquivo | Conteúdo | Linhas |")
    A("|---|---|---:|")
    A(f"| `data/analytic/rf2_catalogo.csv` | Fichas dos sinais | {len(cat)} |")
    A(f"| `data/analytic/rf2_sinais.csv` | Veículo x sinal disparado no corte | "
      f"{len(sig):,} |".replace(",", "."))
    A(f"| `data/analytic/rf2_score_veiculo.csv` | Perfil multidimensional por "
      f"veículo | {len(sc):,} |".replace(",", "."))
    A("")

    with open(os.path.join(DOCS, "METODOLOGIA_RED_FLAGS.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------------------
# 5. Execução
# ---------------------------------------------------------------------------
def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    con = duckdb.connect(DB, read_only=True)
    print("carregando painel de 25 competências ...", flush=True)
    raw, reg = carregar(con)
    con.close()
    d = derivar(raw, reg)
    print(f"grade: {len(d):,} linhas; observadas: {int(d._obs.sum()):,}")

    print(f"avaliando {len(S)} sinais ...", flush=True)
    cat, av = avaliar(d)

    pers = persistencia(av)
    univ = set(d.loc[(d.DT_COMPTC == CORTE) & d._obs, "CNPJ"])
    corte = av[(av.DT_COMPTC == CORTE) & av.CNPJ.isin(univ)].merge(
        pers, on=["CNPJ", "sinal_id"], how="left")
    corte["meses_consecutivos"] = corte.meses_consecutivos.fillna(0).astype(int)

    idm = d[(d.DT_COMPTC == CORTE) & d._obs][["CNPJ", "DENOM_SOCIAL", "VL_PL", "ADMIN"]]
    meta = cat.set_index("sinal_id")

    # ---------------- saída 1: sinais disparados --------------------------
    sig = corte[corte.disparo].merge(idm, on="CNPJ", how="left")
    sig = sig.merge(meta[["pilar", "nome", "severidade", "peso", "limiar",
                          "limiar_sentido", "materialidade",
                          "persistencia_min_meses", "tipo_evidencia"]],
                    left_on="sinal_id", right_index=True, how="left")
    sig["persistencia_atendida"] = sig.meses_consecutivos >= sig.persistencia_min_meses
    sig = sig.rename(columns={"valor": "valor_observado", "mat_rs": "materialidade_rs",
                              "materialidade": "materialidade_regra"})
    sig = sig[["CNPJ", "DENOM_SOCIAL", "VL_PL", "ADMIN", "sinal_id", "pilar", "nome",
               "severidade", "peso", "valor_observado", "limiar", "limiar_sentido",
               "materialidade_regra", "materialidade_rs", "meses_consecutivos",
               "persistencia_min_meses", "persistencia_atendida", "meses_com_disparo",
               "ultimo_mes_disparo", "tipo_evidencia"]].sort_values(
        ["CNPJ", "sinal_id"])
    sig.to_csv(os.path.join(OUT, "rf2_sinais.csv"), index=False)

    # ---------------- saída 2: catálogo -----------------------------------
    cat_out = cat[["sinal_id", "pilar", "nome", "definicao", "formula",
                   "grupo_comparacao", "limiar", "limiar_sentido", "limiar_origem",
                   "severidade", "peso", "materialidade", "persistencia_min_meses",
                   "tipo_evidencia", "explicacoes_benignas", "acao_investigacao",
                   "n_grupo_comparacao", "n_avaliavel", "n_avaliavel_e_material",
                   "n_universo", "cobertura_universo_pct"]]
    disp_n = sig.groupby("sinal_id").CNPJ.nunique().rename("n_veiculos_disparo")
    disp_p = (sig[sig.persistencia_atendida].groupby("sinal_id").CNPJ.nunique()
              .rename("n_veiculos_disparo_persistente"))
    cat_out = (cat_out.merge(disp_n, left_on="sinal_id", right_index=True, how="left")
               .merge(disp_p, left_on="sinal_id", right_index=True, how="left"))
    cat_out[["n_veiculos_disparo", "n_veiculos_disparo_persistente"]] = cat_out[
        ["n_veiculos_disparo", "n_veiculos_disparo_persistente"]].fillna(0).astype(int)
    cat_out.to_csv(os.path.join(OUT, "rf2_catalogo.csv"), index=False)

    # ---------------- saída 3: perfil por veículo -------------------------
    n_sinais = len(S)
    base = corte.groupby("CNPJ").agg(
        n_avaliaveis=("avaliavel", "sum"),
        n_disparos=("disparo", "sum")).reset_index()
    base["cobertura_dados_pct"] = (base.n_avaliaveis / n_sinais * 100).round(2)

    # peso disponível: soma dos pesos dos sinais avaliáveis para o veículo
    cw = corte.merge(meta[["peso", "severidade", "tipo_evidencia"]],
                     left_on="sinal_id", right_index=True, how="left")
    cw = cw.merge(pers[["CNPJ", "sinal_id"]].drop_duplicates(),
                  on=["CNPJ", "sinal_id"], how="left")
    cw = cw.merge(meta[["persistencia_min_meses"]], left_on="sinal_id",
                  right_index=True, how="left")
    cw["conta"] = cw.disparo & (cw.meses_consecutivos >= cw.persistencia_min_meses)
    peso_disp = cw.groupby("CNPJ").apply(
        lambda g: pd.Series({
            "peso_disponivel": g.loc[g.avaliavel, "peso"].sum(),
            "peso_disparado": g.loc[g.conta, "peso"].sum(),
            "peso_disparado_bruto": g.loc[g.disparo, "peso"].sum(),
            "n_disparos_persistentes": int(g.conta.sum()),
            "n_criticos": int(((g.severidade == "crítica") & g.conta).sum()),
            "n_altos": int(((g.severidade == "alta") & g.conta).sum()),
            "obs_disparados": int(((g.tipo_evidencia == "observado") & g.disparo).sum()),
            "der_disparados": int(((g.tipo_evidencia == "derivado") & g.disparo).sum()),
            "materialidade_max_rs": g.loc[g.disparo, "mat_rs"].max(),
            "materialidade_soma_rs": g.loc[g.disparo, "mat_rs"].sum(),
            "persistencia_media_meses": (g.loc[g.disparo, "meses_consecutivos"].mean()
                                         if g.disparo.any() else np.nan),
            "atualidade": (g.loc[g.disparo, "ultimo_mes_disparo"].max()
                           if g.disparo.any() else None),
        }), include_groups=False).reset_index()

    sc = base.merge(peso_disp, on="CNPJ", how="left").merge(idm, on="CNPJ", how="left")
    sc["score_risco"] = np.where(
        sc.peso_disponivel > 0,
        (sc.peso_disparado / sc.peso_disponivel * 100).clip(0, 100), np.nan).round(2)
    sc["forca_evidencia"] = np.where(
        (sc.obs_disparados + sc.der_disparados) > 0,
        sc.obs_disparados / (sc.obs_disparados + sc.der_disparados), np.nan).round(3)
    # Faixas de atenção definidas por PERCENTIL do próprio score, entre os
    # veículos classificáveis com ao menos um disparo — mesma disciplina dos
    # limiares dos sinais: nada de corte redondo arbitrário.
    cls = (sc.cobertura_dados_pct >= 50)
    base_sc = sc.loc[cls & (sc.score_risco > 0), "score_risco"]
    q90, q99 = float(base_sc.quantile(0.90)), float(base_sc.quantile(0.99))
    sc["classificacao"] = np.where(
        ~cls, "não classificável",
        np.where(sc.score_risco >= q99, "atenção alta",
                 np.where(sc.score_risco >= q90, "atenção média",
                          np.where(sc.score_risco > 0, "atenção baixa",
                                   "sem sinal disparado"))))
    print(f"\ncortes de faixa (percentis do score entre classificáveis com "
          f"disparo, n={len(base_sc)}): p90={q90:.2f} p99={q99:.2f}")
    sc = sc[["CNPJ", "DENOM_SOCIAL", "VL_PL", "ADMIN", "classificacao", "score_risco",
             "materialidade_max_rs", "materialidade_soma_rs", "forca_evidencia",
             "obs_disparados", "der_disparados", "cobertura_dados_pct",
             "n_avaliaveis", "n_disparos", "n_disparos_persistentes",
             "n_criticos", "n_altos", "persistencia_media_meses", "atualidade",
             "peso_disponivel", "peso_disparado"]].sort_values(
        ["score_risco", "materialidade_max_rs"], ascending=False)
    sc.to_csv(os.path.join(OUT, "rf2_score_veiculo.csv"), index=False)

    gerar_doc(cat_out, sig, sc, (q90, q99))

    # ---------------- resumo ----------------------------------------------
    print("\n=== sinais por pilar ===")
    print(cat_out.groupby("pilar").agg(
        n_sinais=("sinal_id", "count"),
        veiculos_disparo=("n_veiculos_disparo", "sum"),
        cobertura_media=("cobertura_universo_pct", "mean")).round(1).to_string())
    print("\n=== classificação ===")
    print(sc.classificacao.value_counts().to_string())
    print(f"\nuniverso no corte: {sc.CNPJ.nunique()} veículos; "
          f"{int((sc.n_disparos > 0).sum())} com ao menos um disparo")
    print("\n=== top 10 score (score alto != irregularidade) ===")
    top = sc[sc.classificacao != "não classificável"].head(10).copy()
    top["PL_mi"] = (top.VL_PL / 1e6).round(1)
    print(top[["DENOM_SOCIAL", "PL_mi", "score_risco", "n_disparos_persistentes",
               "cobertura_dados_pct"]].assign(
        DENOM_SOCIAL=lambda x: x.DENOM_SOCIAL.str[:52]).to_string(index=False))
    print(f"\ngravados: rf2_catalogo.csv ({len(cat_out)} sinais), "
          f"rf2_sinais.csv ({len(sig):,} linhas), "
          f"rf2_score_veiculo.csv ({len(sc):,} veículos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
