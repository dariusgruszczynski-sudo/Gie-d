// chordpro.js — parser i renderer formatu ChordPro (chwyty w [nawiasach] w tekście)
// oraz transpozycja. Format ChordPro to standard dla śpiewników:
//   [C]Panie mój, [G]dobry mój
//   {title: ...}, {comment: ...}, {start_of_chorus}, {start_of_tab} ...

const SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

const NOTE_TO_IDX = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

// Rozbija akord na [root, reszta]. Obsługuje np. C, Cm, C#m7, Bb/D, F#sus4
function splitChord(chord) {
  const m = chord.match(/^([A-G])([#b]?)(.*)$/);
  if (!m) return null;
  const [, letter, accidental, rest] = m;
  let idx = NOTE_TO_IDX[letter];
  if (accidental === '#') idx = (idx + 1) % 12;
  if (accidental === 'b') idx = (idx + 11) % 12;
  return { idx, rest };
}

function idxToName(idx, preferFlat) {
  return (preferFlat ? FLAT : SHARP)[((idx % 12) + 12) % 12];
}

// Transponuje pojedynczy token akordu o `steps` półtonów. Obsługuje akordy z basem (C/E).
export function transposeChord(chord, steps, preferFlat = false) {
  if (!chord) return chord;
  return chord
    .split('/')
    .map((part) => {
      const sp = splitChord(part);
      if (!sp) return part;
      const newIdx = (sp.idx + steps) % 12;
      return idxToName(newIdx, preferFlat) + sp.rest;
    })
    .join('/');
}

// Transponuje cały tekst ChordPro (tylko zawartość [nawiasów]).
export function transposeSource(source, steps, preferFlat = false) {
  if (!steps) return source;
  return source.replace(/\[([^\]]+)\]/g, (_, c) => `[${transposeChord(c, steps, preferFlat)}]`);
}

// Zwraca unikalną listę akordów użytych w tekście (po transpozycji).
export function extractChords(source, steps = 0, preferFlat = false) {
  const set = new Set();
  const re = /\[([^\]]+)\]/g;
  let m;
  while ((m = re.exec(source))) {
    const c = steps ? transposeChord(m[1], steps, preferFlat) : m[1];
    if (/^[A-G]/.test(c)) set.add(c);
  }
  return [...set];
}

function esc(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Parsuje jedną linię tekstu na segmenty {chord, text}
function parseLine(line) {
  const units = [];
  const re = /\[([^\]]+)\]/g;
  let last = 0;
  let m;
  let pendingText = '';
  let firstChordSeen = false;
  while ((m = re.exec(line))) {
    const before = line.slice(last, m.index);
    if (!firstChordSeen) {
      pendingText += before;
      if (pendingText) units.push({ chord: '', text: pendingText });
      pendingText = '';
      firstChordSeen = true;
      units.push({ chord: m[1], text: '' });
    } else {
      units[units.length - 1].text += before;
      units.push({ chord: m[1], text: '' });
    }
    last = re.lastIndex;
  }
  const tail = line.slice(last);
  if (units.length) units[units.length - 1].text += tail;
  else units.push({ chord: '', text: line });
  return units;
}

// Renderuje ChordPro -> HTML. Opcje: { steps, preferFlat, showChords }
export function render(source, opts = {}) {
  const { steps = 0, preferFlat = false, showChords = true } = opts;
  const lines = String(source).replace(/\r\n/g, '\n').split('\n');
  let html = '';
  let inTab = false;
  let inChorus = false;
  let tabBuffer = [];

  const flushTab = () => {
    if (tabBuffer.length) {
      html += `<pre class="cp-tab">${esc(tabBuffer.join('\n'))}</pre>`;
      tabBuffer = [];
    }
  };

  for (let raw of lines) {
    const line = raw;
    const directive = line.trim().match(/^\{\s*([a-zA-Z_]+)\s*:?\s*([^}]*)\}$/);
    if (directive) {
      const name = directive[1].toLowerCase();
      const val = directive[2].trim();
      switch (name) {
        case 'title': case 't':
          html += `<div class="cp-title">${esc(val)}</div>`; break;
        case 'subtitle': case 'st': case 'artist':
          html += `<div class="cp-subtitle">${esc(val)}</div>`; break;
        case 'comment': case 'c': case 'ci':
          html += `<div class="cp-comment">${esc(val)}</div>`; break;
        case 'start_of_chorus': case 'soc':
          inChorus = true; html += `<div class="cp-chorus">`; if (val) html += `<div class="cp-label">${esc(val)}</div>`; break;
        case 'end_of_chorus': case 'eoc':
          inChorus = false; html += `</div>`; break;
        case 'start_of_verse': case 'sov':
          html += `<div class="cp-verse">`; if (val) html += `<div class="cp-label">${esc(val)}</div>`; break;
        case 'end_of_verse': case 'eov':
          html += `</div>`; break;
        case 'start_of_tab': case 'sot':
          inTab = true; break;
        case 'end_of_tab': case 'eot':
          inTab = false; flushTab(); break;
        case 'key': case 'capo': case 'tempo': case 'time':
          html += `<div class="cp-meta">${esc(name)}: ${esc(val)}</div>`; break;
        default:
          if (val) html += `<div class="cp-comment">${esc(val)}</div>`;
      }
      continue;
    }

    if (inTab) { tabBuffer.push(raw); continue; }

    if (line.trim() === '') { html += `<div class="cp-blank"></div>`; continue; }

    const src = steps ? transposeSource(line, steps, preferFlat) : line;
    const units = parseLine(src);
    let lineHtml = '<div class="cp-line">';
    for (const u of units) {
      // gdy chwyty wyłączone, i tak parsujemy by usunąć [nawiasy]
      const text = esc(u.text.length ? u.text : (u.chord && showChords ? ' ' : ''));
      if (showChords && u.chord) {
        lineHtml += `<span class="cp-unit"><span class="cp-chord">${esc(u.chord)}</span><span class="cp-lyric">${text}</span></span>`;
      } else {
        lineHtml += `<span class="cp-unit cp-nochord"><span class="cp-lyric">${text}</span></span>`;
      }
    }
    lineHtml += '</div>';
    html += lineHtml;
  }
  flushTab();
  return html;
}

// Konwertuje "surowy" tekst (linie chwytów nad liniami tekstu) na ChordPro.
// Obsługuje też polski zapis: H = B, oraz małe litery = akordy molowe (a = Am,
// e7 = Em7). Heurystyka: linia jest "linią chwytów", jeśli w większości składa
// się z tokenów akordów i zawiera co najmniej jeden „mocny” akord.
const CHORD_SUFFIX = /^(m|maj|min|dim|aug|sus|add|M)?[0-9]*(sus[0-9]|add[0-9]|maj[0-9])?$/;

// Normalizuje token do standardowego akordu (np. "h"->"Bm", "a7"->"Am7", "C/e"->"C/E")
// albo zwraca null, gdy to nie akord.
export function normalizeChordToken(raw) {
  if (!raw) return null;
  let t = String(raw).trim().replace(/[.,;)]+$/, '').replace(/^\(/, '');
  if (!t) return null;
  const m = t.match(/^([A-Ha-h])([#b]?)(.*)$/);
  if (!m) return null;
  let [, letter, acc, rest] = m;
  const lowerMinor = letter >= 'a' && letter <= 'h';
  // rozdziel bas po '/'
  let bass = '';
  const slash = rest.match(/\/([A-Ha-h])([#b]?)$/);
  if (slash) {
    let b = slash[1].toUpperCase(); if (b === 'H') b = 'B';
    bass = '/' + b + slash[2];
    rest = rest.slice(0, slash.index);
  }
  if (!CHORD_SUFFIX.test(rest)) return null;
  let up = letter.toUpperCase(); if (up === 'H') up = 'B';
  let core = up + acc;
  if (lowerMinor && !/^(m|maj|min|dim|aug|M)/.test(rest)) core += 'm';
  return core + rest + bass;
}

function isChordLine(line) {
  const tokens = line.trim().split(/\s+/).filter(Boolean);
  if (!tokens.length) return false;
  let chords = 0, strong = 0;
  for (const t of tokens) {
    const n = normalizeChordToken(t);
    if (n) { chords++; if (t.length >= 2 || /[A-H]/.test(t[0])) strong++; }
  }
  // Akceptujemy linię, gdy ≥60% tokenów to akordy ORAZ jest ≥2 akordy (np. „a e")
  // albo choć jeden „mocny" akord (duża litera / dłuższy token). Chroni to przed
  // uznaniem pojedynczej małej literki („a" jako polskie słowo) za akord.
  return chords / tokens.length >= 0.6 && (chords >= 2 || strong >= 1);
}

// Łączy linię chwytów z linią tekstu w jedną linię ChordPro na podstawie pozycji kolumn.
function mergeChordLyric(chordLine, lyricLine) {
  const chords = [];
  const re = /(\S+)/g;
  let m;
  while ((m = re.exec(chordLine))) {
    const norm = normalizeChordToken(m[1]);
    if (norm) chords.push({ pos: m.index, chord: norm });
  }
  if (!chords.length) return lyricLine;
  let out = '';
  let prev = 0;
  const line = lyricLine || '';
  for (const c of chords) {
    const p = Math.min(c.pos, line.length);
    out += line.slice(prev, p) + `[${c.chord}]`;
    prev = p;
  }
  out += line.slice(prev);
  return out;
}

// Czy token to na tyle jednoznaczny akord, że można go bezpiecznie oznaczyć
// WEWNĄTRZ linii z tekstem (bez psucia zwykłych słów)?
function looksLikeChordStrong(t) {
  if (!normalizeChordToken(t)) return false;
  const bare = t.replace(/^[("']+/, '').replace(/[).,;:!?"']+$/, '');
  if (/[#b]/.test(bare)) return true;          // z krzyżykiem/bemolem: F#, Bb…
  if (bare.length >= 2) return true;            // z sufiksem: Am, G7, Dm7, C/E…
  if (/^[BCDEFGH]$/.test(bare)) return true;    // duża litera nutowa (bez „A", bo to polskie słowo)
  return false;
}

// Oznacza chwyty ZAPISANE W LINII Z TEKSTEM (w środku, między słowami, po prawej)
// oraz w nawiasach „(C)". Pozostawia tekst nietknięty tam, gdzie akordów nie ma.
export function inlineChords(line) {
  if (line.includes('[')) return line; // już w formacie ChordPro
  // chwyty w nawiasach: (C), (Am7), (F#) -> [C] [Am7] [F#]
  line = line.replace(/\(([A-Ha-h][#b]?[^\s()]{0,6})\)/g, (full, inner) => {
    const n = normalizeChordToken(inner);
    return n ? `[${n}]` : full;
  });
  // chwyty PO PRAWEJ: tekst + większa przerwa + zbitka SAMYCH akordów na końcu.
  // Bierzemy najwcześniejszą dużą przerwę, po której już wszystko jest akordami —
  // dzięki temu łapiemy całą zbitkę (np. „…tekst      C  G  a"). Mocny kontekst,
  // więc akceptujemy też pojedyncze małe litery molowe.
  for (const g of line.matchAll(/\s{2,}/g)) {
    const prefix = line.slice(0, g.index);
    if (!prefix.trim()) continue;
    const after = line.slice(g.index + g[0].length);
    if (after.includes('[')) continue;
    const toks = after.trim().split(/\s+/);
    if (toks.length && toks.every((t) => normalizeChordToken(t))) {
      line = prefix + g[0] + toks.map((t) => `[${normalizeChordToken(t)}]`).join(' ');
      break;
    }
  }
  // samodzielne, jednoznaczne chwyty w środku tekstu (prefix i reszta)
  return line.replace(/\S+/g, (tok) => {
    const m = tok.match(/^([("']?)([A-Ha-h][^\s]*?)([).,;:!?"']*)$/);
    if (!m) return tok;
    if (!looksLikeChordStrong(m[2])) return tok;
    const n = normalizeChordToken(m[2]);
    return n ? `${m[1]}[${n}]${m[3]}` : tok;
  });
}

export function plainToChordPro(text) {
  const lines = String(text).replace(/\r\n/g, '\n').split('\n');
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const cur = lines[i];
    const next = lines[i + 1];
    if (isChordLine(cur) && next !== undefined && !isChordLine(next) && next.trim() !== '') {
      out.push(mergeChordLyric(cur, next));
      i++; // pomijamy zużytą linię tekstu
    } else if (isChordLine(cur) && (next === undefined || next.trim() === '')) {
      // sama linia chwytów (np. wstęp) — zamień tokeny na [akordy]
      out.push(cur.trim().split(/\s+/).map((t) => normalizeChordToken(t)).filter(Boolean).map((c) => `[${c}]`).join(' '));
    } else {
      // zwykła linia tekstu — ale mogą w niej siedzieć chwyty (w środku/po prawej/w nawiasach)
      out.push(inlineChords(cur));
    }
  }
  return out.join('\n');
}
