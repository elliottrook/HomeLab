"""Read-only intent groups from the reviewed exported Home contract only."""
from dataclasses import dataclass
from datetime import datetime
import math
from home_freshness import assess

WEATHER = {'clear-night','cloudy','exceptional','fog','hail','lightning',
    'lightning-rainy','partlycloudy','pouring','rainy','snowy','snowy-rainy',
    'sunny','windy','windy-variant'}
TEMPERATURES = {'hall temperature','outside temperature','closet temperature'}
NAMES = ('Lighting','Comfort','Cameras','Timers')


@dataclass(frozen=True)
class Group:
    name: str
    state: str
    summary: str
    details: tuple


@dataclass(frozen=True)
class Dashboard:
    state: str
    notice: str
    groups: tuple
    publication: str = ''

    @property
    def exceptions(self): return sum(g.state!='reported' for g in self.groups)


def unavailable(state):
    reasons = dict(stale='Local Home feed expired; exported values are hidden.',
        missing='No local Home feed is available.',
        future='Home feed clock is ahead; values are hidden.',
        invalid='Home feed contract is unsupported; values are hidden.')
    reason = reasons.get(state,reasons['invalid'])
    return Dashboard(state,reason,tuple(Group(name,state,'Values unavailable',
        (reason,)) for name in NAMES))


def require(value):
    if not value: raise ValueError('home-reviewed-contract-required')


def records(snapshot,key,maximum):
    value=snapshot.get(key)
    require(isinstance(value,list) and len(value)<=maximum and all(isinstance(r,dict) for r in value))
    aliases=[r.get('alias') for r in value]
    require(all(isinstance(a,str) for a in aliases) and len(aliases)==len(set(aliases)))
    return value


def temperature(value,unit):
    require(unit in ('°C','°F') and type(value) in (int,float) and math.isfinite(value))
    low,high=(-50,60) if unit=='°C' else (-58,140)
    require(low<=value<=high)
    return f'{value:g}{unit}'


def project(payload,now):
    freshness=assess(payload,now)
    if not freshness.permits_value_validation:return unavailable(freshness.state)
    try:
        require(set(payload)=={'schema_version','generated_at','source_updated_at','snapshot'})
        snapshot=payload['snapshot']
        required={'schema_version','snapshot_id','lights','temperatures','weather',
            'rooms','entities','timers','media_providers'}
        require(set(snapshot) in (required,required|{'cameras'}) and snapshot['snapshot_id']=='ha-home-pilot-v3')
        require(all(snapshot[k]==[] for k in ('rooms','entities','timers','media_providers')))
        lights=[]
        for row in records(snapshot,'lights',1):
            require(set(row)=={'alias','state'} and row['alias']=='laundry lights' and row['state'] in ('on','off'))
            lights.append('Laundry lights · '+row['state'].title())
        comfort=[]
        for row in records(snapshot,'temperatures',3):
            require(set(row)=={'alias','value','unit'} and row['alias'] in TEMPERATURES)
            comfort.append(row['alias'].title()+' · '+temperature(row['value'],row['unit']))
        for row in records(snapshot,'weather',1):
            require(set(row) in ({'alias','condition','temperature','unit'},
                {'alias','condition','temperature','unit','humidity'}) and row['alias']=='home weather'
                and row['condition'] in WEATHER)
            value=temperature(row['temperature'],row['unit'])
            condition=row['condition'].replace('partlycloudy','partly cloudy').replace('-',' ').title()
            if 'humidity' in row:
                humidity=row['humidity']
                require(type(humidity) in (int,float) and math.isfinite(humidity) and 0<=humidity<=100)
                value+=f' · {humidity:g}% humidity'
            comfort.append(condition+' · '+value)
        # A legacy status record is not a verified live-view or status transport.
        if 'cameras' in snapshot:
            for row in records(snapshot,'cameras',1):
                require(set(row)=={'alias','status'} and row['alias']=='Front of house'
                    and row['status'] in ('online','offline'))
        def reported(name,rows):
            return Group(name,'reported' if rows else 'unavailable',
                str(len(rows))+' exported reading'+('s' if len(rows)!=1 else '') if rows else 'No reviewed values',
                tuple(rows) if rows else ('No usable values in this export.',))
        groups=(reported('Lighting',lights),reported('Comfort',comfort),
            Group('Cameras','unavailable','Not connected',('No verified camera delivery in this preview.',)),
            Group('Timers','unavailable','Not connected',('No structured Home Assistant timer state.',
                'Existing Home timer is unchanged.')))
        stamp=datetime.fromisoformat(payload['generated_at'].replace('Z','+00:00')).isoformat()
        return Dashboard('fresh','Recent export · read-only, not individual-sensor liveness.',groups,stamp)
    except (ValueError,TypeError,KeyError,OverflowError):return unavailable('invalid')
