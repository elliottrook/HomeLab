"""Small localhost-only intake prototype using the Python standard library."""

from __future__ import annotations

import argparse
import cgi
import html
import io
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from .intake import preview
from .manifest import ManifestError, write_candidate

FORM = """<!doctype html><meta charset=utf-8><title>Aster Wiki intake</title>
<style>body{font:16px system-ui;max-width:54rem;margin:2rem auto;padding:0 1rem}label{display:block;margin:.8rem 0}input,select{width:100%;padding:.45rem}button{padding:.6rem 1rem}pre{white-space:pre-wrap;background:#f3f3f3;padding:1rem}</style>
<h1>Add a private knowledge source</h1><p>Preview is read-only. Acceptance creates a candidate for the collector; it does not publish content.</p>
<form method=post action=/preview enctype=multipart/form-data>
<label>Type <select name=kind><option>web</option><option>git</option><option>manual</option></select></label>
<label>Title <input required name=title></label><label>Source ID <input name=source_id></label>
<label>Publisher/owner <input name=owner></label><label>HTTPS URL or upload label <input name=location></label>
<label>Boundary <input name=boundary placeholder="exact URL, path prefix, or comma-separated repository paths"></label>
<label>Manual upload (PDF, HTML, Markdown or text; prototype limit 64 KiB) <input type=file name=manual_file></label>
<label>License <select name=license_status><option>review-required</option><option>permitted</option><option>metadata-only</option></select></label>
<button>Preview source</button></form>"""


def parse_submission(content_type: str, body: bytes) -> tuple[dict[str, str], bytes | None]:
    """Parse one bounded form submission without requiring a listening socket."""
    upload = None
    if content_type.startswith("multipart/form-data"):
        fields = cgi.FieldStorage(
            fp=io.BytesIO(body),
            headers={"content-type": content_type, "content-length": str(len(body))},
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type,
                     "CONTENT_LENGTH": str(len(body))}, keep_blank_values=True,
        )
        form = {}
        for key in fields.keys():
            item = fields[key]
            if isinstance(item, list):
                item = item[-1]
            if key == "manual_file" and item.filename:
                upload = item.file.read(64 * 1024 + 1)
                if len(upload) > 64 * 1024:
                    raise ManifestError("manual too large for prototype")
                form["filename"] = Path(item.filename).name
            elif item.value is not None:
                form[key] = str(item.value)
        return form, upload
    return ({key: values[-1] for key, values in parse_qs(body.decode()).items()}, None)


class Handler(BaseHTTPRequestHandler):
    state_root = Path("state")
    wiki_root = Path(".")
    previews: dict[str, dict] = {}

    def reply(self, status: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/":
            self.reply(200, FORM + "<p><a href='/wiki/'>Browse offline wiki</a></p>")
        elif self.path == "/wiki/":
            self.reply(200, self.render_markdown(self.wiki_root / "docs/index.md"))
        elif self.path.startswith("/wiki/"):
            relative = self.path[len("/wiki/"):].strip("/")
            if not relative or ".." in relative.split("/"):
                self.reply(400, "<h1>Invalid path</h1>")
                return
            source = self.wiki_root / "docs" / relative
            if source.is_dir():
                source /= "index.md"
            if source.suffix != ".md":
                source = source.with_suffix(".md")
            try:
                source.resolve().relative_to((self.wiki_root / "docs").resolve())
            except ValueError:
                self.reply(400, "<h1>Invalid path</h1>")
                return
            if not source.is_file():
                self.reply(404, "<h1>Not found</h1>")
                return
            self.reply(200, self.render_markdown(source))
        elif self.path == "/healthz":
            self.reply(200, '{"status":"ok","mode":"prototype"}\n', "application/json")
        else:
            self.reply(404, "<h1>Not found</h1>")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 64 * 1024:
            self.reply(413, "<h1>Request too large</h1>")
            return
        body = self.rfile.read(length)
        try:
            form, upload = parse_submission(self.headers.get("Content-Type", ""), body)
            if self.path == "/preview":
                result = preview(form, upload)
                token = result["source"]["id"]
                self.previews[token] = result
                rendered = html.escape(json.dumps(result, indent=2, sort_keys=True))
                self.reply(200, f"<h1>Acceptance preview</h1><pre>{rendered}</pre><form method=post action=/accept><input type=hidden name=token value='{html.escape(token)}'><button>Accept source candidate</button></form><p><a href='/'>Cancel</a></p>")
            elif self.path == "/accept":
                result = self.previews.pop(form.get("token", ""), None)
                if result is None:
                    raise ManifestError("preview expired or unknown")
                path = write_candidate(self.state_root, result["source"])
                self.reply(202, f"<h1>Candidate queued</h1><p>{html.escape(path.name)}</p>")
            else:
                self.reply(404, "<h1>Not found</h1>")
        except (ManifestError, ValueError) as exc:
            self.reply(400, f"<h1>Invalid source</h1><p>{html.escape(str(exc))}</p>")

    def log_message(self, format: str, *args: object) -> None:
        return

    @staticmethod
    def render_markdown(path: Path) -> str:
        """Render a deliberately small, no-HTML Markdown subset."""
        rendered = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = html.escape(raw)
            if line.startswith("# "):
                rendered.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                rendered.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("- "):
                rendered.append(f"<p>• {line[2:]}</p>")
            elif line.startswith("&gt; "):
                rendered.append(f"<blockquote>{line[5:]}</blockquote>")
            elif line:
                line = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"<a href='/wiki/\2'>\1</a>", line)
                rendered.append(f"<p>{line}</p>")
        return "<!doctype html><meta charset=utf-8><title>HomeLab Wiki</title><style>body{font:16px system-ui;max-width:54rem;margin:2rem auto;padding:0 1rem}blockquote{border-left:3px solid #777;padding-left:1rem}</style><nav><a href='/wiki/'>Wiki home</a> · <a href='/'>Add source</a></nav>" + "".join(rendered)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    Handler.state_root = args.state_root or args.wiki_root / "state"
    Handler.wiki_root = args.wiki_root.resolve()
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
