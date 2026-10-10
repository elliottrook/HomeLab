"""Bind an approved candidate into the accepted finished brand template."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import shutil

from content import ContentError
from candidate import build_candidate
from store import ContentStore


BANNER = '<div class="tcf-private-candidate">PRIVATE CANDIDATE — NOT PUBLISHED</div>'
BANNER_STYLE = '''<style>.tcf-private-candidate{position:fixed;z-index:2147483647;top:0;left:0;right:0;padding:8px 16px;background:#7d1717;color:#fff;font:700 12px/1.4 system-ui;letter-spacing:.12em;text-align:center}body{padding-top:32px}</style>'''


def _file_manifest(directory: Path) -> None:
    entries = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        entries.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{path.relative_to(directory).as_posix()}")
    (directory / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _capacity(template: Path, site: str, collection: str) -> int:
    text = (template / f"{collection}.html").read_text(encoding="utf-8")
    if site == "contrast":
        return len(re.findall(r'<article class="work(?:\s|\")', text))
    return len(re.findall(r'<article class="(?:lead|work)(?:\s|\")', text))


def build_template_candidate(store: ContentStore, import_root: Path, site: str,
                             template: Path, destination: Path) -> dict:
    required = {"index.html", "styles.css", "script.js", "landscapes.html",
                "flora.html", "contrasts.html", "people.html"}
    if not template.is_dir() or any(not (template / name).is_file() for name in required):
        raise ContentError("accepted brand template is incomplete")

    generic_manifest = build_candidate(store, import_root, site, destination)
    records = generic_manifest["content"]
    by_collection = {name: [] for name in ("landscapes", "flora", "contrasts", "people")}
    for record in records:
        by_collection[record["collection"]].append(record)
    for collection, members in by_collection.items():
        if len(members) > _capacity(template, site, collection):
            shutil.rmtree(destination)
            raise ContentError(f"{collection} exceeds the accepted template capacity")

    shutil.copytree(
        template, destination, dirs_exist_ok=True, symlinks=False,
        ignore=shutil.ignore_patterns("._*", ".DS_Store", "MANIFEST.sha256"),
    )
    payload = []
    annotations = []
    for record in records:
        image = f"{record['id']}-{record['image_sha256'][:12]}.jpg"
        item = {**record, "image": image}
        payload.append(item)
        annotations.append({"image": f"assets/{image}", "text": record["annotation_text"],
                            "x": record["annotation_x"], "y": record["annotation_y"]})

    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    binding = r'''(()=>{const pieces=__DATA__;const groups=pieces.reduce((all,p)=>{(all[p.collection]??=[]).push(p);return all},{});const page=location.pathname.split('/').pop().replace('.html','')||'index';const q=(root,s)=>root.querySelector(s);function bind(card,p){const img=q(card,'img');if(img){img.src='assets/'+p.image;img.alt=p.alt_text}card.dataset.title=p.title;const button=q(card,'button');if(button){button.setAttribute('aria-label','Open '+p.title+' and its story');button.dataset.piece=p.id}const title=q(card,'.work-meta h3,.lead-note h2,.work-story h2');if(title)title.textContent=p.title;const story=q(card,'.piece-story');if(story){story.replaceChildren();const para=document.createElement('p');para.textContent=p.story;story.append(para)}const credit=q(card,'.photo-credit,.credit');if(credit)credit.textContent=p.credit||'Photograph by the site owner'}function collection(){const list=groups[page]||[];const cards=[...document.querySelectorAll(page==='index'?'.never-match':(document.body.classList.contains('collection-page')?'article.work':'main article.lead,main article.work'))];cards.forEach((card,i)=>list[i]?bind(card,list[i]):card.remove())}function home(){const p=(groups.landscapes||[])[0];if(!p)return;if(document.body.classList.contains('collection-page'))return;const hero=document.querySelector('.hero');if(hero){const img=q(hero,'img');if(img){img.src='assets/'+p.image;img.alt=p.alt_text}const title=document.querySelector('.featured-story h2');if(title)title.textContent=p.title;const story=document.querySelector('.featured-story .piece-story');if(story){story.replaceChildren();const para=document.createElement('p');para.textContent=p.story;story.append(para)}}else{const lead=document.querySelector('main article.lead');if(lead)bind(lead,p)}}collection();home()})();'''.replace("__DATA__", data)
    (destination / "candidate-bindings.js").write_text(binding, encoding="utf-8")
    (destination / "annotations.json").write_text(json.dumps({
        "schema_version": 1,
        "brand_id": "closet-fatman" if site == "closet" else "contrasting-frame",
        "annotations": annotations,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if site == "closet":
        (destination / "content.json").write_text(json.dumps({
            "schema_version": 1, "brand_id": "closet-fatman", "pieces": payload,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for page in destination.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        text = text.replace("</head>", BANNER_STYLE + "</head>", 1)
        text = re.sub(r"(<body(?:\s[^>]*)?>)", r"\1" + BANNER, text, count=1)
        text = text.replace("</body>", '<script src="candidate-bindings.js"></script></body>', 1)
        page.write_text(text, encoding="utf-8")
    (destination / "candidate.json").write_text(
        json.dumps(generic_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _file_manifest(destination)
    return generic_manifest
