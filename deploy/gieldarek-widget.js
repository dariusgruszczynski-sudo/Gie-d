// GielDarek — widget iPhone (Scriptable), styl Apple Fitness: pierścienie
// aktywności = skład konta (W grze / Gotówka), duże liczby, legenda z kropkami
// (w tym "Zysk automatu"), wykres. Ciągnie GET /api/widget?share=... (tylko odczyt).
// (Widżety iOS nie animują się na żywo — system je odświeża; tu stawiamy na
//  bogaty, żywy wygląd: pierścienie z poświatą, gradientowy wykres.)
// =============================================================================
// INSTALACJA: Scriptable -> "+" -> wklej CAŁY plik -> nazwij "GielDarek".
// Ekran główny -> przytrzymaj -> "+" -> Scriptable -> rozmiar -> Dodaj.
// Parameter:  https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN
// (albo wklej token w SHARE_TOKEN niżej). ŚREDNI = pierścienie+legenda+wykres,
// DUŻY = do tego pozycje.
// =============================================================================

let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "";
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

const HEX = {
  ink: "#05080f", ink2: "#0b1120", text: "#eef3fa", dim: "#7c8aa2", faint: "#4f5c73",
  mint: "#19e39a", amber: "#ffae34", blue: "#8fa3c8", rose: "#ff5470",
};
const C = {
  ink: new Color(HEX.ink), ink2: new Color(HEX.ink2), text: new Color(HEX.text),
  dim: new Color(HEX.dim), faint: new Color(HEX.faint),
  mint: new Color(HEX.mint), amber: new Color(HEX.amber), blue: new Color(HEX.blue), rose: new Color(HEX.rose),
};

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
const isUp = (v) => v === null || v === undefined || v >= 0;

const base = () => BASE_URL.replace(/\/$/, "");
async function fetchWidget() {
  const req = new Request(`${base()}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 20;
  const data = await req.loadJSON();
  const status = req.response ? req.response.statusCode : 200;
  return { data, status };
}

function pill(parent, text, hex, size) {
  const s = parent.addStack();
  s.setPadding(3, 9, 3, 9);
  s.cornerRadius = 10;
  s.backgroundColor = new Color(hex, 0.18);
  s.centerAlignContent();
  const t = s.addText(text);
  t.font = Font.semiboldSystemFont(size || 11);
  t.textColor = new Color(hex);
  t.lineLimit = 1;
  return s;
}

// --- Apple-Fitness activity rings -------------------------------------------
// Concentric rings (outer→inner) drawn as a dense arc of dots so ends look
// rounded; a faint full-circle track behind each, plus a glowing end cap.
function drawRings(size, rings) {
  const ctx = new DrawContext();
  ctx.size = new Size(size, size);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const cx = size / 2, cy = size / 2;
  const th = size * 0.13, gap = size * 0.035;
  const steps = 200;
  for (let i = 0; i < rings.length; i++) {
    const ring = rings[i];
    const r = size / 2 - th / 2 - i * (th + gap) - 1;
    const dot = th / 2;
    for (let k = 0; k < steps; k++) {
      const f = k / steps, ang = -Math.PI / 2 + f * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color(ring.color, 0.15));
      ctx.fillEllipse(new Rect(x - dot, y - dot, dot * 2, dot * 2));
    }
    const frac = Math.max(0, Math.min(1, ring.frac));
    const pdots = Math.round(steps * frac);
    for (let k = 0; k <= pdots; k++) {
      const f = k / steps, ang = -Math.PI / 2 + f * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color(ring.color));
      ctx.fillEllipse(new Rect(x - dot, y - dot, dot * 2, dot * 2));
    }
    // glowing end cap
    if (frac > 0.003) {
      const f = pdots / steps, ang = -Math.PI / 2 + f * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color(ring.color, 0.35));
      ctx.fillEllipse(new Rect(x - dot * 1.5, y - dot * 1.5, dot * 3, dot * 3));
      ctx.setFillColor(new Color("#ffffff", 0.9));
      ctx.fillEllipse(new Rect(x - dot * 0.4, y - dot * 0.4, dot * 0.8, dot * 0.8));
    }
  }
  return ctx.getImage();
}

// --- area sparkline ----------------------------------------------------------
function drawSpark(spark, w, h) {
  const vals = (spark || []).map(Number).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
  const range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const colHex = up ? HEX.mint : HEX.rose;
  const pad = 3;
  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const pt = (i) => new Point(pad + (i / (vals.length - 1)) * (w - 2 * pad), h - pad - ((vals[i] - min) / range) * (h - 2 * pad));
  for (const a of [0.05, 0.13]) {
    const fill = new Path();
    fill.move(new Point(pad, h - pad));
    for (let i = 0; i < vals.length; i++) fill.addLine(pt(i));
    fill.addLine(new Point(w - pad, h - pad));
    fill.closeSubpath();
    ctx.setFillColor(new Color(colHex, a));
    ctx.addPath(fill);
    ctx.fillPath();
  }
  const path = new Path();
  path.move(pt(0));
  for (let i = 1; i < vals.length; i++) path.addLine(pt(i));
  ctx.setStrokeColor(new Color(colHex));
  ctx.setLineWidth(2.4);
  ctx.addPath(path);
  ctx.strokePath();
  const last = pt(vals.length - 1);
  ctx.setFillColor(new Color(colHex, 0.3));
  ctx.fillEllipse(new Rect(last.x - 5, last.y - 5, 10, 10));
  ctx.setFillColor(new Color(colHex));
  ctx.fillEllipse(new Rect(last.x - 2.4, last.y - 2.4, 4.8, 4.8));
  return ctx.getImage();
}

function legendItem(parent, hex, name, value) {
  const s = parent.addStack();
  s.layoutVertically();
  const top = s.addStack();
  top.centerAlignContent();
  const d = top.addText("●");
  d.font = Font.boldSystemFont(9);
  d.textColor = new Color(hex);
  top.addSpacer(5);
  const l = top.addText(name.toUpperCase());
  l.font = Font.mediumSystemFont(8.5);
  l.textColor = C.dim;
  s.addSpacer(2);
  const v = s.addText(value);
  v.font = Font.semiboldSystemFont(13);
  v.textColor = C.text;
  v.minimumScaleFactor = 0.6;
  v.lineLimit = 1;
  return s;
}

function header(w, mode) {
  const row = w.addStack();
  row.centerAlignContent();
  const mark = row.addText("◆");
  mark.font = Font.boldSystemFont(11);
  mark.textColor = C.mint;
  row.addSpacer(6);
  const t = row.addText("GIELDAREK");
  t.font = Font.boldSystemFont(12);
  t.textColor = C.text;
  row.addSpacer();
  if (mode) pill(row, mode === "live" ? "● LIVE" : "PAPER", mode === "live" ? HEX.mint : HEX.dim, 9);
}

function errorCard(w, title, msg) {
  header(w, "");
  w.addSpacer(8);
  const e = w.addText(title);
  e.textColor = C.rose;
  e.font = Font.semiboldSystemFont(14);
  w.addSpacer(3);
  const m = w.addText(msg);
  m.textColor = C.dim;
  m.font = Font.systemFont(10);
  m.lineLimit = 4;
}

async function build() {
  const w = new ListWidget();
  const g = new LinearGradient();
  g.colors = [C.ink2, C.ink];
  g.locations = [0, 1];
  g.startPoint = new Point(0, 0);
  g.endPoint = new Point(0.6, 1);
  w.backgroundGradient = g;
  w.setPadding(14, 15, 13, 15);
  if (SHARE_TOKEN) w.url = `${base()}/?share=${encodeURIComponent(SHARE_TOKEN)}`;
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

  const fam = config.widgetFamily || "medium";
  const small = fam === "small";
  const large = fam === "large";

  if (!SHARE_TOKEN) { errorCard(w, "Brak tokenu", "Wpisz w Parameter:  adres|token"); return w; }

  let d;
  try {
    const res = await fetchWidget();
    if (res.status >= 400 || !res.data || res.data.detail || res.data.total === undefined) {
      errorCard(w, `Brak dostępu (${res.status})`, res.status === 401 ? "Zły/brak SHARE_TOKEN — sprawdź token." : `Serwer zwrócił ${res.status}.`);
      return w;
    }
    d = res.data;
  } catch (e) { errorCard(w, "Błąd połączenia", String((e && e.message) || e)); return w; }

  const positions = d.positions || [];
  let sesja = 0, poza = 0;
  for (const p of positions) { if (p.leg === "extended") poza += p.value || 0; else sesja += p.value || 0; }
  const invested = sesja + poza;               // jeden silnik: wszystko "w grze"
  const cash = d.cash || 0;
  const total = d.total || invested + cash || 1;
  const up = isUp(d.day_pnl_pct);
  const pnl = d.trading_pnl_usd;               // "Zysk automatu" (bez wpłat) -- jak w apce
  const pnlStr = (pnl === null || pnl === undefined) ? "—" : (pnl >= 0 ? "+" : "") + fmtUsd(pnl, 0);
  const pnlHex = (pnl === null || pnl === undefined || pnl >= 0) ? HEX.mint : HEX.rose;

  header(w, d.mode);
  w.addSpacer(small ? 8 : 10);

  // HERO: activity rings (left) + big value & day pill (right)
  const hero = w.addStack();
  hero.centerAlignContent();
  const ringSize = small ? 82 : large ? 116 : 98;
  // Jeden silnik: dwa pierścienie -- W grze (pozycje) i Gotówka. Gdyby kiedyś
  // wróciła noga POZA SESJĄ (poza>0), dokładamy bursztynowy pierścień.
  const rings = poza > 0.5
    ? [{ frac: sesja / total, color: HEX.mint }, { frac: poza / total, color: HEX.amber }, { frac: cash / total, color: HEX.blue }]
    : [{ frac: invested / total, color: HEX.mint }, { frac: cash / total, color: HEX.blue }];
  const img = hero.addImage(drawRings(ringSize, rings));
  img.imageSize = new Size(ringSize, ringSize);
  hero.addSpacer(small ? 11 : 15);
  const right = hero.addStack();
  right.layoutVertically();
  const cap = right.addText("WARTOŚĆ KONTA");
  cap.font = Font.mediumSystemFont(8.5);
  cap.textColor = C.faint;
  right.addSpacer(2);
  const val = right.addText(fmtUsd(d.total));
  val.font = Font.boldSystemFont(small ? 22 : 30);
  val.textColor = C.text;
  val.minimumScaleFactor = 0.5;
  val.lineLimit = 1;
  right.addSpacer(7);
  const chg = right.addStack();
  chg.centerAlignContent();
  pill(chg, (up ? "▲ " : "▼ ") + fmtPct(d.day_pnl_pct) + " dziś", up ? HEX.mint : HEX.rose, 11);

  if (small) { w.addSpacer(); return w; }

  // LEGEND: W grze / Gotówka / Zysk automatu (ten sam wskaźnik co w apce).
  w.addSpacer(12);
  const leg = w.addStack();
  leg.centerAlignContent();
  if (poza > 0.5) {
    legendItem(leg, HEX.mint, "Sesja", fmtUsd(sesja, 0));
    leg.addSpacer();
    legendItem(leg, HEX.amber, "Poza", fmtUsd(poza, 0));
  } else {
    legendItem(leg, HEX.mint, "W grze", fmtUsd(invested, 0));
  }
  leg.addSpacer();
  legendItem(leg, HEX.blue, "Gotówka", fmtUsd(cash, 0));
  leg.addSpacer();
  legendItem(leg, pnlHex, "Zysk automatu", pnlStr);

  // SPARK
  w.addSpacer(12);
  const sp = drawSpark(d.spark, 320, large ? 52 : 42);
  if (sp) { const wi = w.addImage(sp); wi.imageSize = new Size(320, large ? 52 : 42); wi.centerAlignImage(); }

  if (!large) { w.addSpacer(); return w; }

  // POZYCJE (large)
  w.addSpacer(12);
  const ph = w.addText("POZYCJE");
  ph.font = Font.mediumSystemFont(8.5);
  ph.textColor = C.faint;
  w.addSpacer(5);
  if (positions.length === 0) {
    const none = w.addText("Brak pozycji — gotówka czeka na wejścia.");
    none.font = Font.systemFont(10.5);
    none.textColor = C.dim;
  } else {
    for (const p of positions.slice(0, 5)) {
      const row = w.addStack();
      row.centerAlignContent();
      row.setPadding(3, 0, 3, 0);
      const dot = row.addText("●");
      dot.font = Font.boldSystemFont(9);
      dot.textColor = p.leg === "extended" ? C.amber : C.mint;
      row.addSpacer(6);
      const sym = row.addText(p.asset);
      sym.font = Font.semiboldSystemFont(12);
      sym.textColor = C.text;
      row.addSpacer();
      const v = row.addText(fmtUsd(p.value, 0));
      v.font = Font.systemFont(11);
      v.textColor = C.dim;
      row.addSpacer(8);
      if (p.pnl_pct === null || p.pnl_pct === undefined) {
        const dash = row.addText("—"); dash.font = Font.semiboldSystemFont(10.5); dash.textColor = C.dim;
      } else {
        pill(row, fmtPct(p.pnl_pct), p.pnl_pct >= 0 ? HEX.mint : HEX.rose, 10.5);
      }
    }
    const extra = positions.length - Math.min(positions.length, 5);
    if (extra > 0) { w.addSpacer(4); const m = w.addText(`+${extra} więcej w apce`); m.font = Font.systemFont(9.5); m.textColor = C.faint; }
  }
  w.addSpacer();
  return w;
}

const widget = await build();
if (config.runsInWidget) Script.setWidget(widget);
else await widget.presentMedium();
Script.complete();
