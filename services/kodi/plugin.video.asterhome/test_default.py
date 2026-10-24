"""Kodi adapter tests with fake runtime modules; no household state writes."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


class AdapterTests(unittest.TestCase):
    def setUp(self):
        modules = {name: Mock() for name in ('xbmc', 'xbmcgui', 'xbmcplugin')}
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location(
                'aster_video_default', Path(__file__).with_name('default.py'))
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def run_directory(self, truncate=False, failure=False):
        show = {'tvshowid': 1, 'label': 'Series', 'watchedepisodes': 1}
        episodes = [dict(tvshowid=1, season=1, episode=n, playcount=2-n,
                         episodeid=n, file='plugin://existing/play', showtitle='Series')
                    for n in (1, 2)]
        def rpc(method, *args, **kwargs):
            if method.endswith('GetMovies'): return {'movies': []}
            if method.endswith('GetTVShows'):
                if failure: raise ValueError('offline')
                return {'tvshows': [show]}
            if 'tvshowid' not in kwargs: return {'episodes': []}
            return {'episodes': episodes, 'limits': {'total': 2001 if truncate else 2}}
        with patch.object(self.module, 'rpc', side_effect=rpc), \
                patch.object(self.module, 'add_item') as add:
            self.module.add_continue_watching(1)
            return add.call_args_list

    def test_directory_includes_next_episode_from_complete_local_query(self):
        rows = self.run_directory()
        self.assertEqual(rows[0].args[1]['episode'], 2)
        self.assertTrue(rows[0].args[1]['next_up'])

    def test_truncated_query_does_not_create_caught_up_card(self):
        self.assertEqual(self.run_directory(truncate=True), [])

    def test_next_up_read_failure_still_finishes_directory(self):
        self.assertEqual(self.run_directory(failure=True), [])
        self.module.xbmcplugin.endOfDirectory.assert_called_once_with(1, cacheToDisc=False)

    def test_next_up_property_and_caught_up_folder_path(self):
        self.module.add_item(1, {'kind':'tvshow', 'id':42, 'label':'Caught up', 'next_up':True})
        item = self.module.xbmcgui.ListItem.return_value
        item.setProperty.assert_any_call('AsterUpNext', 'true')
        self.module.xbmcplugin.addDirectoryItem.assert_called_once_with(
            1, 'videodb://tvshows/titles/42/', item, isFolder=True)

    def test_series_beyond_old_recent_24_limit_is_considered(self):
        calls=[]
        def rpc(method, *args, **kwargs):
            if method.endswith('GetMovies'): return {'movies': []}
            if method.endswith('GetTVShows'):
                calls.append(kwargs['limits'])
                return {'tvshows':[{'tvshowid':i, 'watchedepisodes':1} for i in range(30)],
                        'limits':{'total':30}}
            if kwargs.get('tvshowid') == 29:
                return {'episodes':[
                    {'season':4,'episode':10,'playcount':1},
                    {'season':5,'episode':1,'playcount':0,'file':'plugin://existing/play'}]}
            return {'episodes':[]}
        with patch.object(self.module, 'rpc', side_effect=rpc), \
                patch.object(self.module, 'add_item') as add:
            self.module.add_continue_watching(1)
        self.assertEqual(calls,[{'start':0,'end':1000}])
        self.assertEqual(add.call_count,1)
        self.assertEqual(add.call_args.args[1]['season'],5)

    def test_incomplete_show_catalogue_keeps_only_genuine_resume(self):
        def rpc(method, *args, **kwargs):
            if method.endswith('GetMovies'):
                return {'movies':[{'label':'Movie','resume':{'position':1,'total':100}}]}
            if method.endswith('GetTVShows'):
                return {'tvshows':[{'tvshowid':1,'watchedepisodes':1}], 'limits':{'total':1001}}
            return {'episodes':[]}
        with patch.object(self.module, 'rpc', side_effect=rpc), \
                patch.object(self.module, 'add_item') as add:
            self.module.add_continue_watching(1)
        self.assertEqual(add.call_count,1)
        self.assertEqual(add.call_args.args[1]['kind'],'movie')


if __name__ == '__main__':
    unittest.main()
