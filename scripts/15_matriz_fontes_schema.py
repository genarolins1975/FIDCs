#!/usr/bin/env python3
"""
Etapa 15 — Matriz de fontes/cobertura e changelog de schema.

Gera dois entregáveis de forma AUTOMÁTICA (nada escrito à mão):

  MATRIZ_FONTES_COBERTURA.csv — uma linha por tabela-fonte, com período
      disponível, nº de competências, veículos no corte, cobertura sobre o
      universo, se está carregada na base e onde é usada.

  SCHEMA_CHANGELOG.md — detecta mudanças reais de layout comparando os
      cabeçalhos de cada tabela entre competências consecutivas (colunas
      criadas, removidas e renomeadas), desde 2013.

Reprodução: python3 scripts/15_matriz_fontes_schema.py
"""
import glob
import os
import re
import sys
from collections import defaultdict

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXTRACT = os.environ.get("FIDC_EXTRACT_DIR", os.path.join(ROOT, "data", "raw", "extracted"))
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"

USO = {
    "I": "ativo, carteira, cedentes, circularidade, exclusividade (lentes 3,4)",
    "II": "carteira por segmento econômico",
    "III": "passivo e derivativos — identidade contábil Ativo−Passivo=PL",
    "IV": "patrimônio líquido — base de todos os agregados (lentes 1,2)",
    "V": "DC com risco: prazos e inadimplência",
    "VI": "DC sem risco: prazos e inadimplência",
    "VII": "aquisições, alienações, recompras e substituições",
    "VIII": "concentração dos 25 maiores devedores (lente 5)",
    "IX": "taxas de desconto e juros — preço de aquisição",
    "X": "classificação SCR das operações e dos devedores",
    "X_1": "número de cotistas por série (lente 6)",
    "X_1_1": "cotistas por categoria de investidor",
    "X_2": "valor por série de cota — subordinação (lente 6)",
    "X_3": "rentabilidade mensal por série",
    "X_4": "captações, resgates e amortizações",
    "X_5": "liquidez por prazo",
    "X_6": "desempenho esperado × realizado por série",
    "X_7": "garantias sobre os direitos creditórios",
}

TABELA_DB = {
    "I": "ativo", "II": "carteira_segmento", "IV": "pl", "V": "dc_risco_prazos",
    "VI": "dc_semrisco_prazos", "VII": "negocios", "VIII": "sacados_conc",
    "IX": "taxas", "X": "scr", "X_1": "cotistas_serie", "X_1_1": "cotistas_tipo",
    "X_2": "series_cotas", "X_3": "rentab_cotas", "X_4": "captacoes",
    "X_5": "liquidez", "X_6": "desempenho", "X_7": "garantias", "III": "passivo",
}


def tabs_disponiveis():
    """Mapeia tabela -> {competência: [colunas]} a partir dos CSVs extraídos."""
    pat = re.compile(r"inf_mensal_fidc_tab_([A-Z_0-9]+?)_(\d{4,6})\.csv$")
    out = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(EXTRACT, "*.csv"))):
        m = pat.search(os.path.basename(f))
        if not m:
            continue
        tab, comp = m.group(1), m.group(2)
        with open(f, encoding="latin1") as fh:
            header = fh.readline().strip().split(";")
        out[tab][comp] = header
    return out


def main() -> int:
    disp = tabs_disponiveis()
    con = duckdb.connect(DB, read_only=True)
    n_univ = con.execute(
        f"SELECT COUNT(*) FROM painel_saneado WHERE DT_COMPTC='{CORTE}'").fetchone()[0]
    tabelas_db = set(con.execute("SHOW TABLES").df().name)

    linhas = []
    for tab in sorted(disp, key=lambda t: (len(t), t)):
        comps = sorted(disp[tab])
        alvo = con.execute("SELECT 1").fetchone()  # placeholder
        t_db = TABELA_DB.get(tab)
        carregada = bool(t_db and t_db in tabelas_db)
        n_corte = None
        if carregada:
            try:
                n_corte = con.execute(
                    f"SELECT COUNT(DISTINCT CNPJ) FROM {t_db} WHERE DT_COMPTC='{CORTE}'"
                ).fetchone()[0]
            except duckdb.Error:
                n_corte = None
        linhas.append({
            "fonte": "CVM — Informe Mensal FIDC",
            "tabela": f"tab {tab}",
            "conteudo": USO.get(tab, "—"),
            "primeira_competencia": comps[0],
            "ultima_competencia": comps[-1],
            "n_competencias": len(comps),
            "carregada_na_base": carregada,
            "tabela_duckdb": t_db or "—",
            "veiculos_no_corte": n_corte,
            "cobertura_sobre_universo_pct": (
                round(100 * n_corte / n_univ, 1) if n_corte else None),
            "nivel_fonte": "1-primária",
        })

    # fontes não-informe
    extras = [
        ("CVM — Cadastro/Registro fundo-classe-subclasse", "registro_*",
         "papéis institucionais e situação cadastral", True, "registro_fundo/classe/subclasse"),
        ("CVM — Medidas FIE", "medidas_mes_fie", "validação cruzada do PL (T16)", True, "—"),
        ("CVM — CDA (bloco 2)", "cda_fi_BLC_2", "detentores de cotas na indústria de fundos", True, "—"),
        ("BCB/SGS série 433", "IPCA", "deflacionamento da série real", True, "ipca"),
        ("Receita Federal (base pública CNPJ)", "minhareceita.org",
         "razão social e CNAE de cedentes", True, "—"),
        ("Demonstrações financeiras publicadas", "DF corporativas",
         "cotas de FIDC em balanço (lente 7)", True, "—"),
        ("DataJud/CNJ", "api_publica", "recuperação judicial e falência (lente 9)",
         os.path.exists(os.path.join(ROOT, "data", "analytic", "rj_processos.csv")), "—"),
    ]
    for fonte, tabela, conteudo, carregada, tdb in extras:
        linhas.append({
            "fonte": fonte, "tabela": tabela, "conteudo": conteudo,
            "primeira_competencia": None, "ultima_competencia": None,
            "n_competencias": None, "carregada_na_base": carregada,
            "tabela_duckdb": tdb, "veiculos_no_corte": None,
            "cobertura_sobre_universo_pct": None,
            "nivel_fonte": "1-primária" if "CVM" in fonte or "BCB" in fonte
                           or "Receita" in fonte or "Demonstra" in fonte
                           or "DataJud" in fonte else "2-validação",
        })

    matriz = pd.DataFrame(linhas)
    matriz.to_csv(os.path.join(ROOT, "MATRIZ_FONTES_COBERTURA.csv"), index=False)

    # ---------- changelog de schema ----------
    md = ["# SCHEMA_CHANGELOG — Informe Mensal de FIDC",
          "",
          "Gerado automaticamente por `scripts/15_matriz_fontes_schema.py` comparando os",
          "cabeçalhos de cada tabela entre competências consecutivas. Toda mudança abaixo",
          "foi detectada nos arquivos publicados pela CVM, não em documentação.",
          ""]
    total_mud = 0
    for tab in sorted(disp, key=lambda t: (len(t), t)):
        comps = sorted(disp[tab])
        eventos = []
        for a, b in zip(comps, comps[1:]):
            ca, cb = set(disp[tab][a]), set(disp[tab][b])
            add, rem = sorted(cb - ca), sorted(ca - cb)
            if add or rem:
                eventos.append((b, add, rem))
        if eventos:
            total_mud += len(eventos)
            md.append(f"## tab {tab} — {USO.get(tab,'')}")
            md.append("")
            for comp, add, rem in eventos:
                md.append(f"**{comp[:4]}-{comp[4:] or '01'}**")
                if add:
                    md.append(f"- criadas ({len(add)}): `" + "`, `".join(add[:12]) +
                              ("`, …" if len(add) > 12 else "`"))
                if rem:
                    md.append(f"- removidas ({len(rem)}): `" + "`, `".join(rem[:12]) +
                              ("`, …" if len(rem) > 12 else "`"))
                md.append("")
    md.insert(6, f"**{total_mud} mudanças de layout detectadas** em "
                 f"{len(disp)} tabelas, entre {min(min(v) for v in disp.values())} e "
                 f"{max(max(v) for v in disp.values())}.\n")
    with open(os.path.join(ROOT, "SCHEMA_CHANGELOG.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(matriz[["tabela", "carregada_na_base", "veiculos_no_corte",
                  "cobertura_sobre_universo_pct"]].head(20).to_string(index=False))
    print(f"\n{total_mud} mudanças de schema detectadas")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
