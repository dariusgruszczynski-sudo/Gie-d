// search-client.js — klient modułu "Wyszukaj". Rozmawia z backendem
// (server/server.js). Gdy backend jest niedostępny (np. otwarcie pliku
// bezpośrednio z dysku), zwraca czytelny komunikat i pozwala wkleić tekst ręcznie.

async function api(pathAndQuery) {
  const r = await fetch(pathAndQuery, { headers: { Accept: 'application/json' } });
  const data = await r.json().catch(() => ({}));
  return { status: r.status, data };
}

export async function backendAvailable() {
  try {
    const r = await fetch('/api/health', { cache: 'no-store' });
    return r.ok;
  } catch {
    return false;
  }
}

// Wyszukuje tekst piosenki po wykonawcy i tytule.
export async function searchLyrics(artist, title) {
  try {
    const { status, data } = await api(`/api/lyrics?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`);
    if (status === 200 && data.ok) return { ok: true, lyrics: data.lyrics };
    return { ok: false, error: data.error || `Nie znaleziono (status ${status}).` };
  } catch (e) {
    return { ok: false, error: 'Backend niedostępny. Uruchom serwer (node server/server.js) lub wklej tekst ręcznie.' };
  }
}

// Importuje dowolną stronę z chwytami/tabami po adresie URL.
export async function importUrl(url) {
  try {
    const { status, data } = await api(`/api/import?url=${encodeURIComponent(url)}`);
    if (status === 200 && data.ok) return { ok: true, text: data.text, source: data.source };
    return { ok: false, error: data.error || `Nie udało się pobrać (status ${status}).` };
  } catch (e) {
    return { ok: false, error: 'Backend niedostępny. Uruchom serwer, aby importować po URL.' };
  }
}
