"""Offline M4 progress planning, never an API client or write authorization.

Server identity comes from a separately verified account context. Episode IDs
are required for podcasts; neither row numbers nor local capability URLs are
progress identity. Preflight equality is not server-side compare-and-swap.
"""
from __future__ import annotations
from dataclasses import dataclass
import math,re

class ProgressUnavailable(ValueError):pass
def require(value,code):
    if not value:raise ProgressUnavailable(code)
def identifier(value):
    require(isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}',value),'invalid-progress-identity')
    return value
def seconds(value):
    require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=604800,'invalid-progress-time')
    return float(value)

@dataclass(frozen=True)
class Scope:
    account:str
    kind:str
    item:str
    episode:str|None=None
    def __post_init__(self):
        identifier(self.account);identifier(self.item)
        require(self.kind in ('audiobook','podcast'),'invalid-progress-kind')
        if self.kind=='podcast':identifier(self.episode)
        else:require(self.episode is None,'book-cannot-use-episode')

@dataclass(frozen=True)
class Progress:
    scope:Scope
    duration:float
    position:float
    finished:bool
    hidden:bool
    updated_ms:int

def snapshot(scope,row):
    """None means a confirmed server 404, not a timeout or network failure."""
    require(isinstance(scope,Scope),'verified-scope-required')
    if row is None:return None
    require(isinstance(row,dict) and row.get('libraryItemId')==scope.item
        and row.get('episodeId')==scope.episode,'progress-item-mismatch')
    duration=seconds(row.get('duration'));position=seconds(row.get('currentTime'))
    finished=row.get('isFinished');hidden=row.get('hideFromContinueListening',False);updated=row.get('lastUpdate')
    require(type(finished) is bool and type(hidden) is bool,'invalid-progress-flags')
    require(type(updated) is int and 0<=updated<=253402300799999,'invalid-progress-revision')
    # Finished records can legitimately have zero duration (manually completed).
    require((finished and duration==0) or position<=duration,'progress-outside-duration')
    return Progress(scope,duration,position,finished,hidden,updated)

@dataclass(frozen=True)
class Span:
    index:int
    start:float
    duration:float

def timeline(durations):
    """Already identity-verified file order; no paths or credentials accepted."""
    require(isinstance(durations,(list,tuple)) and 0<len(durations)<=1000,'invalid-file-count')
    spans=[];start=0.0
    for index,value in enumerate(durations):
        duration=seconds(value);require(duration>0,'unknown-file-duration')
        spans.append(Span(index,start,duration));start=seconds(start+duration)
    return tuple(spans)

def checked_timeline(spans):
    require(isinstance(spans,tuple) and 0<len(spans)<=1000,'verified-timeline-required')
    expected=0.0
    for index,span in enumerate(spans):
        require(isinstance(span,Span) and type(span.index) is int and span.index==index,'invalid-file-order')
        require(seconds(span.start)==expected and seconds(span.duration)>0,'invalid-file-span')
        expected=seconds(expected+span.duration)
    return expected

def resume_target(progress,spans):
    total=checked_timeline(spans)
    require(isinstance(progress,Progress),'server-progress-required')
    require(progress.duration>0 and abs(progress.duration-total)<=1,'progress-timeline-mismatch')
    if progress.finished:return None
    require(progress.position<total,'unfinished-at-end-needs-review')
    for span in spans:
        if progress.position<span.start+span.duration:return span.index,progress.position-span.start
    raise ProgressUnavailable('progress-not-mapped')

def global_position(spans,index,local_seconds):
    checked_timeline(spans)
    require(type(index) is int and 0<=index<len(spans),'unknown-playing-file')
    local=seconds(local_seconds);span=spans[index]
    require(local<=span.duration,'position-outside-file')
    return span.start+local

@dataclass(frozen=True)
class Draft:
    scope:Scope
    duration:float
    position:float
    finished:bool
    def payload(self):
        return dict(duration=self.duration,currentTime=self.position,
            progress=1.0 if self.finished else self.position/self.duration,isFinished=self.finished)

def propose(scope,baseline,fresh,spans,index,local_seconds,*,natural_end=False):
    """A non-executable draft. Any external change requires explicit resolution.

    No greater-position-wins rule, client-clock ordering, offline replay or
    completion from a seek alone. A future adapter must separately prove the
    account, current playback ownership, concurrency policy and write grant.
    """
    require(isinstance(scope,Scope),'verified-scope-required')
    require(all(p is None or isinstance(p,Progress) and p.scope==scope for p in (baseline,fresh)),
        'progress-account-or-item-mismatch')
    require(baseline==fresh,'server-progress-changed')
    require(fresh is None or not fresh.finished,'completed-item-needs-explicit-restart')
    total=checked_timeline(spans);position=global_position(spans,index,local_seconds)
    require(type(natural_end) is bool,'invalid-completion-event')
    if fresh is not None:require(abs(fresh.duration-total)<=1,'progress-timeline-mismatch')
    finished=natural_end and index==len(spans)-1 and total-position<=1
    return Draft(scope,total,position,finished)
