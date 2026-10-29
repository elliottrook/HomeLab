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
        item.setProperty.assert_any_call('AsterMediaKind', 'tvshow')
        item.setProperty.assert_any_call('AsterDbId', '42')
        item.getVideoInfoTag.return_value.setDbId.assert_called_once_with(42)
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

    def test_recent_directory_queries_movies_and_series_and_finishes_uncached(self):
        calls = []
        def rpc(method, *args, **kwargs):
            calls.append((method, args, kwargs))
            if method.endswith('GetMovies'):
                return {'movies':[{'movieid':1, 'label':'Movie',
                                   'dateadded':'2026-10-22'}]}
            return {'tvshows':[{'tvshowid':2, 'label':'Series',
                                'dateadded':'2026-10-23'}]}
        with patch.object(self.module, 'rpc', side_effect=rpc), \
                patch.object(self.module, 'add_item') as add:
            self.module.add_recently_added(1)
        self.assertEqual([call.args[1]['kind'] for call in add.call_args_list],
                         ['tvshow', 'movie'])
        self.assertEqual([call[1][0] for call in calls],
                         [self.module.RECENT_PROPERTIES,
                          self.module.RECENT_PROPERTIES])
        self.module.xbmcplugin.endOfDirectory.assert_called_once_with(
            1, cacheToDisc=False)

    def test_recommendation_directory_uses_only_local_kodi_queries(self):
        calls = []
        def rpc(method, *args, **kwargs):
            calls.append((method, args, kwargs))
            if method.endswith('GetMovies'):
                return {'movies':[{'movieid':1, 'label':'Movie',
                                   'file':'/owned/movie.mkv',
                                   'art':{'fanart':'fanart.jpg'}}]}
            if method.endswith('GetEpisodes'):
                return {'episodes':[]}
            return {'tvshows':[]}
        with patch.object(self.module, 'rpc', side_effect=rpc), \
                patch.object(self.module, 'add_item') as add:
            self.module.add_recommended(1)
        self.assertEqual([call[0] for call in calls],
                         ['VideoLibrary.GetMovies', 'VideoLibrary.GetTVShows',
                          'VideoLibrary.GetEpisodes'])
        self.assertTrue(all(call[2]['limits'] == {'start':0, 'end':2000}
                            for call in calls))
        self.assertEqual(add.call_args.args[1]['file'], '/owned/movie.mkv')
        self.module.xbmcplugin.endOfDirectory.assert_called_once_with(
            1, cacheToDisc=False)

    def test_recommendation_refuses_incomplete_continue_exclusion_catalogue(self):
        def rpc(method, *args, **kwargs):
            if method.endswith('GetMovies'):
                return {'movies': []}
            if method.endswith('GetTVShows'):
                return {'tvshows': []}
            return {'episodes': [], 'limits': {'total': 2001}}
        with patch.object(self.module, 'rpc', side_effect=rpc):
            with self.assertRaisesRegex(ValueError, 'pagination stalled'):
                self.module.add_recommended(1)

    def test_episode_projection_is_paginated_to_completion(self):
        calls = []
        def rpc(method, properties, limits):
            calls.append(limits)
            start = limits['start']
            rows = [{'episodeid': value} for value in range(start, min(start + 2, 5))]
            return {'episodes': rows, 'limits': {'total': 5}}
        with patch.object(self.module, 'rpc', side_effect=rpc):
            rows = self.module.all_episodes(['episodeid'], page_size=2)
        self.assertEqual([row['episodeid'] for row in rows], list(range(5)))
        self.assertEqual(calls, [
            {'start': 0, 'end': 2}, {'start': 2, 'end': 4},
            {'start': 4, 'end': 6}])

    def test_idle_hero_tick_advances_without_moving_remote_focus(self):
        self.module.xbmcgui.getCurrentWindowId.return_value = 10000
        window = self.module.xbmcgui.Window.return_value
        window.getFocusId.return_value = 121
        self.module.rotate_hero()
        self.module.xbmc.executebuiltin.assert_called_once_with(
            'Control.Move(101,1)')

    def test_hero_tick_pauses_for_visible_media_rows(self):
        self.module.xbmcgui.getCurrentWindowId.return_value = 10000
        window = self.module.xbmcgui.Window.return_value
        for focus in (100, 110):
            with self.subTest(focus=focus):
                self.module.xbmc.executebuiltin.reset_mock()
                window.getFocusId.return_value = focus
                self.module.rotate_hero()
                self.module.xbmc.executebuiltin.assert_not_called()

    def test_hero_refreshes_once_after_day_changes(self):
        self.module.xbmcgui.getCurrentWindowId.return_value = 10000
        window = self.module.xbmcgui.Window.return_value
        window.getProperty.return_value = '2026-10-28'
        with patch.object(self.module, 'date') as clock:
            clock.today.return_value.isoformat.return_value = '2026-10-29'
            self.module.rotate_hero()
        window.setProperty.assert_called_once_with('AsterMediaHeroDay', '2026-10-29')
        self.module.xbmc.executebuiltin.assert_called_once_with('ReloadSkin')

    def test_hero_tick_is_inert_outside_home(self):
        self.module.xbmcgui.getCurrentWindowId.return_value = 10025
        self.module.rotate_hero()
        self.module.xbmc.executebuiltin.assert_not_called()


if __name__ == '__main__':
    unittest.main()
