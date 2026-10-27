from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlsplit
from flakewise.analyzer import analyze, InputError

MAX_BODY = 3 * 1024 * 1024

def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('Duplicate JSON key')
        out[key] = value
    return out

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def respond(self, status, obj):
        body = json.dumps(obj, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        if urlsplit(self.path).path != '/api/analyze':
            return self.respond(404, {'error': 'Not found.'})
        origin = self.headers.get('Origin')
        if origin:
            try:
                parsed = urlsplit(origin)
                same = parsed.scheme in {'http','https'} and parsed.netloc == self.headers.get('Host') and parsed.path in {'','/'}
            except ValueError:
                same = False
            if not same:
                return self.respond(403, {'error': 'Cross-origin requests are not allowed.'})
        if self.headers.get('Content-Type','').split(';',1)[0].strip().lower() != 'application/json':
            return self.respond(415, {'error':'Use application/json.'})
        size = self.headers.get('Content-Length','')
        if not size.isascii() or not size.isdigit() or len(size) > 8:
            return self.respond(400, {'error':'Invalid content length.'})
        size = int(size)
        if size > MAX_BODY:
            return self.respond(413, {'error':'Request is too large.'})
        try:
            data = json.loads(self.rfile.read(size).decode('utf-8'), object_pairs_hook=no_duplicates,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite number')))
            result = analyze(data)
        except (InputError, ValueError, UnicodeDecodeError, RecursionError) as e:
            return self.respond(400, {'error': str(e)[:500] if isinstance(e, InputError) else 'Invalid JSON request.'})
        return self.respond(200, result)
