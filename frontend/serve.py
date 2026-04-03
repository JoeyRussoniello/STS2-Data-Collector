"""Serve the Eldritch Archive frontend."""

import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".mjs": "application/javascript",
    }

    def do_GET(self):
        if self.path == "/js/config.js":
            api_url = os.environ.get(
                "STS2_API_URL", "https://sts2-data-collector-production.up.railway.app"
            ).rstrip("/")
            body = f"globalThis.__STS2_API_URL__ = {api_url!r};\n".encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


with http.server.HTTPServer(("", PORT), Handler) as server:
    print(f"\n  ✦ Eldritch Archive serving at http://localhost:{PORT}\n")
    server.serve_forever()
