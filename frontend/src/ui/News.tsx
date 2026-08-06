import { useEffect, useState } from "react";
import { api, NewsSourcesResponse } from "../api/client";

function sentClass(score?: number): string {
  if (score === undefined) return "neu";
  return score > 0.15 ? "pos" : score < -0.15 ? "neg" : "neu";
}

// Keyed (główne) źródła pierwsze, potem per-ticker, RSS, Reddit na końcu.
function groupOrder(g: string): number {
  if (g.startsWith("Keyed")) return 0;
  if (g === "Per-ticker") return 1;
  if (g === "Reddit") return 3;
  return 2;
}

export function News() {
  const [data, setData] = useState<NewsSourcesResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    setBusy(true);
    setMsg(null);
    try {
      setData(await api.newsSources());
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    load();
    const id = setInterval(load, 60000);
    return () => clearInterval(id);
  }, []);

  const groups = data ? Array.from(new Set(data.sources.map((s) => s.group))).sort((a, b) => groupOrder(a) - groupOrder(b)) : [];

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">
          Newsy {data ? `· ${data.summary.ok} źródeł OK · ${data.summary.down} padło · ${data.summary.headlines} nagłówków na żywo` : ""}
        </span>
        <button className="gd-btn" disabled={busy} onClick={load}>{busy ? "…" : "Odśwież"}</button>
      </div>
      {data?.discovery && data.discovery.total > 0 && (
        <div className="gd-discovery">
          <span className="gd-discovery-dot" />
          Automat sam szuka nowych źródeł raz dziennie · <b>{data.discovery.total}</b> auto-odkrytych
          {data.discovery.added_last > 0 && <> · ostatnio dołożył <b>+{data.discovery.added_last}</b>{data.discovery.date ? ` (${data.discovery.date})` : ""}</>}
        </div>
      )}
      {msg && <div className="gd-ribbon">{msg}</div>}
      {!data ? (
        <p className="gd-empty">Sprawdzam źródła…</p>
      ) : (
        <>
          <p className="gd-note">
            Do czego Claude ma połączenie i CO REALNIE WIDZI teraz. Zielone = źródło zwróciło dane w tym odczycie;
            szare = padło (zwykle blokada datacenter-IP albo limit free-tier) — nieszkodliwe, dopóki keyed i część RSS świecą.
          </p>
          {groups.map((g) => (
            <div key={g} className="gd-newsgrp">
              <div className="gd-newsgrp-h">{g}</div>
              <div className="gd-srcgrid">
                {data.sources
                  .filter((s) => s.group === g)
                  .map((s) => (
                    <div className="gd-src" key={s.name} title={s.status === "ok" ? `${s.count} nagłówków` : "brak danych w tym odczycie"}>
                      <span className={`gd-hl-led ${s.status === "ok" ? "ok" : "down"}`} />
                      <span className="gd-src-name">{s.name}</span>
                      <span className="gd-src-cnt">{s.count}</span>
                    </div>
                  ))}
              </div>
            </div>
          ))}

          <div className="gd-newsgrp-h" style={{ marginTop: 18 }}>Na żywo — co widzę</div>
          <div className="gd-feed">
            {data.headlines.length === 0 ? (
              <p className="gd-empty">Brak nagłówków w tym odczycie.</p>
            ) : (
              data.headlines.map((h, i) => (
                <div className="gd-feed-item" key={i}>
                  <div className="gd-feed-title">{h.title}</div>
                  <div className="gd-feed-meta">
                    <span className="gd-feed-src">{h.source}</span>
                    {h.sentiment_label && <span className={`gd-sent ${sentClass(h.sentiment_score)}`}>{h.sentiment_label}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
