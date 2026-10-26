"""Local-only network facts. No reachability probes, credentials or configuration writes."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess

MAX_BYTES=65536
IFACE=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,14}')


@dataclass(frozen=True)
class NetworkFacts:
    state:str
    interface:str|None
    link:str
    addresses:tuple=field(repr=False)
    gateway:str|None=field(repr=False)
    dns:tuple=field(repr=False)
    notes:tuple
    observed_at:str
    reachability:str='Not tested'


def lines(raw):
    if not isinstance(raw,str) or len(raw.encode('utf-8'))>MAX_BYTES:return None
    value=raw.splitlines()
    return value if len(value)<=256 else None


def addresses(raw):
    rows=lines(raw);result=[];invalid=False
    if rows is None:return (),True
    for row in rows:
        words=row.split()
        if not words:continue
        if (len(words)<4 or not re.fullmatch('[0-9]+:',words[0]) or words[2]!='inet'):
            invalid=True;continue
        interface=words[1].split('@',1)[0]
        try:
            if not IFACE.fullmatch(interface):raise ValueError()
            address=ipaddress.IPv4Interface(words[3])
            if address.ip.is_loopback:continue
            if address.ip.is_unspecified or address.ip.is_multicast:raise ValueError()
            item=(interface,str(address))
            if item not in result:result.append(item)
        except ValueError:invalid=True
    if len(result)>64:return (),True
    return tuple(result),invalid


def routes(raw):
    rows=lines(raw);result=[];invalid=False
    if rows is None or not rows:return (),True
    if rows[0].split()[:3]!=['Iface','Destination','Gateway']:return (),True
    for row in rows[1:]:
        words=row.split()
        if not words:continue
        try:
            if (len(words)!=11 or not IFACE.fullmatch(words[0]) or
                not all(re.fullmatch('[a-fA-F0-9]{8}',words[i]) for i in (1,2,7)) or
                not re.fullmatch('[a-fA-F0-9]{1,8}',words[3]) or
                not re.fullmatch('[0-9]{1,9}',words[6])):raise ValueError()
            flags=int(words[3],16);metric=int(words[6])
            if words[1]!='00000000' or words[7]!='00000000' or not flags&1:continue
            gateway=ipaddress.IPv4Address(int(words[2],16).to_bytes(4,'little'))
            if gateway.is_multicast:raise ValueError()
            result.append((metric,words[0],None if gateway.is_unspecified else str(gateway)))
        except (ValueError,OverflowError):invalid=True
    if len(result)>16:return (),True
    return tuple(sorted(set(result))),invalid


def dns_servers(raw):
    rows=lines(raw);result=[];invalid=False
    if rows is None:return (),True
    for row in rows:
        words=row.split('#',1)[0].split()
        if not words or words[0]!='nameserver':continue
        try:
            if len(words)!=2 or len(words[1])>80:raise ValueError()
            if '%' in words[1] and not IFACE.fullmatch(words[1].split('%',1)[1]):raise ValueError()
            address=ipaddress.ip_address(words[1])
            if address.is_unspecified or address.is_multicast:raise ValueError()
            value=str(address)
            if value not in result:result.append(value)
        except ValueError:invalid=True
    if len(result)>8:return (),True
    return tuple(result),invalid


def model(address_text,route_text,dns_text,link_states,now):
    if not isinstance(now,datetime) or now.utcoffset() is None:raise ValueError('network-aware-clock-required')
    ips,bad_ips=addresses(address_text);defaults,bad_routes=routes(route_text)
    dns,bad_dns=dns_servers(dns_text);notes=[]
    if bad_ips:notes.append('Some address information is unavailable or unsupported.')
    if bad_routes:notes.append('Some route information is unavailable or unsupported.')
    if bad_dns:notes.append('Some DNS configuration is unavailable or unsupported.')
    candidates=[r for r in defaults if r[0]==defaults[0][0]] if defaults else []
    selected=candidates[0] if len(candidates)==1 else None
    if len(candidates)>1:notes.append('Multiple equal-priority default routes; no route was selected.')
    interface=selected[1] if selected else ips[0][0] if len({i for i,_ in ips})==1 else None
    link=link_states.get(interface,'unknown') if isinstance(link_states,dict) else 'unknown'
    if link not in ('up','down','unknown','dormant','notpresent','lowerlayerdown','testing'):link='unknown'
    if not ips:state='No local IPv4 address'
    elif link in ('down','notpresent','lowerlayerdown'):state='Link down'
    elif not defaults:state='No default route'
    elif len(candidates)>1:state='Route ambiguous'
    elif not any(i==interface for i,_ in ips):state='Default interface has no IPv4 address'
    elif all(ipaddress.IPv4Interface(a).ip.is_link_local for i,a in ips if i==interface):state='Link-local address only'
    elif link!='up':state='Link state unknown'
    else:state='Local configuration available'
    if not dns:notes.append('No configured DNS server was found.')
    if selected and selected[2] is None:notes.append('Default route is on-link; no gateway address is configured.')
    notes.append('DNS, gateway, media services and Internet reachability have not been tested.')
    return NetworkFacts(state,interface,link,ips,selected[2] if selected else None,dns,
                        tuple(notes),now.astimezone(timezone.utc).isoformat())


def read_local(path):
    # Fixed OS-managed paths only; resolv.conf/sysfs links are expected. No caller path API.
    try:
        descriptor=os.open(str(path),os.O_RDONLY|os.O_NONBLOCK)
        with os.fdopen(descriptor,'rb') as stream:raw=stream.read(MAX_BYTES+1)
        return raw.decode('utf-8') if len(raw)<=MAX_BYTES else None
    except (OSError,UnicodeError):return None


def collect():
    try:
        result=subprocess.run(['ip','-o','-4','addr','show'],stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,timeout=3,check=False)
        text=result.stdout.decode('utf-8') if result.returncode==0 and len(result.stdout)<=MAX_BYTES else None
    except (OSError,UnicodeError,subprocess.SubprocessError):text=None
    route_text=read_local('/proc/net/route')
    ips,_=addresses(text);defaults,_=routes(route_text)
    interfaces={i for i,_ in ips}|{r[1] for r in defaults}
    links={i:(read_local(Path('/sys/class/net')/i/'operstate') or '').strip()
           for i in sorted(interfaces)[:16] if IFACE.fullmatch(i)}
    return model(text,route_text,read_local('/etc/resolv.conf'),links,datetime.now(timezone.utc))


if __name__=='__main__':
    value=collect()
    print(json.dumps(dict(state=value.state,link=value.link,address_count=len(value.addresses),
        dns_count=len(value.dns),gateway_configured=value.gateway is not None,
        reachability=value.reachability,notes_count=len(value.notes),network_changed=False)))
