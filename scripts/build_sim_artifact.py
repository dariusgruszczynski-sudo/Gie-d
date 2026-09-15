"""Buduje/aktualizuje artefakt HTML (raport Monte Carlo v2 — profil jakości + dopłaty)."""
import json

SCRATCH = "/tmp/claude-0/-home-user-Gie-d/fe1df807-8e8a-512a-a12c-6c9b924b2af0/scratchpad"
sim = json.load(open(f"{SCRATCH}/sim2.json"))
DATA = json.dumps(sim, separators=(",", ":"))

HTML = r"""<title>Symulacja roku GielDarek</title>
<meta name="description" content="Monte Carlo: profil jakości + dopłaty $300/mies, pasmo trafności, na najbliższy rok.">
<style>
:root{
  --bg:#f5f1ea; --panel:#fffdf9; --panel-2:#f0e9dd; --ink:#211c16; --ink-2:#5b5145;
  --muted:#8a7d6c; --line:#e2d8c8; --copper:#b96a26; --copper-2:#d98a45;
  --silver:#8d8577; --gain:#2f8f74; --loss:#c3453f; --warn:#b8791a;
  --band-far:rgba(185,106,38,.13); --band-mid:rgba(185,106,38,.26);
  --shadow:0 1px 2px rgba(33,28,22,.05),0 8px 24px rgba(33,28,22,.06);
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --sans:"IBM Plex Sans",system-ui,sans-serif; --disp:"Chivo","IBM Plex Sans",sans-serif;
}
:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
  --bg:#181410;--panel:#221c16;--panel-2:#2b241c;--ink:#f2ebe0;--ink-2:#c8bdaa;--muted:#9a8d7a;
  --line:#352c22;--copper:#e0954c;--copper-2:#f0a95f;--silver:#a49b8a;--gain:#5cc3a2;--loss:#e8746c;--warn:#e0a54a;
  --band-far:rgba(224,149,76,.12);--band-mid:rgba(224,149,76,.24);
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}}
:root[data-theme="dark"]{
  --bg:#181410;--panel:#221c16;--panel-2:#2b241c;--ink:#f2ebe0;--ink-2:#c8bdaa;--muted:#9a8d7a;
  --line:#352c22;--copper:#e0954c;--copper-2:#f0a95f;--silver:#a49b8a;--gain:#5cc3a2;--loss:#e8746c;--warn:#e0a54a;
  --band-far:rgba(224,149,76,.12);--band-mid:rgba(224,149,76,.24);
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:940px;margin:0 auto;padding-block:clamp(28px,5vw,56px);padding-left:20px;padding-right:20px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--copper);font-weight:600}
h1{font-family:var(--disp);font-weight:800;font-size:clamp(30px,5.2vw,50px);line-height:1.04;letter-spacing:-.02em;text-wrap:balance;margin:.35em 0 .3em}
.lede{font-size:clamp(16px,2.2vw,19px);color:var(--ink-2);max-width:64ch;margin:0}
h2{font-family:var(--disp);font-weight:700;font-size:22px;letter-spacing:-.01em;margin:0 0 4px}
.sec-note{color:var(--muted);font-size:14px;margin:0 0 18px}
section{margin-top:44px}
.cards3{margin-top:30px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:720px){.cards3{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:var(--shadow)}
.tag{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11.5px;font-weight:600;padding:4px 10px;border-radius:999px;letter-spacing:.03em}
.tag.good{background:color-mix(in srgb,var(--gain) 15%,transparent);color:var(--gain)}
.tag.warn{background:color-mix(in srgb,var(--warn) 16%,transparent);color:var(--warn)}
.tag.dot::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.big{font-family:var(--disp);font-weight:800;font-size:clamp(26px,5vw,38px);letter-spacing:-.02em;line-height:1;margin-top:12px}
.big.gain{color:var(--gain)} .big.warn{color:var(--warn)}
.sub{color:var(--muted);font-size:13px;margin-top:7px;line-height:1.5}
.chartcard{padding:20px}
.switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.switch button{font-family:var(--mono);font-size:12.5px;font-weight:500;color:var(--ink-2);background:var(--panel-2);border:1px solid var(--line);border-radius:999px;padding:6px 13px;cursor:pointer;transition:.15s}
.switch button[aria-pressed="true"]{background:var(--copper);border-color:var(--copper);color:#fff;font-weight:600}
.switch button:focus-visible{outline:2px solid var(--copper);outline-offset:2px}
figure{margin:0}
svg{display:block;width:100%;height:auto;font-family:var(--mono)}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;font-size:12.5px;color:var(--ink-2);font-family:var(--mono)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:16px;height:10px;border-radius:3px;display:inline-block}
.tt{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 11px;font-family:var(--mono);font-size:12px;box-shadow:var(--shadow);opacity:0;transition:opacity .1s;min-width:170px;z-index:5}
.tt b{color:var(--ink)} .tt .r{display:flex;justify-content:space-between;gap:14px;color:var(--ink-2);margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:12px 10px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
thead th{font-family:var(--mono);font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
td .pill{font-family:var(--mono);font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px}
.pill.neg{background:color-mix(in srgb,var(--loss) 14%,transparent);color:var(--loss)}
.pill.pos{background:color-mix(in srgb,var(--gain) 16%,transparent);color:var(--gain)}
.pill.zero{background:var(--panel-2);color:var(--ink-2)}
.rowbe td{background:color-mix(in srgb,var(--warn) 8%,transparent)}
ul.clean{margin:10px 0 0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:10px}
ul.clean li{padding-left:24px;position:relative;color:var(--ink-2);font-size:14.5px;max-width:66ch}
ul.clean li::before{content:"";position:absolute;left:2px;top:9px;width:9px;height:9px;border-radius:2px;background:var(--copper);transform:rotate(45deg)}
ul.clean li strong{color:var(--ink)}
.foot{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px;font-family:var(--mono);line-height:1.7}
.kicker{color:var(--warn);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">Monte Carlo · profil jakości · dopłaty $300/mies · rok</div>
  <h1>Symulacja roku — nowe warunki</h1>
  <p class="lede">Po zdjęciu agresji: mniejsze i rzadsze pozycje (ryzyko 2%, próg konfluencji 2/3, auto-deploy
    off) plus <b>$300/mies dopłaty</b>. Trafność, którą ma podnieść zacieśnienie, jest nieznana — więc liczę
    <em>pasmo</em> scenariuszy i oddzielam Twoje wpłaty od tego, co realnie dołożył bot.</p>

  <div class="cards3">
    <div class="card">
      <span class="tag good dot">RYZYKO OPANOWANE</span>
      <div class="big gain">~2–3%</div>
      <div class="sub">mediana maks. obsunięcia (było <b>31%</b> na profilu agresywnym). Zdjęcie auto-deployu i mniejsze
        pozycje sprawiają, że bot nie może już mocno zaszkodzić.</div>
    </div>
    <div class="card">
      <span class="tag dot" style="background:var(--panel-2);color:var(--ink-2)">WPŁATY BUDUJĄ KONTO</span>
      <div class="big">$4 593</div>
      <div class="sub">tyle wpłacasz przez rok (start $993 + 12×$300). Konto kończy ~$4,5–4,9k — handel to małe
        ± na tej sumie, nie główny motor.</div>
    </div>
    <div class="card">
      <span class="tag warn dot">BOT DOKŁADA DOPIERO &gt; 31%</span>
      <div class="big warn">31,2%</div>
      <div class="sub">próg opłacalności (payoff 2,21×). Poniżej — bot lekko odejmuje; powyżej — realnie dokłada.
        Cała gra to trafność wejść.</div>
    </div>
  </div>

  <section>
    <h2>Wartość konta przez rok — wg trafności</h2>
    <p class="sec-note">Mediana + pasma 5–95% ścieżek. Przerywana linia = „gdyby tylko wpłacać, bez handlu". Przełącz trafność.</p>
    <div class="card chartcard">
      <div class="switch" id="switch"></div>
      <figure style="position:relative">
        <svg id="fan" viewBox="0 0 760 360" role="img" aria-label="Wartość konta w czasie"></svg>
        <div class="tt" id="tt"></div>
      </figure>
      <div class="legend">
        <span><i class="sw" style="background:var(--band-far)"></i>5–95% ścieżek</span>
        <span><i class="sw" style="width:16px;height:3px;border-radius:2px;background:var(--copper)"></i>mediana (z handlem)</span>
        <span><i class="sw" style="width:16px;height:0;border-top:2px dashed var(--silver)"></i>tylko wpłaty (bez handlu)</span>
      </div>
    </div>
  </section>

  <section>
    <h2>Wkład bota — po odjęciu wpłat</h2>
    <p class="sec-note">Ile handel realnie dołożył/odjął (mediana), oddzielnie od pieniędzy, które wpłacasz.</p>
    <div class="card" style="padding:6px 14px;overflow-x:auto">
      <table>
        <thead><tr><th>Trafność (założona)</th><th>Mediana konta</th><th>Wkład bota</th><th>P(bot na plus)</th><th>Obsun.</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Jak to czytać</h2>
    <ul class="clean">
      <li><strong>Downside jest teraz mały.</strong> Najgorszy realny scenariusz (trafność zostaje 28%) to bot
        odejmujący ~$140 przez rok i obsunięcie ~3% — a nie −27%, jak groził profil agresywny. To była właściwa
        zamiana: mniej upside w zamian za realną ochronę kapitału, póki edge nieudowodniony.</li>
      <li><strong>Wpłaty, nie bot, budują saldo.</strong> Konto rośnie do ~$4,6k głównie dlatego, że wpłacasz
        $3,600. To Twoje pieniądze — nie myl ich z zyskiem. Handel dokłada od −$140 (28%) do +$296 (38%).</li>
      <li><strong>Bot zaczyna zarabiać powyżej 31% trafności.</strong> Przy 34% dokłada ~$118 i ma 83% szansy na
        plus; przy 38% ~<span class="kicker">$296</span> i 99% szansy. To właśnie testuje dzienny nadzór:
        czy próg konfluencji 2/3 realnie pcha trafność w tę stronę.</li>
      <li><strong>Uczciwie o skali.</strong> Nawet najlepszy modelowany rok to ~+6% na wpłaconym kapitale.
        To małe konto na dorobku — realny cel na teraz to <em>nie tracić</em> i udowodnić edge, a nie szybki zysk.</li>
    </ul>
  </section>

  <div class="foot">
    Metoda: 20 000 ścieżek Monte Carlo; transakcja = zwrot na ~10% konta (profil jakości: ryzyko 2%, mniejsze
    pozycje niż auto-deploy), ~300 transakcji/rok, payoff 2,21× (z realnych danych), dopłata $300 w 12 ratach,
    składanie. Trafność to ZAŁOŻENIE (pasmo 28–38%), bo dopiero ją testujemy — nie prognoza. Realny edge do dziś:
    27,8% (poniżej progu). Jeśli trafność nie wzrośnie, obowiązuje wiersz 28%.
  </div>
</div>

<script>
const SIM=__DATA__;
const order=["p28","p31","p34","p38"];
const NS="http://www.w3.org/2000/svg";
let current="p34";
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();

// tabela
const tb=document.getElementById("tbody");
for(const k of order){const s=SIM.scenarios[k];const tr=document.createElement("tr");
  if(k==="p31")tr.className="rowbe";
  const c=s.contrib;const cls=c>15?"pos":(c<-15?"neg":"zero");const sign=c>=0?"+":"";
  tr.innerHTML=`<td>${s.name}</td>`+
    `<td class="num">$${s.median_end.toLocaleString()}</td>`+
    `<td class="num"><span class="pill ${cls}">${sign}$${Math.abs(c).toLocaleString()}</span></td>`+
    `<td class="num">${s.pcontrib}%</td><td class="num">${s.dd}%</td>`;
  tb.appendChild(tr);}

// switch
const sw=document.getElementById("switch");
const shortlab=k=>({p28:"28% (obecna)",p31:"31% (próg)",p34:"34%",p38:"38%"})[k];
for(const k of order){const b=document.createElement("button");b.textContent=shortlab(k);
  b.setAttribute("aria-pressed",k===current);
  b.onclick=()=>{current=k;[...sw.children].forEach((c,i)=>c.setAttribute("aria-pressed",order[i]===k));draw();};
  sw.appendChild(b);}

const svg=document.getElementById("fan"),tt=document.getElementById("tt");
const W=760,H=360,ML=60,MR=18,MT=18,MB=34;
function draw(){
  while(svg.firstChild)svg.removeChild(svg.firstChild);
  const sc=SIM.scenarios[current],wk=SIM.weeks,dep=SIM.deposit_only;
  const lo=Math.min(...sc.p5,...dep),hi=Math.max(...sc.p95,...dep);
  const pad=(hi-lo)*0.08||1;const ymin=lo-pad,ymax=hi+pad;
  const X=i=>ML+(i/(wk.length-1))*(W-ML-MR);
  const Y=v=>MT+(1-(v-ymin)/(ymax-ymin))*(H-MT-MB);
  const mk=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;};
  for(let i=0;i<=4;i++){const v=ymin+(ymax-ymin)*i/4,y=Y(v);
    svg.appendChild(mk("line",{x1:ML,x2:W-MR,y1:y,y2:y,stroke:css("--line"),"stroke-width":1}));
    const tx=mk("text",{x:ML-9,y:y+4,"text-anchor":"end",fill:css("--muted"),"font-size":11});
    tx.textContent="$"+Math.round(v).toLocaleString();svg.appendChild(tx);}
  for(let m=0;m<=12;m+=3){const i=Math.round(m/12*(wk.length-1)),x=X(i);
    const anc=m===0?"start":(m===12?"end":"middle");
    const tx=mk("text",{x:x,y:H-12,"text-anchor":anc,fill:css("--muted"),"font-size":11});
    tx.textContent=m+" mies";svg.appendChild(tx);}
  // pasmo 5-95
  let d="M"+X(0)+" "+Y(sc.p95[0]);
  for(let i=1;i<sc.p95.length;i++)d+="L"+X(i)+" "+Y(sc.p95[i]);
  for(let i=sc.p5.length-1;i>=0;i--)d+="L"+X(i)+" "+Y(sc.p5[i]);d+="Z";
  svg.appendChild(mk("path",{d,fill:css("--band-far"),stroke:"none"}));
  // linia tylko-wpłaty
  let dd="M"+X(0)+" "+Y(dep[0]);for(let i=1;i<dep.length;i++)dd+="L"+X(i)+" "+Y(dep[i]);
  svg.appendChild(mk("path",{d:dd,fill:"none",stroke:css("--silver"),"stroke-width":1.5,"stroke-dasharray":"5 4"}));
  // mediana
  let dm="M"+X(0)+" "+Y(sc.p50[0]);for(let i=1;i<sc.p50.length;i++)dm+="L"+X(i)+" "+Y(sc.p50[i]);
  svg.appendChild(mk("path",{d:dm,fill:"none",stroke:css("--copper"),"stroke-width":2.5,"stroke-linejoin":"round"}));
  const ev=sc.p50[sc.p50.length-1];
  const lab=mk("text",{x:W-MR,y:Y(ev)-8,"text-anchor":"end",fill:css("--copper"),"font-size":12,"font-weight":700});
  lab.textContent="$"+Math.round(ev).toLocaleString();svg.appendChild(lab);
  // hover
  const hit=mk("rect",{x:ML,y:MT,width:W-ML-MR,height:H-MT-MB,fill:"transparent"});
  const cross=mk("line",{y1:MT,y2:H-MB,stroke:css("--muted"),"stroke-width":1,opacity:0});
  const dot=mk("circle",{r:4,fill:css("--copper"),stroke:css("--panel"),"stroke-width":2,opacity:0});
  svg.appendChild(cross);svg.appendChild(dot);svg.appendChild(hit);
  hit.addEventListener("pointermove",ev2=>{const r=svg.getBoundingClientRect();
    const px=(ev2.clientX-r.left)/r.width*W;let i=Math.round((px-ML)/(W-ML-MR)*(wk.length-1));
    i=Math.max(0,Math.min(wk.length-1,i));const x=X(i);
    cross.setAttribute("x1",x);cross.setAttribute("x2",x);cross.setAttribute("opacity",.6);
    dot.setAttribute("cx",x);dot.setAttribute("cy",Y(sc.p50[i]));dot.setAttribute("opacity",1);
    const mo=(i/(wk.length-1)*12).toFixed(1);
    tt.innerHTML=`<b>${mo} mies</b>`+
      `<div class="r"><span>mediana</span><span>$${Math.round(sc.p50[i]).toLocaleString()}</span></div>`+
      `<div class="r"><span>tylko wpłaty</span><span>$${Math.round(dep[i]).toLocaleString()}</span></div>`+
      `<div class="r"><span>5–95%</span><span>$${Math.round(sc.p5[i]).toLocaleString()}–$${Math.round(sc.p95[i]).toLocaleString()}</span></div>`;
    tt.style.left=Math.min(x/W*r.width+14,r.width-185)+"px";
    tt.style.top=(Y(sc.p50[i])/H*r.height-10)+"px";tt.style.opacity=1;});
  hit.addEventListener("pointerleave",()=>{tt.style.opacity=0;cross.setAttribute("opacity",0);dot.setAttribute("opacity",0);});
}
draw();
</script>
"""

out = HTML.replace("__DATA__", DATA)
open(f"{SCRATCH}/symulacja-roku.html", "w").write(out)
print("OK", len(out), "->", f"{SCRATCH}/symulacja-roku.html")
