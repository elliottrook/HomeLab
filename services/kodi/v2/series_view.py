"""Small deterministic focus model; exact IDs survive season round trips."""
class SeriesSelection:
    def __init__(self,page,episode_id=None):
        self.page=page;self.remembered={}
        self.season,self.index=page.restore(episode_id) or (0,0)

    @property
    def group(self):return self.page.seasons[self.season] if self.page.seasons else None

    @property
    def episode(self):return self.group.episodes[self.index] if self.group else None

    def select(self,index):
        if self.group and type(index) is int and 0<=index<len(self.group.episodes):
            self.index=index;self.remembered[self.group.number]=self.episode.selection_key

    def change_season(self,index):
        if type(index) is not int or not 0<=index<len(self.page.seasons):return False
        if self.group:self.remembered[self.group.number]=self.episode.selection_key
        group=self.page.seasons[index];identity=self.remembered.get(group.number)
        self.season,self.index=self.page.restore(identity,season=group.number)
        return True

    def follow_episode(self,identity):
        """Restore only an exact positively observed playing episode."""
        if type(identity) is not int:return False
        position=self.page.restore(identity)
        if position is None:return False
        season,index=position
        if self.page.seasons[season].episodes[index].episode_id!=identity:return False
        if self.group:self.remembered[self.group.number]=self.episode.selection_key
        self.season,self.index=position
        self.remembered[self.group.number]=identity
        return True

def episode_metadata(row):
    duration=f'{int(row.duration)//60} min' if row.duration else 'Duration unavailable'
    return row.numbering+' · '+duration+' · '+(row.first_aired or 'Air date unavailable')
