#!/usr/bin/env python3
"""Mikroserwis wykrywania akordów (opcjonalny). Wystawia GET /detect?url=…

Główny serwer Śpiewnika (Node) proxuje tu żądania z /api/chords. Trzymany osobno,
bo ma ciężkie zależności (librosa, ffmpeg, yt-dlp) — nie obciąża głównej apki.
"""
import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import detect

PORT = 8100


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            return self._send(200, {'ok': True, 'service': 'spiewnik-audio'})
        if parsed.path == '/detect':
            qs = parse_qs(parsed.query)
            url = (qs.get('url') or [''])[0].strip()
            if not url:
                return self._send(400, {'ok': False, 'error': 'Podaj parametr url.'})
            try:
                return self._send(200, detect.detect(url))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {'ok': False, 'error': str(e)})
        return self._send(404, {'ok': False, 'error': 'Nieznany endpoint.'})

    def do_POST(self):
        parsed = urlparse(self.path)
        # Wgrany plik audio (mp3/wav/m4a…) — analiza bez YouTube (omija bot-check).
        if parsed.path == '/detect':
            try:
                length = int(self.headers.get('Content-Length') or 0)
            except ValueError:
                length = 0
            if length <= 0:
                return self._send(400, {'ok': False, 'error': 'Pusty plik audio.'})
            if length > 80 * 1024 * 1024:
                return self._send(413, {'ok': False, 'error': 'Plik za duży (max 80 MB). Użyj mp3/m4a.'})
            qs = parse_qs(parsed.query)
            name = (qs.get('name') or [''])[0]
            ext = os.path.splitext(name)[1].lower() or '.bin'
            if ext not in ('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.opus', '.webm'):
                ext = '.bin'
            tmp = tempfile.mkdtemp(prefix='spiewnik_upload_')
            path = os.path.join(tmp, 'audio' + ext)
            try:
                remaining = length
                with open(path, 'wb') as f:
                    while remaining > 0:
                        chunk = self.rfile.read(min(65536, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                return self._send(200, detect.detect(path))
            except Exception as e:  # noqa: BLE001
                return self._send(502, {'ok': False, 'error': str(e)})
            finally:
                try:
                    for f in os.listdir(tmp):
                        os.remove(os.path.join(tmp, f))
                    os.rmdir(tmp)
                except OSError:
                    pass
        return self._send(404, {'ok': False, 'error': 'Nieznany endpoint.'})

    def log_message(self, *args):  # cisza w logach
        pass


if __name__ == '__main__':
    print(f'spiewnik-audio nasłuchuje na :{PORT}')
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
