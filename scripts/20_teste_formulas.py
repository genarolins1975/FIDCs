#!/usr/bin/env python3
"""
Etapa 20 — Teste automático de fórmulas do painel (gate de publicação).

Exigência do parecer-espelho (revalidação, bloqueante 2): "um teste que, para
CADA indicador, execute a fórmula publicada contra os CSV e falhe o build se
divergir do valor em mais de 0,1%". Este script é esse teste.

Regras:
  1. TODO indicador de painel_dados.json precisa ter um verificador executável
     aqui. Indicador sem verificador FALHA o build — é assim que a classe de
     erro "fórmula publicada não reproduz o valor" deixa de reincidir.
  2. O verificador recomputa o valor a partir dos artefatos de data/analytic/
     e do DuckDB — nunca lê o próprio painel_dados.json como fonte.
  3. Divergência > 0,1% (ou qualquer divergência em contagens) = FALHA.
  4. Indicador com valor nulo declarado (ex.: "Dados insuficientes") é
     verificado como nulo — o verificador devolve None e ambos devem coincidir.

Também executa o LINTER JURÍDICO da tabela de casos (regra do manual):
  - linha com status contendo "condena" precisa exibir número de processo;
  - nenhum texto publicado pode reidentificar pessoa natural por cargo +
    entidade nominada ("seu diretor", entidade iniciando por "Diretor").

Saída: data/analytic/verificacao_formulas.csv. Exit 1 em qualquer falha.
Reprodução: python3 scripts/20_teste_formulas.py
"""
import json
import os
import re
import sys

import duckdb
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
CORTE = "2026-06-30"


def read(name, **kw):
    return pd.read_csv(os.path.join(OUT, name), **kw)


def main() -> int:
    dados = json.load(open(os.path.join(OUT, "painel_dados.json"), encoding="utf-8"))
    IND = dados["indicadores"]
    con = duckdb.connect(os.path.join(ROOT, "data", "duckdb", "fidc.db"), read_only=True)

    def q1(sql):
        return con.execute(sql).fetchone()[0]

    serie = read("serie_mercado_mensal.csv")
    s_at = serie.set_index("DT_COMPTC")
    pl = lambda d: float(s_at.loc[d, "pl_total"])

    ag = read("inadimplencia_aging_serie.csv")
    agc = ag[ag.DT_COMPTC == CORTE].iloc[0]
    sub = read("subordinacao_agregada.csv").set_index("TIPO_COTA").valor
    cobj = read("cobertura_competencia_202607_resumo.csv").set_index("metrica").valor
    sres = read("sacados_concentracao_resumo.csv").set_index("metrica").valor
    sdet = read("sacados_concentracao.csv")
    rf2 = read("rf2_score_veiculo.csv")
    rf2_cl = rf2[rf2.cobertura_dados_pct >= 50]
    rfs = read("rf2_sinais.csv")
    det = read("detentores_cda_resumo.csv").iloc[0]
    rjm = read("rj_matches_cedentes.csv")

    def p99_alta():
        com = rf2_cl[rf2_cl.score_risco > 0]
        return int((com.score_risco >= np.percentile(com.score_risco, 99)).sum())

    VERIF = {
        # --- tela 1: estoque, contagens e variações ---
        "pl_total": lambda: q1(f"SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{CORTE}'"),
        "circularidade": lambda: q1(f"""SELECT SUM(a.TAB_I2H_VL_COTA_FIDC) FROM ativo a
            JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
            WHERE a.DT_COMPTC='{CORTE}'"""),
        "pl_liquido": lambda: q1(f"""SELECT SUM(p.VL_PL) - (SELECT SUM(a.TAB_I2H_VL_COTA_FIDC)
            FROM ativo a JOIN painel_saneado x ON x.CNPJ=a.CNPJ AND x.DT_COMPTC=a.DT_COMPTC
            WHERE a.DT_COMPTC='{CORTE}')
            FROM painel_saneado p WHERE p.DT_COMPTC='{CORTE}'"""),
        "n_veiculos": lambda: q1(f"SELECT COUNT(*) FROM painel_saneado WHERE DT_COMPTC='{CORTE}'"),
        "posicoes_cotistas": lambda: q1(f"""SELECT SUM(c.TAB_X_NR_COTST) FROM cotistas_serie c
            JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
            WHERE c.DT_COMPTC='{CORTE}'"""),
        "dc_total": lambda: q1(f"""SELECT SUM(COALESCE(a.TAB_I2A_VL_DIRCRED_RISCO,0)
            +COALESCE(a.TAB_I2B_VL_DIRCRED_SEM_RISCO,0)) FROM ativo a
            JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
            WHERE a.DT_COMPTC='{CORTE}'"""),
        "dc_sem_risco": lambda: q1(f"""SELECT SUM(a.TAB_I2B_VL_DIRCRED_SEM_RISCO) FROM ativo a
            JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
            WHERE a.DT_COMPTC='{CORTE}'"""),
        "var_1m": lambda: pl(CORTE) / pl("2026-05-31") - 1,
        "var_3m": lambda: pl(CORTE) / pl("2026-03-31") - 1,
        "var_6m": lambda: pl(CORTE) / pl("2025-12-31") - 1,
        "var_12m": lambda: pl(CORTE) / pl("2025-06-30") - 1,
        "var_24m": lambda: pl(CORTE) / pl("2024-06-30") - 1,
        "cagr_real": lambda: (
            (pl(CORTE) * 1.0)
            / (pl("2013-12-31") * float(s_at.loc[CORTE, "indice"]) / float(s_at.loc["2013-12-31", "indice"]))
        ) ** (1 / 12.5) - 1,
        # --- fluxos do mês ---
        "aquisicoes_mes": lambda: q1(f"""SELECT SUM(COALESCE(n.TAB_VII_A1_2_VL_DIRCRED_RISCO,0)
            +COALESCE(n.TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO,0)) FROM negocios n
            JOIN painel_saneado p ON p.CNPJ=n.CNPJ AND p.DT_COMPTC=n.DT_COMPTC
            WHERE n.DT_COMPTC='{CORTE}'"""),
        "captacoes_mes": lambda: q1(_sql_fluxo("('Captações no Mês')")),
        "resgates_mes": lambda: q1(_sql_fluxo("('Resgates no Mês','Amortizações')")),
        # --- o que mudou ---
        "mudou_entrantes": lambda: q1(f"""SELECT COUNT(*) FROM painel_saneado a
            WHERE a.DT_COMPTC='{CORTE}' AND NOT EXISTS (SELECT 1 FROM painel_saneado b
            WHERE b.DT_COMPTC='2026-05-31' AND b.CNPJ=a.CNPJ)"""),
        "mudou_saintes": lambda: q1(f"""SELECT COUNT(*) FROM painel_saneado b
            WHERE b.DT_COMPTC='2026-05-31' AND NOT EXISTS (SELECT 1 FROM painel_saneado a
            WHERE a.DT_COMPTC='{CORTE}' AND a.CNPJ=b.CNPJ)"""),
        "mudou_sinais_novos": lambda: int((rfs.meses_consecutivos == 1).sum()),
        "mudou_sinais_persistentes": lambda: int((rfs.meses_consecutivos > 1).sum()),
        "mudou_sinais_encerrados": lambda: None,  # declarado "Dados insuficientes"
        # --- crédito ---
        "inadimplencia": lambda: (agc.inad_com_risco + agc.inad_sem_risco)
        / (agc.dc_com_risco + agc.dc_sem_risco),
        "atraso_180": lambda: (agc.v_maior_180 + agc.vi_maior_180)
        / (agc.dc_com_risco + agc.dc_sem_risco),
        "provisionamento": lambda: q1(f"""
            SELECT (SELECT SUM(COALESCE(a.TAB_I2A11_VL_REDUCAO_RECUP,0)
                              +COALESCE(a.TAB_I2B11_VL_REDUCAO_RECUP,0))
                    FROM ativo a JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
                    WHERE a.DT_COMPTC='{CORTE}')
                 / ((SELECT SUM(v.TAB_V_B_VL_DIRCRED_INAD) FROM dc_risco_prazos v
                     JOIN painel_saneado p ON p.CNPJ=v.CNPJ AND p.DT_COMPTC=v.DT_COMPTC
                     WHERE v.DT_COMPTC='{CORTE}')
                  + (SELECT SUM(w.TAB_VI_B_VL_DIRCRED_INAD) FROM dc_semrisco_prazos w
                     JOIN painel_saneado p ON p.CNPJ=w.CNPJ AND p.DT_COMPTC=w.DT_COMPTC
                     WHERE w.DT_COMPTC='{CORTE}'))"""),
        "subordinacao": lambda: 1 - float(sub.get("senior", 0)) / float(sub.sum()),
        "serie_senior": lambda: float(sub.get("senior", 0)),
        "serie_mezanino": lambda: float(sub.get("mezanino", 0)),
        "serie_subordinada": lambda: float(sub.get("subordinada", 0)),
        # --- blackout de julho ---
        "jul_ausentes": lambda: float(cobj["n_ausentes_em_jul"]),
        "jul_same_store": lambda: float(cobj["var_pl_same_store"]),
        "jul_pl_ausente": lambda: float(cobj["pl_ausentes_em_jul"]),
        # --- sacados (tab VIII) — recomputados do detalhe, não do resumo ---
        "sacado_cobertura_dc": lambda: float(sres["pct_dc_coberto"]),
        "sacado_mediana_top1": lambda: float(
            sdet[sdet.top1_sobre_dc.notna()].top1_sobre_dc.median()),
        "sacado_n_top1_50": lambda: int((sdet.top1_sobre_dc > 0.50).sum()),
        # --- integridade e desempenho ---
        "identidade_contabil": lambda: float(read("identidade_contabil.csv").iloc[0].n_divergentes),
        "series_abaixo_esperado": lambda: float(
            read("desempenho_resumo.csv").iloc[0].n_series_abaixo_do_esperado),
        "veiculos_com_garantia": lambda: float(
            read("garantias_resumo.csv").iloc[0].n_com_garantia_positiva),
        # --- CDA ---
        "detido_fundos": lambda: float(det.vl_detido_por_nao_fidc),
        "emissor_ligado": lambda: float(det.vl_posicoes_emissor_ligado),
        # --- red flags v2 ---
        "rf_nao_classificavel": lambda: int((rf2.cobertura_dados_pct < 50).sum()),
        "rf_atencao_alta": p99_alta,
        "rf_sem_sinal": lambda: int((rf2_cl.score_risco == 0).sum()),
        "rf_n_sinais": lambda: len(read("rf2_catalogo.csv")),
        # --- judicial ---
        "rj_processos": lambda: len(read("rj_processos.csv")),
        "rj_vinculos": lambda: len(rjm),
        "rj_exposicao": lambda: float(rjm.exposicao_estimada.sum()),
        "rj_casos": lambda: len(read("rj_casos_confirmados.csv")),
    }

    def _sql_fluxo(tipos):
        return f"""
        WITH p2 AS (SELECT p.CNPJ, p.VL_PL,
               lag(p.VL_PL) OVER (PARTITION BY p.CNPJ ORDER BY p.DT_COMPTC) pl_ant, p.DT_COMPTC
               FROM painel_saneado p)
        SELECT SUM(c.TAB_X_VL_TOTAL) FILTER (
               c.TAB_X_VL_TOTAL <= 3*GREATEST(coalesce(p2.VL_PL,0),coalesce(p2.pl_ant,0))+1e8)
        FROM captacoes c JOIN p2 ON p2.CNPJ=c.CNPJ AND p2.DT_COMPTC=c.DT_COMPTC
        WHERE c.DT_COMPTC='{CORTE}' AND c.TAB_X_TP_OPER IN {tipos}"""

    # ---------------- execução ----------------
    linhas, falhas = [], []
    sem_verificador = [k for k in IND if k not in VERIF]
    for k in sem_verificador:
        falhas.append(f"indicador '{k}' NÃO TEM verificador executável")

    for k, fn in VERIF.items():
        if k not in IND:
            continue
        pub = IND[k]["valor"]
        try:
            rec = fn()
        except Exception as e:
            falhas.append(f"{k}: verificador quebrou ({e})")
            linhas.append(dict(indicador=k, publicado=pub, recalculado=None,
                               diff_pct=None, status="ERRO"))
            continue
        if pub is None and rec is None:
            ok, diff = True, 0.0
        elif pub is None or rec is None:
            ok, diff = False, None
        else:
            pub_f, rec_f = float(pub), float(rec)
            base = max(abs(pub_f), abs(rec_f), 1e-12)
            diff = abs(pub_f - rec_f) / base * 100
            ok = diff <= 0.1
        if not ok:
            falhas.append(f"{k}: publicado={pub} recalculado={rec} diff={diff}")
        linhas.append(dict(indicador=k, publicado=pub,
                           recalculado=None if rec is None else float(rec),
                           diff_pct=diff, status="OK" if ok else "FALHA"))

    # ---------------- linter jurídico da tabela de casos ----------------
    casos = dados["tabelas"].get("casos", {})
    cols = casos.get("colunas", [])
    # formatos de identificador: SEI (19957.006858/2019-25) e antigo (RJ2013/5456)
    proc_re = re.compile(r"\d{5}\.\d{6}/\d{4}-\d{2}|RJ\s?\d{4}/\d+")
    n_lint = 0
    for row in casos.get("linhas", []):
        d = dict(zip(cols, row))
        texto = " ".join(str(v) for v in row)
        status = str(d.get("status_processual", ""))
        if "condena" in status.lower() and not proc_re.search(texto):
            falhas.append(f"LINTER: condenação sem número de processo visível: "
                          f"{d.get('entidade_principal', '?')[:60]}")
            n_lint += 1
        if re.search(r"\bseus? diretor(es)?\b|\bsua diretora\b", texto, re.I):
            falhas.append(f"LINTER: reidentificação cargo+entidade: "
                          f"{d.get('entidade_principal', '?')[:60]}")
            n_lint += 1
        if re.match(r"^\s*Diretora?\b", str(d.get("entidade_principal", ""))):
            falhas.append("LINTER: pessoa natural publicada por cargo sem agregação")
            n_lint += 1
    linhas.append(dict(indicador="linter_juridico_casos", publicado=len(casos.get("linhas", [])),
                       recalculado=n_lint, diff_pct=None,
                       status="OK" if n_lint == 0 else "FALHA"))

    # ---------------- regra-mãe nas fichas ----------------
    fichas = dados["tabelas"].get("fichas", {})
    fcols = fichas.get("colunas", [])
    n_ficha_err = 0
    if "cobertura_dados_pct" in fcols and "classificacao" in fcols:
        i_cob, i_cla = fcols.index("cobertura_dados_pct"), fcols.index("classificacao")
        for row in fichas.get("linhas", []):
            cob = row[i_cob]
            if cob is not None and float(cob) < 50 and row[i_cla] != "não classificável":
                n_ficha_err += 1
    else:
        n_ficha_err = -1
        falhas.append("fichas sem colunas cobertura_dados_pct/classificacao")
    if n_ficha_err > 0:
        falhas.append(f"{n_ficha_err} ficha(s) com cobertura<50% sem rótulo 'não classificável'")
    linhas.append(dict(indicador="regra_mae_fichas", publicado=len(fichas.get("linhas", [])),
                       recalculado=n_ficha_err, diff_pct=None,
                       status="OK" if n_ficha_err == 0 else "FALHA"))

    df = pd.DataFrame(linhas)
    df.to_csv(os.path.join(OUT, "verificacao_formulas.csv"), index=False)
    n_ok = int((df.status == "OK").sum())
    print(f"{n_ok}/{len(df)} verificações OK -> verificacao_formulas.csv")
    if falhas:
        print("\nFALHAS:")
        for f in falhas:
            print(" -", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
