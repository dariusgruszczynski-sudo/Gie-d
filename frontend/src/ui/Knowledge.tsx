import { useEffect, useState } from "react";
import { api, KnowledgeResponse } from "../api/client";

/* „Co umiem" — trwała wiedza bota czytana przez LLM (gdy włączony):
 *  • PLAYBOOK — stałe zasady + nasze twarde lekcje (z 4 mies. akcji).
 *  • LEKCJE — świeże wnioski destylowane co tydzień z własnego handlu.
 * To jest „pamięć", z którą wystartuje Sonnet. Prosto, czytelnie, bez ozdób. */
export function Knowledge() {
  const [k, setK] = useState<KnowledgeResponse | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let alive = true;
    api.knowledge().then((r) => alive && setK(r)).catch(() => alive && setErr(true));
    return () => { alive = false; };
  }, []);

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Co umiem · wiedza dla LLM</span>
        {k && (
          <span className={`gd-mode ${k.llm_active ? "" : "off"}`}>
            <span className="gd-blip" />{k.llm_active ? "LLM czyta to" : "zbieram (LLM wyłączony)"}
          </span>
        )}
      </div>

      <p className="gd-know-intro">
        To jest pamięć bota, którą czyta model, gdy jest włączony. Teraz krypto gra
        <b> mechanicznie (bez LLM)</b>, więc wiedza się <b>gromadzi</b> — i czeka na
        włączenie Sonneta, który wystartuje <b>z tym wszystkim</b>, nie na zimno.
      </p>

      {err && <p className="gd-empty">Nie udało się pobrać wiedzy — spróbuj odświeżyć.</p>}
      {!k && !err && <p className="gd-empty">Ładuję…</p>}

      {k && (
        <>
          <div className="gd-know-sec">
            <h4 className="gd-know-h">📘 Zasady (playbook) <span className="gd-know-n">{k.playbook.length}</span></h4>
            <p className="gd-know-sub">Stała baza: zasady traderów + nasze twarde lekcje. Nie rotuje.</p>
            <ul className="gd-know-list">
              {k.playbook.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>

          <div className="gd-know-sec">
            <h4 className="gd-know-h">🧠 Lekcje z własnego handlu <span className="gd-know-n">{k.lessons.length}</span></h4>
            <p className="gd-know-sub">
              Świeże wnioski, które bot sam destyluje z własnych transakcji (co tydzień).
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
