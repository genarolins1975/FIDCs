#!/usr/bin/env python3
"""
Etapa 10 — Triagem regulatória: red flags derivadas dos casos documentados.

Tipologia extraída dos casos públicos de uso indevido de FIDCs (Cruzeiro do
Sul 2012, Silverado 2013-24, Trendbank, Union National, Reag/Carbono Oculto
2025, Master 2025 — ver auditoria/casos_uso_indevido_fidc.md):

  RF1  lastro "bom demais": inadimplência ~zero com carteira grande e cedente
       concentrado (fraudes de lastro exibem adimplência perfeita até o colapso)
  RF2  rolagem: recompras+substituições elevadas vs carteira (esconde atraso)
  RF3  estrutura fechada: 1-2 cotistas + interesse único + subordinação <5%
       (veículo espelho do originador, sem verificação de mercado)
  RF4  colapso: queda de PL >50% m/m em veículo relevante (12m)
  RF5  crescimento >150% em 12m com cedente único (carrossel/pirâmide)
  RF6  exposição a prestadores atingidos por liquidação BCB (Reag, Master):
       busca nominal em administradores/gestores/veículos da base

IMPORTANTE: red flag é sinal estatístico de atenção supervisória, NÃO
imputação de irregularidade. Falsos positivos são esperados (ex.: RF3 captura
FIDCs cativos legítimos de tesouraria).

Reprodução: python3 scripts/10_red_flags.py
"""
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    flags = []

    # RF1 — inadimplência ~0 com DC > R$ 200 mi e top cedente >= 50% do bucket
    rf1 = con.execute(f"""
    WITH inad AS (
      SELECT v.CNPJ,
        coalesce(v.TAB_V_A_VL_DIRCRED_PRAZO,0)+coalesce(vi.TAB_VI_A_VL_DIRCRED_PRAZO,0) dc,
        coalesce(v.TAB_V_B_VL_DIRCRED_INAD,0)+coalesce(vi.TAB_VI_B_VL_DIRCRED_INAD,0) inad
      FROM dc_risco_prazos v FULL JOIN dc_semrisco_prazos vi
        ON vi.CNPJ=v.CNPJ AND vi.DT_COMPTC=v.DT_COMPTC
      WHERE v.DT_COMPTC='{CORTE}'),
    topced AS (
      SELECT CNPJ, MAX(PR_CEDENTE) pr_max FROM cedentes
      WHERE DT_COMPTC='{CORTE}' AND PR_CEDENTE BETWEEN 0 AND 100 GROUP BY 1)
    SELECT p.DENOM_SOCIAL, p.CNPJ, p.VL_PL, i.dc, i.inad/nullif(i.dc,0) inad_pct, t.pr_max
    FROM painel_saneado p
    JOIN inad i ON i.CNPJ=p.CNPJ
    JOIN topced t ON t.CNPJ=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' AND i.dc > 2e8
      AND i.inad/nullif(i.dc,0) < 0.001 AND t.pr_max >= 50
    ORDER BY i.dc DESC""").df()
    rf1["red_flag"] = "RF1 inadimplência ~zero + cedente concentrado"
    flags.append(rf1)

    # RF2 — recompras+substituições 12m > 15% da carteira média
    rf2 = con.execute(f"""
    WITH neg AS (
      SELECT n.CNPJ,
        SUM(coalesce(TAB_VII_D_2_VL_RECOMPRA,0)+coalesce(TAB_VII_C_2_VL_SUBST,0)) roll_12m
      FROM negocios n WHERE n.DT_COMPTC BETWEEN '2025-07-01' AND '2026-06-30'
      GROUP BY 1),
    dcm AS (
      SELECT CNPJ, AVG(coalesce(TAB_I2A_VL_DIRCRED_RISCO,0)+coalesce(TAB_I2B_VL_DIRCRED_SEM_RISCO,0)) dc_medio
      FROM ativo WHERE DT_COMPTC BETWEEN '2025-07-01' AND '2026-06-30' GROUP BY 1)
    SELECT p.DENOM_SOCIAL, p.CNPJ, p.VL_PL, n.roll_12m, d.dc_medio,
           n.roll_12m/nullif(d.dc_medio,0) razao_rolagem
    FROM painel_saneado p JOIN neg n ON n.CNPJ=p.CNPJ JOIN dcm d ON d.CNPJ=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' AND d.dc_medio > 1e8
      AND n.roll_12m/nullif(d.dc_medio,0) > 0.15
    ORDER BY razao_rolagem DESC""").df()
    rf2["red_flag"] = "RF2 recompras/substituições > 15% da carteira (12m)"
    flags.append(rf2)

    # RF3 — 1-2 cotistas, interesse único, subordinação < 5%, PL > R$ 100 mi
    rf3 = con.execute(f"""
    WITH cot AS (SELECT CNPJ, SUM(TAB_X_NR_COTST) n_cot FROM cotistas_serie
                 WHERE DT_COMPTC='{CORTE}' GROUP BY 1),
    subx AS (
      SELECT CNPJ,
        SUM(VL_SERIE) FILTER (TIPO_COTA IN ('subordinada','mezanino')) v_sub,
        SUM(VL_SERIE) v_tot
      FROM series_cotas WHERE DT_COMPTC='{CORTE}' GROUP BY 1)
    SELECT p.DENOM_SOCIAL, p.CNPJ, p.VL_PL, c.n_cot, a.COTST_INTERESSE,
           s.v_sub/nullif(s.v_tot,0) subord
    FROM painel_saneado p
    JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    JOIN cot c ON c.CNPJ=p.CNPJ
    LEFT JOIN subx s ON s.CNPJ=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' AND p.VL_PL > 1e8 AND c.n_cot <= 2
      AND a.COTST_INTERESSE='S' AND coalesce(s.v_sub/nullif(s.v_tot,0),0) < 0.05
    ORDER BY p.VL_PL DESC""").df()
    rf3["red_flag"] = "RF3 1-2 cotistas + interesse único + subordinação <5%"
    flags.append(rf3)

    # RF4 — queda de PL > 50% m/m nos últimos 12m (PL anterior > R$ 200 mi)
    rf4 = con.execute("""
    WITH x AS (
      SELECT CNPJ, DENOM_SOCIAL, DT_COMPTC, VL_PL,
             LAG(VL_PL) OVER (PARTITION BY CNPJ ORDER BY DT_COMPTC) pl_ant
      FROM painel_saneado)
    SELECT DENOM_SOCIAL, CNPJ, DT_COMPTC, pl_ant, VL_PL, VL_PL/pl_ant-1 var
    FROM x WHERE DT_COMPTC>='2025-07-01' AND pl_ant>2e8 AND VL_PL/pl_ant-1 < -0.50
    ORDER BY var""").df()
    rf4["red_flag"] = "RF4 queda de PL > 50% m/m (12m)"
    flags.append(rf4)

    # RF5 — crescimento > 150% em 12m com cedente máximo >= 80%
    rf5 = con.execute(f"""
    WITH h AS (SELECT CNPJ, VL_PL pl_12m FROM painel_saneado WHERE DT_COMPTC='2025-06-30'),
    topced AS (SELECT CNPJ, MAX(PR_CEDENTE) pr_max FROM cedentes
               WHERE DT_COMPTC='{CORTE}' AND PR_CEDENTE BETWEEN 0 AND 100 GROUP BY 1)
    SELECT p.DENOM_SOCIAL, p.CNPJ, h.pl_12m, p.VL_PL, p.VL_PL/h.pl_12m-1 crescimento, t.pr_max
    FROM painel_saneado p JOIN h ON h.CNPJ=p.CNPJ JOIN topced t ON t.CNPJ=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' AND p.VL_PL > 2e8 AND h.pl_12m > 1e7
      AND p.VL_PL/h.pl_12m-1 > 1.5 AND t.pr_max >= 80
    ORDER BY p.VL_PL DESC""").df()
    rf5["red_flag"] = "RF5 crescimento >150% em 12m + cedente >=80%"
    flags.append(rf5)

    out = pd.concat(flags, ignore_index=True)
    out.to_csv(f"{OUT}/red_flags_regulatorios.csv", index=False)
    print(out.red_flag.value_counts().to_string())

    # RF6 — exposição nominal a prestadores/veículos ligados a liquidações BCB
    termos = ["REAG", "GOLD STYLE", "BANCO MASTER", "MASTER S.A"]
    rf6 = con.execute(f"""
    SELECT DISTINCT p.DENOM_SOCIAL, p.CNPJ, p.DT_COMPTC, p.VL_PL,
           a.ADMIN, g.gestor
    FROM painel p
    LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    LEFT JOIN (
      SELECT regexp_replace(rc.CNPJ_Classe,'\\D','','g') cnpj, MAX(rf.Gestor) gestor
      FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo) GROUP BY 1) g
      ON g.cnpj = p.CNPJ
    WHERE p.DT_COMPTC IN ('2025-06-30','2025-12-31','{CORTE}') AND (
      {" OR ".join(f"upper(p.DENOM_SOCIAL) LIKE '%{t}%' OR upper(a.ADMIN) LIKE '%{t}%' OR upper(g.gestor) LIKE '%{t}%'" for t in termos)})
    ORDER BY p.DT_COMPTC, p.VL_PL DESC""").df()
    rf6.to_csv(f"{OUT}/red_flags_liquidacoes_bcb.csv", index=False)
    print(f"\nRF6 veículos com REAG/GOLD STYLE/MASTER no nome/prestador: "
          f"{rf6.CNPJ.nunique()} CNPJs")
    print(rf6[rf6.DT_COMPTC == rf6.DT_COMPTC.max()].head(12)[
        ["DENOM_SOCIAL", "VL_PL", "ADMIN"]].assign(
        DENOM_SOCIAL=lambda d: d.DENOM_SOCIAL.str[:55],
        VL_PL=lambda d: (d.VL_PL / 1e6).round(1)).to_string(index=False))
    # ---- concentração de veículos sinalizados por gestor ----
    # unidade: CNPJs distintos sinalizados em qualquer RF1-RF5 no corte
    flagged = set(out.CNPJ.astype(str))
    con2 = con
    gest_map = con2.execute(r"""
      WITH mapa AS (
        SELECT regexp_replace(rc.CNPJ_Classe,'\D','','g') cnpj, MAX(rf.Gestor) gestor
        FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo) GROUP BY 1
        UNION ALL
        SELECT regexp_replace(CNPJ_Fundo,'\D','','g'), MAX(Gestor) FROM registro_fundo GROUP BY 1)
      SELECT cnpj, MAX(gestor) gestor FROM mapa WHERE gestor IS NOT NULL GROUP BY 1""").df()
    pl_corte = con2.execute(f"""
      SELECT CNPJ, DENOM_SOCIAL, VL_PL FROM painel_saneado WHERE DT_COMPTC='{CORTE}'""").df()
    pl_corte = pl_corte.merge(gest_map, left_on="CNPJ", right_on="cnpj", how="left")
    pl_corte["flagged"] = pl_corte.CNPJ.isin(flagged)
    nflags = out.groupby("CNPJ").red_flag.nunique()
    pl_corte["n_flags"] = pl_corte.CNPJ.map(nflags).fillna(0).astype(int)
    g = (pl_corte.groupby("gestor", dropna=True)
         .agg(pl_total_gestor=("VL_PL", "sum"),
              pl_sinalizado=("VL_PL", lambda x: x[pl_corte.loc[x.index, "flagged"]].sum()),
              n_veiculos_sinalizados=("flagged", "sum"),
              n_veiculos=("CNPJ", "nunique"))
         .reset_index())
    g["pct_carteira_sinalizada"] = g.pl_sinalizado / g.pl_total_gestor
    g = g[g.n_veiculos_sinalizados > 0].sort_values("pl_sinalizado", ascending=False)
    g.to_csv(f"{OUT}/red_flags_por_gestor.csv", index=False)
    print("\nGestores com maior PL sinalizado (top 8):")
    print(g.head(8).assign(pl_sinalizado=lambda d: (d.pl_sinalizado/1e9).round(2),
                           pct=lambda d: (d.pct_carteira_sinalizada*100).round(0))[
        ["gestor", "pl_sinalizado", "n_veiculos_sinalizados", "pct"]].to_string(index=False))

    # ---- detentores dos veículos sinalizados ----
    # (a) via CDA: fundos não-FIDC que detêm cotas dos sinalizados
    import os as _os
    cda_path = _os.path.join(ROOT, "data", "raw", "extracted_cda", "cda_fi_BLC_2_202606.csv")
    blc = pd.read_csv(cda_path, sep=";", encoding="latin1", dtype=str, quoting=3)
    blc["VL_MERC_POS_FINAL"] = pd.to_numeric(blc.VL_MERC_POS_FINAL, errors="coerce")
    blc["cnpj_investidor"] = blc.CNPJ_FUNDO_CLASSE.str.replace(r"\D", "", regex=True)
    blc["cnpj_cota"] = blc.CNPJ_FUNDO_CLASSE_COTA.str.replace(r"\D", "", regex=True)
    posf = blc[blc.cnpj_cota.isin(flagged)].copy()
    det = (posf.groupby(["cnpj_investidor", "DENOM_SOCIAL"], as_index=False)
           .agg(vl=("VL_MERC_POS_FINAL", "sum"),
                n_sinalizados=("cnpj_cota", "nunique"),
                n_ligadas=("EMISSOR_LIGADO", lambda x: (x == "S").sum())))
    det = det.merge(gest_map, left_on="cnpj_investidor", right_on="cnpj", how="left")
    det = det.sort_values("vl", ascending=False)
    det.to_csv(f"{OUT}/red_flags_detentores_cda.csv", index=False)
    lig_share = posf[posf.EMISSOR_LIGADO == "S"].VL_MERC_POS_FINAL.sum() / max(posf.VL_MERC_POS_FINAL.sum(), 1)
    # (b) perfil de cotistas (X.1.1) dos sinalizados
    fl_list = "','".join(sorted(flagged))
    cot = con2.execute(f"""
      SELECT * FROM cotistas_tipo WHERE DT_COMPTC='{CORTE}' AND CNPJ IN ('{fl_list}')""").df()
    cols = [c for c in cot.columns if c.startswith("TAB_X_NR_COTST_")]
    perfil = cot[cols].sum().rename("n_cotistas").to_frame()
    perfil["classe"] = ["senior" if "_SENIOR_" in i else "subordinada" for i in perfil.index]
    perfil["categoria"] = [i.replace("TAB_X_NR_COTST_SENIOR_", "").replace("TAB_X_NR_COTST_SUBORD_", "")
                           for i in perfil.index]
    perfil.to_csv(f"{OUT}/red_flags_cotistas_perfil.csv")
    resumo_det = pd.DataFrame([{
        "pl_sinalizado_total": pl_corte[pl_corte.flagged].VL_PL.sum(),
        "n_veiculos_sinalizados": int(pl_corte.flagged.sum()),
        "vl_detido_via_cda": posf.VL_MERC_POS_FINAL.sum(),
        "share_emissor_ligado_na_cda": lig_share,
        "n_fundos_detentores_cda": det.cnpj_investidor.nunique(),
    }])
    resumo_det.to_csv(f"{OUT}/red_flags_detentores_resumo.csv", index=False)
    print("\nDetentores CDA dos sinalizados:", round(posf.VL_MERC_POS_FINAL.sum()/1e9, 2),
          "bi em", det.cnpj_investidor.nunique(), "fundos; emissor ligado:",
          f"{lig_share:.0%}")

    # série do PL administrado pela CBSF DTVM (ex-Reag Trust) — para o painel
    cbsf = con.execute("""
    SELECT substr(a.DT_COMPTC,1,7) m, SUM(p.VL_PL) pl, COUNT(*) n
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE regexp_replace(a.CNPJ_ADMIN,'\\D','','g')='34829992000186'
      AND a.DT_COMPTC>='2025-06-01'
    GROUP BY 1 ORDER BY 1""").df()
    cbsf.to_csv(f"{OUT}/cbsf_exreag_serie.csv", index=False)

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
