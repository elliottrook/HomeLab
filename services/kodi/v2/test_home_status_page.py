import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,Mock

class PageTests(unittest.TestCase):
    def setUp(self):
        self.props={};self.commands=[];self.position=2
        self.listing=Mock();self.listing.getSelectedPosition.return_value=2
        self.window=Mock(getProperty=lambda key:self.props.get(key,''),setProperty=lambda k,v:self.props.__setitem__(k,v))
        self.window.getControl.return_value=self.listing
        self.xbmc=types.SimpleNamespace(executebuiltin=self.commands.append)
        self.gui=types.SimpleNamespace(getCurrentWindowId=lambda:11112,Window=lambda identity:self.window,
                                       ListItem=lambda title,detail:(title,detail))
        self.hub=types.SimpleNamespace(main=Mock())
        self.patch=patch.dict(sys.modules,{'xbmc':self.xbmc,'xbmcgui':self.gui,'hub_data':self.hub});self.patch.start()
        spec=importlib.util.spec_from_file_location('home_status_page_test',Path(__file__).parent/'home_status_page.py')
        self.page=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.page)
        self.folder=tempfile.TemporaryDirectory();self.page.FEED=Path(self.folder.name)/'feed.json'
        self.page.FEED.write_text(json.dumps(dict(schema_version=4,snapshot_id='ha-home-dashboard-v4',
            observed_at=datetime.now(timezone.utc).isoformat(),entities=[dict(id='light.room',name='Room',kind='light',availability='available',state='on')])))

    def tearDown(self):self.patch.stop();self.folder.cleanup()

    def test_entry_uses_existing_initializer_once_and_local_alarm(self):
        self.page.main('entry');self.hub.main.assert_called_once_with('home')
        self.assertTrue(any('AlarmClock(AsterHomeStatus' in cmd for cmd in self.commands))
        self.assertEqual(self.props['AsterHub.HomeSourceState'],'fresh')

    def test_refresh_preserves_timer_camera_and_selection(self):
        self.props.update({'AsterHub.HomeTimerActive':'true','AsterHub.HomeTimerDeadline':'fixed','AsterHub.CameraPlaying':'true'})
        self.page.main('refresh');self.hub.main.assert_not_called()
        for key,value in (('HomeTimerActive','true'),('HomeTimerDeadline','fixed'),('CameraPlaying','true')):
            self.assertEqual(self.props['AsterHub.'+key],value)
        self.listing.selectItem.assert_called_once_with(0)

    def test_other_window_never_uses_controls(self):
        self.gui.getCurrentWindowId=lambda:10000
        self.page.main('tick');self.window.getControl.assert_not_called();self.hub.main.assert_not_called()

    def test_leave_only_cancels_local_alarm_and_existing_cleanup(self):
        self.gui.getCurrentWindowId=lambda:10000
        self.page.main('leave');self.window.getControl.assert_not_called()
        self.hub.main.assert_called_once_with('home','home_stop')
        self.assertEqual(self.commands,['CancelAlarm(AsterHomeStatus,silent)'])

    def test_missing_and_symlink_values_hidden(self):
        original=self.page.FEED;self.page.FEED=original.with_name('missing')
        self.page.main('refresh');self.assertEqual(self.props['AsterHub.HomeLightValue'],'Unavailable')
        self.page.FEED.symlink_to(original)
        self.page.main('refresh');self.assertEqual(self.props['AsterHub.HomeSourceState'],'invalid')

if __name__=='__main__':unittest.main()
