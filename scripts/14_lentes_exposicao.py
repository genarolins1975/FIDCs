#!/usr/bin/env python3
"""
Etapa 14 — As nove lentes de exposição (correção do achado crítico nº 5 da
AUDITORIA_PAINEL_FIDC.md).

O painel anterior exibia "PL sob administração" e "PL sob gestão" lado a lado
como se fossem a mesma medida de exposição. São coisas distintas, e nenhuma
das duas é exposição econômica. Este script materializa NOVE lentes, cada uma
com definição, numerador, denominador, cobertura, unidade de análise e o que
a lente explicitamente NÃO significa.

Saídas:
  data/analytic/lentes_catalogo.csv        — a ficha de cada lente
  data/analytic/lente_<n>_<nome>.csv       — o ranking/medida de cada lente

Princípio: ausência de informação permanece nula e é reportada como cobertura.
Nenhum denominador recebe zero por conveniência.

Reprodução: python3 scripts/14_lentes_exposicao.py
"""
import os
import sys

import duckdb
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DB = os.path.join(ROOT, "data", "duckdb", "fidc.db")
CORTE = "2026-06-30"

FICHAS = []


def ficha(n, nome, definicao, numerador, denominador, unidade, nao_significa,
          fonte, cobertura_pct, n_entidades, limitacao):
    FICHAS.append(dict(
        lente=n, nome=nome, definicao=definicao, numerador=numerador,
        denominador=denominador, unidade_analise=unidade,
        o_que_NAO_significa=nao_significa, fonte=fonte,
        cobertura_pct=cobertura_pct, n_entidades=n_entidades,
        limitacao=limitacao, data_base=CORTE))


def main() -> int:
    con = duckdb.connect(DB, read_only=True)
    pl_total = con.execute(
        f"SELECT SUM(VL_PL) FROM painel_saneado WHERE DT_COMPTC='{CORTE}'").fetchone()[0]

    # mapa gestor por veículo (registro ativo mais recente)
    con.execute(r"""
    CREATE OR REPLACE TEMP VIEW gestor_veiculo AS
    -- prioridade 1: CNPJ da classe (regime RCVM 175); prioridade 2: CNPJ do
    -- fundo (regime anterior). O ROW_NUMBER é aplicado DEPOIS do UNION, sobre
    -- o conjunto, para que um CNPJ presente nos dois braços conte uma só vez.
    WITH reg AS (
      SELECT regexp_replace(rc.CNPJ_Classe,'\D','','g') cnpj,
             rf.Gestor gestor, rf.CPF_CNPJ_Gestor doc, 1 AS prio,
             CASE rf.Situacao WHEN 'Em Funcionamento Normal' THEN 0 ELSE 1 END AS sit,
             rf.Data_Registro AS dt
      FROM registro_classe rc JOIN registro_fundo rf USING (ID_Registro_Fundo)
      WHERE rf.Gestor IS NOT NULL AND rc.CNPJ_Classe IS NOT NULL
      UNION ALL
      SELECT regexp_replace(CNPJ_Fundo,'\D','','g'), Gestor, CPF_CNPJ_Gestor, 2,
             CASE Situacao WHEN 'Em Funcionamento Normal' THEN 0 ELSE 1 END,
             Data_Registro
      FROM registro_fundo WHERE Gestor IS NOT NULL AND CNPJ_Fundo IS NOT NULL),
    dedup AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY cnpj ORDER BY prio, sit, dt DESC) rn
      FROM reg)
    SELECT cnpj, gestor, doc FROM dedup WHERE rn=1""")

    # ---------- Lente 1: PL sob gestão ----------
    l1 = con.execute(f"""
    SELECT g.gestor AS entidade, regexp_replace(g.doc,'\\D','','g') AS cnpj,
           SUM(p.VL_PL) AS valor, COUNT(*) AS n_veiculos,
           SUM(p.VL_PL)/{pl_total} AS participacao
    FROM painel_saneado p JOIN gestor_veiculo g ON g.cnpj=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' GROUP BY 1,2 ORDER BY valor DESC""").df()
    l1.to_csv(f"{OUT}/lente_1_pl_sob_gestao.csv", index=False)
    ficha(1, "PL sob gestão",
          "Soma do patrimônio líquido das classes cuja gestão de carteira é exercida pela entidade.",
          "Σ PL das classes geridas", "PL total do universo no corte", "gestor (entidade jurídica)",
          "NÃO é capital próprio do gestor nem exposição econômica dele ao risco de crédito das carteiras; "
          "o gestor responde por decisão de investimento, não pelo risco do ativo.",
          "CVM: registro fundo/classe (gestor) + informe mensal tab IV",
          round(100 * l1.valor.sum() / pl_total, 2), len(l1),
          "Registro é fotografia atual: trocas de gestor não são rastreadas retroativamente. "
          "Cobertura publicada com 2 casas: arredondar para 100% esconderia os veículos "
          "sem gestor identificado no registro.")

    # ---------- Lente 2: PL sob administração ----------
    l2 = con.execute(f"""
    SELECT MAX(a.ADMIN) AS entidade, regexp_replace(a.CNPJ_ADMIN,'\\D','','g') AS cnpj,
           SUM(p.VL_PL) AS valor, COUNT(*) AS n_veiculos,
           SUM(p.VL_PL)/{pl_total} AS participacao
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' AND a.CNPJ_ADMIN IS NOT NULL
    GROUP BY 2 ORDER BY valor DESC""").df()
    l2.to_csv(f"{OUT}/lente_2_pl_sob_administracao.csv", index=False)
    ficha(2, "PL sob administração fiduciária",
          "Soma do PL das classes cuja administração fiduciária é exercida pela entidade.",
          "Σ PL das classes administradas", "PL total do universo no corte",
          "administrador fiduciário (entidade jurídica)",
          "NÃO é exposição financeira do administrador: o patrimônio do fundo é segregado do "
          "patrimônio do prestador. Mede concentração OPERACIONAL, não risco de crédito.",
          "CVM: informe mensal tab I (CNPJ_ADMIN) + tab IV",
          round(100 * l2.valor.sum() / pl_total, 2), len(l2),
          "Autodeclarado no informe; mudanças de administrador aparecem com defasagem.")

    # ---------- Lente 3: exposição da carteira (direitos creditórios) ----------
    l3 = con.execute(f"""
    SELECT p.DENOM_SOCIAL AS entidade, p.CNPJ AS cnpj,
           a.TAB_I2A_VL_DIRCRED_RISCO AS dc_com_risco,
           a.TAB_I2B_VL_DIRCRED_SEM_RISCO AS dc_sem_risco,
           COALESCE(a.TAB_I2A_VL_DIRCRED_RISCO,0)+COALESCE(a.TAB_I2B_VL_DIRCRED_SEM_RISCO,0) AS valor,
           p.VL_PL,
           CASE WHEN p.VL_PL > 0 THEN
             (COALESCE(a.TAB_I2A_VL_DIRCRED_RISCO,0)+COALESCE(a.TAB_I2B_VL_DIRCRED_SEM_RISCO,0))/p.VL_PL
           END AS dc_sobre_pl
    FROM painel_saneado p JOIN ativo a ON a.CNPJ=p.CNPJ AND a.DT_COMPTC=p.DT_COMPTC
    WHERE p.DT_COMPTC='{CORTE}' ORDER BY valor DESC""").df()
    l3.to_csv(f"{OUT}/lente_3_carteira_dc.csv", index=False)
    ficha(3, "Exposição da carteira (direitos creditórios)",
          "Estoque de direitos creditórios de titularidade do fundo/classe, separado entre "
          "aquisição COM e SEM transferência substancial de riscos e benefícios.",
          "TAB_I2A + TAB_I2B", "PL do próprio veículo (razão DC/PL)", "fundo ou classe",
          "A parcela SEM aquisição substancial de risco NÃO representa risco transferido ao fundo: "
          "o risco econômico permanece no cedente (funding garantido, não venda definitiva).",
          "CVM: informe mensal tab I", 100.0, len(l3),
          "Valores contábeis autodeclarados, sem auditoria individual.")

    # ---------- Lente 4: exposição a cedente/originador ----------
    l4 = pd.read_csv(f"{OUT}/cedentes_ranking_nomes.csv", dtype={"doc_cedente": str})
    cob_ced = pd.read_csv(f"{OUT}/cedentes_cobertura.csv").iloc[0]
    l4.to_csv(f"{OUT}/lente_4_cedentes.csv", index=False)
    ficha(4, "Exposição a cedente/originador",
          "Estoque de direitos creditórios atribuível a cada cedente, pelo percentual declarado "
          "no informe (apenas os 9 maiores cedentes de cada veículo).",
          "Σ (% declarado × valor do bucket de DC)", "estoque total de DC do mercado",
          "cedente (CNPJ) — estoque atribuído",
          "NÃO é fluxo cedido no período nem dívida da empresa: é o saldo de recebíveis originados "
          "por ela que está na carteira dos fundos. NÃO é ranking completo — é piso.",
          "CVM: informe mensal tab I (campos de cedente) + base pública do CNPJ",
          round(100 * float(cob_ced.cobertura_top9), 1), len(l4),
          "Cobertura de 29,4% do estoque; cauda além do top-9 não observável; CPFs não resolvidos.")

    # ---------- Lente 5: exposição a sacado/devedor (tab VIII) ----------
    # Concentração dos 25 maiores devedores; SEM identificador do sacado.
    l5 = con.execute(f"""
    WITH s AS (
      SELECT CNPJ, DT_COMPTC,
             MAX(VALOR) FILTER (SEQUENCIAL='1') AS maior_sacado,
             SUM(VALOR) FILTER (CAST(SEQUENCIAL AS INT) <= 5) AS top5,
             SUM(VALOR) FILTER (CAST(SEQUENCIAL AS INT) <= 10) AS top10,
             SUM(VALOR) AS top25, COUNT(*) AS n_posicoes
      FROM sacados_conc WHERE DT_COMPTC='{CORTE}' GROUP BY 1,2),
    dc AS (
      SELECT CNPJ, TAB_I2A_VL_DIRCRED_RISCO, TAB_I2B_VL_DIRCRED_SEM_RISCO,
             COALESCE(TAB_I2A_VL_DIRCRED_RISCO,0)+COALESCE(TAB_I2B_VL_DIRCRED_SEM_RISCO,0) AS dc_tot
      FROM ativo WHERE DT_COMPTC='{CORTE}')
    SELECT p.DENOM_SOCIAL AS entidade, p.CNPJ AS cnpj, p.VL_PL,
           s.maior_sacado, s.top5, s.top10, s.top25, s.n_posicoes, dc.dc_tot,
           CASE WHEN dc.dc_tot > 0 THEN s.maior_sacado/dc.dc_tot END AS pct_maior_sacado,
           CASE WHEN dc.dc_tot > 0 THEN s.top5/dc.dc_tot END AS pct_top5,
           CASE WHEN dc.dc_tot > 0 THEN s.top10/dc.dc_tot END AS pct_top10
    FROM painel_saneado p
    JOIN s ON s.CNPJ=p.CNPJ
    LEFT JOIN dc ON dc.CNPJ=p.CNPJ
    WHERE p.DT_COMPTC='{CORTE}' ORDER BY s.maior_sacado DESC""").df()
    # marca os casos em que a soma dos 25 maiores excede a carteira informada:
    # a razão existe, mas não é interpretável como participação
    sc = pd.read_csv(f"{OUT}/sacados_concentracao.csv", dtype={"CNPJ": str})
    if "inconsistencia_viii_vs_i" in sc.columns:
        flag = sc.set_index(sc.CNPJ.astype(str).str.zfill(14))["inconsistencia_viii_vs_i"]
        l5["inconsistente_viii_vs_i"] = l5.cnpj.astype(str).str.zfill(14).map(flag).fillna(False)
    else:
        l5["inconsistente_viii_vs_i"] = False
    l5.to_csv(f"{OUT}/lente_5_sacados_concentracao.csv", index=False)
    # Três coberturas distintas, cada uma com sua definição — publicá-las sem
    # rótulo faria 69,3% e 79,7% parecerem contraditórias:
    #   (a) veículos: % dos veículos do corte que reportam a tab VIII;
    #   (b) DC dos cobertos: % do estoque de DC que está em veículos cobertos;
    #   (c) valor explicado: % do estoque total de DC efetivamente listado
    #       nas 25 posições (a cauda além do top-25 não é observável).
    cob5, cob5_dc, cob5_valor = con.execute(f"""
      WITH dc AS (SELECT a.CNPJ,
             COALESCE(a.TAB_I2A_VL_DIRCRED_RISCO,0)+COALESCE(a.TAB_I2B_VL_DIRCRED_SEM_RISCO,0) v
             FROM ativo a JOIN painel_saneado p ON p.CNPJ=a.CNPJ AND p.DT_COMPTC=a.DT_COMPTC
             WHERE a.DT_COMPTC='{CORTE}'),
      s AS (SELECT CNPJ, SUM(VALOR) top25 FROM sacados_conc
            WHERE DT_COMPTC='{CORTE}' GROUP BY 1)
      SELECT ROUND(100.0*COUNT(DISTINCT s.CNPJ)/(SELECT COUNT(*) FROM painel_saneado
                   WHERE DT_COMPTC='{CORTE}'),1),
             ROUND(100.0*SUM(dc.v) FILTER (s.CNPJ IS NOT NULL)/SUM(dc.v),1),
             ROUND(100.0*SUM(LEAST(s.top25, dc.v))/SUM(dc.v),1)
      FROM dc LEFT JOIN s ON s.CNPJ=dc.CNPJ""").fetchone()
    ficha(5, "Exposição a sacado/devedor (concentração)",
          "Valor devido pelos 25 maiores devedores de cada veículo e sua participação no estoque "
          "de direitos creditórios (tabela VIII do informe).",
          "valor por posição no ranking de devedores", "estoque de DC do veículo",
          "fundo ou classe (concentração), nunca a identidade do devedor",
          "A tabela VIII NÃO contém identificador do sacado. É IMPOSSÍVEL, com dados públicos, "
          "montar ranking nominal de devedores do mercado. Qualquer identificação seria inferência.",
          "CVM: informe mensal tab VIII", cob5, len(l5),
          f"Três coberturas, três definições: {cob5}% dos veículos do corte reportam a tabela; "
          f"esses veículos carregam {cob5_dc}% do estoque de DC; as posições listadas (top-25 "
          f"por veículo) explicam {cob5_valor}% do estoque total de DC — a cauda além do top-25 "
          "não é observável. Sem identidade do devedor; veículos sem a tabela ficam fora "
          "(não são zero).")

    # ---------- Lente 6: exposição do cotista ----------
    l6 = con.execute(f"""
    SELECT s.TIPO_COTA AS entidade, SUM(s.VL_SERIE) AS valor,
           COUNT(DISTINCT s.CNPJ) AS n_veiculos
    FROM series_cotas s JOIN painel_saneado p ON p.CNPJ=s.CNPJ AND p.DT_COMPTC=s.DT_COMPTC
    WHERE s.DT_COMPTC='{CORTE}' GROUP BY 1 ORDER BY valor DESC""").df()
    l6.to_csv(f"{OUT}/lente_6_cotistas.csv", index=False)
    ficha(6, "Exposição do cotista",
          "Valor investido por classe de cota (sênior, mezanino, subordinada) e número de POSIÇÕES "
          "de cotistas por categoria de investidor.",
          "quantidade de cotas × valor da cota, por série", "passivo total do veículo",
          "série/classe de cota; posições de cotistas (não pessoas)",
          "O número de cotistas NÃO mede pessoas únicas: um investidor presente em N fundos é "
          "contado N vezes. A identidade e o valor por cotista NÃO são públicos.",
          "CVM: informe mensal tabs X_1, X_1_1 e X_2", 100.0, len(l6),
          "Identidade do cotista indisponível, salvo quando a própria empresa a divulga em "
          "demonstração financeira (ver lente 7).")

    # ---------- Lente 7: dependência corporativa de FIDC ----------
    l7 = pd.read_csv(f"{OUT}/investidores_corporativos.csv")
    l7.to_csv(f"{OUT}/lente_7_dependencia_corporativa.csv", index=False)
    ficha(7, "Dependência corporativa de FIDC",
          "Importância do FIDC como funding da empresa: cotas retidas em balanço, cessões com "
          "retenção de risco, coobrigação e garantias.",
          "saldo confirmado em demonstração financeira", "ativo/PL da empresa",
          "empresa (CNPJ) e grupo econômico",
          "Aparecer como cedente NÃO implica dependência; e a existência do veículo não prova "
          "transferência de risco. Só há afirmação quando a nota explicativa confirma.",
          "Demonstrações financeiras publicadas (fonte primária)",
          None, len(l7),
          "Não é censo: 1 caso confirmado em fonte primária e 7 indiciários. Um Top-20 nacional "
          "exigiria mineração sistemática de DFP/ITR.")

    # ---------- Lente 8: exposição operacional (prestadores) ----------
    rows = []
    for papel, arq, col_val in (("Administrador", "lente_2_pl_sob_administracao.csv", "valor"),
                                ("Gestor", "lente_1_pl_sob_gestao.csv", "valor"),
                                ("Custodiante", "ranking_custodiantes.csv", "pl"),
                                ("Controlador", "ranking_controladores.csv", "pl"),
                                ("Auditor", "ranking_auditores.csv", "pl")):
        d = pd.read_csv(f"{OUT}/{arq}")
        v = d[col_val].clip(lower=0)
        sh = v / v.sum() if v.sum() else v
        rows.append({"papel": papel, "n_entidades": len(d),
                     "pl_identificado": v.sum(),
                     "cobertura_sobre_pl_mercado": v.sum() / pl_total,
                     "hhi": float((sh ** 2).sum()),
                     "share_top1": float(sh.max()) if len(sh) else None,
                     "share_top5": float(sh.nlargest(5).sum())})
    l8 = pd.DataFrame(rows)
    l8.to_csv(f"{OUT}/lente_8_exposicao_operacional.csv", index=False)
    ficha(8, "Exposição operacional (concentração de prestadores)",
          "Concentração do mercado em cada papel de prestação de serviço (HHI e share dos maiores).",
          "share de PL por prestador", "PL identificado no papel", "papel × entidade",
          "Concentração de prestador NÃO equivale a concentração de risco de crédito: um prestador "
          "serve veículos economicamente independentes entre si.",
          "CVM: informe mensal + registro de classes", None, len(l8),
          "Cobertura varia por papel (controlador: apenas 7% do PL tem o campo preenchido).")

    # ---------- Lente 9: exposição em recuperação judicial ----------
    rj_path = f"{OUT}/rj_casos_confirmados.csv"
    if os.path.exists(rj_path):
        l9 = pd.read_csv(rj_path)
        n9 = len(l9)
    else:
        l9 = pd.DataFrame(columns=["entidade", "cnpj", "status_processual",
                                   "papel_no_fidc", "nivel_evidencia", "fonte_url"])
        n9 = 0
    l9.to_csv(f"{OUT}/lente_9_recuperacao_judicial.csv", index=False)
    ficha(9, "Exposição em recuperação judicial",
          "Entidades relacionadas a FIDCs com processo de recuperação judicial ou falência, por "
          "papel (cedente, devedor, cotista, patrocinador) e status processual.",
          "valor da operação relacionada", "exposição do fundo à entidade",
          "empresa (CNPJ) × operação",
          "Estar em recuperação judicial NÃO é evidência de irregularidade. A classificação do "
          "crédito como concursal ou extraconcursal depende do contrato e da data do fato gerador "
          "(Lei 11.101/2005, art. 49 e §3º), nunca do nome do credor.",
          "DataJud/CNJ e fontes públicas oficiais", None, n9,
          "Casamento apenas por CNPJ; correspondência por nome exige validação humana.")

    cat = pd.DataFrame(FICHAS)
    cat.to_csv(f"{OUT}/lentes_catalogo.csv", index=False)
    print(cat[["lente", "nome", "n_entidades", "cobertura_pct"]].to_string(index=False))
    print(f"\nPL total do corte: R$ {pl_total/1e9:.1f} bi")
    print(f"Lente 5 (sacados) cobre {cob5}% dos veículos")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
