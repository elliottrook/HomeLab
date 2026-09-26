"""Pure fake-transport feasibility state machine. No real transport/SSH branch."""
import copy
import hashlib
import json
import math
import struct

from validate_label_batch import exact, reject, unique

CAP = 8192
OPS = frozenset({'preflight-unit','preflight-paths','preflight-health','preflight-dns',
                 'create','run-start','inspect-running','run-result','postflight-health',
                 'postflight-dns','final-health','final-dns','stop','inspect-cleanup','remove-canary','verify-cleanup'})
CHECKS = frozenset({'inherited_environment_allowlisted','fixed_locale','environment_cleared',
                    'inet_socket_denied','unix_socket_denied','fork_denied',
                    'canary_read_denied','runtime_write_readonly','unprivileged'})
EXPECTED = {'DynamicUser':True,'NoNewPrivileges':True,'PrivateNetwork':True,
            'ProtectSystem':'strict','MemoryMax':67108864,'MemorySwapMax':0,'TasksMax':1,
            'RuntimeMaxUSec':15000000,'KillMode':'control-group',
            'network_filter':True,'fork_filter':True,'mount_filter':True,
            'inaccessible_paths':['/etc','/opt','/srv','/var','/run'],
            'cgroup_memory_max':67108864,'cgroup_memory_swap_max':0,'cgroup_pids_max':1}
QUERY_ID=0x534f
QUESTION=b'\x07example\x03org\x00\x00\x01\x00\x01'


def envelope(value):
    return {'returncode':0,'stdout':json.dumps(value).encode(),'stderr':b''}


class FakeTransport:
    """Data-only invented responses. Not subclassable at the execution boundary."""
    def __init__(self, responses):
        reject(type(responses) is not dict or not set(responses)<=OPS,'unknown operations')
        self.responses=copy.deepcopy(responses);self.calls=[]

    def exchange(self, operation):
        reject(operation not in OPS,'unknown operation')
        self.calls.append(operation)
        if operation not in self.responses: raise ValueError('missing fixture response')
        value=self.responses[operation]
        if value is None: raise TimeoutError('invented transport timeout')
        return copy.deepcopy(value)


def real_transport(*_, **__):
    raise PermissionError('real transport permanently disabled in dry-run candidate')


def decode(response):
    exact(response,{'returncode','stdout','stderr'})
    reject(type(response['returncode']) is not int or response['returncode']!=0,'command failed')
    reject(type(response['stdout']) is not bytes or type(response['stderr']) is not bytes,'invalid stream')
    reject(len(response['stdout'])+len(response['stderr'])>CAP or response['stderr']!=b'','output limit or warning')
    raw=response['stdout']
    def bad(_):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=unique,parse_constant=bad)


def nonnegative_int(value):
    reject(type(value) is not int or value<0,'invalid integer')


def health(value):
    exact(value,{'host','pihole','containers','guest_mem_available','cgroup_memory_current',
                 'cgroup_memory_max','memory_psi_some_avg10'})
    reject(value['host']!='running','guest not healthy')
    for field in ('guest_mem_available','cgroup_memory_current','cgroup_memory_max'):nonnegative_int(value[field])
    reject(value['guest_mem_available']<512*1024**2 or
           value['cgroup_memory_max']-value['cgroup_memory_current']<256*1024**2,'memory headroom')
    psi=value['memory_psi_some_avg10']
    reject(type(psi) not in (int,float) or not math.isfinite(psi) or not 0<=psi<1,'memory pressure')
    reject(type(value['containers']) is not dict or not value['containers'],'container inventory')
    for name,status in value['containers'].items():
        reject(type(name) is not str or not name or len(name)>128,'container name')
        exact(status,{'running','health','restarts'})
        reject(status['running'] is not True or status['health'] not in ('healthy','none'),'container unhealthy')
        nonnegative_int(status['restarts'])
    exact(value['pihole'],{'running','health','restarts'})
    reject(value['pihole']['running'] is not True or value['pihole']['health']!='healthy','DNS service unhealthy')
    nonnegative_int(value['pihole']['restarts'])
    reject(value['containers'].get('pihole')!=value['pihole'],'inconsistent DNS service')
    return {'host':value['host'],'pihole':value['pihole'],'containers':value['containers']}


def dns(value):
    exact(value,{'responses'})
    reject(type(value['responses']) is not list or len(value['responses'])!=2,'DNS count')
    for row in value['responses']:
        exact(row,{'packet_hex','elapsed_ms'})
        elapsed=row['elapsed_ms']
        reject(type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0<=elapsed<=2000,'DNS timeout')
        reject(type(row['packet_hex']) is not str or len(row['packet_hex'])>1024,'DNS size')
        raw=bytes.fromhex(row['packet_hex'])
        reject(len(raw)<12+len(QUESTION),'DNS truncation')
        ident,flags,questions,_,_,_=struct.unpack('!6H',raw[:12])
        reject(ident!=QUERY_ID or not flags&0x8000 or flags&0x0200 or flags&0x7800 or flags&15 or
               questions!=1 or raw[12:12+len(QUESTION)]!=QUESTION,'DNS response mismatch')
    return True


def run_dry(transport):
    if type(transport) is not FakeTransport: raise PermissionError('only exact FakeTransport allowed')
    history=[];failures=[];baseline=None;preflight=False
    create_attempt=False;created=False;run_attempt=False;unit_owned=False
    health_ok=False;dns_ok=False;final_health_ok=False;final_dns_ok=False;removed=False;stopped=False;clean=False;result_ok=False
    total=0

    def call(op):
        nonlocal total
        response=FakeTransport.exchange(transport,op)
        if op=='preflight-unit':
            exact(response,{'returncode','stdout','stderr'})
            reject(type(response['returncode']) is not int or response['returncode']!=0 or
                   response['stdout']!=b'LoadState=not-found\n' or response['stderr']!=b'',
                   'existing or unknown unit')
            parsed={'load_state':'not-found'}
        else:
            parsed=decode(response)
        total+=len(response['stdout'])+len(response['stderr'])
        reject(total>65536,'total fixture transcript budget')
        history.append({'operation':op,'outcome':'parsed',
                        'response_sha256':hashlib.sha256(response['stdout']).hexdigest()})
        return parsed

    def fail(op):
        failures.append(op)
        history.append({'operation':op,'outcome':'failed-or-unverified'})

    try:
        call('preflight-unit')
        paths=call('preflight-paths');exact(paths,{'canary_directory_absent','runtime_probe_absent'})
        reject(any(v is not True for v in paths.values()),'existing probe paths')
        baseline=health(call('preflight-health'));dns(call('preflight-dns'));preflight=True
        create_attempt=True
        creation=call('create');exact(creation,{'created_exclusively','directory_mode','file_mode'})
        reject(creation['created_exclusively'] is not True or type(creation['directory_mode']) is not int or
               type(creation['file_mode']) is not int or creation['directory_mode']!=0o755 or creation['file_mode']!=0o644,'creation unverified')
        created=True;run_attempt=True
        start=call('run-start');exact(start,{'started_by_attempt','unit','invocation_id'})
        reject(start['started_by_attempt'] is not True or start['unit']!='aster-s0-feasibility-20260926.service' or
               start['invocation_id']!='fixture-invocation-owned','unit ownership unverified')
        unit_owned=True
        observed=call('inspect-running');exact(observed,{'properties','phase','checks','invocation_id'})
        reject(observed['invocation_id']!=start['invocation_id'] or observed['phase']!='ready','running identity')
        exact(observed['properties'],EXPECTED)
        for key,expected in EXPECTED.items():
            actual=observed['properties'][key]
            reject(type(actual) is not type(expected) or actual!=expected,'isolation not applied')
        exact(observed['checks'],CHECKS);reject(any(x is not True for x in observed['checks'].values()),'probe denial failed')
        result=call('run-result');exact(result,{'phase','passed','exit_code','invocation_id'})
        reject(result['phase']!='done' or result['passed'] is not True or type(result['exit_code']) is not int or
               result['exit_code']!=0 or result['invocation_id']!=start['invocation_id'],'probe failed')
        result_ok=True
    except Exception:
        fail('probe-sequence')
    finally:
        # No cleanup mutation at all if preflight failed: paths/units may pre-exist.
        if create_attempt:
            try:health_ok=health(call('postflight-health'))==baseline;reject(not health_ok,'health changed')
            except Exception:fail('postflight-health')
            try:dns_ok=dns(call('postflight-dns'))
            except Exception:fail('postflight-dns')
            if run_attempt:
                if unit_owned:
                    try:
                        stop=call('stop');exact(stop,{'stopped_owned_unit','invocation_id'})
                        reject(stop['stopped_owned_unit'] is not True or stop['invocation_id']!='fixture-invocation-owned','stop unverified')
                        stopped=True
                    except Exception:fail('stop')
                else:fail('manual-unit-recovery-required')
            try:
                cleanup=call('inspect-cleanup')
                exact(cleanup,{'directory_owned_by_attempt','exact_directory_mode','exact_file_mode',
                               'exact_canary_content','no_extra_entries','unit_absent','cgroup_absent'})
                ownership=created and cleanup['directory_owned_by_attempt'] is True
                modes=cleanup['exact_directory_mode'] is True and cleanup['exact_file_mode'] is True
                eligible=ownership and modes and cleanup['exact_canary_content'] is True and cleanup['no_extra_entries'] is True
                # Do not remove under an unverified/still-running process.
                eligible=eligible and cleanup['unit_absent'] is True and cleanup['cgroup_absent'] is True
                reject(not eligible,'cleanup ownership/state uncertain')
                removed_result=call('remove-canary');exact(removed_result,{'removed_only_owned_canary_and_directory'})
                reject(removed_result['removed_only_owned_canary_and_directory'] is not True,'removal failed')
                removed=True
            except Exception:fail('canary-cleanup')
            try:
                verification=call('verify-cleanup');exact(verification,{'unit_absent','cgroup_absent','directory_absent','runtime_probe_absent'})
                clean=all(v is True for v in verification.values())
                reject(not clean,'cleanup incomplete')
            except Exception:fail('verify-cleanup')
            try:final_health_ok=health(call('final-health'))==baseline;reject(not final_health_ok,'final health changed')
            except Exception:fail('final-health')
            try:final_dns_ok=dns(call('final-dns'))
            except Exception:fail('final-dns')
    passed=preflight and result_ok and health_ok and dns_ok and final_health_ok and final_dns_ok and removed and clean and not failures
    report={'format':'s0-probe-dry-run.v1','scope':'invented-fake-transport-only',
            'status':'fixture-pass' if passed else 'fixture-failed-or-inconclusive',
            'history':history,'failure_stages':failures,'operation_order':list(transport.calls),
            'preflight_passed':preflight,'create_attempted':create_attempt,'creation_verified':created,
            'unit_start_attempted':run_attempt,'owned_unit_stopped':stopped,'canary_removed':removed,
            'cleanup_verified':clean,'postflight_health_unchanged':health_ok,'postflight_dns_ok':dns_ok,
            'final_health_unchanged':final_health_ok,'final_dns_ok':final_dns_ok,
            'live_authorized':False,'corpus_evaluated':False}
    if len(json.dumps(report,allow_nan=False).encode())>CAP:raise ValueError('bounded result exceeded; no result persisted')
    return report
