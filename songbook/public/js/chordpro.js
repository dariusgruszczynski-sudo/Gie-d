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

// `known` (opcjonalny Set znormalizowanych akordów) = słownik akordów, o których
// WIEMY, że należą do tego utworu (z pewnych linii chwytów w tym samym tekście
// albo z porównania kilku opracowań). Token, który normalizuje się do akordu z
// tego zbioru, traktujemy jako pewny — dzięki temu poprawnie czytamy nawet
// pojedyncze litery („a", „e", „h"), których inaczej nie ruszamy (polskie słowa).
function isChordLine(line, known) {
  const tokens = line.trim().split(/\s+/).filter(Boolean);
  if (!tokens.length) return false;
  let chords = 0, strong = 0;
  for (const t of tokens) {
    const n = normalizeChordToken(t);
    if (n) {
      chords++;
      if (t.length >= 2 || /[A-H]/.test(t[0]) || (known && known.has(n))) strong++;
    }
  }
  // Akceptujemy linię, gdy ≥60% tokenów to akordy ORAZ jest ≥2 akordy (np. „a e")
  // albo choć jeden „mocny" akord (duża litera / dłuższy token / znany akord).
  return chords / tokens.length >= 0.6 && (chords >= 2 || strong >= 1);
}

// Bardzo pewna linia chwytów (do budowy słownika): prawie same akordy i ≥1 mocny.
function isStrongChordLine(line) {
  const tokens = line.trim().split(/\s+/).filter(Boolean);
  if (tokens.length < 1) return false;
  let chords = 0, strong = 0;
  for (const t of tokens) {
    const n = normalizeChordToken(t);
    if (n) { chords++; if (t.length >= 2 || /[A-H]/.test(t[0]) || /[#b]/.test(t)) strong++; }
  }
  return chords === tokens.length && strong >= 1;
}

// Zbiera słownik akordów utworu: z gotowych [nawiasów] ORAZ z pewnych linii chwytów.
// To podstawa „rozumowania, które litery to akordy" — poznajemy realny zestaw akordów.
export function getChordVocabulary(text) {
  const set = new Set();
  const src = String(text).replace(/\r\n/g, '\n');
  // 1) już oznaczone chwyty [X]
  for (const m of src.matchAll(/\[([^\]]+)\]/g)) {
    const n = normalizeChordToken(m[1]); if (n) set.add(n);
  }
  // 2) pewne linie chwytów (nawet zlepki „CGC")
  for (const line of src.split('\n')) {
    if (!isStrongChordLine(line)) continue;
    for (const t of line.trim().split(/\s+/)) {
      const n = normalizeChordToken(t);
      if (n) { set.add(n); continue; }
      const run = splitChordRun(t);
      if (run) run.forEach((c) => { const nc = normalizeChordToken(c); if (nc) set.add(nc); });
    }
  }
  return set;
}

// Konsensus z KILKU opracowań: akord uznajemy za „prawdziwy dla utworu", gdy
// pojawia się w ≥2 wersjach (albo jest tylko jedna wersja). Odsiewa literówki i
// przypadkowe słowa uznane gdzieś błędnie za akord.
export function consensusVocabulary(texts) {
  const counts = new Map();
  const list = (texts || []).filter(Boolean);
  for (const t of list) {
    for (const c of getChordVocabulary(t)) counts.set(c, (counts.get(c) || 0) + 1);
  }
  const min = list.length >= 2 ? 2 : 1;
  const set = new Set();
  for (const [c, n] of counts) if (n >= min) set.add(c);
  return set;
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
function looksLikeChordStrong(t, known) {
  const n = normalizeChordToken(t);
  if (!n) return false;
  const bare = t.replace(/^[("']+/, '').replace(/[).,;:!?"']+$/, '');
  if (/[#b]/.test(bare)) return true;          // z krzyżykiem/bemolem: F#, Bb…
  if (bare.length >= 2) return true;            // z sufiksem: Am, G7, Dm7, C/E…
  if (/^[BCDEFGH]$/.test(bare)) return true;    // duża litera nutowa (bez „A", bo to polskie słowo)
  // Gołą pojedynczą MAŁĄ literę (a, e, h, c…) uznajemy za akord WEWNĄTRZ tekstu
  // tylko wyjątkowo — bo to polskie słowa („a", „e", „i"). Słownik `known` NIE
  // wystarcza (miałby oznaczać każde „a"/„e" w zwrotce). Zostawiamy jako tekst.
  return false;
}

// Rozkłada ZLEPIONĄ zbitkę chwytów na osobne, np. "CGC" -> [C,G,C],
// "aFG" -> [a,F,G], "CGC/C7" -> [C,G,C,C7]. Zwraca null, gdy się nie da czysto.
function splitChordRun(tok) {
  if (!/^[A-Ha-h][A-Ha-h0-9#b/]*$/.test(tok)) return null;
  const one = /^[A-Ha-h][#b]?(?:maj7|maj9|maj|min|dim|aug|sus2|sus4|sus|add9|add|m)?(?:13|11|9|7|6|5|4|2)?/;
  const parts = [];
  let rest = tok, guard = 0;
  while (rest.length && guard++ < 24) {
    if (rest[0] === '/') { rest = rest.slice(1); continue; } // separator / bas
    const m = rest.match(one);
    if (!m || !m[0]) return null;
    parts.push(m[0]);
    rest = rest.slice(m[0].length);
  }
  return parts.length >= 2 ? parts : null;
}

// Rozmieszcza chwyty NAD słowami linii, gdy znamy je dla całej linii, ale nie
// znamy dokładnych pozycji (np. zbitka po prawej) — rozkładamy równomiernie.
function placeChordsOverLine(lyric, chords) {
  if (!chords.length) return lyric;
  const parts = lyric.split(/(\s+)/); // zachowaj odstępy
  const wordPos = [];
  parts.forEach((p, i) => { if (p.trim()) wordPos.push(i); });
  if (!wordPos.length) return chords.map((c) => `[${c}]`).join(' ');
  const out = [...parts];
  chords.forEach((c, k) => {
    const wp = Math.min(wordPos.length - 1, Math.round((k * wordPos.length) / chords.length));
    out[wordPos[wp]] = `[${c}]` + out[wordPos[wp]];
  });
  return out.join('');
}

// Oznacza chwyty ZAPISANE W LINII Z TEKSTEM (w środku, między słowami, po prawej)
// oraz w nawiasach „(C)". Pozostawia tekst nietknięty tam, gdzie akordów nie ma.
export function inlineChords(line, known) {
  if (line.includes('[')) return line; // już w formacie ChordPro
  // chwyty w nawiasach: (C), (Am7), (F#) -> [C] [Am7] [F#]
  line = line.replace(/\(([A-Ha-h][#b]?[^\s()]{0,6})\)/g, (full, inner) => {
    const n = normalizeChordToken(inner);
    return n ? `[${n}]` : full;
  });
  // chwyty PO PRAWEJ: tekst + większa przerwa + zbitka akordów na końcu (także
  // ZLEPIONA, np. „…dalej    CGC"). Rozkładamy je równomiernie NAD tekstem.
  for (const g of line.matchAll(/\s{2,}/g)) {
    const prefix = line.slice(0, g.index);
    if (!prefix.trim()) continue;
    const after = line.slice(g.index + g[0].length);
    if (after.includes('[')) continue;
    const rawToks = after.trim().split(/\s+/);
    const chords = [];
    let ok = rawToks.length > 0;
    for (const t of rawToks) {
      const n = normalizeChordToken(t);
      if (n) { chords.push(n); continue; }
      const run = splitChordRun(t);
      if (run) { run.forEach((c) => { const nc = normalizeChordToken(c); if (nc) chords.push(nc); }); continue; }
      ok = false; break;
    }
    if (ok && chords.length) return placeChordsOverLine(prefix.replace(/\s+$/, ''), chords);
  }
  // samodzielne, jednoznaczne chwyty w środku tekstu (prefix i reszta)
  return line.replace(/\S+/g, (tok) => {
    const m = tok.match(/^([("']?)([A-Ha-h][^\s]*?)([).,;:!?"']*)$/);
    if (!m) return tok;
    if (!looksLikeChordStrong(m[2], known)) return tok;
    const n = normalizeChordToken(m[2]);
    return n ? `${m[1]}[${n}]${m[3]}` : tok;
  });
}

// `known` (opcjonalny Set) = akordy pewne dla tego utworu (np. konsensus z kilku
// opracowań). Nawet bez niego robimy DWA przebiegi: najpierw poznajemy słownik
// akordów z pewnych linii chwytów w samym tekście, potem parsujemy z tą wiedzą —
// dzięki temu dwuznaczne litery („a", „e", „h") czytamy poprawnie.
export function plainToChordPro(text, known) {
  const raw = String(text).replace(/\r\n/g, '\n');
  // Przebieg 1: słownik akordów utworu (z pewnych linii chwytów) + ewentualny konsensus.
  const vocab = new Set(getChordVocabulary(raw));
  if (known) for (const c of known) vocab.add(c);

  const lines = raw.split('\n');
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const cur = lines[i];
    const next = lines[i + 1];
    if (isChordLine(cur, vocab) && next !== undefined && !isChordLine(next, vocab) && next.trim() !== '') {
      out.push(mergeChordLyric(cur, next));
      i++; // pomijamy zużytą linię tekstu
    } else if (isChordLine(cur, vocab) && (next === undefined || next.trim() === '')) {
      // sama linia chwytów (np. wstęp) — zamień tokeny na [akordy]
      out.push(cur.trim().split(/\s+/).map((t) => normalizeChordToken(t)).filter(Boolean).map((c) => `[${c}]`).join(' '));
    } else {
      // zwykła linia tekstu — ale mogą w niej siedzieć chwyty (w środku/po prawej/w nawiasach)
      out.push(inlineChords(cur, vocab));
    }
  }
  return out.join('\n');
}

// Ocena, jak dobre jest opracowanie (do wyboru najlepszej wersji z kilku):
// premiujemy dużo różnych akordów rozłożonych NAD tekstem i obecność słów.
export function scoreArrangement(chordproText) {
  const src = String(chordproText || '');
  const chordCount = (src.match(/\[[^\]]+\]/g) || []).length;
  const vocab = getChordVocabulary(src).size;
  const lyricLines = src.split('\n').filter((l) => {
    const t = l.replace(/\[[^\]]*\]/g, '').replace(/\{[^}]*\}/g, '').trim();
    return t.length > 3;
  }).length;
  if (chordCount === 0 || lyricLines === 0) return 0;
  // różnorodność akordów + gęstość, z premią za obecność realnego tekstu
  return vocab * 4 + Math.min(chordCount, 120) + Math.min(lyricLines, 80);
}

// Rozciąga chwyty na resztę utworu: bierze pierwszą zwrotkę i pierwszy refren
// (te z chwytami) jako szablon i nakłada je na kolejne, niezachwycone zwrotki/
// refreny — dopasowując linia-do-linii wewnątrz bloku. Linie już z chwytami
// zostają nietknięte. Heurystyka pod śpiewniki „chwyty tylko na 1. zwrotkę".
const chordsOfLine = (line) => (line.match(/\[([^\]]+)\]/g) || []).map((x) => x.slice(1, -1));
const isDirectiveLine = (l) => /^\s*\{.*\}\s*$/.test(l);
const isChorusMarker = (l) => /^\s*(?:\[[^\]]*\]\s*)*(ref\.?\s*:|refren|chorus)/i.test(l);

export function stretchChords(source) {
  const lines = String(source).replace(/\r\n/g, '\n').split('\n');
  const n = lines.length;
  const blockId = new Array(n).fill(0);
  const inChorusArr = new Array(n).fill(false);
  // 1) granice bloków (pusta linia dzieli) + stan refrenu ({soc}/{eoc})
  let bid = 0, soc = false, prevBlank = true;
  for (let i = 0; i < n; i++) {
    const l = lines[i];
    if (l.trim() === '') { prevBlank = true; continue; }
    if (prevBlank) { bid++; prevBlank = false; }
    blockId[i] = bid;
    if (isDirectiveLine(l)) { if (/start_of_chorus|soc/i.test(l)) soc = true; if (/end_of_chorus|eoc/i.test(l)) soc = false; }
    inChorusArr[i] = soc;
  }
  // 2) który blok to refren, który ma chwyty
  const blockChorus = {}, blockHasChords = {};
  for (let i = 0; i < n; i++) {
    const b = blockId[i]; if (!b) continue;
    if (inChorusArr[i] || isChorusMarker(lines[i])) blockChorus[b] = true;
    if (chordsOfLine(lines[i]).length) blockHasChords[b] = true;
  }
  // 3) szablon = pierwszy blok z chwytami danego typu (per-linia lista akordów)
  const buildTpl = (chorus) => {
    let target = 0;
    for (let i = 0; i < n; i++) { const b = blockId[i]; if (b && blockHasChords[b] && (!!blockChorus[b] === chorus)) { target = b; break; } }
    if (!target) return [];
    const tpl = [];
    for (let i = 0; i < n; i++) { if (blockId[i] === target && !isDirectiveLine(lines[i])) tpl.push(chordsOfLine(lines[i])); }
    return tpl;
  };
  const verseTpl = buildTpl(false), chorusTpl = buildTpl(true);
  if (!verseTpl.length && !chorusTpl.length) return source;

  // 4) nałóż szablon na bloki BEZ chwytów (dopasowanie linia-do-linii w bloku)
  const out = lines.slice();
  let lastBlock = -1, li = 0;
  for (let i = 0; i < n; i++) {
    const b = blockId[i]; if (!b) continue;
    if (b !== lastBlock) { lastBlock = b; li = 0; }
    if (isDirectiveLine(lines[i])) continue;
    const idx = li++;
    if (blockHasChords[b]) continue;                 // blok-szablon / już z chwytami
    const tpl = blockChorus[b] ? (chorusTpl.length ? chorusTpl : verseTpl) : (verseTpl.length ? verseTpl : chorusTpl);
    if (!tpl.length) continue;
    const chords = tpl[idx % tpl.length];
    if (chords && chords.length) out[i] = placeChordsOverLine(lines[i], chords);
  }
  return out.join('\n');
}
