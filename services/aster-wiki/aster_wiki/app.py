"""Small localhost-only intake prototype using the Python standard library."""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from .intake import preview
from .manifest import ManifestError, load_manifest, write_candidate, write_control_candidate, write_upload

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


def source_dashboard(wiki_root: Path, state_root: Path) -> list[dict]:
    """Return bounded accepted/source-state rows without mutating pipeline state."""
    manifest_path = wiki_root / "sources/sources.json"
    sources = load_manifest(manifest_path)["sources"] if manifest_path.is_file() else []
    lock_path = wiki_root / "sources/accepted-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
    accepted = {item["source_id"]: item for item in lock.get("sources", [])}
    database = state_root / "pipeline.sqlite3"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True) if database.is_file() else None
    try:
        rows = []
        for source in sources:
            latest = None
            if connection:
                latest = connection.execute(
                    "SELECT i.stage,i.status,i.reason,i.updated_at,r.id "
                    "FROM items i JOIN runs r ON r.id=i.run_id WHERE i.source_id=? "
                    "ORDER BY i.updated_at DESC,r.id DESC LIMIT 1", (source["id"],)
                ).fetchone()
            item = accepted.get(source["id"], {})
            rows.append({
                "id": source["id"], "enabled": source["enabled"],
                "accepted_sha256": item.get("normalized_sha256"),
                "last_stage": latest[0] if latest else None,
                "last_status": latest[1] if latest else None,
                "last_reason": latest[2] if latest else None,
                "last_updated": latest[3] if latest else None,
                "last_run": latest[4] if latest else None,
            })
        return rows
    finally:
        if connection:
            connection.close()


def source_history(state_root: Path, source_id: str, limit: int = 20) -> list[dict]:
    database = state_root / "pipeline.sqlite3"
    if not database.is_file():
        return []
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT r.id AS run_id,r.status AS run_status,i.stage,i.status,i.reason,"
            "i.input_sha256,i.updated_at FROM items i JOIN runs r ON r.id=i.run_id "
            "WHERE i.source_id=? ORDER BY i.updated_at DESC,r.id DESC LIMIT ?",
            (source_id, max(1, min(limit, 100))),
        ).fetchall()
        result = []
        previous = None
        for row in rows:
            item = dict(row)
            digest = item["input_sha256"]
            item["changed_from_next"] = bool(digest and previous and digest != previous)
            if digest:
                previous = digest
            result.append(item)
        return result
    finally:
        connection.close()


def parse_submission(content_type: str, body: bytes) -> tuple[dict[str, str], bytes | None]:
    """Parse one bounded form submission without requiring a listening socket."""
    upload = None
    if content_type.startswith("multipart/form-data"):
        message = BytesParser(policy=policy.HTTP).parsebytes(
            b"Content-Type: " + content_type.encode("ascii", "strict") + b"\r\n"
            b"MIME-Version: 1.0\r\n\r\n" + body
        )
        if not message.is_multipart() or message.defects:
            raise ManifestError("invalid multipart form")
        form: dict[str, str] = {}
        for item in message.iter_parts():
            if item.get_content_disposition() != "form-data":
                continue
            key = item.get_param("name", header="content-disposition")
            if not key:
                continue
            filename = item.get_filename()
            payload = item.get_payload(decode=True) or b""
            if key == "manual_file" and filename:
                if len(payload) > 64 * 1024:
                    raise ManifestError("manual too large for prototype")
                upload = payload
                form["filename"] = Path(filename).name
            elif filename is None:
                charset = item.get_content_charset() or "utf-8"
                try:
                    form[key] = payload.decode(charset)
                except (LookupError, UnicodeDecodeError) as exc:
                    raise ManifestError("invalid form field encoding") from exc
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
            self.reply(200, FORM + "<p><a href='/wiki/'>Browse offline wiki</a> · <a href='/sources'>Source dashboard</a></p>")
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
        elif self.path == "/sources":
            sources = source_dashboard(self.wiki_root, self.state_root)
            candidates = sorted(path.name for path in (self.state_root / "candidates").glob("*.json")) if (self.state_root / "candidates").is_dir() else []
            rows = "".join(
                f"<tr><td><a href='/sources/{html.escape(item['id'])}'>{html.escape(item['id'])}</a></td>"
                f"<td>{'enabled' if item['enabled'] else 'paused'}</td><td>{html.escape(item['last_status'] or 'never')}</td>"
                f"<td>{html.escape((item['accepted_sha256'] or 'none')[:12])}</td>"
                + "<td><form method=post action=/control>" + " ".join(f"<button name=operation value='{op}'>{op}</button>" for op in ("pause","resume","retry","retire"))
                + f"<input type=hidden name=source_id value='{html.escape(item['id'])}'></form></td></tr>"
                for item in sources
            )
            self.reply(200, "<h1>Source status</h1><table><tr><th>Source</th><th>State</th><th>Last result</th><th>Accepted hash</th><th>Queue control</th></tr>" + rows + "</table><h2>Pending candidates</h2><pre>" + html.escape("\n".join(candidates) or "none") + "</pre>")
        elif self.path.startswith("/sources/"):
            source_id = self.path[len("/sources/"):].strip("/")
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", source_id):
                self.reply(400, "<h1>Invalid source</h1>")
                return
            history = source_history(self.state_root, source_id)
            rows = "".join(
                "<tr>" + "".join(f"<td>{html.escape(str(item[key] or ''))}</td>" for key in
                    ("run_id", "run_status", "stage", "status", "reason", "updated_at"))
                + f"<td>{html.escape((item['input_sha256'] or 'none')[:16])}</td>"
                + f"<td>{'changed' if item['changed_from_next'] else 'same/unknown'}</td></tr>"
                for item in history
            )
            self.reply(200, f"<h1>History: {html.escape(source_id)}</h1><p>Hashes compare exact retained inputs; content is not exposed here.</p><table><tr><th>Run</th><th>Run state</th><th>Stage</th><th>Item state</th><th>Reason</th><th>Updated</th><th>Input hash</th><th>Diff</th></tr>{rows}</table><p><a href='/sources'>Back to sources</a></p>")
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
                self.previews[token] = {"result": result, "upload": upload}
                rendered = html.escape(json.dumps(result, indent=2, sort_keys=True))
                self.reply(200, f"<h1>Acceptance preview</h1><pre>{rendered}</pre><form method=post action=/accept><input type=hidden name=token value='{html.escape(token)}'><button>Accept source candidate</button></form><p><a href='/'>Cancel</a></p>")
            elif self.path == "/accept":
                pending = self.previews.pop(form.get("token", ""), None)
                if pending is None:
                    raise ManifestError("preview expired or unknown")
                result = pending["result"]
                if pending["upload"] is not None:
                    write_upload(self.state_root, result["source"], pending["upload"])
                path = write_candidate(self.state_root, result["source"])
                self.reply(202, f"<h1>Candidate queued</h1><p>{html.escape(path.name)}</p>")
            elif self.path == "/control":
                path = write_control_candidate(self.state_root, form.get("source_id", ""), form.get("operation", ""))
                self.reply(202, f"<h1>Control candidate queued</h1><p>{html.escape(path.name)}</p><p>No accepted content or Git history was deleted.</p>")
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
