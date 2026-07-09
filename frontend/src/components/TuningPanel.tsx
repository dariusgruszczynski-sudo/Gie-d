import { useCallback, useEffect, useRef, useState } from "react";
import { api, Tunable } from "../api/client";
import { CollapsibleH2 } from "./CollapsibleH2";

// Panel suwaków do strojenia parametrów zysku/ryzyka NA ŻYWO -- zmiany
// zapisują się do bazy i wchodzą w życie od następnego cyklu, bez redeployu.
function fmtValue(t: Tunable, v: number): string {
  const num = t.is_int ? String(Math.round(v)) : v.toFixed(2);
  return t.unit ? `${num} ${t.unit}` : num;
}

export function TuningPanel() {
  const [tunables, setTunables] = useState<Tunable[]>([]);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saveTimer = useRef<number | null>(null);

  useEffect(() => {
    api
      .tuning()
      .then((r) => setTunables(r.tunables))
      .catch((e) => setError(String(e)));
  }, []);

  const commit = useCallback((values: Record<string, number>) => {
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    // Debounce: dragging a slider fires many events -- save once it settles.
    saveTimer.current = window.setTimeout(async () => {
      setSaving(true);
      setError(null);
      try {
        const res = await api.setTuning(values);
        setTunables(res.tunables); // server clamps -> reflect the true stored value
      } catch (e) {
        setError(String(e));
      } finally {
        setSaving(false);
      }
    }, 350);
  }, []);

  const onSlide = (key: string, raw: number) => {
    setTunables((prev) => prev.map((t) => (t.key === key ? { ...t, value: raw, overridden: true } : t)));
    commit({ [key]: raw });
  };

  const resetOne = (t: Tunable) => onSlide(t.key, t.default);

  if (error && tunables.length === 0) {
    return (
      <div className="panel">
        <h2>Strojenie ryzyka</h2>
        <p className="error-text">Nie udało się wczytać parametrów: {error}</p>
      </div>
    );
  }
  if (tunables.length === 0) return null;

  const changed = tunables.filter((t) => t.overridden).length;

  return (
    <div className="panel">
      <CollapsibleH2
        title="Strojenie ryzyka / zysku"
        open={open}
        onToggle={() => setOpen((o) => !o)}
        summary={changed > 0 ? `${changed} zmienione${saving ? " · zapis…" : ""}` : saving ? "zapis…" : "suwaki"}
      />
      {open && (
        <div className="tuning-body">
          <p className="subtitle" style={{ marginTop: 6 }}>
            Zmiany działają od następnego cyklu, bez restartu. Wartości są przycinane do bezpiecznych zakresów.
          </p>
          <div className="tuning-grid">
            {tunables.map((t) => (
              <div className="tuning-row" key={t.key}>
                <div className="tuning-row-head">
                  <span className="tuning-label">{t.label}</span>
                  <span className={`tuning-value ${t.overridden ? "tuning-value-changed" : ""}`}>
                    {fmtValue(t, t.value)}
                  </span>
                </div>
                <input
                  type="range"
                  min={t.min}
                  max={t.max}
                  step={t.step}
                  value={t.value}
                  onChange={(e) => onSlide(t.key, Number(e.target.value))}
                  className="tuning-slider"
                  aria-label={t.label}
                />
                <div className="tuning-row-foot">
                  <span className="tuning-help">{t.help}</span>
                  {t.overridden && (
                    <button type="button" className="tuning-reset" onClick={() => resetOne(t)}>
                      reset ({fmtValue(t, t.default)})
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          {error && <p className="error-text">Zapis nieudany: {error}</p>}
        </div>
      )}
    </div>
  );
}
