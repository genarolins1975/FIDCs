#!/usr/bin/env python3
"""
Etapa 12 — Monitor de Recuperação Judicial e Falência (DataJud/CNJ) e
casamento com os cedentes dos FIDCs.

O QUE ESTE SCRIPT FAZ
---------------------
1. Consulta a API Pública do DataJud/CNJ (Elasticsearch _search) para as classes
   processuais de Recuperação Judicial (129) e Falência (108) ajuizadas nos
   últimos 24 meses nos tribunais de maior volume (TJSP, TJRJ, TJMG, TJRS, TJPR).
   Grava o JSON bruto em data/raw/datajud/ e um extrato normalizado em
   data/analytic/rj_processos.csv.

2. Casa empresas em RJ/falência com os cedentes dos FIDCs APENAS POR CNPJ.
   Nunca por semelhança de nome.

3. Classifica o papel do FIDC em cada caso.

LIMITAÇÃO ESTRUTURAL — LEIA ANTES DE USAR
-----------------------------------------
A API Pública do DataJud **NÃO retorna as partes** do processo. Os documentos
expõem apenas: id, tribunal, grau, numeroProcesso, dataAjuizamento, nivelSigilo,
orgaoJulgador, classe, sistema, formato, dataHoraUltimaAtualizacao, movimentos e
assuntos. Não há campo de partes, polo ativo/passivo, nome ou CNPJ de litigante
(verificado empiricamente — ver docs/METODOLOGIA_RECUPERACAO_JUDICIAL.md).

Consequência: **é impossível casar processos do DataJud com CNPJs de cedentes.**
O DataJud serve aqui como *denominador* (quantas RJs/falências foram ajuizadas,
onde e quando), não como fonte de identificação de empresas.

A identificação nominal de empresas vem de duas fontes independentes, ambas
ancoradas em CNPJ:
  (a) o cadastro CNPJ da Receita Federal, cuja razão social carrega o sufixo
      "EM RECUPERAÇÃO JUDICIAL" por exigência do art. 69 da Lei 11.101/2005; e
  (b) data/analytic/rj_casos_confirmados.csv, curado a partir de fontes públicas
      com URL e nível de evidência declarados.

RESILIÊNCIA
-----------
Se a API estiver indisponível, o script registra a falha em log, emite os CSVs
com o cabeçalho correto e vazios de linhas, e retorna 0 — o pipeline não quebra.

Reprodução: python3 scripts/12_monitor_rj.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw", "datajud")
OUT = os.path.join(ROOT, "data", "analytic")
LOGDIR = os.path.join(ROOT, "data", "raw")

# Chave pública documentada em https://datajud-wiki.cnj.jus.br/api-publica/acesso
API_KEY = os.environ.get(
    "DATAJUD_APIKEY",
    "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdz==",
)
BASE = "https://api-publica.datajud.cnj.jus.br/api_publica_{trib}/_search"
TRIBUNAIS = ["tjsp", "tjrj", "tjmg", "tjrs", "tjpr"]

# Classes processuais (Tabela Processual Unificada do CNJ).
# ATENÇÃO: 130 NÃO é falência — não retorna nenhum documento no DataJud.
# A classe de falência empresarial é 108.
CLASSES = {
    129: "Recuperação Judicial",
    108: "Falência de Empresários, Sociedades Empresárias, ME e EPP",
}
MESES = 24
PAGE = 1000          # tamanho de página do search_after
MAX_POR_TRIBUNAL = 20000

# Colunas contratuais — emitidas mesmo quando não há dado, para não quebrar o pipeline.
COLS_PROC = [
    "tribunal", "grau", "numero_processo", "classe_codigo", "classe_nome",
    "data_ajuizamento", "orgao_julgador", "municipio_ibge", "assuntos",
    "n_movimentos", "ultimo_movimento", "data_ultimo_movimento",
    "tem_partes_no_datajud",
]
COLS_MATCH = [
    "doc_cedente", "razao_social_cedente", "exposicao_estimada", "n_veiculos",
    "cnpj_empresa_rj", "razao_social_rj", "evento", "data_evento", "tribunal",
    "papel_fidc", "chave_casamento", "nivel_evidencia", "fonte", "observacao",
]

log = logging.getLogger("monitor_rj")


def _setup_log() -> None:
    os.makedirs(LOGDIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(LOGDIR, "monitor_rj.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _headers() -> dict:
    return {"Authorization": f"APIKey {API_KEY}", "Content-Type": "application/json"}


def _janela() -> tuple[str, str]:
    hoje = datetime.now(timezone.utc)
    ini = hoje - timedelta(days=int(MESES * 30.44))
    return ini.strftime("%Y%m%d000000"), hoje.strftime("%Y%m%d235959")


def consulta_tribunal(trib: str, ses: requests.Session) -> list[dict]:
    """Baixa todos os processos de RJ/falência do tribunal na janela, via search_after."""
    gte, lte = _janela()
    query = {
        "size": PAGE,
        "query": {
            "bool": {
                "must": [{"terms": {"classe.codigo": list(CLASSES)}}],
                "filter": [{"range": {"dataAjuizamento": {"gte": gte, "lte": lte}}}],
            }
        },
        "sort": [{"dataAjuizamento": {"order": "asc"}}, {"_id": {"order": "asc"}}],
    }
    docs: list[dict] = []
    after = None
    while len(docs) < MAX_POR_TRIBUNAL:
        body = dict(query)
        if after:
            body["search_after"] = after
        r = ses.post(BASE.format(trib=trib), headers=_headers(), json=body, timeout=120)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            break
        docs.extend(h["_source"] for h in hits)
        after = hits[-1].get("sort")
        if len(hits) < PAGE or not after:
            break
    log.info("%s: %d processos baixados", trib.upper(), len(docs))
    return docs


def normaliza(docs: list[dict]) -> pd.DataFrame:
    linhas = []
    for d in docs:
        movs = d.get("movimentos") or []
        ult = max(movs, key=lambda m: m.get("dataHora", ""), default={})
        oj = d.get("orgaoJulgador") or {}
        linhas.append({
            "tribunal": d.get("tribunal"),
            "grau": d.get("grau"),
            "numero_processo": d.get("numeroProcesso"),
            "classe_codigo": (d.get("classe") or {}).get("codigo"),
            "classe_nome": (d.get("classe") or {}).get("nome"),
            "data_ajuizamento": d.get("dataAjuizamento"),
            "orgao_julgador": oj.get("nome"),
            "municipio_ibge": oj.get("codigoMunicipioIBGE"),
            "assuntos": "; ".join(
                str(a.get("nome")) for a in (d.get("assuntos") or []) if a.get("nome")
            ),
            "n_movimentos": len(movs),
            "ultimo_movimento": ult.get("nome"),
            "data_ultimo_movimento": ult.get("dataHora"),
            # Marcador honesto: o DataJud público nunca traz partes.
            "tem_partes_no_datajud": False,
        })
    df = pd.DataFrame(linhas, columns=COLS_PROC)
    if not df.empty:
        df["data_ajuizamento"] = pd.to_datetime(
            df["data_ajuizamento"], format="%Y%m%d%H%M%S", errors="coerce"
        )
    return df


def _so_digitos(s) -> str:
    return "".join(ch for ch in str(s) if ch.isdigit())


def classifica_papel(natureza: str, no_ranking: bool) -> str:
    """Classifica o papel do FIDC. `natureza` vem do arquivo de casos confirmados."""
    n = (natureza or "").lower()
    if "sacado" in n or "devedor" in n:
        return "FIDC com exposição a sacado em RJ"
    if "coobrig" in n or "recompra" in n:
        return "empresa com coobrigação"
    if "cedente" in n or "originador" in n or "cedeu" in n:
        return "FIDC com exposição a cedente em RJ"
    if "credor" in n or "habilit" in n:
        return "FIDC credor"
    return "FIDC com exposição a cedente em RJ" if no_ranking else "relação apenas hipotética"


def casa_por_cnpj() -> pd.DataFrame:
    """
    Casa empresas em RJ/falência com cedentes de FIDC EXCLUSIVAMENTE por CNPJ.

    Duas trilhas, ambas ancoradas em CNPJ:
      A) razão social do próprio cadastro CNPJ contém "EM RECUPERAÇÃO JUDICIAL"
         (art. 69 da Lei 11.101/2005 obriga o acréscimo ao nome empresarial);
      B) CNPJ listado em rj_casos_confirmados.csv (curadoria de fontes públicas).

    Nunca casa por semelhança de nome. Casos sem CNPJ público entram marcados
    como "correspondência por nome, requer validação humana" e o vínculo NÃO é
    afirmado.
    """
    p_rank = os.path.join(OUT, "cedentes_ranking_nomes.csv")
    if not os.path.exists(p_rank):
        log.warning("ranking de cedentes ausente (%s) — sem casamento", p_rank)
        return pd.DataFrame(columns=COLS_MATCH)

    rank = pd.read_csv(p_rank, dtype={"doc_cedente": str})
    rank = rank[rank["doc_cedente"].str.len() == 14].copy()
    rank["razao_social"] = rank["razao_social"].fillna("")

    linhas = []

    # --- Trilha A: marcador de RJ na própria razão social do cadastro CNPJ ---
    marca = rank["razao_social"].str.upper().str.contains(
        r"EM RECUPERA(C|Ç)(A|Ã)O JUDICIAL|MASSA FALIDA|EM FAL(E|Ê)NCIA", regex=True, na=False
    )
    for _, r in rank[marca].iterrows():
        falida = "MASSA FALIDA" in r["razao_social"].upper()
        linhas.append({
            "doc_cedente": r["doc_cedente"],
            "razao_social_cedente": r["razao_social"],
            "exposicao_estimada": r.get("exposicao_estimada"),
            "n_veiculos": r.get("n_veiculos"),
            "cnpj_empresa_rj": r["doc_cedente"],
            "razao_social_rj": r["razao_social"],
            "evento": "falência" if falida else "recuperação judicial",
            "data_evento": "",
            "tribunal": "",
            "papel_fidc": "FIDC com exposição a cedente em RJ",
            "chave_casamento": "CNPJ (idêntico) — razão social do cadastro CNPJ/RFB",
            "nivel_evidencia": "fato confirmado por fonte primária",
            "fonte": "Cadastro CNPJ/Receita Federal via minhareceita.org; "
                     "Lei 11.101/2005 art. 69 (sufixo obrigatório)",
            "observacao": "Empresa figura como cedente de direitos creditórios em FIDC "
                          "e seu nome empresarial registrado já traz o sufixo de RJ. "
                          "Estar em RJ não é indício de irregularidade.",
        })

    # --- Trilha B: CNPJ presente no arquivo de casos confirmados ---
    p_casos = os.path.join(OUT, "rj_casos_confirmados.csv")
    if os.path.exists(p_casos):
        casos = pd.read_csv(p_casos, dtype=str).fillna("")
        idx = {r["doc_cedente"]: r for _, r in rank.iterrows()}
        for _, c in casos.iterrows():
            cnpj = _so_digitos(c.get("cnpj", ""))
            if len(cnpj) != 14:
                linhas.append({
                    "doc_cedente": "", "razao_social_cedente": "",
                    "exposicao_estimada": "", "n_veiculos": "",
                    "cnpj_empresa_rj": "", "razao_social_rj": c.get("razao_social", ""),
                    "evento": c.get("status_processual", ""),
                    "data_evento": c.get("data_evento", ""),
                    "tribunal": c.get("tribunal", ""),
                    "papel_fidc": "relação apenas hipotética",
                    "chave_casamento": "correspondência por nome, requer validação humana",
                    "nivel_evidencia": "dados insuficientes",
                    "fonte": c.get("fonte_url", ""),
                    "observacao": "CNPJ não público na fonte — vínculo com cedente de FIDC "
                                  "NÃO afirmado. Requer validação humana.",
                })
                continue
            hit = idx.get(cnpj)
            no_ranking = hit is not None
            linhas.append({
                "doc_cedente": cnpj if no_ranking else "",
                "razao_social_cedente": hit["razao_social"] if no_ranking else "",
                "exposicao_estimada": hit.get("exposicao_estimada") if no_ranking else "",
                "n_veiculos": hit.get("n_veiculos") if no_ranking else "",
                "cnpj_empresa_rj": cnpj,
                "razao_social_rj": c.get("razao_social", ""),
                "evento": c.get("status_processual", ""),
                "data_evento": c.get("data_evento", ""),
                "tribunal": c.get("tribunal", ""),
                "papel_fidc": classifica_papel(c.get("natureza_ligacao_fidc", ""), no_ranking),
                "chave_casamento": ("CNPJ (idêntico) — presente no ranking de cedentes"
                                    if no_ranking else
                                    "CNPJ público, porém ausente do ranking de cedentes "
                                    "(sem exposição medida no corte)"),
                "nivel_evidencia": c.get("nivel_evidencia", ""),
                "fonte": c.get("fonte_url", ""),
                "observacao": c.get("observacao", ""),
            })

    df = pd.DataFrame(linhas, columns=COLS_MATCH)
    if not df.empty:
        df = df.drop_duplicates(subset=["cnpj_empresa_rj", "razao_social_rj", "evento"])
        df = df.sort_values("exposicao_estimada", ascending=False, na_position="last")
    return df


def main() -> int:
    _setup_log()
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)

    todos: list[dict] = []
    ok, falhas = [], []
    ses = requests.Session()
    for trib in TRIBUNAIS:
        try:
            docs = consulta_tribunal(trib, ses)
            with open(os.path.join(RAW, f"{trib}_rj_falencia.json"), "w", encoding="utf-8") as fh:
                json.dump(docs, fh, ensure_ascii=False)
            todos.extend(docs)
            ok.append(trib)
        except Exception as e:  # rede, 4xx, 5xx, timeout
            log.error("DataJud indisponível para %s: %s", trib.upper(), str(e)[:200])
            falhas.append(trib)

    df = normaliza(todos)
    df.to_csv(os.path.join(OUT, "rj_processos.csv"), index=False)
    if df.empty:
        log.warning("rj_processos.csv emitido VAZIO (apenas cabeçalho) — "
                    "DataJud indisponível ou sem resultados. Pipeline preservado.")
    else:
        log.info("rj_processos.csv: %d processos | tribunais ok=%s falhas=%s",
                 len(df), ok, falhas)
        log.info("Nenhum processo traz partes: a API pública do DataJud não expõe "
                 "nome/CNPJ de litigante — casamento com cedentes por processo é IMPOSSÍVEL.")

    m = casa_por_cnpj()
    m.to_csv(os.path.join(OUT, "rj_matches_cedentes.csv"), index=False)
    log.info("rj_matches_cedentes.csv: %d vínculos (%d por CNPJ idêntico)",
             len(m), int((m["chave_casamento"].str.startswith("CNPJ")).sum()) if len(m) else 0)

    # resumo agregado do denominador judicial (sem identificação de empresas)
    if not df.empty:
        res = (df.assign(mes=df["data_ajuizamento"].dt.to_period("M").astype(str))
                 .groupby(["tribunal", "classe_nome", "mes"]).size()
                 .reset_index(name="n_processos"))
        res.to_csv(os.path.join(OUT, "rj_processos_resumo.csv"), index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
