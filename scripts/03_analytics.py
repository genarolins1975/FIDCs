#!/usr/bin/env python3
"""
Etapa 3 — Cálculo das tabelas analíticas e rankings.

Produz, em data/analytic/, os CSVs que sustentam o relatório executivo.
Unidade de análise e controles de dupla contagem:

  - "Painel canônico" (view painel): uma linha por veículo informante e mês.
    Regra de dedup: (i) se um CNPJ aparece 2x na mesma competência (Fundo e
    Classe), prevalece a linha Classe; (ii) linhas TP='Fundo' de fundos cujas
    classes com CNPJ próprio TAMBÉM informam na mesma competência são
    excluídas (sobreposição fundo x classe, medida e reportada).
  - O PL agregado NÃO exclui FIC-FIDC nem participações cruzadas; a série
    traz colunas separadas (pl_total, cotas_fidc_detidas, pl_liquido_circular)
    para leitura consolidada.

Reprodução: python3 scripts/03_analytics.py
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
M12, M36, M60 = "2025-06-30", "2023-06-30", "2021-06-30"

SEG_LABELS = {
    "TAB_II_A_VL_INDUST": "Industrial",
    "TAB_II_B_VL_IMOBIL": "Mercado Imobiliário",
    "TAB_II_C_VL_COMERC": "Comercial (total)",
    "TAB_II_C1_VL_COMERC": "Comercial",
    "TAB_II_C2_VL_VAREJO": "Comercial - Varejo",
    "TAB_II_C3_VL_ARREND": "Arrendamento Mercantil",
    "TAB_II_D_VL_SERV": "Serviços (total)",
    "TAB_II_D1_VL_SERV": "Serviços",
    "TAB_II_D2_VL_SERV_PUBLICO": "Serviços Públicos",
    "TAB_II_D3_VL_SERV_EDUC": "Serviços Educacionais",
    "TAB_II_D4_VL_ENTRET": "Entretenimento",
    "TAB_II_E_VL_AGRONEG": "Agronegócio",
    "TAB_II_F_VL_FINANC": "Financeiro (total)",
    "TAB_II_F1_VL_CRED_PESSOA": "Crédito Pessoal",
    "TAB_II_F2_VL_CRED_PESSOA_CONSIG": "Crédito Consignado",
    "TAB_II_F3_VL_CRED_CORP": "Crédito Corporativo",
    "TAB_II_F4_VL_MIDMARKET": "Middle Market",
    "TAB_II_F5_VL_VEICULO": "Veículos",
    "TAB_II_F6_VL_IMOBIL_EMPRESA": "Carteira Imobiliária Empresarial (financeiro)",
    "TAB_II_F7_VL_IMOBIL_RESID": "Carteira Imobiliária Residencial (financeiro)",
    "TAB_II_F8_VL_OUTRO": "Financeiro - Outros",
    "TAB_II_G_VL_CREDITO": "Cartão de Crédito",
    "TAB_II_H_VL_FACTOR": "Factoring (total)",
    "TAB_II_H1_VL_PESSOA": "Factoring Pessoal",
    "TAB_II_H2_VL_CORP": "Factoring Corporativo",
    "TAB_II_I_VL_SETOR_PUBLICO": "Setor Público (total)",
    "TAB_II_I1_VL_PRECAT": "Precatórios",
    "TAB_II_I2_VL_TRIBUT": "Créditos Tributários",
    "TAB_II_I3_VL_ROYALTIES": "Royalties",
    "TAB_II_I4_VL_OUTRO": "Setor Público - Outros",
    "TAB_II_J_VL_JUDICIAL": "Ações Judiciais",
    "TAB_II_K_VL_MARCA": "Propriedade Intelectual/Marcas e Patentes",
}


def main() -> int:
    con = duckdb.connect(DB)
    con.execute("PRAGMA threads=4")

    # ---------- Painel canônico com dedup fundo x classe ----------
    con.execute(r"""
    CREATE OR REPLACE VIEW mapa_classe_fundo AS
    SELECT DISTINCT regexp_replace(rc.CNPJ_Classe,'\D','','g') cnpj_classe,
           regexp_replace(rf.CNPJ_Fundo,'\D','','g') cnpj_fundo
    FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo)
    WHERE rc.CNPJ_Classe IS NOT NULL AND rf.CNPJ_Fundo IS NOT NULL
      AND regexp_replace(rc.CNPJ_Classe,'\D','','g')
          <> regexp_replace(rf.CNPJ_Fundo,'\D','','g');
    """)
    con.execute("""
    CREATE OR REPLACE VIEW painel AS
    WITH dedup_cnpj AS (            -- regra (i): Fundo+Classe no mesmo CNPJ/mês
      SELECT *, ROW_NUMBER() OVER (
        PARTITION BY CNPJ, DT_COMPTC
        ORDER BY CASE TP_FUNDO_CLASSE WHEN 'Classe' THEN 0 ELSE 1 END) rn
      FROM pl),
    fundos_com_classe_informante AS ( -- regra (ii)
      SELECT DISTINCT m.cnpj_fundo, p.DT_COMPTC
      FROM pl p JOIN mapa_classe_fundo m ON p.CNPJ = m.cnpj_classe)
    SELECT d.TP_FUNDO_CLASSE, d.CNPJ, d.DENOM_SOCIAL, d.DT_COMPTC, d.VL_PL
    FROM dedup_cnpj d
    LEFT JOIN fundos_com_classe_informante f
      ON d.TP_FUNDO_CLASSE='Fundo' AND d.CNPJ=f.cnpj_fundo AND d.DT_COMPTC=f.DT_COMPTC
    WHERE d.rn=1 AND f.cnpj_fundo IS NULL;
    """)

    # Saneamento de PL: observações pontuais > 20x a vizinhança e > R$ 1 bi
    # são erros de preenchimento notórios (ex.: INX SSPI BONDS, mai/2016:
    # R$ 101,6 bi num fundo de R$ 25 mi). Excluídas da série e logadas.
    con.execute("""
    CREATE OR REPLACE VIEW pl_outliers AS
    WITH x AS (
      SELECT CNPJ, DENOM_SOCIAL, DT_COMPTC, VL_PL,
             LAG(VL_PL)  OVER w pl_prev, LEAD(VL_PL) OVER w pl_next
      FROM painel WINDOW w AS (PARTITION BY CNPJ ORDER BY DT_COMPTC))
    SELECT CNPJ, DENOM_SOCIAL, DT_COMPTC, VL_PL, pl_prev, pl_next FROM x
    WHERE VL_PL > 1e9 AND pl_prev IS NOT NULL AND pl_next IS NOT NULL
      AND VL_PL > 20*GREATEST(pl_prev, pl_next)""")
    con.execute("""
    CREATE OR REPLACE VIEW painel_saneado AS
    SELECT p.* FROM painel p
    LEFT JOIN pl_outliers o ON o.CNPJ=p.CNPJ AND o.DT_COMPTC=p.DT_COMPTC
    WHERE o.CNPJ IS NULL""")
    con.execute("SELECT * FROM pl_outliers ORDER BY DT_COMPTC").df().to_csv(
        f"{OUT}/pl_saneamento_excluidos.csv", index=False)

    # ---------- Série mensal do mercado ----------
    serie = con.execute(f"""
    WITH a AS (
      SELECT CNPJ, DT_COMPTC, TAB_I2H_VL_COTA_FIDC, TAB_I2I_VL_COTA_FIDC_NP,
             TAB_I2A_VL_DIRCRED_RISCO, TAB_I2B_VL_DIRCRED_SEM_RISCO,
             TAB_I2A21_VL_TOTAL_PARCELA_INAD, TAB_I2B21_VL_TOTAL_PARCELA_INAD,
             FUNDO_EXCLUSIVO, COTST_INTERESSE
      FROM ativo),
    c AS (SELECT CNPJ, DT_COMPTC, SUM(TAB_X_NR_COTST) n_cotistas
          FROM cotistas_serie GROUP BY 1,2)
    SELECT p.DT_COMPTC,
      COUNT(*) n_veiculos,
      COUNT(*) FILTER (p.TP_FUNDO_CLASSE='Classe') n_classes,
      COUNT(*) FILTER (p.TP_FUNDO_CLASSE='Fundo')  n_fundos_legado,
      SUM(p.VL_PL) pl_total,
      SUM(a.TAB_I2A_VL_DIRCRED_RISCO) dc_com_risco,
      SUM(a.TAB_I2B_VL_DIRCRED_SEM_RISCO) dc_sem_risco,
      -- I2I (cotas de FIDC-NP) está 100% em branco no layout desde 2024: a
      -- circularidade medida vem de I2H. Somar nulo como zero seria afirmar
      -- ausência; aqui a soma ignora nulos e a contagem de informantes é
      -- publicada ao lado para tornar a lacuna visível.
      SUM(a.TAB_I2H_VL_COTA_FIDC) cotas_fidc_detidas,
      COUNT(a.TAB_I2H_VL_COTA_FIDC) n_informou_cotas_fidc,
      COUNT(a.TAB_I2I_VL_COTA_FIDC_NP) n_informou_cotas_fidc_np,
      SUM(p.VL_PL) - SUM(a.TAB_I2H_VL_COTA_FIDC) pl_liquido_circular,
      SUM(p.VL_PL) FILTER (a.FUNDO_EXCLUSIVO='S') pl_exclusivos,
      SUM(p.VL_PL) FILTER (a.COTST_INTERESSE='S') pl_cotistas_interesse_unico,
      SUM(a.TAB_I2A21_VL_TOTAL_PARCELA_INAD) parcelas_inad_com_risco,
      SUM(a.TAB_I2B21_VL_TOTAL_PARCELA_INAD) parcelas_inad_sem_risco,
      SUM(c.n_cotistas) n_cotistas
    FROM painel_saneado p
    LEFT JOIN a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN c ON c.CNPJ=p.CNPJ AND c.DT_COMPTC=p.DT_COMPTC
    GROUP BY 1 ORDER BY 1""").df()
    ipca = con.execute("SELECT data, indice FROM ipca").df()
    ipca["m"] = ipca["data"].dt.strftime("%Y-%m")
    serie["m"] = serie["DT_COMPTC"].str[:7]
    serie = serie.merge(ipca[["m", "indice"]], on="m", how="left")
    base_idx = serie.loc[serie["DT_COMPTC"] == CORTE, "indice"].iloc[0]
    serie["pl_total_real_jun26"] = serie["pl_total"] * base_idx / serie["indice"]
    serie.drop(columns=["m"]).to_csv(f"{OUT}/serie_mercado_mensal.csv", index=False)

    # ---------- Ranking de administradores (informe, com histórico) ----------
    con.execute(f"""
    CREATE OR REPLACE VIEW adm_pl AS
    SELECT a.DT_COMPTC, regexp_replace(a.CNPJ_ADMIN,'\\D','','g') cnpj_admin,
           MAX(a.ADMIN) AS nome_admin, SUM(p.VL_PL) pl, COUNT(*) n_veiculos
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE a.CNPJ_ADMIN IS NOT NULL
    GROUP BY 1,2""")
    adm = con.execute(f"""
    WITH now AS (SELECT * FROM adm_pl WHERE DT_COMPTC='{CORTE}'),
    h12 AS (SELECT cnpj_admin, pl FROM adm_pl WHERE DT_COMPTC='{M12}'),
    h36 AS (SELECT cnpj_admin, pl FROM adm_pl WHERE DT_COMPTC='{M36}'),
    h60 AS (SELECT cnpj_admin, pl FROM adm_pl WHERE DT_COMPTC='{M60}')
    SELECT now.nome_admin, now.cnpj_admin, now.pl, now.n_veiculos,
           now.pl/SUM(now.pl) OVER () participacao,
           now.pl/h12.pl - 1 var_12m, now.pl/h36.pl - 1 var_36m, now.pl/h60.pl - 1 var_60m
    FROM now LEFT JOIN h12 USING(cnpj_admin) LEFT JOIN h36 USING(cnpj_admin)
    LEFT JOIN h60 USING(cnpj_admin)
    ORDER BY now.pl DESC""").df()
    adm.to_csv(f"{OUT}/ranking_administradores.csv", index=False)

    # ---------- Ranking de gestores (registro CVM, corte) ----------
    gest = con.execute(f"""
    WITH mapa AS (
      -- prioridade classe->fundo; linhas fundo->fundo só para CNPJs que não
      -- são classe de outro fundo (evita dupla atribuição de PL a 2 gestores)
      SELECT cnpj_classe cnpj, cnpj_fundo FROM mapa_classe_fundo
      UNION ALL
      SELECT DISTINCT regexp_replace(CNPJ_Fundo,'\\D','','g'),
             regexp_replace(CNPJ_Fundo,'\\D','','g') FROM registro_fundo rf
      WHERE regexp_replace(rf.CNPJ_Fundo,'\\D','','g') NOT IN
            (SELECT cnpj_classe FROM mapa_classe_fundo)),
    gestor_fundo AS (
      -- fundos com mais de um registro (ex.: gestor substituído): prevalece o
      -- registro ativo mais recente, evitando dupla atribuição do PL
      SELECT cnpj_fundo, doc_gestor, gestor FROM (
        SELECT regexp_replace(CNPJ_Fundo,'\\D','','g') cnpj_fundo,
               regexp_replace(CPF_CNPJ_Gestor,'\\D','','g') doc_gestor,
               Gestor gestor,
               ROW_NUMBER() OVER (
                 PARTITION BY regexp_replace(CNPJ_Fundo,'\\D','','g')
                 ORDER BY CASE Situacao WHEN 'Em Funcionamento Normal' THEN 0
                          WHEN 'Em Liquidação' THEN 1 ELSE 2 END,
                          Data_Registro DESC, ID_Registro_Fundo DESC) rn
        FROM registro_fundo WHERE Tipo_Fundo LIKE '%FIDC%') WHERE rn=1)
    SELECT g.gestor, g.doc_gestor, SUM(p.VL_PL) pl, COUNT(*) n_veiculos,
           SUM(p.VL_PL)/ (SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{CORTE}') participacao_do_mercado
    FROM painel_saneado p
    JOIN mapa m ON m.cnpj = p.CNPJ
    JOIN gestor_fundo g ON g.cnpj_fundo = m.cnpj_fundo
    WHERE p.DT_COMPTC='{CORTE}'
    GROUP BY 1,2 ORDER BY pl DESC""").df()
    gest.to_csv(f"{OUT}/ranking_gestores.csv", index=False)
    cobertura_gestor = gest["pl"].sum()
    pl_corte = con.execute(f"SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{CORTE}'").fetchone()[0]

    # ---------- Custodiante / Controlador / Auditor (registro de classes, corte) ----------
    for papel, cnpj_col, nome_col in (
        ("custodiantes", "CNPJ_Custodiante", "Custodiante"),
        ("controladores", "CNPJ_Controlador", "Controlador"),
        ("auditores", "CNPJ_Auditor", "Auditor"),
    ):
        df = con.execute(f"""
        WITH classes AS (
          SELECT regexp_replace(rc.CNPJ_Classe,'\\D','','g') cnpj,
                 regexp_replace(rc.{cnpj_col},'\\D','','g') doc, MAX(rc.{nome_col}) nome
          FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo)
          WHERE rf.Tipo_Fundo LIKE '%FIDC%' AND rc.{cnpj_col} IS NOT NULL
          GROUP BY 1,2)
        SELECT c.nome, c.doc cnpj, SUM(p.VL_PL) pl, COUNT(*) n_classes,
               SUM(p.VL_PL)/SUM(SUM(p.VL_PL)) OVER () participacao_do_identificado
        FROM painel_saneado p JOIN classes c ON c.cnpj=p.CNPJ
        WHERE p.DT_COMPTC='{CORTE}'
        GROUP BY 1,2 ORDER BY pl DESC""").df()
        df.to_csv(f"{OUT}/ranking_{papel}.csv", index=False)

    # ---------- Maiores veículos (top 30) ----------
    top = con.execute(f"""
    SELECT p.DENOM_SOCIAL, p.CNPJ, p.TP_FUNDO_CLASSE, p.VL_PL,
           a.ADMIN, a.FUNDO_EXCLUSIVO, a.COTST_INTERESSE,
           p.VL_PL/SUM(p.VL_PL) OVER () participacao
    FROM painel_saneado p LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' ORDER BY p.VL_PL DESC LIMIT 30""").df()
    top.to_csv(f"{OUT}/maiores_veiculos.csv", index=False)

    # ---------- Concentração ----------
    conc = {}
    v = con.execute(f"SELECT VL_PL FROM painel_saneado WHERE DT_COMPTC='{CORTE}' AND VL_PL>0").df()["VL_PL"]
    sh = v / v.sum()
    conc["hhi_veiculos"] = float((sh ** 2).sum())
    conc["share_top10_veiculos"] = float(sh.nlargest(10).sum())
    conc["share_top50_veiculos"] = float(sh.nlargest(50).sum())
    # PL negativo é observação válida (veículo com passivo a descoberto), mas
    # não pode entrar num índice de participação. Excluímos e reportamos.
    adm_pos = adm[adm["pl"] > 0]
    conc["n_administradores_pl_negativo_excluidos"] = int((adm["pl"] <= 0).sum())
    sh_a = adm_pos["pl"] / adm_pos["pl"].sum()
    conc["hhi_administradores"] = float((sh_a ** 2).sum())
    conc["share_top5_administradores"] = float(sh_a.nlargest(5).sum())
    gest_pos = gest[gest["pl"] > 0]
    conc["n_gestores_pl_negativo_excluidos"] = int((gest["pl"] <= 0).sum())
    sh_g = gest_pos["pl"] / gest_pos["pl"].sum()
    conc["hhi_gestores"] = float((sh_g ** 2).sum())
    conc["share_top5_gestores"] = float(sh_g.nlargest(5).sum())
    conc["cobertura_ranking_gestores"] = float(cobertura_gestor / pl_corte)
    pd.Series(conc).to_csv(f"{OUT}/concentracao_indicadores.csv")

    # ---------- Carteira por segmento (tab II), corte e série anual ----------
    cols = [c for c in con.execute("SELECT * FROM carteira_segmento LIMIT 0").df().columns
            if c.startswith("TAB_II")]
    totais = {"TAB_II_C_VL_COMERC", "TAB_II_D_VL_SERV", "TAB_II_F_VL_FINANC",
              "TAB_II_H_VL_FACTOR", "TAB_II_I_VL_SETOR_PUBLICO"}
    subs = [c for c in cols if c in SEG_LABELS and c not in totais]
    seg = con.execute(f"""
    SELECT s.DT_COMPTC, {', '.join(f'SUM(s.{c}) {c}' for c in subs)}
    FROM carteira_segmento s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC
    WHERE s.DT_COMPTC LIKE '%-12-31' OR s.DT_COMPTC='{CORTE}'
    GROUP BY 1 ORDER BY 1""").df()
    seg_long = seg.melt(id_vars="DT_COMPTC", var_name="campo", value_name="valor")
    seg_long["segmento"] = seg_long["campo"].map(SEG_LABELS)
    seg_long.to_csv(f"{OUT}/carteira_segmentos.csv", index=False)

    # ---------- Inadimplência / aging (tabs V e VI) ----------
    aging = con.execute(f"""
    WITH v AS (
      SELECT DT_COMPTC, SUM(TAB_V_A_VL_DIRCRED_PRAZO) dc,
        SUM(TAB_V_B_VL_DIRCRED_INAD) inad_total,
        SUM(TAB_V_B1_VL_INAD_30) i30,
        SUM(TAB_V_B2_VL_INAD_60+TAB_V_B3_VL_INAD_90) i31_90,
        SUM(TAB_V_B4_VL_INAD_120+TAB_V_B5_VL_INAD_150+TAB_V_B6_VL_INAD_180) i91_180,
        SUM(TAB_V_B7_VL_INAD_360+TAB_V_B8_VL_INAD_720+TAB_V_B9_VL_INAD_1080+TAB_V_B10_VL_INAD_MAIOR_1080) i_maior_180
      FROM dc_risco_prazos s WHERE EXISTS (SELECT 1 FROM painel_saneado p WHERE p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC)
      GROUP BY 1),
    vi AS (
      SELECT DT_COMPTC, SUM(TAB_VI_A_VL_DIRCRED_PRAZO) dc,
        SUM(TAB_VI_B_VL_DIRCRED_INAD) inad_total,
        SUM(TAB_VI_B1_VL_INAD_30) i30,
        SUM(TAB_VI_B2_VL_INAD_60+TAB_VI_B3_VL_INAD_90) i31_90,
        SUM(TAB_VI_B4_VL_INAD_120+TAB_VI_B5_VL_INAD_150+TAB_VI_B6_VL_INAD_180) i91_180,
        SUM(TAB_VI_B7_VL_INAD_360+TAB_VI_B8_VL_INAD_720+TAB_VI_B9_VL_INAD_1080+TAB_VI_B10_VL_INAD_MAIOR_1080) i_maior_180
      FROM dc_semrisco_prazos s WHERE EXISTS (SELECT 1 FROM painel_saneado p WHERE p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC)
      GROUP BY 1)
    SELECT v.DT_COMPTC,
      v.dc dc_com_risco, v.inad_total inad_com_risco,
      v.i30 v_i30, v.i31_90 v_i31_90, v.i91_180 v_i91_180, v.i_maior_180 v_maior_180,
      vi.dc dc_sem_risco, vi.inad_total inad_sem_risco,
      vi.i30 vi_i30, vi.i31_90 vi_i31_90, vi.i91_180 vi_i91_180, vi.i_maior_180 vi_maior_180
    FROM v LEFT JOIN vi USING (DT_COMPTC) ORDER BY 1""").df()
    aging.to_csv(f"{OUT}/inadimplencia_aging_serie.csv", index=False)

    # ---------- Subordinação (tab X_2), corte ----------
    sub = con.execute(f"""
    WITH s AS (
      SELECT s.CNPJ, s.TIPO_COTA, SUM(s.VL_SERIE) v
      FROM series_cotas s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC
      WHERE s.DT_COMPTC='{CORTE}' GROUP BY 1,2)
    SELECT TIPO_COTA, SUM(v) valor, COUNT(DISTINCT CNPJ) n_veiculos
    FROM s GROUP BY 1 ORDER BY 2 DESC""").df()
    sub.to_csv(f"{OUT}/subordinacao_agregada.csv", index=False)
    subv = con.execute(f"""
    WITH s AS (
      SELECT s.CNPJ, SUM(s.VL_SERIE) FILTER (s.TIPO_COTA IN ('subordinada','mezanino')) v_sub,
             SUM(s.VL_SERIE) v_tot
      FROM series_cotas s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC
      WHERE s.DT_COMPTC='{CORTE}' GROUP BY 1)
    SELECT p.DENOM_SOCIAL, s.CNPJ, p.VL_PL, s.v_sub, s.v_tot,
           s.v_sub/NULLIF(s.v_tot,0) indice_subordinacao
    FROM s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC='{CORTE}'
    WHERE s.v_tot>0 ORDER BY p.VL_PL DESC""").df()
    subv.to_csv(f"{OUT}/subordinacao_por_veiculo.csv", index=False)

    # ---------- Cotistas por categoria (X_1_1), corte ----------
    cot_cols = [c for c in con.execute("SELECT * FROM cotistas_tipo LIMIT 0").df().columns
                if c.startswith("TAB_X_NR_COTST_")]
    cot = con.execute(f"""
    SELECT {', '.join(f'SUM(c.{c}) {c}' for c in cot_cols)}
    FROM cotistas_tipo c JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
    WHERE c.DT_COMPTC='{CORTE}'""").df().T
    cot.columns = ["n_cotistas"]
    cot["classe"] = ["senior" if "_SENIOR_" in i else "subordinada" for i in cot.index]
    cot["categoria"] = [re.sub(r"TAB_X_NR_COTST_(SENIOR|SUBORD)_", "", i) for i in cot.index]
    cot.to_csv(f"{OUT}/cotistas_por_categoria.csv")

    # ---------- SCR (X.8) e liquidez (X.5), corte ----------
    scr_cols = [c for c in con.execute("SELECT * FROM scr LIMIT 0").df().columns
                if "SCR_RISCO_OPER" in c]
    scr = con.execute(f"""
    SELECT {', '.join(f'SUM(s.{c}) {c}' for c in scr_cols)}
    FROM scr s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC
    WHERE s.DT_COMPTC='{CORTE}'""").df().T
    scr.columns = ["valor"]
    scr["rating"] = [i.rsplit("_", 1)[-1] for i in scr.index]
    scr.to_csv(f"{OUT}/scr_rating_operacoes.csv")

    liq = con.execute(f"""
    SELECT SUM(TAB_X_VL_LIQUIDEZ_0) d0, SUM(TAB_X_VL_LIQUIDEZ_30) d30,
           SUM(TAB_X_VL_LIQUIDEZ_60) d60, SUM(TAB_X_VL_LIQUIDEZ_90) d90,
           SUM(TAB_X_VL_LIQUIDEZ_180) d180, SUM(TAB_X_VL_LIQUIDEZ_360) d360,
           SUM(TAB_X_VL_LIQUIDEZ_MAIOR_360) d_maior_360
    FROM liquidez l JOIN painel_saneado p ON p.CNPJ=l.CNPJ AND p.DT_COMPTC=l.DT_COMPTC
    WHERE l.DT_COMPTC='{CORTE}'""").df()
    liq.to_csv(f"{OUT}/liquidez_corte.csv", index=False)

    # ---------- Negócios 12m (tab VII): recompras, substituições, alienações ----------
    neg = con.execute(f"""
    SELECT substr(n.DT_COMPTC,1,4) ano,
      SUM(TAB_VII_A1_2_VL_DIRCRED_RISCO) aquis_com_risco,
      SUM(TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO) aquis_sem_risco,
      SUM(TAB_VII_B1_2_VL_CEDENTE) alienacoes_para_cedente,
      SUM(TAB_VII_B2_2_VL_PREST) alienacoes_para_prestadores,
      SUM(TAB_VII_B3_2_VL_TERCEIRO) alienacoes_para_terceiros,
      SUM(TAB_VII_C_2_VL_SUBST) substituicoes,
      SUM(TAB_VII_D_2_VL_RECOMPRA) recompras
    FROM negocios n JOIN painel_saneado p ON p.CNPJ=n.CNPJ AND p.DT_COMPTC=n.DT_COMPTC
    GROUP BY 1 ORDER BY 1""").df()
    neg.to_csv(f"{OUT}/negocios_anual.csv", index=False)

    # ---------- Cedentes: ranking por exposição estimada no corte ----------
    ced = con.execute(f"""
    WITH base AS (
      SELECT c.CNPJ cnpj_veiculo, c.DOC_CEDENTE, c.PR_CEDENTE, c.BUCKET,
             CASE c.BUCKET WHEN 'com_risco' THEN a.TAB_I2A_VL_DIRCRED_RISCO
                           ELSE a.TAB_I2B_VL_DIRCRED_SEM_RISCO END vl_bucket
      FROM cedentes c
      JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
      JOIN ativo a ON a.CNPJ=c.CNPJ AND a.DT_COMPTC=c.DT_COMPTC
      WHERE c.DT_COMPTC='{CORTE}' AND length(regexp_replace(c.DOC_CEDENTE,'\\D','','g'))>=11
        AND c.PR_CEDENTE > 0 AND c.PR_CEDENTE <= 100)  -- PR=0 não conta; >100 é erro de preenchimento
    SELECT CASE WHEN length(regexp_replace(DOC_CEDENTE,'\\D','','g'))>=12
                THEN lpad(regexp_replace(DOC_CEDENTE,'\\D','','g'),14,'0')
                ELSE lpad(regexp_replace(DOC_CEDENTE,'\\D','','g'),11,'0') END doc_cedente,
           COUNT(DISTINCT cnpj_veiculo) n_veiculos,
           SUM(PR_CEDENTE/100.0 * vl_bucket) exposicao_estimada,
           SUM(PR_CEDENTE/100.0 * vl_bucket) FILTER (BUCKET='com_risco') exp_com_risco,
           SUM(PR_CEDENTE/100.0 * vl_bucket) FILTER (BUCKET='sem_risco') exp_sem_risco
    FROM base GROUP BY 1 ORDER BY exposicao_estimada DESC NULLS LAST""").df()
    ced.to_csv(f"{OUT}/cedentes_ranking_estimado.csv", index=False)

    # Cobertura do ranking de cedentes: quanto do DC do corte tem cedente
    # identificado no top-9 (ressalva R1 do agente espelho)
    cob = con.execute(f"""
    WITH pr AS (
      SELECT c.CNPJ, c.BUCKET, SUM(c.PR_CEDENTE)/100.0 pr_tot
      FROM cedentes c JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
      WHERE c.DT_COMPTC='{CORTE}' AND c.PR_CEDENTE > 0 AND c.PR_CEDENTE <= 100
      GROUP BY 1,2),
    base AS (
      SELECT a.CNPJ, a.TAB_I2A_VL_DIRCRED_RISCO dc_a, a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc_b
      FROM ativo a JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
      WHERE a.DT_COMPTC='{CORTE}')
    SELECT
      SUM(coalesce(pa.pr_tot,0)*coalesce(b.dc_a,0) + coalesce(pb.pr_tot,0)*coalesce(b.dc_b,0)) dc_coberto,
      SUM(coalesce(b.dc_a,0)+coalesce(b.dc_b,0)) dc_total
    FROM base b
    LEFT JOIN pr pa ON pa.CNPJ=b.CNPJ AND pa.BUCKET='com_risco'
    LEFT JOIN pr pb ON pb.CNPJ=b.CNPJ AND pb.BUCKET='sem_risco'""").df()
    cob["cobertura_top9"] = cob.dc_coberto / cob.dc_total
    cob.to_csv(f"{OUT}/cedentes_cobertura.csv", index=False)

    # Recorrência de cedentes (nº de meses em que aparecem, desde 2013)
    ced_rec = con.execute("""
    SELECT CASE WHEN length(regexp_replace(DOC_CEDENTE,'\\D','','g'))>=12
                THEN lpad(regexp_replace(DOC_CEDENTE,'\\D','','g'),14,'0')
                ELSE lpad(regexp_replace(DOC_CEDENTE,'\\D','','g'),11,'0') END doc_cedente,
           COUNT(DISTINCT DT_COMPTC) n_meses,
           COUNT(DISTINCT CNPJ) n_veiculos_distintos,
           MIN(DT_COMPTC) primeira, MAX(DT_COMPTC) ultima
    FROM cedentes WHERE length(regexp_replace(DOC_CEDENTE,'\\D','','g'))>=11
    GROUP BY 1 HAVING COUNT(DISTINCT DT_COMPTC)>=12
    ORDER BY n_veiculos_distintos DESC LIMIT 500""").df()
    ced_rec.to_csv(f"{OUT}/cedentes_recorrencia.csv", index=False)

    # ---------- Alertas ----------
    alertas = con.execute(f"""
    SELECT 'PL negativo' alerta, DENOM_SOCIAL, CNPJ, DT_COMPTC, VL_PL valor
    FROM painel_saneado WHERE DT_COMPTC='{CORTE}' AND VL_PL < 0
    UNION ALL
    SELECT 'Ativo > 5x PL (possível erro de preenchimento)', p.DENOM_SOCIAL, p.CNPJ, p.DT_COMPTC, a.TAB_I_VL_ATIVO
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' AND a.TAB_I_VL_ATIVO > 5*p.VL_PL AND p.VL_PL > 1e6
    UNION ALL
    SELECT 'Parcelas inadimplentes > 30% dos DC (com risco)', p.DENOM_SOCIAL, p.CNPJ, p.DT_COMPTC,
           a.TAB_I2A21_VL_TOTAL_PARCELA_INAD/NULLIF(a.TAB_I2A_VL_DIRCRED_RISCO,0)
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' AND a.TAB_I2A_VL_DIRCRED_RISCO > 5e7
      AND a.TAB_I2A21_VL_TOTAL_PARCELA_INAD/NULLIF(a.TAB_I2A_VL_DIRCRED_RISCO,0) > 0.30
    ORDER BY 1, valor DESC""").df()
    alertas.to_csv(f"{OUT}/alertas.csv", index=False)

    # Saltos de PL > 30% m/m (veículos > R$ 100 mi) nos últimos 12 meses
    saltos = con.execute("""
    WITH x AS (
      SELECT CNPJ, DENOM_SOCIAL, DT_COMPTC, VL_PL,
             LAG(VL_PL) OVER (PARTITION BY CNPJ ORDER BY DT_COMPTC) pl_ant
      FROM painel)
    SELECT DENOM_SOCIAL, CNPJ, DT_COMPTC, pl_ant, VL_PL, VL_PL/pl_ant-1 var
    FROM x WHERE DT_COMPTC>='2025-07-01' AND pl_ant>1e8 AND abs(VL_PL/pl_ant-1)>0.30
    ORDER BY abs(VL_PL/pl_ant-1) DESC""").df()
    saltos.to_csv(f"{OUT}/saltos_pl_12m.csv", index=False)

    # ---------- Captação líquida (tab X_4: captações - resgates - amortizações) ----------
    cap_frames = []
    for f in sorted(glob.glob(os.path.join(EXTRACT, "inf_mensal_fidc_tab_X_4_*.csv"))):
        df = pd.read_csv(f, sep=";", encoding="latin1", dtype=str, quoting=3)
        if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
            df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
        df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
        df["TAB_X_VL_TOTAL"] = pd.to_numeric(df["TAB_X_VL_TOTAL"], errors="coerce")
        cap_frames.append(df[["CNPJ", "DT_COMPTC", "TAB_X_TP_OPER", "TAB_X_VL_TOTAL"]])
    capt = pd.concat(cap_frames, ignore_index=True)
    con.execute("CREATE OR REPLACE TABLE captacoes AS SELECT * FROM capt")
    # Filtro de sanidade: operações > 3x max(PL_t, PL_{t-1}) + R$100 mi são
    # erros notórios de preenchimento (há registros de R$ 725 tri em veículos
    # de R$ 290 mi de PL); descartadas e contadas.
    cap = con.execute("""
    WITH p2 AS (SELECT CNPJ, DT_COMPTC, VL_PL,
                LAG(VL_PL) OVER (PARTITION BY CNPJ ORDER BY DT_COMPTC) pl_ant
                FROM painel),
    base AS (
      SELECT c.*, (c.TAB_X_VL_TOTAL > 3*GREATEST(coalesce(p2.VL_PL,0),coalesce(p2.pl_ant,0))+1e8) descartada
      FROM captacoes c JOIN p2 ON p2.CNPJ=c.CNPJ AND p2.DT_COMPTC=c.DT_COMPTC)
    SELECT substr(DT_COMPTC,1,4) ano,
      SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Captações no Mês' AND NOT descartada) captacoes,
      SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Resgates no Mês' AND NOT descartada) resgates,
      SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Amortizações' AND NOT descartada) amortizacoes,
      SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Captações no Mês' AND NOT descartada)
        - SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Resgates no Mês' AND NOT descartada)
        - SUM(TAB_X_VL_TOTAL) FILTER (TAB_X_TP_OPER='Amortizações' AND NOT descartada) captacao_liquida,
      COUNT(*) FILTER (descartada) n_ops_descartadas,
      SUM(TAB_X_VL_TOTAL) FILTER (descartada) valor_descartado
    FROM base GROUP BY 1 ORDER BY 1""").df()
    cap.to_csv(f"{OUT}/captacao_liquida_anual.csv", index=False)

    print("séries e rankings gerados em", OUT)
    print("PL no corte:", round(pl_corte / 1e9, 1), "bi; cobertura ranking gestores:",
          round(cobertura_gestor / pl_corte, 4))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
