const { chromium } = require('playwright-core');
const fs=require('fs');
(async()=>{
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args:['--no-sandbox']});
  const out={console:[],pageerror:[]};
  const ctx = await b.newContext({viewport:{width:1400,height:1200}});
  const p = await ctx.newPage();
  p.on('console',m=>out.console.push(m.type()+': '+m.text()));
  p.on('pageerror',e=>out.pageerror.push(String(e)));
  await p.goto('file:///tmp/claude-0/-home-user-FIDCs/074cc374-d902-56ce-8712-fb1748924b7e/scratchpad/aud/snap/painel_fidc_v2.html');
  await p.waitForTimeout(600);
  out.tabs={};
  for(const t of ['t1','t2','t3','t4','t5','t6']){
    await p.click(`[data-tab="${t}"]`); await p.waitForTimeout(300);
    // for t3 iterate all lenses
    if(t==='t3'){
      out.lentes={};
      for(const L of ['lente1','lente2','lente4','lente5','lente8']){
        await p.selectOption('#lensel',L); await p.waitForTimeout(300);
        out.lentes[L]=await p.evaluate(()=>{const tb=document.querySelector('#lentetab table');
          return {head:[...tb.querySelectorAll('th')].map(x=>x.textContent.trim()),
                  rows:[...tb.querySelectorAll('tbody tr')].map(tr=>[...tr.querySelectorAll('td')].map(td=>td.textContent.trim()))};});
      }
      await p.selectOption('#lensel','lente1'); await p.waitForTimeout(200);
    }
    out.tabs[t]=await p.evaluate(id=>{
      const s=document.getElementById(id);
      return {text:s.innerText,
        tiles:[...s.querySelectorAll('.tile')].map(e=>({lab:e.querySelector('.lab').textContent.trim(),val:e.querySelector('.val').textContent.trim()})),
        tables:[...s.querySelectorAll('table')].map(tb=>({head:[...tb.querySelectorAll('thead th')].map(x=>x.textContent.trim()),
          rows:[...tb.querySelectorAll('tbody tr')].map(tr=>[...tr.querySelectorAll('td')].map(td=>td.textContent.trim()))}))};
    },t);
  }
  // all evidence drawers
  await p.click('[data-tab="t1"]'); await p.waitForTimeout(200);
  const keys = await p.evaluate(()=>Object.keys(window.__FIDC__.indicadores));
  out.drawers={};
  for(const k of keys){
    const r = await p.evaluate(k=>{ try{ openEv(k); const d=document.getElementById('evd');
      const t=document.getElementById('evtitle').textContent; const bdy=document.getElementById('evbody').innerText; d.close(); return {ok:true,t,bdy};}catch(e){return {ok:false,e:String(e)};} },k);
    out.drawers[k]=r;
  }
  fs.writeFileSync('aud/probe2.json',JSON.stringify(out,null,1));
  await b.close();
})();
