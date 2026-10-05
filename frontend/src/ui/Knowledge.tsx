import { useEffect, useMemo, useState } from "react";
import { api, KnowledgeResponse } from "../api/client";

/* „Co umiem" — trwała wiedza bota czytana przez LLM (gdy włączony):
 *  • PLAYBOOK — stałe zasady tradingu + nasze twarde lekcje, pogrupowane w domeny
 *    (ryzyko, reżim, funding, mikrostruktura, sentyment, proces). Każda zasada
 *    ma format „Kategoria · treść", więc rozbijamy ją na grupy jak realny playbook.
 *  • LEKCJE — świeże wnioski destylowane co tydzień z własnego handlu.
 * To jest „pamięć", z którą wystartuje Sonnet. */

// Ikona per domena — żeby playbook czytał się jak podręcznik, nie płaska lista.
const DOMAIN_ICON: Record<string, string> = {
  "Ryzyko i rozmiar": "⚖️",
  "Reżim i trend": "📈",
  "Funding i pozycjonowanie": "🔁",
  "Mikrostruktura i egzekucja": "🩻",
  "Sentyment i narracja": "🎭",
  "Proces i meta": "🧭",
};

type Group = { domain: string; items: string[] };

/** Rozbija „Kategoria · treść" na grupy, zachowując kolejność pierwszego wystąpienia. */
function groupByDomain(rules: string[]): Group[] {
  const order: string[] = [];
  const byDomain = new Map<string, string[]>();
  for (const raw of rules) {
    const idx = raw.indexOf(" · ");
    const domain = idx > 0 ? raw.slice(0, idx) : "Ogólne";
    const text = idx > 0 ? raw.slice(idx + 3) : raw;
    if (!byDomain.has(domain)) { byDomain.set(domain, []); order.push(domain); }
    byDomain.get(domain)!.push(text);
  }
  return order.map((domain) => ({ domain, items: byDomain.get(domain)! }));
}

export function Knowledge() {
  const [k, setK] = useState<KnowledgeResponse | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let alive = true;
    api.knowledge().then((r) => alive && setK(r)).catch(() => alive && setErr(true));
    return () => { alive = false; };
  }, []);

  const groups = useMemo(() => (k ? groupByDomain(k.playbook) : []), [k]);

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Co umiem · operacyjna wiedza silnika</span>
        {k && (
          <span className={`gd-mode ${k.llm_active ? "" : "off"}`}>
            <span className="gd-blip" />{k.llm_active ? "LLM czyta to" : "zbieram (LLM wyłączony)"}
          </span>
        )}
      </div>

      <p className="gd-know-intro">
        Pamięć decyzyjna silnika: zasady tradingu destylowane z praktyki + nasze twarde
        lekcje z 4 miesięcy, napisane pod dane, które realnie dostaje model — cena i wskaźniki
        (RSI/SMA/ATR), <b>funding</b>, <b>open interest</b> i <b>long/short</b> z rynku perpetualów
        oraz <b>Fear&amp;Greed</b>. Teraz krypto gra <b>mechanicznie (bez LLM)</b>, więc wiedza się
        <b> gromadzi</b> i czeka na włączenie Sonneta — który wystartuje <b>z tym wszystkim</b>, nie na zimno.
      </p>

      {err && <p className="gd-empty">Nie udało się pobrać wiedzy — spróbuj odświeżyć.</p>}
      {!k && !err && <p className="gd-empty">Ładuję…</p>}

      {k && (
        <>
          <div className="gd-know-sec">
            <h4 className="gd-know-h">📘 Playbook <span className="gd-know-n">{k.playbook.length} zasad · {groups.length} domen</span></h4>
            <p className="gd-know-sub">Stała baza: zasady z praktyki traderów i systemów + nasze twarde lekcje. Nie rotuje — to fundament, na którym model buduje świeże wnioski.</p>

            {groups.map((g) => (
              <div key={g.domain} className="gd-know-domain">
                <div className="gd-know-dh">
                  <span className="gd-know-di">{DOMAIN_ICON[g.domain] ?? "•"}</span>
                  <span className="gd-know-dn">{g.domain}</span>
                  <span className="gd-know-dc">{g.items.length}</span>
                </div>
                <ul className="gd-know-list">
                  {g.items.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            ))}
          </div>

          <div className="gd-know-sec">
            <h4 className="gd-know-h">🧠 Lekcje z własnego handlu <span className="gd-know-n">{k.lessons.length}</span></h4>
            <p className="gd-know-sub">
              Świeże wnioski, które bot sam destyluje z własnych transakcji (co tydzień) — warstwa,
              która rośnie ponad stały playbook.
              {k.lessons_updated ? ` Ostatnio: ${k.lessons_updated}.` : " Jeszcze żadnej — pojawią się po pierwszym tygodniu handlu."}
            </p>
            {k.lessons.length > 0 ? (
              <ul className="gd-know-list gd-know-lessons">
                {k.lessons.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            ) : (
              <p className="gd-empty">Bot dopiero zbiera własne lekcje — wróć za kilka dni handlu.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
