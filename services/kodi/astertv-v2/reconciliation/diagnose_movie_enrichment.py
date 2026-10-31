"""Content-free JSON-RPC shape check for the current movie enrichment."""
import json
import xbmc
import xbmcgui
w=xbmcgui.Window(11130);identity=w.getProperty('Movie.Id')
result={'valid_id':identity.isdecimal()}
if identity.isdecimal():
    req={'jsonrpc':'2.0','id':1,'method':'VideoLibrary.GetMovieDetails','params':{
        'movieid':int(identity),'properties':['cast','director','writer','genre']}}
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(req)));result['error']=reply.get('error',{}).get('message','')
    row=reply.get('result',{}).get('moviedetails',{});result.update({k:type(row.get(k)).__name__ for k in ('cast','director','writer','genre')})
    result['cast_count']=len(row.get('cast',[]));result['director_count']=len(row.get('director',[]));result['genre_count']=len(row.get('genre',[]))
    result['cast_keys']=sorted(row['cast'][0]) if row.get('cast') and isinstance(row['cast'][0],dict) else []
xbmc.log('AsterMovieEnrichmentDiagnostic: '+repr(result),xbmc.LOGINFO)
