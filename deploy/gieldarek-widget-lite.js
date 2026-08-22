// GielDarek - widget iPhone (Scriptable). Kuloodporny na kopiowanie: 100% ASCII,
// bez emoji, bez template literals. Ciemny gradient + poswiata + wykres + pozycje.
// Adres i token juz wpisane. Glowna liczbe wybierasz w apce: Steruj -> Widzet.
// Instalacja: Scriptable -> plus -> wklej calosc -> nazwij GielDarek.
// Rozmiar: SREDNI = liczba+wykres+ostatni ruch; DUZY = to + skutecznosc + pozycje.

var BASE_URL = "https://46.225.229.113.sslip.io";
var SHARE_TOKEN = "gd-ro-8f3ktq29xr7v";
var THEME = "iris"; // iris | midnight | light

var PAL = {
  iris:     { a: "#0b1024", b: "#14092b", c: "#0a1730", tx: "#eef3fa", dim: "#9aa7c4", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  midnight: { a: "#05070f", b: "#0a1020", c: "#05070f", tx: "#eef3fa", dim: "#7f8ba6", up: "#24e6a6", dn: "#ff5c7a", br: "#34dcff" },
  light:    { a: "#eef3fb", b: "#ffffff", c: "#e7eefb", tx: "#0d1526", dim: "#5b6478", up: "#12a074", dn: "#d83a58", br: "#1478c8" }
};
var P = PAL[THEME] || PAL.iris;
var UP = new Color(P.up), DN = new Color(P.dn), TX = new Color(P.tx), DIM = new Color(P.dim), BR = new Color(P.br);

function usd(v, dp) {
  if (v == null || isNaN(v)) return "-";
  if (dp == null) dp = 0;
  var neg = v < 0;
  var n = Math.abs(Number(v)).toFixed(dp);
  var dot = n.indexOf(".");
  var ip = dot === -1 ? n : n.slice(0, dot);
  var fr = dot === -1 ? "" : n.slice(dot);
  ip = ip.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (neg ? "-$" : "$") + ip + fr;
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
  var lx = xx(series.length - 1), ly = yy(series[series.length - 1]);
  dc.setFillColor(new Color(hex));
  dc.fillEllipse(new Rect(lx - 3, ly - 3, 6, 6));
  return dc.getImage();
}
function head(w, d) {
  var r = w.addStack();
  r.centerAlignContent();
  var m1 = r.addText("GIEL"); m1.font = Font.heavySystemFont(11); m1.textColor = TX;
  var m2 = r.addText("DAREK"); m2.font = Font.heavySystemFont(11); m2.textColor = BR;
  r.addSpacer();
  var lv = r.addText(d.mode === "live" ? "LIVE" : "PAPER");
  lv.font = Font.mediumSystemFont(8);
  lv.textColor = d.mode === "live" ? UP : DIM;
}
function bigNum(stack, d, size) {
  var p = d.primary || {};
  var lbl = stack.addText((p.label || "Zysk automatu").toUpperCase());
  lbl.font = Font.mediumSystemFont(9); lbl.textColor = DIM;
  stack.addSpacer(2);
  var color = (p.metric === "account" || p.metric === "positions") ? BR : (p.up ? UP : DN);
  var val = stack.addText(p.text || "-");
  val.font = Font.boldSystemFont(size);
  val.textColor = color;
  val.minimumScaleFactor = 0.5;
  val.lineLimit = 1;
  val.shadowColor = new Color(P.br, 0.5);
  val.shadowRadius = 8;
}
function lastLine(d) {
  var lt = d.last_trade;
  if (!lt) return "konto " + usd(d.total) + "   gotowka " + usd(d.cash);
  var sign = lt.pnl_usd >= 0 ? "  +" : "  -";
  var pp = (lt.pnl_pct != null) ? "  (" + pctv(lt.pnl_pct) + ")" : "";
  return "Ostatnio: " + lt.symbol + sign + usd(Math.abs(lt.pnl_usd), 0) + pp;
}
function edgeLine(d) {
  var e = d.edge || {};
  var wr = (d.win_rate == null) ? "-" : d.win_rate + "%";
  if (e.avg_win_usd != null && e.avg_loss_usd != null) {
    var po = e.payoff ? "  (" + e.payoff + "x)" : "";
    return "skutecznosc " + wr + "   sr. +" + usd(e.avg_win_usd, 0) + " / " + usd(e.avg_loss_usd, 0) + po;
  }
  return "skutecznosc " + wr + "   " + (d.closed || 0) + " zamkniec";
}
function addPositions(w, d, max) {
  var poss = (d.positions || []).slice(0, max);
  if (poss.length === 0) {
    var none = w.addText("Brak pozycji - gotowka czeka.");
    none.font = Font.systemFont(11); none.textColor = DIM;
    return;
  }
  for (var i = 0; i < poss.length; i++) {
    var pos = poss[i];
    var row = w.addStack();
    row.centerAlignContent();
    var sym = row.addText(pos.symbol || pos.asset || "?");
    sym.font = Font.mediumSystemFont(12); sym.textColor = TX;
    row.addSpacer();
    var pp = pos.pnl_pct != null ? pos.pnl_pct : pos.change_pct;
    var pv = row.addText(usd(pos.value, 0) + "   " + (pp != null ? pctv(pp) : ""));
    pv.font = Font.systemFont(12);
    pv.textColor = (pp || 0) >= 0 ? UP : DN;
    w.addSpacer(3);
  }
}
function foot(w) {
  var f = w.addStack();
  f.addSpacer();
  var ts = f.addText("akt. " + hm());
  ts.font = Font.systemFont(8); ts.textColor = DIM;
}
function subLine(w, d, extra) {
  var s = w.addText("konto " + usd(d.total) + "   " + pctv(d.day_pnl_pct) + " dzis" + (extra || ""));
  s.font = Font.systemFont(11); s.textColor = DIM; s.minimumScaleFactor = 0.7; s.lineLimit = 1;
}

function small(w, d) {
  w.setPadding(14, 15, 13, 15);
  head(w, d); w.addSpacer(6);
  bigNum(w, d, 30); w.addSpacer(5);
  subLine(w, d, "");
  w.addSpacer(); foot(w);
}
function medium(w, d) {
  w.setPadding(14, 16, 13, 16);
  head(w, d); w.addSpacer(7);
  var mid = w.addStack(); mid.centerAlignContent();
  var col = mid.addStack(); col.layoutVertically();
  bigNum(col, d, 27);
  mid.addSpacer();
  var img = mid.addImage(spark(d.spark, 128, 52, (d.primary && d.primary.up === false) ? P.dn : P.up));
  img.imageSize = new Size(128, 52);
  w.addSpacer(8);
  var t = w.addText(lastLine(d));
  t.font = Font.systemFont(11); t.textColor = DIM; t.minimumScaleFactor = 0.7; t.lineLimit = 1;
  w.addSpacer(); foot(w);
}
function large(w, d) {
  w.setPadding(18, 18, 16, 18);
  head(w, d); w.addSpacer(8);
  bigNum(w, d, 40); w.addSpacer(4);
  subLine(w, d, d.market_open ? "   rynek otwarty" : "   rynek zamkniety");
  w.addSpacer(10);
  var img = w.addImage(spark(d.spark, 320, 66, (d.primary && d.primary.up === false) ? P.dn : P.up));
  img.imageSize = new Size(320, 66);
  w.addSpacer(10);
  var e = w.addText(edgeLine(d));
  e.font = Font.systemFont(11); e.textColor = DIM; e.minimumScaleFactor = 0.7; e.lineLimit = 1;
  w.addSpacer(4);
  var l = w.addText(lastLine(d));
  l.font = Font.systemFont(11); l.textColor = DIM; l.minimumScaleFactor = 0.7; l.lineLimit = 1;
  w.addSpacer(10);
  addPositions(w, d, 5);
  w.addSpacer(); foot(w);
}

async function run() {
  var w = new ListWidget();
  bg(w);
  var d;
  try {
    var req = new Request(BASE_URL + "/api/widget?share=" + encodeURIComponent(SHARE_TOKEN));
    req.timeoutInterval = 12;
    d = await req.loadJSON();
  } catch (err) {
    var e = w.addText("GielDarek - brak polaczenia");
    e.textColor = DN; e.font = Font.systemFont(12);
    return finish(w);
  }
  var fam = config.widgetFamily;
  if (fam === "small") small(w, d);
  else if (fam === "medium") medium(w, d);
  else large(w, d); // duzy oraz PODGLAD (Run) -> pokaz pelny uklad
  w.url = BASE_URL;
  finish(w);
}
function finish(w) {
  if (config.runsInWidget) Script.setWidget(w);
  else w.presentLarge();
  Script.complete();
}
await run();
