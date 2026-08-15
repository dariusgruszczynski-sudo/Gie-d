// store.js — trwałe przechowywanie danych w localStorage + model danych.

const KEY = 'spiewnik.v1';

const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);

const DEFAULT_SETTINGS = {
  theme: 'auto',          // auto | light | dark
  fontFamily: "'Georgia', serif",
  fontSize: 18,           // px
  lineHeight: 1.9,
  chordColor: '#e2564a',
  lyricColor: '',         // pusty = domyślny kolor motywu
  chordBold: true,
  showChords: true,
  showDiagrams: true,
  columns: 1,             // 1 | 2
  stageScale: 1.25,       // powiększenie tekstu w trybie występu
  seenWelcome: false,     // czy pokazano ekran powitalny
  songSort: 'updated',    // sortowanie listy: updated | created | title | artist
};

function seed() {
  const s1 = {
    id: uid(),
    title: 'Hey There Delilah',
    artist: "Plain White T's",
    key: 'D',
    capo: 0,
    tempo: 104,
    tags: ['przykład', 'akustyk'],
    body: `{comment: Zwrotka}
[D]Hey there De[F#m]lilah, what's it [Bm]like in New York [G]city?
[D]I'm a thousand [F#m]miles a[Bm]way, but [G]girl tonight you look so [A]pretty, yes you [D]do

{start_of_chorus}
Oh it's [Bm]what you [A]do to [G]me
Oh it's [Bm]what you [A]do to [G]me
{end_of_chorus}`,
    tabs: [],
    notes: 'Kapodaster można dać na II próg dla wyższego brzmienia.',
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  const s2 = {
    id: uid(),
    title: 'Przykład z tabulaturą',
    artist: 'Śpiewnik',
    key: 'Em',
    capo: 0,
    tempo: 0,
    tags: ['tab'],
    body: `{comment: Intro (tabulatura)}
{start_of_tab}
e|-----0-----0-----|
B|---0---0---0---0-|
G|-0-------0-------|
D|-----------------|
A|-----------------|
E|-----------------|
{end_of_tab}

[Em]Tak wygląda [C]tekst z [G]chwytami [D]nad słowami.`,
    tabs: [
      { id: uid(), title: 'Riff główny', content: `e|-------------------|\nB|-------------------|\nG|-------------------|\nD|-----2-4-5---------|\nA|-0-3--------3-0----|\nE|-------------------|` },
    ],
    notes: '',
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  const list = { id: uid(), name: 'Na ognisko', description: 'Piosenki na gitarę przy ognisku', songIds: [s1.id, s2.id], createdAt: Date.now() };
  return { songs: [s1, s2], lists: [list], inbox: [], settings: { ...DEFAULT_SETTINGS } };
}

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) {
      const data = seed();
      save(data);
      return data;
    }
    const data = JSON.parse(raw);
    data.settings = { ...DEFAULT_SETTINGS, ...(data.settings || {}) };
    data.songs = data.songs || [];
    data.lists = data.lists || [];
    data.inbox = data.inbox || [];
    return data;
  } catch (e) {
    console.error('Błąd wczytywania danych, tworzę nowe:', e);
    const data = seed();
    save(data);
    return data;
  }
}

const listeners = [];
let storageWarned = false;
let state = load();

function save(data = state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
  } catch (e) {
    // np. pamięć przeglądarki niedostępna/pełna — działamy dalej w pamięci sesji
    if (!storageWarned) { console.warn('Zapis do localStorage nieudany — dane tylko w tej sesji.', e); storageWarned = true; }
  }
  for (const l of listeners) { try { l(); } catch (err) { console.error(err); } }
}

export const store = {
  get() { return state; },
  get settings() { return state.settings; },

  // --- Piosenki ---
  songs() { return state.songs; },
  song(id) { return state.songs.find((s) => s.id === id); },
  createSong(partial = {}) {
    const s = {
      id: uid(), title: 'Nowa piosenka', artist: '', key: '', capo: 0, tempo: 0,
      tags: [], body: '', tabs: [], notes: '',
      createdAt: Date.now(), updatedAt: Date.now(), ...partial,
    };
    state.songs.unshift(s);
    save();
    return s;
  },
  updateSong(id, patch) {
    const s = this.song(id);
    if (!s) return null;
    Object.assign(s, patch, { updatedAt: Date.now() });
    save();
    return s;
  },
  deleteSong(id) {
    state.songs = state.songs.filter((s) => s.id !== id);
    state.lists.forEach((l) => { l.songIds = l.songIds.filter((sid) => sid !== id); });
    save();
  },
  duplicateSong(id) {
    const s = this.song(id);
    if (!s) return null;
    const copy = { ...structuredClone(s), id: uid(), title: s.title + ' (kopia)', createdAt: Date.now(), updatedAt: Date.now() };
    state.songs.unshift(copy);
    save();
    return copy;
  },

  // --- Listy (setlisty) ---
  lists() { return state.lists; },
  list(id) { return state.lists.find((l) => l.id === id); },
  createList(name = 'Nowa lista') {
    const l = { id: uid(), name, description: '', songIds: [], createdAt: Date.now() };
    state.lists.unshift(l);
    save();
    return l;
  },
  updateList(id, patch) {
    const l = this.list(id);
    if (!l) return null;
    Object.assign(l, patch);
    save();
    return l;
  },
  deleteList(id) {
    state.lists = state.lists.filter((l) => l.id !== id);
    save();
  },
  addToList(listId, songId) {
    const l = this.list(listId);
    if (l && !l.songIds.includes(songId)) { l.songIds.push(songId); save(); }
  },
  removeFromList(listId, songId) {
    const l = this.list(listId);
    if (l) { l.songIds = l.songIds.filter((id) => id !== songId); save(); }
  },
  reorderList(listId, fromIdx, toIdx) {
    const l = this.list(listId);
    if (!l) return;
    const arr = l.songIds;
    if (fromIdx < 0 || fromIdx >= arr.length || toIdx < 0 || toIdx >= arr.length) return;
    const [m] = arr.splice(fromIdx, 1);
    arr.splice(toIdx, 0, m);
    save();
  },

  // --- Ustawienia ---
  updateSettings(patch) {
    Object.assign(state.settings, patch);
    save();
  },

  // --- Kopia zapasowa ---
  exportJSON() {
    return JSON.stringify(state, null, 2);
  },
  importJSON(json, { merge = false } = {}) {
    const incoming = JSON.parse(json);
    if (!incoming.songs || !incoming.lists) throw new Error('Plik nie wygląda na kopię śpiewnika.');
    if (merge) {
      state.songs = [...incoming.songs, ...state.songs];
      state.lists = [...incoming.lists, ...state.lists];
    } else {
      state = { ...seed(), ...incoming };
      state.settings = { ...DEFAULT_SETTINGS, ...(incoming.settings || {}) };
    }
    save();
    return state;
  },
  resetSettings() {
    state.settings = { ...DEFAULT_SETTINGS };
    save();
  },

  // --- Poczekalnia (inbox) ---
  inbox() { return state.inbox; },
  addInbox(item) {
    const it = { id: uid(), title: '', author: '', source: '', url: '', createdAt: Date.now(), ...item };
    // pomiń duplikaty po URL
    if (it.url && state.inbox.some((x) => x.url === it.url)) return null;
    state.inbox.unshift(it);
    save();
    return it;
  },
  updateInbox(id, patch) { const it = state.inbox.find((x) => x.id === id); if (it) { Object.assign(it, patch); save(); } return it; },
  removeInbox(id) { state.inbox = state.inbox.filter((x) => x.id !== id); save(); },
  clearInbox() { state.inbox = []; save(); },

  // --- Synchronizacja ---
  subscribe(fn) { listeners.push(fn); },
  // Wczytuje bibliotekę z serwera do lokalnego stanu (w miejscu — zachowuje referencję settings).
  loadFrom(lib) {
    if (!lib || typeof lib !== 'object') return;
    state.songs = Array.isArray(lib.songs) ? lib.songs : [];
    state.lists = Array.isArray(lib.lists) ? lib.lists : [];
    state.inbox = Array.isArray(lib.inbox) ? lib.inbox : [];
    state.settings = { ...DEFAULT_SETTINGS, ...(lib.settings || {}) };
    save();
  },
};

export { DEFAULT_SETTINGS, uid };
