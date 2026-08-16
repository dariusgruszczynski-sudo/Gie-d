#!/usr/bin/env python3
"""
Wykrywanie akordów gitarowych z nagrania (np. z YouTube).

Pipeline: yt-dlp pobiera audio -> ffmpeg/librosa wczytuje -> chroma (CQT),
zsynchronizowana z uderzeniami -> dopasowanie do 24 szablonów akordów (dur/moll)
-> wygładzenie i scalenie w progresję.

To PRZYBLIŻENIE (typowo ~70-85% na prostym popie/rocku) i punkt startowy do
ręcznej poprawki w edytorze. Wymaga: librosa, numpy, ffmpeg, yt-dlp.

Uwaga prawna: pobieranie audio z YouTube bywa niezgodne z regulaminem serwisu —
używaj do prywatnego użytku i na własną odpowiedzialność.

Użycie:  python3 detect.py "<url albo ścieżka do pliku>"
"""
import json
import os
import subprocess
import sys
import tempfile

PITCHES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def chord_templates():
    """24 szablony: 12 durowych + 12 molowych (wektory 12-elementowe 0/1)."""
    tpl = []
    for root in range(12):
        maj = [0.0] * 12
        for iv in (0, 4, 7):
            maj[(root + iv) % 12] = 1.0
        tpl.append((PITCHES[root], maj))
    for root in range(12):
        minor = [0.0] * 12
        for iv in (0, 3, 7):
            minor[(root + iv) % 12] = 1.0
        tpl.append((PITCHES[root] + 'm', minor))
    return tpl


TEMPLATES = chord_templates()


def match_chord(chroma, threshold=0.12):
    """Dopasowuje 12-elementowy wektor chroma do najbliższego akordu.
    Zwraca nazwę akordu albo 'N' (brak/cisza). Czysty Python — testowalny bez numpy."""
    total = sum(chroma)
    if total <= 0:
        return 'N'
    norm = [c / total for c in chroma]
    # odejmij średnią, by promować wyraźne tercje/kwinty, nie sam głośny bas
    mean = sum(norm) / 12.0
    centered = [c - mean for c in norm]
    best, best_score = 'N', threshold
    for name, vec in TEMPLATES:
        score = sum(centered[i] * vec[i] for i in range(12))
        # normalizacja przez liczbę składników akordu (3)
        score /= 3.0
        if score > best_score:
            best, best_score = name, score
    return best


def _smooth(seq, win=4):
    """Median-ish wygładzanie sekwencji etykiet (usuwa pojedyncze przeskoki)."""
    out = list(seq)
    n = len(seq)
    for i in range(n):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        window = seq[lo:hi]
        # najczęstsza etykieta w oknie
        out[i] = max(set(window), key=window.count)
    return out


def _run_ytdlp(url, workdir, extractor_args=None):
    out = os.path.join(workdir, 'audio.%(ext)s')
    cmd = ['yt-dlp', '-x', '--audio-format', 'wav', '--audio-quality', '0',
           '--no-playlist', '--no-warnings', '-o', out]
    if extractor_args:
        cmd += ['--extractor-args', extractor_args]
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def _download_audio(url, workdir):
    """Pobiera audio przez yt-dlp do pliku wav; zwraca ścieżkę.
    Próbuje najpierw klienta 'android' (często omija bot-check na VPS), potem
    domyślnego. Przy błędzie pokazuje PRAWDZIWY komunikat yt-dlp."""
    attempts = ['youtube:player_client=android', None]
    last = ''
    for ea in attempts:
        proc = _run_ytdlp(url, workdir, ea)
        if proc.returncode == 0:
            for f in os.listdir(workdir):
                if f.endswith('.wav'):
                    return os.path.join(workdir, f)
            last = 'yt-dlp zakończył się sukcesem, ale nie ma pliku wav'
            continue
        msg = (proc.stderr or proc.stdout or '').strip().splitlines()
        last = ' | '.join(msg[-4:]) if msg else f'kod wyjścia {proc.returncode}'
    raise RuntimeError('yt-dlp: ' + last)


def detect(source, max_seconds=240):
    """Zwraca dict z progresją akordów. `source` = URL lub ścieżka do pliku."""
    import numpy as np
    import librosa

    is_url = source.startswith('http://') or source.startswith('https://')
    tmp = None
    try:
        if is_url:
            tmp = tempfile.mkdtemp(prefix='spiewnik_audio_')
            path = _download_audio(source, tmp)
        else:
            path = source

        y, sr = librosa.load(path, sr=22050, mono=True, duration=max_seconds)
        y = librosa.effects.harmonic(y)  # wytnij perkusję/transienty
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        # synchronizacja do uderzeń (mediana chroma na takt)
        if len(beats) > 1:
            csync = librosa.util.sync(chroma, beats, aggregate=np.median)
            times = librosa.frames_to_time(beats, sr=sr)
        else:
            csync = chroma
            times = librosa.frames_to_time(range(chroma.shape[1]), sr=sr)

        labels = []
        for j in range(csync.shape[1]):
            labels.append(match_chord([float(x) for x in csync[:, j]]))
        labels = _smooth(labels, win=3)

        # scal kolejne takie same akordy w segmenty
        segments = []
        for j, lab in enumerate(labels):
            t = float(times[j]) if j < len(times) else 0.0
            if lab == 'N':
                continue
            if segments and segments[-1]['chord'] == lab:
                continue
            segments.append({'time': round(t, 2), 'chord': lab})

        uniq = []
        for s in segments:
            if s['chord'] not in uniq:
                uniq.append(s['chord'])

        return {
            'ok': True,
            'tempo': int(round(float(tempo))) if tempo else 0,
            'chords': segments,
            'unique': uniq,
            'note': 'Wykrywanie automatyczne — przybliżone. Popraw w edytorze.',
        }
    finally:
        if tmp:
            try:
                for f in os.listdir(tmp):
                    os.remove(os.path.join(tmp, f))
                os.rmdir(tmp)
            except OSError:
                pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'ok': False, 'error': 'Podaj URL lub ścieżkę do pliku audio.'}))
        sys.exit(1)
    try:
        print(json.dumps(detect(sys.argv[1]), ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
        sys.exit(1)
