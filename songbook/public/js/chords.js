// chords.js — biblioteka kształtów akordów gitarowych + generator diagramów SVG.
// Kształt: tablica 6 liczb dla strun [E A D G B e] (od najgrubszej):
//   -1 = struna wyciszona (x), 0 = pusta, n = próg.
// baseFret: od którego progu rysujemy (dla akordów barre).

export const SHAPES = {
  'C':   { frets: [-1, 3, 2, 0, 1, 0], fingers: [0, 3, 2, 0, 1, 0] },
  'Cmaj7':{ frets: [-1, 3, 2, 0, 0, 0], fingers: [0, 3, 2, 0, 0, 0] },
  'C7':  { frets: [-1, 3, 2, 3, 1, 0], fingers: [0, 3, 2, 4, 1, 0] },
  'Cm':  { frets: [-1, 3, 5, 5, 4, 3], baseFret: 3, barre: 1 },
  'D':   { frets: [-1, -1, 0, 2, 3, 2], fingers: [0, 0, 0, 1, 3, 2] },
  'Dm':  { frets: [-1, -1, 0, 2, 3, 1], fingers: [0, 0, 0, 2, 3, 1] },
  'D7':  { frets: [-1, -1, 0, 2, 1, 2], fingers: [0, 0, 0, 2, 1, 3] },
  'Dmaj7':{ frets: [-1, -1, 0, 2, 2, 2], fingers: [0, 0, 0, 1, 1, 1] },
  'Dsus4':{ frets: [-1, -1, 0, 2, 3, 3], fingers: [0, 0, 0, 1, 2, 3] },
  'E':   { frets: [0, 2, 2, 1, 0, 0], fingers: [0, 2, 3, 1, 0, 0] },
  'Em':  { frets: [0, 2, 2, 0, 0, 0], fingers: [0, 2, 3, 0, 0, 0] },
  'E7':  { frets: [0, 2, 0, 1, 0, 0], fingers: [0, 2, 0, 1, 0, 0] },
  'Em7': { frets: [0, 2, 0, 0, 0, 0], fingers: [0, 2, 0, 0, 0, 0] },
  'F':   { frets: [1, 3, 3, 2, 1, 1], baseFret: 1, barre: 1 },
  'Fmaj7':{ frets: [-1, -1, 3, 2, 1, 0], fingers: [0, 0, 3, 2, 1, 0] },
  'F#m': { frets: [2, 4, 4, 2, 2, 2], baseFret: 2, barre: 1 },
  'G':   { frets: [3, 2, 0, 0, 0, 3], fingers: [2, 1, 0, 0, 0, 3] },
  'G7':  { frets: [3, 2, 0, 0, 0, 1], fingers: [3, 2, 0, 0, 0, 1] },
  'Gm':  { frets: [3, 5, 5, 3, 3, 3], baseFret: 3, barre: 1 },
  'A':   { frets: [-1, 0, 2, 2, 2, 0], fingers: [0, 0, 1, 2, 3, 0] },
  'Am':  { frets: [-1, 0, 2, 2, 1, 0], fingers: [0, 0, 2, 3, 1, 0] },
  'A7':  { frets: [-1, 0, 2, 0, 2, 0], fingers: [0, 0, 2, 0, 3, 0] },
  'Am7': { frets: [-1, 0, 2, 0, 1, 0], fingers: [0, 0, 2, 0, 1, 0] },
  'Asus4':{ frets: [-1, 0, 2, 2, 3, 0], fingers: [0, 0, 1, 2, 3, 0] },
  'B':   { frets: [-1, 2, 4, 4, 4, 2], baseFret: 2, barre: 1 },
  'Bm':  { frets: [-1, 2, 4, 4, 3, 2], baseFret: 2, barre: 1 },
  'B7':  { frets: [-1, 2, 1, 2, 0, 2], fingers: [0, 2, 1, 3, 0, 4] },
  'Bb':  { frets: [-1, 1, 3, 3, 3, 1], baseFret: 1, barre: 1 },
};

// Normalizuje nazwę akordu do klucza w bazie (usuwa bas po '/', zamienia H->B).
function normalize(chord) {
  let c = chord.split('/')[0].replace(/^H/, 'B');
  if (SHAPES[c]) return c;
  // spróbuj bez rozszerzeń typu 9,11,13,add
  const base = c.match(/^([A-G][#b]?m?)/);
  if (base && SHAPES[base[1]]) return base[1];
  return null;
}

// Zwraca SVG diagramu akordu, albo null gdy nie znamy kształtu.
export function chordDiagram(chord, opts = {}) {
  const key = normalize(chord);
  if (!key) return null;
  const shape = SHAPES[key];
  const { frets, fingers = [], baseFret = 1, barre = 0 } = shape;

  const W = 90, H = 112;
  const left = 14, top = 24, right = 76, bottom = 96;
  const strings = 6, fretsShown = 4;
  const dx = (right - left) / (strings - 1);
  const dy = (bottom - top) / fretsShown;
  const dotColor = opts.dotColor || '#e2564a';
  const line = opts.lineColor || 'currentColor';

  let svg = `<svg viewBox="0 0 ${W} ${H}" class="chord-svg" role="img" aria-label="Akord ${chord}">`;
  svg += `<text x="${W / 2}" y="14" text-anchor="middle" class="chord-name">${chord}</text>`;

  // struny (pionowe)
  for (let s = 0; s < strings; s++) {
    const x = left + s * dx;
    svg += `<line x1="${x}" y1="${top}" x2="${x}" y2="${bottom}" stroke="${line}" stroke-width="1"/>`;
  }
  // progi (poziome)
  for (let f = 0; f <= fretsShown; f++) {
    const y = top + f * dy;
    const w = f === 0 && baseFret === 1 ? 3 : 1; // siodełko
    svg += `<line x1="${left}" y1="${y}" x2="${right}" y2="${y}" stroke="${line}" stroke-width="${w}"/>`;
  }
  // numer progu przy barre
  if (baseFret > 1) {
    svg += `<text x="${left - 6}" y="${top + dy - 4}" text-anchor="end" class="chord-fret">${baseFret}</text>`;
  }
  // barre (poprzeczka)
  if (barre) {
    const y = top + (1 - 0.5) * dy;
    svg += `<line x1="${left}" y1="${y}" x2="${right}" y2="${y}" stroke="${dotColor}" stroke-width="7" stroke-linecap="round" opacity="0.85"/>`;
  }

  for (let s = 0; s < strings; s++) {
    const x = left + s * dx;
    const fr = frets[s];
    if (fr === -1) {
      svg += `<text x="${x}" y="${top - 6}" text-anchor="middle" class="chord-mark">×</text>`;
    } else if (fr === 0) {
      svg += `<circle cx="${x}" cy="${top - 10}" r="3" fill="none" stroke="${line}" stroke-width="1.2"/>`;
    } else {
      const rel = fr - baseFret + 1;
      if (rel >= 1 && rel <= fretsShown) {
        const y = top + (rel - 0.5) * dy;
        svg += `<circle cx="${x}" cy="${y}" r="6" fill="${dotColor}"/>`;
        if (fingers[s]) svg += `<text x="${x}" y="${y + 3.5}" text-anchor="middle" class="chord-finger">${fingers[s]}</text>`;
      }
    }
  }
  svg += `</svg>`;
  return svg;
}

export function hasShape(chord) {
  return normalize(chord) !== null;
}
