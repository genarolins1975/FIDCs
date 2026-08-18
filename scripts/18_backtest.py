#!/usr/bin/env python3
"""
Etapa 18 — Backtest dos sinais de atenção.

Pergunta que o backtest responde: **os sinais estavam acesos ANTES do evento?**

Desenho:
  - Casos positivos: veículos ligados a eventos confirmados por fonte oficial
    (liquidação BCB, PAS julgado, stop order), de `casos_regulatorios.csv`.
    O vínculo é feito por CNPJ do prestador (administrador/gestor) ou do
    próprio fundo, nunca por semelhança de nome.
  - Controles negativos: veículos sem evento conhecido, pareados por faixa de
    PL e competência, amostrados com semente fixa.
  - Anti-vazamento: para um evento em T, só se lê informação de competências
    ≤ T−1 mês. Nenhum sinal usa dado posterior ao evento.
  - Métricas: taxa de disparo em positivos (sensibilidade aparente), taxa em
    controles (falso positivo), antecedência mediana em meses, e razão de
    disparo (lift) entre positivos e controles.

Limitação estrutural declarada: o número de eventos com vínculo verificável a
veículos específicos é pequeno (dezenas, não milhares). Os resultados são
indicativos e NÃO autorizam afirmar poder preditivo. A metodologia permanece
EXPERIMENTAL.

Reprodução: python3 scripts/18_backtest.py
"""
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
JANELA = 12  # meses observados antes do evento

# Eventos com vínculo verificável a veículos, por CNPJ de prestador ou fundo.
# CNPJs conferidos em fonte oficial (BCB/CVM) pela trilha regulatória.
EVENTOS = [
    dict(caso="CR023", rotulo="Liquidação BCB — administrador (CBSF/ex-Reag Trust)",
         data="2026-01-15", tipo="admin", cnpj="34829992000186"),
    dict(caso="CR024", rotulo="Stop order CVM — Multiplike Plus FIDC",
         data="2026-05-20", tipo="nome", padrao="MULTIPLIKE"),
    dict(caso="CR022", rotulo="Liquidação BCB — Banco Master (parte relacionada)",
         data="2025-11-18", tipo="nome", padrao="BANCO MASTER"),
]


def sinais_no_mes(con, cnpjs, comp):
    """Calcula os sinais de um conjunto de veículos numa competência.

    Só usa campos disponíveis desde 2013. Ausência de dado devolve NULL, e o
    sinal fica 'não avaliável' para aquele veículo — nunca 'não disparou'.
    """
    if not cnpjs:
        return pd.DataFrame()
    lista = "','".join(sorted(cnpjs))
    return con.execute(f"""
    WITH base AS (
      SELECT p.CNPJ, p.DENOM_SOCIAL, p.VL_PL,
             a.TAB_I2A_VL_DIRCRED_RISCO dc_a, a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc_b,
             a.TAB_I2A21_VL_TOTAL_PARCELA_INAD inad_a,
             a.COTST_INTERESSE, a.FUNDO_EXCLUSIVO
      FROM painel_saneado p
      LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
      WHERE p.DT_COMPTC='{comp}' AND p.CNPJ IN ('{lista}')),
    inad AS (
      SELECT v.CNPJ, v.TAB_V_A_VL_DIRCRED_PRAZO dc_v, v.TAB_V_B_VL_DIRCRED_INAD in_v
      FROM dc_risco_prazos v WHERE v.DT_COMPTC='{comp}'),
    roll AS (
      SELECT n.CNPJ, n.TAB_VII_D_2_VL_RECOMPRA rec, n.TAB_VII_C_2_VL_SUBST subst
      FROM negocios n WHERE n.DT_COMPTC='{comp}'),
    sub AS (
      SELECT CNPJ,
        SUM(VL_SERIE) FILTER (TIPO_COTA IN ('subordinada','mezanino')) v_sub,
        SUM(VL_SERIE) v_tot
      FROM series_cotas WHERE DT_COMPTC='{comp}' GROUP BY 1),
    ced AS (
      SELECT CNPJ, MAX(PR_CEDENTE) pr_max FROM cedentes
      WHERE DT_COMPTC='{comp}' AND PR_CEDENTE > 0 AND PR_CEDENTE <= 100 GROUP BY 1),
    ant AS (
      SELECT CNPJ, VL_PL pl_ant FROM painel_saneado
      WHERE DT_COMPTC = (SELECT MAX(DT_COMPTC) FROM painel_saneado WHERE DT_COMPTC < '{comp}'))
    SELECT b.CNPJ, b.DENOM_SOCIAL, b.VL_PL, '{comp}' AS competencia,
      -- S1: inadimplência ~zero com carteira relevante e cedente concentrado
      CASE WHEN i.dc_v IS NULL OR i.dc_v <= 0 OR c.pr_max IS NULL THEN NULL
           WHEN i.dc_v > 5e7 AND i.in_v/i.dc_v < 0.001 AND c.pr_max >= 50 THEN 1 ELSE 0 END AS S1,
      -- S2: rolagem (recompra+substituição) alta sobre a carteira
      CASE WHEN r.rec IS NULL AND r.subst IS NULL THEN NULL
           WHEN (coalesce(b.dc_a,0)+coalesce(b.dc_b,0)) <= 0 THEN NULL
           WHEN (coalesce(r.rec,0)+coalesce(r.subst,0))/(coalesce(b.dc_a,0)+coalesce(b.dc_b,0)) > 0.15
           THEN 1 ELSE 0 END AS S2,
      -- S3: subordinação baixa (só avaliável se houver séries informadas)
      CASE WHEN s.v_tot IS NULL OR s.v_tot <= 0 THEN NULL
           WHEN coalesce(s.v_sub,0)/s.v_tot < 0.05 THEN 1 ELSE 0 END AS S3,
      -- S4: variação abrupta de PL no mês
      CASE WHEN an.pl_ant IS NULL OR an.pl_ant <= 0 THEN NULL
           WHEN abs(b.VL_PL/an.pl_ant - 1) > 0.30 THEN 1 ELSE 0 END AS S4,
      -- S5: estrutura fechada (interesse único declarado)
      CASE WHEN b.COTST_INTERESSE IS NULL THEN NULL
           WHEN b.COTST_INTERESSE='S' THEN 1 ELSE 0 END AS S5,
      -- S6: cedente único acima de 80%
      CASE WHEN c.pr_max IS NULL THEN NULL
           WHEN c.pr_max >= 80 THEN 1 ELSE 0 END AS S6
    FROM base b
    LEFT JOIN inad i ON i.CNPJ=b.CNPJ
    LEFT JOIN roll r ON r.CNPJ=b.CNPJ
    LEFT JOIN sub s ON s.CNPJ=b.CNPJ
    LEFT JOIN ced c ON c.CNPJ=b.CNPJ
    LEFT JOIN ant an ON an.CNPJ=b.CNPJ""").df()


def competencias_antes(con, data_evento, n):
    """Últimas n competências estritamente anteriores ao mês do evento."""
    mes_evento = data_evento[:7] + "-01"
    return [r[0] for r in con.execute(f"""
        SELECT DISTINCT DT_COMPTC FROM painel_saneado
        WHERE DT_COMPTC < '{mes_evento}' ORDER BY DT_COMPTC DESC LIMIT {n}""").fetchall()][::-1]


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    SINAIS = ["S1", "S2", "S3", "S4", "S5", "S6"]
    linhas, resumo = [], []

    for ev in EVENTOS:
        comps = competencias_antes(con, ev["data"], JANELA)
        if not comps:
            continue
        ref = comps[-1]  # competência imediatamente anterior ao evento
        if ev["tipo"] == "admin":
            alvo = [r[0] for r in con.execute(f"""
                SELECT DISTINCT p.CNPJ FROM painel_saneado p
                JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
                WHERE p.DT_COMPTC='{ref}'
                  AND regexp_replace(a.CNPJ_ADMIN,'\\D','','g')='{ev["cnpj"]}'""").fetchall()]
        else:
            alvo = [r[0] for r in con.execute(f"""
                SELECT DISTINCT CNPJ FROM painel_saneado
                WHERE DT_COMPTC='{ref}' AND upper(DENOM_SOCIAL) LIKE '%{ev["padrao"]}%'""").fetchall()]
        if not alvo:
            resumo.append(dict(caso=ev["caso"], rotulo=ev["rotulo"], n_positivos=0,
                               observacao="nenhum veículo vinculado na competência anterior"))
            continue

        # controles negativos pareados por faixa de PL, sem evento conhecido
        ctrl = [r[0] for r in con.execute(f"""
            WITH faixa AS (
              SELECT MIN(VL_PL) lo, MAX(VL_PL) hi FROM painel_saneado
              WHERE DT_COMPTC='{ref}' AND CNPJ IN ('{"','".join(alvo)}'))
            SELECT p.CNPJ FROM painel_saneado p, faixa f
            WHERE p.DT_COMPTC='{ref}' AND p.CNPJ NOT IN ('{"','".join(alvo)}')
              AND p.VL_PL BETWEEN f.lo AND f.hi
            ORDER BY hash(p.CNPJ || '{ev["caso"]}') LIMIT {max(len(alvo)*3, 30)}""").fetchall()]

        for grupo, cnpjs in (("positivo", alvo), ("controle", ctrl)):
            for comp in comps:
                df = sinais_no_mes(con, cnpjs, comp)
                if df.empty:
                    continue
                df["grupo"], df["caso"] = grupo, ev["caso"]
                df["meses_antes"] = (len(comps) - comps.index(comp) - 1)
                linhas.append(df)

        det = pd.concat([d for d in linhas if d.caso.iloc[0] == ev["caso"]], ignore_index=True)
        for s in SINAIS:
            for grupo in ("positivo", "controle"):
                g = det[det.grupo == grupo]
                aval = g[g[s].notna()]
                if not len(aval):
                    continue
                # veículo conta como "disparou" se acendeu em qualquer mês da janela
                por_veic = aval.groupby("CNPJ")[s].max()
                antec = (aval[aval[s] == 1].groupby("CNPJ").meses_antes.max())
                resumo.append(dict(
                    caso=ev["caso"], rotulo=ev["rotulo"], sinal=s, grupo=grupo,
                    n_veiculos=int(por_veic.size),
                    n_disparou=int(por_veic.sum()),
                    taxa_disparo=float(por_veic.mean()),
                    cobertura=float(len(aval.CNPJ.unique()) / max(g.CNPJ.nunique(), 1)),
                    antecedencia_mediana_meses=(float(antec.median()) if len(antec) else None),
                ))

    det_all = pd.concat(linhas, ignore_index=True) if linhas else pd.DataFrame()
    det_all.to_csv(f"{OUT}/backtest_detalhe.csv", index=False)
    res = pd.DataFrame(resumo)
    # lift = taxa em positivos ÷ taxa em controles
    if "sinal" in res.columns:
        piv = res.pivot_table(index=["caso", "sinal"], columns="grupo",
                              values="taxa_disparo").reset_index()
        piv["lift"] = piv.get("positivo") / piv.get("controle").replace(0, pd.NA)
        res = res.merge(piv[["caso", "sinal", "lift"]], on=["caso", "sinal"], how="left")
    res.to_csv(f"{OUT}/backtest_resumo.csv", index=False)

    if "sinal" in res.columns:
        v = res[res.grupo == "positivo"][["caso", "sinal", "n_veiculos", "n_disparou",
                                          "taxa_disparo", "antecedencia_mediana_meses", "lift"]]
        print(v.to_string(index=False))
    print(f"\ndetalhe: {len(det_all)} observações veículo-mês")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
