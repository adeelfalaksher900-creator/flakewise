"""Development server; pass --host 0.0.0.0 only in controlled environments."""
import argparse
import mimetypes
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from api.analyze import handler

PUBLIC = (Path(__file__).resolve().parent / 'public').resolve()
class App(handler):
    def do_GET(self):
        route = unquote(urlsplit(self.path).path)
        target = (PUBLIC / (route.lstrip('/') or 'index.html')).resolve()
        if not target.is_relative_to(PUBLIC) or not target.is_file():
            return self.respond(404, {'error':'Not found.'})
        body = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(target)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    ThreadingHTTPServer((args.host, args.port), App).serve_forever()
