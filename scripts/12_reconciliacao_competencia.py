#!/usr/bin/env python3
"""
Etapa 12 — Reconciliação de competência: 2026-07-31 vs 2026-06-30.

Pergunta que este script decide: o corte de totalização do painel deve ser
junho ou julho de 2026?

A última competência publicada de um informe periódico está sempre sujeita a
entrega retardatária: veículos que ainda não transmitiram aparecem como
"inexistentes", não como "zero". Se o corte for feito na última competência
disponível, o PL de mercado é SUBESTIMADO por ausência de reporte, e a queda
aparente é confundida com contração real do mercado.

O script mede exatamente:
  (a) quantos CNPJs informaram em 06/2026 e não em 07/2026, e o PL desses ausentes;
  (b) se os ausentes se concentram em algum administrador (contagem, PL e
      participação do administrador que ficou de fora);
  (c) o padrão histórico de "sumiço" mês a mês, para separar o que é
      atrito normal (encerramentos, incorporações) do que é atraso de entrega
      típico da última competência;
  (d) o cruzamento com o registro CVM (situação do fundo/classe), para
      identificar quantos ausentes têm motivo cadastral (liquidação,
      cancelamento) e quantos são simplesmente silêncio.

Saída: data/analytic/cobertura_competencia_202607.csv (uma linha por
administrador, mais linhas-resumo com metrica/valor no arquivo
cobertura_competencia_202607_resumo.csv) e a lista dos ausentes em
data/analytic/cobertura_competencia_202607_ausentes.csv.

Reprodução: python3 scripts/12_reconciliacao_competencia.py
"""
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")

M_ANT, M_ULT = "2026-06-30", "2026-07-31"


def main() -> int:
    con = duckdb.connect(DB, read_only=True)

    # ---------- (a) ausentes e seu PL ----------
    ausentes = con.execute(f"""
    WITH jun AS (SELECT * FROM painel_saneado WHERE DT_COMPTC='{M_ANT}'),
    jul AS (SELECT CNPJ FROM painel_saneado WHERE DT_COMPTC='{M_ULT}'),
    reg AS (
      SELECT regexp_replace(CNPJ_Classe,'\\D','','g') cnpj, MAX(Situacao) situacao
      FROM registro_classe GROUP BY 1
      UNION ALL
      SELECT regexp_replace(CNPJ_Fundo,'\\D','','g'), MAX(Situacao)
      FROM registro_fundo GROUP BY 1),
    reg1 AS (SELECT cnpj, MAX(situacao) situacao FROM reg WHERE cnpj<>'' GROUP BY 1)
    SELECT jun.CNPJ, jun.DENOM_SOCIAL, jun.TP_FUNDO_CLASSE, jun.VL_PL,
           regexp_replace(a.CNPJ_ADMIN,'\\D','','g') cnpj_admin, a.ADMIN,
           a.TAB_I2A_VL_DIRCRED_RISCO + a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc_total,
           r.situacao situacao_registro
    FROM jun
    LEFT JOIN jul ON jul.CNPJ = jun.CNPJ
    LEFT JOIN ativo a ON a.CNPJ=jun.CNPJ AND a.DT_COMPTC='{M_ANT}'
    LEFT JOIN reg1 r ON r.cnpj = jun.CNPJ
    WHERE jul.CNPJ IS NULL
    ORDER BY jun.VL_PL DESC""").df()
    ausentes.to_csv(f"{OUT}/cobertura_competencia_202607_ausentes.csv", index=False)

    # Verificação: a ausência é da FONTE ou foi criada pelas regras de dedup do
    # painel canônico? Confere os ausentes contra a tabela pl BRUTA de julho.
    aus_no_bruto = con.execute(f"""
    WITH jun AS (SELECT CNPJ FROM painel_saneado WHERE DT_COMPTC='{M_ANT}'),
    jul AS (SELECT CNPJ FROM painel_saneado WHERE DT_COMPTC='{M_ULT}'),
    aus AS (SELECT jun.CNPJ FROM jun LEFT JOIN jul USING (CNPJ) WHERE jul.CNPJ IS NULL)
    SELECT COUNT(*) FILTER (EXISTS (SELECT 1 FROM pl
             WHERE pl.CNPJ=aus.CNPJ AND pl.DT_COMPTC='{M_ULT}')) FROM aus""").fetchone()[0]

    tot = con.execute(f"""
    SELECT
      (SELECT COUNT(*) FROM painel_saneado WHERE DT_COMPTC='{M_ANT}') n_jun,
      (SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{M_ANT}') pl_jun,
      (SELECT COUNT(*) FROM painel_saneado WHERE DT_COMPTC='{M_ULT}') n_jul,
      (SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{M_ULT}') pl_jul""").fetchone()
    n_jun, pl_jun, n_jul, pl_jul = tot

    novos = con.execute(f"""
    WITH jun AS (SELECT CNPJ FROM painel_saneado WHERE DT_COMPTC='{M_ANT}'),
    jul AS (SELECT * FROM painel_saneado WHERE DT_COMPTC='{M_ULT}')
    SELECT COUNT(*) n, SUM(jul.VL_PL) pl FROM jul
    LEFT JOIN jun ON jun.CNPJ=jul.CNPJ WHERE jun.CNPJ IS NULL""").fetchone()

    # PL dos que informaram nos dois meses (variação "same-store")
    same = con.execute(f"""
    SELECT COUNT(*) n, SUM(j2.VL_PL) pl_jul, SUM(j1.VL_PL) pl_jun
    FROM painel_saneado j1 JOIN painel_saneado j2
      ON j2.CNPJ=j1.CNPJ AND j1.DT_COMPTC='{M_ANT}' AND j2.DT_COMPTC='{M_ULT}'""").fetchone()

    # ---------- (b) concentração dos ausentes por administrador ----------
    por_admin = con.execute(f"""
    WITH jun AS (
      SELECT p.CNPJ, p.VL_PL,
             regexp_replace(a.CNPJ_ADMIN,'\\D','','g') cnpj_admin, a.ADMIN
      FROM painel_saneado p LEFT JOIN ativo a
        ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
      WHERE p.DT_COMPTC='{M_ANT}'),
    jul AS (SELECT CNPJ FROM painel_saneado WHERE DT_COMPTC='{M_ULT}'),
    x AS (SELECT jun.*, (jul.CNPJ IS NULL) ausente
          FROM jun LEFT JOIN jul ON jul.CNPJ=jun.CNPJ)
    SELECT COALESCE(MAX(ADMIN),'(sem administrador na tab I)') nome_admin,
           cnpj_admin,
           COUNT(*) n_veiculos_jun,
           SUM(VL_PL) pl_jun,
           COUNT(*) FILTER (ausente) n_ausentes,
           SUM(VL_PL) FILTER (ausente) pl_ausente,
           COUNT(*) FILTER (ausente)::DOUBLE / COUNT(*) pct_veiculos_ausentes,
           SUM(VL_PL) FILTER (ausente) / NULLIF(SUM(VL_PL),0) pct_pl_ausente
    FROM x GROUP BY cnpj_admin
    ORDER BY pl_ausente DESC NULLS LAST""").df()
    por_admin.to_csv(f"{OUT}/cobertura_competencia_202607.csv", index=False)

    # ---------- (c) padrão histórico de ausências mês a mês ----------
    hist = con.execute("""
    WITH meses AS (SELECT DISTINCT DT_COMPTC FROM painel_saneado
                   WHERE DT_COMPTC >= '2024-01-31'),
    pares AS (
      SELECT m.DT_COMPTC mes,
             LAG(m.DT_COMPTC) OVER (ORDER BY m.DT_COMPTC) mes_ant
      FROM meses m)
    SELECT p.mes, p.mes_ant,
      (SELECT COUNT(*) FROM painel_saneado a WHERE a.DT_COMPTC=p.mes_ant) n_ant,
      (SELECT COUNT(*) FROM painel_saneado a WHERE a.DT_COMPTC=p.mes) n_mes,
      (SELECT COUNT(*) FROM painel_saneado a
       WHERE a.DT_COMPTC=p.mes_ant
         AND NOT EXISTS (SELECT 1 FROM painel_saneado b
                         WHERE b.CNPJ=a.CNPJ AND b.DT_COMPTC=p.mes)) n_sumidos,
      (SELECT SUM(a.VL_PL) FROM painel_saneado a
       WHERE a.DT_COMPTC=p.mes_ant
         AND NOT EXISTS (SELECT 1 FROM painel_saneado b
                         WHERE b.CNPJ=a.CNPJ AND b.DT_COMPTC=p.mes)) pl_sumidos
    FROM pares p WHERE p.mes_ant IS NOT NULL ORDER BY p.mes""").df()
    hist["pct_sumidos"] = hist.n_sumidos / hist.n_ant
    pl_por_mes = con.execute("""
      SELECT DT_COMPTC, SUM(VL_PL) pl FROM painel_saneado GROUP BY 1""").df()
    hist = hist.merge(pl_por_mes.rename(columns={"DT_COMPTC": "mes_ant", "pl": "pl_ant"}),
                      on="mes_ant", how="left")
    hist["pct_pl_sumido"] = hist.pl_sumidos / hist.pl_ant
    hist.to_csv(f"{OUT}/cobertura_competencia_historico.csv", index=False)

    # ---------- (d) situação cadastral dos ausentes ----------
    sit = (ausentes.groupby(ausentes.situacao_registro.fillna("(sem registro)"))
           .agg(n=("CNPJ", "count"), pl=("VL_PL", "sum"))
           .sort_values("pl", ascending=False).reset_index()
           .rename(columns={"situacao_registro": "situacao"}))

    # ---------- resumo ----------
    med_sumidos = hist[hist.mes < M_ULT].n_sumidos.median()
    med_pl_sumido = hist[hist.mes < M_ULT].pct_pl_sumido.median()
    top_admin = por_admin.dropna(subset=["pl_ausente"]).head(5)
    hhi_ausentes = float(((por_admin.pl_ausente.fillna(0) /
                           por_admin.pl_ausente.sum()) ** 2).sum())
    linhas = [
        ("competencia_anterior", M_ANT, "data", ""),
        ("competencia_ultima", M_ULT, "data", ""),
        ("n_informantes_jun", n_jun, "veículos", "painel_saneado"),
        ("n_informantes_jul", n_jul, "veículos", "painel_saneado"),
        ("delta_informantes", n_jul - n_jun, "veículos", ""),
        ("pl_jun", pl_jun, "R$", ""),
        ("pl_jul", pl_jul, "R$", ""),
        ("delta_pl", pl_jul - pl_jun, "R$", "queda aparente do mercado"),
        ("delta_pl_pct", pl_jul / pl_jun - 1, "fração", ""),
        ("n_ausentes_em_jul", len(ausentes), "veículos",
         "informaram em jun e não em jul"),
        ("pl_ausentes_em_jul", float(ausentes.VL_PL.sum()), "R$",
         "PL de junho dos veículos que não informaram em julho"),
        ("pl_ausentes_pct_do_mercado_jun", float(ausentes.VL_PL.sum()) / pl_jun,
         "fração", ""),
        ("dc_ausentes_em_jul", float(ausentes.dc_total.sum(skipna=True)), "R$",
         "direitos creditórios (jun) dos ausentes"),
        ("n_novos_em_jul", novos[0], "veículos", "informaram em jul e não em jun"),
        ("pl_novos_em_jul", float(novos[1] or 0), "R$", ""),
        ("n_informantes_nos_dois_meses", same[0], "veículos", ""),
        ("pl_same_store_jun", float(same[2]), "R$", "só os que informaram nos 2 meses"),
        ("pl_same_store_jul", float(same[1]), "R$", "só os que informaram nos 2 meses"),
        ("var_pl_same_store", float(same[1]) / float(same[2]) - 1, "fração",
         "variação real do mercado, livre do efeito de ausência de reporte"),
        ("mediana_sumidos_mes_a_mes_2024_2026", float(med_sumidos), "veículos",
         "atrito normal em meses já consolidados"),
        ("mediana_pct_pl_sumido_mes_a_mes", float(med_pl_sumido), "fração",
         "atrito normal em meses já consolidados"),
        ("razao_ausencias_jul_sobre_mediana", len(ausentes) / float(med_sumidos),
         "x", "quantas vezes o atrito normal"),
        ("hhi_pl_ausente_por_administrador", hhi_ausentes, "índice",
         "0-1; alto = ausência concentrada em poucos administradores"),
        ("share_top1_admin_no_pl_ausente",
         float(top_admin.pl_ausente.iloc[0] / ausentes.VL_PL.sum()), "fração",
         str(top_admin.nome_admin.iloc[0])[:60]),
        ("share_top5_admin_no_pl_ausente",
         float(top_admin.pl_ausente.sum() / ausentes.VL_PL.sum()), "fração", ""),
        ("ausentes_presentes_na_tabela_pl_bruta", int(aus_no_bruto), "veículos",
         "0 = a ausência é da fonte, não das regras de dedup do painel canônico"),
        ("n_ausentes_em_liquidacao_ou_cancelado",
         int(ausentes.situacao_registro.fillna("").str.contains(
             "Liquid|Cancel", case=False, regex=True).sum()), "veículos",
         "motivo cadastral plausível para não informar"),
    ]
    resumo = pd.DataFrame(linhas, columns=["metrica", "valor", "unidade", "observacao"])
    resumo.to_csv(f"{OUT}/cobertura_competencia_202607_resumo.csv", index=False)

    # ---------- console ----------
    print(f"informantes: {n_jun:,} em {M_ANT} -> {n_jul:,} em {M_ULT} "
          f"({n_jul-n_jun:+,})")
    print(f"PL: R$ {pl_jun/1e9:,.1f} bi -> R$ {pl_jul/1e9:,.1f} bi "
          f"({pl_jul/pl_jun-1:+.2%})")
    print(f"\nausentes em julho: {len(ausentes):,} veículos, "
          f"PL(jun) R$ {ausentes.VL_PL.sum()/1e9:,.1f} bi "
          f"({ausentes.VL_PL.sum()/pl_jun:.1%} do mercado de junho)")
    print(f"novos em julho: {novos[0]:,} veículos, R$ {(novos[1] or 0)/1e9:,.1f} bi")
    print(f"ausentes que aparecem na tabela pl BRUTA de julho: {aus_no_bruto} "
          f"(0 = ausência é da fonte, não do dedup do painel)")
    print(f"same-store (informaram nos 2 meses, n={same[0]:,}): "
          f"R$ {same[2]/1e9:,.1f} bi -> R$ {same[1]/1e9:,.1f} bi "
          f"({same[1]/same[2]-1:+.2%})")
    print(f"\natrito normal (mediana de sumiços mês a mês, 2024-2026): "
          f"{med_sumidos:,.0f} veículos ({med_pl_sumido:.2%} do PL); "
          f"julho: {len(ausentes)/med_sumidos:.1f}x")
    print("\nhistórico de sumiços (últimos 8 meses):")
    print(hist.tail(8)[["mes", "n_ant", "n_mes", "n_sumidos", "pct_sumidos",
                        "pct_pl_sumido"]].to_string(index=False))
    print("\nadministradores com maior PL ausente:")
    print(top_admin.assign(
        nome_admin=lambda d: d.nome_admin.str[:42],
        pl_ausente_bi=lambda d: (d.pl_ausente / 1e9).round(2),
        pct_pl=lambda d: (d.pct_pl_ausente * 100).round(1))[
        ["nome_admin", "n_ausentes", "n_veiculos_jun", "pl_ausente_bi", "pct_pl"]]
        .to_string(index=False))
    print(f"HHI do PL ausente por administrador: {hhi_ausentes:.3f} "
          f"(top-1 = {top_admin.pl_ausente.iloc[0]/ausentes.VL_PL.sum():.1%}, "
          f"top-5 = {top_admin.pl_ausente.sum()/ausentes.VL_PL.sum():.1%})")
    print("\nsituação cadastral dos ausentes:")
    print(sit.assign(pl_bi=lambda d: (d.pl / 1e9).round(2))[
        ["situacao", "n", "pl_bi"]].to_string(index=False))
    print("\nmaiores veículos ausentes:")
    print(ausentes.head(10).assign(
        DENOM_SOCIAL=lambda d: d.DENOM_SOCIAL.str[:46],
        pl_bi=lambda d: (d.VL_PL / 1e9).round(2),
        ADMIN=lambda d: d.ADMIN.str[:26])[
        ["DENOM_SOCIAL", "pl_bi", "ADMIN", "situacao_registro"]].to_string(index=False))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
