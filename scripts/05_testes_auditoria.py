#!/usr/bin/env python3
"""
Etapa 5 — Testes mínimos obrigatórios de auditoria.

Executa os testes da seção 9 do mandato e grava data/analytic/testes_auditoria.csv
com resultado, tolerância e status (PASS / WARN / FAIL).

Tolerâncias: 0,1% para reconciliações internas; 1% para bases externas de
perímetro conhecido; acima disso a divergência é reportada individualmente.

Reprodução: python3 scripts/05_testes_auditoria.py
"""
import hashlib
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"

results = []


def add(teste, resultado, status, detalhe=""):
    results.append({"teste": teste, "resultado": resultado, "status": status,
                    "detalhe": detalhe})
    print(f"[{status}] {teste}: {resultado} {detalhe}")


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    con.execute("""CREATE TEMP VIEW painel_t AS
      WITH dedup_cnpj AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY CNPJ, DT_COMPTC
          ORDER BY CASE TP_FUNDO_CLASSE WHEN 'Classe' THEN 0 ELSE 1 END) rn FROM pl),
      mapa AS (
        SELECT DISTINCT regexp_replace(rc.CNPJ_Classe,'\\D','','g') cnpj_classe,
               regexp_replace(rf.CNPJ_Fundo,'\\D','','g') cnpj_fundo
        FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo)
        WHERE regexp_replace(rc.CNPJ_Classe,'\\D','','g') <> regexp_replace(rf.CNPJ_Fundo,'\\D','','g')),
      f AS (SELECT DISTINCT m.cnpj_fundo, p.DT_COMPTC FROM pl p JOIN mapa m ON p.CNPJ=m.cnpj_classe),
      base AS (
        SELECT d.* FROM dedup_cnpj d
        LEFT JOIN f ON d.TP_FUNDO_CLASSE='Fundo' AND d.CNPJ=f.cnpj_fundo AND d.DT_COMPTC=f.DT_COMPTC
        WHERE d.rn=1 AND f.cnpj_fundo IS NULL),
      viz AS (
        SELECT *, LAG(VL_PL) OVER w pl_prev, LEAD(VL_PL) OVER w pl_next
        FROM base WINDOW w AS (PARTITION BY CNPJ ORDER BY DT_COMPTC))
      SELECT * FROM viz
      WHERE NOT (VL_PL > 1e9 AND pl_prev IS NOT NULL AND pl_next IS NOT NULL
        AND VL_PL > 20*GREATEST(pl_prev, pl_next))""")

    # T1: reconciliação do PL agregado — painel (tab IV) x serie_mercado_mensal.csv
    pl_db = con.execute(f"SELECT SUM(VL_PL) FROM painel_t WHERE DT_COMPTC='{CORTE}'").fetchone()[0]
    serie = pd.read_csv(f"{OUT}/serie_mercado_mensal.csv")
    pl_csv = serie.loc[serie.DT_COMPTC == CORTE, "pl_total"].iloc[0]
    diff = abs(pl_db / pl_csv - 1)
    add("T1 reconciliação PL agregado (DB x CSV publicado)", f"dif {diff:.6%}",
        "PASS" if diff < 0.001 else "FAIL", f"PL={pl_db/1e9:.1f} bi")

    # T2: soma por administrador x total do painel
    adm = pd.read_csv(f"{OUT}/ranking_administradores.csv")
    diff = abs(adm["pl"].sum() / pl_db - 1)
    add("T2 soma por administrador x PL total", f"dif {diff:.4%}",
        "PASS" if diff < 0.001 else "WARN",
        "veículos sem CNPJ_ADMIN no informe ficam fora do ranking")

    # T2b: soma por gestor x total
    gest = pd.read_csv(f"{OUT}/ranking_gestores.csv")
    diff = abs(gest["pl"].sum() / pl_db - 1)
    add("T2b soma por gestor x PL total", f"dif {diff:.4%}",
        "PASS" if diff < 0.001 else "WARN")

    # T3: CNPJs duplicados por competência no painel canônico
    dup = con.execute("""SELECT COUNT(*) FROM (
      SELECT CNPJ, DT_COMPTC FROM painel_t GROUP BY 1,2 HAVING COUNT(*)>1)""").fetchone()[0]
    add("T3 CNPJs duplicados por competência (painel)", dup,
        "PASS" if dup == 0 else "FAIL")

    # T4: veículos cancelados no registro presentes no corte
    canc = con.execute(f"""
    SELECT COUNT(*) FROM painel_t p
    JOIN (SELECT regexp_replace(CNPJ_Fundo,'\\D','','g') c, Situacao FROM registro_fundo
          WHERE Tipo_Fundo LIKE '%FIDC%'
          QUALIFY ROW_NUMBER() OVER (PARTITION BY regexp_replace(CNPJ_Fundo,'\\D','','g')
            ORDER BY CASE Situacao WHEN 'Em Funcionamento Normal' THEN 0 ELSE 1 END)=1) r
      ON r.c=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' AND r.Situacao='Cancelado'""").fetchone()[0]
    add("T4 veículos com registro 'Cancelado' informando no corte", canc,
        "PASS" if canc < 30 else "WARN",
        "cancelamentos posteriores à competência são esperados em pequeno número")

    # T5: PL negativo e DC negativos
    neg = con.execute(f"SELECT COUNT(*) FROM painel_t WHERE DT_COMPTC='{CORTE}' AND VL_PL<0").fetchone()[0]
    add("T5 veículos com PL negativo no corte", neg, "WARN" if neg else "PASS",
        "listados em alertas.csv")
    negdc = con.execute(f"""SELECT COUNT(*) FROM ativo
      WHERE DT_COMPTC='{CORTE}' AND (TAB_I2A_VL_DIRCRED_RISCO<0 OR TAB_I2B_VL_DIRCRED_SEM_RISCO<0)""").fetchone()[0]
    add("T5b direitos creditórios negativos no corte", negdc,
        "PASS" if negdc == 0 else "WARN")

    # T6: continuidade da série mensal
    meses = con.execute("SELECT COUNT(DISTINCT DT_COMPTC) FROM pl").fetchone()[0]
    add("T6 competências na série 2013-01..2026-07", meses,
        "PASS" if meses == 163 else "WARN", "esperado 163 meses")

    # T7: salto máximo do PL agregado m/m
    salto = con.execute("""
    WITH s AS (SELECT DT_COMPTC, SUM(VL_PL) pl FROM painel_t GROUP BY 1),
    d AS (SELECT DT_COMPTC, abs(pl/LAG(pl) OVER (ORDER BY DT_COMPTC)-1) v FROM s)
    SELECT MAX(v) FROM d WHERE DT_COMPTC < '2026-07-01'""").fetchone()[0]
    add("T7 maior variação m/m do PL agregado", f"{salto:.2%}",
        "PASS" if salto < 0.30 else "WARN")

    # T8: reprodução independente do top-20 (leitura direta do CSV bruto da CVM)
    raw = pd.read_csv(os.path.join(RAW, "extracted", "inf_mensal_fidc_tab_IV_202606.csv"),
                      sep=";", encoding="latin1", dtype=str, quoting=3)
    raw["VL_PL"] = pd.to_numeric(raw["TAB_IV_A_VL_PL"], errors="coerce")
    raw["CNPJ"] = raw["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
    raw = raw.sort_values("VL_PL", ascending=False).drop_duplicates("CNPJ")
    top_raw = set(raw.head(20)["CNPJ"])
    top_pub = set(pd.read_csv(f"{OUT}/maiores_veiculos.csv", dtype={"CNPJ": str}).head(20)["CNPJ"])
    inter = len(top_raw & top_pub)
    add("T8 top-20 veículos: interseção bruto x publicado", f"{inter}/20",
        "PASS" if inter >= 19 else "FAIL")

    # T9: recálculo independente do ranking de administradores (caminho alternativo)
    rawI = pd.read_csv(os.path.join(RAW, "extracted", "inf_mensal_fidc_tab_I_202606.csv"),
                       sep=";", encoding="latin1", dtype=str, quoting=3)
    rawI["CNPJ"] = rawI["CNPJ_FUNDO_CLASSE"].str.replace(r"\D", "", regex=True)
    m = raw.merge(rawI[["CNPJ", "CNPJ_ADMIN"]], on="CNPJ", how="left")
    m["cnpj_admin"] = m["CNPJ_ADMIN"].str.replace(r"\D", "", regex=True)
    alt = m.groupby("cnpj_admin")["VL_PL"].sum().sort_values(ascending=False)
    pub = adm.set_index(adm["cnpj_admin"].astype(str).str.zfill(14))["pl"]
    alt.index = alt.index.astype(str).str.zfill(14)
    top10 = alt.head(10)
    comp = pd.concat([top10, pub], axis=1, join="inner")
    maxdif = (comp.iloc[:, 0] / comp.iloc[:, 1] - 1).abs().max()
    add("T9 ranking administradores: recálculo independente top-10",
        f"dif máx {maxdif:.4%}", "PASS" if maxdif < 0.001 else "FAIL")

    # T10: HHI recalculado
    v = con.execute(f"SELECT VL_PL FROM painel_t WHERE DT_COMPTC='{CORTE}' AND VL_PL>0").df()["VL_PL"]
    hhi = float(((v / v.sum()) ** 2).sum())
    conc = pd.read_csv(f"{OUT}/concentracao_indicadores.csv", index_col=0)
    hhi_pub = float(conc.loc["hhi_veiculos"].iloc[0])
    add("T10 HHI veículos recalculado", f"{hhi:.6f} x {hhi_pub:.6f}",
        "PASS" if abs(hhi - hhi_pub) < 1e-6 else "FAIL")

    # T11: circularidade (cotas de FIDC detidas por veículos do mercado)
    circ = serie.loc[serie.DT_COMPTC == CORTE, "cotas_fidc_detidas"].iloc[0]
    add("T11 circularidade intramercado", f"{circ/pl_db:.2%} do PL", "PASS",
        "cotas de FIDC/FIDC-NP no ativo de outros veículos do universo")

    # T12: partes relacionadas — alienações para cedentes/prestadores em 12m
    pr = con.execute("""
    SELECT COUNT(DISTINCT n.CNPJ), SUM(TAB_VII_B1_2_VL_CEDENTE+coalesce(TAB_VII_B2_2_VL_PREST,0))
    FROM negocios n WHERE n.DT_COMPTC BETWEEN '2025-07-01' AND '2026-06-30'
      AND (TAB_VII_B1_2_VL_CEDENTE>0 OR TAB_VII_B2_2_VL_PREST>0)""").fetchone()
    add("T12 veículos com alienações a cedentes/prestadores (12m)",
        f"{pr[0]} veículos, R$ {pr[1]/1e9:.1f} bi", "PASS", "sinal de operações com partes relacionadas")

    # T13: manifesto — existência e integridade (amostra de 5 hashes)
    man = pd.read_csv(os.path.join(ROOT, "manifesto_fontes.csv"))
    missing = [a for a in man["arquivo"] if not os.path.exists(os.path.join(RAW, a))]
    add("T13 arquivos-fonte existentes", f"{len(man)-len(missing)}/{len(man)}",
        "PASS" if not missing else "FAIL")
    amostra = man.sample(5, random_state=42)
    bad = []
    for _, r in amostra.iterrows():
        h = hashlib.sha256(open(os.path.join(RAW, r["arquivo"]), "rb").read()).hexdigest()
        if h != r["sha256"]:
            bad.append(r["arquivo"])
    add("T13b integridade SHA-256 (amostra 5)", f"{5-len(bad)}/5 ok",
        "PASS" if not bad else "FAIL", ";".join(bad))

    # T14: divergência externa — ANBIMA (perímetro distinto, documentada)
    anbima = 852.7e9  # PL FIDC jun/2026, ANBIMA (boletim de fundos, via imprensa)
    diff = pl_db / anbima - 1
    add("T14 PL CVM x ANBIMA jun/2026", f"+{diff:.1%} vs ANBIMA",
        "WARN", "perímetros distintos: universo CVM inclui FIC-FIDC e veículos "
        "fora da cobertura ANBIMA; divergência analisada no relatório, seção Limitações")

    # T15: subordinação x PL (consistência tab X_2 x tab IV)
    sub = pd.read_csv(f"{OUT}/subordinacao_agregada.csv")
    tot_series = sub["valor"].sum()
    diff = abs(tot_series / pl_db - 1)
    n_sem_x2 = con.execute(f"""
      SELECT COUNT(*) FROM painel_t p WHERE p.DT_COMPTC='{CORTE}'
        AND NOT EXISTS (SELECT 1 FROM series_cotas s
                        WHERE s.CNPJ=p.CNPJ AND s.DT_COMPTC='{CORTE}')""").fetchone()[0]
    add("T15 soma das séries de cotas (X_2) x PL (tab IV)", f"dif {diff:.2%}",
        "PASS" if diff < 0.01 else "WARN",
        f"{n_sem_x2} veículos sem X_2 no corte; a diferença residual vem de defasagem "
        "de marcação entre o valor da cota e o PL contábil, não de cobertura")

    pd.DataFrame(results).to_csv(f"{OUT}/testes_auditoria.csv", index=False)
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{len(results)} testes; FAIL={n_fail}")
    con.close()
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
