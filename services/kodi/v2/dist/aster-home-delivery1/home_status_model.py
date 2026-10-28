"""Pure schema4 Home display consumer. Fresh export is not sensor liveness."""
from dataclasses import dataclass
from datetime import datetime,timezone
import json
import math
import re

KINDS={'light','temperature','humidity','battery','illuminance','moisture','motion','door','window','smoke','safety','weather','camera','timer'}
WEATHER={'clear-night','cloudy','exceptional','fog','hail','lightning','lightning-rainy','partlycloudy','pouring','rainy','snowy','snowy-rainy','sunny','windy','windy-variant'}

def require(ok):
    if not ok:raise ValueError('home-status-invalid')
def unique(pairs):
    value={}
    for key,item in pairs:require(key not in value);value[key]=item
    return value
def number(value,low,high):return type(value) in (int,float) and math.isfinite(value) and low<=value<=high

def validate(payload):
    require(isinstance(payload,dict) and set(payload)=={'schema_version','snapshot_id','observed_at','entities'})
    require(type(payload['schema_version']) is int and payload['schema_version']==4 and payload['snapshot_id']=='ha-home-dashboard-v4')
    require(isinstance(payload['observed_at'],str) and len(payload['observed_at'])<=40)
    stamp=datetime.fromisoformat(payload['observed_at'].replace('Z','+00:00'));require(stamp.utcoffset() is not None)
    rows=payload['entities'];require(isinstance(rows,list) and len(rows)<=256)
    seen=set()
    for row in rows:
        require(isinstance(row,dict))
        identity=row.get('id');name=row.get('name');kind=row.get('kind');availability=row.get('availability')
        require(isinstance(identity,str) and re.fullmatch(r'[a-z_]+\.[a-z0-9_]{1,160}',identity) and identity not in seen)
        seen.add(identity)
        require(isinstance(name,str) and 0<len(name)<=80 and not any(c in name for c in '[]<>') and
                all(ord(c)>=32 and ord(c)!=127 for c in name) and '://' not in name and '@' not in name)
        require(kind in KINDS and availability in ('available','unknown','unavailable'))
        domain=identity.split('.')[0]
        require(domain==('sensor' if kind in ('temperature','humidity','battery','illuminance') else
                        'binary_sensor' if kind in ('moisture','motion','door','window','smoke','safety') else kind))
        base={'id','name','kind','availability'}
        if domain in ('light','binary_sensor','camera','timer'):
            options={'light':{'on','off'},'binary_sensor':{'on','off'},'camera':{'idle','streaming','recording'},'timer':{'idle','active','paused'}}
            state=row.get('state');require(state in options[domain]|{'unknown','unavailable'})
            require(availability==('unknown' if state=='unknown' else 'unavailable' if state=='unavailable' else 'available'))
            extra={'remaining','finishes_at'} if kind=='timer' else set()
            require(base|{'state'}<=set(row) and set(row)<=base|{'state'}|extra)
            if 'remaining' in row:require(isinstance(row['remaining'],str) and re.fullmatch(r'\d{1,3}:[0-5]\d:[0-5]\d',row['remaining']))
            if 'finishes_at' in row:
                require(isinstance(row['finishes_at'],str) and len(row['finishes_at'])<=40)
                require(datetime.fromisoformat(row['finishes_at']).utcoffset() is not None)
        elif availability!='available':require(set(row)==base)
        else:
            extra={'condition','humidity'} if kind=='weather' else set()
            require(base|{'value','unit'}<=set(row) and set(row)<=base|{'value','unit'}|extra)
            unit=row['unit'];value=row['value']
            if kind in ('temperature','weather'):
                require(unit in ('°C','°F') and number(value,*((-50,60) if unit=='°C' else (-58,140))))
            elif kind in ('battery','humidity'):require(unit=='%' and number(value,0,100))
            else:require(unit=='lx' and number(value,0,1000000))
            if kind=='weather':
                require(row.get('condition') in WEATHER)
                if 'humidity' in row:require(number(row['humidity'],0,100))
    return stamp

@dataclass(frozen=True)
class View:
    state:str
    rows:tuple
    properties:dict
    notice:str

def view(raw,now=None,section='overview'):
    now=now or datetime.now(timezone.utc)
    base={'LightLabel':'Lighting','LightValue':'Unavailable','TemperatureLabel':'Indoor comfort',
          'TemperatureValue':'Unavailable','WeatherLabel':'Weather','WeatherValue':'Unavailable'}
    try:
        require(isinstance(raw,bytes) and 0<len(raw)<=262144 and now.utcoffset() is not None)
        payload=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:require(False))
        stamp=validate(payload);age=(now-stamp).total_seconds()
        if age < -10:state='future'
        elif age > 600:state='stale'
        else:state='fresh'
        if state!='fresh':
            notice='Home data expired — refresh the source export' if state=='stale' else 'Home data clock is ahead'
            return View(state,(('Home data unavailable',notice),),base,notice)
        rows=payload['entities'];available=[r for r in rows if r['availability']=='available']
        lights=[r for r in rows if r['kind']=='light'];on=sum(r.get('state')=='on' for r in lights)
        ready=sum(r['availability']=='available' for r in lights)
        if lights:base['LightValue']=f'{on} on · {ready}/{len(lights)} available'
        temps=[r for r in available if r['kind']=='temperature']
        if temps:base.update(TemperatureLabel=temps[0]['name'],TemperatureValue=f'{temps[0]["value"]:g}{temps[0]["unit"]}')
        weather=next((r for r in available if r['kind']=='weather'),None)
        if weather:
            condition=weather['condition'].replace('partlycloudy','partly cloudy').replace('-',' ').title()
            base['WeatherValue']=f'{condition} · {weather["value"]:g}{weather["unit"]}'
        def detail(r):
            if r['availability']!='available':return r['availability'].title()
            if 'value' in r:return f'{r["value"]:g}{r["unit"]}'
            state=r.get('state','')
            if r['kind']=='moisture':return 'Leak detected' if state=='on' else 'Dry'
            if r['kind']=='motion':return 'Motion detected' if state=='on' else 'Clear'
            if r['kind'] in ('door','window'):return 'Open' if state=='on' else 'Closed'
            return state.title()
        if section=='lighting':rows=lights
        priority={'moisture':0,'smoke':0,'safety':0,'temperature':1,'light':2,'motion':3,'battery':4}
        rows=sorted(rows,key=lambda r:(priority.get(r['kind'],5),r['name'].casefold()))
        display=tuple((r['name'],detail(r)) for r in rows)
        unavailable=sum(r['availability']!='available' for r in rows)
        notice=f'{len(rows)} readings · {unavailable} unavailable/unknown · Source {stamp.astimezone().strftime("%H:%M")}'
        return View('fresh',display or (('No readings in this section','Read-only Home Assistant export'),),base,notice)
    except (ValueError,TypeError,KeyError,OverflowError,UnicodeError):
        notice='Home export unavailable — no current values shown'
        return View('invalid',(('Home data unavailable',notice),),base,notice)
