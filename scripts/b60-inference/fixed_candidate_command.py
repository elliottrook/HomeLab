"""Offline compiler for one reviewed candidate in the qualified owner scope.

No runner, CLI, network, filesystem mutation or live-admission authority. The
legacy command data is retained exactly, with an explicit scope/deadline adapter;
its old launcher/controller is never imported or deployed by this module.
"""
import hashlib,re,types
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from benchmark_contract_preparation import inspect_contract,CONTRACT_SHA

SOURCE=Path(__file__).resolve().parent/'peer-contract-20261105/full_aster_first_screen_candidate.py'
SOURCE_SHA='9fd4e5746363e7cbdcac0d121d15cdac4ce990c24a1e988bc8b98faad8bcf260'
BOOKING=re.compile(r'b60-exclusive-(\d{8})(?:-day-r[1-9][0-9]{0,2})?')
MAX_TRIAL_SECONDS=1800
RESTORATION_SECONDS=900

def compile_candidate(booking,*,now_epoch,trial_deadline_epoch,source_path=SOURCE):
    required={'booking_id','owner','kind','state','start_epoch','end_epoch'}
    if not isinstance(booking,dict) or not required<=set(booking):raise ValueError('booking fields absent')
    identity=booking['booking_id'];match=BOOKING.fullmatch(identity) if isinstance(identity,str) else None
    if not match or booking['owner']!='b60-stream-a' or booking['kind']!='exclusive-stack' or booking['state']!='claimed':
        raise ValueError('exact claimed B60 identity required')
    values=(now_epoch,trial_deadline_epoch,booking['start_epoch'],booking['end_epoch'])
    if any(type(v) is not int for v in values):raise ValueError('integer epochs required')
    if not (booking['start_epoch']<=now_epoch<trial_deadline_epoch
            and trial_deadline_epoch-now_epoch<=MAX_TRIAL_SECONDS
            and trial_deadline_epoch+RESTORATION_SECONDS<=booking['end_epoch']):
        raise ValueError('trial or restoration window invalid')
    day=datetime.strptime(match.group(1),'%Y%m%d').date()
    zone=ZoneInfo('America/Vancouver')
    if day!=datetime.fromtimestamp(now_epoch,zone).date():raise ValueError('booking cycle differs')
    raw=Path(source_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('reviewed candidate command source drift')
    peer=types.ModuleType('pinned_candidate_command');exec(compile(raw,str(SOURCE),'exec'),peer.__dict__)
    contract=inspect_contract()
    command=list(peer.start_command());old='--unit='+peer.UNIT
    if command.count(old)!=1:raise ValueError('legacy command unit ambiguous')
    unit='b60-exclusive-trial-'+identity+'.service'
    command[command.index(old)]='--unit='+unit
    index=command.index(peer.BINARY)
    command[index:index]=['--property=KillMode=control-group','--property=RuntimeMaxSec='+str(trial_deadline_epoch-now_epoch)]
    return {'schema':'b60-fixed-candidate-command.v1','booking_id':identity,
        'owned_unit':unit,'start_command':tuple(command),
        'stop_command':('pct','exec','110','--','systemctl','stop',unit),
        'model_roles':contract['model_roles'],'contract_sha256':CONTRACT_SHA,
        'peer_command_source_sha256':SOURCE_SHA,'trial_deadline_epoch':trial_deadline_epoch,
        'restore_deadline_epoch':booking['end_epoch'],'reasoning_enabled':True,
        'requests':2,'request_timeout_seconds':60,'retries':0,'promotion':False,
        'authority':'not-granted','live_admission_verified':False,
        'ready_for_live_execution':False}
