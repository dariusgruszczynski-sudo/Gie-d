"""Buduje artefakt HTML (raport Monte Carlo) z danymi z sim.json."""
import json

SCRATCH = "/tmp/claude-0/-home-user-Gie-d/fe1df807-8e8a-512a-a12c-6c9b924b2af0/scratchpad"
sim = json.load(open(f"{SCRATCH}/sim.json"))

# Podsumowania scenariuszy (z przebiegu symulacji) — wpisane wprost, zgodne z runem.
SUMMARY = {
    "status_quo": {"label": "Status quo (małe pozycje ~7,5%)", "invested": 993, "median": 923,
                   "med_pct": -7.0, "p5": 866, "p95": 988, "pprofit": 4, "dd": 9},
    "auto_deploy": {"label": "Auto-deploy 25%/nazwę (obecna konfiguracja)", "invested": 993, "median": 727,
                    "med_pct": -26.8, "p5": 565, "p95": 935, "pprofit": 2, "dd": 31},
    "auto_deploy_deposits": {"label": "Auto-deploy + dopłaty $300/mies", "invested": 4593, "median": 3555,
                             "med_pct": -22.6, "p5": 3044, "p95": 4193, "pprofit": 1, "dd": 10},
    "better_edge": {"label": "Hipotetycznie: win rate 35% (powyżej progu)", "invested": 993, "median": 1390,
                    "med_pct": 40.0, "p5": 1053, "p95": 1811, "pprofit": 98, "dd": 10},
}
for k, v in SUMMARY.items():
    sim["scenarios"][k]["summary"] = v

DATA = json.dumps(sim, separators=(",", ":"))

HTML = """<title>Symulacja roku GielDarek</title>
<meta name="description" content="Monte Carlo na 20 000 ścieżek: rzut realnego edge bota na najbliższy rok.">
<style>
:root{
  --bg:#f5f1ea; --panel:#fffdf9; --panel-2:#f0e9dd; --ink:#211c16; --ink-2:#5b5145;
  --muted:#8a7d6c; --line:#e2d8c8; --copper:#b96a26; --copper-2:#d98a45;
  --silver:#8d8577; --gain:#2f8f74; --loss:#c3453f; --warn:#b8791a;
  --band-far:rgba(185,106,38,.14); --band-mid:rgba(185,106,38,.28);
  --shadow:0 1px 2px rgba(33,28,22,.05),0 8px 24px rgba(33,28,22,.06);
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
  --sans:"IBM Plex Sans",system-ui,sans-serif; --disp:"Chivo","IBM Plex Sans",sans-serif;
}
:root:not([data-theme="light"]){@media (prefers-color-scheme:dark){
  --bg:#181410; --panel:#221c16; --panel-2:#2b241c; --ink:#f2ebe0; --ink-2:#c8bdaa;
  --muted:#9a8d7a; --line:#352c22; --copper:#e0954c; --copper-2:#f0a95f; --silver:#a49b8a;
  --gain:#5cc3a2; --loss:#e8746c; --warn:#e0a54a;
  --band-far:rgba(224,149,76,.13); --band-mid:rgba(224,149,76,.26);
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
:root[data-theme="dark"]{
  --bg:#181410; --panel:#221c16; --panel-2:#2b241c; --ink:#f2ebe0; --ink-2:#c8bdaa;
  --muted:#9a8d7a; --line:#352c22; --copper:#e0954c; --copper-2:#f0a95f; --silver:#a49b8a;
  --gain:#5cc3a2; --loss:#e8746c; --warn:#e0a54a;
  --band-far:rgba(224,149,76,.13); --band-mid:rgba(224,149,76,.26);
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:940px;margin:0 auto;padding-block:clamp(28px,5vw,56px);padding-left:20px;padding-right:20px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--copper);font-weight:600}
h1{font-family:var(--disp);font-weight:800;font-size:clamp(30px,5.2vw,50px);line-height:1.04;
  letter-spacing:-.02em;text-wrap:balance;margin:.35em 0 .3em}
.lede{font-size:clamp(16px,2.2vw,19px);color:var(--ink-2);max-width:64ch;margin:0}
h2{font-family:var(--disp);font-weight:700;font-size:22px;letter-spacing:-.01em;margin:0 0 4px}
.sec-note{color:var(--muted);font-size:14px;margin:0 0 18px}
section{margin-top:44px}
.verdict{margin-top:30px;display:grid;grid-template-columns:1.15fr .85fr;gap:16px}
@media(max-width:640px){.verdict{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px;box-shadow:var(--shadow)}
.tag{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:12px;font-weight:600;
  padding:4px 10px;border-radius:999px;letter-spacing:.03em}
.tag.bad{background:color-mix(in srgb,var(--loss) 15%,transparent);color:var(--loss)}
.tag.dot::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.big{font-family:var(--disp);font-weight:800;font-size:clamp(30px,6vw,44px);letter-spacing:-.02em;line-height:1}
.big.loss{color:var(--loss)} .big.gain{color:var(--gain)}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.gauge{margin-top:14px}
.gtrack{position:relative;height:12px;border-radius:999px;background:var(--panel-2);overflow:hidden;border:1px solid var(--line)}
.gfill{position:absolute;inset:0 auto 0 0;background:linear-gradient(90deg,var(--copper),var(--copper-2))}
.gmark{position:absolute;top:-5px;bottom:-5px;width:2px;background:var(--ink)}
.grow{display:flex;justify-content:space-between;font-family:var(--mono);font-size:12px;color:var(--ink-2);margin-top:8px}
.metrics{display:flex;flex-direction:column;gap:14px;justify-content:center}
.metric .k{font-family:var(--mono);font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.metric .v{font-family:var(--disp);font-weight:700;font-size:26px;letter-spacing:-.01em}
.chartcard{padding:20px}
.switch{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.switch button{font-family:var(--mono);font-size:12.5px;font-weight:500;color:var(--ink-2);
  background:var(--panel-2);border:1px solid var(--line);border-radius:999px;padding:6px 13px;cursor:pointer;
  transition:.15s}
.switch button[aria-pressed="true"]{background:var(--copper);border-color:var(--copper);color:#fff;font-weight:600}
.switch button:focus-visible{outline:2px solid var(--copper);outline-offset:2px}
figure{margin:0}
svg{display:block;width:100%;height:auto;font-family:var(--mono)}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-top:12px;font-size:12.5px;color:var(--ink-2);font-family:var(--mono)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:16px;height:10px;border-radius:3px;display:inline-block}
.tt{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:9px 11px;font-family:var(--mono);font-size:12px;box-shadow:var(--shadow);opacity:0;transition:opacity .1s;
  min-width:150px;z-index:5}
.tt b{color:var(--ink)} .tt .r{display:flex;justify-content:space-between;gap:14px;color:var(--ink-2);margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:12px 10px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
thead th{font-family:var(--mono);font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600}
td.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
td .pill{font-family:var(--mono);font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px}
.pill.neg{background:color-mix(in srgb,var(--loss) 14%,transparent);color:var(--loss)}
.pill.pos{background:color-mix(in srgb,var(--gain) 16%,transparent);color:var(--gain)}
.rowlive td{background:color-mix(in srgb,var(--copper) 7%,transparent)}
.rowlive td:first-child{box-shadow:inset 3px 0 var(--copper)}
.note{color:var(--ink-2);font-size:14.5px;max-width:66ch}
.note strong{color:var(--ink)}
ul.clean{margin:10px 0 0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:10px}
ul.clean li{padding-left:24px;position:relative;color:var(--ink-2);font-size:14.5px;max-width:64ch}
ul.clean li::before{content:"";position:absolute;left:2px;top:9px;width:9px;height:9px;border-radius:2px;
  background:var(--copper);transform:rotate(45deg)}
.foot{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px;
  font-family:var(--mono);line-height:1.7}
.kicker{color:var(--warn);font-weight:600}
</style>

<div class="wrap">
  <div class="eyebrow">Monte Carlo · 20 000 ścieżek · rzut realnego edge</div>
  <h1>Symulacja GielDarka na najbliższy rok</h1>
  <p class="lede">To nie prognoza rynku — nikt jej nie ma. To rozkład wyników przy założeniu, że
    strategia zachowa swój <em>dotychczasowy, zmierzony</em> edge: trafność 27,8%, wygrana +$2,74 vs
    strata −$1,24 (payoff 2,21×), ~520 zamknięć/rok. Wniosek jest jednoznaczny.</p>

  <div class="verdict">
    <div class="card">
      <span class="tag bad dot">EDGE PONIŻEJ PROGU OPŁACALNOŚCI</span>
      <div style="margin-top:14px" class="big loss">27,8%</div>
      <div class="sub">obecna trafność — przy payoffie 2,21× próg opłacalności to <b style="color:var(--ink)">31,2%</b></div>
      <div class="gauge">
        <div class="gtrack"><div class="gfill" style="width:27.8%"></div><div class="gmark" style="left:31.2%"></div></div>
        <div class="grow"><span>0%</span><span>próg 31,2% ▲</span><span>60%</span></div>
      </div>
      <p class="sub" style="margin-top:12px">Każda transakcja traci średnio <b style="color:var(--loss)">−0,18%</b>
        wystawionego kapitału. Wygrane są 2,2× większe od strat, ale jest ich za mało (15 na 54).</p>
    </div>
    <div class="card metrics">
      <div class="metric"><div class="k">Mediana konta po roku</div>
        <div class="v loss">−27%</div><div class="sub">obecna konfiguracja (auto-deploy)</div></div>
      <div class="metric"><div class="k">Szansa na plus po roku</div>
        <div class="v">~2%</div><div class="sub">na 20 000 symulowanych ścieżek</div></div>
      <div class="metric"><div class="k">Brakuje do opłacalności</div>
        <div class="v" style="color:var(--warn)">+3,4 pp</div><div class="sub">trafności (27,8% → 31,2%)</div></div>
    </div>
  </div>

  <section>
    <h2>Rozkład wartości konta przez rok</h2>
    <p class="sec-note">Mediana i pasma niepewności (5–95% oraz 25–75% ścieżek). Przełącz scenariusz.</p>
    <div class="card chartcard">
      <div class="switch" id="switch"></div>
      <figure style="position:relative">
        <svg id="fan" viewBox="0 0 760 360" role="img" aria-label="Wykres wachlarzowy wartości konta"></svg>
        <div class="tt" id="tt"></div>
      </figure>
      <div class="legend">
        <span><i class="sw" style="background:var(--band-far)"></i>5–95% ścieżek</span>
        <span><i class="sw" style="background:var(--band-mid)"></i>25–75% ścieżek</span>
        <span><i class="sw" style="width:16px;height:3px;border-radius:2px;background:var(--copper)"></i>mediana</span>
        <span><i class="sw" style="width:16px;height:0;border-top:2px dashed var(--silver)"></i>kapitał startowy</span>
      </div>
    </div>
  </section>

  <section>
    <h2>Cztery scenariusze obok siebie</h2>
    <p class="sec-note">Ten sam edge, różna wielkość pozycji / dopłaty / hipoteza o trafności.</p>
    <div class="card" style="padding:6px 14px;overflow-x:auto">
      <table>
        <thead><tr><th>Scenariusz</th><th>Mediana / rok</th><th>Zakres 5–95%</th><th>P(plus)</th><th>Obsun.</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Co realnie odwraca ten wynik</h2>
    <ul class="clean">
      <li><strong>Trafność, nie obrót.</strong> Auto-deploy i rotacja <em>lepiej wykorzystują</em> kapitał,
        ale przy ujemnym edge to pogłębia stratę (mediana −7% → −27%): większe pozycje = większe wahania w obie
        strony, a średnia wciąż na minusie. Sam obrót nie tworzy przewagi.</li>
      <li><strong>Wystarczy +3,4 pp trafności.</strong> Przy payoffie 2,21× granica to 31,2%. Ostatnie 7 dni
        dało 37,5% (mała próba) — gdyby to się utrwaliło, mediana skacze do <span class="kicker">+40%/rok</span>
        (scenariusz 4). Cała gra toczy się o <em>jakość wejść</em>.</li>
      <li><strong>Dźwignie na jakość:</strong> ostrzejszy próg konfluencji (mniej, mocniejszych setupów),
        wyrzucenie chronicznie stratnych nazw (MSTR/MSFT/JAZZ), krótsze trzymanie strat / szybsze cięcie —
        wszystko co podnosi odsetek wygranych powyżej 31%.</li>
      <li><strong>Dopłaty $300/mies</strong> rosną saldo nominalnie (do ~$3,5k), ale to Twoje pieniądze, nie zysk
        — na <em>zainwestowanym</em> kapitale wynik dalej ujemny (−23%). Dopłata to nie edge.</li>
    </ul>
  </section>

  <div class="foot">
    Metoda: 20 000 ścieżek Monte Carlo; każda transakcja = zwrot na wystawionym ułamku konta, losowany z
    realnego rozkładu (wygrana +3,65% / strata −1,65% na pozycji, p=0,278), ~520–680 transakcji/rok, składanie
    kapitału. Dane: /api/audit (54 zamknięcia od 2026-08-10). Założenia upraszczają (stała trafność, brak
    autokorelacji, koszty spreadu ukryte w realnym edge). To projekcja ZMIERZONEJ przewagi, nie prognoza rynku —
    jeśli edge się zmieni, zmieni się wynik.
  </div>
</div>

<script>
const SIM=__DATA__;
const order=["status_quo","auto_deploy","auto_deploy_deposits","better_edge"];
const NS="http://www.w3.org/2000/svg";
let current="auto_deploy";

// --- tabela ---
const tb=document.getElementById("tbody");
for(const k of order){const s=SIM.scenarios[k].summary;const tr=document.createElement("tr");
  if(k==="auto_deploy")tr.className="rowlive";
  const mpos=s.med_pct>=0;
  tr.innerHTML=`<td>${s.label}${k==="auto_deploy"?' <span style="color:var(--copper);font-family:var(--mono);font-size:11px">● LIVE</span>':''}</td>`+
    `<td class="num"><span class="pill ${mpos?'pos':'neg'}">${mpos?'+':''}${s.med_pct.toFixed(0)}%</span></td>`+
    `<td class="num">$${s.p5.toLocaleString()} – $${s.p95.toLocaleString()}</td>`+
    `<td class="num">${s.pprofit}%</td><td class="num">${s.dd}%</td>`;
  tb.appendChild(tr);}

// --- przełącznik ---
const sw=document.getElementById("switch");
for(const k of order){const b=document.createElement("button");b.textContent=SIM.scenarios[k].summary.label.replace(/ \\(.*\\)/,"");
  b.setAttribute("aria-pressed",k===current);b.onclick=()=>{current=k;
    [...sw.children].forEach((c,i)=>c.setAttribute("aria-pressed",order[i]===k));draw();};sw.appendChild(b);}

// --- wykres ---
const svg=document.getElementById("fan"),tt=document.getElementById("tt");
const W=760,H=360,ML=56,MR=18,MT=18,MB=34;
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function draw(){
  while(svg.firstChild)svg.removeChild(svg.firstChild);
  const sc=SIM.scenarios[current],wk=SIM.weeks;
  const lo=Math.min(...sc.p5),hi=Math.max(...sc.p95),start=sc.p50[0];
  const pad=(hi-lo)*0.08||1;const ymin=Math.min(lo,start)-pad,ymax=Math.max(hi,start)+pad;
  const X=i=>ML+(i/(wk.length-1))*(W-ML-MR);
  const Y=v=>MT+(1-(v-ymin)/(ymax-ymin))*(H-MT-MB);
  const mk=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;};
  // siatka Y
  const ticks=4;for(let i=0;i<=ticks;i++){const v=ymin+(ymax-ymin)*i/ticks,y=Y(v);
    svg.appendChild(mk("line",{x1:ML,x2:W-MR,y1:y,y2:y,stroke:css("--line"),"stroke-width":1}));
    const tx=mk("text",{x:ML-9,y:y+4,"text-anchor":"end",fill:css("--muted"),"font-size":11});
    tx.textContent="$"+Math.round(v).toLocaleString();svg.appendChild(tx);}
  // oś X (miesiące)
  for(let m=0;m<=12;m+=3){const i=Math.round(m/12*(wk.length-1)),x=X(i);
    const anc=m===0?"start":(m===12?"end":"middle");
    const tx=mk("text",{x:x,y:H-12,"text-anchor":anc,fill:css("--muted"),"font-size":11});
    tx.textContent=m+" mies";svg.appendChild(tx);}
  const area=(hiA,loA,fill)=>{let d="M"+X(0)+" "+Y(hiA[0]);
    for(let i=1;i<hiA.length;i++)d+="L"+X(i)+" "+Y(hiA[i]);
    for(let i=loA.length-1;i>=0;i--)d+="L"+X(i)+" "+Y(loA[i]);d+="Z";
    svg.appendChild(mk("path",{d,fill,stroke:"none"}));};
  area(sc.p95,sc.p5,css("--band-far"));
  area(sc.p75,sc.p25,css("--band-mid"));
  // linia startu
  svg.appendChild(mk("line",{x1:ML,x2:W-MR,y1:Y(start),y2:Y(start),stroke:css("--silver"),
    "stroke-width":1.5,"stroke-dasharray":"5 4"}));
  // mediana
  let d="M"+X(0)+" "+Y(sc.p50[0]);for(let i=1;i<sc.p50.length;i++)d+="L"+X(i)+" "+Y(sc.p50[i]);
  svg.appendChild(mk("path",{d,fill:"none",stroke:css("--copper"),"stroke-width":2.5,"stroke-linejoin":"round"}));
  // etykieta końca mediany
  const endv=sc.p50[sc.p50.length-1],ep=((endv/start-1)*100);
  const lab=mk("text",{x:W-MR,y:Y(endv)-8,"text-anchor":"end",fill:css("--copper"),"font-size":12,"font-weight":700});
  lab.textContent=(ep>=0?"+":"")+ep.toFixed(0)+"%  $"+Math.round(endv).toLocaleString();svg.appendChild(lab);
  // hover
  const hit=mk("rect",{x:ML,y:MT,width:W-ML-MR,height:H-MT-MB,fill:"transparent"});
  const cross=mk("line",{y1:MT,y2:H-MB,stroke:css("--muted"),"stroke-width":1,opacity:0});
  const dot=mk("circle",{r:4,fill:css("--copper"),stroke:css("--panel"),"stroke-width":2,opacity:0});
  svg.appendChild(cross);svg.appendChild(dot);svg.appendChild(hit);
  hit.addEventListener("pointermove",ev=>{const r=svg.getBoundingClientRect();
    const px=(ev.clientX-r.left)/r.width*W;let i=Math.round((px-ML)/(W-ML-MR)*(wk.length-1));
    i=Math.max(0,Math.min(wk.length-1,i));const x=X(i);
    cross.setAttribute("x1",x);cross.setAttribute("x2",x);cross.setAttribute("opacity",.6);
    dot.setAttribute("cx",x);dot.setAttribute("cy",Y(sc.p50[i]));dot.setAttribute("opacity",1);
    const mo=(i/(wk.length-1)*12).toFixed(1);
    tt.innerHTML=`<b>${mo} mies</b>`+
      `<div class="r"><span>mediana</span><span>$${Math.round(sc.p50[i]).toLocaleString()}</span></div>`+
      `<div class="r"><span>25–75%</span><span>$${Math.round(sc.p25[i]).toLocaleString()}–$${Math.round(sc.p75[i]).toLocaleString()}</span></div>`+
      `<div class="r"><span>5–95%</span><span>$${Math.round(sc.p5[i]).toLocaleString()}–$${Math.round(sc.p95[i]).toLocaleString()}</span></div>`;
    const tx=Math.min(x/W*r.width+14,r.width-165);
    tt.style.left=tx+"px";tt.style.top=(Y(sc.p50[i])/H*r.height-10)+"px";tt.style.opacity=1;});
  hit.addEventListener("pointerleave",()=>{tt.style.opacity=0;cross.setAttribute("opacity",0);dot.setAttribute("opacity",0);});
}
draw();
</script>
"""

out = HTML.replace("__DATA__", DATA)
with open(f"{SCRATCH}/symulacja-roku.html", "w") as f:
    f.write(out)
print("OK", len(out), "bajtów ->", f"{SCRATCH}/symulacja-roku.html")
