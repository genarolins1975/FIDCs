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


def tabela(key, df, cols, rotulo, fonte, campo, nota=None, limite=25):
    if df is None or not len(df):
        TAB[key] = dict(rotulo=rotulo, fonte=fonte, campo=campo, nota=nota,
                        colunas=[], linhas=[])
        return
    d = df[[c for c in cols if c in df.columns]].head(limite)
    TAB[key] = dict(rotulo=rotulo, fonte=fonte, campo=campo, nota=nota,
                    colunas=list(d.columns),
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
        "(TAB_I2A11 + TAB_I2B11) ÷ parcelas inadimplentes", "CVM — Informe Mensal FIDC",
        "tab I", "calculado", "Fato confirmado por fonte primária", 100.0, None, "C027")

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
    if l5 is not None:
        l5 = l5.sort_values("pct_maior_sacado", ascending=False)
        l5 = l5[l5.pct_maior_sacado.notna() & (l5.VL_PL > 1e8)]
    tabela("lente5", l5,
           ["entidade", "VL_PL", "pct_maior_sacado", "pct_top5", "pct_top10"],
           "Concentração por devedor (tab VIII)", "CVM — tab VIII",
           "SEQUENCIAL + VALOR",
           "A tabela VIII NÃO identifica o devedor. Só concentração, nunca identidade.")
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

    # red flags v2 (se disponível) — senão, v1
    rf2 = read("rf2_score_veiculo.csv")
    rfcat = read("rf2_catalogo.csv")
    if rf2 is not None and rfcat is not None:
        tabela("rf_score", rf2.sort_values("score_risco", ascending=False),
               [c_ for c_ in ["denom_social", "entidade", "DENOM_SOCIAL", "CNPJ",
                              "score_risco", "materialidade_financeira",
                              "cobertura_dados", "persistencia_media", "classificacao"]
                if c_ in rf2.columns],
               "Score de risco por veículo (experimental)",
               "CVM — informe mensal", "múltiplos campos",
               "Score alto NÃO é imputação de irregularidade. Cobertura < 50% ⇒ não classificável.")
        tabela("rf_catalogo", rfcat,
               [c_ for c_ in ["id", "pilar", "nome", "severidade", "limiar",
                              "cobertura_pct", "explicacoes_benignas"] if c_ in rfcat.columns],
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

    casos = read("casos_regulatorios.csv")
    tabela("casos", casos,
           [c_ for c_ in ["entidade_principal", "papel", "tipo_evento", "data_evento",
                          "descricao_irregularidade", "status_processual", "nivel_evidencia"]
            if casos is not None and c_ in casos.columns],
           "Casos regulatórios e sancionadores", "CVM, BCB e fontes oficiais",
           "processos e decisões",
           "Investigação, acusação e condenação são estágios distintos e estão explicitados.",
           limite=40)

    testes = read("testes_auditoria.csv")
    tabela("testes", testes, ["teste", "resultado", "status", "detalhe"],
           "Testes de auditoria", "execução própria sobre a base publicada",
           "scripts/05_testes_auditoria.py", None, limite=40)

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
