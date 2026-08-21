import { useEffect, useState } from "react";

/* ===========================================================================
   Warstwa NAUKA (paczka B): jeden wspólny słownik pojęć + legenda kolorów/ikon
   zasila: tooltipy „co to znaczy?", ekran Słownik, Legendę i onboarding.
   Wszystko po ludzku, po polsku. Zero zależności zewnętrznych.
   =========================================================================== */

export interface Term { key: string; name: string; plain: string }

// Słownik po ludzku — definicje krótkie, konkretne, bez żargonu.
export const GLOSSARY: Term[] = [
  { key: "zysk_automatu", name: "Zysk automatu", plain: "Ile bot dorobił OD SIEBIE, bez Twoich wpłat. Wpłata dodaje gotówkę, ale nie liczy się jako zysk." },
  { key: "skutecznosc", name: "Skuteczność", plain: "Jak CZĘSTO transakcja kończy się na plus. Uwaga: ważniejsze, czy wygrane są większe od strat — patrz Edge." },
  { key: "edge", name: "Edge (przewaga)", plain: "Ile ŚREDNIO wychodzi na jedną transakcję: średnia wygrana vs średnia strata. Dodatni = bot zarabia, nawet gdy wygrywa rzadko." },
  { key: "payoff", name: "Payoff", plain: "Ile razy średnia wygrana jest większa od średniej straty. 2× = wygrane są dwa razy większe niż straty." },
  { key: "na_transakcje", name: "Na transakcję", plain: "Średni zysk/strata z jednej transakcji. To najuczciwsza liczba: dodatnia = strategia realnie zarabia." },
  { key: "rezim", name: "Reżim rynku", plain: "Nastrój rynku: sprzyja (risk-on), neutralny albo ostrożnie (risk-off). W risk-off bot trzyma więcej gotówki." },
  { key: "prog_pewnosci", name: "Próg pewności", plain: "Ile pewności musi mieć bot, żeby wejść. ROŚNIE z liczbą pozycji — im więcej trzyma, tym mocniejszy sygnał musi być." },
  { key: "min_hold", name: "Min-hold (anty-churn)", plain: "Minimalny czas trzymania świeżej pozycji, żeby bot nie sprzedawał w kółko na spreadzie. Realny zysk i tak bierze od razu." },
  { key: "trailing", name: "Trailing stop", plain: "Ruchomy stop: chroni zysk, sprzedaje dopiero gdy cena spadnie o X% OD SZCZYTU. Pozwala wygranym rosnąć." },
  { key: "hard_tp", name: "Sufit zysku", plain: "Gdy pozycja urośnie o zadane %, bot bierze CAŁY zysk i nie oddaje go z powrotem." },
  { key: "stop_loss", name: "Stop-loss", plain: "Bezpiecznik: gdy pozycja spadnie o zadane % od wejścia, bot zamyka ją, żeby uciąć stratę." },
  { key: "ryzyko", name: "Skala ryzyka", plain: "Jak agresywnie bot gra TERAZ: ile masz w akcjach, jak blisko limitów straty i jak nastawiony jest rynek." },
  { key: "conviction", name: "Duże zakłady (conviction)", plain: "Im pewniejszy sygnał, tym większa pozycja (do 2×) — z twardym sufitem ryzyka na transakcję, żeby nie wysadzić konta." },
  { key: "vs_spy", name: "Bot vs SPY", plain: "Czy bot bije zwykłe trzymanie indeksu SPY. Plus = zarabiasz więcej, niż gdybyś po prostu trzymał indeks." },
  { key: "kiedy_sprzedam", name: "Kiedy sprzedam", plain: "Plan wyjścia dla każdej pozycji: czy sprzedaję teraz, czekam na cel, czy trzymam — i dlaczego." },
];

const GLO: Record<string, Term> = Object.fromEntries(GLOSSARY.map((t) => [t.key, t]));

// Legenda kolorów / ikon.
export const LEGEND: Array<{ sym: string; cls?: string; label: string }> = [
  { sym: "●", cls: "gd-up", label: "Zielony/mięta = zysk, na plusie" },
  { sym: "●", cls: "gd-down", label: "Czerwony/róż = strata, na minusie" },
  { sym: "🟢", label: "Zysk do wzięcia — pozycja gotowa do sprzedaży" },
  { sym: "↗", label: "Na plusie, rośnie — czeka na cel" },
  { sym: "🔒", label: "Anty-churn — świeża pozycja, chwilowo zablokowana" },
  { sym: "⏳", label: "Czekam — brak wyraźnego ruchu" },
  { sym: "⚠", label: "Blisko stopu — bronię kapitału" },
  { sym: "⚡", label: "Duże zakłady (conviction) włączone" },
  { sym: "☀ ⛅ ⛈", label: "Pogoda rynku: sprzyja / neutralnie / ostrożnie" },
];

/* Tooltip „co to znaczy?" — mały ? przy metryce; dotknięcie pokazuje wyjaśnienie. */
export function Info({ term }: { term: string }) {
  const [open, setOpen] = useState(false);
  const t = GLO[term];
  if (!t) return null;
  return (
    <span className="gd-info">
      <button className="gd-info-q" aria-label={`Co to znaczy: ${t.name}`} onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}>?</button>
      {open && (
        <span className="gd-info-pop" role="tooltip" onClick={(e) => e.stopPropagation()}>
          <b>{t.name}</b>
          <span>{t.plain}</span>
          <button className="gd-info-close" onClick={() => setOpen(false)}>OK</button>
        </span>
      )}
    </span>
  );
}

/* Modal POMOC — dwie zakładki: Słownik pojęć + Legenda. Otwierany z „?" w railu. */
export function HelpModal({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"slownik" | "legenda">("slownik");
  return (
    <div className="gd-modal-bg" onClick={onClose}>
      <div className="gd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="gd-modal-top">
          <b>Pomoc</b>
          <button className="gd-modal-x" onClick={onClose}>✕</button>
        </div>
        <div className="gd-modal-tabs">
          <button className={tab === "slownik" ? "on" : ""} onClick={() => setTab("slownik")}>Słownik</button>
          <button className={tab === "legenda" ? "on" : ""} onClick={() => setTab("legenda")}>Legenda</button>
        </div>
        <div className="gd-modal-body">
          {tab === "slownik" ? (
            GLOSSARY.map((t) => (
              <div className="gd-gloss-row" key={t.key}>
                <b>{t.name}</b>
                <span>{t.plain}</span>
              </div>
            ))
          ) : (
            LEGEND.map((l, i) => (
              <div className="gd-legend-row" key={i}>
                <span className={`gd-legend-sym ${l.cls ?? ""}`}>{l.sym}</span>
                <span>{l.label}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

/* ONBOARDING — 4 slajdy przy pierwszym wejściu (localStorage). „Pomiń" zawsze. */
const SLIDES = [
  { emoji: "💰", title: "Zysk automatu", body: "Wielka liczba na Pulpicie to ile bot dorobił OD SIEBIE — bez Twoich wpłat. Zielony = plus, czerwony = minus." },
  { emoji: "📈", title: "Pozycje i „kiedy sprzedam”", body: "Na ekranie Pozycje każda akcja ma miarkę: czy sprzedam teraz, czekam na cel, czy trzymam — i dlaczego." },
  { emoji: "🎯", title: "Skuteczność vs Edge", body: "Nie patrz tylko, jak często wygrywa. Ważniejsze: czy wygrane są większe od strat (Edge). Bot może wygrywać rzadko i zarabiać." },
  { emoji: "🛟", title: "Bezpieczniki", body: "Bot ma stop-loss, limity straty i pauzę. Widok możesz przełączyć na „prosty” (lewy pasek), a „?” zawsze wyjaśni pojęcia." },
];
const ONBOARD_KEY = "gd-onboarded-v1";

export function useOnboarding(): [boolean, () => void] {
  const [show, setShow] = useState(false);
  useEffect(() => {
    try { if (localStorage.getItem(ONBOARD_KEY) !== "1") setShow(true); } catch { /* ignore */ }
  }, []);
  const done = () => { try { localStorage.setItem(ONBOARD_KEY, "1"); } catch { /* ignore */ } setShow(false); };
  return [show, done];
}

export function Onboarding({ onDone }: { onDone: () => void }) {
  const [i, setI] = useState(0);
  const last = i === SLIDES.length - 1;
  const s = SLIDES[i];
  return (
    <div className="gd-modal-bg">
      <div className="gd-onboard" onClick={(e) => e.stopPropagation()}>
        <div className="gd-onboard-emoji">{s.emoji}</div>
        <b className="gd-onboard-title">{s.title}</b>
        <p className="gd-onboard-body">{s.body}</p>
        <div className="gd-onboard-dots">
          {SLIDES.map((_, k) => <span key={k} className={k === i ? "on" : ""} />)}
        </div>
        <div className="gd-onboard-actions">
          <button className="gd-onboard-skip" onClick={onDone}>Pomiń</button>
          <button className="gd-onboard-next" onClick={() => (last ? onDone() : setI(i + 1))}>{last ? "Zaczynamy" : "Dalej"}</button>
        </div>
      </div>
    </div>
  );
}
