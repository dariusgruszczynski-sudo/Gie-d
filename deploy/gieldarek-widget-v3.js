// GielDarek — widget iPhone v3 (Scriptable). Jeden skrypt, WIELE rozmiarów:
//   • Ekran GŁÓWNY: mały (jedna liczba), średni (liczba + sparkline + ostatni
//     ruch), duży (liczba + wykres + pozycje + skuteczność/edge).
//   • Ekran BLOKADY (iOS 16+): kołowy (accessoryCircular), prostokątny
//     (accessoryRectangular), liniowy (accessoryInline) — zysk dnia / konto na
//     jedno spojrzenie, bez odblokowywania.
//   • MOTYW: zmień THEME poniżej ("auto" / "dark" / "light" / "cyber").
//   Główną liczbę (Zysk automatu / dnia / konto / pozycje) wybierasz W APCE
//   (Sterowanie → Widżet); skrypt czyta ją z serwera (pole `primary`).
//
// UCZCIWIE o granicach iOS (tak jak wcześniej o animacji kafla):
//   • Kafel na ekranie głównym się NIE animuje (iOS odświeża co kilka minut).
//   • Apple Watch: Scriptable NIE tworzy komplikacji tarczy zegarka. Najbliżej
//     „na nadgarstku” jest widżet na ekranie BLOKADY iPhone’a (jest tu niżej).
//   • Live Activity (pasek na Lock Screen tuż po transakcji) NIE jest możliwa z
//     wklejanego skryptu Scriptable — wymaga natywnej apki. Zamiast tego masz
//     powiadomienia push per-transakcja (włączone w apce).
// =============================================================================
// INSTALACJA: Scriptable → „+” → wklej CAŁY plik → nazwij „GielDarek v3”.
//   Ekran główny/blokady → przytrzymaj → „+” → Scriptable → wybierz skrypt i rozmiar.
// =============================================================================

// ——— KONFIG ———
let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
const THEME = "auto"; // "auto" | "dark" | "light" | "cyber"
if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

// ——— MOTYWY ———
const THEMES = {
  dark:  { ink: "#070b16", card: "#0c1322", text: "#eef3fa", dim: "#8593ab", mint: "#24e6a6", rose: "#ff5c7a", brand: "#34dcff" },
  light: { ink: "#f4f7fb", card: "#ffffff", text: "#0d1526", dim: "#5b6478", mint: "#12a074", rose: "#d83a58", brand: "#1478c8" },
  cyber: { ink: "#0a0618", card: "#140a2b", text: "#f2ecff", dim: "#9a8ac0", mint: "#34dcff", rose: "#ff5c9b", brand: "#9b6bff" },
};
function pickTheme() {
  if (THEME === "dark" || THEME === "light" || THEME === "cyber") return THEMES[THEME];
  return Device.isUsingDarkAppearance() ? THEMES.dark : THEMES.light; // auto
}
const T = pickTheme();
const C = {};
for (const k in T) C[k] = new Color(T[k]);

// ——— FORMAT ———
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
  const d = new Date();
  const p = (x) => String(x).padStart(2, "0");
  return p(d.getHours()) + ":" + p(d.getMinutes());
}

// ——— DANE ———
async function fetchData() {
  const url = `${BASE_URL}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`;
  const req = new Request(url);
  req.timeoutInterval = 12;
  return await req.loadJSON();
}

// ——— SPARKLINE (DrawContext) ———
function sparkImage(series, w, h, color) {
  const dc = new DrawContext();
  dc.size = new Size(w, h);
  dc.opaque = false;
  dc.respectScreenScale = true;
  if (!series || series.length < 2) return dc.getImage();
  const lo = Math.min(...series), hi = Math.max(...series);
  const span = hi - lo || 1;
  const x = (i) => (i / (series.length - 1)) * w;
  const y = (v) => h - ((v - lo) / span) * (h - 4) - 2;
  const path = new Path();
  path.move(new Point(x(0), y(series[0])));
  for (let i = 1; i < series.length; i++) path.addLine(new Point(x(i), y(series[i])));
  dc.setStrokeColor(color);
  dc.setLineWidth(2);
  dc.addPath(path);
  dc.strokePath();
  return dc.getImage();
}

// ——— PRIMARY (kolor wg kierunku) ———
function primaryColor(d) {
  const p = d.primary || {};
  if (p.metric === "account" || p.metric === "positions") return C.text;
  return p.up ? C.mint : C.rose;
}

// ——— EKRAN GŁÓWNY: MAŁY ———
function buildSmall(w, d) {
  w.backgroundColor = C.ink;
  w.setPadding(14, 14, 14, 14);
  const p = d.primary || {};
  const lbl = w.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = C.dim;
  w.addSpacer(4);
  const val = w.addText(p.text || "—");
  val.font = Font.boldSystemFont(30); val.textColor = primaryColor(d);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  w.addSpacer(6);
  const sub = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś`);
  sub.font = Font.systemFont(10); sub.textColor = C.dim; sub.minimumScaleFactor = 0.7;
  w.addSpacer();
  footer(w, d);
}

// ——— EKRAN GŁÓWNY: ŚREDNI ———
function buildMedium(w, d) {
  w.backgroundColor = C.ink;
  w.setPadding(14, 16, 14, 16);
  const top = w.addStack(); top.layoutHorizontally();
  const left = top.addStack(); left.layoutVertically();
  const p = d.primary || {};
  const lbl = left.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = C.dim;
  left.addSpacer(2);
  const val = left.addText(p.text || "—");
  val.font = Font.boldSystemFont(28); val.textColor = primaryColor(d);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  top.addSpacer();
  const rimg = top.addImage(sparkImage(d.spark, 120, 46, p.up === false ? C.rose : C.mint));
  rimg.imageSize = new Size(120, 46);
  w.addSpacer(8);
  const lt = d.last_trade;
  const line = lt
    ? `Ostatnio: ${lt.symbol} ${lt.pnl_usd >= 0 ? "✅ +" : "🔻 "}${fmtUsd(Math.abs(lt.pnl_usd), 0)}`
    : `konto ${fmtUsd(d.total)} · gotówka ${fmtUsd(d.cash)}`;
  const t = w.addText(line);
  t.font = Font.systemFont(11); t.textColor = C.dim; t.minimumScaleFactor = 0.7; t.lineLimit = 1;
  w.addSpacer();
  footer(w, d);
}

// ——— EKRAN GŁÓWNY: DUŻY ———
function buildLarge(w, d) {
  w.backgroundColor = C.ink;
  w.setPadding(18, 18, 18, 18);
  const p = d.primary || {};
  const lbl = w.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(10); lbl.textColor = C.dim;
  w.addSpacer(2);
  const val = w.addText(p.text || "—");
  val.font = Font.boldSystemFont(40); val.textColor = primaryColor(d);
  val.minimumScaleFactor = 0.5; val.lineLimit = 1;
  w.addSpacer(4);
  const sub = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś · ${d.market_open ? "rynek otwarty" : "rynek zamknięty"}`);
  sub.font = Font.systemFont(11); sub.textColor = C.dim; sub.minimumScaleFactor = 0.7;
  w.addSpacer(8);
  const img = w.addImage(sparkImage(d.spark, 320, 60, p.up === false ? C.rose : C.mint));
  img.imageSize = new Size(320, 60);
  w.addSpacer(10);
  // Skuteczność + edge
  const e = d.edge || {};
  const wr = d.win_rate === null || d.win_rate === undefined ? "—" : d.win_rate + "%";
  const edgeTxt = e.avg_win_usd !== null && e.avg_loss_usd !== null && e.avg_win_usd !== undefined
    ? `skuteczność ${wr} · ⌀ wygrana +${fmtUsd(e.avg_win_usd, 0)} vs strata ${fmtUsd(e.avg_loss_usd, 0)}${e.payoff ? ` (${e.payoff}×)` : ""}`
    : `skuteczność ${wr} · ${d.closed || 0} zamknięć`;
  const et = w.addText(edgeTxt);
  et.font = Font.systemFont(11); et.textColor = C.dim; et.minimumScaleFactor = 0.7; et.lineLimit = 1;
  w.addSpacer(8);
  // Pozycje (do 4)
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
      const pnlPct = pos.pnl_pct ?? pos.change_pct;
      const pv = row.addText(`${fmtUsd(pos.value, 0)}  ${pnlPct !== null && pnlPct !== undefined ? fmtPct(pnlPct) : ""}`);
      pv.font = Font.systemFont(12);
      pv.textColor = (pnlPct ?? 0) >= 0 ? C.mint : C.rose;
      w.addSpacer(3);
    }
  }
  w.addSpacer();
  footer(w, d);
}

// ——— stopka z czasem aktualizacji ———
function footer(w, d) {
  const f = w.addStack(); f.layoutHorizontally(); f.centerAlignContent();
  const mode = f.addText(d.mode === "live" ? "● LIVE" : "● PAPER");
  mode.font = Font.mediumSystemFont(8); mode.textColor = d.mode === "live" ? C.mint : C.dim;
  f.addSpacer();
  const ts = f.addText(`akt. ${nowHM()}`);
  ts.font = Font.systemFont(8); ts.textColor = C.dim;
}

// ——— EKRAN BLOKADY ———
function buildLockCircular(w, d) {
  const s = w.addStack(); s.layoutVertically(); s.centerAlignContent();
  const p = d.primary || {};
  const a = s.addText(fmtPct(d.day_pnl_pct));
  a.font = Font.boldSystemFont(15); a.centerAlignText();
  s.addSpacer(1);
  const b = s.addText("dziś");
  b.font = Font.systemFont(8); b.centerAlignText();
}
function buildLockRectangular(w, d) {
  const p = d.primary || {};
  const t1 = w.addText(`${p.label || "Zysk"}: ${p.text || "—"}`);
  t1.font = Font.boldSystemFont(13);
  const t2 = w.addText(`konto ${fmtUsd(d.total)} · ${fmtPct(d.day_pnl_pct)} dziś`);
  t2.font = Font.systemFont(11);
  const img = w.addImage(sparkImage(d.spark, 130, 20, C.mint));
  img.imageSize = new Size(130, 20);
}
function buildLockInline(w, d) {
  const p = d.primary || {};
  const t = w.addText(`GielDarek ${p.text || "—"} · ${fmtPct(d.day_pnl_pct)} dziś`);
  t.font = Font.systemFont(12);
}

// ——— ROUTER ———
async function main() {
  let d;
  try { d = await fetchData(); }
  catch (e) {
    const w = new ListWidget(); w.backgroundColor = C.ink;
    const t = w.addText("GielDarek — brak połączenia"); t.textColor = C.rose; t.font = Font.systemFont(12);
    return finish(w);
  }
  const w = new ListWidget();
  const fam = config.widgetFamily;
  if (fam === "accessoryCircular") buildLockCircular(w, d);
  else if (fam === "accessoryRectangular") buildLockRectangular(w, d);
  else if (fam === "accessoryInline") buildLockInline(w, d);
  else if (fam === "small") buildSmall(w, d);
  else if (fam === "large" || fam === "extraLarge") buildLarge(w, d);
  else buildMedium(w, d); // domyślnie/średni
  w.url = BASE_URL; // dotknięcie otwiera panel
  finish(w);
}
function finish(w) {
  if (config.runsInWidget) Script.setWidget(w);
  else w.presentMedium();
  Script.complete();
}
await main();
