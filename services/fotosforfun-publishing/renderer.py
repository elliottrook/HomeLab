"""Render an approved growing catalogue into the accepted static template."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil

from model import ContentError, Photo


PLACEHOLDER_NOTICE = "PREVIEW PHOTOGRAPHS — NOT ALISA'S WORK"
SCRIPT_MARKERS = ('<script src="gallery.js"></script>',
                  '<script src="gallery.js" defer></script>')

SAFE_GALLERY_JS = r'''"use strict";
const labels={flowers:"Flowers",macro:"Up close",everyday:"Everyday wonders"};
let photos=[],visible=[],current=0,opener=null;
const gallery=document.querySelector("#gallery"),viewer=document.querySelector("#viewer");
function element(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node}
function photoButton(photo){
 const figure=element("figure","photo");figure.dataset.category=photo.category;
 const button=element("button");button.type="button";button.setAttribute("aria-label",`View ${photo.title}`);
 const imageWrap=element("div","photo-image"),image=document.createElement("img");
 image.src=photo.asset;image.alt=photo.alt;image.loading="lazy";image.style.objectPosition=`${photo.focalX*100}% ${photo.focalY*100}%`;
 imageWrap.append(image,element("span","open-mark","↗"));imageWrap.lastChild.setAttribute("aria-hidden","true");
 const label=element("span","photo-label");label.append(element("span","photo-title",photo.title),element("span","photo-category",labels[photo.category]||photo.category));
 button.append(imageWrap,label);button.addEventListener("click",()=>{opener=button;current=visible.indexOf(photo);show();viewer.showModal();document.body.classList.add("modal-open");document.querySelector("#close").focus()});
 figure.append(button);return figure;
}
function show(){const photo=visible[current],image=document.querySelector("#viewer-image");image.src=photo.asset;image.alt=photo.alt;image.style.objectPosition=`${photo.focalX*100}% ${photo.focalY*100}%`;document.querySelector("#viewer-title").textContent=photo.title;document.querySelector("#viewer-category").textContent=labels[photo.category]||photo.category;document.querySelector("#viewer-position").textContent=`${current+1} / ${visible.length}`;const credit=document.querySelector("#viewer-credit");credit.textContent=photo.credit?`Photograph by ${photo.credit}`:"Photograph by Alisa";document.querySelector("#previous").disabled=visible.length<2;document.querySelector("#next").disabled=visible.length<2}
async function start(){
 const response=await fetch("gallery-data.json",{credentials:"same-origin"});if(!response.ok)throw new Error("Gallery data unavailable");photos=await response.json();visible=photos.slice();gallery.replaceChildren(...photos.map(photoButton));document.querySelector("#count").textContent=`${photos.length} photograph${photos.length===1?"":"s"}`;
 document.querySelectorAll("[data-filter]").forEach(button=>button.addEventListener("click",()=>{const filter=button.dataset.filter;document.querySelectorAll("[data-filter]").forEach(item=>item.setAttribute("aria-pressed",String(item===button)));visible=photos.filter(photo=>filter==="all"||photo.category===filter);document.querySelectorAll(".photo").forEach(item=>item.hidden=filter!=="all"&&item.dataset.category!==filter);document.querySelector("#count").textContent=`${visible.length} photograph${visible.length===1?"":"s"}`}));
}
document.querySelector("#close").addEventListener("click",()=>viewer.close());viewer.addEventListener("close",()=>{document.body.classList.remove("modal-open");if(opener)opener.focus()});document.querySelector("#previous").addEventListener("click",()=>{current=(current-1+visible.length)%visible.length;show()});document.querySelector("#next").addEventListener("click",()=>{current=(current+1)%visible.length;show()});
start().catch(()=>{gallery.replaceChildren(element("p","gallery-error","The photographs could not be loaded."));document.querySelector("#count").textContent="Gallery unavailable"});
'''


def write_manifest(root: Path) -> str:
    lines = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        relative = path.relative_to(root).as_posix()
        lines.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{relative}")
    manifest = ("\n".join(lines) + "\n").encode()
    (root / "MANIFEST.sha256").write_bytes(manifest)
    return sha256(manifest).hexdigest()


def catalogue_digest(photos: list[Photo]) -> str:
    payload = [photo.public_payload() for photo in photos]
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()).hexdigest()


def render(template: Path, destination: Path, photos: list[Photo], imports_root: Path,
           *, allow_samples: bool = False) -> dict[str, object]:
    if destination.exists():
        raise ContentError("candidate destination already exists")
    index = template / "index.html"
    if not index.is_file() or not (template / "gallery.js").is_file():
        raise ContentError("approved template is incomplete")
    source_html = index.read_text(encoding="utf-8")
    if ('id="gallery"' not in source_html
            or not any(marker in source_html for marker in SCRIPT_MARKERS)):
        raise ContentError("approved template hooks are missing")
    if not photos:
        raise ContentError("candidate requires at least one photograph")
    ids = [photo.id for photo in photos]
    if len(ids) != len(set(ids)):
        raise ContentError("candidate contains duplicate photograph ids")
    for photo in photos:
        photo.validate()
        if photo.retired:
            raise ContentError("candidate contains a retired photograph")
        if photo.sample and not allow_samples:
            raise ContentError("sample photographs cannot become a release")
    shutil.copytree(template, destination, symlinks=False)
    assets = destination / "assets"
    for photo in photos:
        source = imports_root / photo.asset_path.removeprefix("imports/")
        if not source.is_file() or source.is_symlink():
            shutil.rmtree(destination)
            raise ContentError(f"approved image is missing: {photo.id}")
        if sha256(source.read_bytes()).hexdigest() != photo.image_sha256:
            shutil.rmtree(destination)
            raise ContentError(f"approved image checksum changed: {photo.id}")
        shutil.copyfile(source, assets / f"photo-{photo.id}.jpg")
    payload = [photo.public_payload() for photo in photos]
    (destination / "gallery-data.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (destination / "gallery.js").write_text(SAFE_GALLERY_JS, encoding="utf-8")
    html = source_html.replace("hello@fotosforfun.com", "hello@fotosforfun.ca")
    if any(photo.sample for photo in photos):
        banner = (f'<p class="preview-disclosure" role="note">'
                  f'{PLACEHOLDER_NOTICE}</p>')
        html = html.replace("<body>", "<body>" + banner, 1)
    (destination / "index.html").write_text(html, encoding="utf-8")
    catalogue_sha256 = catalogue_digest(photos)
    metadata = {"site": "fotosforfun", "catalogueSha256": catalogue_sha256,
                "photoCount": len(photos), "samples": any(photo.sample for photo in photos)}
    (destination / "candidate.json").write_text(
        json.dumps(metadata, sort_keys=True), encoding="utf-8")
    manifest_sha256 = write_manifest(destination)
    return {**metadata, "manifestSha256": manifest_sha256}
