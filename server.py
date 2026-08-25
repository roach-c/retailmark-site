#!/usr/bin/env python3
"""Local server for the RetailMark site: serves static files and
collects contact-form submissions into submissions.json."""

import json
import html
import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
SUBMISSIONS_FILE = ROOT / "submissions.json"
PORT = 8000


def load_submissions():
    if not SUBMISSIONS_FILE.exists():
        return []
    with open(SUBMISSIONS_FILE, "r") as f:
        return json.load(f)


def save_submission(record):
    submissions = load_submissions()
    submissions.append(record)
    with open(SUBMISSIONS_FILE, "w") as f:
        json.dump(submissions, f, indent=2)


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/submit":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        message = (data.get("message") or "").strip()
        if not name or not email or not message:
            self._send_json(400, {"error": "name, email, and message are required"})
            return

        record = {
            "id": len(load_submissions()) + 1,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "name": name,
            "email": email,
            "company": (data.get("company") or "").strip(),
            "message": message,
        }
        save_submission(record)
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path in ("/admin", "/admin/"):
            self._render_admin()
            return
        # Clean URLs for the interior pages. Most static hosts do this for you;
        # this dev server does not, so /glossary would 404 locally and only
        # locally, which is the worst kind of difference to debug later.
        pretty = self.path.strip("/")
        if pretty and "." not in pretty and (ROOT / f"{pretty}.html").exists():
            self.path = f"/{pretty}.html"
        return super().do_GET()

    def _render_admin(self):
        submissions = load_submissions()
        rows = "".join(
            f"<tr><td>{s['id']}</td><td>{html.escape(s['timestamp'])}</td>"
            f"<td>{html.escape(s['name'])}</td><td>{html.escape(s['email'])}</td>"
            f"<td>{html.escape(s['company'])}</td><td>{html.escape(s['message'])}</td></tr>"
            for s in reversed(submissions)
        )
        page = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>RetailMark — Submissions</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 40px; color: #111; }}
h1 {{ margin-bottom: 4px; }}
p.count {{ color: #6b6b6f; margin-bottom: 24px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #e8e6df; padding: 10px 12px; text-align: left; font-size: 0.9rem; vertical-align: top; }}
th {{ background: #111; color: #e8b923; }}
tr:nth-child(even) {{ background: #faf8f3; }}
</style></head><body>
<h1>Landing Zone — Contact Submissions</h1>
<p class="count">{len(submissions)} total submission(s). Refresh to see new ones.</p>
<table>
<tr><th>ID</th><th>Received</th><th>Name</th><th>Email</th><th>Company</th><th>Message</th></tr>
{rows if rows else '<tr><td colspan="6">No submissions yet.</td></tr>'}
</table>
</body></html>"""
        body = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    import os
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("localhost", PORT), Handler)
    print(f"RetailMark site running at http://localhost:{PORT}")
    print(f"Submissions landing zone (admin view): http://localhost:{PORT}/admin")
    server.serve_forever()
