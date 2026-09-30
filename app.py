"""Local portfolio server, using only the Python standard library."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from engine import evaluate

ROOT = Path(__file__).parent
DB = ROOT / 'creditlens.db'

def connect():
    conn = sqlite3.connect(DB)
    conn.execute('CREATE TABLE IF NOT EXISTS evaluations (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, inputs TEXT NOT NULL, result TEXT NOT NULL)')
    return conn

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        raw = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/api/history':
            with connect() as conn:
                rows = conn.execute('SELECT id, created_at, inputs, result FROM evaluations ORDER BY id DESC LIMIT 100').fetchall()
            self.send_json(200, [{'id': row[0], 'created_at': row[1], 'inputs': json.loads(row[2]), 'result': json.loads(row[3])} for row in rows])
            return
        paths = {'/': ('index.html', 'text/html'), '/style.css': ('style.css', 'text/css'), '/ui.js': ('ui.js', 'text/javascript')}
        if self.path not in paths:
            self.send_json(404, {'error': 'Not found'})
            return
        name, mime = paths[self.path]
        raw = (ROOT / 'static' / name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.path != '/api/evaluate':
            self.send_json(404, {'error': 'Not found'})
            return
        # Only same-origin browser requests; this demo has no public auth layer.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            self.send_json(403, {'error': 'Cross-origin request rejected'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('Request must contain 1 to 16384 bytes')
            data = json.loads(self.rfile.read(size))
            result = evaluate(data)
        except (ValueError, UnicodeDecodeError) as error:
            self.send_json(400, {'error': str(error)})
            return
        with connect() as conn:
            cursor = conn.execute('INSERT INTO evaluations (created_at, inputs, result) VALUES (?, ?, ?)',
                                  (datetime.now(timezone.utc).isoformat(), json.dumps(data), json.dumps(result)))
            result = dict(result, id=cursor.lastrowid)
        self.send_json(200, result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'CreditLens: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
