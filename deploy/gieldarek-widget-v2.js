// GielDarek — widget iPhone v2 (Scriptable) "Iris Terminal".
// GOTOWY DO WKLEJENIA — adres i token już wpisane niżej. Parameter zostaw PUSTE.
// KAFELEK na ekranie głównym: czysty, nowoczesny, STATYCZNY (iOS nie animuje
// kafelków — odświeża co kilka minut). DOTKNIĘCIE kafelka otwiera PEŁNOEKRANOWY
// ANIMOWANY widok (liczby liczą się w górę, pierścień i wykres się rysują,
// puls pulsuje). Wszystko read-only (GET /api/widget?share=...).
// =============================================================================
// INSTALACJA: Scriptable -> "+" -> wklej CAŁY plik -> nazwij "GielDarek v2".
// Ekran główny -> przytrzymaj -> "+" -> Scriptable -> wybierz skrypt -> rozmiar.
// Podgląd animacji: w Scriptable naciśnij ▶ (Run).
// =============================================================================

let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

const HEX = {
  ink: "#070b16", text: "#eef3fa", dim: "#8593ab", faint: "#5b6478",
  mint: "#24e6a6", rose: "#ff5c7a", gold: "#ffd36b", brand: "#34dcff", brand2: "#9b6bff",
};
const C = {};
for (const k in HEX) C[k] = new Color(HEX[k]);

function fmtUsd(v, dp) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  if (dp === undefined) dp = 2;
  const neg = v < 0;
  let n = Math.abs(Number(v)).toFixed(dp);
  const dot = n.indexOf(".");
  let intp = dot === -1 ? n : n.slice(0, dot);
  const frac = dot === -1 ? "" : n.slice(dot);
  intp = intp.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (neg ? "−$" : "$") + intp + frac;
}
function fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + Number(v).toFixed(2) + "%";
}
function fmtSigned(v, dp) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + fmtUsd(v, dp === undefined ? 0 : dp);
}
const clamp01 = (x) => Math.max(0, Math.min(1, x));

const base = () => BASE_URL.replace(/\/$/, "");
async function fetchWidget() {
  const req = new Request(`${base()}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 20;
  const data = await req.loadJSON();
  const status = req.response ? req.response.statusCode : 200;
  return { data, status };
}

// ============================ KAFELEK (statyczny) ============================
function pill(parent, text, hex, size) {
  const s = parent.addStack();
  s.setPadding(3, 9, 3, 9);
  s.cornerRadius = 9;
  s.backgroundColor = new Color(hex, 0.2);
  s.centerAlignContent();
  const t = s.addText(text);
  t.font = Font.semiboldSystemFont(size || 11);
  t.textColor = new Color(hex);
  t.lineLimit = 1;
  return s;
}
function label(parent, text) {
  const l = parent.addText(text);
  l.font = Font.mediumSystemFont(8.5);
  l.textColor = C.faint;
  return l;
}
// czysty gauge (pierścień) z liczbą w środku
function drawGauge(size, frac, hex, centerText, sub) {
  const ctx = new DrawContext();
  ctx.size = new Size(size, size);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const cx = size / 2, cy = size / 2;
  const th = size * 0.11, r = size / 2 - th / 2 - 1, dot = th / 2, steps = 180;
  for (let k = 0; k < steps; k++) {
    const ang = -Math.PI / 2 + (k / steps) * 2 * Math.PI;
    ctx.setFillColor(new Color(hex, 0.13));
    ctx.fillEllipse(new Rect(cx + r * Math.cos(ang) - dot, cy + r * Math.sin(ang) - dot, dot * 2, dot * 2));
  }
  if (frac !== null && frac !== undefined) {
    const pd = Math.round(steps * clamp01(frac));
    for (let k = 0; k <= pd; k++) {
      const ang = -Math.PI / 2 + (k / steps) * 2 * Math.PI;
      ctx.setFillColor(new Color(hex));
      ctx.fillEllipse(new Rect(cx + r * Math.cos(ang) - dot, cy + r * Math.sin(ang) - dot, dot * 2, dot * 2));
    }
    if (frac > 0.003) {
      const ang = -Math.PI / 2 + (pd / steps) * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color("#ffffff", 0.92));
      ctx.fillEllipse(new Rect(x - dot * 0.45, y - dot * 0.45, dot * 0.9, dot * 0.9));
    }
  }
  ctx.setTextAlignedCenter();
  ctx.setFont(Font.boldSystemFont(size * 0.28));
  ctx.setTextColor(new Color(hex));
  ctx.drawTextInRect(centerText, new Rect(0, cy - size * 0.215, size, size * 0.3));
  ctx.setFont(Font.mediumSystemFont(size * 0.085));
  ctx.setTextColor(C.faint);
  ctx.drawTextInRect(sub, new Rect(0, cy + size * 0.11, size, size * 0.16));
  return ctx.getImage();
}
function drawSpark(spark, w, h) {
  const vals = (spark || []).map(Number).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const min = Math.min.apply(null, vals), max = Math.max.apply(null, vals), range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0], colHex = up ? HEX.mint : HEX.rose, pad = 3;
  const ctx = new DrawContext();
  ctx.size = new Size(w, h); ctx.opaque = false; ctx.respectScreenScale = true;
  const pt = (i) => new Point(pad + (i / (vals.length - 1)) * (w - 2 * pad), h - pad - ((vals[i] - min) / range) * (h - 2 * pad));
  for (const a of [0.07, 0.16]) {
    const f = new Path(); f.move(new Point(pad, h - pad));
    for (let i = 0; i < vals.length; i++) f.addLine(pt(i));
    f.addLine(new Point(w - pad, h - pad)); f.closeSubpath();
    ctx.setFillColor(new Color(colHex, a)); ctx.addPath(f); ctx.fillPath();
  }
  const p = new Path(); p.move(pt(0));
  for (let i = 1; i < vals.length; i++) p.addLine(pt(i));
  ctx.setStrokeColor(new Color(colHex)); ctx.setLineWidth(2.6); ctx.addPath(p); ctx.strokePath();
  const last = pt(vals.length - 1);
  ctx.setFillColor(new Color(colHex)); ctx.fillEllipse(new Rect(last.x - 2.6, last.y - 2.6, 5.2, 5.2));
  return ctx.getImage();
}
function accentLine(w) {
  const s = w.addStack(); s.size = new Size(0, 3); s.cornerRadius = 2;
  const g = new LinearGradient(); g.colors = [C.brand, C.brand2]; g.locations = [0, 1];
  g.startPoint = new Point(0, 0); g.endPoint = new Point(1, 0);
  s.backgroundGradient = g; s.addSpacer();
  return s;
}
function errorTile(w, title, msg) {
  const h = w.addStack(); const m = h.addText("◈"); m.font = Font.boldSystemFont(12); m.textColor = C.brand;
  h.addSpacer(6); const t = h.addText("GIELDAREK"); t.font = Font.boldSystemFont(12); t.textColor = C.text;
  w.addSpacer(8);
  const e = w.addText(title); e.textColor = C.rose; e.font = Font.semiboldSystemFont(14);
  w.addSpacer(3); const mm = w.addText(msg); mm.textColor = C.dim; mm.font = Font.systemFont(10); mm.lineLimit = 4;
}

function buildTile(d, fam) {
  const w = new ListWidget();
  const small = fam === "small", large = fam === "large";
  const g = new LinearGradient();
  g.colors = [new Color("#111a33"), new Color("#070a14"), C.ink];
  g.locations = [0, 0.55, 1];
  g.startPoint = new Point(0, 0); g.endPoint = new Point(0.9, 1);
  w.backgroundGradient = g;
  w.setPadding(14, 15, 13, 15);
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

  if (!d) { errorTile(w, "Brak danych", "Sprawdź token / połączenie."); return w; }

  const pnl = d.trading_pnl_usd, pnlUp = (pnl === null || pnl === undefined || pnl >= 0), pnlHex = pnlUp ? HEX.mint : HEX.rose;
  const dayUp = (d.day_pnl_pct === null || d.day_pnl_pct === undefined || d.day_pnl_pct >= 0);
  const wr = d.win_rate, wrHex = (wr == null) ? HEX.dim : wr >= 50 ? HEX.mint : wr >= 35 ? HEX.gold : HEX.rose;
  const positions = d.positions || [];

  accentLine(w);
  w.addSpacer(9);
  const top = w.addStack(); top.centerAlignContent();
  const mk = top.addText("◈"); mk.font = Font.boldSystemFont(12); mk.textColor = C.brand;
  top.addSpacer(6);
  const br = top.addText("GIELDAREK"); br.font = Font.boldSystemFont(12); br.textColor = C.text;
  top.addSpacer();
  pill(top, d.market_open ? "● rynek" : "○ zamkn.", d.market_open ? HEX.mint : HEX.faint, 9);
  top.addSpacer(5);
  pill(top, d.mode === "live" ? "LIVE" : "PAPER", d.mode === "live" ? HEX.brand : HEX.dim, 9);

  w.addSpacer(small ? 9 : 12);
  const hero = w.addStack(); hero.centerAlignContent();
  const gSize = small ? 76 : large ? 106 : 94;
  const gi = hero.addImage(drawGauge(gSize, (wr == null) ? null : wr / 100, wrHex, (wr == null) ? "—" : wr + "%", "SKUTECZNOŚĆ"));
  gi.imageSize = new Size(gSize, gSize);
  hero.addSpacer(small ? 11 : 16);
  const right = hero.addStack(); right.layoutVertically();
  label(right, "ZYSK AUTOMATU");
  right.addSpacer(3);
  const val = right.addText(fmtSigned(pnl, small ? 0 : 2));
  val.font = Font.boldSystemFont(small ? 24 : 32); val.textColor = new Color(pnlHex);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  val.shadowColor = new Color(pnlHex, 0.5); val.shadowRadius = 9; val.shadowOffset = new Point(0, 0);
  right.addSpacer(8);
  const sub = right.addStack(); sub.centerAlignContent();
  pill(sub, (dayUp ? "▲ " : "▼ ") + fmtPct(d.day_pnl_pct) + " dziś", dayUp ? HEX.mint : HEX.rose, 10.5);
  if (!small) { right.addSpacer(6); const acc = right.addText("Konto " + fmtUsd(d.total, 0)); acc.font = Font.mediumSystemFont(10.5); acc.textColor = C.dim; }

  if (small) { w.addSpacer(); return w; }

  w.addSpacer(12);
  const sp = drawSpark(d.spark, 320, large ? 50 : 42);
  if (sp) { const wi = w.addImage(sp); wi.imageSize = new Size(320, large ? 50 : 42); wi.centerAlignImage(); }

  if (!large) { w.addSpacer(); return w; }

  w.addSpacer(11); label(w, "POZYCJE"); w.addSpacer(6);
  if (positions.length === 0) { const n = w.addText("Brak pozycji — gotówka czeka na wejścia."); n.font = Font.systemFont(10.5); n.textColor = C.dim; }
  else {
    for (const p of positions.slice(0, 4)) {
      const row = w.addStack(); row.centerAlignContent(); row.setPadding(6, 10, 6, 10); row.cornerRadius = 11;
      row.backgroundColor = new Color("#ffffff", 0.05);
      const dot = row.addText("●"); dot.font = Font.boldSystemFont(9); dot.textColor = p.leg === "extended" ? C.brand2 : C.brand;
      row.addSpacer(7); const sym = row.addText(p.asset); sym.font = Font.semiboldSystemFont(12.5); sym.textColor = C.text;
      row.addSpacer(); const v = row.addText(fmtUsd(p.value, 0)); v.font = Font.systemFont(11); v.textColor = C.dim; row.addSpacer(9);
      if (p.pnl_pct == null) { const dd = row.addText("—"); dd.font = Font.semiboldSystemFont(10.5); dd.textColor = C.dim; }
      else pill(row, fmtPct(p.pnl_pct), p.pnl_pct >= 0 ? HEX.mint : HEX.rose, 10.5);
      w.addSpacer(6);
    }
  }
  w.addSpacer();
  return w;
}

// ===================== ANIMOWANY WIDOK (WebView, po dotknięciu) ==============
function animatedHTML(d) {
  const DATA = JSON.stringify(d || {});
  return `<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">
<style>
:root{--ink:#070b16;--text:#eef3fa;--dim:#8593ab;--faint:#5b6478;--mint:#24e6a6;--rose:#ff5c7a;--gold:#ffd36b;--brand:#34dcff;--brand2:#9b6bff}
*{box-sizing:border-box;margin:0;padding:0;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
html,body{height:100%;background:var(--ink);color:var(--text);font-family:-apple-system,system-ui,"SF Pro Display",sans-serif;overflow:hidden}
body::before{content:"";position:fixed;inset:-45%;z-index:0;
 background:radial-gradient(38% 38% at 22% 16%,rgba(52,220,255,.30),transparent 60%),radial-gradient(44% 44% at 84% 88%,rgba(155,107,255,.28),transparent 60%);
 animation:drift 16s ease-in-out infinite alternate}
@keyframes drift{from{transform:translate(-4%,-3%) scale(1)}to{transform:translate(5%,5%) scale(1.16)}}
.wrap{position:relative;z-index:1;height:100%;padding:max(30px,env(safe-area-inset-top)) 24px 28px;display:flex;flex-direction:column;gap:14px}
.top{display:flex;align-items:center;gap:8px}
.brand{font-weight:800;letter-spacing:.16em;font-size:15px}.brand b{color:var(--brand)}
.live{margin-left:auto;display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:700}
.live i{width:8px;height:8px;border-radius:50%;background:var(--mint)}
.live.on i{animation:blip 1.6s infinite}
@keyframes blip{0%{box-shadow:0 0 0 0 rgba(36,230,166,.6)}70%{box-shadow:0 0 0 9px transparent}100%{box-shadow:0 0 0 0 transparent}}
.cap{font-size:11px;letter-spacing:.2em;color:var(--dim);text-transform:uppercase;margin-top:6px}
.big{font-size:54px;font-weight:800;line-height:1.02;margin-top:6px;text-shadow:0 0 26px currentColor;font-variant-numeric:tabular-nums}
.sub{display:flex;align-items:center;gap:11px;margin-top:12px;color:var(--dim);font-size:15px}
.pill{padding:5px 12px;border-radius:999px;font-weight:800;font-size:13px}
.mid{display:flex;align-items:center;gap:22px;margin-top:14px}
.ring{position:relative;width:132px;height:132px;flex:0 0 auto}
.ring svg{transform:rotate(-90deg)}
.ring .arc{transition:stroke-dashoffset 1.25s cubic-bezier(.22,1,.36,1)}
.ring .v{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring .v b{font-size:30px;font-weight:800;font-variant-numeric:tabular-nums}
.ring .v small{font-size:9px;letter-spacing:.14em;color:var(--dim);text-transform:uppercase;margin-top:3px}
.sk .lbl{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.12em}
.sk .leg{margin-top:9px;font-size:15px;font-weight:800}
.spark{margin-top:8px}
.spark svg{width:100%;height:76px;display:block;overflow:visible}
.spark .ln{fill:none;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1400;stroke-dashoffset:1400;animation:draw 1.5s .25s ease forwards}
@keyframes draw{to{stroke-dashoffset:0}}
.pos{display:flex;flex-direction:column;gap:9px;margin-top:4px;overflow:auto}
.row{display:flex;align-items:center;gap:11px;background:rgba(255,255,255,.055);border-radius:14px;padding:11px 14px;opacity:0;transform:translateY(9px);animation:in .55s forwards}
@keyframes in{to{opacity:1;transform:none}}
.row .dot{width:9px;height:9px;border-radius:50%}
.row .sym{font-weight:800;font-size:15px}
.row .val{margin-left:auto;color:var(--dim);font-size:13px}
.row .p{font-weight:800;font-size:14px;font-variant-numeric:tabular-nums}
.hint{position:absolute;left:0;right:0;bottom:calc(10px + env(safe-area-inset-bottom));text-align:center;color:var(--faint);font-size:11px;z-index:1}
</style></head><body><div class=wrap id=app></div><div class=hint>GielDarek · dotknij ▶ Run by odświeżyć</div>
<script>
var D=${DATA};
function el(id){return document.getElementById(id);}
function usd(v,dp){if(v==null||isNaN(v))return "—";dp=dp==null?2:dp;var neg=v<0;var n=Math.abs(v).toFixed(dp).split(".");n[0]=n[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g," ");return (neg?"−$":"$")+n.join(".");}
function pct(v){if(v==null||isNaN(v))return "—";return (v>=0?"+":"")+Number(v).toFixed(2)+"%";}
function animCount(node,to,dur,fmt){var t0=performance.now();function tick(t){var p=Math.min(1,(t-t0)/dur);var e=1-Math.pow(1-p,3);node.textContent=fmt(to*e);if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
var pnl=D.trading_pnl_usd,up=(pnl==null||pnl>=0),pc=up?"var(--mint)":"var(--rose)";
var wr=D.win_rate,wrc=(wr==null)?"var(--dim)":(wr>=50?"var(--mint)":wr>=35?"var(--gold)":"var(--rose)");
var day=D.day_pnl_pct,dup=(day==null||day>=0);
var sv=(D.spark||[]).map(Number).filter(function(x){return x>0;});
var spark="";
if(sv.length>1){var mn=Math.min.apply(null,sv),mx=Math.max.apply(null,sv),rg=(mx-mn)||1,W=340,H=76,P=5;
 var scol=sv[sv.length-1]>=sv[0]?"var(--mint)":"var(--rose)";
 var pts=sv.map(function(v,i){var x=P+i/(sv.length-1)*(W-2*P);var y=H-P-((v-mn)/rg)*(H-2*P);return x.toFixed(1)+","+y.toFixed(1);});
 var area="M"+P+","+(H-P)+" L"+pts.join(" L")+" L"+(W-P)+","+(H-P)+" Z";
 spark='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio=none><defs><linearGradient id=g x1=0 y1=0 x2=0 y2=1><stop offset=0% stop-color="'+scol+'" stop-opacity=.28/><stop offset=100% stop-color="'+scol+'" stop-opacity=0/></linearGradient></defs><path d="'+area+'" fill="url(#g)"/><polyline class=ln stroke="'+scol+'" points="'+pts.join(" ")+'"/></svg>';}
var R=54,CIRC=2*Math.PI*R,off=CIRC*(1-(wr==null?0:wr/100));
var pos="";var ps=D.positions||[];
if(ps.length){pos='<div class=pos>';ps.slice(0,6).forEach(function(p,i){var pu=(p.pnl_pct==null||p.pnl_pct>=0);pos+='<div class=row style="animation-delay:'+(0.15+i*0.08)+'s"><span class=dot style="background:'+(p.leg=="extended"?"var(--brand2)":"var(--brand)")+'"></span><span class=sym>'+p.asset+'</span><span class=val>'+usd(p.value,0)+'</span><span class=p style="color:'+(pu?"var(--mint)":"var(--rose)")+'">'+(p.pnl_pct==null?"—":pct(p.pnl_pct))+'</span></div>';});pos+='</div>';}
el("app").innerHTML=
 '<div class=top><span class=brand>GIEL<b>DAREK</b></span><span class="live '+(D.market_open?"on":"")+'" style="color:'+(D.market_open?"var(--mint)":"var(--dim)")+'"><i style="background:'+(D.market_open?"var(--mint)":"var(--dim)")+'"></i>'+(D.market_open?"rynek otwarty":"rynek zamknięty")+'</span></div>'
+'<div><div class=cap>Zysk automatu · bez Twoich wpłat</div><div class=big id=hero style="color:'+pc+'">—</div>'
+'<div class=sub>Konto '+usd(D.total,0)+'<span class=pill style="background:'+(dup?"rgba(36,230,166,.16)":"rgba(255,92,122,.16)")+';color:'+(dup?"var(--mint)":"var(--rose)")+'">'+(dup?"▲ ":"▼ ")+pct(day)+' dziś</span></div></div>'
+'<div class=mid><div class=ring><svg width=132 height=132><circle cx=66 cy=66 r='+R+' fill=none stroke="rgba(255,255,255,.09)" stroke-width=10/><circle id=arc class=arc cx=66 cy=66 r='+R+' fill=none stroke="'+wrc+'" stroke-width=10 stroke-linecap=round stroke-dasharray='+CIRC.toFixed(1)+' stroke-dashoffset='+CIRC.toFixed(1)+' style="filter:drop-shadow(0 0 7px '+wrc+')"/></svg><div class=v><b id=wr style="color:'+wrc+'">'+(wr==null?"—":"0%")+'</b><small>skuteczność</small></div></div>'
+'<div class=sk><div class=lbl>Skuteczność</div><div class=leg>'+(D.closed?('<span style="color:var(--mint)">'+D.wins+' udane</span> · <span style="color:var(--rose)">'+D.losses+' stratne</span>'):'za mało danych')+'</div></div></div>'
+'<div class=spark>'+spark+'</div>'+pos;
animCount(el("hero"),pnl==null?0:pnl,1300,function(v){return (v>=0?"+":"")+usd(v,2);});
if(wr!=null){setTimeout(function(){el("arc").style.strokeDashoffset=off.toFixed(1);},90);animCount(el("wr"),wr,1300,function(v){return Math.round(v)+"%";});}
</script></body></html>`;
}

// ================================ MAIN ======================================
async function main() {
  let d = null, err = null;
  if (!SHARE_TOKEN) { err = "Brak tokenu"; }
  else {
    try {
      const res = await fetchWidget();
      if (res.status >= 400 || !res.data || res.data.detail || res.data.total === undefined) {
        err = res.status === 401 ? "Zły/brak SHARE_TOKEN" : `Serwer zwrócił ${res.status}`;
      } else d = res.data;
    } catch (e) { err = String((e && e.message) || e); }
  }

  if (config.runsInWidget) {
    const w = d ? buildTile(d, config.widgetFamily || "medium") : (() => { const x = new ListWidget(); x.backgroundColor = C.ink; x.setPadding(14, 15, 13, 15); errorTile(x, "Brak dostępu", err || "—"); return x; })();
    Script.setWidget(w);
    Script.complete();
    return;
  }

  // Uruchomienie ręczne / dotknięcie -> PEŁNOEKRANOWY animowany widok.
  if (!d) { const a = new Alert(); a.title = "GielDarek"; a.message = err || "Brak danych"; a.addAction("OK"); await a.present(); Script.complete(); return; }
  const wv = new WebView();
  await wv.loadHTML(animatedHTML(d));
  await wv.present(true);
  Script.complete();
}

await main();
