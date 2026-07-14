#!/usr/bin/env python3
"""Shotlist server: serves static HTML + proxies Feishu API calls."""
import http.server
import json
import urllib.request
import os
import socketserver

PORT = 8089
DOCROOT = "/volume1/主目录/Hermes/read/done"

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Multi-threaded HTTP server — handles concurrent requests."""
    daemon_threads = True

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOCROOT, **kwargs)

    def do_POST(self):
        self._proxy_request("POST")

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/api/rebuild":
            self._rebuild()
        elif self.path.startswith("/api/feishu"):
            self._proxy_request("GET")
        else:
            super().do_GET()

    def _proxy_request(self, method):
        # Read body for both GET and POST (query params come via url)
        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length) if length > 0 else b"{}"
        params = json.loads(body_raw)

        feishu_url = params.get("url", "")
        feishu_headers = params.get("headers", {})
        feishu_body = params.get("body", None)

        if not feishu_url:
            self._send_json(400, {"error": "missing url"})
            return

        data_bytes = json.dumps(feishu_body).encode() if feishu_body else None
        req = urllib.request.Request(
            feishu_url,
            data=data_bytes,
            headers={**feishu_headers, "Content-Type": "application/json; charset=utf-8"} if data_bytes else feishu_headers,
            method=params.get("_method", method) if data_bytes else "GET"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self._send_json(200, json.loads(data))
        except Exception as e:
            self._send_json(502, {"error": str(e)})

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _rebuild(self):
        import subprocess
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_html.py")
        # Read feishu_config.json for credentials
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "feishu_config.json")
        env = os.environ.copy()
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    cfg = json.load(f)
                env["FEISHU_APP_SECRET"] = cfg.get("app_secret", "")
            except: pass
        try:
            result = subprocess.run(["python3", script], capture_output=True, text=True, timeout=60, env=env)
            if result.returncode == 0:
                self._send_json(200, {"status": "ok", "output": result.stdout.strip()})
            else:
                self._send_json(500, {"status": "error", "stderr": result.stderr.strip()})
        except Exception as e:
            self._send_json(500, {"status": "error", "stderr": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Shotlist server on :{PORT} (threaded)")
    server.serve_forever()
