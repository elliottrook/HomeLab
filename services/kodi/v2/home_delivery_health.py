"""Non-secret delivery freshness diagnostic; no probes or publication effects."""
from datetime import datetime,timezone
import re

def assess(ha,hp,now=None):
    now=now or datetime.now(timezone.utc)
    try:
        def fresh(value,maximum):
            if not isinstance(value,str) or len(value)>40:return False
            stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
            return stamp.utcoffset() is not None and -10<=(now-stamp).total_seconds()<=maximum
        if ha.get('ok') is not True or hp.get('ok') is not True:return dict(ok=False,code='delivery-unavailable')
        if not fresh(ha.get('last_success_at'),420) or not fresh(hp.get('received_at'),420):return dict(ok=False,code='delivery-stale')
        if not fresh(ha.get('last_source_at'),600) or not fresh(hp.get('source_at'),600):return dict(ok=False,code='source-stale')
        pin=ha.get('last_sha256','')
        if not isinstance(pin,str) or not re.fullmatch('[0-9a-f]{64}',pin) or pin!=hp.get('sha256'):return dict(ok=False,code='generation-mismatch')
        count=hp.get('readings')
        if type(count) is not int or not 0<=count<=256:return dict(ok=False,code='invalid-health')
        return dict(ok=True,code='fresh',source_at=hp['source_at'],last_received_at=hp['received_at'],readings=count)
    except (ValueError,TypeError,AttributeError,OverflowError):return dict(ok=False,code='invalid-health')
