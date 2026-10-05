"""Attempt-2 guest health and fixed host LXC accounting, no network execution."""
import math
import re
from s0_probe_state import decode,exact,reject,nonnegative_int

MAX_CONTAINERS=32
FIELDS={'status','maxmem','mem','maxswap','swap'}
PRESSURE_FIELDS={'pressurecpufull','pressurecpusome','pressureiofull','pressureiosome','pressurememoryfull','pressurememorysome'}
OPTIONAL_COUNTS={'cpus','disk','maxdisk','diskread','diskwrite','netin','netout','pid','uptime'}
OPTIONAL_NUMERIC={'cpu'}|OPTIONAL_COUNTS|PRESSURE_FIELDS
OPTIONAL_TEXT={'name','type','tags','vmid'}


def parse_host(response):
    exact(response,{'returncode','stdout','stderr'})
    reject(type(response['returncode']) is not int or response['returncode']!=0 or
           type(response['stdout']) is not bytes or response['stderr']!=b'' or len(response['stdout'])>4096,'host query failed')
    values={}
    for line in response['stdout'].decode('ascii').splitlines():
        key,sep,value=line.partition(':');value=value.strip()
        reject(not sep or key in values or key not in FIELDS|OPTIONAL_NUMERIC|OPTIONAL_TEXT,'host field mismatch')
        if key=='status':reject(value!='running','LXC not running');values[key]=value
        elif key in FIELDS:
            reject(not re.fullmatch('[0-9]{1,20}',value),'invalid resource count');values[key]=int(value)
        elif key=='vmid':
            reject(value!='100','unexpected guest identity');values[key]=value
        elif key=='type':
            reject(value!='lxc','unexpected guest type');values[key]=value
        elif key=='name':
            reject(not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',value),'invalid guest name');values[key]=value
        elif key=='tags':
            tags=value.split(';') if value else []
            reject(len(value)>256 or len(tags)>16 or len(set(tags))!=len(tags) or
                   any(not re.fullmatch('[A-Za-z0-9_][A-Za-z0-9_.+-]{0,63}',tag) for tag in tags),'invalid guest tags')
            values[key]=value
        elif key in OPTIONAL_COUNTS:
            reject(not re.fullmatch('[0-9]{1,19}',value) or int(value)>=2**63,'invalid optional count')
            reject(key in ('pid','cpus') and int(value)==0,'invalid positive count')
            values[key]=value
        else:
            reject(len(value)>64 or not re.fullmatch(r'[0-9]{1,20}(?:\.[0-9]{1,20})?(?:[eE][+-]?[0-9]{1,3})?',value) or
                   not math.isfinite(float(value)) or float(value)<0,'invalid optional numeric')
            values[key]=value
    reject(not (FIELDS|{'type','vmid'})<=values.keys(),'missing host accounting/identity')
    result={k:values[k] for k in FIELDS}
    reject(not 0<result['maxmem']<2**63 or not 0<=result['mem']<=result['maxmem'],'host memory range')
    reject(not 0<=result['swap']<=result['maxswap']<2**63,'host swap range')
    reject(result['maxmem']-result['mem']<256*1024**2,'host memory headroom')
    # Existing observed swap is zero. Reject use rather than hide a pressure signal.
    reject(result['swap']!=0,'host swap use')
    return result


def guest_health(value):
    exact(value,{'host','pihole','containers','guest_mem_total','guest_mem_available','memory_psi_some_avg10'})
    reject(value['host']!='running','guest not running')
    for key in ('guest_mem_total','guest_mem_available'):nonnegative_int(value[key])
    reject(not 512*1024**2<=value['guest_mem_available']<=value['guest_mem_total'],'guest headroom')
    psi=value['memory_psi_some_avg10']
    reject(type(psi) not in (int,float) or not math.isfinite(psi) or not 0<=psi<1,'guest memory PSI')
    containers=value['containers']
    reject(type(containers) is not dict or not 1<=len(containers)<=MAX_CONTAINERS,'inventory bounds')
    for name,status in containers.items():
        reject(type(name) is not str or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',name),'container name')
        exact(status,{'running','state','health','restarts'})
        reject(type(status['running']) is not bool or status['state'] not in ('running','exited','created'),'unstable container state')
        reject(status['running']!=(status['state']=='running'),'inconsistent container state')
        reject(status['health'] not in ('healthy','none','unhealthy','starting'),'unknown health state')
        reject(status['running'] and status['health'] not in ('healthy','none'),'running container unhealthy')
        nonnegative_int(status['restarts'])
    reject(containers.get('pihole')!=value['pihole'],'missing/inconsistent Pi-hole')
    reject(value['pihole']['running'] is not True or value['pihole']['health']!='healthy','Pi-hole unhealthy')
    return value


def combined_health(guest_response,host_response):
    guest=guest_health(decode(guest_response));host=parse_host(host_response)
    reject(guest['guest_mem_total']>host['maxmem'],'guest memory exceeds host limit')
    baseline={'host':guest['host'],'containers':guest['containers'],'pihole':guest['pihole'],
              'host_maxmem':host['maxmem'],'host_maxswap':host['maxswap'],'guest_mem_total':guest['guest_mem_total']}
    resources={'guest_mem_available':guest['guest_mem_available'],'guest_psi_some_avg10':guest['memory_psi_some_avg10'],
               'host_memory_current':host['mem'],'host_memory_max':host['maxmem'],'host_swap_current':host['swap'],'host_swap_max':host['maxswap']}
    return baseline,resources
