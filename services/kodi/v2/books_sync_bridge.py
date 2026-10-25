"""Optional HP progress bindings layered on the unchanged private audio bridge."""
import secrets,time,urllib.request,json
from urllib.parse import urlsplit
from books_progress import Scope,timeline,resume_target,require,seconds
from books_progress_reader import Reader
from books_sync import Binding,Registry,Writer,ACCOUNT
from resources.lib.bridge import Bridge,ID,INO,TTL

def book_files(media):
    """Authoritative inode/index/contiguous-track agreement, not filename order."""
    files=media.get('audioFiles')
    require(isinstance(files,list) and 0<len(files)<=1000,'book-file-count')
    inodes=[]
    for file in files:
        require(isinstance(file,dict) and not file.get('exclude') and not file.get('error'),'book-file-unavailable')
        inode=str(file.get('ino'))
        require(INO.fullmatch(inode) and inode not in inodes,'book-file-identity')
        inodes.append(inode)
    spans=timeline([f.get('duration') for f in files])
    if len(files)>1:
        tracks=media.get('tracks')
        require(isinstance(tracks,list) and len(tracks)==len(files),'book-track-map-required')
        for index,(file,track,span) in enumerate(zip(files,tracks,spans),1):
            require(isinstance(track,dict) and str(track.get('ino'))==inodes[index-1]
                and type(file.get('index')) is int and file['index']==index
                and type(track.get('index')) is int and track['index']==index,'book-track-order-identity')
            require(not track.get('exclude') and not track.get('error'),'book-track-unavailable')
            require(abs(seconds(track.get('duration'))-span.duration)<=.05
                and abs(seconds(track.get('startOffset'))-span.start)<=.05,'book-track-timeline-mismatch')
    return tuple(inodes),spans

class ProgressBridge(Bridge):
    def __init__(self,server_url,api_key,directory,**kwargs):
        super().__init__(server_url,api_key,**kwargs)
        self.registry=Registry(clock=self.clock)
        self.reader=Reader(self.progress_upstream)
        self.writer=Writer(self.reader,self.patch_progress,directory)
    def progress_upstream(self,path,method='GET'):
        require(method=='GET','progress-reads-only')
        request=urllib.request.Request(self.server_url+path,headers={'Authorization':'Bearer '+self.api_key},method='GET')
        return self.opener.open(request,timeout=3)
    def patch_progress(self,scope,payload):
        # Called only by Writer after account/revision/ownership/journal checks.
        require(scope.kind in ('audiobook','podcast') and ID.fullmatch(scope.item)
            and (scope.episode is None or ID.fullmatch(scope.episode))
            and scope.episode!='remove-from-continue-listening','progress-write-route')
        require(set(payload)=={'duration','currentTime','progress','isFinished'} and payload['isFinished'] is False,'position-only-pilot')
        path='/api/me/progress/'+scope.item+('/'+scope.episode if scope.episode else '')
        request=urllib.request.Request(self.server_url+path,data=json.dumps(payload).encode(),method='PATCH',
            headers={'Authorization':'Bearer '+self.api_key,'Content-Type':'application/json'})
        with self.opener.open(request,timeout=3) as response:return response.status==200
    def clone_resume(self,entry,item,inode,offset):
        token=secrets.token_urlsafe(32)
        with self.lock:self.capabilities[token]=(item,inode,self.clock()+TTL)
        value=dict(entry,url='http://127.0.0.1:'+str(self.http.server_port)+'/audio/'+token,
            start_offset=offset,title='Resume · household position',number='R',progress_sync='Shared household Resume')
        return value
    def describe(self,kind,item_id):
        with self.lock:
            self.capabilities={key:value for key,value in self.capabilities.items() if value[2]>self.clock()}
            # Base describe can issue 1000 file and 500 chapter capabilities.
            if len(self.capabilities)>6500:
                from resources.lib.bridge import BridgeError
                raise BridgeError('Audio session capacity reached; reopen after a service restart.')
        entries=super().describe(kind,item_id)
        for entry in entries:entry['progress_sync']='Playback only · progress unavailable'
        try:
            account=self.writer.account();metadata=self.metadata(item_id)
            require(metadata.get('id')==item_id and metadata.get('mediaType')==('book' if kind=='audiobook' else 'podcast'),'binding-metadata-identity')
            media=metadata['media'];resume_entry=None
            book_progress=self.reader.progress(account,kind,item_id) if kind=='audiobook' else None
            if kind=='audiobook':
                try:book_inodes,book_spans=book_files(media)
                except Exception:
                    for entry in entries:entry['progress_sync']='Playback only · multi-file mapping not verified'
                    return entries
            for entry in entries:
                # This is a lookup of a capability generated by this very bridge,
                # not inference of content IDs from a URL, label or list position.
                private=self.lookup(urlsplit(entry['url']).path)
                require(private is not None and private[0]==item_id,'binding-capability-changed')
                inode=private[1];episode=None
                if kind=='audiobook':
                    require(inode in book_inodes,'book-capability-file-not-mapped')
                    spans=book_spans;file_index=book_inodes.index(inode)
                else:
                    episodes=media.get('episodes',[])
                    require(isinstance(episodes,list) and len(episodes)<=1000,'bounded-podcast-binding')
                    matches=[r for r in episodes if isinstance(r,dict) and isinstance(r.get('audioFile'),dict)
                        and str(r['audioFile'].get('ino'))==inode]
                    if len(matches)!=1:continue
                    episode=matches[0]['id'];duration=matches[0]['audioFile'].get('duration')
                    spans=timeline([duration]);file_index=0
                scope=Scope(account.identity,kind,item_id,episode)
                entry['episode_id']=episode or ''
                offset=seconds(entry.get('start_offset',0))
                require(offset<spans[file_index].duration,'chapter-offset-outside-file')
                binding=Binding(scope,spans,file_index,offset,kind=='podcast',self.clock()+TTL)
                self.registry.add(entry['url'],binding)
                entry['progress_sync']='Shared household position'
                if book_progress is not None and book_progress.finished:entry['progress_sync']='Completed · playback only; progress unchanged'
                if kind=='audiobook' and resume_entry is None:
                    progress=book_progress
                    if progress is not None and not progress.finished and progress.position>0:
                        index,offset=resume_target(progress,spans)
                        value=self.clone_resume(entry,item_id,book_inodes[index],offset)
                        # The row identifies the whole-book position, not the
                        # remaining length of whichever file contains it.
                        value['title']='Resume · '+clock_label(progress.position)
                        value['resume_position']=progress.position
                        value['duration']=spans[index].duration-offset
                        self.registry.add(value['url'],Binding(scope,spans,index,offset,True,self.clock()+TTL))
                        resume_entry=value
            if resume_entry:entries.insert(0,resume_entry)
        except Exception:
            # Streaming remains usable; observer independently verifies every
            # binding and blocks sync if the account/metadata becomes unavailable.
            pass
        return entries

def clock_label(seconds):
    value=int(seconds);return f'{value//3600}:{value//60%60:02d}:{value%60:02d}'
