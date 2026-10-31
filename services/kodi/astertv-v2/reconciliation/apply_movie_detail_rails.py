#!/usr/bin/env python3
"""Add guarded Cast & Crew and More Like This rails to the v2 movie page."""
import hashlib,json,os
from pathlib import Path
import socket,subprocess

ADDONS=Path('/storage/.kodi/addons');RUNTIME=ADDONS/'script.asterruntime';SEARCH=RUNTIME/'aster-global-search-ui22';SKIN=ADDONS/'skin.asterhome'
PATHS={'movie':SEARCH/'movie.py','player':SEARCH/'resources/lib/movie_player.py',
 'overlay':SEARCH/'overlay/custom_1130_movie.xml','manifest':SEARCH/'manifest.json',
 'live':SKIN/'1080i/custom_1130_movie.xml','family':RUNTIME/'family-manifest.json'}
EXPECTED={'movie':'ea4498ff12c08c36a6313c9700add7d6c4b4e0112eaef39038f6ccdb9d958942',
 'player':'8dfc037fa41ca5a567909df0e29fdbed343b12be843025bb4064d3558e4d87ff',
 'overlay':'86c34e131a40afcda6fdbfe466096a16babdb172c73cbb6d91eaf6f3a2e0d2e2',
 'manifest':'e38723816514699b867fba68b8ac4b703c3355782cdc6ec387bb8931becc7a07',
 'live':'86c34e131a40afcda6fdbfe466096a16babdb172c73cbb6d91eaf6f3a2e0d2e2',
 'family':'d1a420e72c2863fef6e9a2a49200c9d3b43d8989477fdb236f6a97901507b09f'}
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-v2-r11-movie-detail-rails-20261030')
def sha(data):return hashlib.sha256(data).hexdigest()
def encode(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def one(text,old,new,label):
 if text.count(old)!=1:raise RuntimeError(label+'-anchor')
 return text.replace(old,new,1)
def idle():
 req={'jsonrpc':'2.0','id':1,'method':'Player.GetActivePlayers'}
 with socket.create_connection(('127.0.0.1',9090),timeout=3) as c:c.sendall((json.dumps(req)+'\n').encode());a=json.loads(c.recv(4096).decode())
 if a.get('result')!=[]:raise RuntimeError('active-player')
def main():
 idle();old={n:p.read_bytes() for n,p in PATHS.items()}
 for n,h in EXPECTED.items():
  if sha(old[n])!=h:raise RuntimeError('unexpected-live-hash:'+n)
 player=old['player'].decode();player=one(player,
  "READS=frozenset(('VideoLibrary.GetMovieDetails','Player.GetActivePlayers','Playlist.GetItems','Player.GetItem'))",
  "READS=frozenset(('VideoLibrary.GetMovieDetails','VideoLibrary.GetMovies','Player.GetActivePlayers','Playlist.GetItems','Player.GetItem'))",'movie-reads').encode()
 movie=old['movie'].decode()
 anchor="""def admitted_source(movie_id):
"""
 helper="""def enrichment(movie):
    people=[];related=[]
    try:
        detail=rpc('VideoLibrary.GetMovieDetails',dict(movieid=movie.movie_id,
            properties=['cast','director','writer','genre'])).get('moviedetails',{})
        cast=detail.get('cast',[]);directors=detail.get('director',[]);writers=detail.get('writer',[])
        if not isinstance(cast,list) or not isinstance(directors,list) or not isinstance(writers,list):raise ValueError('movie-people')
        for row in cast[:16]:
            if isinstance(row,dict) and isinstance(row.get('name'),str):
                people.append((row['name'],str(row.get('role') or 'Cast'),str(row.get('thumbnail') or '')))
        for name,role in [(n,'Director') for n in directors[:4]]+[(n,'Writer') for n in writers[:4]]:
            if isinstance(name,str) and name and not any(p[0]==name and p[1]==role for p in people):people.append((name,role,''))
        genre=next((g for g in detail.get('genre',[]) if isinstance(g,str) and g),None)
        if genre:
            result=rpc('VideoLibrary.GetMovies',dict(properties=['title','thumbnail','year'],
                filter={'field':'genre','operator':'contains','value':genre},
                sort={'method':'rating','order':'descending'},limits={'start':0,'end':30}))
            for row in result.get('movies',[]):
                identity=row.get('movieid')
                if type(identity) is int and identity!=movie.movie_id and isinstance(row.get('title'),str):
                    related.append((identity,row['title'],str(row.get('thumbnail') or ''),row.get('year',0)))
                    if len(related)==14:break
    except (MovieUnavailable,ValueError,KeyError,TypeError):pass
    return people,related

"""+anchor
 movie=one(movie,anchor,helper,'movie-enrichment')
 render_anchor="""            window.setProperty('Movie.Ready','true')
            window.setProperty('Movie.Phase',session.phase)
"""
 render_new="""            people,related=enrichment(value)
            cast_control=window.getControl(500);cast_control.reset()
            for name,role,thumb in people:
                item=xbmcgui.ListItem(label=name,label2=role);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_control.addItem(item)
            related_control=window.getControl(501);related_control.reset()
            for identity,title,thumb,year in related:
                item=xbmcgui.ListItem(label=title,label2=str(year) if year else '')
                item.setProperty('MovieId',str(identity));item.setArt({'thumb':thumb or 'special://skin/media/08-film.png'});related_control.addItem(item)
            window.setProperty('Movie.CastVisible','true' if people else 'false')
            window.setProperty('Movie.RelatedVisible','true' if related else 'false')
            window.setProperty('Movie.Ready','true')
            window.setProperty('Movie.Phase',session.phase)
"""
 movie=one(movie,render_anchor,render_new,'movie-render-rails')
 command_anchor="""            if command in ('play','resume') and current==11130 and session.phase=='idle':
"""
 command_new="""            if command=='related' and current==11130 and session.phase=='idle':
                try:
                    identity=window.getControl(501).getSelectedItem().getProperty('MovieId')
                    require(identity.isdecimal(),'invalid-related-movie')
                    value=read_movie(rpc,int(identity));session=MovieSession(rpc,value.movie_id);render();xbmc.executebuiltin('SetFocus(200)')
                except (MovieUnavailable,ValueError,AttributeError):window.setProperty('Movie.Status','That related title is currently unavailable.')
            if command in ('play','resume') and current==11130 and session.phase=='idle':
"""
 movie=one(movie,command_anchor,command_new,'movie-related-command').encode()
 xml=old['live'].decode()
 replacements=[
  ('<top>275</top><width>330</width><height>495</height>','<top>175</top><width>300</width><height>450</height>'),
  ('<top>210</top><width>1200</width><height>100</height>','<top>145</top><width>1200</width><height>75</height>'),
  ('<top>310</top><width>1200</width><height>45</height>','<top>225</top><width>1200</width><height>42</height>'),
  ('<top>380</top><width>1200</width><height>245</height>','<top>285</top><width>1200</width><height>170</height>'),
  ('<top>645</top><width>1200</width><height>42</height>','<top>470</top><width>1200</width><height>42</height>'),
  ('<top>725</top><width>96</width><height>90</height>','<top>520</top><width>96</width><height>90</height>'),
  ('<top>735</top><width>76</width><height>70</height>','<top>530</top><width>76</width><height>70</height>'),
  ('<top>748</top><width>44</width><height>44</height>','<top>543</top><width>44</width><height>44</height>'),
  ('<top>746</top><width>48</width><height>48</height>','<top>541</top><width>48</width><height>48</height>'),
  ('<top>818</top><width>200</width><height>40</height>','<top>610</top><width>200</width><height>40</height>'),
  ('<top>818</top><width>240</width><height>40</height>','<top>610</top><width>240</width><height>40</height>'),
  ('<top>910</top><width>1200</width><height>100</height>','<top>655</top><width>1200</width><height>40</height>')]
 for before,after in replacements:
  if before not in xml:raise RuntimeError('movie-layout-anchor:'+before)
  xml=xml.replace(before,after)
 xml=xml.replace('<ondown>202</ondown>','<ondown>500</ondown>',2)
 rails="""
    <control type="label"><left>145</left><top>700</top><width>1600</width><height>34</height><label>Cast &amp; Crew</label><font>font24</font><textcolor>asterInk</textcolor><visible>String.IsEqual(Window.Property(Movie.CastVisible),true)</visible></control>
    <control type="list" id="500"><left>145</left><top>738</top><width>1640</width><height>126</height><orientation>horizontal</orientation><onup>200</onup><ondown>501</ondown><onleft>500</onleft><onright>500</onright><visible>String.IsEqual(Window.Property(Movie.CastVisible),true)</visible><itemlayout width="160" height="126"><control type="image"><left>6</left><width>92</width><height>92</height><texture>$INFO[ListItem.Art(thumb)]</texture><aspectratio>scale</aspectratio></control><control type="label"><left>4</left><top>94</top><width>150</width><height>28</height><label>$INFO[ListItem.Label]</label><font>font16</font><textcolor>asterInk</textcolor><truncate>true</truncate></control></itemlayout><focusedlayout width="160" height="126"><control type="image"><width>104</width><height>104</height><texture border="20" colordiffuse="asterGreen">special://skin/media/ui-compact-card-ring.png</texture></control><control type="image"><left>6</left><top>6</top><width>92</width><height>92</height><texture>$INFO[ListItem.Art(thumb)]</texture><aspectratio>scale</aspectratio></control><control type="label"><left>4</left><top>100</top><width>150</width><height>26</height><label>$INFO[ListItem.Label]</label><font>font16</font><textcolor>asterGreen</textcolor><truncate>true</truncate></control></focusedlayout></control>
    <control type="label"><left>145</left><top>870</top><width>1600</width><height>34</height><label>More Like This</label><font>font24</font><textcolor>asterInk</textcolor><visible>String.IsEqual(Window.Property(Movie.RelatedVisible),true)</visible></control>
    <control type="list" id="501"><left>145</left><top>908</top><width>1640</width><height>164</height><orientation>horizontal</orientation><onup>500</onup><ondown>200</ondown><onleft>501</onleft><onright>501</onright><onclick>SetProperty(AsterMovie.Command,related,home)</onclick><visible>String.IsEqual(Window.Property(Movie.RelatedVisible),true)</visible><itemlayout width="132" height="164"><control type="image"><left>6</left><width>112</width><height>132</height><texture diffuse="special://skin/media/ui-poster-mask.png">$INFO[ListItem.Art(thumb)]</texture><aspectratio scalediffuse="false">scale</aspectratio></control><control type="label"><left>4</left><top>134</top><width>124</width><height>28</height><label>$INFO[ListItem.Label]</label><font>font16</font><textcolor>asterInk</textcolor><truncate>true</truncate></control></itemlayout><focusedlayout width="132" height="164"><control type="image"><width>124</width><height>144</height><texture border="20" colordiffuse="asterGreen">special://skin/media/ui-compact-card-ring.png</texture></control><control type="image"><left>6</left><top>6</top><width>112</width><height>132</height><texture diffuse="special://skin/media/ui-poster-mask.png">$INFO[ListItem.Art(thumb)]</texture><aspectratio scalediffuse="false">scale</aspectratio></control><control type="label"><left>4</left><top>140</top><width>124</width><height>24</height><label>$INFO[ListItem.Label]</label><font>font16</font><textcolor>asterGreen</textcolor><truncate>true</truncate></control></focusedlayout></control>
"""
 xml=one(xml,'  </controls>\n</window>',rails+'  </controls>\n</window>','movie-rails').encode()
 manifest=json.loads(old['manifest'])
 members={'movie.py':movie,'resources/lib/movie_player.py':player,'overlay/custom_1130_movie.xml':xml}
 for row in manifest['files']:
  if row['path'] in members:row['bytes']=len(members[row['path']]);row['sha256']=sha(members[row['path']])
 manifest=encode(manifest)
 family=json.loads(old['family']);family['components']['aster-global-search-ui22']['manifest_sha256']=sha(manifest);family['skin']['1080i/custom_1130_movie.xml']=sha(xml);family=encode(family)
 new={'movie':movie,'player':player,'overlay':xml,'manifest':manifest,'live':xml,'family':family}
 CHECKPOINT.mkdir(mode=0o700);record={'kind':'astertv-v2-r11-movie-detail-rails','files':{}}
 for n,p in PATHS.items():(CHECKPOINT/(n+'__'+p.name)).write_bytes(old[n]);record['files'][str(p.relative_to(ADDONS))]={'before':sha(old[n]),'after':sha(new[n])}
 (CHECKPOINT/'manifest.json').write_bytes(encode(record));subprocess.run(['systemctl','stop','kodi'],check=True)
 try:
  for n,p in PATHS.items():t=p.with_suffix(p.suffix+'.r11rails');t.write_bytes(new[n]);os.chmod(t,p.stat().st_mode&0o777);os.replace(t,p)
 finally:subprocess.run(['systemctl','start','kodi'],check=True)
 print(json.dumps({'checkpoint':str(CHECKPOINT),'movie':sha(movie),'xml':sha(xml),'manifest':sha(manifest),'family':sha(family)},sort_keys=True))
if __name__=='__main__':main()
