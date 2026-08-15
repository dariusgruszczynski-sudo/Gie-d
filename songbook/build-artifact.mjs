// build-artifact.mjs — składa cały frontend (moduły JS + CSS + HTML) w JEDEN
// samowystarczalny plik `artifact/spiewnik.html`, gotowy do opublikowania jako
// Artefakt na claude.ai (dostępny z dowolnego urządzenia po zalogowaniu do Claude).
//
// Uruchomienie:  node build-artifact.mjs
//
// Uwaga: wersja hostowana nie ma backendu, więc automatyczne pobieranie tekstu
// i import po URL są nieaktywne (aplikacja podpowiada, by użyć wklejania ręcznego).
// Wszystko inne — listy, chwyty, tabulatury, transpozycja, diagramy, style,
// eksport/import kopii — działa w pełni po stronie przeglądarki.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUB = path.join(__dirname, 'public');
const read = (p) => fs.readFileSync(path.join(PUB, p), 'utf8');

// --- 1. Przygotuj moduły JS: usuń import/export i rozwiąż kolizje nazw ---
function stripModule(src) {
  return src
    .replace(/^\s*import\s+[^;]*;\s*$/gm, '')  // usuń linie import
    .replace(/^export\s+/gm, '');              // zamień 'export X' na 'X'
}

// chordpro.js eksportuje `render` (aliasowane w app.js jako renderChordPro)
// oraz ma wewnętrzną funkcję `esc` — obie kolidują z nazwami w app.js.
let chordpro = stripModule(read('js/chordpro.js'))
  .replace(/\bfunction render\(/, 'function renderChordPro(')
  .replace(/\besc\b/g, 'escCP');

let chords = stripModule(read('js/chords.js'));
let store = stripModule(read('js/store.js'));
let syncjs = stripModule(read('js/sync.js'));
let searchClient = stripModule(read('js/search-client.js'));
let appjs = stripModule(read('js/app.js'));

const bundle = [
  '/* ==== chordpro.js ==== */', chordpro,
  '/* ==== chords.js ==== */', chords,
  '/* ==== store.js ==== */', store,
  '/* ==== sync.js ==== */', syncjs,
  '/* ==== search-client.js ==== */', searchClient,
  '/* ==== app.js ==== */', appjs,
].join('\n');

// --- 2. Wyciągnij zawartość <body> z index.html (bez znacznika <script>) ---
const html = read('index.html');
const bodyInner = html
  .match(/<body>([\s\S]*)<\/body>/)[1]
  .replace(/<script[\s\S]*?<\/script>/g, '')
  .trim();

const css = read('css/styles.css');

// --- 3. Złóż samowystarczalny plik (bez <html>/<head>/<body> — dodaje je Artefakt) ---
const out = `<title>🎵 Śpiewnik</title>
<style>
${css}
</style>

${bodyInner}

<script type="module">
${bundle}
</script>
`;

const dir = path.join(__dirname, 'artifact');
fs.mkdirSync(dir, { recursive: true });
const outPath = path.join(dir, 'spiewnik.html');
fs.writeFileSync(outPath, out, 'utf8');
console.log('Zapisano', outPath, '(' + Math.round(out.length / 1024) + ' KB)');
