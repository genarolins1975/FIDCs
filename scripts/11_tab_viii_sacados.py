#!/usr/bin/env python3
"""
Etapa 11 — Tabela VIII do informe mensal: concentração de SACADOS (devedores).

A tabela VIII traz, por veículo e competência, os 25 MAIORES DEVEDORES
(sacados) da carteira de direitos creditórios, em ordem decrescente de valor.

LIMITAÇÃO ESTRUTURAL DA FONTE (declarada, não contornável):
  O layout da tab VIII tem apenas TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE,
  DENOM_SOCIAL, DT_COMPTC, SEQUENCIAL (1..25) e VALOR. NÃO HÁ CPF/CNPJ,
  nome ou qualquer identificador do sacado. Portanto:
    - é IMPOSSÍVEL somar a exposição de um mesmo sacado em vários veículos;
    - é IMPOSSÍVEL construir ranking de devedores do mercado;
    - o SEQUENCIAL é posição no ranking DENTRO do veículo, não identidade.
  Nenhuma identidade de sacado é inferida ou atribuída neste script.

LIMITAÇÃO DE COBERTURA DA MEDIDA:
  Só se observam os 25 maiores. O HHI calculado é, por construção, um PISO
  (limite inferior) do HHI verdadeiro da carteira — a cauda não observada
  contribui com valor positivo. Daí o nome hhi_parcial_piso.

REGRA DE NULOS (decisão metodológica central desta etapa):
  O denominador é o total de direitos creditórios do veículo,
  TAB_I2A_VL_DIRCRED_RISCO + TAB_I2B_VL_DIRCRED_SEM_RISCO (tabela ativo).
  Se o veículo não tem linha na tab I na competência, ou se o denominador
  resultante é NULO ou ZERO, TODAS as razões saem NULAS — nunca zero.
  Ausência de informação não é concentração zero. (No corte de jun/2026 há
  1.135 veículos com DC = 0 no informe — tipicamente FICs de FIDC e veículos
  que só carregam cotas/títulos: para eles a razão sacado/DC é indefinida.)

Saídas:
  data/analytic/sacados_concentracao.csv         (um registro por veículo, corte)
  data/analytic/sacados_concentracao_resumo.csv  (agregados de mercado, corte)
  data/analytic/sacados_cobertura_serie.csv      (cobertura mês a mês)
  data/analytic/sacados_dedup_log.csv            (duplicatas removidas por mês)
  tabela DuckDB sacados_conc (linha a linha, todas as competências)
  tabela DuckDB sacados_metricas (métricas por veículo x competência)

Reprodução: python3 scripts/11_tab_viii_sacados.py
"""
import glob
import os
import re
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXTRACT = os.environ.get("FIDC_EXTRACT_DIR",
                         os.path.join(ROOT, "data", "raw", "extracted"))
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")

CORTE = "2026-06-30"

pd.options.mode.copy_on_write = True


def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="latin1", dtype=str, quoting=3)


def carregar_tab_viii():
    """Concatena todas as competências da tab VIII, deduplicando por
    (CNPJ, DT_COMPTC, SEQUENCIAL) com keep='last' e logando as duplicatas."""
    pat = re.compile(r"inf_mensal_fidc_tab_VIII_(\d{6})\.csv$")
    arquivos = [f for f in sorted(glob.glob(os.path.join(EXTRACT, "*.csv")))
                if pat.search(os.path.basename(f))]
    if not arquivos:
        raise SystemExit("nenhum arquivo tab VIII encontrado em " + EXTRACT)

    log, frames = [], []
    for f in arquivos:
        comp = pat.search(os.path.basename(f)).group(1)
        df = read_csv(f)
        if "CNPJ_FUNDO_CLASSE" not in df.columns and "CNPJ_FUNDO" in df.columns:
            df = df.rename(columns={"CNPJ_FUNDO": "CNPJ_FUNDO_CLASSE"})
        if "TP_FUNDO_CLASSE" not in df.columns:
            df["TP_FUNDO_CLASSE"] = "Fundo"
        df["CNPJ"] = df["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
        df["SEQUENCIAL"] = pd.to_numeric(df["SEQUENCIAL"], errors="coerce").astype("Int64")
        df["VALOR"] = pd.to_numeric(df["VALOR"], errors="coerce")
        n0 = len(df)
        df = df.drop_duplicates(subset=["CNPJ", "DT_COMPTC", "SEQUENCIAL"], keep="last")
        log.append({"arquivo": os.path.basename(f), "competencia": comp,
                    "linhas_lidas": n0, "duplicatas_removidas": n0 - len(df),
                    "linhas_mantidas": len(df),
                    "valores_nulos": int(df["VALOR"].isna().sum()),
                    "valores_negativos": int((df["VALOR"] < 0).sum()),
                    "valores_zero": int((df["VALOR"] == 0).sum())})
        frames.append(df[["TP_FUNDO_CLASSE", "CNPJ", "DENOM_SOCIAL", "DT_COMPTC",
                          "SEQUENCIAL", "VALOR"]])
    return pd.concat(frames, ignore_index=True), pd.DataFrame(log)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    sac, dedup_log = carregar_tab_viii()
    dedup_log.to_csv(f"{OUT}/sacados_dedup_log.csv", index=False)
    print(f"tab VIII: {len(sac):,} linhas, "
          f"{int(dedup_log.duplicatas_removidas.sum())} duplicatas removidas, "
          f"{sac.DT_COMPTC.nunique()} competências "
          f"({sac.DT_COMPTC.min()} a {sac.DT_COMPTC.max()})")

    con = duckdb.connect(DB)
    con.execute("PRAGMA threads=4")
    con.register("sac_df", sac)
    con.execute("CREATE OR REPLACE TABLE sacados_conc AS SELECT * FROM sac_df")

    # ------------------------------------------------------------------
    # Métricas por veículo x competência.
    # Denominador: DC = TAB_I2A + TAB_I2B. NULO ou ZERO => razões NULAS.
    # ------------------------------------------------------------------
    con.execute("""
    CREATE OR REPLACE TABLE sacados_metricas AS
    WITH s AS (
      SELECT CNPJ, DT_COMPTC,
             MAX(TP_FUNDO_CLASSE) TP_FUNDO_CLASSE,
             MAX(DENOM_SOCIAL)    DENOM_SOCIAL,
             COUNT(*)             n_sacados_reportados,
             MAX(VALOR) FILTER (SEQUENCIAL = 1)                 top1,
             SUM(VALOR) FILTER (SEQUENCIAL BETWEEN 1 AND 5)     top5,
             SUM(VALOR) FILTER (SEQUENCIAL BETWEEN 1 AND 10)    top10,
             SUM(VALOR)                                         top25,
             -- HHI parcial: soma dos quadrados dos VALORES dos 25 maiores;
             -- dividido pelo DC^2 adiante. É PISO do HHI verdadeiro.
             SUM(VALOR * VALOR)                                 soma_quadrados,
             MIN(VALOR) valor_menor_reportado,
             SUM(CASE WHEN VALOR < 0 THEN 1 ELSE 0 END) n_valores_negativos
      FROM sacados_conc
      WHERE VALOR IS NOT NULL
      GROUP BY 1, 2),
    dc AS (
      SELECT CNPJ, DT_COMPTC,
             TAB_I2A_VL_DIRCRED_RISCO      dc_com_risco,
             TAB_I2B_VL_DIRCRED_SEM_RISCO  dc_sem_risco,
             -- soma estrita: NULA se qualquer componente for NULO
             TAB_I2A_VL_DIRCRED_RISCO + TAB_I2B_VL_DIRCRED_SEM_RISCO dc_total
      FROM ativo)
    SELECT s.DT_COMPTC, s.CNPJ, s.DENOM_SOCIAL, s.TP_FUNDO_CLASSE,
           s.n_sacados_reportados, s.n_valores_negativos, s.valor_menor_reportado,
           s.top1, s.top5, s.top10, s.top25,
           dc.dc_com_risco, dc.dc_sem_risco, dc.dc_total,
           (dc.CNPJ IS NULL)                       AS sem_linha_tab_i,
           (dc.dc_total IS NULL OR dc.dc_total = 0) AS denominador_indisponivel,
           -- NULLIF(...,0) garante NULO (nunca zero) quando o DC é 0;
           -- DC nulo já propaga nulo naturalmente.
           s.top1  / NULLIF(dc.dc_total, 0) AS top1_sobre_dc,
           s.top5  / NULLIF(dc.dc_total, 0) AS top5_sobre_dc,
           s.top10 / NULLIF(dc.dc_total, 0) AS top10_sobre_dc,
           s.top25 / NULLIF(dc.dc_total, 0) AS top25_sobre_dc,
           s.soma_quadrados / NULLIF(dc.dc_total * dc.dc_total, 0) AS hhi_parcial_piso,
           -- Inconsistência entre fontes: a soma dos 25 maiores sacados não
           -- pode exceder o DC informado na tab I. Quando excede (tolerância
           -- de 5% para arredondamento/atualização de valor presente), a razão
           -- é aritmeticamente válida mas economicamente não interpretável.
           -- NÃO se corrige nem se descarta o dado: marca-se.
           (s.top25 / NULLIF(dc.dc_total, 0) > 1.05) AS inconsistencia_viii_vs_i
    FROM s LEFT JOIN dc ON dc.CNPJ = s.CNPJ AND dc.DT_COMPTC = s.DT_COMPTC
    """)

    # ------------------------------------------------------------------
    # Cobertura mês a mês: quantos veículos do painel canônico têm tab VIII
    # e que fração do DC de mercado eles representam.
    # ------------------------------------------------------------------
    cob_serie = con.execute("""
    WITH base AS (
      SELECT p.DT_COMPTC, p.CNPJ,
             a.TAB_I2A_VL_DIRCRED_RISCO + a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc,
             (m.CNPJ IS NOT NULL) tem_viii
      FROM painel_saneado p
      LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
      LEFT JOIN sacados_metricas m ON m.CNPJ=p.CNPJ AND m.DT_COMPTC=p.DT_COMPTC
      WHERE p.DT_COMPTC >= '2025-01-31')
    SELECT DT_COMPTC,
      COUNT(*) n_veiculos_painel,
      COUNT(*) FILTER (tem_viii) n_veiculos_com_tab_viii,
      COUNT(*) FILTER (tem_viii)::DOUBLE / COUNT(*) pct_veiculos,
      COUNT(*) FILTER (dc > 0) n_veiculos_com_dc_positivo,
      COUNT(*) FILTER (dc > 0 AND tem_viii) n_com_dc_e_tab_viii,
      COUNT(*) FILTER (dc > 0 AND tem_viii)::DOUBLE
        / NULLIF(COUNT(*) FILTER (dc > 0), 0) pct_veiculos_com_dc,
      SUM(dc) dc_mercado,
      SUM(dc) FILTER (tem_viii) dc_com_tab_viii,
      SUM(dc) FILTER (tem_viii) / NULLIF(SUM(dc), 0) pct_dc_coberto
    FROM base GROUP BY 1 ORDER BY 1""").df()
    cob_serie.to_csv(f"{OUT}/sacados_cobertura_serie.csv", index=False)

    # ------------------------------------------------------------------
    # Recorte por veículo no corte (só veículos do painel canônico)
    # ------------------------------------------------------------------
    det = con.execute(f"""
    SELECT m.DT_COMPTC, m.CNPJ, m.DENOM_SOCIAL, m.TP_FUNDO_CLASSE,
           p.VL_PL, a.ADMIN,
           m.n_sacados_reportados, m.n_valores_negativos,
           m.top1, m.top5, m.top10, m.top25,
           m.dc_com_risco, m.dc_sem_risco, m.dc_total,
           m.denominador_indisponivel,
           m.top1_sobre_dc, m.top5_sobre_dc, m.top10_sobre_dc, m.top25_sobre_dc,
           m.hhi_parcial_piso, m.inconsistencia_viii_vs_i
    FROM sacados_metricas m
    JOIN painel_saneado p ON p.CNPJ=m.CNPJ AND p.DT_COMPTC=m.DT_COMPTC
    LEFT JOIN ativo a ON a.CNPJ=m.CNPJ AND a.DT_COMPTC=m.DT_COMPTC
    WHERE m.DT_COMPTC='{CORTE}'
    ORDER BY m.top1 DESC NULLS LAST""").df()
    det.to_csv(f"{OUT}/sacados_concentracao.csv", index=False)

    # ------------------------------------------------------------------
    # Resumo de mercado no corte.
    # Distribuição calculada SÓ sobre veículos com razão definida (DC>0).
    # ------------------------------------------------------------------
    linha_cob = cob_serie[cob_serie.DT_COMPTC == CORTE].iloc[0]
    v = det[det.top1_sobre_dc.notna()]
    # subconjunto interpretável: tab VIII e tab I reconciliam (top25 <= 1.05*DC)
    vc = v[~v.inconsistencia_viii_vs_i.astype(bool)]

    def q(col, p):
        return float(v[col].quantile(p)) if len(v) else None

    resumo_rows = [
        {"metrica": "competencia_corte", "valor": CORTE, "unidade": "data",
         "observacao": "corte de totalização do painel"},
        {"metrica": "n_veiculos_painel_saneado", "valor": int(linha_cob.n_veiculos_painel),
         "unidade": "veículos", "observacao": "universo do painel canônico no corte"},
        {"metrica": "n_veiculos_com_tab_viii", "valor": int(linha_cob.n_veiculos_com_tab_viii),
         "unidade": "veículos", "observacao": "veículos do painel com tab VIII preenchida"},
        {"metrica": "pct_veiculos_com_tab_viii", "valor": float(linha_cob.pct_veiculos),
         "unidade": "fração", "observacao": "cobertura em número de veículos"},
        {"metrica": "n_veiculos_com_dc_positivo", "valor": int(linha_cob.n_veiculos_com_dc_positivo),
         "unidade": "veículos", "observacao": "veículos com DC > 0 (universo elegível)"},
        {"metrica": "pct_veiculos_com_dc_e_tab_viii", "valor": float(linha_cob.pct_veiculos_com_dc),
         "unidade": "fração", "observacao": "cobertura entre os elegíveis (DC > 0)"},
        {"metrica": "dc_mercado", "valor": float(linha_cob.dc_mercado),
         "unidade": "R$", "observacao": "DC total do painel no corte"},
        {"metrica": "dc_com_tab_viii", "valor": float(linha_cob.dc_com_tab_viii),
         "unidade": "R$", "observacao": "DC dos veículos com tab VIII"},
        {"metrica": "pct_dc_coberto", "valor": float(linha_cob.pct_dc_coberto),
         "unidade": "fração", "observacao": "cobertura em R$ de direitos creditórios"},
        {"metrica": "n_veiculos_razao_definida", "valor": int(len(v)),
         "unidade": "veículos",
         "observacao": "base das estatísticas de concentração (tab VIII e DC > 0)"},
        {"metrica": "n_veiculos_tab_viii_sem_denominador",
         "valor": int(det.denominador_indisponivel.sum()), "unidade": "veículos",
         "observacao": "tab VIII presente mas DC nulo/zero: razões NULAS, não zero"},
    ]
    for col, rot in (("top1_sobre_dc", "top1"), ("top5_sobre_dc", "top5"),
                     ("top10_sobre_dc", "top10"), ("top25_sobre_dc", "top25"),
                     ("hhi_parcial_piso", "hhi_parcial_piso")):
        for p, nome in ((0.50, "mediana"), (0.75, "p75"), (0.90, "p90"),
                        (0.99, "p99")):
            resumo_rows.append({"metrica": f"{rot}_{nome}", "valor": q(col, p),
                                "unidade": "fração" if rot != "hhi_parcial_piso" else "índice",
                                "observacao": f"distribuição entre os {len(v)} veículos com razão definida"})
        # NÃO se publica média sobre o conjunto completo: os veículos com
        # inconsistência tab VIII x tab I produzem razões de ordem 1e9 e
        # contaminam qualquer momento não-robusto. Média só no reconciliado.
    for lim in (0.20, 0.50, 0.80, 1.00):
        for col, rot in (("top1_sobre_dc", "top1"), ("top5_sobre_dc", "top5"),
                         ("top10_sobre_dc", "top10")):
            n = int((v[col] > lim).sum())
            resumo_rows.append({
                "metrica": f"n_veiculos_{rot}_acima_{int(lim*100)}pct", "valor": n,
                "unidade": "veículos",
                "observacao": f"{n/len(v):.1%} dos {len(v)} com razão definida"})
    # massa de DC nos veículos muito concentrados
    for lim in (0.20, 0.50, 0.80):
        m = v[v.top1_sobre_dc > lim]
        resumo_rows.append({
            "metrica": f"dc_em_veiculos_top1_acima_{int(lim*100)}pct",
            "valor": float(m.dc_total.sum()), "unidade": "R$",
            "observacao": f"{m.dc_total.sum()/v.dc_total.sum():.1%} do DC dos veículos com razão definida"})
    resumo_rows.append({
        "metrica": "top25_sobre_dc_acima_de_1",
        "valor": int((v.top25_sobre_dc > 1.0).sum()), "unidade": "veículos",
        "observacao": "soma dos 25 maiores > DC informado: inconsistência de "
                      "preenchimento entre tab VIII e tab I (não corrigida)"})
    resumo_rows.append({
        "metrica": "n_veiculos_inconsistencia_viii_vs_i",
        "valor": int(v.inconsistencia_viii_vs_i.sum()), "unidade": "veículos",
        "observacao": "top25 > 1,05 x DC: razão não interpretável; dado mantido e marcado"})
    resumo_rows.append({
        "metrica": "dc_em_veiculos_inconsistentes",
        "valor": float(v[v.inconsistencia_viii_vs_i.astype(bool)].dc_total.sum()),
        "unidade": "R$", "observacao": "DC informado (tab I) nos veículos marcados"})
    resumo_rows.append({
        "metrica": "n_veiculos_reconciliados", "valor": int(len(vc)),
        "unidade": "veículos",
        "observacao": "base das estatísticas '_reconciliado' abaixo (tab VIII <= 1,05 x DC)"})
    # distribuição no subconjunto reconciliado — leitura recomendada
    for col, rot in (("top1_sobre_dc", "top1"), ("top5_sobre_dc", "top5"),
                     ("top10_sobre_dc", "top10"), ("top25_sobre_dc", "top25"),
                     ("hhi_parcial_piso", "hhi_parcial_piso")):
        for p, nome in ((0.50, "mediana"), (0.75, "p75"), (0.90, "p90")):
            resumo_rows.append({
                "metrica": f"{rot}_{nome}_reconciliado",
                "valor": float(vc[col].quantile(p)),
                "unidade": "fração" if rot != "hhi_parcial_piso" else "índice",
                "observacao": f"entre os {len(vc)} veículos reconciliados"})
        resumo_rows.append({
            "metrica": f"{rot}_media_reconciliado", "valor": float(vc[col].mean()),
            "unidade": "fração" if rot != "hhi_parcial_piso" else "índice",
            "observacao": "média simples; só faz sentido no subconjunto reconciliado"})
        resumo_rows.append({
            "metrica": f"{rot}_ponderado_por_dc_reconciliado",
            "valor": float((vc[col] * vc.dc_total).sum() / vc.dc_total.sum()),
            "unidade": "fração" if rot != "hhi_parcial_piso" else "índice",
            "observacao": "média ponderada pelo DC do veículo"})
    for lim in (0.20, 0.50, 0.80):
        n = int((vc.top1_sobre_dc > lim).sum())
        resumo_rows.append({
            "metrica": f"n_veiculos_top1_acima_{int(lim*100)}pct_reconciliado",
            "valor": n, "unidade": "veículos",
            "observacao": f"{n/len(vc):.1%} dos {len(vc)} reconciliados"})
    resumo = pd.DataFrame(resumo_rows)
    resumo.to_csv(f"{OUT}/sacados_concentracao_resumo.csv", index=False)

    # ------------------------------------------------------------------
    print("\ncobertura da tab VIII ao longo do tempo (% do DC do painel):")
    print(cob_serie[["DT_COMPTC", "n_veiculos_painel", "n_veiculos_com_tab_viii",
                     "pct_veiculos", "pct_dc_coberto"]].round(3).to_string(index=False))
    print(f"\ncobertura tab VIII no corte {CORTE}:")
    print(f"  veículos do painel: {int(linha_cob.n_veiculos_painel):,}; "
          f"com tab VIII: {int(linha_cob.n_veiculos_com_tab_viii):,} "
          f"({linha_cob.pct_veiculos:.1%})")
    print(f"  com DC>0: {int(linha_cob.n_veiculos_com_dc_positivo):,}; destes com tab VIII: "
          f"{int(linha_cob.n_com_dc_e_tab_viii):,} ({linha_cob.pct_veiculos_com_dc:.1%})")
    print(f"  DC do mercado: R$ {linha_cob.dc_mercado/1e9:,.1f} bi; "
          f"coberto pela tab VIII: R$ {linha_cob.dc_com_tab_viii/1e9:,.1f} bi "
          f"({linha_cob.pct_dc_coberto:.1%})")
    print(f"  veículos com razão definida: {len(v):,}; "
          f"com tab VIII mas sem denominador: {int(det.denominador_indisponivel.sum()):,}")
    print(f"  marcados como inconsistentes (top25 > 1,05 x DC): "
          f"{int(v.inconsistencia_viii_vs_i.sum()):,}; reconciliados: {len(vc):,}")
    cols = ["top1_sobre_dc", "top5_sobre_dc", "top10_sobre_dc", "top25_sobre_dc",
            "hhi_parcial_piso"]
    print("\ndistribuição — veículos RECONCILIADOS (leitura recomendada):")
    print(vc[cols].describe(percentiles=[.25, .5, .75, .9]).to_string())
    print("\ndistribuição — todos os veículos com razão definida (inclui inconsistentes):")
    print(v[cols].quantile([.25, .5, .75, .9]).to_string())
    print("\nveículos por faixa de concentração do maior sacado:")
    for lim in (0.20, 0.50, 0.80):
        n, nc = int((v.top1_sobre_dc > lim).sum()), int((vc.top1_sobre_dc > lim).sum())
        print(f"  top1 > {lim:.0%} do DC: {n:,} ({n/len(v):.1%}) de todos; "
              f"{nc:,} ({nc/len(vc):.1%}) dos reconciliados")
    print("\ntop 12 veículos por valor do maior sacado:")
    print(det.head(12).assign(
        DENOM_SOCIAL=lambda d: d.DENOM_SOCIAL.str[:44],
        top1_bi=lambda d: (d.top1 / 1e9).round(2),
        dc_bi=lambda d: (d.dc_total / 1e9).round(2),
        t1=lambda d: (d.top1_sobre_dc * 100).round(1))[
        ["DENOM_SOCIAL", "top1_bi", "dc_bi", "t1"]].to_string(index=False))

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
