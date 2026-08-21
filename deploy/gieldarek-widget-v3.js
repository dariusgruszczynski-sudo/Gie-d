// GielDarek - widget iPhone v3 (Scriptable), motyw Iris Terminal.
// Ciemny, z gradientem, poswiata i wypelnionym wykresem. Wiele rozmiarow:
//   - Ekran glowny: maly / sredni / duzy.
//   - Ekran blokady (iOS 16+): kolowy / prostokatny / liniowy.
//   Glowna liczbe wybierasz W APCE: Steruj -> Widzet co pokazuje.
// MOTYW: zmien THEME ponizej. Domyslnie "iris" (ciemny). Opcje: iris/midnight/light.
// INSTALACJA: Scriptable -> plus -> wklej CALY plik -> nazwij GielDarek v3.
//   Ekran glowny/blokady -> przytrzymaj -> plus -> Scriptable -> wybierz skrypt.

// --- KONFIG ---
let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
const THEME = "iris"; // "iris" | "midnight" | "light"
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

// --- MOTYWY (tlo = gradient) ---
const THEMES = {
  iris:     { bg: ["#0b1024", "#14092b", "#0a1730"], text: "#eef3fa", dim: "#9aa7c4", mint: "#24e6a6", rose: "#ff5c7a", brand: "#34dcff", brand2: "#9b6bff", glow: "#34dcff" },
  midnight: { bg: ["#05070f", "#0a1020", "#05070f"], text: "#eef3fa", dim: "#7f8ba6", mint: "#24e6a6", rose: "#ff5c7a", brand: "#34dcff", brand2: "#2bd0ff", glow: "#24e6a6" },
  light:    { bg: ["#eef3fb", "#ffffff", "#e7eefb"], text: "#0d1526", dim: "#5b6478", mint: "#12a074", rose: "#d83a58", brand: "#1478c8", brand2: "#6b4bd8", glow: "#1478c8" },
};
const T = THEMES[THEME] || THEMES.iris;
const C = {};
for (const k in T) if (k !== "bg") C[k] = new Color(T[k]);

function applyBg(w) {
  const g = new LinearGradient();
  g.colors = T.bg.map((h) => new Color(h));
  g.locations = T.bg.length === 3 ? [0, 0.55, 1] : [0, 1];
  g.startPoint = new Point(0, 0);
  g.endPoint = new Point(1, 1);
  w.backgroundGradient = g;
  w.backgroundColor = new Color(T.bg[0]);
}

// --- FORMAT ---
function fmtUsd(v, dp) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  if (dp === undefined) dp = 0;
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
  return (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%";
}
function nowHM() {
  const d = new Date(), p = (x) => String(x).padStart(2, "0");
  return p(d.getHours()) + ":" + p(d.getMinutes());
}
function primaryColor(d) {
  const p = d.primary || {};
  if (p.metric === "account" || p.metric === "positions") return C.brand;
  return p.up ? C.mint : C.rose;
}
function hexToColor(hex, a) { return new Color(hex, a); }

// --- SPARKLINE z wypelnieniem (area) + linia ---
function sparkImage(series, w, h, colorHex) {
  const dc = new DrawContext();
  dc.size = new Size(w, h);
  dc.opaque = false;
  dc.respectScreenScale = true;
  if (!series || series.length < 2) return dc.getImage();
  const lo = Math.min(...series), hi = Math.max(...series);
  const span = hi - lo || 1;
  const x = (i) => (i / (series.length - 1)) * w;
  const y = (v) => h - ((v - lo) / span) * (h - 6) - 3;
  // Wypelnienie pod krzywa (delikatna poswiata).
  const fill = new Path();
  fill.move(new Point(0, h));
  for (let i = 0; i < series.length; i++) fill.addLine(new Point(x(i), y(series[i])));
  fill.addLine(new Point(w, h));
  fill.closeSubpath();
  dc.setFillColor(hexToColor(colorHex, 0.16));
  dc.addPath(fill);
  dc.fillPath();
  // Linia.
  const line = new Path();
  line.move(new Point(0, y(series[0])));
  for (let i = 1; i < series.length; i++) line.addLine(new Point(x(i), y(series[i])));
  dc.setStrokeColor(new Color(colorHex));
  dc.setLineWidth(2.4);
  dc.addPath(line);
  dc.strokePath();
  // Kropka na koncu.
  const lastX = x(series.length - 1), lastY = y(series[series.length - 1]);
  dc.setFillColor(new Color(colorHex));
  dc.fillEllipse(new Rect(lastX - 3, lastY - 3, 6, 6));
  return dc.getImage();
}

// --- naglowek: wordmark + LIVE ---
function header(w, d) {
  const row = w.addStack(); row.layoutHorizontally(); row.centerAlignContent();
  const mark = row.addText("GIEL");
  mark.font = Font.heavySystemFont(11); mark.textColor = C.text;
  const mark2 = row.addText("DAREK");
  mark2.font = Font.heavySystemFont(11); mark2.textColor = C.brand;
  row.addSpacer();
  const dot = row.addText("●");
  dot.font = Font.systemFont(8); dot.textColor = d.mode === "live" ? C.mint : C.dim;
  const md = row.addText(d.mode === "live" ? " LIVE" : " PAPER");
  md.font = Font.mediumSystemFont(8); md.textColor = C.dim;
}
function footer(w) {
  const f = w.addStack(); f.layoutHorizontally();
  f.addSpacer();
  const ts = f.addText("akt. " + nowHM());
  ts.font = Font.systemFont(8); ts.textColor = C.dim;
}
function bigNumber(w, d, size) {
  const p = d.primary || {};
  const lbl = w.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = C.dim;
  w.addSpacer(3);
  const val = w.addText(p.text || "—");
  val.font = Font.boldSystemFont(size); val.textColor = primaryColor(d);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  val.shadowColor = hexToColor(T.glow, 0.5); val.shadowRadius = 8; val.shadowOffset = new Point(0, 0);
}

// --- EKRAN GLOWNY ---
function buildSmall(w, d) {
  applyBg(w); w.setPadding(14, 15, 13, 15);
  header(w, d); w.addSpacer(6);
  bigNumber(w, d, 30); w.addSpacer(5);
  const sub = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś`);
  sub.font = Font.systemFont(10); sub.textColor = C.dim; sub.minimumScaleFactor = 0.7; sub.lineLimit = 1;
  w.addSpacer(); footer(w);
}
function buildMedium(w, d) {
  applyBg(w); w.setPadding(14, 16, 13, 16);
  header(w, d); w.addSpacer(6);
  const top = w.addStack(); top.layoutHorizontally(); top.centerAlignContent();
  const left = top.addStack(); left.layoutVertically();
  bigNumberInto(left, d, 27);
  top.addSpacer();
  const img = top.addImage(sparkImage(d.spark, 130, 52, (d.primary && d.primary.up === false) ? T.rose : T.mint));
  img.imageSize = new Size(130, 52);
  w.addSpacer(7);
  const lt = d.last_trade;
  const line = lt
    ? `Ostatnio: ${lt.symbol} ${lt.pnl_usd >= 0 ? "✅ +" : "🔻 −"}${fmtUsd(Math.abs(lt.pnl_usd), 0)}${lt.pnl_pct != null ? ` (${fmtPct(lt.pnl_pct)})` : ""}`
    : `konto ${fmtUsd(d.total)} · gotówka ${fmtUsd(d.cash)}`;
  const t = w.addText(line);
  t.font = Font.systemFont(11); t.textColor = C.dim; t.minimumScaleFactor = 0.7; t.lineLimit = 1;
  w.addSpacer(); footer(w);
}
function buildLarge(w, d) {
  applyBg(w); w.setPadding(18, 18, 16, 18);
  header(w, d); w.addSpacer(6);
  bigNumber(w, d, 40); w.addSpacer(4);
  const sub = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś · ${d.market_open ? "rynek otwarty" : "rynek zamknięty"}`);
  sub.font = Font.systemFont(11); sub.textColor = C.dim; sub.minimumScaleFactor = 0.7;
  w.addSpacer(8);
  const img = w.addImage(sparkImage(d.spark, 320, 64, (d.primary && d.primary.up === false) ? T.rose : T.mint));
  img.imageSize = new Size(320, 64);
  w.addSpacer(10);
  const e = d.edge || {};
  const wr = (d.win_rate == null) ? "—" : d.win_rate + "%";
  const edgeTxt = (e.avg_win_usd != null && e.avg_loss_usd != null)
    ? `skuteczność ${wr} · ⌀ wygrana +${fmtUsd(e.avg_win_usd, 0)} vs strata ${fmtUsd(e.avg_loss_usd, 0)}${e.payoff ? ` (${e.payoff}×)` : ""}`
    : `skuteczność ${wr} · ${d.closed || 0} zamknięć`;
  const et = w.addText(edgeTxt);
  et.font = Font.systemFont(11); et.textColor = C.dim; et.minimumScaleFactor = 0.7; et.lineLimit = 1;
  w.addSpacer(8);
  const poss = (d.positions || []).slice(0, 4);
  if (poss.length === 0) {
    const none = w.addText("Brak otwartych pozycji — gotówka czeka.");
    none.font = Font.systemFont(11); none.textColor = C.dim;
  } else {
    for (const pos of poss) {
      const row = w.addStack(); row.layoutHorizontally(); row.centerAlignContent();
      const sym = row.addText(pos.symbol || pos.asset || "?");
      sym.font = Font.mediumSystemFont(12); sym.textColor = C.text;
      row.addSpacer();
      const pp = pos.pnl_pct != null ? pos.pnl_pct : pos.change_pct;
      const pv = row.addText(`${fmtUsd(pos.value, 0)}   ${pp != null ? fmtPct(pp) : ""}`);
      pv.font = Font.systemFont(12); pv.textColor = (pp || 0) >= 0 ? C.mint : C.rose;
      w.addSpacer(3);
    }
  }
  w.addSpacer(); footer(w);
}
function bigNumberInto(stack, d, size) {
  const p = d.primary || {};
  const lbl = stack.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = C.dim;
  stack.addSpacer(2);
  const val = stack.addText(p.text || "—");
  val.font = Font.boldSystemFont(size); val.textColor = primaryColor(d);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  val.shadowColor = hexToColor(T.glow, 0.5); val.shadowRadius = 8; val.shadowOffset = new Point(0, 0);
}

// --- EKRAN BLOKADY ---
function buildLockCircular(w, d) {
  const s = w.addStack(); s.layoutVertically(); s.centerAlignContent();
  const a = s.addText(fmtPct(d.day_pnl_pct));
  a.font = Font.boldSystemFont(15); a.centerAlignText();
  const b = s.addText("dziś"); b.font = Font.systemFont(8); b.centerAlignText();
}
function buildLockRectangular(w, d) {
  const p = d.primary || {};
  const t1 = w.addText(`${p.label || "Zysk"}: ${p.text || "—"}`); t1.font = Font.boldSystemFont(13);
  const t2 = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś`); t2.font = Font.systemFont(11);
  const img = w.addImage(sparkImage(d.spark, 130, 20, T.mint)); img.imageSize = new Size(130, 20);
}
function buildLockInline(w, d) {
  const p = d.primary || {};
  const t = w.addText(`GielDarek ${p.text || "—"} · ${fmtPct(d.day_pnl_pct)} dziś`); t.font = Font.systemFont(12);
}

// --- DANE + ROUTER ---
async function fetchData() {
  const req = new Request(`${BASE_URL}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 12;
  return await req.loadJSON();
}
async function main() {
  const w = new ListWidget();
  let d;
  try { d = await fetchData(); }
  catch (e) {
    applyBg(w);
    const t = w.addText("GielDarek — brak połączenia"); t.textColor = C.rose; t.font = Font.systemFont(12);
    return finish(w);
  }
  const fam = config.widgetFamily;
  if (fam === "accessoryCircular") buildLockCircular(w, d);
  else if (fam === "accessoryRectangular") buildLockRectangular(w, d);
  else if (fam === "accessoryInline") buildLockInline(w, d);
  else if (fam === "small") buildSmall(w, d);
  else if (fam === "large" || fam === "extraLarge") buildLarge(w, d);
  else buildMedium(w, d);
  w.url = BASE_URL;
  finish(w);
}
function finish(w) {
  if (config.runsInWidget) Script.setWidget(w);
  else w.presentMedium();
  Script.complete();
}
await main();
