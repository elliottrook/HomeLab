"""Content-free check that started podcast episodes expose Resume rows."""
import json
import sys
from pathlib import Path
import xbmc
import xbmcvfs

tools = Path(xbmcvfs.translatePath('special://home/addons/skin.asterhome/tools'))
audio = Path(xbmcvfs.translatePath('special://home/addons/plugin.audio.asterbooks'))
sys.path.insert(0, str(tools)); sys.path.insert(0, str(audio))
from hub_feeds import book_catalogue, read_feed
from resources.lib.bridge import CONTROL_SOCKET, control_request

feed = Path(xbmcvfs.translatePath('special://profile/addon_data/skin.asterhome/feeds/books.json'))
profile = Path(xbmcvfs.translatePath('special://profile/addon_data/plugin.audio.asterbooks'))
podcasts = [row for row in book_catalogue(read_feed(feed)) if row['kind'] == 'podcast']
described = resumes = failures = 0
for row in podcasts[:100]:
    try:
        entries = control_request(profile / CONTROL_SOCKET, 'podcast', row['id'])
        described += 1
        resumes += sum(1 for entry in entries if entry.get('number') == 'R')
    except Exception:
        failures += 1
xbmc.log('AsterPodcastResumeDiagnostic: ' + repr({
    'catalogue': len(podcasts), 'described': described,
    'resume_rows': resumes, 'failures': failures}), xbmc.LOGINFO)
