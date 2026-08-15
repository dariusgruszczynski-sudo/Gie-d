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
    if (!r.ok) return false;
    const d = await r.json();           // upewnij się, że to nasze API (a nie np. statyczny hosting)
    return !!(d && d.service === 'spiewnik');
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
    return { ok: false, error: 'Automatyczne pobieranie działa tylko w wersji z serwerem. Tutaj skorzystaj z „Wklej tekst ręcznie” poniżej.' };
  }
}

// Wyszukuje w sieci OPRACOWANIA Z CHWYTAMI. Zwraca listę wyników do wyboru.
// Działa po częściowym tytule, nazwie zespołu (lub jej braku) albo fragmencie tekstu.
export async function searchWeb({ q = '', artist = '', title = '' } = {}) {
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (artist) params.set('artist', artist);
  if (title) params.set('title', title);
  try {
    const { status, data } = await api(`/api/search?${params.toString()}`);
    if (status === 200 && data.ok) return { ok: true, items: data.items || [], provider: data.provider };
    return { ok: false, error: data.error || `Nie udało się wyszukać (status ${status}).` };
  } catch (e) {
    return { ok: false, error: 'Wyszukiwanie działa w wersji z serwerem. Tutaj użyj „Wklej tekst ręcznie".' };
  }
}

// Importuje dowolną stronę z chwytami/tabami po adresie URL.
export async function importUrl(url) {
  try {
    const { status, data } = await api(`/api/import?url=${encodeURIComponent(url)}`);
    if (status === 200 && data.ok) return { ok: true, text: data.text, source: data.source };
    return { ok: false, error: data.error || `Nie udało się pobrać (status ${status}).` };
  } catch (e) {
    return { ok: false, error: 'Import po URL działa tylko w wersji z serwerem. Tutaj skorzystaj z „Wklej tekst ręcznie” poniżej.' };
  }
}
