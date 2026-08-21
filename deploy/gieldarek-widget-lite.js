// GielDarek - widget iPhone (Scriptable), wersja LITE - kuloodporna na kopiowanie.
// Ciemny gradient + poswiata + wykres. Adres i token juz wpisane.
// Glowna liczbe wybierasz w apce: Steruj -> Widzet co pokazuje.
// Instalacja: Scriptable -> plus -> wklej calosc -> nazwij GielDarek -> plus na ekranie glownym.

var BASE_URL = "https://46.225.229.113.sslip.io";
var SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
var THEME = "iris"; // iris | midnight | light

var PAL = {
  iris:     { a: "#0b1024", b: "#14092b", c: "#0a1730", tx: "#eef3fa", dim: "#9aa7c4", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  midnight: { a: "#05070f", b: "#0a1020", c: "#05070f", tx: "#eef3fa", dim: "#7f8ba6", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  light:    { a: "#eef3fb", b: "#ffffff", c: "#e7eefb", tx: "#0d1526", dim: "#5b6478", up: "#12a074", dn: "#d83a58", br: "#1478c8" }
};
var P = PAL[THEME] || PAL.iris;

function usd(v) {
  if (v == null || isNaN(v)) return "-";
  var neg = v < 0;
  var n = Math.round(Math.abs(Number(v))).toString();
  n = n.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (neg ? "-$" : "$") + n;
}
function pctv(v) {
  if (v == null || isNaN(v)) return "-";
  return (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%";
}
function hm() {
  var d = new Date();
  function z(x) { return (x < 10 ? "0" : "") + x; }
  return z(d.getHours()) + ":" + z(d.getMinutes());
}
function bg(w) {
  var g = new LinearGradient();
  g.colors = [new Color(P.a), new Color(P.b), new Color(P.c)];
  g.locations = [0, 0.55, 1];
  g.startPoint = new Point(0, 0);
  g.endPoint = new Point(1, 1);
  w.backgroundGradient = g;
  w.backgroundColor = new Color(P.a);
}
function spark(series, w, h, hex) {
  var dc = new DrawContext();
  dc.size = new Size(w, h);
  dc.opaque = false;
  dc.respectScreenScale = true;
  if (!series || series.length < 2) return dc.getImage();
  var lo = Math.min.apply(null, series);
  var hi = Math.max.apply(null, series);
  var span = (hi - lo) || 1;
  var i;
  function xx(i) { return (i / (series.length - 1)) * w; }
  function yy(v) { return h - ((v - lo) / span) * (h - 6) - 3; }
  var fill = new Path();
  fill.move(new Point(0, h));
  for (i = 0; i < series.length; i++) fill.addLine(new Point(xx(i), yy(series[i])));
  fill.addLine(new Point(w, h));
  fill.closeSubpath();
  dc.setFillColor(new Color(hex, 0.16));
  dc.addPath(fill);
  dc.fillPath();
  var ln = new Path();
  ln.move(new Point(0, yy(series[0])));
  for (i = 1; i < series.length; i++) ln.addLine(new Point(xx(i), yy(series[i])));
  dc.setStrokeColor(new Color(hex));
  dc.setLineWidth(2.4);
  dc.addPath(ln);
  dc.strokePath();
  return dc.getImage();
}

async function run() {
  var w = new ListWidget();
  bg(w);
  var d;
  try {
    var req = new Request(BASE_URL + "/api/widget?share=" + encodeURIComponent(SHARE_TOKEN));
    req.timeoutInterval = 12;
    d = await req.loadJSON();
  } catch (e) {
    var er = w.addText("GielDarek - brak polaczenia");
    er.textColor = new Color(P.dn);
    er.font = Font.systemFont(12);
    return done(w);
  }
  var prim = d.primary || {};
  w.setPadding(14, 16, 13, 16);

  // Naglowek
  var head = w.addStack();
  head.centerAlignContent();
  var m1 = head.addText("GIEL"); m1.font = Font.heavySystemFont(11); m1.textColor = new Color(P.tx);
  var m2 = head.addText("DAREK"); m2.font = Font.heavySystemFont(11); m2.textColor = new Color(P.br);
  head.addSpacer();
  var live = head.addText(d.mode === "live" ? "LIVE" : "PAPER");
  live.font = Font.mediumSystemFont(8);
  live.textColor = d.mode === "live" ? new Color(P.up) : new Color(P.dim);
  w.addSpacer(8);

  // Glowna liczba + wykres
  var mid = w.addStack();
  mid.centerAlignContent();
  var col = mid.addStack();
  col.layoutVertically();
  var lbl = col.addText((prim.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = new Color(P.dim);
  col.addSpacer(2);
  var valColor = (prim.metric === "account" || prim.metric === "positions") ? new Color(P.br) : new Color(prim.up ? P.up : P.dn);
  var val = col.addText(prim.text || "-");
  val.font = Font.boldSystemFont(30);
  val.textColor = valColor;
  val.minimumScaleFactor = 0.5;
  val.lineLimit = 1;
  val.shadowColor = new Color(P.br, 0.5);
  val.shadowRadius = 8;
  mid.addSpacer();
  var sImg = mid.addImage(spark(d.spark, 120, 50, prim.up === false ? P.dn : P.up));
  sImg.imageSize = new Size(120, 50);
  w.addSpacer(8);

  // Podsumowanie
  var sub = w.addText("konto " + usd(d.total) + "   " + pctv(d.day_pnl_pct) + " dzis");
  sub.font = Font.systemFont(11);
  sub.textColor = new Color(P.dim);
  sub.minimumScaleFactor = 0.7;
  sub.lineLimit = 1;

  w.addSpacer();
  var ft = w.addStack();
  ft.addSpacer();
  var ts = ft.addText("akt. " + hm());
  ts.font = Font.systemFont(8);
  ts.textColor = new Color(P.dim);

  w.url = BASE_URL;
  done(w);
}
function done(w) {
  if (config.runsInWidget) Script.setWidget(w);
  else w.presentMedium();
  Script.complete();
}
await run();
