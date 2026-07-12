// GielDarek — widget na ekran główny iPhone (przez apkę Scriptable)
// =============================================================================
// Żywy podgląd konta: łączny stan, dzienny %, wynik netto, stan obu silników i
// "temperatura" rynku — w kolorach apki. Dane ciągnie z Twojego linku TYLKO DO
// ODCZYTU (GET /api/status?share=...), więc widget nie może nic kliknąć ani
// handlować. iOS odświeża widgety własnym harmonogramem (zwykle co ~5-15 min);
// to nie jest sekundowy stream, ale sam się aktualizuje w tle.
//
// --- INSTALACJA (raz) --------------------------------------------------------
// 1. Zainstaluj darmową apkę "Scriptable" z App Store.
// 2. Otwórz Scriptable -> "+" -> wklej CAŁY ten plik -> nazwij np. "GielDarek".
// 3. Wpisz swój adres i token niżej (BASE_URL + SHARE_TOKEN) LUB zostaw puste i
//    podaj je w parametrze widgetu (patrz krok 5).
// 4. Ekran główny -> przytrzymaj -> "+" -> Scriptable -> wybierz rozmiar
//    (średni pokazuje najwięcej) -> Dodaj widget.
// 5. Przytrzymaj widget -> "Edytuj widget" -> Script: GielDarek. W polu
//    "Parameter" możesz wpisać:  https://46.225.229.113.sslip.io|TWOJ_SHARE_TOKEN
//    (adres i token oddzielone znakiem | ). To nadpisuje wartości z kodu, więc
//    token nie musi siedzieć w skrypcie.
// =============================================================================

// --- Konfiguracja (możesz zostawić puste i podać w Parameter widgetu) --------
let BASE_URL = "https://46.225.229.113.sslip.io";
let SHARE_TOKEN = ""; // wklej swój SHARE_TOKEN z .env (albo podaj w Parameter)

// Parametr widgetu ma priorytet: "baseUrl|token"
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
  border: new Color("#232e3d"),
};

function fmtUsd(v) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return "$" + Number(v).toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + Number(v).toFixed(2) + "%";
}

function tempOf(regime) {
  if (!regime) return { emoji: "🌫️", text: "brak danych" };
  const s = regime.score ?? 0;
  if (regime.regime === "risk_on") return s >= 2 ? { emoji: "🔥", text: "hossa" } : { emoji: "☀️", text: "byczo" };
  if (regime.regime === "risk_off") return { emoji: "🧊", text: "bessa" };
  return s <= -1 ? { emoji: "🌧️", text: "niedźwiedzio" } : { emoji: "⛅", text: "neutralnie" };
}

function engineState(enabled, paused, halted) {
  if (enabled === false) return { label: "wył.", color: C.muted };
  if (halted) return { label: "STOP (limit)", color: C.red };
  if (paused) return { label: "wstrzymany", color: C.crypto };
  return { label: "aktywny", color: C.green };
}

async function fetchStatus() {
  if (!SHARE_TOKEN) throw new Error("Brak SHARE_TOKEN — wpisz go w skrypcie albo w Parameter widgetu.");
  const url = `${BASE_URL.replace(/\/$/, "")}/api/status?share=${encodeURIComponent(SHARE_TOKEN)}`;
  const req = new Request(url);
  req.timeoutInterval = 15;
  return await req.loadJSON();
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

function bigNumbers(w, data) {
  const total = data.account ? data.account.total_value : null;
  const t = w.addText(fmtUsd(total));
  t.textColor = C.text;
  t.font = Font.boldSystemFont(26);
  t.minimumScaleFactor = 0.6;
  t.lineLimit = 1;

  const sub = w.addStack();
  sub.centerAlignContent();
  const day = sub.addText(fmtPct(data.day_pnl_pct) + " dziś");
  day.font = Font.mediumSystemFont(12);
  day.textColor = (data.day_pnl_pct ?? 0) >= 0 ? C.green : C.red;
  sub.addSpacer(8);
  const net = sub.addText("netto " + fmtUsd(data.net_result_usd));
  net.font = Font.systemFont(11);
  net.textColor = C.muted;
  net.minimumScaleFactor = 0.7;
  net.lineLimit = 1;
}

function engineRow(w, dotColor, name, st, tempStr) {
  const row = w.addStack();
  row.centerAlignContent();
  const dot = row.addText("●");
  dot.textColor = dotColor;
  dot.font = Font.boldSystemFont(9);
  row.addSpacer(5);
  const n = row.addText(name);
  n.textColor = C.text;
  n.font = Font.mediumSystemFont(11);
  row.addSpacer();
  const s = row.addText(st.label + (tempStr ? "  " + tempStr : ""));
  s.textColor = st.color;
  s.font = Font.systemFont(11);
  s.lineLimit = 1;
  s.minimumScaleFactor = 0.7;
}

async function buildWidget() {
  const w = new ListWidget();
  const grad = new LinearGradient();
  grad.colors = [C.bg2, C.bg];
  grad.locations = [0, 1];
  w.backgroundGradient = grad;
  w.setPadding(14, 15, 14, 15);
  // Tap opens the live read-only dashboard.
  if (SHARE_TOKEN) w.url = `${BASE_URL.replace(/\/$/, "")}/?share=${encodeURIComponent(SHARE_TOKEN)}`;
  // Ask iOS to refresh in ~5 minutes (it batches; not guaranteed exact).
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);

  const family = config.widgetFamily || "medium";

  let data;
  try {
    data = await fetchStatus();
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

  headerRow(w, data.mode);
  w.addSpacer(8);
  bigNumbers(w, data);

  if (family !== "small") {
    w.addSpacer(10);
    const usTemp = tempOf(data.market_regime);
    engineRow(
      w,
      C.us,
      "Akcje US",
      engineState(true, data.is_paused, data.is_halted),
      `${usTemp.emoji} ${usTemp.text}`,
    );
    w.addSpacer(4);
    const cTemp = tempOf(data.crypto_market_regime);
    engineRow(
      w,
      C.crypto,
      "Krypto",
      engineState(data.crypto_enabled, data.crypto_paused, data.is_halted),
      data.crypto_enabled ? `${cTemp.emoji} ${cTemp.text}` : "",
    );
  }

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
  // Podgląd przy uruchomieniu ręcznym w apce Scriptable.
  await widget.presentMedium();
}
Script.complete();
