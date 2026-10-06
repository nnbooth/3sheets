#!/usr/bin/env python3
"""serve.py — preview the site locally with caching turned off, so the browser
always shows the current files.   python3 tools/serve.py   ->  http://127.0.0.1:8765"""
import functools
import http.server
from pathlib import Path


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(NoCache, directory=str(Path(__file__).resolve().parent.parent))
    http.server.ThreadingHTTPServer(("127.0.0.1", 8765), handler).serve_forever()
