"""Read-only, bounded household display projection; no auth or network access.

Runs inside the already opted-in HA exporter. Never serialize State objects or
raw attributes. The legacy latest.json contract remains independently intact.
"""
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile

OUTPUT=Path('/share/aster-home-registry/dashboard.json')

KINDS = {'light','sensor','binary_sensor','weather','camera','timer'}
SENSORS = {'temperature','humidity','battery','illuminance'}
BINARY = {'moisture','motion','door','window','smoke','safety'}
CONDITIONS = {'clear-night','cloudy','exceptional','fog','hail','lightning',
              'lightning-rainy','partlycloudy','pouring','rainy','snowy',
              'snowy-rainy','sunny','windy','windy-variant'}


def relevant(identity):
    if not isinstance(identity,str) or not re.fullmatch(r'[a-z_]+\.[a-z0-9_]{1,160}',identity):
        return False
    domain,slug=identity.split('.',1)
    return domain in KINDS and not slug.startswith(('iphone_','backup_','home_assistant_',
                                                    'sun_','matter_server_','get_hacs_'))


def number(value,low,high):
    if isinstance(value,bool):return None
    try: result=float(value)
    except (TypeError,ValueError):return None
    return round(result,1) if math.isfinite(result) and low<=result<=high else None


def temperature(value,unit):
    bounds=(-50,60) if unit=='°C' else (-58,140) if unit=='°F' else (1,0)
    return number(value,*bounds)


def project(states,*,now=None):
    records=[]; seen=set()
    for item in states:
        identity=item.get('entity_id')
        if not relevant(identity):continue
        if identity in seen:raise ValueError('home-dashboard-duplicate')
        seen.add(identity)
        domain,slug=identity.split('.',1)
        attrs=item.get('attributes',{});state=item.get('state')
        if not isinstance(attrs,dict) or not isinstance(state,str):continue
        klass=attrs.get('device_class','')
        if domain=='sensor' and klass not in SENSORS:continue
        if domain=='binary_sensor' and klass not in BINARY:continue
        fallback=slug.replace('_',' ').title()[:80]
        name=attrs.get('friendly_name')
        if not isinstance(name,str) or not name.strip():name=fallback
        name=' '.join(re.sub(r'[\[\]<>\x00-\x1f\x7f]',' ',name).split())[:80]
        if not name or '://' in name or '@' in name or name.lower() in ('battery','water leak','motion'):
            name=fallback
        record=dict(id=identity,name=name,kind=klass if domain in ('sensor','binary_sensor') else domain,
                    availability='unavailable' if state=='unavailable' else 'unknown' if state=='unknown' else 'available')
        if domain in ('light','binary_sensor','camera','timer'):
            options={'light':{'on','off'},'binary_sensor':{'on','off'},
                     'camera':{'idle','streaming','recording'},'timer':{'idle','active','paused'}}
            if state not in options[domain]|{'unknown','unavailable'}:continue
            record['state']=state
            if domain=='timer':
                remaining=attrs.get('remaining')
                if isinstance(remaining,str) and re.fullmatch(r'\d{1,3}:[0-5]\d:[0-5]\d',remaining):record['remaining']=remaining
                finishes=attrs.get('finishes_at')
                if isinstance(finishes,str) and len(finishes)<=40:
                    try:
                        stamp=datetime.fromisoformat(finishes.replace('Z','+00:00'))
                        if stamp.utcoffset() is not None:record['finishes_at']=stamp.isoformat()
                    except ValueError:pass
        elif domain=='sensor':
            unit=attrs.get('unit_of_measurement')
            if klass=='temperature':value=temperature(state,unit)
            elif klass in ('humidity','battery'):
                if unit!='%':continue
                value=number(state,0,100)
            else:
                if unit!='lx':continue
                value=number(state,0,1000000)
            if value is not None:record.update(value=value,unit=unit)
            else:record['availability']='unavailable' if state=='unavailable' else 'unknown'
        else:
            unit=attrs.get('temperature_unit');value=temperature(attrs.get('temperature'),unit)
            if state in CONDITIONS and value is not None:
                record.update(condition=state,value=value,unit=unit)
                humidity=number(attrs.get('humidity'),0,100)
                if humidity is not None:record['humidity']=humidity
            else:record['availability']='unavailable' if state=='unavailable' else 'unknown'
        records.append(record)
        if len(records)>256:raise ValueError('home-dashboard-entity-limit')
    now=now or datetime.now(timezone.utc)
    if now.utcoffset() is None:raise ValueError('home-dashboard-naive-time')
    payload=dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',
                 observed_at=now.isoformat(),entities=sorted(records,key=lambda r:r['id']))
    if len(json.dumps(payload,ensure_ascii=True))>262144:raise ValueError('home-dashboard-byte-limit')
    return payload


def write_dashboard(report):
    """Independent atomic file; never replace latest.json or the v1 registry."""
    OUTPUT.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix='.dashboard.',dir=OUTPUT.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(report,stream,ensure_ascii=True,sort_keys=True,separators=(',',':'))
            stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.chmod(temporary,0o600)
        os.replace(temporary,OUTPUT)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
