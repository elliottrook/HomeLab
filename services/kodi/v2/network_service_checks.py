"""Explicit, fixed-LAN HTTP checks. No redirects, auth, bodies, DNS names or retries."""
from __future__ import annotations
from dataclasses import dataclass
import http.client
import time
from types import MappingProxyType

ENDPOINTS=MappingProxyType({'Jellyfin':('192.168.20.40',8096,'/health'),
                          'Audiobookshelf':('192.168.20.40',30067,'/ping')})
TIMEOUT_SECONDS=2


@dataclass(frozen=True)
class ServiceResult:
    name:str
    state:str
    status:int|None
    elapsed_ms:int


def check(name):
    if not isinstance(name,str) or name not in ENDPOINTS:raise ValueError('network-service-not-allowlisted')
    host,port,path=ENDPOINTS[name];start=time.monotonic();connection=None;status=None
    try:
        connection=http.client.HTTPConnection(host,port,timeout=TIMEOUT_SECONDS)
        connection.request('GET',path,headers={'Accept':'text/plain, application/json','Connection':'close'})
        response=connection.getresponse();status=response.status
        if type(status) is not int or not 100<=status<=599:
            status=None;state='Invalid HTTP response'
        elif status==200:state='Endpoint responded'
        elif 300<=status<400:state='Redirect returned; not followed'
        elif status in (401,403):state='Authentication required'
        elif status==404:state='Health path unavailable'
        elif status>=500:state='Service reported an error'
        else:state='HTTP response received'
        # Deliberately never read a body, header, cookie, redirect or server version.
    except TimeoutError:state='Timed out'
    except OSError:state='Connection unavailable'
    except http.client.HTTPException:state='Invalid HTTP response'
    finally:
        if connection is not None:connection.close()
    return ServiceResult(name,state,status,max(0,round((time.monotonic()-start)*1000)))


def check_all(keep_going=lambda:True):
    results=[]
    for name in ENDPOINTS:
        if not keep_going():break
        results.append(check(name))
    return tuple(results)
