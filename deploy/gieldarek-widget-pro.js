// GielDarek - widget iPhone PRO (Scriptable). 100% ASCII, kuloodporny na kopiowanie.
// KAFELEK na ekranie glownym: statyczny (iOS nie animuje widgetow - ograniczenie Apple).
// DOTKNIECIE kafelka: otwiera PELNOEKRANOWY, ANIMOWANY, INTERAKTYWNY widok (HTML/CSS/JS):
//   liczby licza sie w gore, wykres sam sie rysuje, pulsuje, jest przycisk ODSWIEZ.
// WAZNE: przytrzymaj widget -> Edytuj widget -> "When Interacting: Run Script"
//   (nie Open URL), zeby dotkniecie odpalilo ten animowany widok.
// Adres i token juz wpisane. Glowna liczbe wybierasz w apce: Steruj -> Widzet.

var BASE_URL = "https://46.225.229.113.sslip.io";
var SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
var THEME = "iris"; // iris | midnight | light

var PAL = {
  iris:     { a: "#0b1024", b: "#14092b", c: "#0a1730", tx: "#eef3fa", dim: "#9aa7c4", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  midnight: { a: "#05070f", b: "#0a1020", c: "#05070f", tx: "#eef3fa", dim: "#7f8ba6", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  light:    { a: "#eef3fb", b: "#ffffff", c: "#e7eefb", tx: "#0d1526", dim: "#5b6478", up: "#12a074", dn: "#d83a58", br: "#1478c8" }
};
var P = PAL[THEME] || PAL.iris;
var UP = new Color(P.up), TX = new Color(P.tx), DIM = new Color(P.dim), BR = new Color(P.br), DN = new Color(P.dn);

function usd(v, dp) {
  if (v == null || isNaN(v)) return "-";
  if (dp == null) dp = 0;
  var neg = v < 0, n = Math.abs(Number(v)).toFixed(dp), d = n.indexOf(".");
  var ip = d === -1 ? n : n.slice(0, d), fr = d === -1 ? "" : n.slice(d);
  ip = ip.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (neg ? "-$" : "$") + ip + fr;
}
function pctv(v) { return (v == null || isNaN(v)) ? "-" : (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%"; }
function hm() { var d = new Date(); function z(x){return (x<10?"0":"")+x;} return z(d.getHours())+":"+z(d.getMinutes()); }

async function fetchData() {
  var req = new Request(BASE_URL + "/api/widget?share=" + encodeURIComponent(SHARE_TOKEN));
  req.timeoutInterval = 12;
  return await req.loadJSON();
}

// ---------- KAFELEK (statyczny widget) ----------
function bg(w) {
  var g = new LinearGradient();
  g.colors = [new Color(P.a), new Color(P.b), new Color(P.c)];
  g.locations = [0, 0.55, 1]; g.startPoint = new Point(0, 0); g.endPoint = new Point(1, 1);
  w.backgroundGradient = g; w.backgroundColor = new Color(P.a);
}
function spark(series, w, h, hex) {
  var dc = new DrawContext(); dc.size = new Size(w, h); dc.opaque = false; dc.respectScreenScale = true;
  if (!series || series.length < 2) return dc.getImage();
  var lo = Math.min.apply(null, series), hi = Math.max.apply(null, series), span = (hi - lo) || 1, i;
  function xx(i){return (i/(series.length-1))*w;} function yy(v){return h-((v-lo)/span)*(h-6)-3;}
  var f = new Path(); f.move(new Point(0,h));
  for (i=0;i<series.length;i++) f.addLine(new Point(xx(i),yy(series[i])));
  f.addLine(new Point(w,h)); f.closeSubpath();
  dc.setFillColor(new Color(hex,0.16)); dc.addPath(f); dc.fillPath();
  var l = new Path(); l.move(new Point(0,yy(series[0])));
  for (i=1;i<series.length;i++) l.addLine(new Point(xx(i),yy(series[i])));
  dc.setStrokeColor(new Color(hex)); dc.setLineWidth(2.4); dc.addPath(l); dc.strokePath();
  var lx=xx(series.length-1), ly=yy(series[series.length-1]);
  dc.setFillColor(new Color(hex)); dc.fillEllipse(new Rect(lx-3,ly-3,6,6));
  return dc.getImage();
}
function buildTile(w, d, fam) {
  bg(w); w.setPadding(14, 16, 13, 16);
  var prim = d.primary || {};
  var r = w.addStack(); r.centerAlignContent();
  var m1 = r.addText("GIEL"); m1.font = Font.heavySystemFont(11); m1.textColor = TX;
  var m2 = r.addText("DAREK"); m2.font = Font.heavySystemFont(11); m2.textColor = BR;
  r.addSpacer();
  var lv = r.addText(d.mode === "live" ? "LIVE" : "PAPER"); lv.font = Font.mediumSystemFont(8);
  lv.textColor = d.mode === "live" ? UP : DIM;
  w.addSpacer(fam === "small" ? 6 : 8);
  var lbl = w.addText((prim.label || "Zysk automatu").toUpperCase()); lbl.font = Font.mediumSystemFont(9); lbl.textColor = DIM;
  w.addSpacer(2);
  var vc = (prim.metric === "account" || prim.metric === "positions") ? BR : (prim.up ? UP : DN);
  var val = w.addText(prim.text || "-"); val.font = Font.boldSystemFont(fam === "small" ? 28 : 38);
  val.textColor = vc; val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  val.shadowColor = new Color(P.br, 0.5); val.shadowRadius = 8;
  if (fam !== "small") {
    w.addSpacer(8);
    var img = w.addImage(spark(d.spark, fam === "large" ? 300 : 260, fam === "large" ? 60 : 46, prim.up === false ? P.dn : P.up));
    img.imageSize = new Size(fam === "large" ? 300 : 260, fam === "large" ? 60 : 46);
  }
  w.addSpacer(6);
  var sub = w.addText("konto " + usd(d.total) + "   " + pctv(d.day_pnl_pct) + " dzis   (dotknij: zywy widok)");
  sub.font = Font.systemFont(10); sub.textColor = DIM; sub.minimumScaleFactor = 0.6; sub.lineLimit = 1;
  w.addSpacer();
  var ft = w.addStack(); ft.addSpacer();
  var ts = ft.addText("akt. " + hm()); ts.font = Font.systemFont(8); ts.textColor = DIM;
}

// ---------- ANIMOWANY WIDOK PELNOEKRANOWY (HTML WebView) ----------
function pageHTML() {
  // HTML/CSS/JS z prawdziwymi animacjami. Dane pobiera SAM z API (przycisk odswiez
  // dziala na zywo). ASCII w kodzie; polskie napisy przychodza z serwera / prostych stalych.
  var css =
    "*{box-sizing:border-box;margin:0;padding:0;-webkit-user-select:none}"+
    "body{font-family:-apple-system,system-ui,sans-serif;background:radial-gradient(120% 90% at 20% 0%,"+P.b+" 0%,"+P.a+" 55%,"+P.c+" 100%);color:"+P.tx+";min-height:100vh;padding:26px 22px;overflow-x:hidden}"+
    ".hd{display:flex;align-items:center;gap:8px;font-weight:800;letter-spacing:.5px}"+
    ".hd .b{color:"+P.br+"}.dot{margin-left:auto;width:9px;height:9px;border-radius:50%;background:"+P.up+";box-shadow:0 0 0 0 "+P.up+";animation:pulse 1.8s infinite}"+
    "@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(36,230,166,.6)}70%{box-shadow:0 0 0 12px rgba(36,230,166,0)}100%{box-shadow:0 0 0 0 rgba(36,230,166,0)}}"+
    ".lab{margin-top:26px;font-size:12px;letter-spacing:2px;color:"+P.dim+"}"+
    ".big{font-size:64px;font-weight:800;line-height:1.05;margin-top:4px;text-shadow:0 0 24px rgba(52,220,255,.35)}"+
    ".sub{color:"+P.dim+";margin-top:8px;font-size:15px}"+
    "svg{width:100%;height:120px;margin-top:22px;overflow:visible}"+
    ".area{opacity:0;animation:fade 1.2s .3s forwards}.line{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:2000;stroke-dashoffset:2000;animation:draw 1.8s cubic-bezier(.4,0,.2,1) forwards}"+
    "@keyframes draw{to{stroke-dashoffset:0}}@keyframes fade{to{opacity:1}}"+
    ".row{display:flex;gap:10px;margin-top:22px}.card{flex:1;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:14px}"+
    ".card .k{font-size:11px;color:"+P.dim+"}.card .v{font-size:20px;font-weight:700;margin-top:4px}"+
    ".pos{margin-top:22px}.pos h4{font-size:12px;letter-spacing:2px;color:"+P.dim+";margin-bottom:10px}"+
    ".pr{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid rgba(255,255,255,.06);opacity:0;transform:translateY(8px);animation:slide .5s forwards}"+
    "@keyframes slide{to{opacity:1;transform:none}}"+
    ".btn{display:block;width:100%;margin-top:26px;padding:15px;border:0;border-radius:16px;background:linear-gradient(90deg,"+P.br+","+P.up+");color:#04121c;font-size:16px;font-weight:800;letter-spacing:.5px}"+
    ".btn:active{transform:scale(.97)}.up{color:"+P.up+"}.dn{color:"+P.dn+"}";
  var js =
    "var API='"+BASE_URL+"/api/widget?share="+encodeURIComponent(SHARE_TOKEN)+"';"+
    "function usd(v,dp){if(v==null||isNaN(v))return '-';dp=dp||0;var neg=v<0,n=Math.abs(+v).toFixed(dp),d=n.indexOf('.');var ip=d<0?n:n.slice(0,d),fr=d<0?'':n.slice(d);ip=ip.replace(/\\B(?=(\\d{3})+(?!\\d))/g,' ');return (neg?'-$':'$')+ip+fr;}"+
    "function pc(v){return v==null||isNaN(v)?'-':(v>=0?'+':'')+(+v).toFixed(1)+'%';}"+
    "function countUp(el,to,pre){var st=null,dur=900;function f(t){if(!st)st=t;var p=Math.min(1,(t-st)/dur);var e=1-Math.pow(1-p,3);el.textContent=pre+usd(to*e,0).replace('$','$');if(p<1)requestAnimationFrame(f);else el.textContent=pre+usd(to,0);}requestAnimationFrame(f);}"+
    "function path(series,w,h){if(!series||series.length<2)return['',''];var lo=Math.min.apply(null,series),hi=Math.max.apply(null,series),sp=(hi-lo)||1;var pts=series.map(function(v,i){return [i/(series.length-1)*w,h-((v-lo)/sp)*(h-10)-5];});var l='M'+pts.map(function(p){return p[0].toFixed(1)+' '+p[1].toFixed(1);}).join(' L');var a=l+' L'+w+' '+h+' L0 '+h+' Z';return [l,a];}"+
    "function render(d){var prim=d.primary||{};document.getElementById('lab').textContent=(prim.label||'Zysk automatu').toUpperCase();"+
    "var big=document.getElementById('big');var up=prim.up!==false;big.className='big '+(prim.metric==='account'||prim.metric==='positions'?'':(up?'up':'dn'));"+
    "var num=parseFloat(String(prim.text||'').replace(/[^0-9.-]/g,''));if(isNaN(num)){big.textContent=prim.text||'-';}else{countUp(big,num,prim.text&&prim.text.indexOf('-')===0?'-$':(prim.text&&prim.text.indexOf('+')===0?'+$':'$'));}"+
    "document.getElementById('sub').textContent='konto '+usd(d.total)+'  .  '+pc(d.day_pnl_pct)+' dzis  .  '+(d.market_open?'rynek otwarty':'rynek zamkniety');"+
    "var col=up?'"+P.up+"':'"+P.dn+"';var pp=path(d.spark||[],320,120);var svg=document.getElementById('chart');svg.innerHTML='<defs><linearGradient id=g x1=0 y1=0 x2=0 y2=1><stop offset=0% stop-color=\"'+col+'\" stop-opacity=.35/><stop offset=100% stop-color=\"'+col+'\" stop-opacity=0/></linearGradient></defs><path class=area d=\"'+pp[1]+'\" fill=url(#g)/><path class=line d=\"'+pp[0]+'\" stroke=\"'+col+'\"/>';"+
    "var e=d.edge||{};document.getElementById('wr').textContent=(d.win_rate==null?'-':d.win_rate+'%');document.getElementById('ed').textContent=(e.avg_win_usd!=null?'+'+usd(e.avg_win_usd,0)+' / '+usd(e.avg_loss_usd,0):(d.closed||0)+' zamk.');document.getElementById('cash').textContent=usd(d.cash);"+
    "var box=document.getElementById('pos');var ps=(d.positions||[]).slice(0,6);if(!ps.length){box.innerHTML='<h4>POZYCJE</h4><div style=\"color:"+P.dim+"\">Brak pozycji - gotowka czeka.</div>';}else{var html='<h4>POZYCJE</h4>';ps.forEach(function(p,i){var g=(p.pnl_pct!=null?p.pnl_pct:p.change_pct);html+='<div class=pr style=\"animation-delay:'+(i*70+300)+'ms\"><b>'+(p.symbol||p.asset||'?')+'</b><span class='+((g||0)>=0?'up':'dn')+'>'+usd(p.value,0)+'   '+(g!=null?pc(g):'')+'</span></div>';});box.innerHTML=html;}}"+
    "function load(){fetch(API).then(function(r){return r.json();}).then(render).catch(function(){document.getElementById('big').textContent='brak polaczenia';});}"+
    "document.getElementById('rf').addEventListener('click',function(){document.querySelectorAll('.line').forEach(function(x){});load();});"+
    "load();";
  var html =
    "<!DOCTYPE html><html><head><meta name=viewport content='width=device-width,initial-scale=1,maximum-scale=1'><style>"+css+"</style></head><body>"+
    "<div class=hd><span>GIEL<span class=b>DAREK</span></span><span class=dot></span></div>"+
    "<div class=lab id=lab>ZYSK AUTOMATU</div><div class=big id=big>...</div><div class=sub id=sub></div>"+
    "<svg id=chart viewBox='0 0 320 120' preserveAspectRatio=none></svg>"+
    "<div class=row><div class=card><div class=k>Skutecznosc</div><div class=v id=wr>-</div></div>"+
    "<div class=card><div class=k>Wygrana/strata</div><div class=v id=ed>-</div></div>"+
    "<div class=card><div class=k>Gotowka</div><div class=v id=cash>-</div></div></div>"+
    "<div class=pos id=pos></div>"+
    "<button class=btn id=rf>ODSWIEZ</button>"+
    "</body></html>";
  return html;
}

async function run() {
  if (config.runsInWidget) {
    var w = new ListWidget();
    var d;
    try { d = await fetchData(); } catch (e) {
      bg(w); var t = w.addText("GielDarek - brak polaczenia"); t.textColor = DN; t.font = Font.systemFont(12);
      Script.setWidget(w); Script.complete(); return;
    }
    buildTile(w, d, config.widgetFamily || "medium");
    Script.setWidget(w);
    Script.complete();
    return;
  }
  // Dotkniecie / uruchomienie w apce -> pelnoekranowy ANIMOWANY widok.
  var wv = new WebView();
  await wv.loadHTML(pageHTML());
  await wv.present(true);
  Script.complete();
}
await run();
