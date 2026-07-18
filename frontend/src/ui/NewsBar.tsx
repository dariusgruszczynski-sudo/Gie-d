import { useEffect, useState } from "react";
import { api, NewsItem } from "../api/client";

/** A slow-scrolling band of headlines that matter to OUR book — our two legs'
 *  whitelists plus broad US-market news, tagged with any of our tickers named
 *  in the headline. Self-fetching on a gentle 3-minute cadence (the endpoint is
 *  server-cached), independent of the main poll. */
export function NewsBar() {
  const [items, setItems] = useState<NewsItem[]>([]);
  useEffect(() => {
    let dead = false;
    const load = async () => {
      try { const r = await api.news(); if (!dead) setItems(r.items || []); } catch { /* headlines are ambient; ignore */ }
    };
    load();
    const id = setInterval(load, 180000);
    return () => { dead = true; clearInterval(id); };
  }, []);

  if (items.length === 0) return null;
  const row = [...items, ...items]; // seamless loop
  return (
    <div className="gd-news">
      <span className="gd-news-tag">📰 NEWS</span>
      <div className="gd-news-wrap">
        <div className="gd-news-track">
          {row.map((n, i) => (
            <span className="gd-news-item" key={i}>
              {n.tickers.length > 0 && <b className="gd-news-tk">{n.tickers[0]}</b>}
              <span className="t">{n.title}</span>
              {n.source && <em className="src">{n.source}</em>}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
