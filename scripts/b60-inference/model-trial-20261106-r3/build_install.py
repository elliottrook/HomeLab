"""Build one new source-bound R3 installer; no network or effects here."""
import ast,base64,hashlib,json
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
NAMES=('model_trial.py','namespace_mount.py','fixed_command.py','guest_requests.py','guest_supervisor.py','backup_chain_history.py','legacy_requests.py','request_failure_capture.py','news_xpu_boundary.py')
manifest={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in NAMES}
files={n:base64.b64encode((HERE/n).read_bytes()).decode() for n in NAMES}
history=Path('/private/tmp/b60-truenas-history-r3-receipt.json').read_bytes()
prefix='FILES='+repr(files)+'\nMANIFEST='+repr(manifest)+'\nHISTORY='+repr(base64.b64encode(history).decode())+'\nHISTORY_SHA='+repr(hashlib.sha256(history).hexdigest())+'\n'
tree=ast.parse((HERE/'news_xpu_boundary.py').read_bytes())
news={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'PINS','GUEST','GUEST_SHA','MOUNT_SHA'}}
prefix+='NEWS='+repr(news)+'\n'
spec=importlib.util.spec_from_file_location('fixed_registration_builder',HERE/'build_registration.py')
registration=importlib.util.module_from_spec(spec);spec.loader.exec_module(registration);registration.build()
reg_names=('b60_exclusive_card_bridge.py','lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json')
reg_files={n:base64.b64encode((registration.DEST/n).read_bytes()).decode() for n in reg_names}
reg_sha={n:hashlib.sha256((registration.DEST/n).read_bytes()).hexdigest() for n in reg_names}
reg_old=dict(registration.PREDECESSORS,lab_hours_release_manifest=json.loads((registration.SOURCE/'release-snapshot.json').read_bytes())['sha256'])
reg_old['lab_hours_release_manifest.json']=reg_old.pop('lab_hours_release_manifest')
prefix+='REG_FILES='+repr(reg_files)+'\nREG_SHA='+repr(reg_sha)+'\nREG_PREDECESSORS='+repr(reg_old)+'\n'
script=(HERE/'registration_install.py.txt').read_text()+'\n'+(HERE/'install_body.py.txt').read_text()
Path('/private/tmp/b60-model-trial-r3-install.py').write_text(prefix+script)
(HERE/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':')))
print(json.dumps({'manifest':manifest,'history_sha256':hashlib.sha256(history).hexdigest(),'installer_sha256':hashlib.sha256((prefix+script).encode()).hexdigest()}))
