// GielDarek — widget iPhone v2 (Scriptable) "Iris Terminal": PROFIT-FIRST, sexy.
// GOTOWY DO WKLEJENIA — adres i token są już wpisane niżej.
// Świecące tło (radialne poświaty), pierścień skuteczności z liczbą w środku,
// wielki "Zysk automatu" ze świecącym cieniem, gradientowy wykres, pozycje jako
// kolorowe chipy. Ciągnie tylko GET /api/widget?share=... (read-only).
// =============================================================================
// INSTALACJA: Scriptable -> "+" -> wklej CAŁY plik -> nazwij "GielDarek v2".
// Ekran główny -> przytrzymaj -> "+" -> Scriptable -> wybierz skrypt -> rozmiar.
// Parameter zostaw PUSTE. MAŁY = pierścień+zysk, ŚREDNI = +wykres, DUŻY = +pozycje.
// =============================================================================

let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

// Paleta "Iris Terminal": cyan/fiolet chrom, mięta=zysk, róż=strata.
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

// --- świecące tło: baza + dwie radialne poświaty (cyan / fiolet) -------------
function radialGlow(ctx, cx, cy, R, hex, maxA) {
  const rings = 22;
  for (let i = rings; i >= 1; i--) {
    const rr = R * (i / rings);
    const t = 1 - i / rings;
    const a = maxA * t * t;
    ctx.setFillColor(new Color(hex, a));
    ctx.fillEllipse(new Rect(cx - rr, cy - rr, rr * 2, rr * 2));
  }
}
function drawBackground(w, h) {
  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = true;
  ctx.respectScreenScale = true;
  ctx.setFillColor(C.ink);
  ctx.fillRect(new Rect(0, 0, w, h));
  const R = Math.max(w, h);
  radialGlow(ctx, w * 0.14, h * 0.06, R * 0.62, HEX.brand, 0.26);
  radialGlow(ctx, w * 0.92, h * 1.02, R * 0.72, HEX.brand2, 0.24);
  return ctx.getImage();
}

// --- pierścień skuteczności z liczbą w środku (świecący end-cap) -------------
function drawGauge(size, frac, hex, centerText, sub) {
  const ctx = new DrawContext();
  ctx.size = new Size(size, size);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const cx = size / 2, cy = size / 2;
  const th = size * 0.12, r = size / 2 - th / 2 - 1, dot = th / 2, steps = 180;
  for (let k = 0; k < steps; k++) {
    const ang = -Math.PI / 2 + (k / steps) * 2 * Math.PI;
    const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
    ctx.setFillColor(new Color(hex, 0.14));
    ctx.fillEllipse(new Rect(x - dot, y - dot, dot * 2, dot * 2));
  }
  if (frac !== null && frac !== undefined) {
    const pdots = Math.round(steps * clamp01(frac));
    for (let k = 0; k <= pdots; k++) {
      const ang = -Math.PI / 2 + (k / steps) * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color(hex));
      ctx.fillEllipse(new Rect(x - dot, y - dot, dot * 2, dot * 2));
    }
    if (frac > 0.003) {
      const ang = -Math.PI / 2 + (pdots / steps) * 2 * Math.PI;
      const x = cx + r * Math.cos(ang), y = cy + r * Math.sin(ang);
      ctx.setFillColor(new Color(hex, 0.35));
      ctx.fillEllipse(new Rect(x - dot * 1.7, y - dot * 1.7, dot * 3.4, dot * 3.4));
      ctx.setFillColor(new Color("#ffffff", 0.92));
      ctx.fillEllipse(new Rect(x - dot * 0.42, y - dot * 0.42, dot * 0.84, dot * 0.84));
    }
  }
  // liczba w środku + podpis
  ctx.setTextAlignedCenter();
  ctx.setFont(Font.boldSystemFont(size * 0.28));
  ctx.setTextColor(new Color(hex));
  ctx.drawTextInRect(centerText, new Rect(0, cy - size * 0.215, size, size * 0.3));
  ctx.setFont(Font.mediumSystemFont(size * 0.088));
  ctx.setTextColor(C.faint);
  ctx.drawTextInRect(sub, new Rect(0, cy + size * 0.11, size, size * 0.16));
  return ctx.getImage();
}

// --- wykres (gradientowy area sparkline) -------------------------------------
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
  for (const a of [0.06, 0.13, 0.2]) {
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
  ctx.setLineWidth(2.6);
  ctx.addPath(path);
  ctx.strokePath();
  const last = pt(vals.length - 1);
  ctx.setFillColor(new Color(colHex, 0.3));
  ctx.fillEllipse(new Rect(last.x - 5.5, last.y - 5.5, 11, 11));
  ctx.setFillColor(new Color(colHex));
  ctx.fillEllipse(new Rect(last.x - 2.6, last.y - 2.6, 5.2, 5.2));
  return ctx.getImage();
}

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

function header(w, mode, marketOpen) {
  const row = w.addStack();
  row.centerAlignContent();
  const mark = row.addText("◈");
  mark.font = Font.boldSystemFont(12);
  mark.textColor = C.brand;
  row.addSpacer(6);
  const t = row.addText("GIELDAREK");
  t.font = Font.boldSystemFont(12);
  t.textColor = C.text;
  row.addSpacer();
  if (marketOpen !== undefined && marketOpen !== null) {
    pill(row, marketOpen ? "● rynek" : "○ zamkn.", marketOpen ? HEX.mint : HEX.faint, 9);
    row.addSpacer(5);
  }
  if (mode) pill(row, mode === "live" ? "LIVE" : "PAPER", mode === "live" ? HEX.brand : HEX.dim, 9);
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

// karta (półprzezroczysty rounded stack) — dodaje głębi zamiast płaskiej listy
function card(parent) {
  const s = parent.addStack();
  s.layoutVertically();
  s.setPadding(10, 12, 10, 12);
  s.cornerRadius = 14;
  s.backgroundColor = new Color("#ffffff", 0.05);
  return s;
}

async function build() {
  const w = new ListWidget();
  const fam = config.widgetFamily || "medium";
  const small = fam === "small";
  const large = fam === "large";
  const bgW = small ? 170 : large ? 360 : 360, bgH = small ? 170 : large ? 360 : 170;
  w.backgroundImage = drawBackground(bgW, bgH);
  w.setPadding(14, 15, 13, 15);
  if (SHARE_TOKEN) w.url = `${base()}/?share=${encodeURIComponent(SHARE_TOKEN)}`;
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

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

  const pnl = d.trading_pnl_usd;
  const pnlUp = (pnl === null || pnl === undefined || pnl >= 0);
  const pnlHex = pnlUp ? HEX.mint : HEX.rose;
  const dayUp = (d.day_pnl_pct === null || d.day_pnl_pct === undefined || d.day_pnl_pct >= 0);
  const wr = d.win_rate;
  const wrHex = (wr === null || wr === undefined) ? HEX.dim : wr >= 50 ? HEX.mint : wr >= 35 ? HEX.gold : HEX.rose;
  const positions = d.positions || [];

  header(w, d.mode, d.market_open);
  w.addSpacer(small ? 8 : 11);

  // HERO — pierścień skuteczności (lewo) + Zysk automatu (prawo)
  const hero = w.addStack();
  hero.centerAlignContent();
  const gSize = small ? 78 : large ? 108 : 96;
  const gimg = hero.addImage(drawGauge(gSize, (wr === null || wr === undefined) ? null : wr / 100, wrHex, (wr === null || wr === undefined) ? "—" : wr + "%", "SKUTECZNOŚĆ"));
  gimg.imageSize = new Size(gSize, gSize);
  hero.addSpacer(small ? 10 : 15);

  const right = hero.addStack();
  right.layoutVertically();
  const cap = right.addText("ZYSK AUTOMATU");
  cap.font = Font.mediumSystemFont(8.5);
  cap.textColor = C.faint;
  right.addSpacer(3);
  const val = right.addText(fmtSigned(pnl, small ? 0 : 2));
  val.font = Font.boldSystemFont(small ? 24 : 32);
  val.textColor = new Color(pnlHex);
  val.minimumScaleFactor = 0.5;
  val.lineLimit = 1;
  val.shadowColor = new Color(pnlHex, 0.55);   // świecący cień
  val.shadowRadius = 9;
  val.shadowOffset = new Point(0, 0);
  right.addSpacer(8);
  const sub = right.addStack();
  sub.centerAlignContent();
  pill(sub, (dayUp ? "▲ " : "▼ ") + fmtPct(d.day_pnl_pct) + " dziś", dayUp ? HEX.mint : HEX.rose, 10.5);
  if (!small) {
    right.addSpacer(6);
    const acc = right.addText("Konto " + fmtUsd(d.total, 0));
    acc.font = Font.mediumSystemFont(10.5);
    acc.textColor = C.dim;
  }

  if (small) { w.addSpacer(); return w; }

  // WYKRES w karcie
  w.addSpacer(11);
  const sc = card(w);
  const shead = sc.addStack();
  shead.centerAlignContent();
  label(shead, "ZYSK W CZASIE");
  shead.addSpacer();
  if (d.closed) {
    const legt = shead.addText(`${d.wins} udane · ${d.losses} stratne`);
    legt.font = Font.systemFont(8.5);
    legt.textColor = C.faint;
  }
  sc.addSpacer(6);
  const sp = drawSpark(d.spark, 300, large ? 52 : 44);
  if (sp) { const wi = sc.addImage(sp); wi.imageSize = new Size(300, large ? 52 : 44); }
  else { const ns = sc.addText("Zbieram krzywą…"); ns.font = Font.systemFont(10); ns.textColor = C.dim; }

  if (!large) { w.addSpacer(); return w; }

  // POZYCJE jako chipy
  w.addSpacer(11);
  label(w, "POZYCJE");
  w.addSpacer(6);
  if (positions.length === 0) {
    const none = w.addText("Brak pozycji — gotówka czeka na wejścia.");
    none.font = Font.systemFont(10.5);
    none.textColor = C.dim;
  } else {
    for (const p of positions.slice(0, 4)) {
      const row = card(w);
      row.setPadding(7, 11, 7, 11);
      const line = row.addStack();
      line.centerAlignContent();
      const dot = line.addText("●");
      dot.font = Font.boldSystemFont(9);
      dot.textColor = p.leg === "extended" ? C.brand2 : C.brand;
      line.addSpacer(7);
      const sym = line.addText(p.asset);
      sym.font = Font.semiboldSystemFont(13);
      sym.textColor = C.text;
      line.addSpacer();
      const v = line.addText(fmtUsd(p.value, 0));
      v.font = Font.systemFont(11);
      v.textColor = C.dim;
      line.addSpacer(9);
      if (p.pnl_pct === null || p.pnl_pct === undefined) {
        const dash = line.addText("—"); dash.font = Font.semiboldSystemFont(10.5); dash.textColor = C.dim;
      } else {
        pill(line, fmtPct(p.pnl_pct), p.pnl_pct >= 0 ? HEX.mint : HEX.rose, 10.5);
      }
      w.addSpacer(6);
    }
    const extra = positions.length - Math.min(positions.length, 4);
    if (extra > 0) { const m = w.addText(`+${extra} więcej w apce`); m.font = Font.systemFont(9.5); m.textColor = C.faint; }
  }
  w.addSpacer();
  return w;
}

const widget = await build();
if (config.runsInWidget) Script.setWidget(widget);
else await widget.presentMedium();
Script.complete();
