"""Build one new source-bound R3 installer; no network or effects here."""
import base64,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
NAMES=('model_trial.py','namespace_mount.py','fixed_command.py','guest_requests.py','guest_supervisor.py','backup_chain_history.py','legacy_requests.py','request_failure_capture.py','news_xpu_boundary.py')
manifest={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in NAMES}
files={n:base64.b64encode((HERE/n).read_bytes()).decode() for n in NAMES}
history=Path('/private/tmp/b60-truenas-history-r3-receipt.json').read_bytes()
prefix='FILES='+repr(files)+'\nMANIFEST='+repr(manifest)+'\nHISTORY='+repr(base64.b64encode(history).decode())+'\nHISTORY_SHA='+repr(hashlib.sha256(history).hexdigest())+'\n'
script=(HERE/'install_body.py.txt').read_text()
Path('/private/tmp/b60-model-trial-r3-install.py').write_text(prefix+script)
(HERE/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':')))
print(json.dumps({'manifest':manifest,'history_sha256':hashlib.sha256(history).hexdigest(),'installer_sha256':hashlib.sha256((prefix+script).encode()).hexdigest()}))
