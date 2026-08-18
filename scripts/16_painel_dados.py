#!/usr/bin/env python3
"""
Etapa 16 — Compilador de dados do painel v2.

Lê os artefatos de data/analytic/ e emite UM único JSON
(data/analytic/painel_dados.json) contendo:

  - indicadores: cada número exibível, com valor sem arredondamento, unidade,
    fórmula, fonte, tabela/campo, data-base, cobertura, status
    (observado/calculado/estimado/inferido) e nível de confiança;
  - tabelas: os rankings e listas, já ordenados, com as colunas de cobertura;
  - meta: datas, hashes do manifesto e contagens de controle.

Objetivo: eliminar o achado crítico nº 4 da auditoria (números escritos à mão
no HTML). O gerador do painel NÃO pode conter literal numérico — tudo vem
deste JSON, e cada número carrega sua própria evidência.

Reprodução: python3 scripts/16_painel_dados.py
"""
import hashlib
import json
import os
import sys

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DEST = os.path.join(OUT, "painel_dados.json")
CORTE = "2026-06-30"
EXTRACAO = "2026-08-18"

IND = {}
TAB = {}


def read(name, **kw):
    p = os.path.join(OUT, name)
    return pd.read_csv(p, **kw) if os.path.exists(p) else None


def ind(key, valor, unidade, rotulo, formula, fonte, campo, status,
        confianca, cobertura=None, obs=None, claim=None):
    """Registra um indicador com sua trilha de evidência completa."""
    IND[key] = dict(valor=None if valor is None or pd.isna(valor) else float(valor),
                    unidade=unidade, rotulo=rotulo, formula=formula, fonte=fonte,
                    campo=campo, status=status, confianca=confianca,
                    cobertura=cobertura, obs=obs, claim=claim,
                    data_base=CORTE, data_extracao=EXTRACAO)


# Unidade declarada de cada coluna conhecida. Sem heurística de escala: o
# renderizador NUNCA adivinha se 0,9 é 0,9% ou 90% (achado do espelho).
UNIDADES = {
    # moeda
    "valor": "brl", "VL_PL": "brl", "vl_cotas_fidc": "brl", "exposicao_estimada": "brl",
    "pl_identificado": "brl", "materialidade_soma_rs": "brl", "materialidade_max_rs": "brl",
    "dc": "brl", "dc_sem_risco": "brl", "vl": "brl",
    # fração 0-1
    "participacao": "fracao", "pct_maior_sacado": "fracao", "pct_top5": "fracao",
    "pct_top10": "fracao", "share_top1": "fracao", "share_top5": "fracao",
    "cobertura_sobre_pl_mercado": "fracao", "subord": "fracao", "inad_pct": "fracao",
    # percentual já em 0-100
    "cobertura_pct": "pct100", "cobertura_dados_pct": "pct100",
    "cobertura_universo_pct": "pct100", "pct_maior_cedente": "pct100",
    # índice adimensional
    "hhi": "indice", "score_risco": "indice", "persistencia_media_meses": "indice",
    # inteiros
    "n_veiculos": "int", "n_entidades": "int", "n_fundos": "int", "n_sinalizados": "int",
    "n_fidcs_investidos": "int", "n_ligadas": "int", "lente": "int", "n_criticos": "int",
    "n_altos": "int", "posicoes_cotistas": "int", "n_cedentes_declarados": "int",
    "n_cot": "int", "n_meses": "int", "n_avaliaveis": "int", "n_disparos": "int",
    "n_veiculos_distintos": "int",
}


def tabela(key, df, cols, rotulo, fonte, campo, nota=None, limite=25):
    if df is None or not len(df):
        TAB[key] = dict(rotulo=rotulo, fonte=fonte, campo=campo, nota=nota,
                        colunas=[], unidades=[], linhas=[])
        return
    d = df[[c for c in cols if c in df.columns]].head(limite)
    # CNPJ e documentos são identificadores: string sempre, nunca número
    for c in d.columns:
        if any(k in c.lower() for k in ("cnpj", "doc_", "cpf")):
            d[c] = d[c].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(14)
    TAB[key] = dict(rotulo=rotulo, fonte=fonte, campo=campo, nota=nota,
                    colunas=list(d.columns),
                    unidades=[UNIDADES.get(c, "auto") for c in d.columns],
                    linhas=json.loads(d.to_json(orient="values")))


def main() -> int:
    serie = read("serie_mercado_mensal.csv")
    c = serie[serie.DT_COMPTC == CORTE].iloc[0]
    jul = serie[serie.DT_COMPTC == "2026-07-31"]
    h12 = serie[serie.DT_COMPTC == "2025-06-30"].iloc[0]
    h24 = serie[serie.DT_COMPTC == "2024-06-30"].iloc[0]
    h13 = serie[serie.DT_COMPTC == "2013-12-31"].iloc[0]

    # ---------------- Tela 1: visão geral ----------------
    ind("pl_total", c.pl_total, "R$", "Patrimônio líquido do mercado",
        "Σ VL_PL sobre o painel canônico deduplicado (fundo × classe)",
        "CVM — Informe Mensal FIDC", "tab IV / TAB_IV_A_VL_PL", "observado",
        "Fato confirmado por fonte primária", 100.0,
        "Soma bruta: inclui cotas de FIDC detidas por outros FIDCs.", "C001")
    ind("pl_liquido", c.pl_liquido_circular, "R$", "PL líquido de circularidade",
        "PL total − Σ TAB_I2H (cotas de FIDC detidas dentro do universo)",
        "CVM — Informe Mensal FIDC", "tab IV e tab I / TAB_I2H", "calculado",
        "Fato confirmado por fonte primária", 100.0,
        "TAB_I2I (cotas de FIDC-NP) está 100% em branco no layout; a medida usa I2H.", "C004")
    ind("circularidade", c.cotas_fidc_detidas, "R$", "Cotas de FIDC dentro do universo",
        "Σ TAB_I2H_VL_COTA_FIDC", "CVM — Informe Mensal FIDC", "tab I / TAB_I2H",
        "observado", "Fato confirmado por fonte primária", 100.0, None, "C003")
    ind("n_veiculos", c.n_veiculos, "un", "Veículos informantes",
        "COUNT(*) do painel canônico", "CVM — Informe Mensal FIDC", "tab IV",
        "observado", "Fato confirmado por fonte primária", 100.0,
        "Classes (RCVM 175) + fundos do regime anterior. Subclasses não são somadas.", "C002")
    ind("posicoes_cotistas", c.n_cotistas, "un", "Posições de cotistas",
        "Σ TAB_X_NR_COTST por veículo", "CVM — Informe Mensal FIDC", "tab X_1",
        "observado", "Fato confirmado por fonte primária", 100.0,
        "NÃO mede pessoas únicas: um investidor em N fundos conta N vezes.", "C007")
    ind("dc_total", (c.dc_com_risco or 0) + (c.dc_sem_risco or 0), "R$",
        "Direitos creditórios", "Σ (TAB_I2A + TAB_I2B)", "CVM — Informe Mensal FIDC",
        "tab I", "observado", "Fato confirmado por fonte primária", 100.0, None, "C008")
    ind("dc_sem_risco", c.dc_sem_risco, "R$", "DC sem transferência de risco",
        "Σ TAB_I2B_VL_DIRCRED_SEM_RISCO", "CVM — Informe Mensal FIDC", "tab I",
        "observado", "Fato confirmado por fonte primária", 100.0,
        "Risco econômico permanece no cedente: funding garantido, não venda definitiva.", "C009")
    ind("var_12m", c.pl_total / h12.pl_total - 1, "%", "Variação do PL em 12 meses",
        "PL(jun/26) / PL(jun/25) − 1", "CVM — Informe Mensal FIDC", "tab IV",
        "calculado", "Fato confirmado por fonte primária", 100.0, None, None)
    ind("var_24m", c.pl_total / h24.pl_total - 1, "%", "Variação do PL em 24 meses",
        "PL(jun/26) / PL(jun/24) − 1", "CVM — Informe Mensal FIDC", "tab IV",
        "calculado", "Fato confirmado por fonte primária", 100.0, None, None)
    ind("cagr_real", (c.pl_total_real_jun26 / h13.pl_total_real_jun26) ** (1 / 12.5) - 1,
        "%", "Crescimento real anualizado desde 2013",
        "(PL real jun/26 / PL real dez/13)^(1/12,5) − 1", "CVM + BCB/SGS 433",
        "tab IV + IPCA", "calculado", "Fato confirmado por fonte primária", 100.0,
        "Deflacionado pelo IPCA, base jun/2026.", "C006")

    # variações de curto prazo (1, 3 e 6 meses) — mesma fonte da série
    for nm, dt in (("1m", "2026-05-31"), ("3m", "2026-03-31"), ("6m", "2025-12-31")):
        hh = serie[serie.DT_COMPTC == dt]
        if len(hh):
            ind(f"var_{nm}", c.pl_total / hh.iloc[0].pl_total - 1, "%",
                f"Variação do PL em {nm.replace('m', ' mês' if nm == '1m' else ' meses')}",
                f"PL(jun/26) / PL({dt[5:7]}/{dt[2:4]}) − 1", "CVM — Informe Mensal FIDC",
                "tab IV", "calculado", "Fato confirmado por fonte primária", 100.0,
                "Variação de estoque: mistura valorização, captação e entrada/saída "
                "de informantes.", None)

    # ---------------- fluxos do mês do corte ----------------
    import duckdb as _dd0
    _con0 = _dd0.connect(os.path.join(ROOT, "data", "duckdb", "fidc.db"), read_only=True)
    aq1, aq2 = _con0.execute(f"""
        SELECT SUM(n.TAB_VII_A1_2_VL_DIRCRED_RISCO), SUM(n.TAB_VII_A2_2_VL_DIRCRED_SEM_RISCO)
        FROM negocios n JOIN painel_saneado p ON p.CNPJ=n.CNPJ AND p.DT_COMPTC=n.DT_COMPTC
        WHERE n.DT_COMPTC='{CORTE}'""").fetchone()
    ind("aquisicoes_mes", (aq1 or 0) + (aq2 or 0), "R$",
        "Direitos creditórios adquiridos no mês",
        "Σ (TAB_VII_A1_2 + TAB_VII_A2_2) na competência do corte",
        "CVM — Informe Mensal FIDC", "tab VII", "observado",
        "Fato confirmado por fonte primária", 100.0,
        "Fluxo bruto de aquisição, com e sem transferência substancial de risco.", None)
    # captações e resgates com o MESMO filtro de sanidade da série anual
    # (operação > 3×max(PL_t, PL_t−1) + R$100 mi é descartada e contada)
    flx = _con0.execute(f"""
        WITH p2 AS (
          SELECT p.CNPJ, p.VL_PL, lag(p.VL_PL) OVER (PARTITION BY p.CNPJ ORDER BY p.DT_COMPTC) pl_ant,
                 p.DT_COMPTC
          FROM painel_saneado p),
        cx AS (
          SELECT c.TAB_X_TP_OPER op, c.TAB_X_VL_TOTAL v,
                 (c.TAB_X_VL_TOTAL > 3*GREATEST(coalesce(p2.VL_PL,0),coalesce(p2.pl_ant,0))+1e8) descartada
          FROM captacoes c JOIN p2 ON p2.CNPJ=c.CNPJ AND p2.DT_COMPTC=c.DT_COMPTC
          WHERE c.DT_COMPTC='{CORTE}')
        SELECT op, SUM(v) FILTER (NOT descartada), COUNT(*) FILTER (descartada)
        FROM cx GROUP BY op""").fetchall()
    fl = {r[0]: (r[1] or 0, r[2] or 0) for r in flx}
    n_desc = sum(v[1] for v in fl.values())
    ind("captacoes_mes", fl.get("Captações no Mês", (None,))[0], "R$",
        "Captações no mês", "Σ TAB_X_VL_TOTAL (tipo 'Captações no Mês'), com filtro de sanidade",
        "CVM — Informe Mensal FIDC", "tab X_4", "observado",
        "Fato confirmado por fonte primária", None,
        f"Filtro de sanidade idêntico ao da série anual; {n_desc} operações descartadas "
        "na competência (contadas, nunca somadas).", None)
    ind("resgates_mes",
        fl.get("Resgates no Mês", (0,))[0] + fl.get("Amortizações", (0,))[0], "R$",
        "Resgates e amortizações no mês",
        "Σ TAB_X_VL_TOTAL (tipos 'Resgates no Mês' + 'Amortizações'), com filtro de sanidade",
        "CVM — Informe Mensal FIDC", "tab X_4", "observado",
        "Fato confirmado por fonte primária", None,
        "Saída efetiva de cotistas; 'Resgates Solicitados' (estoque a liquidar) fica fora.", None)

    # ---------------- o que mudou desde a última competência ----------------
    ent, sai = _con0.execute(f"""
      SELECT
       (SELECT COUNT(*) FROM painel_saneado a WHERE a.DT_COMPTC='{CORTE}'
         AND NOT EXISTS (SELECT 1 FROM painel_saneado b WHERE b.DT_COMPTC='2026-05-31' AND b.CNPJ=a.CNPJ)),
       (SELECT COUNT(*) FROM painel_saneado b WHERE b.DT_COMPTC='2026-05-31'
         AND NOT EXISTS (SELECT 1 FROM painel_saneado a WHERE a.DT_COMPTC='{CORTE}' AND a.CNPJ=b.CNPJ))
      """).fetchone()
    _con0.close()
    ind("mudou_entrantes", ent, "un", "Veículos que passaram a informar no mês",
        "CNPJs presentes em jun/26 e ausentes em mai/26 (painel canônico)",
        "CVM — Informe Mensal FIDC", "tab IV", "calculado",
        "Fato confirmado por fonte primária", 100.0,
        "Inclui veículos novos e retornos de interrupção de reporte.", None)
    ind("mudou_saintes", sai, "un", "Veículos que deixaram de informar no mês",
        "CNPJs presentes em mai/26 e ausentes em jun/26 (painel canônico)",
        "CVM — Informe Mensal FIDC", "tab IV", "calculado",
        "Fato confirmado por fonte primária", 100.0,
        "Interrupção de reporte não distingue liquidação, incorporação ou atraso "
        "de envio — o motivo não é público.", None)
    rfsx = read("rf2_sinais.csv")
    if rfsx is not None and "meses_consecutivos" in rfsx.columns:
        ind("mudou_sinais_novos", int((rfsx.meses_consecutivos == 1).sum()), "un",
            "Sinais que acenderam neste mês",
            "COUNT(sinais ativos com meses_consecutivos = 1)",
            "metodologia própria sobre informe CVM", "rf2_sinais.csv", "calculado",
            "Indicador calculado", None,
            "Primeiro mês do sinal na janela corrente — não distingue estreia "
            "absoluta de reincidência após pausa.", None)
        ind("mudou_sinais_persistentes", int((rfsx.meses_consecutivos > 1).sum()), "un",
            "Sinais persistentes (2+ meses consecutivos)",
            "COUNT(sinais ativos com meses_consecutivos > 1)",
            "metodologia própria sobre informe CVM", "rf2_sinais.csv", "calculado",
            "Indicador calculado", None, None, None)
        ind("mudou_sinais_encerrados", None, "un",
            "Sinais encerrados desde a última publicação",
            "exigiria snapshot da publicação anterior — ainda não versionado",
            "metodologia própria", "rf2_sinais.csv", "calculado",
            "Dados insuficientes", None,
            "NÃO COMPUTÁVEL nesta edição: o painel ainda não guarda snapshot entre "
            "publicações. O orquestrador passa a versionar rf2_sinais a cada execução; "
            "a partir da próxima, este número existe.", None)

    ag = read("inadimplencia_aging_serie.csv")
    r = ag[ag.DT_COMPTC == CORTE].iloc[0]
    dc = r.dc_com_risco + r.dc_sem_risco
    inad = r.inad_com_risco + r.inad_sem_risco
    ind("inadimplencia", inad / dc, "%", "Inadimplência (parcelas vencidas / DC)",
        "(TAB_V_B + TAB_VI_B) ÷ (TAB_V_A + TAB_VI_A)", "CVM — Informe Mensal FIDC",
        "tabs V e VI", "calculado", "Fato confirmado por fonte primária", 100.0,
        "Medida abrangente: todas as faixas de atraso.", "C016")
    ind("atraso_180", (r.v_maior_180 + r.vi_maior_180) / dc, "%",
        "Atraso acima de 180 dias", "Σ faixas B7..B10 ÷ DC", "CVM — Informe Mensal FIDC",
        "tabs V e VI", "calculado", "Fato confirmado por fonte primária", 100.0, None, "C017")

    prov = read("provisoes_reducao.csv").iloc[0]
    ind("provisionamento", prov.razao_reducao_sobre_inadimplencia, "%",
        "Atraso coberto por provisão",
        "(TAB_I2A11 + TAB_I2B11) ÷ (TAB_V_B_VL_DIRCRED_INAD + TAB_VI_B_VL_DIRCRED_INAD)",
        "CVM — Informe Mensal FIDC", "tabs I (numerador), V e VI (denominador)",
        "calculado", "Fato confirmado por fonte primária", 100.0,
        "Numerador e denominador vêm de tabelas distintas: a redução ao valor recuperável "
        "está na tab I; as parcelas inadimplentes, nas tabs V e VI.", "C027")

    sub = read("subordinacao_agregada.csv")
    tot_s = sub.valor.sum()
    sen = sub.set_index("TIPO_COTA").valor
    ind("subordinacao", 1 - float(sen.get("senior", 0)) / tot_s, "%",
        "Subordinação + mezanino", "(mezanino + subordinada) ÷ total das séries",
        "CVM — Informe Mensal FIDC", "tab X_2", "calculado",
        "Fato confirmado por fonte primária", 100.0, None, "C015")
    for k in ("senior", "mezanino", "subordinada"):
        ind(f"serie_{k}", float(sen.get(k, 0)), "R$", f"Cotas {k}",
            "Σ (quantidade × valor da cota) por tipo de série",
            "CVM — Informe Mensal FIDC", "tab X_2", "calculado",
            "Fato confirmado por fonte primária", 100.0, None, "C015")

    # ---------------- cobertura da competência (blackout de julho) ----------------
    cobj = read("cobertura_competencia_202607_resumo.csv")
    if cobj is not None:
        m = cobj.set_index("metrica").valor
        def g(k):
            try:
                return float(m.get(k))
            except (TypeError, ValueError):
                return None
        ind("jul_ausentes", g("n_ausentes_em_jul"), "un",
            "Veículos que informaram em junho e não em julho",
            "CNPJs presentes em jun/26 e ausentes em jul/26", "CVM — Informe Mensal FIDC",
            "tab IV", "calculado", "Fato confirmado por fonte primária", None,
            "Ausência verificada na tabela bruta: não é efeito das regras de dedup.", None)
        ind("jul_same_store", g("var_pl_same_store"), "%",
            "Crescimento entre veículos que informaram nos dois meses",
            "PL same-store jul/26 ÷ PL same-store jun/26 − 1", "CVM — Informe Mensal FIDC",
            "tab IV", "calculado", "Fato confirmado por fonte primária", None,
            "Mostra que a queda aparente da competência é artefato de cobertura.", None)
        ind("jul_pl_ausente", g("pl_ausentes_em_jul"), "R$", "PL que deixou de ser informado em julho",
            "Σ PL(jun/26) dos CNPJs ausentes em jul/26", "CVM — Informe Mensal FIDC",
            "tab IV", "calculado", "Fato confirmado por fonte primária", None,
            "Concentrado por administrador; ver tabela de ausências.", None)

    # ---------------- sacados (tab VIII) ----------------
    sres = read("sacados_concentracao_resumo.csv")
    if sres is not None:
        sm = sres.set_index("metrica").valor
        def gs(k):
            try:
                return float(sm.get(k))
            except (TypeError, ValueError):
                return None
        ind("sacado_cobertura_dc", gs("pct_dc_coberto"), "%",
            "Cobertura da tabela VIII sobre o estoque de DC",
            "Σ DC dos veículos com tab VIII ÷ DC total", "CVM — Informe Mensal FIDC",
            "tab VIII", "calculado", "Fato confirmado por fonte primária", None,
            "Cobertura em queda monotônica desde jan/2025.", None)
        ind("sacado_mediana_top1", gs("top1_mediana"), "%",
            "Mediana da participação do maior devedor",
            "mediana(valor do maior sacado ÷ DC do veículo)", "CVM — Informe Mensal FIDC",
            "tab VIII", "calculado", "Fato confirmado por fonte primária", None,
            "A tabela VIII não identifica o devedor: só posição e valor.", None)
        ind("sacado_n_top1_50", gs("n_veiculos_top1_acima_50pct"), "un",
            "Veículos cujo maior devedor supera 50% da carteira",
            "contagem sobre veículos com razão definida", "CVM — Informe Mensal FIDC",
            "tab VIII", "calculado", "Fato confirmado por fonte primária", None, None, None)

    # ---------------- lentes ----------------
    lent = read("lentes_catalogo.csv")
    TAB["lentes"] = dict(
        rotulo="As nove lentes de exposição",
        fonte="CVM — informe mensal, registro e fontes complementares",
        campo="lentes_catalogo.csv", nota=None,
        colunas=["lente", "nome", "unidade_analise", "cobertura_pct", "n_entidades",
                 "o_que_NAO_significa", "limitacao"],
        linhas=json.loads(lent[["lente", "nome", "unidade_analise", "cobertura_pct",
                                "n_entidades", "o_que_NAO_significa",
                                "limitacao"]].to_json(orient="values")))

    tabela("lente1", read("lente_1_pl_sob_gestao.csv"),
           ["entidade", "valor", "n_veiculos", "participacao"],
           "PL sob gestão", "CVM — registro de fundo/classe + tab IV",
           "Gestor do registro vigente",
           "Não é capital do gestor nem exposição econômica dele.")
    tabela("lente2", read("lente_2_pl_sob_administracao.csv"),
           ["entidade", "valor", "n_veiculos", "participacao"],
           "PL sob administração fiduciária", "CVM — tab I (CNPJ_ADMIN) + tab IV",
           "CNPJ_ADMIN", "Patrimônio do fundo é segregado do administrador: mede "
           "concentração operacional, não risco de crédito.")
    tabela("lente4", read("lente_4_cedentes.csv"),
           ["razao_social", "doc_cedente", "exposicao_estimada", "n_veiculos",
            "cnae_principal"],
           "Exposição a cedente/originador", "CVM — tab I + base pública do CNPJ",
           "campos de cedente (top-9 por veículo)",
           "Estoque atribuído ≠ fluxo cedido. Piso: cobre 29,4% do estoque.")
    l5 = read("lente_5_sacados_concentracao.csv")
    n_incons = 0
    if l5 is not None:
        if "inconsistente_viii_vs_i" in l5.columns:
            n_incons = int(l5.inconsistente_viii_vs_i.fillna(False).astype(bool).sum())
            # razão > 1 não é participação: a soma dos 25 maiores excede a carteira
            # informada na tab I. Ficam fora do ranking e são contados à parte.
            l5 = l5[~l5.inconsistente_viii_vs_i.fillna(False).astype(bool)]
        l5 = l5[l5.pct_maior_sacado.notna() & (l5.VL_PL > 1e8)]
        l5 = l5.sort_values("pct_maior_sacado", ascending=False)
    tabela("lente5", l5,
           ["entidade", "VL_PL", "pct_maior_sacado", "pct_top5", "pct_top10"],
           "Concentração por devedor (tab VIII)", "CVM — tab VIII",
           "SEQUENCIAL + VALOR",
           "A tabela VIII NÃO identifica o devedor: só concentração, nunca identidade. "
           f"Excluídos {n_incons} veículos em que a soma dos 25 maiores devedores excede a "
           "carteira informada na tab I — a razão existe, mas não é interpretável como "
           "participação, e a divergência entre tabelas é publicada como achado.")
    tabela("lente8", read("lente_8_exposicao_operacional.csv"),
           ["papel", "n_entidades", "hhi", "share_top1", "share_top5",
            "cobertura_sobre_pl_mercado"],
           "Exposição operacional por papel", "CVM — informe + registro",
           "prestadores", "Concentração de prestador ≠ concentração de risco de crédito.")

    # ---------------- risco e integridade ----------------
    ident = read("identidade_contabil.csv")
    if ident is not None:
        i0 = ident.iloc[0]
        ind("identidade_contabil", i0.n_divergentes, "un",
            "Veículos que violam Ativo − Passivo = PL",
            "|TAB_I_VL_ATIVO − TAB_III_VL_PASSIVO − VL_PL| > 0,01",
            "CVM — Informe Mensal FIDC", "tabs I, III e IV", "calculado",
            "Fato confirmado por fonte primária",
            round(100.0 * i0.n_avaliaveis / c.n_veiculos, 1),
            "Teste de integridade contábil do próprio informe.", None)

    des = read("desempenho_resumo.csv")
    if des is not None:
        d0 = des.iloc[0]
        ind("series_abaixo_esperado", d0.n_series_abaixo_do_esperado, "un",
            "Séries com desempenho abaixo do esperado",
            "COUNT(desempenho real < esperado), ambos informados",
            "CVM — Informe Mensal FIDC", "tab X_6", "calculado",
            "Fato confirmado por fonte primária", float(d0.cobertura_pct),
            "Compara a promessa declarada com o realizado, por série.", None)

    gar = read("garantias_resumo.csv")
    if gar is not None:
        g0 = gar.iloc[0]
        ind("veiculos_com_garantia", g0.n_com_garantia_positiva, "un",
            "Veículos com garantia real declarada",
            "COUNT(TAB_X_VL_GARANTIA_DIRCRED > 0)", "CVM — Informe Mensal FIDC",
            "tab X_7", "observado", "Fato confirmado por fonte primária",
            float(g0.cobertura_pct),
            "Colateral formal é raro: o mercado se apoia em subordinação e coobrigação.", None)

    det = read("detentores_cda_resumo.csv")
    if det is not None:
        d1 = det.iloc[0]
        ind("detido_fundos", d1.vl_detido_por_nao_fidc, "R$",
            "Cotas de FIDC em carteiras de fundos não-FIDC",
            "Σ VL_MERC_POS_FINAL das posições em cotas de FIDC", "CVM — CDA",
            "cda_fi_BLC_2", "observado", "Fato confirmado por fonte primária", None,
            "Canal de transmissão até o investidor de varejo.", "C029")
        ind("emissor_ligado", d1.vl_posicoes_emissor_ligado, "R$",
            "Posições declaradas como emissor ligado",
            "Σ VL_MERC_POS_FINAL onde EMISSOR_LIGADO='S'", "CVM — CDA",
            "cda_fi_BLC_2 / EMISSOR_LIGADO", "observado",
            "Fato confirmado por fonte primária", None,
            "Nulo não é lido como 'não ligado'; ver valor não informado.", "C030")

    tabela("detentores", read("detentores_cda_gestores.csv"),
           ["gestor", "vl_cotas_fidc", "n_fundos"],
           "Gestores detentores de cotas de FIDC", "CVM — CDA jun/2026",
           "cda_fi_BLC_2",
           "Só a indústria de fundos: bancos, empresas e pessoas físicas ficam fora.")

    rf2s = read("rf2_score_veiculo.csv")
    rf2c = read("rf2_catalogo.csv")
    if rf2s is not None:
        vc = rf2s.classificacao.value_counts()
        ind("rf_nao_classificavel", int(vc.get("não classificável", 0)), "un",
            "Veículos não classificáveis por cobertura insuficiente",
            "COUNT(cobertura_dados_pct < 50)", "metodologia própria sobre informe CVM",
            "rf2_score_veiculo.csv", "calculado", "Indicador calculado", None,
            "Cobertura insuficiente NUNCA é lida como baixo risco.", None)
        ind("rf_atencao_alta", int(vc.get("atenção alta", 0)), "un",
            "Veículos na faixa de atenção alta",
            "score ≥ p99 da distribuição entre os veículos CLASSIFICÁVEIS "
            "(cobertura ≥ 50%) COM ao menos um sinal disparado (score > 0) — "
            "não do universo completo",
            "metodologia própria sobre informe CVM", "rf2_score_veiculo.csv",
            "calculado", "Indicador calculado", None,
            "Faixa estatística, não imputação. Fundos de NPL e distressed disparam por desenho.",
            None)
        ind("rf_sem_sinal", int(vc.get("sem sinal disparado", 0)), "un",
            "Veículos classificáveis sem nenhum sinal disparado",
            "COUNT(cobertura_dados_pct ≥ 50 E score_risco = 0)",
            "metodologia própria sobre informe CVM", "rf2_score_veiculo.csv",
            "calculado", "Indicador calculado", None,
            "Só entre CLASSIFICÁVEIS: veículo sem cobertura suficiente não entra aqui — "
            "cobertura insuficiente nunca é lida como ausência de sinal.", None)
    if rf2c is not None:
        ind("rf_n_sinais", len(rf2c), "un", "Sinais catalogados",
            "COUNT(*) do catálogo", "metodologia própria", "rf2_catalogo.csv",
            "calculado", "Indicador calculado", None,
            "Distribuídos em 8 pilares, com limiar percentílico calculado sobre o mercado.",
            None)

    rjp = read("rj_processos.csv")
    if rjp is not None:
        ind("rj_processos", len(rjp), "un",
            "Processos de recuperação judicial e falência coletados",
            "COUNT(*) da consulta ao DataJud", "DataJud/CNJ (API pública)",
            "rj_processos.csv", "observado", "Fato confirmado por fonte primária", None,
            "A API não retorna as partes: o casamento com CNPJs de cedentes é impossível "
            "por essa via e foi feito por fonte pública complementar.", None)
    rjm = read("rj_matches_cedentes.csv")
    if rjm is not None and len(rjm):
        cnpj_ok = rjm[rjm.chave_casamento.astype(str).str.contains("cnpj", case=False, na=False)] \
            if "chave_casamento" in rjm.columns else rjm
        ind("rj_vinculos", len(rjm), "un",
            "Vínculos entre cedentes e empresas em recuperação ou falência",
            "casamento por CNPJ entre cedentes do informe e marcador cadastral de RJ",
            "CVM (tab I) + base pública do CNPJ (art. 69 da Lei 11.101/2005)",
            "rj_matches_cedentes.csv", "calculado", "Fato confirmado por fonte primária",
            None, "O DataJud não retorna as partes do processo; o estado processual é lido "
            "do sufixo obrigatório no nome empresarial constante do cadastro CNPJ.", None)
        ind("rj_exposicao", float(rjm.exposicao_estimada.sum()), "R$",
            "Estoque atribuído a cedentes com recuperação ou falência",
            "Σ exposição estimada dos cedentes com marcador cadastral",
            "CVM (tab I) + base pública do CNPJ", "rj_matches_cedentes.csv",
            "estimado", "Indício forte", None,
            "Mede ORIGINAÇÃO, não perda: o recebível pode estar performando normalmente. "
            "Estar em recuperação judicial não é evidência de irregularidade.", None)

    rjc = read("rj_casos_confirmados.csv")
    if rjc is not None:
        ind("rj_casos", len(rjc), "un",
            "Empresas ligadas a FIDCs com RJ ou falência documentada",
            "casos com fonte pública citada", "fontes públicas oficiais e imprensa",
            "rj_casos_confirmados.csv", "calculado",
            "Nível de evidência declarado caso a caso", None,
            "Estar em recuperação judicial não é evidência de irregularidade.", None)

    # red flags v2 (se disponível) — senão, v1
    rf2, rfcat = rf2s, rf2c
    if rf2 is not None and rfcat is not None:
        rf2_class = rf2[rf2.classificacao != "não classificável"]
        tabela("rf_score", rf2_class.sort_values("score_risco", ascending=False),
               [c_ for c_ in ["DENOM_SOCIAL", "VL_PL", "score_risco", "classificacao",
                              "materialidade_soma_rs", "cobertura_dados_pct",
                              "persistencia_media_meses", "n_criticos", "n_altos"]
                if c_ in rf2.columns],
               "Score de risco por veículo (experimental)",
               "CVM — informe mensal", "múltiplos campos",
               "Apenas veículos CLASSIFICÁVEIS (cobertura ≥ 50%), ordenados por score. "
               "Score alto NÃO é imputação de irregularidade: fundos de crédito inadimplido, "
               "distressed e créditos judiciais disparam sinais de qualidade de ativo por "
               "desenho do mandato. Os não classificáveis ficam fora desta tabela e são "
               "contados no cartão próprio — nunca são lidos como baixo risco.")
        tabela("rf_catalogo", rfcat,
               [c_ for c_ in ["sinal_id", "pilar", "nome", "severidade", "limiar",
                              "limiar_origem", "cobertura_universo_pct",
                              "explicacoes_benignas"] if c_ in rfcat.columns],
               "Catálogo de sinais (8 pilares)", "metodologia própria",
               "docs/METODOLOGIA_RED_FLAGS.md",
               "Metodologia experimental enquanto os pesos não forem validados por backtest.",
               limite=60)

    rj = read("rj_casos_confirmados.csv")
    tabela("rj", rj,
           [c_ for c_ in ["entidade", "razao_social", "cnpj", "status_processual",
                          "papel_no_fidc", "natureza_ligacao_fidc", "data_evento",
                          "nivel_evidencia", "fonte_url"] if rj is not None and c_ in rj.columns],
           "Empresas ligadas a FIDCs em recuperação judicial ou falência",
           "DataJud/CNJ e fontes públicas", "processos judiciais",
           "Estar em recuperação judicial NÃO é evidência de irregularidade. "
           "Classificação concursal/extraconcursal depende do contrato e da data do fato gerador.")

    if rjm is not None and len(rjm):
        tabela("rj_vinculos", rjm.sort_values("exposicao_estimada", ascending=False),
               ["razao_social_cedente", "exposicao_estimada", "n_veiculos", "evento",
                "data_evento", "papel_fidc", "nivel_evidencia"],
               "Cedentes com recuperação judicial, extrajudicial ou falência",
               "CVM tab I + base pública do CNPJ", "marcador do art. 69 da Lei 11.101/2005",
               "Exposição = estoque atribuído de recebíveis originados, não dívida nem perda. "
               "Instituições financeiras não podem usar recuperação judicial (art. 2º, II).",
               limite=30)

    casos = read("casos_regulatorios.csv")
    if casos is not None and len(casos):
        import re as _re

        def _processos(txt):
            """Identificadores de processo citados num texto (PAS, SEI etc.)."""
            return sorted(set(_re.findall(r"\d{5}\.\d{6}/\d{4}-\d{2}", str(txt))))

        # Pessoas naturais: cargo + entidade + processo + data permitem reidentificação
        # trivial em consulta pública. No painel elas entram agregadas por caso,
        # sem cargo nem vínculo específico (recomendação do manual jurídico) — mas o
        # NÚMERO DO PROCESSO permanece visível: imputação sem identificador do
        # processo é a regressão apontada pelo espelho.
        pf = casos.entidade_principal.str.contains("pessoa natural", case=False, na=False)
        if pf.any():
            agreg = (casos[pf].groupby(["tipo_evento", "data_evento", "status_processual"],
                                       as_index=False)
                     .agg(entidade_principal=("entidade_principal", lambda x:
                          f"{len(x)} pessoa(s) natural(is) acusada(s) — identificação "
                          "suprimida nesta apresentação; consulte a fonte oficial"),
                          papel=("papel", lambda x: "; ".join(sorted(set(x)))),
                          descricao_irregularidade=("descricao_irregularidade", lambda x:
                          "Processo(s): " + "; ".join(sorted({p for t in x for p in _processos(t)}))
                          + ". Condutas individuais descritas na decisão oficial (fonte)."),
                          nivel_evidencia=("nivel_evidencia", "first"),
                          fonte_url=("fonte_url", "first")))
            casos = pd.concat([casos[~pf], agreg], ignore_index=True)
        # "Seu diretor responsável foi multado…" liga cargo a empresa nominada
        # (reidentificação trivial). A sanção à pessoa natural fica registrada
        # sem o cargo; o nome está na fonte oficial.
        if "descricao_irregularidade" in casos.columns:
            casos["descricao_irregularidade"] = casos.descricao_irregularidade.str.replace(
                r"Seus? diretora? respons[áa]vel foi multad[oa]",
                "Pessoa natural também foi multada", regex=True, case=False)
        # CR010: "gestora, seu diretor, Santander Securities e seu diretor" liga
        # cargo a empresa nominada — reidentificação trivial. Reescrito no padrão
        # agregado, mantendo instituições, valores e o número do processo.
        m10 = casos.get("caso_id", pd.Series(dtype=str)).eq("CR010") \
            if "caso_id" in casos.columns else \
            casos.entidade_principal.str.contains("seu diretor", case=False, na=False)
        if m10.any():
            casos.loc[m10, "entidade_principal"] = (
                "Proponentes de termo de compromisso no PAS CVM 19957.006858/2019-25 — "
                "2 instituições e 2 pessoa(s) natural(is), identificação das pessoas "
                "naturais suprimida nesta apresentação")
            casos.loc[m10, "descricao_irregularidade"] = (
                "PAS CVM 19957.006858/2019-25. Propostas de termo de compromisso "
                "apresentadas por 2 instituições (R$ 90.000,00 e R$ 300.000,00) e por "
                "2 pessoas naturais (R$ 60.000,00 e R$ 100.000,00). O Colegiado da CVM "
                "rejeitou, por unanimidade, todas as propostas.")
    tabela("casos", casos,
           [c_ for c_ in ["entidade_principal", "papel", "tipo_evento", "data_evento",
                          "descricao_irregularidade", "status_processual",
                          "nivel_evidencia", "fonte_url"]
            if casos is not None and c_ in casos.columns],
           "Casos regulatórios e sancionadores", "CVM, BCB e fontes oficiais",
           "processos e decisões",
           "Investigação, acusação e condenação são estágios distintos e estão explicitados. "
           "A descrição da conduta e o número do processo qualificam cada imputação — "
           "linha sem eles não é publicável.",
           limite=40)

    testes = read("testes_auditoria.csv")
    tabela("testes", testes, ["teste", "resultado", "status", "detalhe"],
           "Testes de auditoria", "execução própria sobre a base publicada",
           "scripts/05_testes_auditoria.py", None, limite=40)

    # ---------------- fichas individuais (raio-X do veículo) ----------------
    # Universo: os 400 maiores por PL + todos os que disparam sinal, para que a
    # busca cubra tanto o topo do mercado quanto os casos de atenção.
    import duckdb as _dd
    con = _dd.connect(os.path.join(ROOT, "data", "duckdb", "fidc.db"), read_only=True)
    fichas = con.execute(f"""
    WITH base AS (
      SELECT p.CNPJ, p.DENOM_SOCIAL, p.VL_PL, p.TP_FUNDO_CLASSE,
             a.ADMIN, a.CNPJ_ADMIN, a.FUNDO_EXCLUSIVO, a.COTST_INTERESSE,
             a.TAB_I2A_VL_DIRCRED_RISCO dc_a, a.TAB_I2B_VL_DIRCRED_SEM_RISCO dc_b,
             a.TAB_I2A11_VL_REDUCAO_RECUP prov_a
      FROM painel_saneado p
      LEFT JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
      WHERE p.DT_COMPTC='{CORTE}'),
    ge AS (
      SELECT regexp_replace(rc.CNPJ_Classe,'\\D','','g') cnpj, MAX(rf.Gestor) gestor
      FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo) GROUP BY 1),
    inad AS (
      SELECT CNPJ, TAB_V_A_VL_DIRCRED_PRAZO dcv, TAB_V_B_VL_DIRCRED_INAD inadv
      FROM dc_risco_prazos WHERE DT_COMPTC='{CORTE}'),
    sub AS (
      SELECT CNPJ, SUM(VL_SERIE) FILTER (TIPO_COTA IN ('subordinada','mezanino')) vsub,
             SUM(VL_SERIE) vtot
      FROM series_cotas WHERE DT_COMPTC='{CORTE}' GROUP BY 1),
    sac AS (
      SELECT CNPJ, MAX(VALOR) FILTER (SEQUENCIAL='1') maior_sacado
      FROM sacados_conc WHERE DT_COMPTC='{CORTE}' GROUP BY 1),
    ced AS (
      SELECT CNPJ, MAX(PR_CEDENTE) pr_max, COUNT(*) n_ced FROM cedentes
      WHERE DT_COMPTC='{CORTE}' AND PR_CEDENTE > 0 AND PR_CEDENTE <= 100 GROUP BY 1),
    cot AS (SELECT CNPJ, SUM(TAB_X_NR_COTST) n_cot FROM cotistas_serie
            WHERE DT_COMPTC='{CORTE}' GROUP BY 1)
    SELECT b.DENOM_SOCIAL, b.CNPJ, b.TP_FUNDO_CLASSE, b.VL_PL, b.ADMIN, g.gestor,
           COALESCE(b.dc_a,0)+COALESCE(b.dc_b,0) dc, b.dc_b dc_sem_risco,
           CASE WHEN i.dcv > 0 THEN i.inadv/i.dcv END inad_pct,
           CASE WHEN s.vtot > 0 THEN s.vsub/s.vtot END subord,
           CASE WHEN (COALESCE(b.dc_a,0)+COALESCE(b.dc_b,0)) > 0
                THEN sc.maior_sacado/(COALESCE(b.dc_a,0)+COALESCE(b.dc_b,0)) END pct_maior_sacado,
           c.pr_max pct_maior_cedente, c.n_ced n_cedentes_declarados,
           ct.n_cot posicoes_cotistas, b.FUNDO_EXCLUSIVO exclusivo,
           b.COTST_INTERESSE interesse_unico
    FROM base b
    LEFT JOIN ge g ON g.cnpj=b.CNPJ
    LEFT JOIN inad i ON i.CNPJ=b.CNPJ
    LEFT JOIN sub s ON s.CNPJ=b.CNPJ
    LEFT JOIN sac sc ON sc.CNPJ=b.CNPJ
    LEFT JOIN ced c ON c.CNPJ=b.CNPJ
    LEFT JOIN cot ct ON ct.CNPJ=b.CNPJ
    ORDER BY b.VL_PL DESC LIMIT 400""").df()
    # sinais disparados por veículo (rf2)
    sinais_v = {}
    rfs = read("rf2_sinais.csv")
    if rfs is not None:
        col_cnpj = "CNPJ" if "CNPJ" in rfs.columns else rfs.columns[0]
        col_sig = next((c for c in ("sinal_id", "sinal", "id") if c in rfs.columns), None)
        if col_sig:
            for cnpj, grp in rfs.groupby(rfs[col_cnpj].astype(str)):
                sinais_v[cnpj.zfill(14)] = sorted(set(grp[col_sig].astype(str)))[:12]
    fichas["sinais"] = fichas.CNPJ.astype(str).map(lambda x: sinais_v.get(x, []))
    # Cobertura e classificação rf2 em TODA ficha: sem isso, um veículo não
    # classificável apareceria com "nenhum sinal disparado" — a regra-mãe
    # (cobertura insuficiente nunca é baixo risco) vale também aqui.
    if rf2s is not None:
        rfx = rf2s.copy()
        rfx["CNPJ"] = rfx.CNPJ.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(14)
        rfx = rfx.set_index("CNPJ")[["cobertura_dados_pct", "classificacao",
                                     "score_risco", "n_avaliaveis", "n_disparos"]]
        fichas = fichas.merge(rfx, left_on=fichas.CNPJ.astype(str).str.zfill(14),
                              right_index=True, how="left").drop(columns=["key_0"],
                                                                 errors="ignore")
    TAB["fichas"] = dict(
        rotulo="Ficha do veículo", fonte="CVM — informe mensal (múltiplas tabelas)",
        campo="painel canônico do corte",
        nota="Os 400 maiores veículos por patrimônio. Campos nulos aparecem como '—' e "
             "significam ausência de reporte, nunca zero. Veículo com cobertura de dados "
             "abaixo de 50% é NÃO CLASSIFICÁVEL: a ficha não emite juízo de sinal para ele.",
        colunas=list(fichas.columns),
        linhas=json.loads(fichas.to_json(orient="values")))

    # ---------------- raio-X da empresa (grupo econômico) ----------------
    # Visão centrada na EMPRESA: em quais veículos ela aparece como cedente,
    # com que recorrência, e se há recuperação/falência ou papel de cotista
    # corporativo documentado. Cobertura herdada da lente 4 (piso, top-9).
    emp = read("lente_4_cedentes.csv", dtype={"doc_cedente": str})
    if emp is not None and len(emp):
        emp["doc_cedente"] = emp.doc_cedente.astype(str).str.zfill(14)
        rec = read("cedentes_recorrencia.csv", dtype={"doc_cedente": str})
        if rec is not None:
            rec["doc_cedente"] = rec.doc_cedente.astype(str).str.zfill(14)
            emp = emp.merge(rec[["doc_cedente", "n_meses", "primeira", "ultima"]],
                            on="doc_cedente", how="left")
        rjm2 = read("rj_matches_cedentes.csv", dtype={"doc_cedente": str})
        if rjm2 is not None and len(rjm2):
            rjm2["doc_cedente"] = rjm2.doc_cedente.astype(str).str.zfill(14)
            st = (rjm2.groupby("doc_cedente")
                  .apply(lambda g: "; ".join(f"{r.evento} ({r.data_evento})"
                                             for r in g.itertuples()), include_groups=False)
                  .rename("status_judicial"))
            emp = emp.merge(st, on="doc_cedente", how="left")
        icx = read("investidores_corporativos.csv", dtype=str)
        if icx is not None and "cnpj" in icx.columns:
            docs_ic = set(icx.cnpj.astype(str).str.replace(r"\D", "", regex=True).str.zfill(14))
            emp["cotista_corporativo"] = emp.doc_cedente.isin(docs_ic)
        emp = emp.sort_values("exposicao_estimada", ascending=False).head(60)
        # veículos onde a empresa aparece como cedente (nome + % declarado)
        docs = "','".join(emp.doc_cedente)
        vlist = con.execute(f"""
          SELECT c.DOC_CEDENTE doc, p.DENOM_SOCIAL nome, MAX(c.PR_CEDENTE) pr
          FROM cedentes c JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
          WHERE c.DT_COMPTC='{CORTE}' AND c.DOC_CEDENTE IN ('{docs}')
            AND c.PR_CEDENTE > 0 AND c.PR_CEDENTE <= 100
          GROUP BY 1,2 ORDER BY pr DESC""").df()
        vmap = {d: [f"{r.nome} ({r.pr:.0f}%)" for r in g.head(5).itertuples()]
                for d, g in vlist.groupby("doc")}
        emp["veiculos"] = emp.doc_cedente.map(lambda d: vmap.get(d, []))
        emp = emp[[c_ for c_ in ["razao_social", "doc_cedente", "cnae_principal",
                                 "situacao", "uf", "exposicao_estimada", "n_veiculos",
                                 "n_meses", "primeira", "ultima", "status_judicial",
                                 "cotista_corporativo", "veiculos"] if c_ in emp.columns]]
        TAB["empresas"] = dict(
            rotulo="Raio-X da empresa (cedente/originador)",
            fonte="CVM — tab I (cedentes) + base pública do CNPJ + DataJud/CNJ",
            campo="lente_4_cedentes + cedentes_recorrencia + rj_matches_cedentes",
            nota="Estoque ATRIBUÍDO de recebíveis originados — não é dívida da empresa "
                 "nem fluxo cedido. Cobertura é piso (top-9 cedentes por veículo, 29,4% "
                 "do estoque). Recuperação judicial NÃO é evidência de irregularidade. "
                 "Percentual entre parênteses = participação declarada da empresa na "
                 "carteira do veículo.",
            colunas=list(emp.columns),
            unidades=[UNIDADES.get(c_, "auto") for c_ in emp.columns],
            linhas=json.loads(emp.to_json(orient="values")))
    con.close()

    # ---------------- meta ----------------
    man = pd.read_csv(os.path.join(ROOT, "manifesto_fontes.csv"))
    matriz = pd.read_csv(os.path.join(ROOT, "MATRIZ_FONTES_COBERTURA.csv"))
    meta = dict(
        data_corte=CORTE, data_extracao=EXTRACAO,
        competencia_parcial="2026-07-31" if len(jul) else None,
        n_arquivos_manifesto=int(len(man)),
        n_tabelas_informe=int((matriz.tabela.str.startswith("tab ")).sum()),
        n_tabelas_carregadas=int(matriz[matriz.tabela.str.startswith("tab ")]
                                 .carregada_na_base.sum()),
        pl_parcial_julho=float(jul.pl_total.iloc[0]) if len(jul) else None,
        n_veiculos_julho=int(jul.n_veiculos.iloc[0]) if len(jul) else None,
        hash_manifesto=hashlib.sha256(
            open(os.path.join(ROOT, "manifesto_fontes.csv"), "rb").read()).hexdigest()[:16],
    )

    with open(DEST, "w", encoding="utf-8") as f:
        json.dump(dict(meta=meta, indicadores=IND, tabelas=TAB), f,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"{len(IND)} indicadores, {len(TAB)} tabelas -> {DEST} "
          f"({os.path.getsize(DEST)/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
