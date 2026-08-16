// app.js — główny moduł aplikacji Śpiewnik.
import { store } from './store.js';
import { render as renderChordPro, extractChords, transposeSource, plainToChordPro, stretchChords } from './chordpro.js';
import { chordDiagram, hasShape } from './chords.js';
import { searchLyrics, importUrl, searchWeb, resolveLink, detectChords, detectChordsFile } from './search-client.js';
import { sync } from './sync.js';
import { SUGGEST_PL, SUGGEST_WORLD } from './suggestions.js';

// ------------------------------------------------------------------ helpers
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const el = (tag, props = {}, ...children) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k === 'text') n.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v !== null && v !== undefined && v !== false) n.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    n.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return n;
};
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const fmtDate = (ts) => new Date(ts).toLocaleDateString('pl-PL', { day: '2-digit', month: 'short', year: 'numeric' });

// Automatycznie ustawia chwyty NAD tekstem: jeśli tekst nie jest jeszcze w
// formacie ChordPro (brak [ ]) a wykryto chwyty, konwertuje. W przeciwnym razie
// zostawia bez zmian. Zwraca { body, converted }.
function autoChordify(body) {
  // plainToChordPro jest bezpieczne per-linia (linie z [chwytami] pomija), więc
  // działa też na treści mieszanej (część surowa, część już w ChordPro).
  const conv = plainToChordPro(body || '');
  return { body: conv, converted: conv !== (body || '') };
}

// Rozbija linię ChordPro na czysty tekst + listę chwytów z pozycjami w tekście.
function lineToPlain(line) {
  const chords = []; let plain = ''; const re = /\[([^\]]+)\]/g; let last = 0, m;
  while ((m = re.exec(line))) { plain += line.slice(last, m.index); chords.push({ pos: plain.length, chord: m[1] }); last = re.lastIndex; }
  plain += line.slice(last);
  return { plain, chords };
}
// Buduje linię ChordPro z tekstu + chwytów (chwyty w rosnących pozycjach).
function plainToLine(plain, chords) {
  const sorted = [...chords].sort((a, b) => a.pos - b.pos);
  let out = '';
  for (let i = 0; i <= plain.length; i++) {
    for (const c of sorted) if (c.pos === i) out += `[${c.chord}]`;
    if (i < plain.length) out += plain[i];
  }
  return out;
}

function toast(msg, type = 'info') {
  const t = el('div', { class: `toast toast-${type}`, text: msg });
  $('#toastRoot').append(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 2800);
}

function modal({ title, body, actions = [], wide = false, onClose }) {
  const root = $('#modalRoot');
  const overlay = el('div', { class: 'modal-overlay' });
  const box = el('div', { class: 'modal' + (wide ? ' modal-wide' : '') });
  const close = () => { overlay.remove(); onClose && onClose(); };
  box.append(
    el('div', { class: 'modal-head' },
      el('h3', { text: title }),
      el('button', { class: 'icon-btn', onClick: close, title: 'Zamknij' }, '✕')
    ),
    el('div', { class: 'modal-body' }, body),
    actions.length ? el('div', { class: 'modal-foot' }, ...actions) : null,
  );
  overlay.append(box);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  root.append(overlay);
  return { close, box };
}

function confirmDialog(message, onYes, { danger = false, yes = 'Tak', no = 'Anuluj' } = {}) {
  const m = modal({
    title: 'Potwierdzenie',
    body: el('p', { text: message }),
    actions: [
      el('button', { class: 'btn', onClick: () => m.close() }, no),
      el('button', { class: 'btn ' + (danger ? 'btn-danger' : 'btn-primary'), onClick: () => { m.close(); onYes(); } }, yes),
    ],
  });
}

function copyText(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text); return; }
  } catch { /* fallback poniżej */ }
  const ta = el('textarea', { style: 'position:fixed;opacity:0' }); ta.value = text;
  document.body.append(ta); ta.select();
  try { document.execCommand('copy'); } catch { /* ignore */ }
  ta.remove();
}

async function download(filename, text, type = 'application/json') {
  // W wersji hostowanej na claude.ai zwykły <a download> jest zablokowany —
  // korzystamy z natywnej funkcji zapisu, jeśli jest dostępna.
  try {
    if (window.claude && typeof window.claude.use === 'function') {
      const dl = await window.claude.use('downloads');
      if (dl) { await dl.save({ filename, data: text }); return; }
    }
  } catch (e) { /* np. użytkownik anulował zapis — po cichu wróć do metody zapasowej */ }
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = el('a', { href: url, download: filename });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ------------------------------------------------------------------ state
const app = {
  view: 'songs',
  songId: null,
  listId: null,
  editing: false,
  filter: '',
  tagFilter: '',
};

// ------------------------------------------------------------------ theming
function applySettings() {
  const s = store.settings;
  const root = document.documentElement;
  root.style.setProperty('--song-font', s.fontFamily);
  root.style.setProperty('--song-size', s.fontSize + 'px');
  root.style.setProperty('--song-line', s.lineHeight);
  root.style.setProperty('--chord-color', s.chordColor);
  root.style.setProperty('--lyric-color', s.lyricColor || 'var(--text)');
  root.style.setProperty('--chord-weight', s.chordBold ? '700' : '500');
  let theme = s.theme;
  if (theme === 'auto') theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  root.setAttribute('data-theme', theme);
}

// ------------------------------------------------------------------ router
function go(view, opts = {}) {
  app.view = view;
  if ('songId' in opts) app.songId = opts.songId;
  if ('listId' in opts) app.listId = opts.listId;
  app.editing = opts.editing || false;
  render();
  if (window.innerWidth < 860) $('#sidebar').classList.remove('open');
}

function render() {
  applySettings();
  $$('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.view === app.view));
  const titleMap = { songs: 'Piosenki', lists: 'Listy', suggest: 'Propozycje', inbox: 'Poczekalnia', search: 'Wyszukaj', settings: 'Wygląd' };
  updateInboxBadge();
  const actions = $('#topbarActions'); actions.innerHTML = '';
  const view = $('#view'); view.innerHTML = '';
  $('#viewTitle').textContent = titleMap[app.view] || 'Śpiewnik';

  if (app.view === 'songs' && app.songId) return renderSongDetail(view, actions);
  if (app.view === 'songs') return renderSongs(view, actions);
  if (app.view === 'lists' && app.listId) return renderListDetail(view, actions);
  if (app.view === 'lists') return renderLists(view, actions);
  if (app.view === 'suggest') return renderSuggestions(view, actions);
  if (app.view === 'inbox') return renderInbox(view, actions);
  if (app.view === 'search') return renderSearch(view, actions);
  if (app.view === 'settings') return renderSettings(view, actions);
}

// ------------------------------------------------------------------ Piosenki
function allTags() {
  const set = new Set();
  store.songs().forEach((s) => (s.tags || []).forEach((t) => set.add(t)));
  return [...set].sort();
}

function renderSongs(view, actions) {
  $('#viewTitle').textContent = 'Piosenki';
  actions.append(el('button', { class: 'btn btn-primary', onClick: () => newSong() }, '＋ Nowa'));

  const search = el('input', {
    class: 'input search-input', placeholder: '🔎 Szukaj po tytule, wykonawcy, tagu…', value: app.filter,
    oninput: (e) => { app.filter = e.target.value; refreshList(); },
  });
  const tagBar = el('div', { class: 'tagbar' });
  const buildTagBar = () => {
    tagBar.innerHTML = '';
    tagBar.append(el('button', { class: 'chip' + (app.tagFilter === '' ? ' chip-on' : ''), onClick: () => { app.tagFilter = ''; render(); } }, 'Wszystkie'));
    allTags().forEach((t) => tagBar.append(el('button', {
      class: 'chip' + (app.tagFilter === t ? ' chip-on' : ''), onClick: () => { app.tagFilter = (app.tagFilter === t ? '' : t); render(); },
    }, '#' + t)));
  };
  buildTagBar();

  // sortowanie + filtr tonacji + licznik
  const keysPresent = [...new Set(store.songs().map((s) => (s.key || '').trim()).filter(Boolean))].sort();
  const sortSel = el('select', { class: 'input mini', onchange: (e) => { store.updateSettings({ songSort: e.target.value }); refreshList(); } },
    ...[['updated', 'Ostatnio zmienione'], ['created', 'Ostatnio dodane'], ['title', 'Tytuł A–Z'], ['artist', 'Wykonawca A–Z']]
      .map(([v, l]) => el('option', { value: v, ...(store.settings.songSort === v ? { selected: true } : {}) }, l)));
  const keySel = el('select', { class: 'input mini', onchange: (e) => { app.keyFilter = e.target.value; refreshList(); } },
    el('option', { value: '' }, 'Każda tonacja'),
    ...keysPresent.map((k) => el('option', { value: k, ...(app.keyFilter === k ? { selected: true } : {}) }, '🎹 ' + k)));
  const count = el('span', { class: 'muted-sm count' });

  const listWrap = el('div', { class: 'card-grid' });
  const refreshList = () => {
    listWrap.innerHTML = '';
    const q = app.filter.trim().toLowerCase();
    let songs = store.songs().filter((s) => {
      if (app.tagFilter && !(s.tags || []).includes(app.tagFilter)) return false;
      if (app.keyFilter && (s.key || '').trim() !== app.keyFilter) return false;
      if (!q) return true;
      return (s.title + ' ' + s.artist + ' ' + (s.tags || []).join(' ')).toLowerCase().includes(q);
    });
    const sort = store.settings.songSort;
    const cmp = {
      updated: (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0),
      created: (a, b) => (b.createdAt || 0) - (a.createdAt || 0),
      title: (a, b) => (a.title || '').localeCompare(b.title || '', 'pl'),
      artist: (a, b) => (a.artist || '').localeCompare(b.artist || '', 'pl'),
    }[sort] || (() => 0);
    songs = [...songs].sort(cmp);
    count.textContent = `${songs.length} ${plural(songs.length, 'piosenka', 'piosenki', 'piosenek')}`;
    if (!songs.length) {
      listWrap.append(el('div', { class: 'empty' },
        el('div', { class: 'empty-emoji' }, '🎼'),
        el('p', {}, 'Brak piosenek. Dodaj pierwszą albo skorzystaj z modułu „Wyszukaj”.'),
        el('button', { class: 'btn btn-primary', onClick: () => newSong() }, '＋ Nowa piosenka'),
      ));
      return;
    }
    for (const s of songs) {
      const chords = extractChords(s.body).slice(0, 8);
      listWrap.append(el('div', { class: 'song-card', onClick: () => go('songs', { songId: s.id }) },
        el('div', { class: 'song-card-main' },
          el('div', { class: 'song-title', text: s.title }),
          el('div', { class: 'song-artist', text: s.artist || '—' }),
          el('div', { class: 'song-meta' },
            s.key ? el('span', { class: 'pill' }, '🎹 ' + s.key) : null,
            s.tempo ? el('span', { class: 'pill' }, '⏱ ' + s.tempo) : null,
            s.tabs && s.tabs.length ? el('span', { class: 'pill' }, '🎸 tab') : null,
            ...(s.tags || []).map((t) => el('span', { class: 'pill pill-tag' }, '#' + t)),
          ),
          chords.length ? el('div', { class: 'song-chords', text: chords.join('  ') }) : null,
        ),
        el('div', { class: 'song-card-side' }, el('span', { class: 'muted-sm', text: fmtDate(s.updatedAt) }), el('span', { class: 'chev' }, '›')),
      ));
    }
  };
  refreshList();

  view.append(
    el('div', { class: 'toolbar' }, search,
      el('div', { class: 'list-controls' }, sortSel, keysPresent.length ? keySel : null, count)),
    tagBar, listWrap);
}

function newSong(partial) {
  const s = store.createSong(partial);
  go('songs', { songId: s.id, editing: true });
}

// ------------------------------------------------ Szczegóły / widok piosenki
// Transpozycja jest ZAPISYWANA przy piosence (i synchronizuje się między urządzeniami).
function currentSteps(id) { const s = store.song(id); return (s && s.transpose) || 0; }
function setTranspose(id, steps) { store.updateSong(id, { transpose: steps }); }

function renderSongDetail(view, actions) {
  const s = store.song(app.songId);
  if (!s) { app.songId = null; return renderSongs(view, actions); }
  $('#viewTitle').textContent = s.title;

  if (app.editing) return renderSongEditor(view, actions, s);

  // pasek akcji
  actions.append(
    el('button', { class: 'btn btn-sm', onClick: () => go('songs') }, '‹ Wróć'),
    el('button', { class: 'btn btn-sm', onClick: () => { app.editing = true; render(); } }, '✏️ Edytuj'),
    el('button', { class: 'btn btn-sm', onClick: () => openPerformance(s.id) }, '▶︎ Występ'),
    el('button', { class: 'btn btn-sm', onClick: () => window.print() }, '🖨 Drukuj'),
    el('button', { class: 'btn btn-sm', onClick: () => addToListDialog(s.id) }, '＋ Do listy'),
    el('button', { class: 'btn btn-sm', onClick: () => { store.duplicateSong(s.id); toast('Skopiowano piosenkę'); go('songs'); } }, '⧉'),
    el('button', { class: 'btn btn-sm btn-danger', onClick: () => confirmDialog(`Usunąć „${s.title}”?`, () => { store.deleteSong(s.id); toast('Usunięto'); go('songs'); }, { danger: true }) }, '🗑'),
  );

  view.append(renderSongReader(s, { withControls: true }));
}

// Renderuje czytelny widok piosenki (nagłówek + tekst z chwytami + diagramy).
function renderSongReader(s, { withControls = false } = {}) {
  const steps = currentSteps(s.id);
  const settings = store.settings;
  const wrap = el('div', { class: 'reader' });

  // nagłówek utworu
  const head = el('div', { class: 'reader-head' },
    el('h2', { class: 'reader-title', text: s.title }),
    el('div', { class: 'reader-sub', text: [s.artist, s.key ? 'tonacja ' + transposeKey(s.key, steps) : '', s.capo ? 'kapo ' + s.capo : '', s.tempo ? s.tempo + ' BPM' : ''].filter(Boolean).join(' · ') }),
  );
  wrap.append(head);

  // Piosenka zapisana w „surowej" formie (chwyty nie nad tekstem)? Zaproponuj naprawę.
  if (withControls) {
    const fix = autoChordify(s.body);
    if (fix.converted) {
      wrap.append(el('div', { class: 'notice notice-warn no-print fix-chords' },
        el('span', {}, '⚠︎ Chwyty nie są ustawione nad tekstem.'),
        el('button', { class: 'btn btn-sm', onClick: () => { store.updateSong(s.id, { body: fix.body }); toast('Ustawiłem chwyty nad tekstem ✓', 'success'); render(); } }, '🎸 Ustaw chwyty nad tekstem'),
      ));
    }
  }

  if (withControls) {
    const showChordsBtn = el('button', { class: 'btn btn-sm', onClick: () => { store.updateSettings({ showChords: !store.settings.showChords }); render(); } }, store.settings.showChords ? '🎸 Chwyty: wł.' : '🎸 Chwyty: wył.');
    const controls = el('div', { class: 'reader-controls no-print' },
      el('div', { class: 'ctrl-group' },
        el('span', { class: 'ctrl-label' }, 'Transpozycja'),
        el('button', { class: 'btn btn-sm', onClick: () => { setTranspose(s.id, currentSteps(s.id) - 1); render(); } }, '−'),
        el('span', { class: 'ctrl-val', text: (steps > 0 ? '+' : '') + steps }),
        el('button', { class: 'btn btn-sm', onClick: () => { setTranspose(s.id, currentSteps(s.id) + 1); render(); } }, '+'),
        el('button', { class: 'btn btn-sm btn-ghost', onClick: () => { setTranspose(s.id, 0); render(); } }, 'reset'),
      ),
      showChordsBtn,
      el('button', { class: 'btn btn-sm', onClick: () => { store.updateSettings({ showDiagrams: !store.settings.showDiagrams }); render(); } }, store.settings.showDiagrams ? '📊 Diagramy: wł.' : '📊 Diagramy: wył.'),
      (() => { const stretched = stretchChords(s.body); return stretched !== s.body ? el('button', { class: 'btn btn-sm', title: 'Rozciągnij chwyty z 1. zwrotki i refrenu na resztę utworu', onClick: () => { store.updateSong(s.id, { body: stretched }); toast('Rozciągnięto chwyty na całość ✓', 'success'); render(); } }, '🔁 Rozciągnij chwyty') : null; })(),
      s.tempo ? el('button', { class: 'btn btn-sm', onClick: (e) => toggleMetronome(e.target, s.tempo) }, '🥁 Metronom') : null,
    );
    wrap.append(controls);
  }

  // diagramy chwytów
  if (settings.showDiagrams && settings.showChords) {
    const chords = extractChords(s.body, steps).filter(hasShape);
    if (chords.length) {
      const dg = el('div', { class: 'diagrams' });
      chords.forEach((c) => { const svg = chordDiagram(c); if (svg) dg.append(el('div', { class: 'diagram', html: svg })); });
      wrap.append(dg);
    }
  }

  // treść
  const body = el('div', { class: 'song-body' + (settings.columns === 2 ? ' two-col' : '') });
  body.innerHTML = renderChordPro(s.body, { steps, showChords: settings.showChords });
  wrap.append(body);

  // taby z osobnego modułu
  if (s.tabs && s.tabs.length) {
    const tabsWrap = el('div', { class: 'tabs-block' }, el('h3', { class: 'block-h' }, '🎸 Tabulatury'));
    s.tabs.forEach((t) => tabsWrap.append(
      el('div', { class: 'tab-item' },
        el('div', { class: 'tab-item-title', text: t.title || 'Tabulatura' }),
        el('pre', { class: 'cp-tab', text: t.content }),
      ),
    ));
    wrap.append(tabsWrap);
  }

  if (s.notes) wrap.append(el('div', { class: 'notes-block' }, el('h3', { class: 'block-h' }, '📝 Notatki'), el('p', { text: s.notes })));

  return wrap;
}

function transposeKey(key, steps) {
  if (!steps || !key) return key;
  return transposeSource('[' + key + ']', steps).replace(/[[\]]/g, '');
}

// ------------------------------------------------------------- Edytor utworu
function renderSongEditor(view, actions, s) {
  const savedTag = el('span', { class: 'saved-tag muted-sm' });
  actions.append(
    el('button', { class: 'btn btn-sm', title: 'Zapisz i pokaż podgląd', onClick: () => save() }, '‹ Gotowe'),
    el('button', { class: 'btn btn-sm', title: 'Cofnij zmianę chwytów', onClick: () => undo() }, '↶ Cofnij'),
    savedTag,
  );

  const f = {};
  const field = (label, node) => el('label', { class: 'field' }, el('span', { class: 'field-label', text: label }), node);

  f.title = el('input', { class: 'input', value: s.title });
  f.artist = el('input', { class: 'input', value: s.artist || '' });
  f.key = el('input', { class: 'input', value: s.key || '', placeholder: 'np. D, Em' });
  f.capo = el('input', { class: 'input', type: 'number', min: '0', max: '12', value: s.capo || 0 });
  f.tempo = el('input', { class: 'input', type: 'number', min: '0', max: '300', value: s.tempo || 0 });
  f.tags = el('input', { class: 'input', value: (s.tags || []).join(', '), placeholder: 'np. ognisko, akustyk' });
  f.notes = el('textarea', { class: 'input', rows: '2' }); f.notes.value = s.notes || '';
  f.body = el('textarea', { class: 'input mono editor-area', rows: '18', spellcheck: 'false' }); f.body.value = s.body || '';

  // podgląd na żywo
  const preview = el('div', { class: 'song-body live-preview' });
  const updatePreview = () => { preview.innerHTML = renderChordPro(autoChordify(f.body.value).body, { showChords: store.settings.showChords }); };
  f.body.addEventListener('input', updatePreview);
  updatePreview();

  // pasek narzędzi edytora ChordPro
  const insert = (before, after = '') => {
    const ta = f.body; const start = ta.selectionStart, end = ta.selectionEnd;
    const sel = ta.value.slice(start, end);
    ta.value = ta.value.slice(0, start) + before + sel + after + ta.value.slice(end);
    ta.focus(); ta.selectionStart = ta.selectionEnd = start + before.length + sel.length + after.length;
    updatePreview();
  };
  const cpToolbar = el('div', { class: 'cp-toolbar' },
    el('button', { class: 'btn btn-xs', type: 'button', title: 'Wstaw chwyt', onClick: () => insert('[', ']') }, '[Chwyt]'),
    el('button', { class: 'btn btn-xs', type: 'button', onClick: () => insert('{comment: ', '}') }, 'Komentarz'),
    el('button', { class: 'btn btn-xs', type: 'button', onClick: () => insert('{start_of_chorus}\n', '\n{end_of_chorus}') }, 'Refren'),
    el('button', { class: 'btn btn-xs', type: 'button', onClick: () => insert('{start_of_tab}\n', '\n{end_of_tab}') }, 'Tabulatura' ),
    el('button', { class: 'btn btn-xs', type: 'button', title: 'Zamień wklejony surowy tekst (chwyty nad tekstem) na format ChordPro', onClick: () => { snapshot(); f.body.value = plainToChordPro(f.body.value); updatePreview(); refreshRight(); autosave(); toast('Skonwertowano do ChordPro'); } }, '✨ Auto-konwersja'),
    el('button', { class: 'btn btn-xs', type: 'button', title: 'Rozciągnij chwyty z 1. zwrotki i refrenu na resztę utworu', onClick: () => { snapshot(); f.body.value = stretchChords(autoChordify(f.body.value).body); updatePreview(); refreshRight(); autosave(); toast('Rozciągnięto chwyty na całość ✓', 'success'); } }, '🔁 Rozciągnij chwyty'),
    el('button', { class: 'btn btn-xs', type: 'button', title: 'Wgraj plik audio i rozłóż wykryte akordy nad tym tekstem', onClick: () => { store.updateSong(s.id, collect()); detectFromFile({ song: s, title: f.title.value }); } }, '🎵 Akordy z pliku'),
  );

  // --- Wizualny edytor chwytów (klik = dodaj/edytuj chwyt nad tekstem) ---
  const arranger = el('div', { class: 'arranger' });
  let activeEdit = null; // { li, pos }
  const buildArranger = () => {
    arranger.innerHTML = '';
    // paleta: najczęstsze chwyty + te już użyte w utworze
    const base = ['C', 'D', 'E', 'F', 'G', 'A', 'Am', 'Em', 'Dm', 'Bm', 'A7', 'E7', 'D7', 'G7'];
    const used = extractChords(f.body.value);
    const palette = [...new Set([...used, ...base])].slice(0, 18);
    const lines = f.body.value.split('\n');
    lines.forEach((line, li) => {
      if (/^\s*\{.*\}\s*$/.test(line) || line.trim() === '') {
        arranger.append(el('div', { class: 'arr-skip', text: line || '·' }));
        return;
      }
      const { plain, chords } = lineToPlain(line);
      const chordAt = (p) => chords.find((c) => c.pos === p);
      const commit = (pos, value) => {
        snapshot();
        const parsed = lineToPlain(f.body.value.split('\n')[li]);
        parsed.chords = parsed.chords.filter((c) => c.pos !== pos);
        if (value.trim()) parsed.chords.push({ pos, chord: value.trim() });
        const newLines = f.body.value.split('\n');
        newLines[li] = plainToLine(parsed.plain, parsed.chords);
        f.body.value = newLines.join('\n');
        activeEdit = null; updatePreview(); buildArranger(); autosave();
      };
      const slot = (pos, ch) => {
        if (activeEdit && activeEdit.li === li && activeEdit.pos === pos) {
          const inp = el('input', { class: 'arr-input', value: ch ? ch.chord : '', spellcheck: 'false' });
          inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); commit(pos, inp.value); } if (e.key === 'Escape') { activeEdit = null; buildArranger(); } });
          inp.addEventListener('blur', () => setTimeout(() => { if (activeEdit && activeEdit.li === li && activeEdit.pos === pos) commit(pos, inp.value); }, 120));
          setTimeout(() => inp.focus(), 0);
          const pal = el('div', { class: 'arr-pal' }, ...palette.map((c) => el('button', { class: 'btn btn-xs', type: 'button', onMousedown: (e) => { e.preventDefault(); commit(pos, c); } }, c)));
          return el('span', { class: 'arr-editing' }, inp, pal);
        }
        return el('span', { class: 'arr-chord' + (ch ? ' has' : ''), onClick: (e) => { e.stopPropagation(); activeEdit = { li, pos }; buildArranger(); } }, ch ? ch.chord : '');
      };
      const lineEl = el('div', { class: 'arr-line' });
      for (let p = 0; p < plain.length; p++) {
        lineEl.append(el('span', { class: 'arr-unit' }, slot(p, chordAt(p)), el('span', { class: 'arr-char', onClick: () => { activeEdit = { li, pos: p }; buildArranger(); } }, plain[p] === ' ' ? ' ' : plain[p])));
      }
      // slot na końcu linii
      lineEl.append(el('span', { class: 'arr-unit' }, slot(plain.length, chordAt(plain.length)), el('span', { class: 'arr-char arr-end', onClick: () => { activeEdit = { li, pos: plain.length }; buildArranger(); } }, ' ')));
      arranger.append(lineEl);
    });
    if (!f.body.value.trim()) arranger.append(el('p', { class: 'muted', text: 'Najpierw wpisz tekst (po lewej), potem klikaj w słowa, żeby dodać chwyty.' }));
  };

  // przełącznik prawej kolumny: Podgląd / Rozmieść chwyty
  let rightMode = 'preview';
  const rightBox = el('div', { class: 'preview-frame' });
  const refreshRight = () => {
    rightBox.innerHTML = '';
    if (rightMode === 'preview') { updatePreview(); rightBox.append(preview); }
    else {
      // wchodząc w edytor chwytów, zamień surowe chwyty na edytowalne [chwyty]
      const c = autoChordify(f.body.value);
      if (c.converted) { f.body.value = c.body; updatePreview(); }
      buildArranger(); rightBox.append(arranger);
    }
  };
  f.body.addEventListener('input', () => { if (rightMode === 'arrange') buildArranger(); });
  refreshRight(); // start w trybie podglądu

  // moduł tabulatur (osobne taby przypięte do utworu)
  let localTabs = structuredClone(s.tabs || []);
  const tabsBox = el('div', { class: 'tabs-editor' });
  const renderTabsEditor = () => {
    tabsBox.innerHTML = '';
    localTabs.forEach((t, i) => {
      const titleI = el('input', { class: 'input', value: t.title, placeholder: 'Nazwa (np. Intro)', oninput: (e) => (localTabs[i].title = e.target.value) });
      const contentI = el('textarea', { class: 'input mono', rows: '6', spellcheck: 'false' });
      contentI.value = t.content; contentI.addEventListener('input', (e) => (localTabs[i].content = e.target.value));
      tabsBox.append(el('div', { class: 'tab-editor-item' },
        el('div', { class: 'tab-editor-head' }, titleI,
          el('button', { class: 'btn btn-xs', type: 'button', title: 'Wstaw pustą 6-strunową siatkę', onClick: () => { localTabs[i].content += (localTabs[i].content ? '\n\n' : '') + tabTemplate(); renderTabsEditor(); } }, 'Siatka'),
          el('button', { class: 'btn btn-xs btn-danger', type: 'button', onClick: () => { localTabs.splice(i, 1); renderTabsEditor(); } }, '🗑')),
        contentI,
      ));
    });
    tabsBox.append(el('button', { class: 'btn btn-sm', type: 'button', onClick: () => { localTabs.push({ id: Date.now().toString(36), title: '', content: tabTemplate() }); renderTabsEditor(); } }, '＋ Dodaj tabulaturę'));
  };
  renderTabsEditor();

  // zbiera bieżące pola do obiektu piosenki (body surowe — bez formatowania)
  function collect(body = f.body.value) {
    return {
      title: f.title.value.trim() || 'Bez tytułu',
      artist: f.artist.value.trim(),
      key: f.key.value.trim(),
      capo: parseInt(f.capo.value) || 0,
      tempo: parseInt(f.tempo.value) || 0,
      tags: f.tags.value.split(',').map((t) => t.trim()).filter(Boolean),
      notes: f.notes.value,
      body,
      tabs: localTabs.filter((t) => t.content.trim()),
    };
  }

  // --- Autozapis (bez klikania „Zapisz") + status ---
  let autosaveTimer = null;
  const showSaved = () => { savedTag.textContent = 'zapisano ✓'; savedTag.classList.add('on'); setTimeout(() => savedTag.classList.remove('on'), 1500); };
  const autosave = () => { savedTag.textContent = 'zapisywanie…'; clearTimeout(autosaveTimer); autosaveTimer = setTimeout(() => { store.updateSong(s.id, collect()); showSaved(); }, 900); };
  [f.title, f.artist, f.key, f.capo, f.tempo, f.tags, f.notes, f.body].forEach((n) => n.addEventListener('input', autosave));

  // --- Undo dla przekształceń chwytów (auto-konwersja, rozciąganie, wizualny edytor) ---
  const history = [];
  function snapshot() { history.push(f.body.value); if (history.length > 60) history.shift(); }
  function undo() {
    if (!history.length) { toast('Nie ma czego cofnąć', 'info'); return; }
    f.body.value = history.pop();
    updatePreview(); refreshRight(); autosave();
  }

  // finalizuj: ustaw chwyty nad tekstem i wyjdź do podglądu
  function save() {
    const { body: bodyVal, converted } = autoChordify(f.body.value);
    store.updateSong(s.id, collect(bodyVal));
    toast(converted ? 'Gotowe — ustawiłem chwyty nad tekstem ✓' : 'Zapisano ✓', 'success');
    app.editing = false;
    render();
  }

  view.append(el('div', { class: 'editor' },
    el('div', { class: 'editor-grid' },
      field('Tytuł', f.title), field('Wykonawca', f.artist),
      field('Tonacja', f.key), field('Kapodaster', f.capo), field('Tempo (BPM)', f.tempo),
      field('Tagi (po przecinku)', f.tags),
    ),
    field('Notatki', f.notes),
    el('div', { class: 'editor-split' },
      el('div', { class: 'editor-col' },
        el('div', { class: 'field-label with-help' }, el('span', {}, 'Tekst z chwytami (format ChordPro)'), el('button', { class: 'link-btn', type: 'button', onClick: chordProHelp }, 'jak pisać?')),
        cpToolbar, f.body,
      ),
      el('div', { class: 'editor-col' },
        el('div', { class: 'field-label with-help' },
          el('span', {}, 'Podgląd / edytor chwytów'),
          (() => {
            const segPrev = el('button', { class: 'btn btn-xs seg-on', type: 'button' }, 'Podgląd');
            const segArr = el('button', { class: 'btn btn-xs', type: 'button' }, '🎯 Rozmieść chwyty');
            const setMode = (m) => { rightMode = m; segPrev.classList.toggle('seg-on', m === 'preview'); segArr.classList.toggle('seg-on', m === 'arrange'); refreshRight(); };
            segPrev.addEventListener('click', () => setMode('preview'));
            segArr.addEventListener('click', () => setMode('arrange'));
            return el('div', { class: 'seg' }, segPrev, segArr);
          })(),
        ),
        rightBox,
      ),
    ),
    el('div', { class: 'field-label mt' }, '🎸 Moduł tabulatur'),
    tabsBox,
  ));
}

function tabTemplate() {
  return 'e|-----------------|\nB|-----------------|\nG|-----------------|\nD|-----------------|\nA|-----------------|\nE|-----------------|';
}

// Pomoc / pierwsze kroki
function helpModal() {
  modal({
    title: '🎵 Śpiewnik — pomoc',
    wide: true,
    body: el('div', { class: 'help' },
      el('h4', {}, '➕ Dodawanie piosenek'),
      el('ul', {},
        el('li', {}, '„＋ Nowa piosenka" — wpisujesz ręcznie.'),
        el('li', {}, '🔎 Wyszukaj — znajdź opracowanie z chwytami w sieci (częściowy tytuł, zespół albo fragment tekstu).'),
        el('li', {}, '💡 Propozycje — 15 polskich i 15 zagranicznych do dodania guzikiem.'),
        el('li', {}, '🕓 Poczekalnia — wklej linki polubionych z TikToka/IG/FB/YT; akceptujesz do biblioteki.'),
      ),
      el('h4', {}, '🎸 Chwyty nad tekstem'),
      el('ul', {},
        el('li', {}, 'Chwyty zapisujesz w nawiasach: ', el('code', {}, '[C]'), ' tuż przed literą, nad którą mają być.'),
        el('li', {}, 'Wklejasz surowy tekst z chwytami (nad tekstem, w tekście, po prawej — też zlepione) → zapisują się nad tekstem automatycznie.'),
        el('li', {}, 'W edytorze: „🎯 Rozmieść chwyty" — klikasz nad literą i wpisujesz chwyt; „🔁 Rozciągnij chwyty" — kopiuje chwyty z 1. zwrotki i refrenu na resztę.'),
      ),
      el('h4', {}, '🎚 Transpozycja i występ'),
      el('ul', {},
        el('li', {}, 'Transpozycja (− / +) zapisuje się przy piosence — działa też z poziomu list.'),
        el('li', {}, '▶︎ Występ — pełny ekran, ekran nie gaśnie, A− / A+ i auto‑scroll.'),
      ),
      el('h4', {}, '☁︎ Synchronizacja'),
      el('p', {}, 'W wersji z serwerem wszystko synchronizuje się między urządzeniami. Zapisz swój link (Wygląd → „Kopiuj mój link"), by wchodzić bez wpisywania tokenu.'),
    ),
    actions: [el('button', { class: 'btn btn-primary', onClick: () => document.querySelector('.modal-overlay')?.remove() }, 'OK')],
  });
}

function welcomeModal() {
  const m = modal({
    title: '👋 Witaj w Śpiewniku!',
    body: el('div', {},
      el('p', { text: 'Twój śpiewnik na każde urządzenie: listy piosenek, teksty z chwytami, tabulatury i wyszukiwarka. Od czego zaczniesz?' }),
      el('div', { class: 'welcome-actions' },
        el('button', { class: 'btn btn-primary btn-block', onClick: () => { m.close(); newSong(); } }, '＋ Dodaj pierwszą piosenkę'),
        el('button', { class: 'btn btn-block', onClick: () => { m.close(); go('search'); } }, '🔎 Znajdź piosenkę z chwytami'),
        el('button', { class: 'btn btn-block', onClick: () => { m.close(); go('suggest'); } }, '💡 Zobacz propozycje (15+15)'),
        el('button', { class: 'btn btn-ghost btn-block', onClick: () => { m.close(); helpModal(); } }, '❓ Jak to działa?'),
      ),
    ),
    onClose: () => store.updateSettings({ seenWelcome: true }),
  });
}

// Wyjaśnia, że moduł wykrywania akordów z audio jest opcjonalny + jak go włączyć.
function audioModuleInfo() {
  const cmd = 'cd /root/gie-d && touch songbook/deploy/audio.enabled && ./deploy/deploy.sh';
  modal({
    title: '🎧 Wykrywanie akordów z audio',
    wide: true,
    body: el('div', { class: 'help' },
      el('p', {}, 'Ten moduł potrafi „posłuchać" nagrania z YouTube i wykryć przybliżoną progresję akordów. Jest ', el('b', {}, 'opcjonalny i wyłączony'), ' — bo jest ciężki (analiza dźwięku) i ma haczyki:'),
      el('ul', {},
        el('li', {}, 'Wynik jest ', el('b', {}, 'przybliżony'), ' (~70–85% na prostym popie) — punkt startowy do poprawki w edytorze.'),
        el('li', {}, 'Pobieranie audio z YouTube bywa niezgodne z regulaminem serwisu — do prywatnego użytku, na własną odpowiedzialność.'),
      ),
      el('p', {}, 'Aby włączyć, uruchom raz na serwerze:'),
      el('pre', {}, cmd),
      el('p', { class: 'muted' }, 'Pierwszy build potrwa (librosa + ffmpeg). Potem przycisk „🎧 Akordy z YT" zacznie działać przy linkach z YouTube.'),
    ),
    actions: [
      el('button', { class: 'btn', onClick: () => { copyText(cmd); toast('Skopiowano komendę'); } }, '📋 Kopiuj komendę'),
      el('button', { class: 'btn btn-primary', onClick: () => document.querySelector('.modal-overlay')?.remove() }, 'OK'),
    ],
  });
}

function chordProHelp() {
  modal({
    title: 'Jak pisać teksty z chwytami (ChordPro)',
    wide: true,
    body: el('div', { class: 'help', html: `
      <p>Chwyty umieszczasz w <b>nawiasach kwadratowych</b> dokładnie tam, gdzie w słowie ma się zmienić akord:</p>
      <pre>[C]Panie mój, [G]dobry mój, [Am]bądź ze [F]mną</pre>
      <p>Dyrektywy w nawiasach klamrowych porządkują utwór:</p>
      <ul>
        <li><code>{comment: Zwrotka 1}</code> — etykieta / komentarz</li>
        <li><code>{start_of_chorus}</code> … <code>{end_of_chorus}</code> — refren (wyróżniony)</li>
        <li><code>{start_of_tab}</code> … <code>{end_of_tab}</code> — blok tabulatury (czcionka stała)</li>
      </ul>
      <p>Masz surowy tekst z chwytami w osobnych liniach nad słowami? Wklej go i użyj
      przycisku <b>✨ Auto-konwersja</b> — aplikacja sama poprzesuwa chwyty do nawiasów.</p>
      <p>„H” zostanie potraktowane jak „B” (zapis polski/niemiecki).</p>
    ` }),
    actions: [],
  });
}

// ------------------------------------------------------------------ Listy
function renderLists(view, actions) {
  $('#viewTitle').textContent = 'Listy';
  actions.append(el('button', { class: 'btn btn-primary', onClick: () => { const l = store.createList(); go('lists', { listId: l.id }); } }, '＋ Nowa lista'));
  const lists = store.lists();
  if (!lists.length) {
    view.append(el('div', { class: 'empty' }, el('div', { class: 'empty-emoji' }, '📋'), el('p', {}, 'Nie masz jeszcze list. Twórz setlisty na koncerty, próby albo ognisko.'), el('button', { class: 'btn btn-primary', onClick: () => { const l = store.createList(); go('lists', { listId: l.id }); } }, '＋ Nowa lista')));
    return;
  }
  const grid = el('div', { class: 'card-grid' });
  for (const l of lists) {
    grid.append(el('div', { class: 'list-card', onClick: () => go('lists', { listId: l.id }) },
      el('div', { class: 'list-card-icon' }, '📋'),
      el('div', { class: 'list-card-main' },
        el('div', { class: 'list-title', text: l.name }),
        el('div', { class: 'muted-sm', text: (l.description || '') }),
        el('div', { class: 'muted-sm', text: `${l.songIds.length} ${plural(l.songIds.length, 'piosenka', 'piosenki', 'piosenek')}` }),
      ),
      el('span', { class: 'chev' }, '›'),
    ));
  }
  view.append(grid);
}

function plural(n, one, few, many) {
  if (n === 1) return one;
  if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) return few;
  return many;
}

function renderListDetail(view, actions) {
  const l = store.list(app.listId);
  if (!l) { app.listId = null; return renderLists(view, actions); }
  $('#viewTitle').textContent = l.name;
  actions.append(
    el('button', { class: 'btn btn-sm', onClick: () => go('lists') }, '‹ Wróć'),
    l.songIds.length ? el('button', { class: 'btn btn-sm', onClick: () => openPerformance(l.songIds[0], l.id) }, '▶︎ Odtwórz listę') : null,
    el('button', { class: 'btn btn-sm', onClick: () => window.print() }, '🖨 Drukuj'),
    el('button', { class: 'btn btn-sm btn-danger', onClick: () => confirmDialog(`Usunąć listę „${l.name}”?`, () => { store.deleteList(l.id); go('lists'); }, { danger: true }) }, '🗑'),
  );

  const nameI = el('input', { class: 'input title-input', value: l.name, onchange: (e) => { store.updateList(l.id, { name: e.target.value }); $('#viewTitle').textContent = e.target.value; } });
  const descI = el('input', { class: 'input', value: l.description || '', placeholder: 'Opis listy (opcjonalnie)', onchange: (e) => store.updateList(l.id, { description: e.target.value }) });

  const listBox = el('div', { class: 'setlist' });
  const renderItems = () => {
    listBox.innerHTML = '';
    if (!l.songIds.length) { listBox.append(el('p', { class: 'muted', text: 'Lista jest pusta — dodaj piosenki poniżej.' })); return; }
    l.songIds.forEach((sid, idx) => {
      const s = store.song(sid);
      if (!s) return;
      const tr = currentSteps(s.id);
      const item = el('div', { class: 'setlist-item', draggable: 'true' },
        el('span', { class: 'drag', title: 'Przeciągnij, aby zmienić kolejność' }, '⠿'),
        el('span', { class: 'setlist-num', text: (idx + 1) + '.' }),
        el('span', { class: 'setlist-main', onClick: () => go('songs', { songId: s.id }) },
          el('span', { class: 'setlist-title', text: s.title }), el('span', { class: 'setlist-artist', text: s.artist || '' })),
        s.key ? el('span', { class: 'pill', title: tr ? 'tonacja po transpozycji' : 'tonacja' }, (tr ? transposeKey(s.key, tr) : s.key)) : null,
        el('span', { class: 'setlist-tr', title: 'Transpozycja chwytów (zapisywana)' },
          el('button', { class: 'btn btn-xs', title: 'Chwyty niżej', onClick: (e) => { e.stopPropagation(); setTranspose(s.id, currentSteps(s.id) - 1); renderItems(); } }, '♭'),
          el('span', { class: 'tr-val', text: (tr > 0 ? '+' : '') + tr }),
          el('button', { class: 'btn btn-xs', title: 'Chwyty wyżej', onClick: (e) => { e.stopPropagation(); setTranspose(s.id, currentSteps(s.id) + 1); renderItems(); } }, '♯'),
        ),
        el('button', { class: 'btn btn-xs', title: 'W górę', onClick: () => { store.reorderList(l.id, idx, idx - 1); renderItems(); } }, '↑'),
        el('button', { class: 'btn btn-xs', title: 'W dół', onClick: () => { store.reorderList(l.id, idx, idx + 1); renderItems(); } }, '↓'),
        el('button', { class: 'btn btn-xs btn-danger', onClick: () => { store.removeFromList(l.id, sid); renderItems(); } }, '✕'),
      );
      // drag & drop
      item.addEventListener('dragstart', (e) => { e.dataTransfer.setData('text/plain', idx); item.classList.add('dragging'); });
      item.addEventListener('dragend', () => item.classList.remove('dragging'));
      item.addEventListener('dragover', (e) => e.preventDefault());
      item.addEventListener('drop', (e) => { e.preventDefault(); const from = parseInt(e.dataTransfer.getData('text/plain')); store.reorderList(l.id, from, idx); renderItems(); });
      listBox.append(item);
    });
  };
  renderItems();

  // dodawanie piosenek
  const available = store.songs().filter((s) => !l.songIds.includes(s.id));
  const addSelect = el('select', { class: 'input' },
    el('option', { value: '' }, '— wybierz piosenkę —'),
    ...available.map((s) => el('option', { value: s.id }, `${s.title} — ${s.artist || '?'}`)),
  );
  const addRow = el('div', { class: 'add-row' }, addSelect,
    el('button', { class: 'btn btn-primary', onClick: () => { if (addSelect.value) { store.addToList(l.id, addSelect.value); render(); } } }, '＋ Dodaj'),
    el('button', { class: 'btn', onClick: () => newSongIntoList(l.id) }, '＋ Nowa piosenka'),
  );

  view.append(el('div', { class: 'list-detail' },
    el('div', { class: 'list-meta' }, nameI, descI),
    el('h3', { class: 'block-h' }, 'Kolejność występu'),
    listBox,
    el('h3', { class: 'block-h mt' }, 'Dodaj do listy'),
    addRow,
  ));
}

function newSongIntoList(listId) {
  const s = store.createSong();
  store.addToList(listId, s.id);
  go('songs', { songId: s.id, editing: true });
}

function addToListDialog(songId) {
  const lists = store.lists();
  const body = el('div', {});
  if (!lists.length) body.append(el('p', { text: 'Nie masz jeszcze żadnej listy.' }));
  lists.forEach((l) => {
    const inList = l.songIds.includes(songId);
    body.append(el('label', { class: 'check-row' },
      el('input', { type: 'checkbox', ...(inList ? { checked: true } : {}), onchange: (e) => { e.target.checked ? store.addToList(l.id, songId) : store.removeFromList(l.id, songId); } }),
      el('span', { text: l.name }),
    ));
  });
  const nameNew = el('input', { class: 'input', placeholder: 'Nazwa nowej listy' });
  body.append(el('div', { class: 'add-row mt' }, nameNew, el('button', { class: 'btn', onClick: () => { if (nameNew.value.trim()) { const l = store.createList(nameNew.value.trim()); store.addToList(l.id, songId); toast('Dodano do „' + l.name + '”'); m.close(); } } }, '＋ Utwórz i dodaj')));
  const m = modal({ title: 'Dodaj do listy', body, actions: [el('button', { class: 'btn btn-primary', onClick: () => m.close() }, 'Gotowe')] });
}

// ------------------------------------------------------------------ Wyszukaj
// ------------------------------------------------------------------ Poczekalnia
function updateInboxBadge() {
  const b = $('#inboxBadge'); if (!b) return;
  const n = store.inbox().length;
  b.textContent = n; b.hidden = n === 0;
}

// ---------------------------------------------- wykrywanie akordów z audio

// Wstawia N akordów w linię tekstu, równomiernie nad słowami (jak w chordpro).
function placeOverLine(lyric, chords) {
  if (!chords.length) return lyric;
  const parts = lyric.split(/(\s+)/);
  const wordPos = [];
  parts.forEach((p, i) => { if (p.trim()) wordPos.push(i); });
  if (!wordPos.length) return lyric;
  const out = [...parts];
  chords.forEach((c, k) => {
    const wp = Math.min(wordPos.length - 1, Math.round((k * wordPos.length) / chords.length));
    out[wordPos[wp]] = `[${c}]` + out[wordPos[wp]];
  });
  return out.join('');
}

// Rozkłada wykrytą sekwencję akordów NAD istniejącym tekstem (proporcjonalnie
// do liczby wersów, max ~4 akordy na linię). Zwraca tekst ChordPro.
function overlayDetectedOnLyrics(lyrics, seq) {
  const lines = lyrics.replace(/\r/g, '').split('\n');
  const idx = [];
  lines.forEach((ln, i) => {
    const t = ln.trim();
    if (t && !/^\{.*\}$/.test(t) && !/^\[[^\]]*\]$/.test(t)) idx.push(i);
  });
  if (!idx.length || !seq.length) return null;
  const per = Math.max(1, Math.min(4, Math.round(seq.length / idx.length)));
  let cur = 0;
  idx.forEach((li, n) => {
    // ostatniej linii oddaj resztę, by nie zgubić akordów
    const take = (n === idx.length - 1) ? Math.max(per, seq.length - cur) : per;
    const slice = seq.slice(cur, cur + take);
    cur += take;
    if (slice.length) lines[li] = placeOverLine(lines[li], slice);
  });
  return lines.join('\n');
}

// Ma piosenka realny tekst (nie same akordy/dyrektywy)?
function songHasLyrics(song) {
  if (!song || !song.body) return false;
  return song.body.replace(/\r/g, '').split('\n').some((ln) => {
    const t = ln.replace(/\[[^\]]*\]/g, '').trim();
    return t && !/^\{.*\}$/.test(t);
  });
}

// Wspólne: z wyniku detekcji buduje/uzupełnia piosenkę i otwiera edytor.
function applyDetected(res, meta) {
  if (!res.chords.length) { toast('Nie wykryto wyraźnych akordów w tym nagraniu.', 'error'); return; }
  const seq = res.chords.map((c) => c.chord);
  // Świeży stan piosenki (edytor mógł właśnie zapisać nowy tekst).
  const song = meta.song ? (store.song(meta.song.id) || meta.song) : null;

  // Jeśli mamy piosenkę z gotowym tekstem — rozłóż akordy NAD tym tekstem.
  if (song && songHasLyrics(song)) {
    const overlaid = overlayDetectedOnLyrics(song.body, seq);
    if (overlaid) {
      const head = `{comment: Akordy z audio — PRZYBLIŻONE, popraw rozmieszczenie}\n`;
      const body = /\{comment: Akordy z audio/.test(song.body) ? overlaid : head + overlaid;
      store.updateSong(song.id, { body, tempo: song.tempo || res.tempo || 0 });
      if (meta.inboxId) { store.removeInbox(meta.inboxId); updateInboxBadge(); }
      toast('Rozłożono wykryte akordy nad tekstem — sprawdź i popraw ✓', 'success');
      go('songs', { songId: song.id, editing: true });
      return;
    }
  }

  // Brak tekstu: zapisz akordy w osobnych liniach (punkt startowy).
  const lines = [];
  for (let i = 0; i < seq.length; i += 8) lines.push(seq.slice(i, i + 8).map((c) => `[${c}]`).join(' '));
  const body = `{comment: Akordy wykryte z audio — PRZYBLIŻONE, dopasuj do tekstu}\n{comment: Użyte akordy: ${res.unique.join(' ')}}\n\n${lines.join('\n')}`;
  if (song) {
    store.updateSong(song.id, { body, tempo: song.tempo || res.tempo || 0 });
    if (meta.inboxId) { store.removeInbox(meta.inboxId); updateInboxBadge(); }
    toast('Wykryto akordy — dodaj tekst i rozmieść chwyty ✓', 'success');
    go('songs', { songId: song.id, editing: true });
    return;
  }
  const s = store.createSong({ title: meta.title || 'Wykryte z audio', artist: meta.artist || '', tempo: res.tempo || 0, tags: ['z audio'], notes: meta.notes || '', body });
  if (meta.inboxId) { store.removeInbox(meta.inboxId); updateInboxBadge(); }
  toast('Wykryto akordy — dodaj tekst i rozmieść chwyty ✓', 'success');
  go('songs', { songId: s.id, editing: true });
}

function detectError(err) {
  const botCheck = /not a bot|Sign in|cookies/i.test(err || '');
  modal({
    title: '🎧 Nie udało się wykryć akordów',
    wide: true,
    body: el('div', { class: 'help' },
      el('p', {}, 'Powód:'), el('pre', {}, err || 'nieznany'),
      botCheck
        ? el('p', {}, el('b', {}, 'YouTube blokuje pobieranie z serwera. '), 'Najpewniejsza droga bez YouTube: kliknij ', el('b', {}, '„🎵 Z pliku audio"'), ' i wgraj mp3/m4a utworu. Analiza pójdzie lokalnie, bez bot-checku.')
        : el('p', { class: 'muted' }, 'Najczęstsze przyczyny: moduł audio nie jest włączony na serwerze, pierwszy build jeszcze trwa, albo YouTube ograniczył pobieranie. Sprawdź też /api/config (pole „audio"). Zawsze możesz wgrać plik audio przyciskiem „🎵 Z pliku audio".'),
    ),
    actions: [el('button', { class: 'btn btn-primary', onClick: () => document.querySelector('.modal-overlay')?.remove() }, 'OK')],
  });
}

async function detectFromYT(it, btn) {
  const old = btn.textContent; btn.disabled = true; btn.textContent = '🎧 Analizuję… (to potrwa)';
  const res = await detectChords(it.url);
  btn.disabled = false; btn.textContent = old;
  if (!res.ok) { detectError(res.error); return; }
  applyDetected(res, { title: it.title || 'Wykryte z YT', artist: it.author || '', notes: 'Źródło: ' + it.url, inboxId: it.id });
}

// Wykrywanie z WGRANEGO pliku audio — pewna droga, omija YouTube i bot-check.
function detectFromFile(meta) {
  if (!sync.audioAvailable()) { audioModuleInfo(); return; }
  const inp = el('input', { type: 'file', accept: 'audio/*,.mp3,.m4a,.wav,.ogg,.flac,.aac,.opus', style: 'display:none' });
  inp.addEventListener('change', async () => {
    const file = inp.files && inp.files[0];
    if (!file) return;
    modal({
      title: '🎧 Analizuję plik…',
      body: el('div', { class: 'help' },
        el('p', {}, 'Trwa analiza „', el('b', {}, file.name), '". To może potrwać kilkadziesiąt sekund — nie zamykaj tej karty.'),
      ),
      actions: [],
    });
    const res = await detectChordsFile(file);
    document.querySelector('.modal-overlay')?.remove();
    if (!res.ok) { detectError(res.error); return; }
    applyDetected(res, {
      title: meta.title || file.name.replace(/\.[^.]+$/, ''),
      artist: meta.artist || '', notes: meta.notes || ('Plik: ' + file.name),
      inboxId: meta.inboxId, song: meta.song,
    });
  });
  document.body.append(inp); inp.click();
  setTimeout(() => inp.remove(), 60000);
}

// Rozdziela tytuł filmu na wykonawcę i tytuł oraz sprząta śmieci („(Official Video)" itd.)
function parseTrack(rawTitle, author) {
  let t = (rawTitle || '').replace(/\s+/g, ' ').trim();
  t = t.replace(/\((?:official|lyric|audio|video|teledysk|prod\.?|hd|4k)[^)]*\)/gi, '')
       .replace(/\[[^\]]*\]/g, '')
       .replace(/(official (music )?video|lyric video|audio|teledysk|visualizer)/gi, '')
       .replace(/\s+/g, ' ').trim();
  let artist = author ? author.replace(/\s*-\s*Topic$/i, '').trim() : '';
  let title = t;
  const m = t.match(/^(.{1,60}?)\s*[-–—]\s*(.+)$/); // „Wykonawca - Tytuł"
  if (m) { artist = m[1].trim(); title = m[2].trim(); }
  title = title.replace(/["'|]+$/,'').trim();
  return { artist, title: title || t || 'Nowa piosenka' };
}

function renderInbox(view, actions) {
  $('#viewTitle').textContent = 'Poczekalnia';
  if (store.inbox().length) {
    actions.append(el('button', { class: 'btn btn-sm btn-danger', onClick: () => confirmDialog('Wyczyścić całą poczekalnię?', () => { store.clearInbox(); render(); }, { danger: true }) }, 'Wyczyść'));
  }

  const linksArea = el('textarea', { class: 'input mono', rows: '3', placeholder: 'Wklej link(i) z TikToka / Instagrama / Facebooka / YouTube — po jednym w linii. „Udostępnij → Kopiuj link".' });
  const box = el('div', { class: 'search-box' },
    el('p', { class: 'search-intro' }, 'Wrzucaj tu polubione utwory z social mediów. Wklej linki (Udostępnij → Kopiuj link), a aplikacja rozpozna tytuł i doda do kolejki „do akceptacji". ',
      el('span', {}, 'Przy linkach z YouTube możesz też '),
      el('a', { class: 'link-btn', href: '#', onClick: (e) => { e.preventDefault(); audioModuleInfo(); } }, '🎧 wykryć akordy z dźwięku'),
      el('span', {}, '.')),
    linksArea,
    el('div', { class: 'search-fields' },
      el('button', { class: 'btn btn-primary', onClick: addLinks }, '⬇︎ Dodaj do poczekalni'),
      el('button', { class: 'btn', title: 'Wgraj plik audio (mp3/m4a) i wykryj akordy — pewna droga bez YouTube', onClick: () => detectFromFile({}) }, '🎵 Akordy z pliku audio'),
    ),
  );

  async function addLinks() {
    const urls = linksArea.value.split(/\s+/).map((s) => s.trim()).filter((s) => /^https?:\/\//i.test(s));
    if (!urls.length) { toast('Wklej przynajmniej jeden link (http…)', 'error'); return; }
    linksArea.value = '';
    let added = 0;
    for (const url of urls) {
      const stub = store.addInbox({ url, source: (() => { try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return ''; } })(), title: '' });
      if (stub) { added++; updateInboxBadge(); renderList(); resolveInto(stub); }
    }
    toast(added ? `Dodano ${added} do poczekalni` : 'Już były w poczekalni', added ? 'success' : 'info');
    renderList();
  }
  async function resolveInto(stub) {
    const r = await resolveLink(stub.url);
    if (r.ok && (r.title || r.author)) {
      const p = parseTrack(r.title, r.author);
      store.updateInbox(stub.id, { title: p.title, author: p.artist });
    }
    renderList();
  }

  const listWrap = el('div', { class: 'inbox-list' });
  function renderList() {
    listWrap.innerHTML = '';
    const items = store.inbox();
    if (!items.length) { listWrap.append(el('div', { class: 'empty' }, el('div', { class: 'empty-emoji' }, '🕓'), el('p', {}, 'Poczekalnia jest pusta. Wklej linki powyżej.'))); return; }
    items.forEach((it) => {
      const titleI = el('input', { class: 'input', value: it.title || '', placeholder: 'Tytuł', oninput: (e) => { store.updateInbox(it.id, { title: e.target.value }); } });
      const artistI = el('input', { class: 'input', value: it.author || '', placeholder: 'Wykonawca', oninput: (e) => { store.updateInbox(it.id, { author: e.target.value }); } });
      const accept = (search) => {
        const s = store.createSong({ title: (it.title || '').trim() || 'Nowa piosenka', artist: (it.author || '').trim(), tags: ['z social'], notes: 'Źródło: ' + it.url });
        store.removeInbox(it.id); updateInboxBadge();
        toast('Zaakceptowano ✓', 'success');
        if (search) { app.pendingSearch = { q: s.title, artist: s.artist }; go('search'); }
        else { go('songs', { songId: s.id }); }
      };
      listWrap.append(el('div', { class: 'inbox-item' },
        el('div', { class: 'inbox-main' },
          el('div', { class: 'inbox-fields' }, titleI, artistI),
          el('div', { class: 'inbox-meta' },
            it.source ? el('span', { class: 'result-source', text: it.source }) : el('span', { class: 'result-source' }, '…'),
            el('a', { class: 'inbox-link', href: it.url, target: '_blank', rel: 'noopener', text: it.url }),
          ),
        ),
        el('div', { class: 'inbox-actions' },
          el('button', { class: 'btn btn-sm btn-primary', onClick: () => accept(false) }, '✓ Akceptuj'),
          el('button', { class: 'btn btn-sm', title: 'Akceptuj i znajdź chwyty', onClick: () => accept(true) }, '🔎 + chwyty'),
          /youtu/.test(it.url) ? el('button', { class: 'btn btn-sm', title: 'Wykryj akordy z audio (przybliżone)', onClick: (e) => (sync.audioAvailable() ? detectFromYT(it, e.target) : audioModuleInfo()) }, '🎧 Akordy z YT') : null,
          el('button', { class: 'btn btn-sm', title: 'Wgraj plik audio (mp3/m4a) i wykryj akordy — bez YouTube', onClick: () => detectFromFile({ title: it.title, artist: it.author, inboxId: it.id, notes: 'Źródło: ' + it.url }) }, '🎵 Z pliku'),
          el('button', { class: 'btn btn-sm btn-danger', onClick: () => { store.removeInbox(it.id); updateInboxBadge(); renderList(); } }, '✕'),
        ),
      ));
    });
  }
  renderList();

  view.append(box, listWrap);
}

// ------------------------------------------------------------------ Propozycje
const normKey = (t, a) => (String(t) + '|' + String(a)).toLowerCase().replace(/\s+/g, ' ').trim();

function renderSuggestions(view, actions) {
  $('#viewTitle').textContent = 'Propozycje';

  // co już mam + profil gustu (wykonawcy i tagi z biblioteki)
  const have = new Set(store.songs().map((s) => normKey(s.title, s.artist)));
  const myArtists = new Set(store.songs().map((s) => (s.artist || '').toLowerCase()).filter(Boolean));
  const myTags = new Set(store.songs().flatMap((s) => (s.tags || []).map((t) => t.toLowerCase())));
  const score = (it) => (myArtists.has((it.artist || '').toLowerCase()) ? 2 : 0) + (it.tags || []).reduce((n, t) => n + (myTags.has(t.toLowerCase()) ? 1 : 0), 0);

  const goSearch = (it) => { app.pendingSearch = { q: it.title, artist: it.artist === 'trad.' ? '' : it.artist }; go('search'); };

  const card = (it) => {
    const added = have.has(normKey(it.title, it.artist));
    const matched = score(it) > 0;
    const addBtn = added
      ? el('span', { class: 'pill pill-ok' }, '✓ w bibliotece')
      : el('button', { class: 'btn btn-sm btn-primary', onClick: (e) => {
          const s = store.createSong({ title: it.title, artist: it.artist, key: it.key || '', capo: it.capo || 0, tempo: it.tempo || 0, tags: it.tags || [] });
          toast('Dodano „' + it.title + '" ✓', 'success');
          e.target.replaceWith(el('span', { class: 'pill pill-ok' }, '✓ dodano'));
          void s;
        } }, '＋ Dodaj');
    return el('div', { class: 'suggest-card' },
      el('div', { class: 'suggest-main' },
        el('div', { class: 'suggest-title' }, it.title, matched ? el('span', { class: 'match-badge', title: 'pasuje do Twojej biblioteki' }, '★') : null),
        el('div', { class: 'suggest-artist', text: it.artist }),
        el('div', { class: 'song-meta' },
          it.key ? el('span', { class: 'pill' }, '🎹 ' + it.key) : null,
          it.capo ? el('span', { class: 'pill' }, 'kapo ' + it.capo) : null,
          it.tempo ? el('span', { class: 'pill' }, '⏱ ' + it.tempo) : null,
          ...(it.tags || []).slice(0, 3).map((t) => el('span', { class: 'pill pill-tag' }, '#' + t)),
        ),
      ),
      el('div', { class: 'suggest-actions' },
        addBtn,
        el('button', { class: 'btn btn-sm', title: 'Znajdź chwyty', onClick: () => goSearch(it) }, '🔎 Chwyty'),
      ),
    );
  };

  const section = (heading, items) => {
    const sorted = [...items].sort((a, b) => score(b) - score(a));
    const grid = el('div', { class: 'suggest-grid' });
    sorted.forEach((it) => grid.append(card(it)));
    return el('div', { class: 'suggest-section' }, el('h3', { class: 'block-h' }, heading), grid);
  };

  view.append(
    el('p', { class: 'search-intro', text: 'Gotowe propozycje do dodania jednym kliknięciem. ★ oznacza pozycje pasujące do Twojej biblioteki. „＋ Dodaj" tworzy piosenkę (tytuł, tonacja, tempo), a „🔎 Chwyty" od razu ją wyszukuje.' }),
    section('🇵🇱 Polskie (15)', SUGGEST_PL),
    section('🌍 Zagraniczne (15)', SUGGEST_WORLD),
  );
}

function renderSearch(view, actions) {
  $('#viewTitle').textContent = 'Wyszukaj';
  const q = el('input', { class: 'input', placeholder: 'Tytuł, zespół lub fragment tekstu — np. „hej sokoły", „dżem naboso", „przyjaciół nikt…"' });
  const artist = el('input', { class: 'input', placeholder: 'Zespół / wykonawca (opcjonalnie)' });
  const result = el('div', { class: 'search-result' });

  const chordsCount = (body) => (body.match(/\[[A-Ha-h][^\]]*\]/g) || []).length;

  // Wybór konkretnego wyniku → pobranie i sformatowanie pod śpiewnik.
  const pickResult = async (item) => {
    result.innerHTML = '';
    result.append(el('div', { class: 'searching' }, el('span', { class: 'spinner' }), ` Pobieram z ${item.source}…`));
    const res = await importUrl(item.url);
    result.innerHTML = '';
    const back = el('button', { class: 'btn btn-sm', onClick: doSearch }, '‹ Wróć do wyników');
    if (!res.ok) { result.append(back, el('div', { class: 'notice notice-warn', text: '⚠︎ ' + res.error })); return; }
    const body = plainToChordPro(res.text);
    const n = chordsCount(body);
    const note = n >= 3
      ? `Znaleziono opracowanie z chwytami (${n}) ze strony ${item.source}. Sprawdź i popraw, potem zapisz.`
      : `To źródło (${item.source}) ma mało/zero chwytów — może to sam tekst. Wróć i wybierz inny wynik albo dodaj chwyty ręcznie.`;
    result.append(el('div', { class: 'result-actions-top' }, back, el('a', { class: 'btn btn-sm', href: item.url, target: '_blank', rel: 'noopener' }, '↗ Otwórz źródło')));
    showFoundText(result, artist.value.trim(), title(item), body, note);
  };

  const title = (item) => q.value.trim() && !artist.value.trim() ? q.value.trim() : (item.title || q.value.trim());

  const doSearch = async () => {
    if (!q.value.trim() && !artist.value.trim()) { toast('Wpisz choć tytuł, zespół albo fragment tekstu', 'error'); return; }
    result.innerHTML = '';
    result.append(el('div', { class: 'searching' }, el('span', { class: 'spinner' }), ' Szukam opracowań z chwytami…'));
    const res = await searchWeb({ q: q.value.trim(), artist: artist.value.trim() });
    result.innerHTML = '';
    if (!res.ok) { result.append(el('div', { class: 'notice notice-warn', text: '⚠︎ ' + res.error }), el('p', { class: 'muted', text: 'Możesz też wkleić link do strony z chwytami lub tekst ręcznie (niżej).' })); return; }
    if (!res.items.length) { result.append(el('div', { class: 'notice notice-warn', text: 'Brak wyników. Spróbuj innych słów albo dodaj „chwyty".' })); return; }
    result.append(el('div', { class: 'muted-sm mb', text: `Wybierz opracowanie (${res.items.length}) — kliknij, żeby pobrać i sformatować:` }));
    const list = el('div', { class: 'result-list' });
    res.items.forEach((item) => {
      list.append(el('button', { class: 'result-card', onClick: () => pickResult(item) },
        el('div', { class: 'result-main' },
          el('div', { class: 'result-title', text: item.title || item.url }),
          item.snippet ? el('div', { class: 'result-snippet', text: item.snippet }) : null,
        ),
        el('span', { class: 'result-source', text: item.source }),
      ));
    });
    result.append(list);
  };
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

  const box = el('div', { class: 'search-box' },
    el('p', { class: 'search-intro', text: 'Szukaj opracowań z chwytami w sieci. Działa po częściowym tytule, nazwie zespołu (albo bez niej) lub po fragmencie tekstu. Polskie znaki są OK. Dostaniesz listę wersji do wyboru.' }),
    el('div', { class: 'search-fields' }, q),
    el('div', { class: 'search-fields' }, artist, el('button', { class: 'btn btn-primary', onClick: doSearch }, '🔎 Szukaj z chwytami')),
    result,
  );

  // import chwytów/tabów po URL
  const urlInput = el('input', { class: 'input', placeholder: 'https://… (konkretna strona z chwytami lub tabami)' });
  const importResult = el('div', { class: 'search-result' });
  const doImport = async () => {
    if (!urlInput.value.trim()) { toast('Wklej adres URL', 'error'); return; }
    importResult.innerHTML = '';
    importResult.append(el('div', { class: 'searching' }, el('span', { class: 'spinner' }), ' Pobieram i formatuję…'));
    const res = await importUrl(urlInput.value.trim());
    importResult.innerHTML = '';
    if (!res.ok) { importResult.append(el('div', { class: 'notice notice-warn', text: '⚠︎ ' + res.error })); return; }
    const converted = plainToChordPro(res.text);
    showFoundText(importResult, artist.value.trim(), q.value.trim(), converted, 'Zaimportowano i wykryto chwyty. Sprawdź i popraw ustawienie chwytów, potem zapisz.');
  };
  const importBox = el('div', { class: 'search-box' },
    el('h3', { class: 'block-h' }, '🎸 Mam już konkretny link'),
    el('p', { class: 'search-intro', text: 'Wklej link do strony z chwytami lub tabulaturą — aplikacja pobierze treść, oczyści z HTML i wykryje chwyty nad tekstem.' }),
    el('div', { class: 'search-fields' }, urlInput, el('button', { class: 'btn btn-primary', onClick: doImport }, '⬇︎ Importuj')),
    importResult,
  );

  // wklej ręcznie
  const pasteArea = el('textarea', { class: 'input mono', rows: '8', placeholder: 'Wklej tu surowy tekst z chwytami (chwyty w osobnych liniach nad słowami)…' });
  const pasteBox = el('div', { class: 'search-box' },
    el('h3', { class: 'block-h' }, '📋 Wklej tekst ręcznie'),
    el('p', { class: 'search-intro', text: 'Skopiuj tekst z dowolnego źródła i wklej tutaj. Auto-konwersja przełoży chwyty do formatu ChordPro.' }),
    pasteArea,
    el('button', { class: 'btn btn-primary', onClick: () => { if (!pasteArea.value.trim()) { toast('Najpierw wklej tekst', 'error'); return; } showFoundText(pasteBox, artist.value.trim(), q.value.trim(), plainToChordPro(pasteArea.value), 'Skonwertowano wklejony tekst.'); } }, '✨ Konwertuj i podejrzyj'),
  );

  view.append(box, importBox, pasteBox);

  // wejście z „Propozycji" (🔎 Chwyty) — wypełnij i od razu szukaj
  if (app.pendingSearch) {
    q.value = app.pendingSearch.q || '';
    artist.value = app.pendingSearch.artist || '';
    app.pendingSearch = null;
    setTimeout(doSearch, 0);
  }
}

function showFoundText(container, artist, title, body, note) {
  // usuń poprzedni podgląd w tym kontenerze
  container.querySelectorAll('.found-preview').forEach((n) => n.remove());
  const titleI = el('input', { class: 'input', value: title, placeholder: 'Tytuł' });
  const artistI = el('input', { class: 'input', value: artist, placeholder: 'Wykonawca' });
  const bodyI = el('textarea', { class: 'input mono', rows: '12', spellcheck: 'false' }); bodyI.value = body;
  const preview = el('div', { class: 'song-body preview-frame' });
  const upd = () => (preview.innerHTML = renderChordPro(bodyI.value, { showChords: true }));
  bodyI.addEventListener('input', upd); upd();

  const wrap = el('div', { class: 'found-preview' },
    note ? el('div', { class: 'notice notice-ok', text: '✓ ' + note }) : null,
    el('div', { class: 'found-fields' }, artistI, titleI),
    el('div', { class: 'found-split' },
      el('div', {}, el('div', { class: 'field-label' }, 'Treść (ChordPro)'),
        el('div', { class: 'cp-toolbar' }, el('button', { class: 'btn btn-xs', type: 'button', onClick: () => { bodyI.value = plainToChordPro(bodyI.value); upd(); } }, '✨ Auto-konwersja')),
        bodyI),
      el('div', {}, el('div', { class: 'field-label' }, 'Podgląd'), preview),
    ),
    el('div', { class: 'found-actions' },
      el('button', { class: 'btn btn-primary', onClick: () => {
        const s = store.createSong({ title: titleI.value.trim() || 'Bez tytułu', artist: artistI.value.trim(), body: bodyI.value });
        toast('Zapisano do śpiewnika ✓', 'success');
        go('songs', { songId: s.id });
      } }, '💾 Zapisz jako piosenkę'),
    ),
  );
  container.append(wrap);
  wrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ------------------------------------------------------------------ Ustawienia
function renderSettings(view, actions) {
  $('#viewTitle').textContent = 'Wygląd i style';
  const s = store.settings;
  const upd = (patch) => { store.updateSettings(patch); applySettings(); };

  const row = (label, node, hint) => el('div', { class: 'set-row' }, el('div', { class: 'set-label' }, el('span', { text: label }), hint ? el('small', { class: 'muted', text: hint }) : null), node);

  const themeSel = el('select', { class: 'input', onchange: (e) => upd({ theme: e.target.value }) },
    ...['auto', 'light', 'dark'].map((v) => el('option', { value: v, ...(s.theme === v ? { selected: true } : {}) }, { auto: 'Automatyczny', light: 'Jasny', dark: 'Ciemny' }[v])));

  const fonts = ["'Georgia', serif", "'Segoe UI', system-ui, sans-serif", "'Courier New', monospace", "'Times New Roman', serif", "'Trebuchet MS', sans-serif"];
  const fontSel = el('select', { class: 'input', onchange: (e) => upd({ fontFamily: e.target.value }) },
    ...fonts.map((v) => el('option', { value: v, ...(s.fontFamily === v ? { selected: true } : {}) }, v.split(',')[0].replace(/'/g, ''))));

  const sizeI = el('input', { class: 'range', type: 'range', min: '13', max: '34', value: s.fontSize, oninput: (e) => { upd({ fontSize: +e.target.value }); sizeVal.textContent = e.target.value + 'px'; } });
  const sizeVal = el('span', { class: 'range-val', text: s.fontSize + 'px' });

  const lineI = el('input', { class: 'range', type: 'range', min: '12', max: '30', value: Math.round(s.lineHeight * 10), oninput: (e) => { const v = +e.target.value / 10; upd({ lineHeight: v }); lineVal.textContent = v.toFixed(1); } });
  const lineVal = el('span', { class: 'range-val', text: s.lineHeight.toFixed(1) });

  const chordColor = el('input', { type: 'color', class: 'color', value: s.chordColor, oninput: (e) => upd({ chordColor: e.target.value }) });
  const lyricColor = el('input', { type: 'color', class: 'color', value: s.lyricColor || '#222222', oninput: (e) => upd({ lyricColor: e.target.value }) });

  const chk = (checked, onchange) => el('label', { class: 'switch' }, el('input', { type: 'checkbox', ...(checked ? { checked: true } : {}), onchange }), el('span', { class: 'slider' }));

  const colsSel = el('select', { class: 'input', onchange: (e) => upd({ columns: +e.target.value }) },
    el('option', { value: '1', ...(s.columns === 1 ? { selected: true } : {}) }, '1 kolumna'),
    el('option', { value: '2', ...(s.columns === 2 ? { selected: true } : {}) }, '2 kolumny'));

  // podgląd
  const demo = `{comment: Podgląd stylu}\n[C]Tak wygląda [G]tekst z [Am]chwytami [F]w Twoim śpiewniku`;
  const demoBox = el('div', { class: 'song-body preview-frame' });
  const refreshDemo = () => (demoBox.innerHTML = renderChordPro(demo, { showChords: s.showChords }));
  const wrapUpd = (patch) => { upd(patch); refreshDemo(); };
  refreshDemo();

  view.append(el('div', { class: 'settings' },
    el('div', { class: 'settings-panel' },
      el('h3', { class: 'block-h' }, 'Motyw i typografia'),
      row('Motyw', themeSel),
      row('Czcionka tekstu', fontSel),
      row('Wielkość tekstu', el('div', { class: 'range-wrap' }, sizeI, sizeVal)),
      row('Odstęp linii', el('div', { class: 'range-wrap' }, lineI, lineVal)),
      row('Układ', colsSel, 'Dwie kolumny oszczędzają papier przy druku'),
      el('h3', { class: 'block-h mt' }, 'Kolory i chwyty'),
      row('Kolor chwytów', chordColor),
      row('Kolor tekstu', lyricColor),
      row('Pogrubione chwyty', chk(s.chordBold, (e) => wrapUpd({ chordBold: e.target.checked }))),
      row('Pokazuj chwyty', chk(s.showChords, (e) => wrapUpd({ showChords: e.target.checked }))),
      row('Diagramy akordów', chk(s.showDiagrams, (e) => upd({ showDiagrams: e.target.checked })), 'Rysunki chwytów gitarowych nad tekstem'),
      el('button', { class: 'btn btn-ghost mt', onClick: () => { store.resetSettings(); render(); toast('Przywrócono domyślne'); } }, '↺ Przywróć domyślne'),
    ),
    el('div', { class: 'settings-preview' },
      el('div', { class: 'field-label' }, 'Podgląd'),
      demoBox,
      el('div', { class: 'about' },
        (sync.available() && sync.hasToken()) ? el('div', { class: 'about-link' },
          el('h4', {}, '🔗 Twój link bez wpisywania tokenu'),
          el('p', { class: 'muted', text: 'Zapisz ten link w zakładkach lub dodaj do ekranu głównego — otworzy śpiewnik od razu, bez podawania tokenu.' }),
          el('button', { class: 'btn btn-sm', onClick: (e) => { const link = `${location.origin}/?t=${encodeURIComponent(sync.token())}`; copyText(link); toast('Skopiowano link ✓', 'success'); } }, '📋 Kopiuj mój link'),
        ) : null,
        el('h4', { class: 'mt' }, 'O aplikacji'),
        el('p', { class: 'muted', text: 'Dane działają na tym urządzeniu (localStorage), a w wersji z serwerem synchronizują się między urządzeniami. Status widać w menu na dole. Dobrze mieć też kopię: Eksport / Import.' }),
      ),
    ),
  ));
}

// ------------------------------------------------------------------ Występ
let scrollTimer = null;
function openPerformance(startSongId, listId = null) {
  const songIds = listId ? [...store.list(listId).songIds] : [startSongId];
  let idx = Math.max(0, songIds.indexOf(startSongId));
  const overlay = el('div', { class: 'perf-overlay' });
  const content = el('div', { class: 'perf-content' });
  let speed = 0;

  const applyScale = () => overlay.style.setProperty('--stage-scale', store.settings.stageScale);
  const bumpScale = (d) => { const v = Math.min(2.6, Math.max(0.9, Math.round((store.settings.stageScale + d) * 100) / 100)); store.updateSettings({ stageScale: v }); applyScale(); };

  const draw = () => {
    const s = store.song(songIds[idx]);
    content.innerHTML = '';
    content.append(renderSongReader(s, { withControls: false }));
    content.scrollTop = 0;
    nav.querySelector('.perf-pos').textContent = `${idx + 1} / ${songIds.length}`;
  };

  // Wake Lock — ekran nie gaśnie podczas występu (jeśli przeglądarka wspiera).
  let wakeLock = null;
  const acquireWake = async () => { try { if ('wakeLock' in navigator) wakeLock = await navigator.wakeLock.request('screen'); } catch { /* ignore */ } };
  const releaseWake = () => { try { wakeLock && wakeLock.release(); } catch { /* ignore */ } wakeLock = null; };
  const onVis = () => { if (document.visibilityState === 'visible' && document.body.contains(overlay)) acquireWake(); };
  document.addEventListener('visibilitychange', onVis);

  const closePerf = () => { stopScroll(); releaseWake(); document.removeEventListener('visibilitychange', onVis); overlay.remove(); document.body.classList.remove('perf-mode'); };
  const stopScroll = () => { if (scrollTimer) { clearInterval(scrollTimer); scrollTimer = null; } };
  const setScroll = (v) => {
    speed = v; stopScroll();
    if (speed > 0) scrollTimer = setInterval(() => { content.scrollTop += 1; }, Math.max(10, 110 - speed * 30));
    spd.textContent = speed ? '×' + speed : 'auto-scroll';
  };
  const spd = el('span', { class: 'perf-val', text: 'auto-scroll' });

  const nav = el('div', { class: 'perf-bar' },
    el('button', { class: 'btn btn-sm', onClick: closePerf }, '✕ Zamknij'),
    el('span', { class: 'perf-pos' }, ''),
    el('div', { class: 'perf-spacer' }),
    el('button', { class: 'btn btn-sm', title: 'Mniejszy tekst', onClick: () => bumpScale(-0.15) }, 'A−'),
    el('button', { class: 'btn btn-sm', title: 'Większy tekst', onClick: () => bumpScale(0.15) }, 'A+'),
    el('button', { class: 'btn btn-sm', onClick: () => { setTranspose(songIds[idx], currentSteps(songIds[idx]) - 1); draw(); } }, '♭'),
    el('button', { class: 'btn btn-sm', onClick: () => { setTranspose(songIds[idx], currentSteps(songIds[idx]) + 1); draw(); } }, '♯'),
    el('button', { class: 'btn btn-sm', onClick: () => setScroll(Math.max(0, speed - 1)) }, '−'),
    spd,
    el('button', { class: 'btn btn-sm', onClick: () => setScroll(Math.min(3, speed + 1)) }, '+'),
    el('div', { class: 'perf-spacer' }),
    el('button', { class: 'btn btn-sm', disabled: songIds.length < 2 ? true : false, onClick: () => { if (idx > 0) { idx--; setScroll(0); draw(); } } }, '‹ Poprz.'),
    el('button', { class: 'btn btn-sm', disabled: songIds.length < 2 ? true : false, onClick: () => { if (idx < songIds.length - 1) { idx++; setScroll(0); draw(); } } }, 'Nast. ›'),
  );
  overlay.append(nav, content);
  document.body.append(overlay);
  document.body.classList.add('perf-mode');
  applyScale();
  acquireWake();
  draw();

  const keyHandler = (e) => {
    if (!document.body.contains(overlay)) { document.removeEventListener('keydown', keyHandler); return; }
    if (e.key === 'Escape') { closePerf(); }
    if (e.key === 'ArrowRight' && idx < songIds.length - 1) { idx++; setScroll(0); draw(); }
    if (e.key === 'ArrowLeft' && idx > 0) { idx--; setScroll(0); draw(); }
  };
  document.addEventListener('keydown', keyHandler);
}

// ------------------------------------------------------------------ Metronom
let metro = { ctx: null, timer: null, on: false, btn: null };
function toggleMetronome(btn, bpm) {
  if (metro.on) {
    clearInterval(metro.timer); metro.on = false;
    if (metro.btn) metro.btn.classList.remove('active');
    return;
  }
  metro.ctx = metro.ctx || new (window.AudioContext || window.webkitAudioContext)();
  metro.on = true; metro.btn = btn; btn.classList.add('active');
  let beat = 0;
  const tick = () => {
    const o = metro.ctx.createOscillator();
    const g = metro.ctx.createGain();
    o.frequency.value = beat % 4 === 0 ? 1500 : 900;
    g.gain.setValueAtTime(0.001, metro.ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.4, metro.ctx.currentTime + 0.001);
    g.gain.exponentialRampToValueAtTime(0.001, metro.ctx.currentTime + 0.05);
    o.connect(g); g.connect(metro.ctx.destination);
    o.start(); o.stop(metro.ctx.currentTime + 0.05);
    beat++;
  };
  tick();
  metro.timer = setInterval(tick, 60000 / bpm);
}

// --------------------------------------------------------- status + synchronizacja
function setSyncStatus(state) {
  const node = $('#backendStatus');
  if (!node) return;
  const map = {
    local: '<span class="dot dot-off"></span> Tryb lokalny (dane na tym urządzeniu)',
    ok: '<span class="dot dot-ok"></span> Zsynchronizowano ✓',
    saving: '<span class="dot dot-sync"></span> Zapisywanie…',
    error: '<span class="dot dot-err"></span> Błąd synchronizacji',
    auth: '<span class="dot dot-err"></span> Wymagany token — kliknij, by podać',
    connecting: '<span class="dot dot-sync"></span> Łączenie z serwerem…',
  };
  node.innerHTML = map[state] || map.local;
  node.style.cursor = state === 'auth' ? 'pointer' : 'default';
  node.onclick = state === 'auth' ? promptToken : null;
}

function promptToken() {
  const input = el('input', { class: 'input', type: 'password', placeholder: 'Token dostępu' });
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') connect(); });
  async function connect() {
    sync.setToken(input.value);
    m.close();
    setSyncStatus('connecting');
    const res = await sync.pull();
    if (res.auth) { toast('Nieprawidłowy token', 'error'); setSyncStatus('auth'); return; }
    if (!res.ok) { setSyncStatus('error'); return; }
    if (res.empty) { await sync.push(); } else { sync.applyRemote(res.library); }
    startPushing();
    render();
    setSyncStatus('ok');
    toast('Zsynchronizowano ✓', 'success');
  }
  const m = modal({
    title: '🔒 Śpiewnik — dostęp',
    body: el('div', {},
      el('p', { text: 'Ten śpiewnik jest chroniony tokenem. Podaj go, aby zsynchronizować swoje piosenki na tym urządzeniu.' }),
      input),
    actions: [el('button', { class: 'btn btn-primary', onClick: connect }, 'Połącz')],
  });
  setTimeout(() => input.focus(), 50);
}

let pushingStarted = false;
function startPushing() {
  if (pushingStarted) return;
  pushingStarted = true;
  store.subscribe(() => sync.schedulePush());
}

async function setupSync() {
  setSyncStatus('connecting');
  const ok = await sync.detect();
  if (!ok) { setSyncStatus('local'); return; }        // brak serwera → czysto lokalnie
  sync.onStatus(setSyncStatus);
  if (sync.authRequired() && !sync.hasToken()) { setSyncStatus('auth'); promptToken(); return; }
  const res = await sync.pull();
  if (res.auth) { setSyncStatus('auth'); promptToken(); return; }
  if (!res.ok) { setSyncStatus('error'); return; }
  if (res.empty) { await sync.push(); } else { sync.applyRemote(res.library); }
  startPushing();
  render();
  setSyncStatus('ok');
}

// ------------------------------------------------------------------ init
function bind() {
  $$('.nav-item').forEach((b) => b.addEventListener('click', () => go(b.dataset.view, b.dataset.view === 'songs' ? { songId: null } : b.dataset.view === 'lists' ? { listId: null } : {})));
  $('#btnNewSong').addEventListener('click', () => newSong());
  $('#btnNewList').addEventListener('click', () => { const l = store.createList(); go('lists', { listId: l.id }); });
  $('#menuToggle').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  $('#sidebarClose').addEventListener('click', () => $('#sidebar').classList.remove('open'));
  $('#btnHelp').addEventListener('click', helpModal);
  // skrót „/" — skok do wyszukiwarki w liście piosenek
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      const s = document.querySelector('.search-input'); if (s) { e.preventDefault(); s.focus(); }
    }
  });

  $('#btnExport').addEventListener('click', async () => { await download(`spiewnik-kopia-${new Date().toISOString().slice(0, 10)}.json`, store.exportJSON()); });
  $('#btnImport').addEventListener('click', () => $('#importFile').click());
  $('#importFile').addEventListener('change', (e) => {
    const file = e.target.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const doImport = (merge) => {
        try { store.importJSON(reader.result, { merge }); toast(merge ? 'Dołączono dane z kopii' : 'Zaimportowano (zastąpiono)'); m.close(); go('songs', { songId: null }); }
        catch (err) { toast('Błąd importu: ' + err.message, 'error'); }
      };
      const m = modal({
        title: 'Import kopii',
        body: el('p', { text: 'Jak zaimportować dane z pliku?' }),
        actions: [
          el('button', { class: 'btn', onClick: () => m.close() }, 'Anuluj'),
          el('button', { class: 'btn', onClick: () => doImport(true) }, 'Dołącz do istniejących'),
          el('button', { class: 'btn btn-danger', onClick: () => doImport(false) }, 'Zastąp wszystko'),
        ],
      });
    };
    reader.readAsText(file);
    e.target.value = '';
  });

  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (store.settings.theme === 'auto') applySettings(); });
}

// Token można podać w adresie (?t=… albo #t=…) — dzięki temu wystarczy raz
// zapisać osobisty link (zakładka / ekran główny) i nigdy nie wpisywać tokenu.
function captureUrlToken() {
  try {
    const url = new URL(location.href);
    let t = url.searchParams.get('t') || url.searchParams.get('token') || '';
    if (!t && location.hash) { const m = location.hash.match(/[#&](?:t|token)=([^&]+)/); if (m) t = decodeURIComponent(m[1]); }
    if (t) sync.setToken(t);
  } catch { /* ignore */ }
}

applySettings();
bind();
render();
captureUrlToken();
setupSync();
if (!store.settings.seenWelcome) setTimeout(welcomeModal, 400);
