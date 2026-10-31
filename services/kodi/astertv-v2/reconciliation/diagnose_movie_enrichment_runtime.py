"""Content-free execution check for the installed movie enrichment function."""
import importlib.util
from pathlib import Path
import xbmc
import xbmcgui
root=Path('/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22')
spec=importlib.util.spec_from_file_location('aster_movie_diagnostic',root/'movie.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
identity=xbmcgui.Window(11130).getProperty('Movie.Id');result={'valid_id':identity.isdecimal()}
try:
    value=module.read_movie(module.rpc,int(identity));people,related=module.enrichment(value)
    result.update(people=len(people),related=len(related))
except Exception as error:result['error']=type(error).__name__+':'+str(error)[:80]
xbmc.log('AsterMovieEnrichmentRuntime: '+repr(result),xbmc.LOGINFO)
