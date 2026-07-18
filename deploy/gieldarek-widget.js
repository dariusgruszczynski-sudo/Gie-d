// GielDarek — widget na ekran główny iPhone (przez apkę Scriptable)
// =============================================================================
// Nowoczesny, żywy podgląd portfela: wartość konta, dzienny % (kolorowy pill),
// wykres skuteczności (krzywa wartości konta z gradientem), luźna gotówka,
// wynik netto, pozostały budżet Claude i trzymane pozycje z P&L. Ciągnie JEDEN
// lekki endpoint tylko-do-odczytu (GET /api/widget?share=...) — szybki, nie handluje.
//
// --- INSTALACJA (raz) --------------------------------------------------------
// 1. Zainstaluj darmową apkę "Scriptable" z App Store.
// 2. Scriptable -> "+" -> wklej CAŁY ten plik -> nazwij np. "GielDarek".
// 3. Adres i token: zostaw puste tu niżej i podaj je w polu "Parameter" widgetu
//    w formacie:  https://TWOJ-ADRES|TWOJ_SHARE_TOKEN
// 4. Ekran główny -> przytrzymaj -> "+" -> Scriptable -> rozmiar (ŚREDNI lub
//    DUŻY pokazuje wykres, staty i pozycje) -> Dodaj widget.
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

// Aurora palette (matches the app v4 theme): electric-violet accent, fresh
// emerald/rose for P&L, warm gold for the POZA SESJĄ leg.
const C = {
  bg: new Color("#08070f"),
  bg2: new Color("#14121f"),
  card: new Color("#ffffff", 0.05),
  cardBorder: new Color("#ffffff", 0.07),
  text: new Color("#ecedf6"),
  muted: new Color("#9698b4"),
  faint: new Color("#63647e"),
  accent: new Color("#7c5cff"),
  green: new Color("#2fd6a0"),
  red: new Color("#fb6f84"),
  us: new Color("#7c5cff"),
  crypto: new Color("#f0b429"),
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
function isUp(v) {
  return v === null || v === undefined || v >= 0;
}
function pnlColor(v) {
  return isUp(v) ? C.green : C.red;
}

// --- małe komponenty UI ------------------------------------------------------
function pill(parent, text, fg, bg, size) {
  const s = parent.addStack();
  s.setPadding(3, 8, 3, 8);
  s.cornerRadius = 8;
  s.backgroundColor = bg;
  s.centerAlignContent();
  const t = s.addText(text);
  t.font = Font.semiboldSystemFont(size || 11);
  t.textColor = fg;
  t.lineLimit = 1;
  return s;
}

function card(parent) {
  const s = parent.addStack();
  s.layoutVertically();
  s.setPadding(9, 11, 9, 11);
  s.cornerRadius = 13;
  s.backgroundColor = C.card;
  s.borderColor = C.cardBorder;
  s.borderWidth = 1;
  return s;
}

function statBlock(parent, label, value, valueColor, dotColor) {
  const s = parent.addStack();
  s.layoutVertically();
  const lrow = s.addStack();
  lrow.centerAlignContent();
  if (dotColor) {
    const dot = lrow.addText("●");
    dot.font = Font.boldSystemFont(7);
    dot.textColor = dotColor;
    lrow.addSpacer(4);
  }
  const l = lrow.addText(label.toUpperCase());
  l.font = Font.mediumSystemFont(8);
  l.textColor = C.faint;
  l.lineLimit = 1;
  s.addSpacer(2);
  const v = s.addText(value);
  v.font = Font.semiboldSystemFont(13);
  v.textColor = valueColor || C.text;
  v.lineLimit = 1;
  v.minimumScaleFactor = 0.6;
  return s;
}

// --- pierścień alokacji (jak "activity rings") -------------------------------
// Segmentowany donut pokazujący podział konta: gotówka / SESJA / POZA SESJĄ.
// Scriptable nie ma prymitywu łuku, więc kreślimy pierścień gęstą serią kropek,
// kolorując każdą wg segmentu, w którym leży jej kąt — daje gładki, żywy ring.
function drawRing(segments, size, thickness, centerTop, centerBig) {
  const total = segments.reduce((a, s) => a + Math.max(0, s.value), 0) || 1;
  const ctx = new DrawContext();
  ctx.size = new Size(size, size);
  ctx.opaque = false;
  ctx.respectScreenScale = true;

  const cx = size / 2;
  const cy = size / 2;
  const r = (size - thickness) / 2 - 1;
  const steps = 160;
  const dot = thickness / 2;

  const bounds = [];
  let acc = 0;
  for (const s of segments) {
    const frac = Math.max(0, s.value) / total;
    bounds.push({ from: acc, to: acc + frac, color: s.color });
    acc += frac;
  }
  const track = new Color("#ffffff", 0.06);
  for (let i = 0; i < steps; i++) {
    const f = i / steps;
    const ang = -Math.PI / 2 + f * 2 * Math.PI; // start at 12 o'clock
    const x = cx + r * Math.cos(ang);
    const y = cy + r * Math.sin(ang);
    let col = track;
    for (const b of bounds) {
      if (f >= b.from - 1e-9 && f < b.to - 1e-9) {
        col = b.color;
        break;
      }
    }
    ctx.setFillColor(col);
    ctx.fillEllipse(new Rect(x - dot, y - dot, dot * 2, dot * 2));
  }

  // Środek: mała etykieta + duża liczba (np. % zainwestowany).
  if (centerBig) {
    ctx.setTextAlignedCenter();
    if (centerTop) {
      ctx.setFont(Font.mediumSystemFont(9));
      ctx.setTextColor(C.faint);
      ctx.drawTextInRect(centerTop, new Rect(0, cy - 22, size, 12));
    }
    ctx.setFont(Font.boldSystemFont(21));
    ctx.setTextColor(C.text);
    ctx.drawTextInRect(centerBig, new Rect(0, cy - 12, size, 26));
  }
  return ctx.getImage();
}

const base = () => BASE_URL.replace(/\/$/, "");
async function fetchWidget() {
  const req = new Request(`${base()}/api/widget?share=${encodeURIComponent(SHARE_TOKEN)}`);
  req.timeoutInterval = 20;
  // NB: Scriptable's loadJSON() does NOT throw on HTTP 401/4xx -- it returns the
  // parsed error body (e.g. {"detail":"Wymagane logowanie"}). So we must inspect
  // the status code ourselves, or a bad token silently renders an empty widget.
  const data = await req.loadJSON();
  const status = req.response ? req.response.statusCode : 200;
  return { data, status };
}

// --- wykres powierzchniowy (area sparkline) ---------------------------------
function drawSparkline(spark, w, h) {
  const vals = (spark || []).map(Number).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const min = Math.min.apply(null, vals);
  const max = Math.max.apply(null, vals);
  const range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const col = up ? "#2fd6a0" : "#fb6f84";
  const pad = 4;

  const ctx = new DrawContext();
  ctx.size = new Size(w, h);
  ctx.opaque = false;
  ctx.respectScreenScale = true;

  const pt = (i) =>
    new Point(pad + (i / (vals.length - 1)) * (w - 2 * pad), h - pad - ((vals[i] - min) / range) * (h - 2 * pad));

  // Wypełnienie gradientowe imitujące głębię — dwie nakładane półprzezroczyste
  // warstwy (Scriptable nie ma gradientu w Path, więc robimy to warstwami).
  for (const a of [0.05, 0.11]) {
    const fill = new Path();
    fill.move(new Point(pad, h - pad));
    for (let i = 0; i < vals.length; i++) fill.addLine(pt(i));
    fill.addLine(new Point(w - pad, h - pad));
    fill.closeSubpath();
    ctx.setFillColor(new Color(col, a));
    ctx.addPath(fill);
    ctx.fillPath();
  }

  const path = new Path();
  path.move(pt(0));
  for (let i = 1; i < vals.length; i++) path.addLine(pt(i));
  ctx.setStrokeColor(new Color(col));
  ctx.setLineWidth(2.4);
  ctx.addPath(path);
  ctx.strokePath();

  // Kropka końcowa z poświatą.
  const last = pt(vals.length - 1);
  ctx.setFillColor(new Color(col, 0.28));
  ctx.fillEllipse(new Rect(last.x - 5.5, last.y - 5.5, 11, 11));
  ctx.setFillColor(new Color(col));
  ctx.fillEllipse(new Rect(last.x - 2.6, last.y - 2.6, 5.2, 5.2));
  return ctx.getImage();
}

// --- nagłówek / błędy --------------------------------------------------------
function headerRow(w, mode) {
  const row = w.addStack();
  row.centerAlignContent();
  const dot = row.addText("●");
  dot.textColor = C.accent;
  dot.font = Font.boldSystemFont(9);
  row.addSpacer(5);
  const title = row.addText("GielDarek");
  title.textColor = C.text;
  title.font = Font.boldSystemFont(14);
  row.addSpacer();
  if (mode) {
    const live = mode === "live";
    pill(row, live ? "● LIVE" : "PAPER", live ? C.green : C.muted, new Color(live ? "#2fd6a0" : "#9698b4", 0.14), 9);
  }
}

function errorCard(w, title, msg) {
  headerRow(w, "");
  w.addSpacer(8);
  const e = w.addText(title);
  e.textColor = C.red;
  e.font = Font.semiboldSystemFont(14);
  w.addSpacer(3);
  const m = w.addText(msg);
  m.textColor = C.muted;
  m.font = Font.systemFont(10);
  m.lineLimit = 4;
}

// --- główny build ------------------------------------------------------------
async function buildWidget() {
  const w = new ListWidget();
  const grad = new LinearGradient();
  grad.colors = [C.bg2, C.bg];
  grad.locations = [0, 1];
  grad.startPoint = new Point(0, 0);
  grad.endPoint = new Point(0.4, 1);
  w.backgroundGradient = grad;
  w.setPadding(14, 15, 13, 15);
  if (SHARE_TOKEN) w.url = `${base()}/?share=${encodeURIComponent(SHARE_TOKEN)}`;
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

  const family = config.widgetFamily || "medium";
  const small = family === "small";

  if (!SHARE_TOKEN) {
    errorCard(w, "Brak SHARE_TOKEN", "Wpisz go w polu Parameter widgetu:  adres|token");
    return w;
  }

  let d;
  try {
    const res = await fetchWidget();
    if (res.status >= 400 || !res.data || res.data.detail || res.data.total === undefined) {
      const why =
        res.status === 401 || (res.data && res.data.detail)
          ? "Zły / brak SHARE_TOKEN — sprawdź token w Parameter i na serwerze (.env)."
          : `Serwer zwrócił ${res.status}.`;
      errorCard(w, `Brak dostępu (${res.status})`, why);
      return w;
    }
    d = res.data;
  } catch (e) {
    errorCard(w, "Błąd połączenia", String((e && e.message) || e));
    return w;
  }

  const up = isUp(d.day_pnl_pct);

  // Podział konta na segmenty pierścienia (z pozycji per noga).
  const positions = d.positions || [];
  let sesjaVal = 0;
  let pozaVal = 0;
  for (const p of positions) {
    if (p.leg === "extended") pozaVal += p.value || 0;
    else sesjaVal += p.value || 0;
  }
  const cashVal = d.cash || 0;
  const investedVal = sesjaVal + pozaVal;
  const invPct = d.total ? Math.round((investedVal / d.total) * 100) : 0;
  const cashRingColor = new Color("#8a8ca8", 0.45);
  const ringSegs = [
    { value: sesjaVal, color: C.us },
    { value: pozaVal, color: C.crypto },
    { value: cashVal, color: cashRingColor },
  ];

  headerRow(w, d.mode);
  w.addSpacer(small ? 9 : 11);

  // --- HERO: pierścień alokacji + wartość konta + zmiana dzienna -------------
  const hero = w.addStack();
  hero.centerAlignContent();

  const ringSize = small ? 78 : family === "large" ? 104 : 92;
  const ringImg = drawRing(ringSegs, ringSize, small ? 12 : 15, "ZAINWEST.", invPct + "%");
  const ringView = hero.addImage(ringImg);
  ringView.imageSize = new Size(ringSize, ringSize);

  hero.addSpacer(small ? 11 : 14);

  const heroR = hero.addStack();
  heroR.layoutVertically();
  const capLbl = heroR.addText("WARTOŚĆ KONTA");
  capLbl.font = Font.mediumSystemFont(8.5);
  capLbl.textColor = C.faint;
  heroR.addSpacer(2);
  const total = heroR.addText(fmtUsd(d.total));
  total.textColor = C.text;
  total.font = Font.boldSystemFont(small ? 22 : 28);
  total.minimumScaleFactor = 0.5;
  total.lineLimit = 1;
  heroR.addSpacer(6);
  const chg = heroR.addStack();
  chg.centerAlignContent();
  pill(
    chg,
    (up ? "▲ " : "▼ ") + fmtPct(d.day_pnl_pct),
    up ? C.green : C.red,
    new Color(up ? "#2fd6a0" : "#fb6f84", 0.16),
    11.5
  );
  chg.addSpacer(6);
  const chgCap = chg.addText("dziś");
  chgCap.font = Font.mediumSystemFont(9);
  chgCap.textColor = C.faint;
  if (!small) {
    heroR.addSpacer(6);
    const netRow = heroR.addStack();
    netRow.centerAlignContent();
    const netLbl = netRow.addText("NETTO ");
    netLbl.font = Font.mediumSystemFont(9);
    netLbl.textColor = C.faint;
    const netV = netRow.addText(fmtUsd(d.net_result_usd, 2));
    netV.font = Font.boldSystemFont(13);
    netV.textColor = pnlColor(d.net_result_usd);
  }

  if (small) {
    w.addSpacer();
    return w;
  }

  // --- WYKRES ----------------------------------------------------------------
  w.addSpacer(11);
  const img = drawSparkline(d.spark, 320, family === "large" ? 56 : 44);
  if (img) {
    const wi = w.addImage(img);
    wi.imageSize = new Size(320, family === "large" ? 56 : 44);
    wi.centerAlignImage();
  } else {
    const nn = w.addText("zbieram dane do wykresu…");
    nn.font = Font.systemFont(10);
    nn.textColor = C.muted;
  }

  // --- KARTA STATÓW: gotówka / SESJA / POZA SESJĄ / budżet -------------------
  w.addSpacer(10);
  const stats = card(w);
  const statsRow = stats.addStack();
  statsRow.centerAlignContent();
  statBlock(statsRow, "Gotówka", fmtUsd(cashVal, 0), C.text, new Color("#8a8ca8", 0.7));
  statsRow.addSpacer();
  statBlock(statsRow, "Sesja", fmtUsd(sesjaVal, 0), C.text, C.us);
  statsRow.addSpacer();
  statBlock(statsRow, "Poza", fmtUsd(pozaVal, 0), C.text, C.crypto);
  if (d.claude_budget_remaining_usd !== undefined && d.claude_budget_remaining_usd !== null) {
    statsRow.addSpacer();
    statBlock(statsRow, "Budżet AI", "~" + fmtUsd(d.claude_budget_remaining_usd, 0));
  }

  // --- POZYCJE ---------------------------------------------------------------
  w.addSpacer(10);
  const posHdr = w.addText("POZYCJE");
  posHdr.font = Font.mediumSystemFont(8.5);
  posHdr.textColor = C.faint;
  w.addSpacer(5);

  if (positions.length === 0) {
    const none = w.addText("Brak otwartych pozycji — cała gotówka czeka na wejścia.");
    none.font = Font.systemFont(10.5);
    none.textColor = C.muted;
    none.lineLimit = 2;
  } else {
    const maxRows = family === "large" ? 6 : 3;
    for (const p of positions.slice(0, maxRows)) {
      const row = w.addStack();
      row.centerAlignContent();
      row.setPadding(3, 0, 3, 0);
      const dot = row.addText("●");
      dot.textColor = p.leg === "extended" ? C.crypto : C.us;
      dot.font = Font.boldSystemFont(9);
      row.addSpacer(6);
      const sym = row.addText(p.asset);
      sym.font = Font.semiboldSystemFont(12);
      sym.textColor = C.text;
      row.addSpacer();
      const val = row.addText(fmtUsd(p.value, 0));
      val.font = Font.systemFont(11);
      val.textColor = C.muted;
      row.addSpacer(8);
      if (p.pnl_pct === null || p.pnl_pct === undefined) {
        const dash = row.addText("—");
        dash.font = Font.semiboldSystemFont(10.5);
        dash.textColor = C.muted;
      } else {
        const pu = p.pnl_pct >= 0;
        pill(row, fmtPct(p.pnl_pct), pu ? C.green : C.red, new Color(pu ? "#2fd6a0" : "#fb6f84", 0.14), 10.5);
      }
    }
    const extra = positions.length - Math.min(positions.length, family === "large" ? 6 : 3);
    if (extra > 0) {
      w.addSpacer(4);
      const more = w.addText(`+${extra} więcej w apce`);
      more.font = Font.systemFont(9.5);
      more.textColor = C.faint;
    }
  }

  // --- STOPKA ----------------------------------------------------------------
  w.addSpacer();
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const foot = w.addText(`odświeżono ${hh}:${mm}`);
  foot.textColor = C.faint;
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
