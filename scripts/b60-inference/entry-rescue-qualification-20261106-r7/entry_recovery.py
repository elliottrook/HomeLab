"""Preserve an already restored, proved entry backend during guardian rescue.

No second backend start is authorized. Unknown/inactive prior-start state still
refuses; all candidate processes and every other declared consumer are fenced.
"""
import time

BACKEND=('110','aster-llama.service')


def require(value,code):
    if value is not True:raise RuntimeError(code)


def bounded_verify(original,rows,deadline,*,clock=time.time,sleep=time.sleep):
    stop=min(deadline,clock()+45)
    while clock()<stop:
        if original(rows,stop) is True:return True
        if clock()+2>=stop:return False
        sleep(2)
    return False


def install(adapter,store,*,kernel_check,gpu_users,clock=time.time,sleep=time.sleep):
    """Bind only an existing exact checkpoint adapter; no default runner/lease."""
    original_fence=adapter.fence_experiments
    original_verify=adapter.units.verify
    adapter.units.verify=lambda rows,deadline:bounded_verify(original_verify,rows,deadline,clock=clock,sleep=sleep)

    def proof(state,deadline):
        rows=[r for r in adapter.private['units'] if (r['guest'],r['unit'])==BACKEND]
        require(len(rows)==1 and rows[0]['active']=='active','ENTRY_BACKEND_NOT_ACTIVE_AT_ENTRY')
        current=adapter.units.observe(*BACKEND,deadline)
        require(current['ActiveState']=='active' and current['UnitFileState']==rows[0]['enablement'] and current['MainPID'].isdigit() and int(current['MainPID'])>0,'ENTRY_BACKEND_NOT_PROVEN_RUNNING')
        # Existing helper verifies private configuration, full artifact hashes
        # AND the current process's captured model/runtime binding.
        verified=adapter._guest('110','verify',deadline)
        require(verified.get('verified') is True,'ENTRY_BACKEND_CHECKPOINT_NOT_VERIFIED')
        adapter._call(('pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'),deadline,30)
        holders=gpu_users()
        require(len(holders)==1 and next(iter(holders)).cgroup.endswith('/lxc/110/ns/system.slice/aster-llama.service'),'ENTRY_BACKEND_GPU_HOLDER_NOT_EXCLUSIVE')
        clean=kernel_check(adapter,deadline,adapter.bookings.get(state['booking_id'])['start_epoch'])
        identity=dict(l.split('=',1) for l in adapter._call(('pct','exec','110','--','systemctl','show','aster-llama.service','--property=ExecMainStartTimestampMonotonic'),deadline,10).splitlines());require(set(identity)=={'ExecMainStartTimestampMonotonic'} and identity['ExecMainStartTimestampMonotonic'].isdigit() and int(identity['ExecMainStartTimestampMonotonic'])>0,'ENTRY_BACKEND_START_IDENTITY')
        return {'exec_main_start_usec':int(identity['ExecMainStartTimestampMonotonic']),'entry_sha256':state['entry_sha256'],'main_pid':current['MainPID'],'enablement':current['UnitFileState'],'private_checkpoint_and_active_binding_verified':True,'sole_accepted_gpu_holder':True,'metadata_auth_probe_passed':True,'kernel':clean,'observed_epoch':int(clock())}

    def empty(booking,kind,deadline):
        unit='b60-exclusive-'+kind+'-'+booking+'.service'
        adapter.runner(('pct','exec','110','--','systemctl','stop',unit),min(30,deadline-clock()))
        code,raw=adapter.runner(('pct','exec','110','--','systemctl','show',unit,'--property=LoadState,ActiveState,MainPID,TasksCurrent'),min(10,deadline-clock()))
        require(len(raw)<=4096,'ENTRY_RESCUE_SCOPE_OBSERVATION')
        v=dict(l.split('=',1) for l in raw.splitlines())
        require(code in {0,1} and v.get('ActiveState') in {'inactive','failed'} and v.get('MainPID')=='0' and v.get('TasksCurrent') in {'0','','[not set]'},'ENTRY_RESCUE_SCOPE_NOT_EMPTY')

    def fence(state):
        intent=store.root/'entry-backend-start-intent.json'
        if not intent.exists():return original_fence(state)
        # Never stop an entry backend after its one allowed restoration start.
        # A failed/unknown start is retained for diagnosis, never auto-retried.
        adapter._load()
        deadline=max(state['restore_deadline'],clock()+300)
        empty(state['booking_id'],'client',deadline)
        empty(state['booking_id'],'trial',deadline)
        before=proof(state,deadline)
        store.write('entry-backend-preservation-intent.json',before,immutable=True)
        others=[r for r in adapter.private['units'] if (r['guest'],r['unit'])!=BACKEND]
        require(len(others)==len(adapter.private['units'])-1,'ENTRY_RESCUE_CONSUMER_CLOSURE')
        require(adapter.units.isolate(others,deadline) is True,'ENTRY_RESCUE_CONSUMERS_NOT_QUIESCENT')
        after=proof(state,deadline)
        require(after['main_pid']==before['main_pid'] and after['exec_main_start_usec']==before['exec_main_start_usec'],'ENTRY_BACKEND_PROCESS_CHANGED_DURING_FENCE')
        store.write('entry-backend-preservation-proof.json',{'schema':'b60-entry-backend-preservation.v1','booking_id':state['booking_id'],'before':before,'after':after,'candidate_and_client_empty':True,'other_consumers_quiescent':True,'backend_stop_calls':0,'additional_backend_start_calls':0},immutable=True)
        return True
    adapter.fence_experiments=fence
