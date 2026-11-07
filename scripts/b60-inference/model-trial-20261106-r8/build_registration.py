"""Exact update of the existing model route; preserve every unrelated pin/route."""
import ast,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'registry-predecessor';DEST=Path('/private/tmp/b60-registration-candidate-20261106-r8')
WORKLOAD='b60-qwen36-35b-failure-capture-v1';BRIDGE='b60_exclusive_card_bridge.py'
# Refreshed from actual authoritative installed source after R7 acceptance.
PREDECESSORS={}

def update(registry_raw,runner_raw,manifest_raw,bridge_raw):
 manifest=json.loads(manifest_raw);old=dict(manifest['pins']);old_bridge=old[BRIDGE]
 assert hashlib.sha256(registry_raw).hexdigest()==old['lab_hours_workloads.py'] and hashlib.sha256(runner_raw).hexdigest()==old['lab_hours_reserved_runner.py']
 assert re.fullmatch('[a-f0-9]{64}',old_bridge)
 text=registry_raw.decode();assert text.count('WORKLOADS['+repr(WORKLOAD)+']')==1
 assert text.count(old_bridge)==2 # exact existing entry + its exact validator guard
 new_bridge=hashlib.sha256(bridge_raw).hexdigest();registry=text.replace(old_bridge,new_bridge).encode()
 out={BRIDGE:bridge_raw,'lab_hours_workloads.py':registry,'lab_hours_reserved_runner.py':runner_raw}
 for n,raw in out.items():compile(raw,n,'exec')
 manifest['pins'].update({n:hashlib.sha256(raw).hexdigest() for n,raw in out.items()});manifest['release']=str(manifest['release'])+'-b60-model-entry-preservation-v2'
 assert set(manifest['pins'])==set(old) and all(manifest['pins'][n]==sha for n,sha in old.items() if n not in {BRIDGE,'lab_hours_workloads.py'})
 out['lab_hours_release_manifest.json']=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode();return out

def build():
 acceptance=json.loads((HERE/'controller_acceptance_pin.json').read_text());assert acceptance['actual_independent_acceptance'] is True and acceptance['booking_id']=='b60-exclusive-20261106-day-r7'
 tree=ast.parse((HERE/BRIDGE).read_bytes());pins={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'CONTROLLER_ACCEPTANCE_SHA256','CONTROLLER_INDEPENDENT_SHA256','CONTROLLER_SOURCE_SHA256','CONTROLLER_ACCEPTANCE_PRODUCER_SHA256'}}
 assert pins['CONTROLLER_ACCEPTANCE_SHA256']==acceptance['root_acceptance_sha256'] and pins['CONTROLLER_INDEPENDENT_SHA256']==acceptance['independent_postcheck_sha256'] and pins['CONTROLLER_SOURCE_SHA256']==acceptance['source_sha256'] and pins['CONTROLLER_ACCEPTANCE_PRODUCER_SHA256']==acceptance['acceptance_producer_sha256']
 assert set(PREDECESSORS)=={BRIDGE,'lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json'}
 raw={n:(SOURCE/n).read_bytes() for n in PREDECESSORS};assert all(hashlib.sha256(raw[n]).hexdigest()==sha for n,sha in PREDECESSORS.items())
 outputs=update(raw['lab_hours_workloads.py'],raw['lab_hours_reserved_runner.py'],raw['lab_hours_release_manifest.json'],(HERE/BRIDGE).read_bytes())
 DEST.mkdir(mode=0o700,exist_ok=True)
 for n,value in outputs.items():(DEST/n).write_bytes(value)
 return {n:hashlib.sha256(v).hexdigest() for n,v in outputs.items()}
if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
