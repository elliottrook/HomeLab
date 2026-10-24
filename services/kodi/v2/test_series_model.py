import copy
import unittest
from series_model import build_series,SeriesUnavailable


def episode(identity=1,season=1,number=1,**values):
    return dict(episodeid=identity,tvshowid=12,season=season,episode=number,
        label='Synthetic episode',file='plugin://fixture/play',**values)


class SeriesTests(unittest.TestCase):
    def page(self,rows,**values):
        return build_series(12,rows,expected_total=len(rows),today='2026-10-24',**values)

    def test_single_season_no_redundant_picker_and_new_show_play(self):
        page=self.page([episode()]);self.assertFalse(page.show_season_picker)
        self.assertEqual((page.primary_episode_id,page.primary_action),(1,'play'))

    def test_multiple_seasons_sorted_and_specials_reachable(self):
        page=self.page([episode(3,0,2),episode(2,2,1),episode()])
        self.assertEqual([s.label for s in page.seasons],['Season 1','Season 2','Specials'])
        self.assertTrue(page.show_season_picker)

    def test_real_numbering_including_zero_never_synthesized(self):
        page=self.page([episode(1,0,0),episode(2,None,None)])
        self.assertEqual(page.seasons[0].episodes[0].numbering,'S0 E0')
        self.assertEqual(page.seasons[1].episodes[0].numbering,'Episode number unavailable')
        self.assertIsNone(page.primary_episode_id)

    def test_resume_wins_over_supplied_upnext_and_keeps_fractional_progress(self):
        rows=[episode(resume={'position':12.5,'total':100},lastplayed='2026-10-23'),episode(2,1,2)]
        page=self.page(rows,next_episode_id=2)
        self.assertEqual((page.primary_episode_id,page.primary_action),(1,'resume'))
        self.assertEqual(page.seasons[0].episodes[0].progress_percent,12.5)

    def test_latest_resume_and_exact_source_id_restoration(self):
        rows=[episode(resume={'position':10,'total':100},lastplayed='2026-10-22'),
            episode(2,1,2,resume={'position':20,'total':100},lastplayed='2026-10-24')]
        page=self.page(list(reversed(rows)));self.assertEqual(page.primary_episode_id,2)
        self.assertEqual(page.restore(2),(0,1))
        self.assertEqual(page.restore(999,season=1),(0,0))

    def test_caught_up_never_invents_new_episode(self):
        page=self.page([episode(playcount=1)])
        self.assertEqual((page.primary_episode_id,page.primary_action),(None,'browse'))

    def test_watched_special_does_not_advance_regular_series(self):
        page=self.page([episode(2,0,1,playcount=1),episode()])
        self.assertEqual((page.primary_episode_id,page.primary_action),(1,'play'))

    def test_multiple_versions_keep_distinct_ids_and_real_numbering(self):
        page=self.page([episode(2),episode()])
        self.assertEqual([row.episode_id for row in page.seasons[0].episodes],[1,2])
        self.assertEqual([row.numbering for row in page.seasons[0].episodes],['S1 E1','S1 E1'])

    def test_unknown_season_does_not_steal_default_focus(self):
        page=self.page([episode(),episode(2,None,None)])
        self.assertEqual(page.restore(),(0,0))
        self.assertEqual(page.restore(season=None),(1,0))

    def test_only_accepted_upnext_identity_is_used(self):
        rows=[episode(playcount=1),episode(2,1,2)]
        self.assertIsNone(self.page(rows).primary_episode_id)
        self.assertEqual(self.page(rows,next_episode_id=2).primary_episode_id,2)
        self.assertIsNone(self.page(rows,next_episode_id=999).primary_episode_id)

    def test_future_missing_and_watched_next_never_play(self):
        for values in ({'firstaired':'2027-01-01'},{'playcount':1}):
            rows=[episode(playcount=1),episode(2,1,2,**values)]
            self.assertIsNone(self.page(rows,next_episode_id=2).primary_episode_id)
        row=episode();row['file']=''
        self.assertIsNone(self.page([row],next_episode_id=1).primary_episode_id)

    def test_first_unavailable_is_not_skipped_for_new_series(self):
        row=episode();row['file']=''
        self.assertIsNone(self.page([row,episode(2,1,2)]).primary_episode_id)

    def test_missing_airdate_not_invented_and_source_paths_not_retained(self):
        row=self.page([episode()]).seasons[0].episodes[0]
        self.assertEqual(row.first_aired,'');self.assertTrue(row.available)
        self.assertFalse(hasattr(row,'file'))

    def test_unknown_duration_and_invalid_resume_have_no_false_progress(self):
        for value in (None,-1,True,float('nan'),float('inf'),'90',10**1000):
            row=self.page([episode(runtime=value,resume={'position':value,'total':100})]).seasons[0].episodes[0]
            self.assertIsNone(row.duration);self.assertIsNone(row.progress_percent)
        self.assertIsNone(self.page([episode(runtime=0)]).seasons[0].episodes[0].duration)
        for position in (0,100,101):
            row=self.page([episode(resume={'position':position,'total':100})]).seasons[0].episodes[0]
            self.assertIsNone(row.resume_seconds)

    def test_empty_snapshot_has_safe_escape_without_fake_season(self):
        page=self.page([]);self.assertEqual(page.seasons,());self.assertIsNone(page.restore())

    def test_snapshot_complete_identity_and_watch_state_guards(self):
        with self.assertRaises(SeriesUnavailable):build_series(12,[episode()],expected_total=2)
        for rows in ([episode(),episode()], [dict(episode(),tvshowid=99)],
                     [dict(episode(),episodeid=True)], [episode(playcount=True)],
                     [episode(firstaired='not-a-date')]):
            with self.subTest(rows=rows),self.assertRaises(SeriesUnavailable):self.page(rows)

    def test_inputs_not_mutated(self):
        rows=[episode(2,2,1),episode()];before=copy.deepcopy(rows)
        self.page(rows);self.assertEqual(rows,before)
