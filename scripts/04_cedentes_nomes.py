#!/usr/bin/env python3
"""
Etapa 4 — Resolução de entidades: razão social e CNAE dos maiores cedentes.

Os informes mensais identificam os cedentes apenas por CPF/CNPJ. Este script
resolve os CNPJs dos maiores cedentes (por exposição estimada no corte e por
recorrência) contra a base pública do CNPJ da Receita Federal, via API
minhareceita.org (espelho aberto da base oficial de CNPJs).

CPFs (cedentes pessoa física) NÃO são resolvidos — apenas contados — para
não reidentificar pessoas naturais.

Reprodução: python3 scripts/04_cedentes_nomes.py
"""
import json
import os
import sys
import time

import pandas as pd
import requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
CACHE = os.path.join(ROOT, "data", "cnpj_cache.json")
TOP_N = 150


def main() -> int:
    rank = pd.read_csv(os.path.join(OUT, "cedentes_ranking_estimado.csv"),
                       dtype={"doc_cedente": str})
    rec = pd.read_csv(os.path.join(OUT, "cedentes_recorrencia.csv"),
                      dtype={"doc_cedente": str})

    docs = list(dict.fromkeys(
        list(rank.head(TOP_N)["doc_cedente"]) +
        list(rec.head(100)["doc_cedente"])))
    cnpjs = [d for d in docs if isinstance(d, str) and len(d) == 14]

    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE))
    ses = requests.Session()
    for i, c in enumerate(cnpjs):
        if c in cache:
            continue
        try:
            r = ses.get(f"https://minhareceita.org/{c}", timeout=30)
            if r.status_code == 200:
                j = r.json()
                cache[c] = {
                    "razao_social": j.get("razao_social"),
                    "nome_fantasia": j.get("nome_fantasia"),
                    "cnae_principal": j.get("cnae_fiscal_descricao"),
                    "situacao": j.get("descricao_situacao_cadastral"),
                    "uf": j.get("uf"),
                }
            else:
                cache[c] = {"razao_social": None, "erro": f"http {r.status_code}"}
        except requests.RequestException as e:
            cache[c] = {"razao_social": None, "erro": str(e)[:120]}
        time.sleep(0.4)
        if i % 25 == 0:
            print(f"{i}/{len(cnpjs)}", flush=True)
            json.dump(cache, open(CACHE, "w"))
    json.dump(cache, open(CACHE, "w"))

    res = pd.DataFrame.from_dict(cache, orient="index")
    res.index.name = "doc_cedente"
    top = rank.head(TOP_N).merge(res, on="doc_cedente", how="left")
    top["tipo_doc"] = top["doc_cedente"].str.len().map({14: "CNPJ", 11: "CPF"})
    top.loc[top["tipo_doc"] == "CPF", "razao_social"] = "(pessoa física — não identificada)"
    top.to_csv(os.path.join(OUT, "cedentes_ranking_nomes.csv"), index=False)
    print("ok:", len(top), "cedentes; resolvidos:", res["razao_social"].notna().sum())
    return 0


if __name__ == "__main__":
    sys.exit(main())
