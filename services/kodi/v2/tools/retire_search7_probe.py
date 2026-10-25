"""One exact diagnosed no-play test admission fence; retain, never discard."""
import hashlib,json,os,subprocess
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','kodi-must-be-stopped')
require(hashlib.sha256((root/'active-manifest.json').read_bytes()).hexdigest()=='def37da8481dd0b53cd2650056ddeee94656ba14b21b83d0b73bafeda5fc9a6c','exact-six-restored')
fence=root/'handoff-pending.json'
require(json.loads(fence.read_text())==dict(kind='tvshow',identity=106,time=1792905991),'exact-diagnosed-fence')
checks=[]
for path in root.glob('native-playerlinks-*.json'):
    row=json.loads(path.read_text())
    if row.get('stage_manifest_sha256')=='00e52adb295c90e054847ceefc115cc4fc1617d5b81020596028faa446b38168':checks.append(row)
require(len(checks)==2 and all(row.get('checks_enforced') is True and row.get('idle_empty') is True for row in checks)
    and {row.get('failure') for row in checks}=={'artist-parent-exact-return','child-back-tvshow'},'diagnosed-no-play-tests')
target=root/'aster-global-search-ui7/retired-test-admission-1792905991.json'
require(not target.exists(),'already-retired')
fence.rename(target)
print(json.dumps(dict(retained_diagnosed_test_fence=True,accepted_six_restored=True)))
