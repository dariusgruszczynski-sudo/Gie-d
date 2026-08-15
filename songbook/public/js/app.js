// app.js — główny moduł aplikacji Śpiewnik.
import { store } from './store.js';
import { render as renderChordPro, extractChords, transposeSource, plainToChordPro } from './chordpro.js';
import { chordDiagram, hasShape } from './chords.js';
import { searchLyrics, importUrl, searchWeb } from './search-client.js';
import { sync } from './sync.js';

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
  const titleMap = { songs: 'Piosenki', lists: 'Listy', search: 'Wyszukaj', settings: 'Wygląd' };
  const actions = $('#topbarActions'); actions.innerHTML = '';
  const view = $('#view'); view.innerHTML = '';
  $('#viewTitle').textContent = titleMap[app.view] || 'Śpiewnik';

  if (app.view === 'songs' && app.songId) return renderSongDetail(view, actions);
  if (app.view === 'songs') return renderSongs(view, actions);
  if (app.view === 'lists' && app.listId) return renderListDetail(view, actions);
  if (app.view === 'lists') return renderLists(view, actions);
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

  const listWrap = el('div', { class: 'card-grid' });
  const refreshList = () => {
    listWrap.innerHTML = '';
    const q = app.filter.trim().toLowerCase();
    let songs = store.songs().filter((s) => {
      if (app.tagFilter && !(s.tags || []).includes(app.tagFilter)) return false;
      if (!q) return true;
      return (s.title + ' ' + s.artist + ' ' + (s.tags || []).join(' ')).toLowerCase().includes(q);
    });
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

  view.append(el('div', { class: 'toolbar' }, search), tagBar, listWrap);
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
  actions.append(
    el('button', { class: 'btn btn-sm', onClick: () => { app.editing = false; render(); } }, '‹ Podgląd'),
    el('button', { class: 'btn btn-sm btn-primary', onClick: save }, '💾 Zapisz'),
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
  const updatePreview = () => { preview.innerHTML = renderChordPro(f.body.value, { showChords: store.settings.showChords }); };
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
    el('button', { class: 'btn btn-xs', type: 'button', title: 'Zamień wklejony surowy tekst (chwyty nad tekstem) na format ChordPro', onClick: () => { f.body.value = plainToChordPro(f.body.value); updatePreview(); toast('Skonwertowano do ChordPro'); } }, '✨ Auto-konwersja'),
  );

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

  function save() {
    const tags = f.tags.value.split(',').map((t) => t.trim()).filter(Boolean);
    store.updateSong(s.id, {
      title: f.title.value.trim() || 'Bez tytułu',
      artist: f.artist.value.trim(),
      key: f.key.value.trim(),
      capo: parseInt(f.capo.value) || 0,
      tempo: parseInt(f.tempo.value) || 0,
      tags, notes: f.notes.value, body: f.body.value,
      tabs: localTabs.filter((t) => t.content.trim()),
    });
    toast('Zapisano ✓', 'success');
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
        el('div', { class: 'field-label' }, 'Podgląd na żywo'),
        el('div', { class: 'preview-frame' }, preview),
      ),
    ),
    el('div', { class: 'field-label mt' }, '🎸 Moduł tabulatur'),
    tabsBox,
  ));
}

function tabTemplate() {
  return 'e|-----------------|\nB|-----------------|\nG|-----------------|\nD|-----------------|\nA|-----------------|\nE|-----------------|';
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
        el('h4', {}, 'O aplikacji'),
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

  const draw = () => {
    const s = store.song(songIds[idx]);
    content.innerHTML = '';
    content.append(renderSongReader(s, { withControls: false }));
    content.scrollTop = 0;
    nav.querySelector('.perf-pos').textContent = `${idx + 1} / ${songIds.length}`;
  };
  const stopScroll = () => { if (scrollTimer) { clearInterval(scrollTimer); scrollTimer = null; } };
  const setScroll = (v) => {
    speed = v; stopScroll();
    if (speed > 0) scrollTimer = setInterval(() => { content.scrollTop += 1; }, Math.max(10, 110 - speed * 30));
    spd.textContent = speed ? '×' + speed : 'auto-scroll';
  };
  const spd = el('span', { class: 'perf-val', text: 'auto-scroll' });

  const nav = el('div', { class: 'perf-bar' },
    el('button', { class: 'btn btn-sm', onClick: () => { stopScroll(); overlay.remove(); document.body.classList.remove('perf-mode'); } }, '✕ Zamknij'),
    el('span', { class: 'perf-pos' }, ''),
    el('div', { class: 'perf-spacer' }),
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
  draw();

  const keyHandler = (e) => {
    if (!document.body.contains(overlay)) { document.removeEventListener('keydown', keyHandler); return; }
    if (e.key === 'Escape') { stopScroll(); overlay.remove(); document.body.classList.remove('perf-mode'); }
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

applySettings();
bind();
render();
setupSync();
