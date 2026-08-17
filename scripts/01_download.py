#!/usr/bin/env python3
"""
Etapa 1 — Extração das bases primárias (CVM Dados Abertos).

Baixa, com trilha de auditoria completa (URL, SHA-256, tamanho, timestamps),
as bases necessárias ao panorama do mercado de FIDCs:

  - Cadastro de fundos (cad_fi.csv) e registro fundo/classe/subclasse (RCVM 175)
  - Informes Mensais de FIDC: zips anuais 2013-2024 (HIST) e mensais 2025-2026
  - Metadados (dicionário de dados) do Informe Mensal FIDC

Cada arquivo baixado gera uma linha em manifesto_fontes.csv.
Reprodução: python3 scripts/01_download.py
"""
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone

import requests

BASE = "https://dados.cvm.gov.br/dados"
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
MANIFEST = os.path.join(os.path.dirname(__file__), "..", "manifesto_fontes.csv")

SOURCES = []
# Cadastro
SOURCES.append(("cadastro", f"{BASE}/FI/CAD/DADOS/cad_fi.csv"))
SOURCES.append(("cadastro", f"{BASE}/FI/CAD/DADOS/registro_fundo_classe.zip"))
# Metadados do informe mensal FIDC
SOURCES.append(("metadados", f"{BASE}/FIDC/DOC/INF_MENSAL/META/meta_inf_mensal_fidc_txt.zip"))
# Histórico anual 2013-2024
for y in range(2013, 2025):
    SOURCES.append(("inf_mensal_hist", f"{BASE}/FIDC/DOC/INF_MENSAL/DADOS/HIST/inf_mensal_fidc_{y}.zip"))
# Mensal 2025-01 a 2026-07
for y, mmax in ((2025, 12), (2026, 7)):
    for m in range(1, mmax + 1):
        SOURCES.append(("inf_mensal", f"{BASE}/FIDC/DOC/INF_MENSAL/DADOS/inf_mensal_fidc_{y}{m:02d}.zip"))


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    rows = []
    ses = requests.Session()
    for kind, url in SOURCES:
        name = url.rsplit("/", 1)[-1]
        dest = os.path.join(RAW, name)
        t0 = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not os.path.exists(dest):
            print(f"baixando {name} ...", flush=True)
            r = ses.get(url, stream=True, timeout=300)
            r.raise_for_status()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
            os.replace(tmp, dest)
            last_mod = r.headers.get("Last-Modified", "")
        else:
            last_mod = ""
        rows.append({
            "arquivo": name,
            "categoria": kind,
            "url": url,
            "tamanho_bytes": os.path.getsize(dest),
            "sha256": sha256_of(dest),
            "last_modified_servidor": last_mod,
            "data_extracao_utc": t0,
            "fonte": "CVM — Portal de Dados Abertos",
            "nivel_fonte": "1-primaria",
        })
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"ok: {len(rows)} arquivos; manifesto em {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
