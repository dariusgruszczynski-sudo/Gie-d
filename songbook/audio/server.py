#!/usr/bin/env python3
"""Mikroserwis wykrywania akordów (opcjonalny). Wystawia GET /detect?url=…

Główny serwer Śpiewnika (Node) proxuje tu żądania z /api/chords. Trzymany osobno,
bo ma ciężkie zależności (librosa, ffmpeg, yt-dlp) — nie obciąża głównej apki.
"""
import json
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

    def log_message(self, *args):  # cisza w logach
        pass


if __name__ == '__main__':
    print(f'spiewnik-audio nasłuchuje na :{PORT}')
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
