"""Disable only the known HP scrub2 OSD after Kodi has fully stopped."""
import hashlib,json,os,subprocess,tempfile,time
from pathlib import Path
def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
require(os.uname().nodename=='AsterTV','hp-only')
state=subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()
require(state=='0','kodi-must-be-stopped')
root=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')
active=root/'active-manifest.json';target=Path('/storage/.kodi/addons/skin.asterhome/1080i/VideoOSD.xml')
require(digest(active)=='ac96d5b2e0c059a035aabf65a16b1212b6cc89618201867064504c98e65e2184','known-active-manifest')
require(digest(target)=='ff32bb852887cdf290b892a13103d277ffc34d3c0f02419061b3bb0356a0fa38','known-active-osd')
backup=root/'aster-video-scrub2/VideoOSD.xml';original='7fe65ddc4e2e33931a771bd57de349ae7a1d47e4d1983534a83e02a5a6ed03c6'
require(digest(backup)==original,'verified-original-required')
fd,name=tempfile.mkstemp(prefix='.aster-osd-restore-',dir=target.parent)
with os.fdopen(fd,'wb') as handle:handle.write(backup.read_bytes());handle.flush();os.fsync(handle.fileno())
os.chmod(name,0o644);os.replace(name,target)
require(digest(target)==original,'restored-osd-hash')
active.rename(root/('disabled-manifest-'+str(time.time_ns())+'.json'))
print(json.dumps(dict(restored=True,files_changed=1,original_osd_sha256=original,
    retained_stage=True,retained_recovery=True,no_profile_or_history_restore=True)))
