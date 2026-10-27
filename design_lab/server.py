"""Loopback-only server for the fixed public study bundle."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
MIME = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.mjs':'text/javascript; charset=utf-8',
        '.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.dxf':'application/dxf','.scad':'text/plain; charset=utf-8'}


def public_files(directory):
    base = ['index.html', 'styles.css', 'model.mjs', 'app.mjs', 'assets/report.json']
    exports = [p.relative_to(directory).as_posix() for p in (directory / 'assets/designs').glob('*')
               if re.fullmatch(r'(baseline|seed-\d{1,10})\.(svg|dxf|scad)', p.name)]
    return tuple(base + sorted(exports))


def make_server(port=8790, web_root=None):
    directory = Path(web_root or ROOT / 'web').resolve()
    allowed = public_files(directory)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass
        def do_GET(self): self.serve(False)
        def do_HEAD(self): self.serve(True)

        def serve(self, head):
            if self.headers.get('Host','') not in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}:
                self.send_error(403); return
            try:
                parsed = urlsplit(self.path)
            except ValueError:
                self.send_error(400); return
            name = 'index.html' if parsed.path == '/' else parsed.path.removeprefix('/')
            if parsed.scheme or parsed.netloc or name not in allowed:
                self.send_error(404); return
            target = directory / name
            try:
                if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(directory):
                    raise FileNotFoundError
                with target.open('rb') as source: data = source.read(4_000_001)
                if len(data) > 4_000_000: raise OSError('Public asset exceeds limit')
            except OSError:
                self.send_error(404); return
            self.send_response(200)
            self.send_header('Content-Type', MIME[target.suffix])
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            if not head: self.wfile.write(data)

    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
