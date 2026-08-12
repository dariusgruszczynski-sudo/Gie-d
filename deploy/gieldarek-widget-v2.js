// GielDarek — widget iPhone v2 (Scriptable), styl "Iris Terminal": PROFIT-FIRST.
// Wielki "Zysk automatu" (bez wpłat), pasek skuteczności (udane/stratne), wykres
// i pozycje z zyskiem/stratą + status rynku (otwarty/zamknięty). Ciągnie tylko
// GET /api/widget?share=... (read-only). Widżety iOS nie animują się na żywo —
// system je odświeża co kilka minut; stawiamy na czytelny, bogaty wygląd.
// =============================================================================
// INSTALACJA: Scriptable -> "+" -> wklej CAŁY plik -> nazwij "GielDarek v2".
// Ekran główny -> przytrzymaj -> "+" -> Scriptable -> wybierz skrypt -> rozmiar.
// Parameter:  https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN
// (albo wpisz token w SHARE_TOKEN niżej). MAŁY = zysk+skuteczność,
//  ŚREDNI = +wykres, DUŻY = +pozycje.
// =============================================================================

let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "";
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

// Paleta "Iris Terminal" (jak w apce): cyan/fiolet chrom, mięta=zysk, róż=strata.
const HEX = {
  ink: "#05070f", ink2: "#0a0e1c", text: "#eef3fa", dim: "#8593ab", faint: "#55627a",
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
  s.cornerRadius = 9;
  s.backgroundColor = new Color(hex, 0.18);
  s.centerAlignContent();
  const t = s.addText(text);
  t.font = Font.semiboldSystemFont(size || 11);
  t.textColor = new Color(hex);
  t.lineLimit = 1;
  return s;
}

// --- pasek skuteczności: zielone (udane) vs czerwone (stratne) ---------------
function drawWinBar(w, h, winFrac) {
  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const r = h / 2;
  const track = new Path(); track.addRoundedRect(new Rect(0, 0, w, h), r, r);
  ctx.setFillColor(new Color("#ffffff", 0.07)); ctx.addPath(track); ctx.fillPath();
  if (winFrac === null || winFrac === undefined) return ctx.getImage();
  // czerwone tło (cała szerokość) + zielona część od lewej
  ctx.setFillColor(new Color(HEX.rose, 0.85));
  const rp = new Path(); rp.addRoundedRect(new Rect(0, 0, w, h), r, r); ctx.addPath(rp); ctx.fillPath();
  const gw = Math.max(r * 2, Math.min(w, w * winFrac));
  ctx.setFillColor(new Color(HEX.mint));
  const gp = new Path(); gp.addRoundedRect(new Rect(0, 0, gw, h), r, r); ctx.addPath(gp); ctx.fillPath();
  return ctx.getImage();
}

// --- wykres (area sparkline) -------------------------------------------------
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
  for (const a of [0.06, 0.14]) {
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

function label(parent, text) {
  const l = parent.addText(text);
  l.font = Font.mediumSystemFont(8.5);
  l.textColor = C.faint;
  return l;
}

async function build() {
  const w = new ListWidget();
  const g = new LinearGradient();
  g.colors = [new Color("#0c1226"), C.ink];
  g.locations = [0, 1];
  g.startPoint = new Point(0, 0);
  g.endPoint = new Point(0.7, 1);
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

  const pnl = d.trading_pnl_usd;
  const pnlUp = (pnl === null || pnl === undefined || pnl >= 0);
  const pnlHex = pnlUp ? HEX.mint : HEX.rose;
  const dayUp = (d.day_pnl_pct === null || d.day_pnl_pct === undefined || d.day_pnl_pct >= 0);
  const wr = d.win_rate;                       // 0..100 lub null
  const positions = d.positions || [];

  header(w, d.mode, d.market_open);
  w.addSpacer(small ? 9 : 11);

  // HERO — ZYSK AUTOMATU (to, na czym najbardziej Ci zależy)
  label(w, "ZYSK AUTOMATU · BEZ TWOICH WPŁAT");
  w.addSpacer(2);
  const hero = w.addText(fmtSigned(pnl, 2));
  hero.font = Font.boldSystemFont(small ? 26 : 34);
  hero.textColor = new Color(pnlHex);
  hero.minimumScaleFactor = 0.5;
  hero.lineLimit = 1;
  w.addSpacer(7);

  // Konto + dzień
  const sub = w.addStack();
  sub.centerAlignContent();
  const acc = sub.addText("Konto " + fmtUsd(d.total, 0));
  acc.font = Font.mediumSystemFont(11);
  acc.textColor = C.dim;
  sub.addSpacer(8);
  pill(sub, (dayUp ? "▲ " : "▼ ") + fmtPct(d.day_pnl_pct) + " dziś", dayUp ? HEX.mint : HEX.rose, 10.5);

  // SKUTECZNOŚĆ — pasek udane/stratne
  w.addSpacer(small ? 10 : 13);
  const skRow = w.addStack();
  skRow.centerAlignContent();
  label(skRow, "SKUTECZNOŚĆ");
  skRow.addSpacer();
  const skv = skRow.addText(wr === null || wr === undefined ? "—" : wr + "%");
  skv.font = Font.boldSystemFont(13);
  skv.textColor = new Color(wr === null || wr === undefined ? HEX.dim : wr >= 50 ? HEX.mint : wr >= 35 ? HEX.gold : HEX.rose);
  w.addSpacer(5);
  const barW = small ? 128 : 320;
  const bar = drawWinBar(barW, 9, wr === null || wr === undefined ? null : wr / 100);
  const bi = w.addImage(bar); bi.imageSize = new Size(barW, 9);
  if (d.closed) {
    w.addSpacer(4);
    const leg = w.addText(`${d.wins} udane · ${d.losses} stratne`);
    leg.font = Font.systemFont(9);
    leg.textColor = C.faint;
  }

  if (small) { w.addSpacer(); return w; }

  // WYKRES (średni/duży)
  w.addSpacer(12);
  const sp = drawSpark(d.spark, 320, large ? 50 : 40);
  if (sp) { const wi = w.addImage(sp); wi.imageSize = new Size(320, large ? 50 : 40); wi.centerAlignImage(); }

  if (!large) { w.addSpacer(); return w; }

  // POZYCJE (duży)
  w.addSpacer(12);
  label(w, "POZYCJE");
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
      dot.textColor = p.leg === "extended" ? C.brand2 : C.brand;
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
