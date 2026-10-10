"""Create an internal-only sample release from the accepted static baseline."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil


BANNER = '<div class="tcf-sample-banner" role="status">SAMPLE — NOT FOR PUBLICATION</div>'
STYLE = """<style>
.tcf-sample-banner{position:fixed;z-index:2147483647;top:0;left:0;right:0;
padding:8px 16px;background:#7d1717;color:#fff;font:700 12px/1.4 system-ui;
letter-spacing:.12em;text-align:center}.site-header{top:32px!important}
</style>"""


def build(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError("destination must not already exist")
    required = {"index.html", "styles.css", "script.js", "landscapes.html",
                "flora.html", "contrasts.html", "people.html"}
    missing = sorted(name for name in required if not (source / name).is_file())
    if missing:
        raise ValueError(f"baseline is incomplete: {', '.join(missing)}")
    shutil.copytree(
        source,
        destination,
        symlinks=False,
        ignore=shutil.ignore_patterns("._*", ".DS_Store"),
    )
    for path in destination.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        if BANNER in text:
            raise ValueError(f"sample banner already present in {path.name}")
        text = text.replace("</head>", f"{STYLE}</head>", 1)
        text, replacements = re.subn(r"(<body(?:\s[^>]*)?>)", rf"\1{BANNER}", text, count=1)
        if replacements != 1:
            raise ValueError(f"body element missing from {path.name}")
        path.write_text(text, encoding="utf-8")
    (destination / "SAMPLE-NOT-FOR-PUBLICATION.txt").write_text(
        "This release is for private workflow testing only.\n", encoding="utf-8")
    entries = []
    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        relative = path.relative_to(destination).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  ./{relative}")
    (destination / "MANIFEST.sha256").write_text(
        "\n".join(entries) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    build(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
