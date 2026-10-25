"""Bounded GET-only ABS projections using an existing private bridge transport.

No credential parameters, URLs in results, persistent writes or progress writes.
The transport must retain TLS and redirect refusal from the existing bridge.
"""
from dataclasses import dataclass,field
import hashlib,json,urllib.error
from books_progress import Scope,ProgressUnavailable,identifier,snapshot,require
MAX_RESPONSE=2*1024*1024

@dataclass(frozen=True)
class Account:
    identity:str=field(repr=False)
    role:str
    locked:bool
    permissions:tuple
    @property
    def fingerprint(self):return hashlib.sha256(self.identity.encode()).hexdigest()
    @property
    def limited(self):
        return self.role=='user' and not self.locked and not any(
            value for key,value in self.permissions if key in ('update','delete','upload'))

class Reader:
    def __init__(self,upstream):self.upstream=upstream
    def _get(self,path,*,missing=False):
        # ABS also has mutating GET routes: method=GET alone is not a boundary.
        if path!='/api/me':
            require(path.startswith('/api/me/progress/'),'read-only-progress-route-required')
            parts=path[len('/api/me/progress/'):].split('/')
            require(len(parts) in (1,2) and all(identifier(p) for p in parts)
                and 'remove-from-continue-listening' not in parts,'read-only-progress-route-required')
        try:
            with self.upstream(path,method='GET') as response:
                if response.status==404 and missing:return None
                require(response.status==200,'progress-service-unavailable')
                raw=response.read(MAX_RESPONSE+1)
            require(len(raw)<=MAX_RESPONSE,'progress-response-too-large')
            value=json.loads(raw)
            require(isinstance(value,dict),'invalid-progress-response')
            return value
        except urllib.error.HTTPError as error:
            if error.code==404 and missing:return None
            raise ProgressUnavailable('progress-service-unavailable') from None
        except ProgressUnavailable:raise
        except Exception:raise ProgressUnavailable('progress-service-unavailable') from None
    def account(self):
        row=self._get('/api/me');identity=identifier(row.get('id'));role=row.get('type');locked=row.get('isLocked',False)
        require(role in ('root','admin','user','guest') and type(locked) is bool,'invalid-progress-account')
        permissions=row.get('permissions');require(isinstance(permissions,dict),'invalid-progress-permissions')
        values=tuple((key,permissions.get(key)) for key in ('download','update','delete','upload'))
        require(all(type(value) is bool for key,value in values),'invalid-progress-permissions')
        return Account(identity,role,locked,values)
    def progress(self,account,kind,item,episode=None):
        require(isinstance(account,Account) and account.limited,'limited-progress-account-required')
        scope=Scope(account.identity,kind,item,episode)
        path='/api/me/progress/'+scope.item+('/'+scope.episode if scope.episode is not None else '')
        value=snapshot(scope,self._get(path,missing=True))
        require(self.account()==account,'progress-account-changed')
        return value
