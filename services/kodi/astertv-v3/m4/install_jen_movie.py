#!/usr/bin/env python3
"""Install the bounded Jen M4 movie actions over the accepted v2.0.7 page.

The installer is deliberately hash-pinned and Jen-only.  It adds no resolver:
cast actions use the existing exact-person plugin route and trailers use only
the strictly validated Jellyfin trailer URL helper shipped beside this file.
"""
from __future__ import annotations

import hashlib
import ast
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HOST = "AsterTV-Jen"
ADDONS = Path("/storage/.kodi/addons")
SKIN = ADDONS / "skin.asterhome/1080i/custom_1130_movie.xml"
RUNTIME = ADDONS / "script.asterruntime/aster-global-search-ui22"
MOVIE = RUNTIME / "movie.py"
OVERLAY = RUNTIME / "overlay/custom_1130_movie.xml"
MANIFEST = RUNTIME / "manifest.json"
FAMILY = ADDONS / "script.asterruntime/family-manifest.json"
HELPER = RUNTIME / "jellyfin_trailer_route.py"
DISPATCH = ADDONS / "skin.asterhome/tools/select_dispatch.py"
DISPATCH_OVERLAY = RUNTIME / "overlay/select_dispatch.py"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m4-jen-movie")
STABLE = Path("/storage/.aster-v3/m4")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m4-jen.service")

EXPECTED = {
    SKIN: "42af932055ce5a5edd8dbab2c424225d06a8c4070693f1280e8c54301b6ade8e",
    OVERLAY: "42af932055ce5a5edd8dbab2c424225d06a8c4070693f1280e8c54301b6ade8e",
    MOVIE: "406362f7f6ac0f6833df604176ef40b5406790103863b3bf72aefc2105cc05ce",
    MANIFEST: "6ba1c71374e9c8d402bd6c68fb4ce9423dcf357c0d8d7eecf395336f2a751b0f",
    FAMILY: "f176be124c82362137ef042732b758c5efefff15caa993b813e6e0e0b0150eda",
    DISPATCH: "6b60681bc187c168e5b17abee542a9b2c2ab112e79865273d0f00d4de5b7b44e",
    DISPATCH_OVERLAY: "a3d6f11926c87d69017ca74a12e0ca2722bdf78ef9b8755785f91b871325b508",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall(json.dumps(request).encode())
        reply = json.loads(client.recv(1024 * 1024).decode())
    if "error" in reply:
        raise RuntimeError(f"rpc:{method}:{reply['error'].get('code')}")
    return reply.get("result")


def replace_once(text: str, old: str, new: str, name: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"anchor:{name}:{text.count(old)}")
    return text.replace(old, new, 1)


def patch_xml(text: str) -> str:
    resume_nav = '<onleft>200</onleft><onright>202</onright><onup>400</onup><ondown>500</ondown>'
    text = replace_once(
        text,
        resume_nav,
        '<onleft>200</onleft><onright>203</onright><onup>400</onup><ondown>500</ondown>',
        "resume-navigation",
    )
    back_nav = '<onleft>201</onleft><onright>200</onright><onup>400</onup><ondown>200</ondown>'
    text = replace_once(
        text,
        back_nav,
        '<onleft>203</onleft><onright>200</onright><onup>400</onup><ondown>200</ondown>',
        "back-navigation",
    )
    back_control = '    <control type="image"><left>1705</left><top>35</top>'
    trailer = '''    <control type="image"><left>1055</left><top>520</top><width>96</width><height>90</height><texture border="24" colordiffuse="dd005c46">special://skin/media/ui-panel.png</texture><visible>Control.HasFocus(203)</visible></control><control type="button" id="203"><left>1065</left><top>530</top><width>76</width><height>70</height><label>Trailer</label><textcolor>00000000</textcolor><focusedcolor>00000000</focusedcolor><texturefocus/><texturenofocus/><visible>String.IsEqual(Window.Property(Movie.HasTrailer),true)</visible><enable>String.IsEqual(Window.Property(Movie.Phase),idle)</enable><onclick>SetProperty(AsterMovie.Command,trailer,home)</onclick><onleft>201</onleft><onright>202</onright><onup>400</onup><ondown>500</ondown></control>
    <control type="image"><left>1081</left><top>543</top><width>44</width><height>44</height><texture colordiffuse="asterInk">special://skin/media/player-controls/trailer.png</texture><aspectratio>keep</aspectratio><visible>Control.IsVisible(203)</visible></control>
    <control type="image"><left>1079</left><top>541</top><width>48</width><height>48</height><texture colordiffuse="asterGreen">special://skin/media/player-controls/trailer.png</texture><aspectratio>keep</aspectratio><visible>Control.IsVisible(203) + Control.HasFocus(203)</visible></control>
    <control type="label"><left>1005</left><top>610</top><width>200</width><height>40</height><label>Trailer</label><font>font20</font><textcolor>asterInk</textcolor><align>center</align><visible>Control.IsVisible(203)</visible></control>
'''
    text = replace_once(text, back_control, trailer + back_control, "trailer-control")
    cast = '<control type="list" id="500"><left>145</left>'
    text = replace_once(
        text,
        cast,
        '<control type="list" id="500"><left>145</left>',
        "cast-control",
    )
    marker = '<onleft>500</onleft><onright>500</onright><visible>String.IsEqual(Window.Property(Movie.CastVisible),true)</visible>'
    text = replace_once(
        text,
        marker,
        '<onleft>500</onleft><onright>500</onright><onclick>SetProperty(AsterMovie.Command,person,home)</onclick><visible>String.IsEqual(Window.Property(Movie.CastVisible),true)</visible>',
        "cast-action",
    )
    return text


def patch_movie(text: str) -> str:
    text = replace_once(
        text,
        "import fcntl,json,os,sys,time\nfrom pathlib import Path",
        "import fcntl,json,os,sys,time\nfrom pathlib import Path\nfrom urllib.parse import quote",
        "imports",
    )
    text = replace_once(
        text,
        "from movie_player import MovieSession,MovieUnavailable,READS,read_movie,idle,verify_stage",
        "from movie_player import MovieSession,MovieUnavailable,READS,read_movie,idle,verify_stage\nfrom jellyfin_trailer_route import validated_kodi_youtube_plugin_url",
        "helper-import",
    )
    text = replace_once(
        text,
        "sys.path.insert(0,str(ROOT/'resources/lib'))",
        "sys.path.insert(0,str(ROOT/'resources/lib'))\nsys.path.insert(0,str(ROOT))",
        "runtime-root-path",
    )
    text = replace_once(
        text,
        "require(method in READS|{'Player.Open','Player.Stop','Playlist.Clear'},'movie-rpc-boundary')",
        "require(method in READS|{'Player.Open','Player.Stop','Playlist.Clear','Addons.GetAddonDetails'},'movie-rpc-boundary')",
        "rpc-boundary",
    )
    insert = '''def trailer_route(movie_id):
    try:
        addon=rpc('Addons.GetAddonDetails',{'addonid':'plugin.video.youtube','properties':['enabled']}).get('addon',{})
        if not addon.get('enabled'):return None
        detail=rpc('VideoLibrary.GetMovieDetails',dict(movieid=movie_id,properties=['trailer'])).get('moviedetails',{})
        value=detail.get('trailer','') if isinstance(detail,dict) else ''
        return validated_kodi_youtube_plugin_url(value) if isinstance(value,str) else None
    except MovieUnavailable:return None

'''
    text = replace_once(text, "def enrichment(movie):\n", insert + "def enrichment(movie):\n", "trailer-route")
    text = replace_once(
        text,
        "Playable='true' if value.available else 'false').items():window.setProperty('Movie.'+key,text)",
        "Playable='true' if value.available else 'false',HasTrailer='true' if trailer_route(value.movie_id) else 'false').items():window.setProperty('Movie.'+key,text)",
        "trailer-property",
    )
    text = replace_once(
        text,
        "item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_items.append(item)",
        "item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setProperty('Person',name);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_items.append(item)",
        "person-property",
    )
    text = replace_once(
        text,
        "fullscreen=False;return_until=0",
        "fullscreen=False;return_until=0;external_mode=''",
        "external-state",
    )
    command_anchor = "            if command in ('play','resume') and current==11130 and session.phase=='idle':\n"
    actions = '''            if command=='person' and current==11130 and session.phase=='idle':
                try:
                    person=window.getControl(500).getSelectedItem().getProperty('Person')
                    require(bool(person),'invalid-person')
                    external_mode='person-opening'
                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.astersearch/?actor='+quote(person,safe='')+'",return)')
                except (MovieUnavailable,ValueError,AttributeError):window.setProperty('Movie.Status','That person is currently unavailable.')
            if command=='trailer' and current==11130 and session.phase=='idle':
                try:
                    route=trailer_route(value.movie_id);require(bool(route),'trailer-unavailable');require(idle(rpc),'idle-trailer-required')
                    rpc('Player.Open',{'item':{'file':route}});external_mode='trailer';fullscreen=False
                except (MovieUnavailable,ValueError,KeyError):window.setProperty('Movie.Status','A safe Jellyfin trailer is not available for this title.')
'''
    text = replace_once(text, command_anchor, actions + command_anchor, "commands")
    text = replace_once(
        text,
        "            if session.phase=='playing' and not fullscreen and current==11130:\n                fullscreen=True;xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')",
        "            if (session.phase=='playing' or external_mode=='trailer') and not fullscreen and rpc('Player.GetActivePlayers'):\n                fullscreen=True;xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')\n            if external_mode=='trailer' and not rpc('Player.GetActivePlayers'):\n                external_mode='';fullscreen=False\n                if current!=11130:xbmc.executebuiltin('ActivateWindow(1130)')\n            if external_mode=='person-opening' and current==10025:\n                external_mode='person'\n            if external_mode=='person' and current not in (11130,10025):\n                xbmc.executebuiltin('ActivateWindow(1130)')\n            if external_mode=='person' and current==11130:\n                external_mode=''",
        "external-observation",
    )
    text = replace_once(
        text,
        "if session.phase=='idle' and current!=11130 and time.monotonic()>=return_until:",
        "if session.phase=='idle' and not external_mode and current!=11130 and time.monotonic()>=return_until:",
        "external-lifetime",
    )
    return text


def patch_dispatch(text: str) -> str:
    text = replace_once(
        text,
        "    11129: frozenset((30,)),\n",
        "    11129: frozenset((30,)),\n    11130: frozenset((500, 501)),\n",
        "movie-dynamic-controls",
    )
    anchor = "    if window_id == 11121 and focus_id == 50:\n        return 'RunScript(special://skin/tools/music_data.py,music-player,track)'\n"
    actions = anchor + "    if window_id == 11130 and focus_id == 500:\n        return 'SetProperty(AsterMovie.Command,person,home)'\n    if window_id == 11130 and focus_id == 501:\n        return 'SetProperty(AsterMovie.Command,related,home)'\n"
    return replace_once(text, anchor, actions, "movie-dynamic-actions")


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-host")
    reapply = "--reapply" in sys.argv[1:]
    reinstall = "--reinstall" in sys.argv[1:]
    if not reapply and rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active-player")
    if not reapply and not reinstall and "--check" not in sys.argv[1:] and CHECKPOINT.exists():
        raise RuntimeError("checkpoint-exists")
    check_only = "--check" in sys.argv[1:]
    arguments = [value for value in sys.argv[1:] if value not in ("--check", "--reapply", "--reinstall")]
    source_helper = Path(arguments[0]).resolve() if arguments else Path(__file__).with_name("jellyfin_trailer_route.py")
    helper_data = source_helper.read_bytes()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if digest(originals[path]) != expected:
            raise RuntimeError(f"unexpected-hash:{path}")
    if SKIN.read_bytes() != OVERLAY.read_bytes():
        raise RuntimeError("overlay-drift")

    xml = patch_xml(originals[SKIN].decode()).encode()
    movie = patch_movie(originals[MOVIE].decode()).encode()
    dispatch = patch_dispatch(originals[DISPATCH].decode()).encode()
    dispatch_overlay = patch_dispatch(originals[DISPATCH_OVERLAY].decode()).encode()
    ET.fromstring(xml)
    ast.parse(movie, filename=str(MOVIE))
    ast.parse(dispatch, filename=str(DISPATCH))
    ast.parse(dispatch_overlay, filename=str(DISPATCH_OVERLAY))
    ast.parse(helper_data, filename=str(HELPER))
    manifest = json.loads(originals[MANIFEST])
    rows = {row["path"]: row for row in manifest["files"]}
    rows["movie.py"].update(bytes=len(movie), sha256=digest(movie))
    rows["overlay/custom_1130_movie.xml"].update(bytes=len(xml), sha256=digest(xml))
    rows["overlay/select_dispatch.py"].update(bytes=len(dispatch_overlay), sha256=digest(dispatch_overlay))
    rows["jellyfin_trailer_route.py"] = {"path": "jellyfin_trailer_route.py", "bytes": len(helper_data), "sha256": digest(helper_data)}
    manifest["files"] = sorted(rows.values(), key=lambda row: row["path"])
    manifest_data = encoded(manifest)
    family = json.loads(originals[FAMILY])
    family["components"]["aster-global-search-ui22"]["manifest_sha256"] = digest(manifest_data)
    family_data = encoded(family)

    result = {"movie": digest(movie), "xml": digest(xml), "dispatch": digest(dispatch), "dispatch_overlay": digest(dispatch_overlay), "manifest": digest(manifest_data), "helper": digest(helper_data)}
    if check_only:
        print(json.dumps(result, sort_keys=True))
        return

    if not reapply and not reinstall:
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        for path, data in originals.items():
            target = CHECKPOINT / str(path.relative_to(ADDONS)).replace("/", "__")
            target.write_bytes(data)
            os.chmod(target, 0o600)
        state = {"created": int(time.time()), "host": HOST, "files": {str(path): digest(data) for path, data in originals.items()}}
        (CHECKPOINT / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        os.chmod(CHECKPOINT / "state.json", 0o600)

    if not reapply:
        STABLE.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copy2(Path(__file__).resolve(), STABLE / "install_jen_movie.py")
        shutil.copy2(source_helper, STABLE / "jellyfin_trailer_route.py")
        SERVICE.write_text(
            "[Unit]\nDescription=Apply the checkpointed AsterTV v3 M4 Jen movie overlay\n"
            "After=astertv-release-guard.service\nBefore=kodi.service\n"
            "[Service]\nType=oneshot\n"
            "ExecStart=/usr/bin/python3 /storage/.aster-v3/m4/install_jen_movie.py --reapply /storage/.aster-v3/m4/jellyfin_trailer_route.py\n"
            "[Install]\nWantedBy=kodi.service\n"
        )
        subprocess.run(["systemctl", "disable", "astertv-v3-m4-jen.service"], check=True)
        subprocess.run(["systemctl", "enable", "astertv-v3-m4-jen.service"], check=True)
        subprocess.run(["systemctl", "stop", "kodi"], check=True)
    try:
        updates = {SKIN: xml, OVERLAY: xml, MOVIE: movie, HELPER: helper_data, DISPATCH: dispatch, DISPATCH_OVERLAY: dispatch_overlay, MANIFEST: manifest_data, FAMILY: family_data}
        for path, data in updates.items():
            temp = path.with_name(path.name + ".m4")
            temp.write_bytes(data)
            os.chmod(temp, 0o755 if path.suffix == ".py" else 0o644)
            os.replace(temp, path)
    finally:
        if not reapply:
            subprocess.run(["systemctl", "start", "kodi"], check=True)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
