#!/usr/bin/env python3
"""
Etapa 00 — Orquestrador de atualização do Panorama FIDC Brasil.

Executa o pipeline completo na ordem correta, com dois contratos:

  1. GATE DE PUBLICAÇÃO: se os testes de auditoria (etapa 05) ou a verificação
     de fórmulas (etapa 20) falharem, o painel NÃO é regenerado — o build para
     com erro e o manifesto registra a falha. Nenhum artefato inconsistente
     sai deste script.
  2. MANIFESTO DE EXECUÇÃO: cada rodada grava data/analytic/manifesto_execucao.csv
     com etapa, status, duração e hash do artefato principal — a trilha de que
     versão do código produziu que versão do dado.

Também versiona um SNAPSHOT de rf2_sinais.csv por execução
(data/analytic/snapshots/rf2_sinais_<data>.csv). É esse snapshot que torna
computável, na próxima edição, o indicador "sinais encerrados desde a última
publicação" — sem ele, só é possível contar sinais novos e persistentes.

Uso:
  python3 scripts/00_atualizar.py           # pipeline analítico completo
  python3 scripts/00_atualizar.py --com-download   # inclui download CVM (etapa 01)

A etapa de download é opcional porque é a única com dependência de rede; todo
o restante roda offline sobre data/raw/.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time
from datetime import date

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "analytic")

# (script, artefato principal para hash, é gate de publicação?)
ETAPAS = [
    ("02_build.py", "data/duckdb/fidc.db", False),
    ("02b_build_series_classes.py", "data/duckdb/fidc.db", False),
    ("03_analytics.py", "data/analytic/serie_mercado_mensal.csv", False),
    ("09_cda_detentores.py", "data/analytic/detentores_cda_resumo.csv", False),
    ("11_tab_viii_sacados.py", "data/analytic/sacados_concentracao.csv", False),
    ("11b_tabelas_faltantes.py", "data/analytic/identidade_contabil.csv", False),
    ("12_reconciliacao_competencia.py",
     "data/analytic/cobertura_competencia_202607_resumo.csv", False),
    ("13_red_flags_v2.py", "data/analytic/rf2_score_veiculo.csv", False),
    ("14_lentes_exposicao.py", "data/analytic/lentes_catalogo.csv", False),
    ("15_matriz_fontes_schema.py", "MATRIZ_FONTES_COBERTURA.csv", False),
    ("18_backtest.py", "data/analytic/backtest_resumo.csv", False),
    ("06_livro_evidencias.py", "auditoria/livro_evidencias.csv", False),
    ("05_testes_auditoria.py", "data/analytic/testes_auditoria.csv", True),
    ("16_painel_dados.py", "data/analytic/painel_dados.json", False),
    ("20_teste_formulas.py", "data/analytic/verificacao_formulas.csv", True),
    ("17_painel_v2.py", "relatorio/painel_fidc_v2.html", False),
    ("19_dicionario_dados.py", "DICIONARIO_DADOS_FIDC.md", False),
]

# Etapas com dependência de rede (CVM, API do CNPJ, DataJud): só entram com
# --com-download. O restante do pipeline roda offline sobre data/raw/.
ETAPAS_REDE = [
    ("01_download.py", "manifesto_fontes.csv", False),
    ("04_cedentes_nomes.py", "data/analytic/cedentes_ranking_nomes.csv", False),
    ("12_monitor_rj.py", "data/analytic/rj_processos.csv", False),
    ("12b_rj_casos_confirmados.py", "data/analytic/rj_casos_confirmados.csv", False),
]


def sha256(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> int:
    etapas = list(ETAPAS)
    if "--com-download" in sys.argv:
        etapas = ETAPAS_REDE[:1] + etapas
        # etapas de rede que dependem da base construída entram na posição certa
        pos = [e[0] for e in etapas].index("11_tab_viii_sacados.py")
        etapas[pos:pos] = ETAPAS_REDE[1:]

    linhas = []
    falhou = False
    for script, artefato, gate in etapas:
        t0 = time.time()
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)],
                           capture_output=True, text=True)
        dur = round(time.time() - t0, 1)
        ok = r.returncode == 0
        linhas.append(dict(etapa=script, status="OK" if ok else "FALHA",
                           gate="sim" if gate else "não", duracao_s=dur,
                           artefato=artefato, sha256_16=sha256(artefato)))
        print(f"{'OK  ' if ok else 'FALHA'} {script:32s} {dur:7.1f}s  {artefato}")
        if not ok:
            print(r.stdout[-2000:])
            print(r.stderr[-2000:])
            falhou = True
            if gate:
                print(f"\nGATE DE PUBLICAÇÃO: {script} reprovou — o painel não será "
                      "regenerado. Corrija e reexecute.")
            break

    # snapshot versionado de rf2_sinais: habilita "sinais encerrados" na próxima edição
    if not falhou:
        snap_dir = os.path.join(OUT, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        src = os.path.join(OUT, "rf2_sinais.csv")
        if os.path.exists(src):
            dst = os.path.join(snap_dir, f"rf2_sinais_{date.today().isoformat()}.csv")
            shutil.copy2(src, dst)
            print(f"snapshot: {os.path.relpath(dst, ROOT)}")

    import csv
    man = os.path.join(OUT, "manifesto_execucao.csv")
    with open(man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["etapa", "status", "gate", "duracao_s",
                                          "artefato", "sha256_16"])
        w.writeheader()
        w.writerows(linhas)
    print(f"manifesto de execução: {os.path.relpath(man, ROOT)}")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
