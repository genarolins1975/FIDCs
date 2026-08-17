#!/usr/bin/env python3
"""
Etapa 8 — Validações adicionais incorporadas após benchmark externo.

(a) Reconciliação Informe Mensal x Medidas CVM/FIE (segunda fonte primária
    interna) na interseção de CNPJs — teste T16.
(b) Cobertura explícita dos rankings de prestadores (custodiante,
    controlador, auditor) sobre o PL do corte.
(c) Publicação das anomalias de cedentes (percentuais fora de (0,100]).
(d) Provisões/redução de valor (TAB_I2A11/I2B11) e razão sobre inadimplência.
(e) Atualização do manifesto com as fontes novas (Medidas FIE, DF Banco Honda).

Reprodução: python3 scripts/08_validacoes_extra.py
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


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    con = duckdb.connect(DB, read_only=True)

    # (a) Medidas FIE x Informe na interseção
    med = pd.read_csv(os.path.join(RAW, "medidas_mes_fie_202606.csv"),
                      sep=";", encoding="latin1", dtype=str, quoting=3)
    med["CNPJ"] = med["CNPJ_FUNDO"].str.replace(r"\D", "", regex=True)
    med["PL_MEDIDAS"] = pd.to_numeric(med["VL_PATRIM_LIQ"], errors="coerce")
    med = med[med["TP_FUNDO"].str.contains("FIDC", na=False)]
    med = med.drop_duplicates("CNPJ")
    painel = con.execute(f"""
      SELECT CNPJ, VL_PL FROM painel_saneado WHERE DT_COMPTC='{CORTE}'""").df()
    inter = painel.merge(med[["CNPJ", "PL_MEDIDAS"]], on="CNPJ", how="inner")
    dif = abs(inter.VL_PL.sum() / inter.PL_MEDIDAS.sum() - 1)
    rec = pd.DataFrame([{
        "teste": "T16 Informe x Medidas CVM/FIE (interseção de CNPJs)",
        "n_cnpjs_intersecao": len(inter),
        "pl_informe_intersecao": inter.VL_PL.sum(),
        "pl_medidas_intersecao": inter.PL_MEDIDAS.sum(),
        "diferenca_relativa": dif,
        "cobertura_medidas_sobre_pl_corte": inter.VL_PL.sum() / painel.VL_PL.sum(),
        "status": "PASS" if dif < 0.001 else "FAIL",
    }])
    rec.to_csv(f"{OUT}/reconciliacao_medidas_fie.csv", index=False)
    print(rec.to_string(index=False))

    # (b) cobertura dos rankings de prestadores
    pl_corte = painel.VL_PL.sum()
    cob = []
    for papel in ("custodiantes", "controladores", "auditores"):
        df = pd.read_csv(f"{OUT}/ranking_{papel}.csv")
        cob.append({"papel": papel, "pl_identificado": df.pl.sum(),
                    "cobertura_sobre_pl_corte": df.pl.sum() / pl_corte,
                    "n_entidades": len(df)})
    pd.DataFrame(cob).to_csv(f"{OUT}/prestadores_cobertura.csv", index=False)
    print(pd.DataFrame(cob).to_string(index=False))

    # (c) anomalias de cedentes no corte (PR fora de (0,100])
    anom = con.execute(f"""
      SELECT c.CNPJ cnpj_veiculo, c.DOC_CEDENTE, c.PR_CEDENTE, c.BUCKET, c.POSICAO
      FROM cedentes c JOIN painel_saneado p ON p.CNPJ=c.CNPJ AND p.DT_COMPTC=c.DT_COMPTC
      WHERE c.DT_COMPTC='{CORTE}' AND (c.PR_CEDENTE <= 0 OR c.PR_CEDENTE > 100)
        AND c.PR_CEDENTE IS NOT NULL""").df()
    anom.to_csv(f"{OUT}/cedentes_anomalias_excluidas.csv", index=False)
    print("anomalias de cedentes excluídas:", len(anom))

    # (d) provisões / redução de valor
    prov = con.execute(f"""
      SELECT SUM(coalesce(TAB_I2A11_VL_REDUCAO_RECUP,0)) red_com_risco,
             SUM(coalesce(TAB_I2B11_VL_REDUCAO_RECUP,0)) red_sem_risco
      FROM ativo WHERE DT_COMPTC='{CORTE}'""").df()
    ag = pd.read_csv(f"{OUT}/inadimplencia_aging_serie.csv")
    r = ag[ag.DT_COMPTC == CORTE].iloc[0]
    inad = r.inad_com_risco + r.inad_sem_risco
    prov["inadimplencia_total"] = inad
    prov["razao_reducao_sobre_inadimplencia"] = (
        prov.red_com_risco + prov.red_sem_risco) / inad
    prov.to_csv(f"{OUT}/provisoes_reducao.csv", index=False)
    print(prov.round(3).to_string(index=False))

    # (e) manifesto: fontes novas
    man = pd.read_csv(os.path.join(ROOT, "manifesto_fontes.csv"))
    novas = []
    p_med = os.path.join(RAW, "medidas_mes_fie_202606.csv")
    if os.path.exists(p_med) and "medidas_mes_fie_202606.csv" not in set(man.arquivo):
        novas.append({
            "arquivo": "medidas_mes_fie_202606.csv", "categoria": "medidas_fie",
            "url": "https://dados.cvm.gov.br/dados/FIE/MEDIDAS/DADOS/medidas_mes_fie_202606.csv",
            "tamanho_bytes": os.path.getsize(p_med), "sha256": sha256_of(p_med),
            "last_modified_servidor": "", "data_extracao_utc": "2026-08-17T20:40:00+00:00",
            "fonte": "CVM — Portal de Dados Abertos", "nivel_fonte": "1-primaria"})
    if novas:
        man = pd.concat([man, pd.DataFrame(novas)], ignore_index=True)
        man.to_csv(os.path.join(ROOT, "manifesto_fontes.csv"), index=False)
        print("manifesto atualizado:", len(man), "arquivos")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
