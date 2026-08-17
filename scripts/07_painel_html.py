#!/usr/bin/env python3
"""
Etapa 7 — Painel executivo (Entregável 5): gera relatorio/painel_executivo.html
a partir dos artefatos de data/analytic/. Autocontido (CSS/JS inline, SVG
gerado aqui), tema claro/escuro, tooltips e trilha de evidência por indicador.

Reprodução: python3 scripts/07_painel_html.py
"""
import json
import os
import sys

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "analytic")
DEST = os.path.join(ROOT, "relatorio", "painel_executivo.html")
CORTE = "2026-06-30"

C1, C2, C3 = "var(--s1)", "var(--s2)", "var(--s3)"


def fmt(v, dec=1):
    return f"{v:,.{dec}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def hbar_block(rows, unit="R$ bi", color=C1, maxw=560):
    """Lista de barras horizontais com rótulo e valor (hover via data-attrs)."""
    mx = max(v for _, v in rows)
    out = []
    for lbl, v in rows:
        w = max(0.5, v / mx * 100)
        out.append(
            f'<div class="hrow" data-tip="{lbl}: {fmt(v)} {unit}">'
            f'<div class="hlbl">{lbl}</div>'
            f'<div class="htrack"><div class="hfill" style="width:{w:.1f}%;background:{color}"></div></div>'
            f'<div class="hval">{fmt(v)}</div></div>')
    return "\n".join(out)


def main() -> int:
    s = pd.read_csv(f"{OUT}/serie_mercado_mensal.csv")
    c = s[s.DT_COMPTC == CORTE].iloc[0]
    adm = pd.read_csv(f"{OUT}/ranking_administradores.csv")
    ges = pd.read_csv(f"{OUT}/ranking_gestores.csv")
    seg = pd.read_csv(f"{OUT}/carteira_segmentos.csv")
    sub = pd.read_csv(f"{OUT}/subordinacao_agregada.csv")
    ag = pd.read_csv(f"{OUT}/inadimplencia_aging_serie.csv")
    scr = pd.read_csv(f"{OUT}/scr_rating_operacoes.csv", index_col=0).dropna()
    ced = pd.read_csv(f"{OUT}/cedentes_ranking_nomes.csv")
    tst = pd.read_csv(f"{OUT}/testes_auditoria.csv")
    prov = pd.read_csv(f"{OUT}/provisoes_reducao.csv").iloc[0]
    med = pd.read_csv(f"{OUT}/reconciliacao_medidas_fie.csv").iloc[0]
    cobc = pd.read_csv(f"{OUT}/cedentes_cobertura.csv").iloc[0]
    corp = pd.read_csv(f"{OUT}/investidores_corporativos.csv")
    jul = s.loc[s.DT_COMPTC == "2026-07-31"]
    detres = pd.read_csv(f"{OUT}/detentores_cda_resumo.csv").iloc[0]
    detg = pd.read_csv(f"{OUT}/detentores_cda_gestores.csv").dropna(subset=["gestor"])
    rfs = pd.read_csv(f"{OUT}/red_flags_regulatorios.csv")
    rf6 = pd.read_csv(f"{OUT}/red_flags_liquidacoes_bcb.csv")
    cbsf = pd.read_csv(f"{OUT}/cbsf_exreag_serie.csv")

    # ------- linha: PL nominal x real (mensal 2013-2026-06) -------
    ss = s[s.DT_COMPTC <= CORTE].reset_index(drop=True)
    W, H, PAD_L, PAD_B, PAD_T = 940, 280, 46, 26, 14
    ymax = max(ss.pl_total.max(), ss.pl_total_real_jun26.max()) / 1e9
    ymax = (int(ymax / 200) + 1) * 200
    n = len(ss)

    def xy(i, v):
        x = PAD_L + i / (n - 1) * (W - PAD_L - 8)
        y = PAD_T + (1 - v / ymax) * (H - PAD_T - PAD_B)
        return x, y

    def path(col):
        pts = [xy(i, v / 1e9) for i, v in enumerate(ss[col])]
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    grid, ylabels = [], []
    for gv in range(0, ymax + 1, 200):
        _, gy = xy(0, gv)
        grid.append(f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{W-8}" y2="{gy:.1f}" class="grid"/>')
        ylabels.append(f'<text x="{PAD_L-6}" y="{gy+4:.1f}" class="tick" text-anchor="end">{gv}</text>')
    xticks = []
    for yr in range(2013, 2027, 2):
        idx = ss.index[ss.DT_COMPTC.str.startswith(f"{yr}-01")]
        if len(idx):
            x, _ = xy(idx[0], 0)
            xticks.append(f'<text x="{x:.1f}" y="{H-8}" class="tick" text-anchor="middle">{yr}</text>')
    pts_json = json.dumps([
        {"m": d[:7], "n": round(p / 1e9, 1), "r": round(r / 1e9, 1)}
        for d, p, r in zip(ss.DT_COMPTC, ss.pl_total, ss.pl_total_real_jun26)])
    ex, ey = xy(n - 1, ss.pl_total.iloc[-1] / 1e9)
    line_svg = f'''
<svg viewBox="0 0 {W} {H}" id="plchart" role="img" aria-label="Evolução do patrimônio líquido de FIDCs, 2013 a 2026">
  {''.join(grid)}{''.join(ylabels)}{''.join(xticks)}
  <path d="{path('pl_total_real_jun26')}" class="lreal"/>
  <path d="{path('pl_total')}" class="lnom"/>
  <circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" class="endpt"/>
  <text x="{ex-6:.1f}" y="{max(ey-10,16):.1f}" class="endlbl" text-anchor="end">R$ {fmt(ss.pl_total.iloc[-1]/1e9,0)} bi</text>
  <line id="xhair" x1="0" y1="{PAD_T}" x2="0" y2="{H-PAD_B}" class="xhair" style="display:none"/>
</svg>
<script type="application/json" id="plpts">{pts_json}</script>'''

    # ------- blocos de barras -------
    sg = seg[(seg.DT_COMPTC == CORTE) & seg.valor.notna()].sort_values("valor", ascending=False)
    sg = sg[~sg.segmento.str.contains(r"\(total\)", na=False)]
    seg_rows = [(r.segmento, r.valor / 1e9) for r in sg.head(10).itertuples()]
    adm_rows = [(r.nome_admin.title()[:38], r.pl / 1e9) for r in adm.head(8).itertuples()]
    ges_rows = [(r.gestor.title()[:38], r.pl / 1e9) for r in ges.head(8).itertuples()]

    tot_sub = sub.valor.sum()
    sub_map = sub.set_index("TIPO_COTA").valor / tot_sub
    seg100 = ""
    x0 = 0.0
    for key, lbl, col in (("senior", "Sênior", C1), ("mezanino", "Mezanino", C2),
                          ("subordinada", "Subordinada", C3)):
        wv = float(sub_map.get(key, 0)) * 100
        seg100 += (f'<div class="stseg" style="left:{x0:.2f}%;width:{max(wv-0.3,0.3):.2f}%;'
                   f'background:{col}" data-tip="{lbl}: {wv:.1f}% (R$ {fmt(float(sub.set_index("TIPO_COTA").valor.get(key,0))/1e9,0)} bi)"></div>')
        x0 += wv

    r = ag[ag.DT_COMPTC == CORTE].iloc[0]
    dc = r.dc_com_risco + r.dc_sem_risco
    aging_rows = [("1–30 dias", (r.v_i30 + r.vi_i30) / dc * 100),
                  ("31–90 dias", (r.v_i31_90 + r.vi_i31_90) / dc * 100),
                  ("91–180 dias", (r.v_i91_180 + r.vi_i91_180) / dc * 100),
                  ("acima de 180 dias", (r.v_maior_180 + r.vi_maior_180) / dc * 100)]
    aging_html = hbar_block(aging_rows, unit="% dos DC", color=C2)

    scr_tot = scr.valor.sum()
    scr_order = ["AA", "A", "B", "C", "D", "E", "F", "G", "H"]
    scr_rows = [(f"Rating {k}", scr[scr.rating == k].valor.sum() / scr_tot * 100) for k in scr_order]
    scr_html = hbar_block([x for x in scr_rows if x[1] > 0.01], unit="%", color=C1)

    ced_rows = []
    for r2 in ced.head(10).itertuples():
        nome = (r2.razao_social or "—")
        ced_rows.append(f"<tr><td>{nome.title()}</td><td class='num'>{fmt(r2.exposicao_estimada/1e9)}</td>"
                        f"<td class='num'>{r2.n_veiculos}</td></tr>")

    chips = "".join(
        f'<span class="chip {"ok" if r3.status=="PASS" else "warn"}" data-tip="{r3.teste}: {r3.resultado}">'
        f'{r3.teste.split(" ")[0]}</span>' for r3 in tst.itertuples())

    tiles = [
        ("PL total", f"R$ {fmt(c.pl_total/1e9,0)} bi", "informes CVM, tab. IV · C001"),
        ("PL líquido de circularidade", f"R$ {fmt(c.pl_liquido_circular/1e9,0)} bi", "desconta cotas de FIDC intramercado · C004"),
        ("Veículos informantes", f"{int(c.n_veiculos):,}".replace(",", "."), "classes + fundos legado · C002"),
        ("Cotistas", f"{fmt(c.n_cotistas/1e3,0)} mil", "tab. X.1 · C007"),
        ("Inadimplência", f"{fmt((r.inad_com_risco+r.inad_sem_risco)/dc*100)}%", "parcelas vencidas / DC · C016"),
        ("Subordinação + mezanino", f"{fmt((1-float(sub_map.get('senior',0)))*100)}%", "tab. X.2 · C015"),
        ("Atraso provisionado", f"{fmt(prov.razao_reducao_sobre_inadimplencia*100)}%", "redução/recuperação ÷ inadimplência · C027"),
    ]
    tiles_html = "".join(
        f'<div class="tile"><div class="tlabel">{a}</div><div class="tvalue">{b}</div>'
        f'<div class="tsrc">{d}</div></div>' for a, b, d in tiles)

    jul_n = int(jul.n_veiculos.iloc[0]) if len(jul) else 0
    jul_pl = fmt(float(jul.pl_total.iloc[0]) / 1e9, 0) if len(jul) else "—"
    med_n = int(med.n_cnpjs_intersecao)
    med_cob = fmt(float(med.cobertura_medidas_sobre_pl_corte) * 100)
    # ---- supervisão: detentores, red flags, cluster ex-Reag ----
    detg_rows = [(g.gestor.title()[:36], g.vl_cotas_fidc / 1e9)
                 for g in detg.head(8).itertuples()]
    detentores_html = hbar_block(detg_rows, color=C2)

    RF_DESC = {
        "RF1": "inadimplência ~zero + cedente concentrado (perfil das fraudes de lastro)",
        "RF2": "recompras/substituições >15% da carteira em 12m (rolagem)",
        "RF3": "1-2 cotistas + interesse único + subordinação <5% (circuito fechado)",
        "RF4": "queda de PL >50% m/m (colapso)",
        "RF5": "crescimento >150% em 12m + cedente >=80% (expansão sem verificação)",
    }
    cnt = rfs.red_flag.str[:3].value_counts()
    rf_html = "".join(
        f'<div class="hrow" data-tip="{k}: {RF_DESC[k]}">'
        f'<div class="hlbl">{k} — {RF_DESC[k][:44]}…</div>'
        f'<div class="htrack"><div class="hfill" style="width:{cnt[k]/cnt.max()*100:.0f}%;background:{C3}"></div></div>'
        f'<div class="hval">{cnt[k]}</div></div>'
        for k in ["RF1", "RF2", "RF3", "RF4", "RF5"] if k in cnt)

    u6 = rf6[rf6.DT_COMPTC == CORTE]
    # sparkline CBSF (ex-Reag): PL administrado, jun/25..jul/26
    cb = cbsf[cbsf.m <= "2026-07"]
    W2, H2, P2 = 430, 110, 12
    mx = cb.pl.max()
    pts2 = [(P2 + i / (len(cb) - 1) * (W2 - 2 * P2),
             P2 + (1 - v / mx) * (H2 - 2 * P2 - 14)) for i, v in enumerate(cb.pl)]
    path2 = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts2)
    marcos = {"2025-08": "Carbono Oculto", "2026-01": "liquidação BCB"}
    marks = ""
    for i, mrow in enumerate(cb.itertuples()):
        if mrow.m in marcos:
            x, y = pts2[i]
            marks += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="endpt" '
                      f'style="fill:{C3}"/>'
                      f'<text x="{x:.1f}" y="{min(y+26, H2-4):.1f}" class="tick" '
                      f'text-anchor="middle">{marcos[mrow.m]}</text>')
    cbsf_svg = (f'<svg viewBox="0 0 {W2} {H2}" role="img" aria-label="PL administrado pela CBSF ex-Reag">'
                f'<path d="{path2}" class="lnom" style="stroke:{C3}"/>{marks}'
                f'<text x="{pts2[0][0]:.1f}" y="{pts2[0][1]-6:.1f}" class="tick" text-anchor="start">R$ {fmt(cb.pl.iloc[0]/1e9,0)} bi · {int(cb.n.iloc[0])} veículos</text>'
                f'<text x="{pts2[-2][0]:.1f}" y="{pts2[-2][1]-8:.1f}" class="tick" text-anchor="end">R$ {fmt(cb.pl.iloc[-2]/1e9,0)} bi · {int(cb.n.iloc[-2])}</text>'
                f'</svg>')

    casos_html = "".join(
        f"<tr><td>{a}</td><td>{b}</td><td>{c_}</td><td>{d}</td></tr>" for a, b, c_, d in [
        ("Reag / FIDC Gold Style", "2025-26", "carrossel de fundos; recursos sem origem (alegado)", "Operação Carbono Oculto; Reag Trust/CBSF liquidada pelo BCB"),
        ("Banco Master", "2025-26", "interconexão banco-fundos; 52-58 FIDCs afetados", "liquidação extrajudicial; investigações em curso"),
        ("Banco Cruzeiro do Sul", "2007-12", "320 mil consignados fictícios cedidos a FIDC cativo", "intervenção, liquidação e falência; denúncias MPF"),
        ("Silverado / Maximum", "2010s", "duplicatas sem lastro; cedentes ligados à gestora", "multas CVM de R$ 489,8 mi (2024)"),
        ("Trendbank Multisetorial", "2010s", "operações de crédito simuladas; notas frias", "denúncia FT Greenfield; multas CVM"),
        ("Union National", "2010s", "insolvência ocultada; falha de gatekeepers", "multas CVM a auditor e administrador"),
    ])

    corp_rows = []
    for rc in corp.itertuples():
        conf = str(rc.confianca)
        cls = "ok" if conf.startswith("Confirmado") else "warn"
        pos = str(rc.tipo_cota)
        if isinstance(rc.valor_cotas_rs_mil, float) and rc.valor_cotas_rs_mil == rc.valor_cotas_rs_mil:
            pos = f"R$ {fmt(rc.valor_cotas_rs_mil/1e3)} mi — {pos}"
        corp_rows.append(
            f"<tr><td>{rc.entidade}</td><td>{rc.periodo}</td>"
            f"<td style='max-width:420px'>{pos[:160]}</td>"
            f"<td><span class='chip {cls}'>{conf.split(' (')[0].split(';')[0]}</span></td></tr>")
    corp_html = "".join(corp_rows)
    html = f'''<title>Panorama FIDC Brasil</title>
<style>
:root {{
  --bg:#F5F5F1; --surface:#FFFFFF; --ink:#1B2430; --ink2:#57616E; --muted:#8A93A0;
  --grid:#E3E5DF; --line:#D6D9D2; --s1:#0E7A55; --s2:#4460C7; --s3:#B26312;
  --real:#9AA1AB; --ok:#0E7A55; --warnc:#B26312; --tipbg:#1B2430; --tipink:#F5F5F1;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#14171A; --surface:#1C2024; --ink:#E8EAED; --ink2:#A5ADB8; --muted:#7A828C;
  --grid:#2A2F35; --line:#333941; --s1:#17936A; --s2:#6478DC; --s3:#C0762C;
  --real:#6E7681; --ok:#17936A; --warnc:#C0762C; --tipbg:#E8EAED; --tipink:#14171A;
}} }}
:root[data-theme="dark"] {{
  --bg:#14171A; --surface:#1C2024; --ink:#E8EAED; --ink2:#A5ADB8; --muted:#7A828C;
  --grid:#2A2F35; --line:#333941; --s1:#17936A; --s2:#6478DC; --s3:#C0762C;
  --real:#6E7681; --ok:#17936A; --warnc:#C0762C; --tipbg:#E8EAED; --tipink:#14171A;
}}
* {{ box-sizing:border-box }}
body {{ background:var(--bg); color:var(--ink); margin:0;
  font:15px/1.55 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; }}
.wrap {{ max-width:1080px; margin:0 auto; padding:36px 24px 64px }}
header h1 {{ font-family:Georgia,"Times New Roman",serif; font-weight:400;
  font-size:34px; margin:0 0 4px; letter-spacing:-.01em; text-wrap:balance }}
.sub {{ color:var(--ink2); margin:0 0 8px }}
.meta {{ color:var(--muted); font-size:12.5px; text-transform:uppercase; letter-spacing:.06em }}
section {{ margin-top:40px }}
h2 {{ font-family:Georgia,serif; font-weight:400; font-size:22px; margin:0 0 4px }}
.note {{ color:var(--ink2); font-size:13px; margin:0 0 14px; max-width:70ch }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; margin-top:22px }}
.tile {{ background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:14px 16px }}
.tlabel {{ font-size:12px; color:var(--ink2); text-transform:uppercase; letter-spacing:.05em }}
.tvalue {{ font-size:24px; font-variant-numeric:tabular-nums; margin-top:2px }}
.tsrc {{ font-size:11px; color:var(--muted); margin-top:4px }}
.card {{ background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:18px 20px; overflow-x:auto }}
.grid {{ stroke:var(--grid); stroke-width:1 }}
.tick {{ fill:var(--muted); font-size:11px; font-variant-numeric:tabular-nums }}
.lnom {{ fill:none; stroke:var(--s1); stroke-width:2 }}
.lreal {{ fill:none; stroke:var(--real); stroke-width:2; stroke-dasharray:5 4 }}
.endpt {{ fill:var(--s1) }} .endlbl {{ fill:var(--ink); font-size:12px; font-variant-numeric:tabular-nums }}
.xhair {{ stroke:var(--muted); stroke-width:1; stroke-dasharray:2 3 }}
.legend {{ display:flex; gap:18px; font-size:13px; color:var(--ink2); margin-top:8px; flex-wrap:wrap }}
.sw {{ display:inline-block; width:14px; height:3px; vertical-align:middle; margin-right:6px; border-radius:2px }}
.cols {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px }}
.hrow {{ display:grid; grid-template-columns:minmax(120px,220px) 1fr 64px; gap:10px; align-items:center; padding:3px 0 }}
.hlbl {{ font-size:13px; color:var(--ink2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis }}
.htrack {{ background:var(--grid); border-radius:4px; height:14px }}
.hfill {{ height:14px; border-radius:4px }}
.hval {{ font-size:13px; text-align:right; font-variant-numeric:tabular-nums }}
.stack {{ position:relative; height:26px; border-radius:5px; overflow:hidden; background:var(--grid) }}
.stseg {{ position:absolute; top:0; height:26px }}
table {{ border-collapse:collapse; width:100%; font-size:14px }}
th {{ text-align:left; color:var(--ink2); font-size:12px; text-transform:uppercase;
  letter-spacing:.05em; border-bottom:1px solid var(--line); padding:6px 8px }}
td {{ border-bottom:1px solid var(--grid); padding:7px 8px }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums }}
.chip {{ display:inline-block; font-size:12px; padding:3px 10px; border-radius:99px; margin:3px 4px 0 0;
  border:1px solid var(--line); font-variant-numeric:tabular-nums }}
.chip.ok {{ color:var(--ok); border-color:var(--ok) }}
.chip.warn {{ color:var(--warnc); border-color:var(--warnc) }}
.badge {{ font-size:11px; color:var(--warnc); border:1px solid var(--warnc); padding:1px 8px; border-radius:99px }}
#tip {{ position:fixed; display:none; background:var(--tipbg); color:var(--tipink); font-size:12.5px;
  padding:6px 10px; border-radius:5px; pointer-events:none; max-width:320px; z-index:10;
  font-variant-numeric:tabular-nums }}
details.explain {{ margin-top:12px; border:1px solid var(--line); border-radius:6px;
  background:var(--surface); padding:0 16px }}
details.explain summary {{ cursor:pointer; padding:11px 0; font-size:13.5px; color:var(--ink2);
  font-weight:600; list-style-position:inside }}
details.explain[open] summary {{ border-bottom:1px solid var(--grid) }}
details.explain .body {{ padding:12px 2px 16px; font-size:13.5px; color:var(--ink2); max-width:88ch }}
details.explain .body p {{ margin:0 0 10px }}
details.explain .body strong {{ color:var(--ink) }}
details.explain .body ul {{ margin:0 0 10px; padding-left:20px }}
details.explain .body li {{ margin-bottom:6px }}
footer {{ margin-top:48px; color:var(--muted); font-size:12.5px; max-width:80ch }}
a {{ color:var(--s2) }}
@media (prefers-reduced-motion: no-preference) {{ .hfill {{ transition:width .5s ease }} }}
</style>
<div class="wrap">
<header>
  <div class="meta">Mercado brasileiro de fundos de investimento em direitos creditórios</div>
  <h1>Panorama FIDC Brasil</h1>
  <p class="sub">Data-base 30/06/2026 · fontes primárias CVM (Dados Abertos) · cada indicador
  referencia o campo de origem e o claim do livro de evidências (C0xx)</p>
</header>

<div class="tiles">{tiles_html}</div>

<section>
  <h2>Evolução do patrimônio líquido</h2>
  <p class="note">Painel canônico deduplicado (fundo × classe). Série real deflacionada pelo
  IPCA (base jun/2026). R$ bilhões. A competência de jul/2026, ainda em janela de
  entrega (JULN informantes; R$ JULPL bi), não integra a série do corte. O PL do corte
  reconcilia com a base Medidas CVM/FIE com diferença zero em MEDN CNPJs
  (MEDCOB% do PL) — teste T16.</p>
  <div class="card">{line_svg}
  <div class="legend"><span><span class="sw" style="background:var(--s1)"></span>PL nominal</span>
  <span><span class="sw" style="background:var(--real)"></span>PL real (IPCA, base jun/26)</span></div></div>
</section>

<section>
  <h2>Carteira por segmento</h2>
  <p class="note">Dez maiores segmentos dos direitos creditórios (informe mensal, tabela II,
  subitens sem subtotais). R$ bilhões.</p>
  <div class="card">{hbar_block(seg_rows)}</div>
</section>

<section>
  <h2>Quem administra e quem gere</h2>
  <p class="note">PL por administrador fiduciário (informe, tab. I) e por gestor (registro CVM,
  registro ativo mais recente por fundo). Cobertura de 100% do PL nos dois rankings. R$ bilhões.
  Rankings brutos de circularidade: nos veículos administrados pelo BTG, 31% do PL são cotas de
  outros FIDCs do universo (QI: 21%) — líquidos disso, BTG e QI empatam.</p>
  <div class="cols">
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Administradores — top 8 (52,6% do PL nos 5 primeiros)</h3>{hbar_block(adm_rows)}</div>
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Gestores — top 8 (24,1% nos 5 primeiros)</h3>{hbar_block(ges_rows, color=C2)}</div>
  </div>
</section>

<section>
  <h2>Estrutura de capital</h2>
  <p class="note">Valor das séries de cotas (tab. X.2): quem absorve a primeira perda.</p>
  <div class="card"><div class="stack">{seg100}</div>
  <div class="legend">
    <span><span class="sw" style="background:var(--s1)"></span>Sênior {fmt(float(sub_map.get("senior",0))*100)}%</span>
    <span><span class="sw" style="background:var(--s2)"></span>Mezanino {fmt(float(sub_map.get("mezanino",0))*100)}%</span>
    <span><span class="sw" style="background:var(--s3)"></span>Subordinada {fmt(float(sub_map.get("subordinada",0))*100)}%</span>
  </div></div>
</section>

<section>
  <h2>Qualidade de crédito</h2>
  <div class="cols">
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Atraso (parcelas vencidas, % dos DC) — 97,9% provisionado</h3>{aging_html}</div>
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Classificação SCR das operações (%) — cobre 51% do estoque</h3>{scr_html}</div>
  </div>
</section>

<section>
  <h2>Maiores cedentes identificados <span class="badge">estimativa-piso</span></h2>
  <p class="note">CNPJs declarados nos informes (9 maiores cedentes por veículo) × % × bucket de
  DC; razão social pela base pública do CNPJ. Os percentuais declarados cobrem 29,4% do estoque
  de DCs — o ranking identifica a cabeça da distribuição, não o censo. Estoque atribuído ≠ fluxo
  cedido no período.</p>
  <div class="card"><table>
    <thead><tr><th>Cedente</th><th style="text-align:right">Exposição est. (R$ bi)</th><th style="text-align:right">Veículos</th></tr></thead>
    <tbody>{''.join(ced_rows)}</tbody>
  </table></div>
</section>

<section>
  <h2>Cotas de FIDC em balanços corporativos <span class="badge">não exaustivo</span></h2>
  <p class="note">Par 6 do mandato, execução parcial: um caso confirmado por leitura direta da
  demonstração financeira; demais posições identificadas por análise externa aguardam
  verificação nas notas explicativas originais.</p>
  <div class="card"><table>
    <thead><tr><th>Entidade</th><th>Período</th><th>Posição</th><th>Confiança</th></tr></thead>
    <tbody>{corp_html}</tbody>
  </table></div>
</section>

<section>
  <h2>Supervisão e integridade</h2>
  <p class="note">Visão de regulador. Red flag é sinal estatístico de atenção — não imputação de
  irregularidade; a liquidação de um prestador não implica ilicitude dos fundos servidos
  (patrimônios segregados). Dossiê completo com fontes em
  <code>auditoria/casos_uso_indevido_fidc.md</code>.</p>
  <div class="tiles" style="margin-top:0">
    <div class="tile"><div class="tlabel">Cotas de FIDC em fundos não-FIDC</div>
      <div class="tvalue">R$ {fmt(detres.vl_detido_por_nao_fidc/1e9,0)} bi</div>
      <div class="tsrc">CDA jun/26 · {f"{int(detres.n_fundos_investidores):,}".replace(",", ".")} fundos · C029</div></div>
    <div class="tile"><div class="tlabel">Posições "emissor ligado"</div>
      <div class="tvalue">R$ {fmt(detres.vl_posicoes_emissor_ligado/1e9,0)} bi</div>
      <div class="tsrc">{fmt(detres.vl_posicoes_emissor_ligado/detres.vl_detido_por_nao_fidc*100,0)}% da detenção via fundos · C030</div></div>
    <div class="tile"><div class="tlabel">Ecossistema ex-Reag no corte</div>
      <div class="tvalue">R$ {fmt(u6.VL_PL.sum()/1e9,1)} bi</div>
      <div class="tsrc">{u6.CNPJ.nunique()} CNPJs (busca nominal) · C031</div></div>
  </div>
  <details class="explain"><summary>Como ler estes três números</summary><div class="body">
    <p>Juntos, os cartões respondem à pergunta central de um supervisor: <strong>se um FIDC
    quebrar, quem sente — e por qual canal?</strong></p>
    <p><strong>R$ {fmt(detres.vl_detido_por_nao_fidc/1e9,0)} bi em fundos não-FIDC</strong> medem
    a distância que o risco viaja. São fundos DI, renda fixa e multimercados — produtos de
    varejo — que carregam cotas de FIDC na carteira. Um problema de lastro chega ao
    correntista comum em dois passos (FIDC → fundo → cotista), o mesmo mecanismo de
    empacotamento que amplificou a crise de 2008. Em 2013 esse canal era irrelevante; hoje
    conecta a securitização à poupança popular.</p>
    <p><strong>R$ {fmt(detres.vl_posicoes_emissor_ligado/1e9,0)} bi como "emissor ligado"
    ({fmt(detres.vl_posicoes_emissor_ligado/detres.vl_detido_por_nao_fidc*100,0)}%)</strong> medem
    quanto dessa detenção circula dentro do próprio grupo que estrutura o FIDC — o campo
    EMISSOR_LIGADO é declarado à CVM pelo próprio administrador. Quando quem compra a cota
    é o grupo que a criou, desaparece a verificação independente de lastro e preço, e é o
    mesmo grupo que marca o valor da cota que precisa que ela não caia. Não é ilegal — é
    assim que tesourarias de conglomerado operam — mas é o terreno comum a praticamente
    todos os casos de fraude documentados (Silverado, Cruzeiro do Sul, Reag): circuito
    fechado entre cedente, gestor e cotista.</p>
    <p><strong>R$ {fmt(u6.VL_PL.sum()/1e9,1)} bi do ecossistema ex-Reag</strong> são o risco
    materializado: veículos ligados a um grupo cuja administradora (CBSF, ex-Reag Trust) era
    a 7ª maior do mercado quando foi liquidada pelo BCB. A lição é dupla: contágio por
    prestador comum atinge também os fundos idôneos (no caso Master, 52-58 FIDCs ficaram
    sem administrador de uma vez), e os sinais eram visíveis nos dados públicos meses antes
    das manchetes — a queda de 33% no PL administrado aparecia no ranking. Ressalva
    obrigatória: patrimônio de fundo é segregado do prestador; estar nesta lista não imputa
    ilicitude a nenhum veículo.</p>
  </div></details>
  <div class="cols" style="margin-top:16px">
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Maiores gestores detentores de cotas de FIDC (CDA, R$ bi)</h3>{detentores_html}</div>
    <div class="card"><h3 style="margin:0 0 6px;font-size:15px">CBSF DTVM (ex-Reag Trust) — PL administrado</h3>
      <p class="note" style="margin:0 0 6px">7ª maior administradora no corte, em liquidação extrajudicial (BCB, 15/01/2026); migração dos veículos praticamente completa em jul/26.</p>
      {cbsf_svg}</div>
  </div>
  <div class="cols" style="margin-top:16px">
    <div class="card"><h3 style="margin:0 0 10px;font-size:15px">Triagem de red flags (nº de veículos por padrão)</h3>{rf_html}
      <details class="explain" style="margin-top:12px"><summary>O que cada red flag significa</summary><div class="body">
      <ul>
        <li><strong>RF1 — inadimplência ~zero com cedente concentrado.</strong> Carteira grande,
        um cedente dominante e atraso praticamente nulo. Parece virtude, mas é a assinatura
        das fraudes de lastro: crédito inventado não atrasa — no Cruzeiro do Sul, os 320 mil
        consignados fictícios eram "adimplentes perfeitos" até a intervenção. Adimplência
        realista tem ruído; perfeição prolongada merece inspeção do lastro.</li>
        <li><strong>RF2 — recompras e substituições acima de 15% da carteira em 12 meses.</strong>
        O cedente recomprar ou trocar créditos antes do vencimento pode ser gestão comercial
        legítima — ou rolagem: o crédito prestes a vencer some da carteira antes de virar
        atraso, e a inadimplência publicada fica artificialmente baixa. Volume alto e
        recorrente transfere a dúvida para o administrador demonstrar a substância.</li>
        <li><strong>RF3 — um ou dois cotistas, interesse único e subordinação abaixo de 5%.</strong>
        Estrutura fechada: quem cede, quem gere e quem investe são o mesmo interesse
        econômico, e quase não há capital subordinado absorvendo primeira perda. Sem
        investidor externo, ninguém independente valida preço nem lastro. Captura FIDCs
        cativos de tesouraria legítimos — por isso é sinal de atenção, não veredito — mas
        foi o desenho usado em todos os grandes casos.</li>
        <li><strong>RF4 — queda de patrimônio superior a 50% em um mês.</strong> Colapsos não
        avisam: a cota fica estável por anos (marcação controlada) e reprecifica de uma vez,
        como nos FIDCs Maximum da Silverado. Quedas abruptas também identificam resgates em
        massa de cotista único — em ambos os casos, o evento merece autópsia.</li>
        <li><strong>RF5 — crescimento acima de 150% em 12 meses com cedente ≥80%.</strong>
        Expansão explosiva alimentada por um único originador, sem diversificação. É o perfil
        de esquemas em carrossel e pirâmides de recebíveis (a acusação no caso Reag), em que
        o crescimento da captação é a própria fonte de pagamento das cotas antigas. Crescimento
        rápido exige due diligence proporcional do lastro novo.</li>
      </ul>
      <p>Método: cada padrão foi extraído dos casos documentados ao lado e aplicado aos 4.327
      veículos do corte. Os limiares são deliberadamente conservadores; falsos positivos são
      esperados e aceitáveis — o objetivo é priorizar inspeção, não acusar. A interseção de
      dois ou mais padrões no mesmo veículo é o critério natural de escalonamento.</p>
      </div></details>
      <p class="note" style="margin:10px 0 0">Tipologia derivada dos casos documentados; listas nominais em <code>red_flags_regulatorios.csv</code>.</p></div>
    <div class="card" style="overflow-x:auto"><h3 style="margin:0 0 10px;font-size:15px">Casos documentados</h3>
      <table><thead><tr><th>Caso</th><th>Anos</th><th>Mecanismo</th><th>Desfecho</th></tr></thead>
      <tbody>{casos_html}</tbody></table></div>
  </div>
</section>

<section>
  <h2>Auditoria</h2>
  <p class="note">18 testes obrigatórios executados sobre a base publicada — verde = aprovado,
  âmbar = ressalva documentada. Detalhes em <code>data/analytic/testes_auditoria.csv</code>.</p>
  <div class="card">{chips}<span class="chip ok" data-tip="T16 Informe x Medidas CVM/FIE: diferença zero em MEDN CNPJs (MEDCOB% do PL)">T16</span></div>
</section>

<footer>
Produzido a partir dos informes mensais de FIDC e do registro de fundos da CVM
(dados.cvm.gov.br), com manifesto de extração (URL + SHA-256) e pipeline
reproduzível. Valores em R$ correntes, salvo indicação. Estimativas e limitações
descritas na metodologia. Divergência com o perímetro ANBIMA (+17,2%) documentada
no teste T14. Este painel não constitui recomendação de investimento.
</footer>
</div>
<div id="tip" role="status"></div>
<script>
(function () {{
  var tip = document.getElementById('tip');
  function show(t, x, y) {{ tip.textContent = t; tip.style.display = 'block';
    tip.style.left = Math.min(x + 14, innerWidth - 330) + 'px'; tip.style.top = (y + 14) + 'px'; }}
  function hide() {{ tip.style.display = 'none'; }}
  document.querySelectorAll('[data-tip]').forEach(function (el) {{
    el.addEventListener('mousemove', function (e) {{ show(el.dataset.tip, e.clientX, e.clientY); }});
    el.addEventListener('mouseleave', hide);
  }});
  var svg = document.getElementById('plchart');
  var pts = JSON.parse(document.getElementById('plpts').textContent);
  var xh = document.getElementById('xhair');
  if (svg) svg.addEventListener('mousemove', function (e) {{
    var r = svg.getBoundingClientRect();
    var fx = (e.clientX - r.left) / r.width * 940;
    var i = Math.round((fx - 46) / (940 - 46 - 8) * (pts.length - 1));
    if (i < 0 || i >= pts.length) {{ hide(); xh.style.display = 'none'; return; }}
    var x = 46 + i / (pts.length - 1) * (940 - 46 - 8);
    xh.setAttribute('x1', x); xh.setAttribute('x2', x); xh.style.display = 'block';
    show(pts[i].m + ' · nominal R$ ' + pts[i].n.toLocaleString('pt-BR') +
         ' bi · real R$ ' + pts[i].r.toLocaleString('pt-BR') + ' bi', e.clientX, e.clientY);
  }});
  if (svg) svg.addEventListener('mouseleave', function () {{ hide(); xh.style.display = 'none'; }});
}})();
</script>'''
    html = (html.replace("JULN", f"{jul_n:,}".replace(",", "."))
                .replace("JULPL", jul_pl)
                .replace("MEDN", f"{med_n:,}".replace(",", "."))
                .replace("MEDCOB", med_cob))
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(html)
    print("painel gerado:", DEST, len(html), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
