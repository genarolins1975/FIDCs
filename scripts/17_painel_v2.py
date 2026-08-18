#!/usr/bin/env python3
"""
Etapa 17 — Painel v2 (reconstrução).

Renderiza relatorio/painel_fidc_v2.html a partir de data/analytic/painel_dados.json.

Regra estruturante (achado crítico nº 4 da auditoria): este arquivo NÃO contém
nenhum número do domínio. Todo valor exibido é lido do JSON em tempo de
renderização no navegador, e cada número abre a gaveta de evidências com
fórmula, fonte, campo, cobertura, status e nível de confiança.

Telas: 1 Agora · 2 Anatomia · 3 Exposição (9 lentes) · 4 Supervisão ·
       5 Judicial e regulatório · 6 Auditoria e método.

Reprodução: python3 scripts/17_painel_v2.py
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(ROOT, "data", "analytic", "painel_dados.json")
DEST = os.path.join(ROOT, "relatorio", "painel_fidc_v2.html")

CSS = """
:root{
  --bg:#F4F4F0; --surface:#FFF; --surface2:#FAFAF7; --ink:#181F27; --ink2:#525C68;
  --muted:#8A929C; --line:#DFE1DA; --grid:#E9EAE4;
  --s1:#0E7A55; --s2:#4460C7; --s3:#B26312; --s4:#7A5AA8;
  --ok:#0E7A55; --warn:#B26312; --crit:#A32C2C; --neutral:#6E7681;
  --tipbg:#181F27; --tipink:#F4F4F0;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#13161A; --surface:#1B1F24; --surface2:#20252B; --ink:#E9EBEE; --ink2:#A8B0BA;
  --muted:#79818B; --line:#313841; --grid:#282E35;
  --s1:#17936A; --s2:#6478DC; --s3:#C0762C; --s4:#9C7FC7;
  --ok:#17936A; --warn:#C0762C; --crit:#D45E5E; --neutral:#79818B;
  --tipbg:#E9EBEE; --tipink:#13161A;
}}
:root[data-theme="dark"]{
  --bg:#13161A; --surface:#1B1F24; --surface2:#20252B; --ink:#E9EBEE; --ink2:#A8B0BA;
  --muted:#79818B; --line:#313841; --grid:#282E35;
  --s1:#17936A; --s2:#6478DC; --s3:#C0762C; --s4:#9C7FC7;
  --ok:#17936A; --warn:#C0762C; --crit:#D45E5E; --neutral:#79818B;
  --tipbg:#E9EBEE; --tipink:#13161A;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1140px;margin:0 auto;padding:28px 22px 80px}
header .eyebrow{font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:33px;
  margin:6px 0 4px;letter-spacing:-.01em}
.sub{color:var(--ink2);margin:0;font-size:14px;max-width:80ch}
nav{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);
  margin:22px -22px 0;padding:0 22px;display:flex;gap:2px;overflow-x:auto}
nav button{background:none;border:none;border-bottom:2px solid transparent;color:var(--ink2);
  font:inherit;font-size:14px;padding:11px 13px;cursor:pointer;white-space:nowrap}
nav button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--s1);font-weight:600}
nav button:focus-visible{outline:2px solid var(--s2);outline-offset:-2px}
section[role=tabpanel]{padding-top:24px}
section[hidden]{display:none}
h2{font-family:Georgia,serif;font-weight:400;font-size:21px;margin:30px 0 4px}
h2:first-child{margin-top:0}
h3{font-size:14.5px;margin:0 0 10px;font-weight:600}
.note{color:var(--ink2);font-size:13px;margin:0 0 14px;max-width:82ch}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:10px;margin:16px 0}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:7px;padding:14px 15px}
.tile .lab{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink2)}
.tile .val{font-size:25px;margin-top:3px;font-variant-numeric:tabular-nums}
.tile .src{font-size:11px;color:var(--muted);margin-top:5px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:7px;padding:17px 19px;
  overflow-x:auto}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:15px}
.ev{cursor:pointer;border-bottom:1px dotted var(--muted);text-decoration:none;color:inherit}
.ev:hover{border-bottom-style:solid;background:var(--surface2)}
.ev:focus-visible{outline:2px solid var(--s2);outline-offset:2px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;
  color:var(--ink2);border-bottom:1px solid var(--line);padding:7px 9px;position:sticky;top:0;
  background:var(--surface)}
td{border-bottom:1px solid var(--grid);padding:7px 9px;vertical-align:top}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tbody tr:hover{background:var(--surface2)}
.bar{height:13px;border-radius:3px;background:var(--grid);position:relative;min-width:60px}
.bar>i{display:block;height:13px;border-radius:3px;background:var(--s1)}
.chip{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:99px;
  border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.chip.ok{color:var(--ok);border-color:var(--ok)}
.chip.warn{color:var(--warn);border-color:var(--warn)}
.chip.crit{color:var(--crit);border-color:var(--crit)}
.chip.na{color:var(--neutral);border-color:var(--neutral)}
.toolbar{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin:0 0 13px}
input[type=search],select{font:inherit;font-size:13.5px;padding:7px 10px;border:1px solid var(--line);
  border-radius:6px;background:var(--surface);color:var(--ink);min-width:190px}
button.act{font:inherit;font-size:13px;padding:7px 12px;border:1px solid var(--line);
  border-radius:6px;background:var(--surface);color:var(--ink2);cursor:pointer}
button.act:hover{border-color:var(--s2);color:var(--ink)}
details.explain{border:1px solid var(--line);border-radius:7px;background:var(--surface);
  padding:0 15px;margin:12px 0}
details.explain summary{cursor:pointer;padding:11px 0;font-size:13.5px;color:var(--ink2);
  font-weight:600}
details.explain[open] summary{border-bottom:1px solid var(--grid)}
details.explain .b{padding:12px 2px 15px;font-size:13.5px;color:var(--ink2);max-width:86ch}
details.explain .b p{margin:0 0 9px}
details.explain .b strong{color:var(--ink)}
.warnbox{border-left:3px solid var(--warn);background:var(--surface2);padding:11px 14px;
  font-size:13px;color:var(--ink2);border-radius:0 6px 6px 0;margin:12px 0;max-width:86ch}
dialog{border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--ink);
  padding:0;max-width:640px;width:92vw;box-shadow:0 18px 50px rgba(0,0,0,.28)}
dialog::backdrop{background:rgba(0,0,0,.45)}
dialog .head{padding:16px 20px 12px;border-bottom:1px solid var(--line);display:flex;
  justify-content:space-between;gap:14px;align-items:flex-start}
dialog .head h4{margin:0;font-size:16px;font-family:Georgia,serif;font-weight:400}
dialog .body{padding:14px 20px 20px;font-size:13.5px}
dialog dl{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin:0}
dialog dt{color:var(--ink2);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
dialog dd{margin:0;word-break:break-word}
dialog .close{background:none;border:none;color:var(--ink2);font-size:22px;cursor:pointer;
  line-height:1;padding:0 2px}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--ink2);font-size:12.5px;max-width:88ch}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
@media (prefers-reduced-motion:no-preference){.bar>i{transition:width .45s ease}}
"""

JS = r"""
const D = window.__FIDC__;
const nf = new Intl.NumberFormat('pt-BR');
function fmtVal(v, unidade, dec){
  if(v===null||v===undefined) return '—';
  if(unidade==='R$'){
    if(v===0) return 'R$ 0 (reportado)';
    const bi = v/1e9;
    if(Math.abs(bi)>=1) return 'R$ '+nf.format(+bi.toFixed(dec??1))+' bi';
    if(Math.abs(v)>=1e6) return 'R$ '+nf.format(+(v/1e6).toFixed(1))+' mi';
    return 'R$ '+nf.format(+(v/1e3).toFixed(1))+' mil';
  }
  if(unidade==='%') return nf.format(+(v*100).toFixed(dec??1))+'%';
  return nf.format(+v.toFixed(dec??0));
}
function ind(key){ return D.indicadores[key] || null; }
// número com gaveta de evidência
function ev(key, dec){
  const i = ind(key);
  if(!i) return '<span class="mono">—</span>';
  return `<a class="ev" tabindex="0" role="button" data-ev="${key}">${fmtVal(i.valor,i.unidade,dec)}</a>`;
}
function tile(key, dec){
  const i = ind(key);
  if(!i) return '';
  return `<div class="tile"><div class="lab">${i.rotulo}</div>
    <div class="val">${ev(key,dec)}</div>
    <div class="src">${i.campo} · ${i.status}${i.claim? ' · '+i.claim : ''}</div></div>`;
}
function openEv(key){
  const i = ind(key); if(!i) return;
  const dlg = document.getElementById('evd');
  document.getElementById('evtitle').textContent = i.rotulo;
  const rows = [
    ['Valor exato', i.valor===null? 'não disponível' : nf.format(i.valor)+' '+(i.unidade==='%'?'(fração)':i.unidade)],
    ['Fórmula', i.formula],
    ['Fonte', i.fonte],
    ['Tabela / campo', i.campo],
    ['Data-base', i.data_base],
    ['Extração', i.data_extracao],
    ['Status', i.status],
    ['Nível de confiança', i.confianca],
    ['Cobertura', i.cobertura===null||i.cobertura===undefined? 'não aplicável' : nf.format(i.cobertura)+'%'],
    ['Observação', i.obs || '—'],
    ['Claim', i.claim || '—'],
  ];
  document.getElementById('evbody').innerHTML =
    '<dl>'+rows.map(r=>`<dt>${r[0]}</dt><dd>${r[1]}</dd>`).join('')+'</dl>';
  dlg.showModal();
}
// tabelas
function isNum(v){ return typeof v === 'number' && isFinite(v); }
// A unidade de cada coluna é DECLARADA no JSON. Nunca inferida da magnitude:
// adivinhar escala produziu erro de 100x na versão anterior.
function cellFmt(col, v, unidade){
  if(v===null||v===undefined||v==='') return '—';
  if(!isNum(v)) return String(v);
  switch(unidade){
    case 'brl':   return fmtVal(v,'R$');
    case 'fracao':return nf.format(+(v*100).toFixed(1))+'%';
    case 'pct100':return nf.format(+v.toFixed(1))+'%';
    case 'indice':return nf.format(+v.toFixed(4));
    case 'int':   return nf.format(Math.round(v));
    default:      return nf.format(+v.toFixed(2));
  }
}
function renderTable(key, mount, opts){
  const t = D.tabelas[key]; const el = document.getElementById(mount);
  if(!t || !t.linhas.length){ el.innerHTML = '<p class="note">Sem dados disponíveis nesta versão.</p>'; return; }
  const o = opts||{}; const barCol = o.bar ? t.colunas.indexOf(o.bar) : -1;
  let max = 1;
  if(barCol>=0) max = Math.max(...t.linhas.map(r=>isNum(r[barCol])?r[barCol]:0)) || 1;
  const un = t.unidades || t.colunas.map(()=> 'auto');
  const head = t.colunas.map((c,i)=>`<th class="${['brl','fracao','pct100','indice','int'].includes(un[i])?'num':''}">${c.replace(/_/g,' ')}</th>`).join('');
  const body = t.linhas.map(r=>{
    const tds = r.map((v,ix)=>{
      const col = t.colunas[ix], u = un[ix];
      if(ix===barCol && isNum(v)){
        return `<td class="num">${cellFmt(col,v,u)}<div class="bar"><i style="width:${Math.max(2,100*v/max)}%"></i></div></td>`;
      }
      return `<td class="${isNum(v)&&u!=='auto'?'num':''}">${cellFmt(col,v,u)}</td>`;
    }).join('');
    return `<tr data-row="${r.join(' ').toLowerCase()}">${tds}</tr>`;
  }).join('');
  el.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
    + (t.nota? `<p class="note" style="margin:11px 0 0">${t.nota}</p>`:'')
    + `<p class="note mono" style="margin:6px 0 0">fonte: ${t.fonte} · ${t.campo}</p>`;
}
function filterTables(q){
  q = (q||'').trim().toLowerCase();
  document.querySelectorAll('tbody tr[data-row]').forEach(tr=>{
    tr.hidden = q && !tr.dataset.row.includes(q);
  });
}
function copyTable(key){
  const t = D.tabelas[key]; if(!t) return;
  const csv = [t.colunas.join(';')]
    .concat(['# unidades: '+(t.unidades||[]).join(';')])
    .concat(t.linhas.map(r=>r.map(v=>v===null?'':v).join(';'))).join('\n');
  navigator.clipboard.writeText(csv).then(()=>{
    const b = document.querySelector(`[data-copy="${key}"]`);
    if(b){ const o=b.textContent; b.textContent='copiado'; setTimeout(()=>b.textContent=o,1400); }
  });
}
// navegação
function showTab(id){
  document.querySelectorAll('nav button').forEach(b=>{
    const on = b.dataset.tab===id; b.setAttribute('aria-selected', on?'true':'false');
  });
  document.querySelectorAll('section[role=tabpanel]').forEach(s=>{ s.hidden = s.id!==id; });
  history.replaceState(null,'','#'+id);
  window.scrollTo({top:0,behavior:'instant'});
}
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-ev]'); if(a){ openEv(a.dataset.ev); return; }
  const b = e.target.closest('[data-tab]'); if(b){ showTab(b.dataset.tab); return; }
  const cp = e.target.closest('[data-copy]'); if(cp){ copyTable(cp.dataset.copy); return; }
  if(e.target.id==='evclose'){ document.getElementById('evd').close(); }
});
document.addEventListener('keydown', e=>{
  const el = e.target.closest ? e.target.closest('[data-ev]') : null;
  if((e.key==='Enter' || e.key===' ') && el){ e.preventDefault(); openEv(el.dataset.ev); }
});
"""


def main() -> int:
    with open(SRC, encoding="utf-8") as f:
        dados = json.load(f)
    # resultado da verificação de fórmulas (etapa 20) entra como tabela do payload
    vpath = os.path.join(ROOT, "data", "analytic", "verificacao_formulas.csv")
    if os.path.exists(vpath):
        import csv
        with open(vpath, encoding="utf-8") as vf:
            rd = list(csv.reader(vf))
        dados["tabelas"]["verificacao"] = dict(
            rotulo="Verificação automática de fórmulas",
            fonte="execução própria (scripts/20_teste_formulas.py)",
            campo="verificacao_formulas.csv", nota=None, colunas=rd[0],
            unidades=["auto"] * len(rd[0]),
            linhas=[[None if v == "" else v for v in r] for r in rd[1:]])
    payload = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))

    body = """<title>Panorama FIDC Brasil</title>
<style>__CSS__</style>
<div class="wrap">
<header>
  <div class="eyebrow">Mercado brasileiro de fundos de investimento em direitos creditórios</div>
  <h1>Panorama FIDC Brasil</h1>
  <p class="sub">Ferramenta de leitura e supervisão construída sobre fontes primárias da CVM.
  Cada indicador desta página abre, ao clique, a gaveta de evidência que o sustenta — fórmula,
  tabela de origem, cobertura, status e nível de confiança; as tabelas declaram fonte e unidade
  por coluna, e todo valor publicado passa por verificação automática de fórmula contra os
  arquivos de origem.</p>
</header>

<nav role="tablist" aria-label="Seções">
  <button data-tab="t1" role="tab" aria-selected="true">1 · Agora</button>
  <button data-tab="t2" role="tab" aria-selected="false">2 · Anatomia</button>
  <button data-tab="t3" role="tab" aria-selected="false">3 · Exposição</button>
  <button data-tab="t4" role="tab" aria-selected="false">4 · Supervisão</button>
  <button data-tab="tf" role="tab" aria-selected="false">Ficha do veículo</button>
  <button data-tab="te" role="tab" aria-selected="false">Raio-X da empresa</button>
  <button data-tab="t5" role="tab" aria-selected="false">5 · Judicial e regulatório</button>
  <button data-tab="t6" role="tab" aria-selected="false">6 · Auditoria e método</button>
</nav>

<!-- ================= TELA 1 ================= -->
<section id="t1" role="tabpanel">
  <h2>O mercado agora</h2>
  <p class="note" id="capa-nota"></p>
  <div class="tiles" id="tiles1"></div>
  <div class="warnbox" id="box-julho"></div>
  <details class="explain"><summary>Como ler estes números</summary><div class="b">
    <p><strong>Patrimônio bruto e patrimônio líquido de circularidade são coisas diferentes.</strong>
    Parte do mercado é formada por fundos que compram cotas de outros fundos do próprio
    universo. Somar tudo conta o mesmo dinheiro duas vezes; a segunda medida desconta essa
    sobreposição e é a que responde "quanto deste mercado financia a economia real".</p>
    <p><strong>"Posições de cotistas" não é número de investidores.</strong> O informe conta
    posições por veículo: quem investe em dez fundos aparece dez vezes. A identidade e o valor
    por cotista não são públicos.</p>
    <p><strong>Direitos creditórios sem transferência de risco</strong> são recebíveis que o
    fundo comprou, mas cujo risco econômico permaneceu com quem os cedeu — funding garantido
    por recebíveis, não venda definitiva. É uma fatia relevante do estoque e muda a leitura
    de quem realmente carrega o risco.</p>
  </div></details>
  <h2>O que mudou no mês</h2>
  <p class="note">Fluxos e movimentos da competência do corte, e o giro da triagem de sinais.
  "Sinais encerrados" ainda não é computável — exige o snapshot da publicação anterior, que o
  orquestrador passou a versionar; o número existe a partir da próxima edição.</p>
  <div class="tiles" id="tiles1b"></div>
  <h2>Estrutura de capital</h2>
  <p class="note">Quem absorve a primeira perda. Valor por tipo de série (tab X_2).</p>
  <div class="card" id="capital"></div>
</section>

<!-- ================= TELA 2 ================= -->
<section id="t2" role="tabpanel" hidden>
  <h2>Anatomia do mercado</h2>
  <p class="note">Composição, qualidade do crédito e integridade do reporte, no corte.</p>
  <div class="tiles" id="tiles2"></div>
  <div class="cols">
    <div class="card"><h3>Qualidade do crédito</h3><div id="qual"></div></div>
    <div class="card"><h3>Integridade e desempenho</h3><div id="integ"></div></div>
  </div>
  <details class="explain"><summary>O que estes indicadores revelam</summary><div class="b">
    <p><strong>Identidade contábil.</strong> Ativo menos passivo deve ser igual ao patrimônio
    líquido em cada informe. É o teste mais simples de consistência do que foi declarado, e
    roda sobre todos os veículos avaliáveis.</p>
    <p><strong>Desempenho esperado × realizado.</strong> O informe pede que o administrador
    declare o desempenho esperado de cada série e o efetivamente entregue. A comparação mostra
    quantas séries ficaram abaixo da própria promessa — indicador de deterioração que independe
    de qualquer modelo.</p>
    <p><strong>Garantia real declarada.</strong> Colateral formal sobre os direitos creditórios
    é raro neste mercado. A proteção do investidor vem, na prática, da subordinação e da
    coobrigação do cedente, não de garantia sobre ativos.</p>
  </div></details>
</section>

<!-- ================= TELA 3 ================= -->
<section id="t3" role="tabpanel" hidden>
  <h2>Exposição: nove lentes distintas</h2>
  <p class="note">Não existe um ranking único de "maiores expostos". Cada lente mede uma coisa
  diferente, com unidade de análise e cobertura próprias — e cada uma declara o que
  <em>não</em> significa.</p>
  <div class="card" id="lentes"></div>
  <div class="toolbar" style="margin-top:20px">
    <label for="lensel" class="note" style="margin:0">Ver ranking:</label>
    <select id="lensel">
      <option value="lente1">1 · PL sob gestão</option>
      <option value="lente2">2 · PL sob administração fiduciária</option>
      <option value="lente4">4 · Exposição a cedente/originador</option>
      <option value="lente5">5 · Concentração por devedor (tab VIII)</option>
      <option value="lente8">8 · Exposição operacional por papel</option>
    </select>
    <input type="search" id="q3" placeholder="filtrar por nome ou CNPJ…" aria-label="Filtrar">
    <button class="act" data-copy="lente1" id="cp3">copiar CSV</button>
  </div>
  <div class="card" id="lentetab"></div>
</section>

<!-- ================= TELA 4 ================= -->
<section id="t4" role="tabpanel" hidden>
  <h2>Supervisão e integridade</h2>
  <div class="warnbox"><strong>Regra de leitura.</strong> Sinal estatístico não é imputação de
  irregularidade. Nenhum veículo, gestor ou empresa desta tela está sendo acusado de ilícito;
  o que se mede é onde a informação pública indica atenção supervisória. Cobertura insuficiente
  gera classificação "não classificável" — nunca "baixo risco".</div>
  <div class="tiles" id="tiles4"></div>
  <h2>Quem detém as cotas</h2>
  <p class="note">Cotas de FIDC dentro da indústria de fundos, por gestor do fundo investidor.
  Bancos, empresas e pessoas físicas não aparecem nesta fonte.</p>
  <div class="toolbar"><input type="search" id="q4" placeholder="filtrar…" aria-label="Filtrar">
    <button class="act" data-copy="detentores">copiar CSV</button></div>
  <div class="card" id="detentores"></div>
  <h2>Sinais de atenção por veículo</h2>
  <p class="note" id="rfnota"></p>
  <div class="card" id="rfscore"></div>
  <h2>Catálogo de sinais</h2>
  <div class="card" id="rfcat"></div>
</section>

<!-- ================= FICHA ================= -->
<section id="tf" role="tabpanel" hidden>
  <h2>Raio-X do veículo</h2>
  <p class="note">Busque um fundo ou classe por nome ou CNPJ. Os 400 maiores por patrimônio
  estão disponíveis. Campo vazio significa <strong>ausência de reporte</strong>, nunca zero.</p>
  <div class="toolbar">
    <input type="search" id="qf" placeholder="nome do fundo ou CNPJ…" aria-label="Buscar veículo"
           style="min-width:320px">
    <select id="fsel" aria-label="Selecionar veículo"></select>
  </div>
  <div class="card" id="ficha"></div>
</section>

<!-- ================= EMPRESA ================= -->
<section id="te" role="tabpanel" hidden>
  <h2>Raio-X da empresa (cedente/originador)</h2>
  <p class="note">Visão centrada na <strong>empresa</strong>: em quais veículos ela aparece como
  cedente, com que recorrência histórica, e se há recuperação judicial ou falência documentada.
  O valor é estoque <strong>atribuído</strong> de recebíveis originados — não é dívida da empresa
  nem fluxo cedido — e a cobertura é um piso (só os 9 maiores cedentes de cada veículo são
  públicos). Recuperação judicial não é evidência de irregularidade.</p>
  <div class="toolbar">
    <input type="search" id="qe" placeholder="razão social ou CNPJ…" aria-label="Buscar empresa"
           style="min-width:320px">
    <select id="esel" aria-label="Selecionar empresa"></select>
  </div>
  <div class="card" id="empresa"></div>
</section>

<!-- ================= TELA 5 ================= -->
<section id="t5" role="tabpanel" hidden>
  <h2>Recuperação judicial e falência</h2>
  <div class="warnbox">Estar em recuperação judicial <strong>não</strong> é evidência de
  irregularidade — é um instituto legal de reorganização. A classificação de um crédito como
  concursal ou extraconcursal depende do contrato e da data do fato gerador (Lei 11.101/2005,
  art. 49 e §3º), nunca do nome do credor. Casamento de entidades feito por CNPJ; correspondência
  por nome é sinalizada como pendente de validação humana.</div>
  <div class="tiles" id="tiles5"></div>
  <div class="card" id="rjvinc"></div>
  <h2>Casos com fonte pública citada</h2>
  <div class="card" id="rj"></div>
  <h2>Casos regulatórios e sancionadores</h2>
  <p class="note">Cada caso traz o estágio processual. Investigação, acusação, processo em curso,
  decisão e decisão definitiva são situações jurídicas distintas e não devem ser lidas como
  equivalentes.</p>
  <div class="toolbar"><input type="search" id="q5" placeholder="filtrar casos…" aria-label="Filtrar">
    <button class="act" data-copy="casos">copiar CSV</button></div>
  <div class="card" id="casos"></div>
</section>

<!-- ================= TELA 6 ================= -->
<section id="t6" role="tabpanel" hidden>
  <h2>Auditoria e método</h2>
  <p class="note">Testes executados sobre a base publicada. Verde: aprovado. Âmbar: ressalva
  documentada. O detalhe de cada teste aparece ao passar o mouse.</p>
  <div class="card" id="testes"></div>
  <h2>Verificação automática de fórmulas</h2>
  <p class="note">Cada indicador publicado é recomputado, de forma independente, a partir dos
  arquivos de origem (<span class="mono">scripts/20_teste_formulas.py</span>). Divergência acima
  de 0,1% — ou indicador sem verificador — reprova o build. Inclui o linter jurídico da tabela
  de casos e a regra-mãe das fichas.</p>
  <div class="card" id="verif"></div>
  <h2>Cobertura das fontes</h2>
  <div class="card" id="meta"></div>
  <details class="explain" open><summary>Limitações que não podem ser omitidas</summary><div class="b">
    <p><strong>Identidade do devedor.</strong> A tabela VIII traz os 25 maiores devedores de cada
    veículo em valor, mas sem qualquer identificador. É impossível, com dados públicos, montar
    ranking nominal de devedores ou somar a exposição de uma mesma empresa entre fundos.</p>
    <p><strong>Cedentes.</strong> O informe revela apenas os nove maiores cedentes por veículo,
    com percentual declarado — o ranking é um piso, não um censo.</p>
    <p><strong>Cotistas.</strong> Há contagem por categoria, não identidade nem valor por
    investidor. Quem detém as cotas subordinadas em valor não é observável.</p>
    <p><strong>Dados autodeclarados.</strong> O informe é preenchido pelo administrador e contém
    erros de digitação detectáveis. Onde há erro grosseiro, a observação é excluída com regra
    explícita e registrada em log, nunca corrigida silenciosamente.</p>
    <p><strong>Ausência não é zero.</strong> Campo não informado permanece nulo e reduz a
    cobertura do indicador; jamais é convertido em zero para fechar uma conta.</p>
  </div></details>
</section>

<footer>
  Fontes primárias: Portal de Dados Abertos da CVM (informe mensal de FIDC, cadastro e registro
  de fundos, classes e subclasses, CDA e Medidas FIE), Banco Central (IPCA), base pública do CNPJ
  e demonstrações financeiras publicadas. Valores em reais correntes, salvo indicação.
  Este material é analítico e não constitui recomendação de investimento, opinião de crédito
  ou imputação de conduta a qualquer pessoa ou entidade.
</footer>
</div>

<dialog id="evd" aria-labelledby="evtitle">
  <div class="head"><h4 id="evtitle"></h4><button class="close" id="evclose" aria-label="Fechar">×</button></div>
  <div class="body" id="evbody"></div>
</dialog>

<script>window.__FIDC__ = __PAYLOAD__;</script>
<script>__JS__
// ---------- montagem ----------
const M = D.meta;
document.getElementById('capa-nota').innerHTML =
  `Competência de referência <strong>${M.data_corte}</strong> — a última com entrega completa. ` +
  `Extração de ${M.data_extracao}. ${M.n_tabelas_carregadas} de ${M.n_tabelas_informe} tabelas do ` +
  `informe carregadas; ${M.n_arquivos_manifesto} arquivos-fonte com hash registrado.`;

document.getElementById('tiles1').innerHTML =
  ['pl_total','pl_liquido','n_veiculos','posicoes_cotistas','dc_total','inadimplencia',
   'subordinacao','var_12m'].map(k=>tile(k)).join('');

const ja = ind('jul_ausentes'), jp = ind('jul_pl_ausente');
document.getElementById('box-julho').innerHTML = ja && jp
  ? `<strong>Por que o corte é ${M.data_corte} e não a competência seguinte.</strong> ` +
    `Em ${M.competencia_parcial}, ${ev('jul_ausentes')} veículos que haviam informado no mês ` +
    `anterior deixaram de entregar o informe, carregando ${ev('jul_pl_ausente')} de patrimônio. ` +
    `A ausência foi verificada na tabela bruta e é fortemente concentrada em poucos administradores, ` +
    `o que a distingue do atraso difuso normal. Totalizar sobre uma competência incompleta produziria ` +
    `queda aparente do mercado onde houve, entre os veículos que informaram nos dois meses, crescimento.`
  : '';

document.getElementById('tiles1b').innerHTML =
  ['var_1m','var_3m','var_6m','aquisicoes_mes','captacoes_mes','resgates_mes',
   'mudou_entrantes','mudou_saintes','mudou_sinais_novos','mudou_sinais_persistentes',
   'mudou_sinais_encerrados'].map(k=>tile(k)).join('');

document.getElementById('capital').innerHTML = (function(){
  const s=['serie_senior','serie_mezanino','serie_subordinada'].map(ind).filter(Boolean);
  const tot=s.reduce((a,b)=>a+(b.valor||0),0)||1;
  const cores=['var(--s1)','var(--s2)','var(--s3)'];
  const nomes=['Sênior','Mezanino','Subordinada'];
  let x=0, segs='';
  s.forEach((v,i)=>{ const w=100*(v.valor||0)/tot;
    segs+=`<div style="position:absolute;left:${x}%;width:${Math.max(w-0.3,0.3)}%;top:0;height:26px;background:${cores[i]}"></div>`;
    x+=w; });
  const leg=s.map((v,i)=>`<span style="margin-right:16px"><span style="display:inline-block;width:13px;height:3px;background:${cores[i]};vertical-align:middle;margin-right:6px"></span>${nomes[i]} ${nf.format((100*(v.valor||0)/tot).toFixed(1))}% · ${ev(['serie_senior','serie_mezanino','serie_subordinada'][i])}</span>`).join('');
  return `<div style="position:relative;height:26px;border-radius:5px;overflow:hidden;background:var(--grid)">${segs}</div>
    <p class="note" style="margin:10px 0 0">${leg}</p>`;
})();

document.getElementById('tiles2').innerHTML =
  ['dc_sem_risco','circularidade','atraso_180','provisionamento','cagr_real','var_24m']
  .map(k=>tile(k)).join('');
document.getElementById('qual').innerHTML =
  ['inadimplencia','atraso_180','provisionamento'].map(k=>{
    const i=ind(k); return i? `<p style="margin:0 0 9px">${i.rotulo}: <strong>${ev(k)}</strong></p>`:'';
  }).join('') + `<p class="note" style="margin:8px 0 0">Medida abrangente de atraso: todas as faixas
  das tabelas V e VI, sobre o estoque de direitos creditórios.</p>`;
document.getElementById('integ').innerHTML =
  ['identidade_contabil','series_abaixo_esperado','veiculos_com_garantia'].map(k=>{
    const i=ind(k); return i? `<p style="margin:0 0 9px">${i.rotulo}: <strong>${ev(k)}</strong>
      <span class="note" style="display:block;margin:2px 0 0">${i.obs||''}</span></p>`:'';
  }).join('');

renderTable('lentes','lentes');
function drawLente(){
  const k=document.getElementById('lensel').value;
  renderTable(k,'lentetab',{bar:'valor'});
  document.getElementById('cp3').dataset.copy=k;
  filterTables(document.getElementById('q3').value);
}
document.getElementById('lensel').addEventListener('change',drawLente);
document.getElementById('q3').addEventListener('input',e=>filterTables(e.target.value));
drawLente();

document.getElementById('tiles4').innerHTML =
  ['detido_fundos','emissor_ligado','sacado_cobertura_dc','sacado_mediana_top1',
   'sacado_n_top1_50','rf_n_sinais','rf_atencao_alta','rf_nao_classificavel']
   .map(k=>tile(k)).join('');
renderTable('detentores','detentores',{bar:'vl_cotas_fidc'});
document.getElementById('q4').addEventListener('input',e=>filterTables(e.target.value));
renderTable('rf_score','rfscore');
renderTable('rf_catalogo','rfcat');
document.getElementById('rfnota').textContent = D.tabelas.rf_score && D.tabelas.rf_score.linhas.length
  ? 'Score decomposto: risco, materialidade, cobertura e persistência aparecem lado a lado — nunca um número único. Falso positivo estrutural conhecido: fundos de crédito inadimplido (NPL), distressed e créditos judiciais disparam sinais de qualidade de ativo por desenho do próprio mandato, não por deterioração. Metodologia experimental — o backtest descartou dois sinais e não validou poder preditivo.'
  : 'Triagem em consolidação nesta versão.';

document.getElementById('tiles5').innerHTML =
  ['rj_vinculos','rj_exposicao','rj_casos','rj_processos'].map(k=>tile(k)).join('');
// ---- ficha do veículo ----
(function(){
  const t = D.tabelas.fichas; if(!t || !t.linhas.length) return;
  const col = {}; t.colunas.forEach((c,i)=>col[c]=i);
  const sel = document.getElementById('fsel');
  function opcoes(q){
    q=(q||'').trim().toLowerCase();
    const lista = t.linhas.filter(r=> !q ||
      String(r[col.DENOM_SOCIAL]).toLowerCase().includes(q) || String(r[col.CNPJ]).includes(q));
    sel.innerHTML = lista.slice(0,200).map((r,i)=>
      `<option value="${t.linhas.indexOf(r)}">${r[col.DENOM_SOCIAL]}</option>`).join('');
    if(lista.length) desenha(t.linhas.indexOf(lista[0]));
    else document.getElementById('ficha').innerHTML='<p class="note">Nenhum veículo encontrado nesta seleção.</p>';
  }
  function linha(rot,val,nota){
    return `<tr><td style="color:var(--ink2);width:38%">${rot}</td><td>${val}</td>
      <td class="note" style="border:none;padding-top:7px">${nota||''}</td></tr>`;
  }
  function pct(v){ return (v===null||v===undefined)? '—' : nf.format(+(v*100).toFixed(1))+'%'; }
  function brl(v){ return (v===null||v===undefined)? '—' : fmtVal(v,'R$'); }
  function desenha(ix){
    const r = t.linhas[ix]; if(!r) return;
    const sig = r[col.sinais]||[];
    // Regra-mãe: cobertura insuficiente NUNCA vira "nenhum sinal disparado".
    const cob = col.cobertura_dados_pct!==undefined ? r[col.cobertura_dados_pct] : null;
    const cobTxt = (cob===null||cob===undefined)? 'não avaliada' : nf.format(+(+cob).toFixed(1))+'% dos sinais avaliáveis';
    const naoClassificavel = (cob===null||cob===undefined) || (+cob < 50);
    const chipSinais = naoClassificavel
      ? `<span class="chip na">cobertura insuficiente para concluir (${cobTxt})</span>`
      : (sig.length? sig.map(x=>`<span class="chip warn">${x}</span>`).join(' ')
                   : `<span class="chip ok">nenhum disparado (cobertura ${cobTxt})</span>`);
    document.getElementById('ficha').innerHTML =
      `<h3 style="font-size:17px;font-family:Georgia,serif;font-weight:400;margin:0 0 3px">${r[col.DENOM_SOCIAL]}</h3>
       <p class="note mono" style="margin:0 0 14px">CNPJ ${r[col.CNPJ]} · ${r[col.TP_FUNDO_CLASSE]}</p>
       <table><tbody>
       ${linha('Patrimônio líquido', brl(r[col.VL_PL]))}
       ${linha('Administrador fiduciário', r[col.ADMIN]||'—','não assume o risco de crédito da carteira')}
       ${linha('Gestor', r[col.gestor]||'—','responde pela decisão de investimento')}
       ${linha('Direitos creditórios', brl(r[col.dc]))}
       ${linha('— sem transferência de risco', brl(r[col.dc_sem_risco]),'risco econômico permanece no cedente')}
       ${linha('Inadimplência', pct(r[col.inad_pct]),'parcelas vencidas sobre a carteira (tab V)')}
       ${linha('Subordinação + mezanino', pct(r[col.subord]),'colchão que absorve a primeira perda')}
       ${linha('Maior devedor', pct(r[col.pct_maior_sacado]),'tab VIII — sem identificação do devedor')}
       ${linha('Maior cedente declarado', r[col.pct_maior_cedente]===null?'—':nf.format(r[col.pct_maior_cedente])+'%',
               (r[col.n_cedentes_declarados]||0)+' cedente(s) declarado(s), até 9 por veículo')}
       ${linha('Posições de cotistas', r[col.posicoes_cotistas]===null?'—':nf.format(r[col.posicoes_cotistas]),'não mede pessoas únicas')}
       ${linha('Exclusivo', r[col.exclusivo]==='S'?'sim':(r[col.exclusivo]==='N'?'não':'—'))}
       ${linha('Cotistas de interesse único', r[col.interesse_unico]==='S'?'sim':(r[col.interesse_unico]==='N'?'não':'—'),
               'indica estrutura fechada em torno de um mesmo interesse econômico')}
       ${linha('Cobertura de dados', cobTxt,
               'fração dos sinais da metodologia avaliável para este veículo — abaixo de 50% o veículo é NÃO CLASSIFICÁVEL')}
       ${linha('Sinais de atenção', chipSinais,
               naoClassificavel? 'cobertura insuficiente nunca é lida como baixo risco'
                               : 'sinal estatístico, não imputação de irregularidade')}
       </tbody></table>`;
  }
  document.getElementById('qf').addEventListener('input', e=>opcoes(e.target.value));
  sel.addEventListener('change', e=>desenha(+e.target.value));
  opcoes('');
})();
// ---- raio-X da empresa ----
(function(){
  const t = D.tabelas.empresas; if(!t || !t.linhas.length) return;
  const col = {}; t.colunas.forEach((c,i)=>col[c]=i);
  const sel = document.getElementById('esel');
  function linha(rot,val,nota){
    return `<tr><td style="color:var(--ink2);width:38%">${rot}</td><td>${val}</td>
      <td class="note" style="border:none;padding-top:7px">${nota||''}</td></tr>`;
  }
  function opcoes(q){
    q=(q||'').trim().toLowerCase();
    const lista = t.linhas.filter(r=> !q ||
      String(r[col.razao_social]).toLowerCase().includes(q) || String(r[col.doc_cedente]).includes(q));
    sel.innerHTML = lista.slice(0,100).map(r=>
      `<option value="${t.linhas.indexOf(r)}">${r[col.razao_social]}</option>`).join('');
    if(lista.length) desenha(t.linhas.indexOf(lista[0]));
    else document.getElementById('empresa').innerHTML='<p class="note">Nenhuma empresa encontrada nesta seleção.</p>';
  }
  function desenha(ix){
    const r = t.linhas[ix]; if(!r) return;
    const veic = r[col.veiculos]||[];
    const rj = r[col.status_judicial];
    document.getElementById('empresa').innerHTML =
      `<h3 style="font-size:17px;font-family:Georgia,serif;font-weight:400;margin:0 0 3px">${r[col.razao_social]}</h3>
       <p class="note mono" style="margin:0 0 14px">CNPJ ${r[col.doc_cedente]} · ${r[col.cnae_principal]||'CNAE não resolvido'} · ${r[col.uf]||''}</p>
       <table><tbody>
       ${linha('Situação cadastral', r[col.situacao]||'—','base pública do CNPJ')}
       ${linha('Estoque atribuído', fmtVal(r[col.exposicao_estimada],'R$'),'recebíveis originados presentes em carteiras de FIDC — não é dívida da empresa')}
       ${linha('Veículos com a empresa como cedente', r[col.n_veiculos]===null?'—':nf.format(r[col.n_veiculos]),'entre os 9 maiores cedentes declarados por veículo')}
       ${linha('Recorrência histórica', r[col.n_meses]===null||r[col.n_meses]===undefined?'—':nf.format(r[col.n_meses])+' competências',
               (r[col.primeira]&&r[col.ultima])? 'primeira '+r[col.primeira]+' · última '+r[col.ultima] : '')}
       ${linha('Recuperação judicial / falência', rj? `<span class="chip warn">${rj}</span>` : 'não identificada em fonte pública',
               rj? 'marcador cadastral do art. 69 da Lei 11.101/2005 — NÃO é evidência de irregularidade'
                 : 'ausência de marcador não prova inexistência de processo')}
       ${linha('Também cotista corporativo de FIDC', r[col.cotista_corporativo]===true?'sim (demonstração financeira publicada)':'não identificado',
               'papéis simultâneos (cedente e cotista) elevam a dependência corporativa do instrumento')}
       ${linha('Principais veículos', veic.length? veic.map(v=>`<span class="chip">${v}</span>`).join(' ') : '—',
               '% = participação declarada da empresa na carteira do veículo')}
       </tbody></table>`;
  }
  document.getElementById('qe').addEventListener('input', e=>opcoes(e.target.value));
  sel.addEventListener('change', e=>desenha(+e.target.value));
  opcoes('');
})();
renderTable('rj_vinculos','rjvinc',{bar:'exposicao_estimada'});
renderTable('rj','rj');
renderTable('casos','casos');
document.getElementById('q5').addEventListener('input',e=>filterTables(e.target.value));

(function(){
  const t=D.tabelas.verificacao; const el=document.getElementById('verif');
  if(!t||!t.linhas.length){ el.innerHTML='<p class="note">Verificação ainda não executada neste build.</p>'; return; }
  const ix={i:t.colunas.indexOf('indicador'),s:t.colunas.indexOf('status'),
            d:t.colunas.indexOf('diff_pct')};
  const nOk = t.linhas.filter(r=>r[ix.s]==='OK').length;
  el.innerHTML = `<p style="margin:0 0 9px"><strong>${nf.format(nOk)} de ${nf.format(t.linhas.length)}</strong> verificações aprovadas nesta execução.</p>`
    + t.linhas.map(r=>{
      const cls = r[ix.s]==='OK'?'ok':'crit';
      const d = r[ix.d]===null||r[ix.d]===undefined? '' : ' · diff '+nf.format(+(+r[ix.d]).toFixed(4))+'%';
      return `<span class="chip ${cls}" title="${r[ix.i]}${d}">${r[ix.i]}</span> `;
    }).join('');
})();
(function(){
  const t=D.tabelas.testes; const el=document.getElementById('testes');
  if(!t||!t.linhas.length){ el.innerHTML='<p class="note">—</p>'; return; }
  const ix={teste:t.colunas.indexOf('teste'),res:t.colunas.indexOf('resultado'),
          st:t.colunas.indexOf('status'),det:t.colunas.indexOf('detalhe')};
  el.innerHTML = t.linhas.map(r=>{
    const st=String(r[ix.st]||''); const cls= st==='PASS'?'ok': st==='FAIL'?'crit':'warn';
    const id=String(r[ix.teste]||'').split(' ')[0];
    return `<span class="chip ${cls}" title="${String(r[ix.teste]||'').replace(/"/g,'')} — ${r[ix.res]} ${r[ix.det]||''}">${id}</span> `;
  }).join('');
})();
document.getElementById('meta').innerHTML =
  `<p style="margin:0 0 8px">Tabelas do informe carregadas: <strong>${M.n_tabelas_carregadas} de ${M.n_tabelas_informe}</strong>.
   Arquivos-fonte no manifesto: <strong>${M.n_arquivos_manifesto}</strong> (hash do manifesto
   <span class="mono">${M.hash_manifesto}</span>).</p>
   <p class="note" style="margin:0">Cada indicador desta página carrega sua própria cobertura;
   onde a fonte não cobre o universo, o número aparece com a fração coberta na gaveta de evidências.</p>`;

if(location.hash) showTab(location.hash.slice(1));
</script>"""

    body = (body.replace("__CSS__", CSS)
                .replace("__JS__", JS)
                .replace("__PAYLOAD__", payload))
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"painel v2: {DEST} ({os.path.getsize(DEST)/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
