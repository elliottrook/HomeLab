#!/usr/bin/env python3
"""Validate the approved frontend against the safe catalogue renderer."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile

from model import Photo
from renderer import PLACEHOLDER_NOTICE, render
from release import verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("sample_image", type=Path)
    arguments = parser.parse_args()
    payload = arguments.sample_image.read_bytes()
    digest = sha256(payload).hexdigest()
    sample = Photo(
        id="template-validation",
        title="Template validation photograph",
        category="flowers",
        alt_text="A temporary credited preview photograph used to validate the template",
        asset_path=f"imports/fotosforfun/template-validation/{digest}.jpg",
        image_sha256=digest,
        width=1200,
        height=800,
        sort_order=10,
        rights="licensed",
        rights_note="Existing credited design stand-in; validation only",
        credit="Credited preview source",
        sample=True,
    )
    with tempfile.TemporaryDirectory(prefix="fotosforfun-template-") as temporary:
        root = Path(temporary)
        source = root / sample.asset_path.removeprefix("imports/")
        source.parent.mkdir(parents=True)
        shutil.copyfile(arguments.sample_image, source)
        candidate = root / "candidate"
        result = render(arguments.template, candidate, [sample], root,
                        allow_samples=True)
        assert verify_manifest(candidate) == result["manifestSha256"]
        html = (candidate / "index.html").read_text(encoding="utf-8")
        script = (candidate / "gallery.js").read_text(encoding="utf-8")
        assert PLACEHOLDER_NOTICE in html
        assert "hello@fotosforfun.ca" in html and "hello@fotosforfun.com" not in html
        assert "innerHTML" not in script and "textContent" in script
    print("approved template validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
