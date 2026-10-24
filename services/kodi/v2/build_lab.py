"""Deterministic isolated lab ZIP; never edits installed v1 source trees."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

HERE=Path(__file__).resolve().parent
ADDON='script.astermusic.v2lab'


def build(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('Nonempty output')
    output.mkdir(parents=True,exist_ok=True)
    files={p.relative_to(HERE/ADDON).as_posix():p.read_bytes()
           for p in sorted((HERE/ADDON).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for name in ('music_catalogue.py','music_policy.py','lab_model.py','music_album.py','music_selection.py','music_audio.py','music_playlists.py','music_playlist_save.py','music_jellyfin.py','music_shared_save.py','music_queue.py','queue_reader.py','music_trial.py','music_expanded_trial.py','music_progressive.py'):
        files['resources/lib/'+name]=(HERE/name).read_bytes()
    files['resources/icon.png']=(HERE.parent/'skin.asterhome/media/20-music-app.png').read_bytes()
    archive=output/(ADDON+'-0.1.0.zip')
    records=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(ADDON+'/'+name,(2026,10,23,1,0,0))
            info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            records.append({'path':ADDON+'/'+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'addon_id':ADDON,'version':'0.1.0','archive':archive.name,
              'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':records,
              'boundary':'HP only; read-only by default; expiring explicit song-ID grant; approved expanded trial capped at 20000 queue items and 200 per write; no v1 or production changes'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(json.dumps(build(parser.parse_args().output),indent=2))
