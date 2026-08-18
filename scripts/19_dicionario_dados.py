#!/usr/bin/env python3
"""
Etapa 19 — Dicionário de dados (gerado, não escrito à mão).

Combina os dicionários oficiais da CVM (meta_inf_mensal_fidc_tab_*.txt) com o
schema efetivo das tabelas materializadas no DuckDB, produzindo
DICIONARIO_DADOS_FIDC.md com: campo, descrição oficial, tipo, tabela de
origem, tabela analítica onde vive, cobertura no corte e observações de uso.

Reprodução: python3 scripts/19_dicionario_dados.py
"""
import glob
import os
import re
import sys
import zipfile

import duckdb

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
DEST = os.path.join(ROOT, "DICIONARIO_DADOS_FIDC.md")
CORTE = "2026-06-30"

TAB_DB = {
    "I": "ativo", "II": "carteira_segmento", "III": "passivo", "IV": "pl",
    "V": "dc_risco_prazos", "VI": "dc_semrisco_prazos", "VII": "negocios",
    "VIII": "sacados_conc", "IX": "taxas", "X": "scr", "X_1": "cotistas_serie",
    "X_1_1": "cotistas_tipo", "X_2": "series_cotas", "X_3": "rentab_cotas",
    "X_4": "captacoes", "X_5": "liquidez", "X_6": "desempenho", "X_7": "garantias",
}

NOTAS = {
    "TAB_I2I_VL_COTA_FIDC_NP": "**Campo em branco em 100% das linhas desde 2024.** A "
        "medida de circularidade usa apenas TAB_I2H. Somar como zero afirmaria ausência.",
    "TAB_I2A4_VL_CRED_DIRCRED_PERFM": "Descontinuado: cobertura zero desde 2023. Mantido no "
        "catálogo para documentar a lacuna, não usado em indicador.",
    "TAB_X_NR_COTST": "Conta **posições por veículo**, não pessoas únicas. Um investidor "
        "presente em N fundos é contado N vezes.",
    "SEQUENCIAL": "Posição no ranking interno de devedores do veículo (1 a 25). **Não há "
        "identificador do sacado** — é impossível somar a exposição de um devedor entre fundos.",
    "TAB_IX_A1_1_2_COMPRA_MEDIA": "Taxa média ponderada de desconto na aquisição. Apenas ~26% "
        "dos veículos operam no mês; os demais reportam zero. Há erros de unidade na cauda.",
    "TAB_X_PR_DESEMP_ESPERADO": "Desempenho declarado como esperado pelo administrador. "
        "Comparável ao realizado apenas quando ambos são informados.",
    "TAB_X_VL_GARANTIA_DIRCRED": "Garantia real sobre os direitos creditórios. Declarada por "
        "pouquíssimos veículos: a proteção do investidor vem de subordinação e coobrigação.",
    "TAB_III_VL_PASSIVO": "Habilita o teste de identidade contábil Ativo − Passivo = PL.",
}


def parse_meta():
    """Extrai {campo: descrição} dos dicionários oficiais da CVM."""
    out = {}
    z = os.path.join(RAW, "meta_inf_mensal_fidc_txt.zip")
    if not os.path.exists(z):
        return out
    with zipfile.ZipFile(z) as zf:
        for name in zf.namelist():
            tab = re.search(r"tab_([A-Z_0-9]+)\.txt$", name)
            if not tab:
                continue
            txt = zf.read(name).decode("latin1")
            campo = None
            for linha in txt.splitlines():
                m = re.match(r"Campo:\s*(\S+)", linha)
                if m:
                    campo = m.group(1)
                    continue
                d = re.match(r"\s*Descrição\s*:\s*(.*)", linha)
                if d and campo:
                    out.setdefault(campo, (tab.group(1), d.group(1).strip()))
                    campo = None
    return out


def main() -> int:
    meta = parse_meta()
    con = duckdb.connect(DB, read_only=True)
    tabelas = set(con.execute("SHOW TABLES").df().name)

    md = ["# DICIONÁRIO DE DADOS — Panorama FIDC Brasil", "",
          "Gerado por `scripts/19_dicionario_dados.py` cruzando os dicionários oficiais da CVM",
          "(`meta_inf_mensal_fidc_txt.zip`) com o schema efetivo das tabelas materializadas.",
          f"Cobertura medida na competência {CORTE}.", "",
          "Convenção de leitura: **cobertura** é a fração de veículos do universo com o campo",
          "preenchido (não nulo). Campo ausente permanece nulo e reduz a cobertura do indicador",
          "que dependa dele — nunca é convertido em zero.", ""]

    for tab, tdb in TAB_DB.items():
        if tdb not in tabelas:
            continue
        cols = con.execute(f"SELECT * FROM {tdb} LIMIT 0").df().columns.tolist()
        try:
            n_univ = con.execute(
                f"SELECT COUNT(*) FROM {tdb} WHERE DT_COMPTC='{CORTE}'").fetchone()[0] or 1
        except duckdb.Error:
            n_univ = 1
        md += [f"## Tabela {tab} → `{tdb}`", "",
               "| Campo | Descrição oficial | Cobertura | Observação |",
               "|---|---|---:|---|"]
        for c in cols:
            if c in ("CNPJ", "DT_COMPTC", "TP_FUNDO_CLASSE", "DENOM_SOCIAL"):
                continue
            desc = meta.get(c, (None, "—"))[1] or "—"
            try:
                nn = con.execute(
                    f'SELECT COUNT("{c}") FROM {tdb} WHERE DT_COMPTC=\'{CORTE}\'').fetchone()[0]
                cob = f"{100*nn/n_univ:.0f}%"
            except duckdb.Error:
                cob = "—"
            nota = NOTAS.get(c, "")
            md.append(f"| `{c}` | {desc} | {cob} | {nota} |")
        md.append("")

    md += ["## Tabelas derivadas (camada analítica)", "",
           "| Artefato | Conteúdo | Unidade de análise |", "|---|---|---|",
           "| `serie_mercado_mensal.csv` | série 2013-2026 de PL, carteira, cotistas e circularidade | veículo-mês agregado |",
           "| `lente_1..9_*.csv` | as nove lentes de exposição | varia por lente (ver `lentes_catalogo.csv`) |",
           "| `rf2_catalogo.csv` | fichas dos 46 sinais de atenção | sinal |",
           "| `rf2_sinais.csv` | disparos observados | veículo × sinal |",
           "| `rf2_score_veiculo.csv` | score decomposto em seis dimensões | veículo |",
           "| `sacados_concentracao.csv` | concentração por devedor | veículo |",
           "| `rj_matches_cedentes.csv` | vínculos com recuperação judicial | cedente × empresa |",
           "| `backtest_resumo.csv` | desempenho dos sinais antes de eventos | caso × sinal × grupo |",
           "| `painel_dados.json` | tudo que o painel exibe, com evidência por número | indicador |",
           ""]
    with open(DEST, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"dicionário: {DEST} ({len(md)} linhas, {len(meta)} campos oficiais mapeados)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
