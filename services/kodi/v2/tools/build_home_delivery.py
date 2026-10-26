"""Build only the forced-command receiver and identical strict display model."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

def main():
    base=Path(__file__).resolve().parents[1];destination=Path(sys.argv[1])
    destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    for source,name in ((base/'home_delivery_receiver.py','receive.py'),(base/'home_status_model.py','home_status_model.py')):
        shutil.copyfile(source,destination/name)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}
    (destination/'manifest.json').write_text(json.dumps(dict(kind='hp-home-delivery-v1',files=files),sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(files=2,manifest=hashlib.sha256((destination/'manifest.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()
