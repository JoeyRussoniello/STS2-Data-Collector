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


with http.server.HTTPServer(("", PORT), Handler) as server:
    print(f"\n  ✦ Eldritch Archive serving at http://localhost:{PORT}\n")
    server.serve_forever()
