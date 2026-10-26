"""Native HP wrapper for the series catalogue component upgrade."""
import json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from series_catalogue_upgrade_install import inspect,run
def require(value,code):
    if not value:raise AssertionError(code)
require(os.uname().nodename=='AsterTV' and len(sys.argv)==2,'catalogue-upgrade-hp-arguments')
pin=sys.argv[1];require(re.fullmatch('[0-9a-f]{64}',pin),'catalogue-upgrade-pin')
inspect(ROOT,pin)
def idle():
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))
    return not reply.get('result') and xbmcgui.getCurrentWindowId()==10000
try:
    result=run(ROOT,Path('/storage'),pin,idle=idle)
    xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1500)
    require(xbmcgui.getCurrentWindowId()==10000,'catalogue-upgrade-home-return')
    result.update(passed=True,timestamp_ns=time.time_ns())
except (OSError,ValueError,AssertionError,KeyError) as error:
    result=dict(passed=False,code=str(error) if re.fullmatch('[a-z0-9-]{1,100}',str(error)) else type(error).__name__)
(ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
