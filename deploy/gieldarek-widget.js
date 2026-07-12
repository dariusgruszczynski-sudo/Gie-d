// GielDarek — widget na ekran główny iPhone (przez apkę Scriptable)
// =============================================================================
// Żywy podgląd portfela: łączny stan, dzienny %, LUŹNA GOTÓWKA, trzymane
// pozycje (które tickery/monety chodzą, z ich P&L) i mini-wykres skuteczności
// (krzywa wartości konta) — w kolorach apki. Dane ciągnie z Twojego linku
// TYLKO DO ODCZYTU (GET /api/status + /api/portfolio ?share=...), więc widget
// nic nie kliknie ani nie handluje. iOS odświeża widgety własnym harmonogramem
// (zwykle co ~5-15 min); to nie sekundowy stream, ale aktualizuje się w tle.
//
// --- INSTALACJA (raz) --------------------------------------------------------
// 1. Zainstaluj darmową apkę "Scriptable" z App Store.
// 2. Scriptable -> "+" -> wklej CAŁY ten plik -> nazwij np. "GielDarek".
// 3. Wpisz adres i token niżej (BASE_URL + SHARE_TOKEN) LUB zostaw puste i
//    podaj w polu "Parameter" widgetu:  https://TWOJ-ADRES|TWOJ_SHARE_TOKEN
// 4. Ekran główny -> przytrzymaj -> "+" -> Scriptable -> rozmiar (ŚREDNI lub
//    DUŻY pokazuje wykres i pozycje) -> Dodaj widget.
// 5. Przytrzymaj widget -> "Edytuj widget" -> Script: GielDarek; w "Parameter"
//    wpisz  https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN  (token poza kodem).
// =============================================================================

// --- Konfiguracja (możesz zostawić puste i podać w Parameter widgetu) --------
let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = ""; // wklej swój SHARE_TOKEN z .env (albo podaj w Parameter)

if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

// --- Paleta (spójna z motywem apki "institutional terminal") -----------------
const C = {
  bg: new Color("#0a0e15"),
  bg2: new Color("#141b26"),
  text: new Color("#e6ecf3"),
  muted: new Color("#8894a6"),
  accent: new Color("#4c82f0"),
  green: new Color("#2ebd85"),
  red: new Color("#f0616d"),
  us: new Color("#4c82f0"),
  crypto: new Color("#d9a441"),
};

function fmtUsd(v, dp = 2) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return "$" + Number(v).toLocaleString("pl-PL", { minimumFractionDigits: dp, maximumFractionDigits: dp });
}
function fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + Number(v).toFixed(2) + "%";
}
function pnlColor(v) {
  return (v ?? 0) >= 0 ? C.green : C.red;
}

const base = () => BASE_URL.replace(/\/$/, "");
async function fetchJSON(path) {
  const sep = path.includes("?") ? "&" : "?";
  const req = new Request(`${base()}${path}${sep}share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 15;
  return await req.loadJSON();
}

// Pozycje z jednego silnika: co trzymamy, ile warte, jaki P&L.
function extractPositions(pf, leg) {
  const cur = pf && pf.current;
  if (!cur) return [];
  let balances = {};
  let prices = {};
  try { balances = JSON.parse(cur.balances_json || "{}"); } catch (e) {}
  try { prices = JSON.parse(cur.prices_json || "{}"); } catch (e) {}
  const cost = (pf.cost_basis) || {};
  const out = [];
  for (const asset of Object.keys(balances)) {
    const qty = Number(balances[asset]);
    if (!(qty > 0)) continue;
    // Krypto: ceny pod pełnym symbolem ("BTCUSD"), salda pod bazą ("BTC").
    const price = prices[asset] != null ? prices[asset] : (prices[asset + "USD"] != null ? prices[asset + "USD"] : null);
    if (price === null) continue;
    const value = qty * price;
    if (value < 1) continue; // pomiń pył
    const entry = cost[asset] != null ? cost[asset] : null;
    const pnlPct = entry && entry > 0 ? (price - entry) / entry * 100 : null;
    out.push({ asset, leg, value, pnlPct });
  }
  return out;
}

// Mini krzywa wartości konta (skuteczność) jako obrazek.
function drawSparkline(history, w, h) {
  const vals = (history || []).map((s) => Number(s.total_value_usdt)).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const line = up ? C.green : C.red;
  const pad = 3;

  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = false;
  ctx.respectScreenScale = true;

  const pt = (i) => {
    const x = pad + (i / (vals.length - 1)) * (w - 2 * pad);
    const y = h - pad - ((vals[i] - min) / range) * (h - 2 * pad);
    return new Point(x, y);
  };

  // Wypełnienie pod krzywą (delikatne).
  const fill = new Path();
  fill.move(new Point(pad, h - pad));
  for (let i = 0; i < vals.length; i++) fill.addLine(pt(i));
  fill.addLine(new Point(w - pad, h - pad));
  fill.closeSubpath();
  ctx.setFillColor(new Color(up ? "#2ebd85" : "#f0616d", 0.12));
  ctx.addPath(fill);
  ctx.fillPath();

  // Sama krzywa.
  const path = new Path();
  path.move(pt(0));
  for (let i = 1; i < vals.length; i++) path.addLine(pt(i));
  ctx.setStrokeColor(line);
  ctx.setLineWidth(2);
  ctx.addPath(path);
  ctx.strokePath();

  return ctx.getImage();
}

// --- Elementy UI -------------------------------------------------------------
function headerRow(w, mode) {
  const row = w.addStack();
  row.centerAlignContent();
  const dot = row.addText("●");
  dot.textColor = C.accent;
  dot.font = Font.boldSystemFont(9);
  row.addSpacer(5);
  const title = row.addText("GielDarek");
  title.textColor = C.text;
  title.font = Font.boldSystemFont(13);
  row.addSpacer();
  const tag = row.addText(mode === "live" ? "LIVE" : "PAPER");
  tag.textColor = mode === "live" ? C.green : C.muted;
  tag.font = Font.mediumSystemFont(9);
}

function totalRow(w, data) {
  const t = w.addText(fmtUsd(data.account ? data.account.total_value : null));
  t.textColor = C.text;
  t.font = Font.boldSystemFont(24);
  t.minimumScaleFactor = 0.6;
  t.lineLimit = 1;

  const sub = w.addStack();
  sub.centerAlignContent();
  const day = sub.addText(fmtPct(data.day_pnl_pct) + " dziś");
  day.font = Font.mediumSystemFont(11);
  day.textColor = pnlColor(data.day_pnl_pct);
  sub.addSpacer(8);
  const net = sub.addText("netto " + fmtUsd(data.net_result_usd));
  net.font = Font.systemFont(10);
  net.textColor = C.muted;
  net.minimumScaleFactor = 0.7;
  net.lineLimit = 1;
}

function cashRow(w, data) {
  const cash = data.account ? data.account.cash : null;
  const row = w.addStack();
  row.centerAlignContent();
  const label = row.addText("💵 luźna gotówka");
  label.font = Font.systemFont(11);
  label.textColor = C.muted;
  row.addSpacer(6);
  const val = row.addText(fmtUsd(cash));
  val.font = Font.semiboldSystemFont(12);
  val.textColor = C.text;
}

function positionsList(w, positions, maxRows) {
  if (positions.length === 0) {
    const none = w.addText("Brak otwartych pozycji — cała gotówka czeka.");
    none.font = Font.systemFont(10);
    none.textColor = C.muted;
    none.lineLimit = 2;
    return;
  }
  const shown = positions.slice(0, maxRows);
  for (const p of shown) {
    const row = w.addStack();
    row.centerAlignContent();
    const dot = row.addText("●");
    dot.textColor = p.leg === "crypto" ? C.crypto : C.us;
    dot.font = Font.boldSystemFont(8);
    row.addSpacer(4);
    const sym = row.addText(p.asset);
    sym.font = Font.mediumSystemFont(11);
    sym.textColor = C.text;
    row.addSpacer();
    const val = row.addText(fmtUsd(p.value, 0));
    val.font = Font.systemFont(10);
    val.textColor = C.muted;
    row.addSpacer(6);
    const pnl = row.addText(p.pnlPct === null ? "—" : fmtPct(p.pnlPct));
    pnl.font = Font.semiboldSystemFont(10);
    pnl.textColor = p.pnlPct === null ? C.muted : pnlColor(p.pnlPct);
  }
  const extra = positions.length - shown.length;
  if (extra > 0) {
    const more = w.addText(`+${extra} więcej`);
    more.font = Font.systemFont(9);
    more.textColor = C.muted;
  }
}

function chartBlock(w, history, cw) {
  const label = w.addText("Skuteczność — wartość konta");
  label.font = Font.systemFont(9);
  label.textColor = C.muted;
  w.addSpacer(2);
  const img = drawSparkline(history, cw, 42);
  if (img) {
    const wi = w.addImage(img);
    wi.imageSize = new Size(cw, 42);
    wi.centerAlignImage();
  } else {
    const none = w.addText("zbieram dane do wykresu…");
    none.font = Font.systemFont(10);
    none.textColor = C.muted;
  }
}

// --- Budowa widgetu ----------------------------------------------------------
async function buildWidget() {
  const w = new ListWidget();
  const grad = new LinearGradient();
  grad.colors = [C.bg2, C.bg];
  grad.locations = [0, 1];
  w.backgroundGradient = grad;
  w.setPadding(13, 15, 12, 15);
  if (SHARE_TOKEN) w.url = `${base()}/?share=${encodeURIComponent(SHARE_TOKEN)}`;
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

  const family = config.widgetFamily || "medium";

  if (!SHARE_TOKEN) {
    headerRow(w, "");
    w.addSpacer(6);
    const e = w.addText("Brak SHARE_TOKEN");
    e.textColor = C.red;
    e.font = Font.mediumSystemFont(13);
    const h = w.addText("Wpisz go w skrypcie lub w polu Parameter widgetu.");
    h.textColor = C.muted;
    h.font = Font.systemFont(9);
    h.lineLimit = 2;
    return w;
  }

  let status, pfAlpaca, pfCrypto;
  try {
    status = await fetchJSON("/api/status");
    pfAlpaca = await fetchJSON("/api/portfolio?limit=200&venue=alpaca");
    if (status.crypto_enabled) pfCrypto = await fetchJSON("/api/portfolio?limit=200&venue=crypto");
  } catch (e) {
    headerRow(w, "");
    w.addSpacer(6);
    const err = w.addText("Błąd połączenia");
    err.textColor = C.red;
    err.font = Font.mediumSystemFont(13);
    const msg = w.addText(String(e.message || e));
    msg.textColor = C.muted;
    msg.font = Font.systemFont(9);
    msg.lineLimit = 3;
    return w;
  }

  const positions = [
    ...extractPositions(pfAlpaca, "us"),
    ...extractPositions(pfCrypto, "crypto"),
  ].sort((a, b) => b.value - a.value);

  headerRow(w, status.mode);
  w.addSpacer(6);
  totalRow(w, status);
  w.addSpacer(3);
  cashRow(w, status);

  if (family === "small") {
    w.addSpacer();
    return w;
  }

  // Wykres skuteczności (krzywa wartości konta z historii silnika akcji US).
  const chartW = family === "large" ? 300 : 300;
  w.addSpacer(8);
  chartBlock(w, pfAlpaca ? pfAlpaca.history : [], chartW);

  w.addSpacer(8);
  positionsList(w, positions, family === "large" ? 7 : 3);

  w.addSpacer();
  const foot = w.addText("odświeżono " + new Date().toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" }));
  foot.textColor = C.muted;
  foot.font = Font.systemFont(8);
  foot.rightAlignText();

  return w;
}

const widget = await buildWidget();
if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  const fam = (args.widgetParameter && args.widgetParameter.includes("large")) ? "large" : "medium";
  if (fam === "large") await widget.presentLarge();
  else await widget.presentMedium();
}
Script.complete();
