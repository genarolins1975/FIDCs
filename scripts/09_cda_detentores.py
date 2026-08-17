#!/usr/bin/env python3
"""
Etapa 9 — Quem carrega cotas de FIDC em carteira (visão de regulador).

Cruza a CDA (Composição e Diversificação das Aplicações) de toda a indústria
de fundos (cda_fi_BLC_2: bloco "cotas de fundos") com o universo de FIDCs do
painel, identificando os fundos investidores com maiores posições em cotas de
FIDC, seus gestores e o flag de emissor ligado (EMISSOR_LIGADO — declarado
pelo próprio administrador).

Limitação declarada: a CDA pública cobre o universo de fundos regulados
(inclui FICs, FIMs, previdência aberta etc.); posições confidenciais (art.
56, §3º) ficam no arquivo CONFID e não são somadas; detentores fora da
indústria de fundos (bancos, empresas, PF) não aparecem aqui.

Reprodução: python3 scripts/09_cda_detentores.py
"""
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
CDA = os.path.join(ROOT, "data", "raw", "extracted_cda")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    fidc_univ = set(con.execute(
        f"SELECT DISTINCT CNPJ FROM painel_saneado WHERE DT_COMPTC='{CORTE}'").df().CNPJ)

    blc = pd.read_csv(os.path.join(CDA, "cda_fi_BLC_2_202606.csv"),
                      sep=";", encoding="latin1", dtype=str, quoting=3)
    for c in ("VL_MERC_POS_FINAL",):
        blc[c] = pd.to_numeric(blc[c], errors="coerce")
    blc["cnpj_investidor"] = blc.CNPJ_FUNDO_CLASSE.str.replace(r"\D", "", regex=True)
    blc["cnpj_cota"] = blc.CNPJ_FUNDO_CLASSE_COTA.str.replace(r"\D", "", regex=True)
    pos = blc[blc.cnpj_cota.isin(fidc_univ)].copy()

    # o investidor pode ser ele próprio um FIDC/FIC-FIDC (circularidade já
    # medida); flag para leitura separada
    pos["investidor_e_fidc"] = pos.cnpj_investidor.isin(fidc_univ)

    # ranking de fundos investidores (fora do universo FIDC)
    ext = pos[~pos.investidor_e_fidc]
    rank_fundos = (ext.groupby(["cnpj_investidor", "DENOM_SOCIAL"], as_index=False)
                   .agg(vl_cotas_fidc=("VL_MERC_POS_FINAL", "sum"),
                        n_fidcs_investidos=("cnpj_cota", "nunique"),
                        n_posicoes_ligadas=("EMISSOR_LIGADO", lambda s: (s == "S").sum()))
                   .sort_values("vl_cotas_fidc", ascending=False))
    rank_fundos.to_csv(f"{OUT}/detentores_cda_fundos.csv", index=False)

    # agregar por gestor do fundo investidor (cad_fi, fotografia)
    cad = con.execute(r"""
      WITH reg AS (
        SELECT regexp_replace(rc.CNPJ_Classe,'\D','','g') cnpj, MAX(rf.Gestor) gestor
        FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo)
        GROUP BY 1
        UNION ALL
        SELECT regexp_replace(CNPJ_Fundo,'\D','','g'), MAX(Gestor)
        FROM registro_fundo GROUP BY 1
        UNION ALL
        SELECT regexp_replace(CNPJ_FUNDO,'\D','','g'), MAX(GESTOR)
        FROM cad_fi GROUP BY 1)
      SELECT cnpj, MAX(gestor) gestor FROM reg WHERE gestor IS NOT NULL GROUP BY 1""").df()
    m = rank_fundos.merge(cad, left_on="cnpj_investidor", right_on="cnpj", how="left")
    rank_gestores = (m.groupby("gestor", dropna=False, as_index=False)
                     .agg(vl_cotas_fidc=("vl_cotas_fidc", "sum"),
                          n_fundos=("cnpj_investidor", "nunique"))
                     .sort_values("vl_cotas_fidc", ascending=False))
    rank_gestores.to_csv(f"{OUT}/detentores_cda_gestores.csv", index=False)

    # posições declaradas como emissor ligado (partes relacionadas na cadeia)
    ligadas = pos[pos.EMISSOR_LIGADO == "S"]
    resumo = pd.DataFrame([{
        "posicoes_cotas_fidc": len(pos),
        "vl_total_cotas_fidc_na_cda": pos.VL_MERC_POS_FINAL.sum(),
        "vl_detido_por_nao_fidc": ext.VL_MERC_POS_FINAL.sum(),
        "vl_detido_por_fidc_fic": pos[pos.investidor_e_fidc].VL_MERC_POS_FINAL.sum(),
        "vl_posicoes_emissor_ligado": ligadas.VL_MERC_POS_FINAL.sum(),
        "n_fundos_investidores": ext.cnpj_investidor.nunique(),
    }])
    resumo.to_csv(f"{OUT}/detentores_cda_resumo.csv", index=False)
    print(resumo.T.to_string())
    print("\nTop 10 fundos detentores (fora do universo FIDC):")
    print(rank_fundos.head(10)[["DENOM_SOCIAL", "vl_cotas_fidc", "n_fidcs_investidos"]]
          .assign(vl_cotas_fidc=lambda d: (d.vl_cotas_fidc / 1e9).round(2)).to_string(index=False))
    print("\nTop 10 gestores detentores:")
    print(rank_gestores.head(10).assign(
        vl_cotas_fidc=lambda d: (d.vl_cotas_fidc / 1e9).round(2)).to_string(index=False))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
