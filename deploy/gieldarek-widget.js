// GielDarek — widget na ekran główny iPhone (przez apkę Scriptable)
// =============================================================================
// Żywy podgląd portfela: łączny stan, dzienny %, LUŹNA GOTÓWKA, trzymane
// pozycje (co chodzi + P&L) i mini-wykres skuteczności (krzywa wartości konta)
// — w kolorach apki. Ciągnie JEDEN lekki endpoint tylko-do-odczytu
// (GET /api/widget?share=...), więc jest szybki i nie handluje.
//
// --- INSTALACJA (raz) --------------------------------------------------------
// 1. Zainstaluj darmową apkę "Scriptable" z App Store.
// 2. Scriptable -> "+" -> wklej CAŁY ten plik -> nazwij np. "GielDarek".
// 3. Wpisz adres i token niżej (BASE_URL + SHARE_TOKEN) LUB zostaw puste i
//    podaj je w polu "Parameter" widgetu:  https://TWOJ-ADRES|TWOJ_SHARE_TOKEN
// 4. Ekran główny -> przytrzymaj -> "+" -> Scriptable -> rozmiar (ŚREDNI lub
//    DUŻY pokazuje wykres i pozycje) -> Dodaj widget.
// 5. Przytrzymaj widget -> "Edytuj widget" -> Script: GielDarek; w "Parameter"
//    wpisz  https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN
//
// WARUNEK: na serwerze musi być ustawiony SHARE_TOKEN w .env (Centrum
// sterowania -> "Link tylko do odczytu"). Bez tego widget nie ma z czego czytać.
// =============================================================================

let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = ""; // wklej swój SHARE_TOKEN z .env (albo podaj w Parameter)

if (args.widgetParameter) {
  const parts = String(args.widgetParameter).split("|");
  if (parts[0]) BASE_URL = parts[0].trim();
  if (parts[1]) SHARE_TOKEN = parts[1].trim();
}

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

// Ręczne formatowanie (bez Intl/toLocaleString — bywa zawodne w Scriptable).
function fmtUsd(v, dp) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  if (dp === undefined) dp = 2;
  const neg = v < 0;
  let n = Math.abs(Number(v)).toFixed(dp);
  const dot = n.indexOf(".");
  let intPart = dot === -1 ? n : n.slice(0, dot);
  const frac = dot === -1 ? "" : n.slice(dot);
  intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (neg ? "-$" : "$") + intPart + frac;
}
function fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + Number(v).toFixed(2) + "%";
}
function pnlColor(v) {
  return (v === null || v === undefined || v >= 0) ? C.green : C.red;
}

const base = () => BASE_URL.replace(/\/$/, "");
async function fetchWidget() {
  const req = new Request(`${base()}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 20;
  return await req.loadJSON();
}

function drawSparkline(spark, w, h) {
  const vals = (spark || []).map(Number).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const min = Math.min.apply(null, vals);
  const max = Math.max.apply(null, vals);
  const range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const pad = 3;

  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = false;
  ctx.respectScreenScale = true;

  const pt = (i) =>
    new Point(pad + (i / (vals.length - 1)) * (w - 2 * pad), h - pad - ((vals[i] - min) / range) * (h - 2 * pad));

  const fill = new Path();
  fill.move(new Point(pad, h - pad));
  for (let i = 0; i < vals.length; i++) fill.addLine(pt(i));
  fill.addLine(new Point(w - pad, h - pad));
  fill.closeSubpath();
  ctx.setFillColor(new Color(up ? "#2ebd85" : "#f0616d", 0.12));
  ctx.addPath(fill);
  ctx.fillPath();

  const path = new Path();
  path.move(pt(0));
  for (let i = 1; i < vals.length; i++) path.addLine(pt(i));
  ctx.setStrokeColor(up ? C.green : C.red);
  ctx.setLineWidth(2);
  ctx.addPath(path);
  ctx.strokePath();
  return ctx.getImage();
}

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

function errorCard(w, title, msg) {
  headerRow(w, "");
  w.addSpacer(6);
  const e = w.addText(title);
  e.textColor = C.red;
  e.font = Font.mediumSystemFont(13);
  const m = w.addText(msg);
  m.textColor = C.muted;
  m.font = Font.systemFont(9);
  m.lineLimit = 3;
}

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
    errorCard(w, "Brak SHARE_TOKEN", "Wpisz go w skrypcie lub w polu Parameter widgetu (adres|token).");
    return w;
  }

  let d;
  try {
    d = await fetchWidget();
  } catch (e) {
    errorCard(w, "Błąd połączenia", String((e && e.message) || e));
    return w;
  }

  headerRow(w, d.mode);
  w.addSpacer(6);

  const total = w.addText(fmtUsd(d.total));
  total.textColor = C.text;
  total.font = Font.boldSystemFont(24);
  total.minimumScaleFactor = 0.6;
  total.lineLimit = 1;

  const sub = w.addStack();
  sub.centerAlignContent();
  const day = sub.addText(fmtPct(d.day_pnl_pct) + " dziś");
  day.font = Font.mediumSystemFont(11);
  day.textColor = pnlColor(d.day_pnl_pct);
  sub.addSpacer(8);
  const net = sub.addText("netto " + fmtUsd(d.net_result_usd));
  net.font = Font.systemFont(10);
  net.textColor = C.muted;
  net.minimumScaleFactor = 0.7;
  net.lineLimit = 1;

  w.addSpacer(3);
  const cashRow = w.addStack();
  cashRow.centerAlignContent();
  const cl = cashRow.addText("💵 luźna gotówka");
  cl.font = Font.systemFont(11);
  cl.textColor = C.muted;
  cashRow.addSpacer(6);
  const cv = cashRow.addText(fmtUsd(d.cash));
  cv.font = Font.semiboldSystemFont(12);
  cv.textColor = C.text;

  if (family === "small") {
    w.addSpacer();
    return w;
  }

  w.addSpacer(8);
  const lbl = w.addText("Skuteczność — wartość konta");
  lbl.font = Font.systemFont(9);
  lbl.textColor = C.muted;
  w.addSpacer(2);
  const img = drawSparkline(d.spark, 300, 42);
  if (img) {
    const wi = w.addImage(img);
    wi.imageSize = new Size(300, 42);
    wi.centerAlignImage();
  } else {
    const nn = w.addText("zbieram dane do wykresu…");
    nn.font = Font.systemFont(10);
    nn.textColor = C.muted;
  }

  w.addSpacer(8);
  const positions = d.positions || [];
  if (positions.length === 0) {
    const none = w.addText("Brak otwartych pozycji — cała gotówka czeka.");
    none.font = Font.systemFont(10);
    none.textColor = C.muted;
    none.lineLimit = 2;
  } else {
    const maxRows = family === "large" ? 7 : 3;
    for (const p of positions.slice(0, maxRows)) {
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
      const pnl = row.addText(p.pnl_pct === null ? "—" : fmtPct(p.pnl_pct));
      pnl.font = Font.semiboldSystemFont(10);
      pnl.textColor = p.pnl_pct === null ? C.muted : pnlColor(p.pnl_pct);
    }
    const extra = positions.length - Math.min(positions.length, family === "large" ? 7 : 3);
    if (extra > 0) {
      const more = w.addText(`+${extra} więcej`);
      more.font = Font.systemFont(9);
      more.textColor = C.muted;
    }
  }

  w.addSpacer();
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const foot = w.addText(`odświeżono ${hh}:${mm}`);
  foot.textColor = C.muted;
  foot.font = Font.systemFont(8);
  foot.rightAlignText();
  return w;
}

const widget = await buildWidget();
if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  await widget.presentMedium();
}
Script.complete();
