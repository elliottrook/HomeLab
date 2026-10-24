import copy
import random
import unittest

from music_policy import (CATEGORIES, OTHER, categories_for, is_holiday,
                          shuffle_candidates, shuffled_ids)


class MusicPolicyTests(unittest.TestCase):
    def test_canonical_labels_are_not_split_on_commas(self):
        self.assertEqual(categories_for({'genre':['Jazz, Blues, R&B & Soul']}),
                         (CATEGORIES[1],))

    def test_legacy_aliases_are_explicit(self):
        self.assertEqual(categories_for({'genre':['Funk Rock']}), (CATEGORIES[2],))
        self.assertEqual(categories_for({'genre':['Americana']}), (CATEGORIES[3],))
        self.assertEqual(categories_for({'genre':['Unknown future tag']}), (OTHER,))

    def test_track_genre_wins_over_album_for_browsing(self):
        self.assertEqual(categories_for({'genre':['Classical']}, {'genre':['Rock']}), ('Classical',))
        self.assertEqual(categories_for({'genre':[]}, {'genre':['Rock & Alternative']}), (CATEGORIES[2],))

    def test_holiday_aliases_and_unicode(self):
        for label in ('Christmas', ' HOLIDAY ', 'Holiday Music', 'Xmas', 'X-mas', 'Noël'):
            self.assertTrue(is_holiday({'genre':[label]}), label)

    def test_titles_and_substrings_are_not_classifications(self):
        self.assertFalse(is_holiday({'title':'Holiday in Cambodia', 'genre':['Rock']}))
        self.assertFalse(is_holiday({'genre':['Postholiday Rock']}))

    def test_album_holiday_exclusion_survives_conflicting_track_genre(self):
        songs=[{'songid':1,'albumid':2,'genre':['Jazz, Blues, R&B & Soul']},
               {'songid':2,'albumid':3,'genre':['Rock']}]
        albums=[{'albumid':2,'genre':['Christmas']},{'albumid':3,'genre':['Rock']}]
        result=shuffle_candidates(songs,albums,expected_total=2)
        self.assertEqual(result['eligible_ids'],[2])
        self.assertEqual(result['excluded'],1)

    def test_direct_holiday_tag_on_mixed_ordinary_album_is_excluded(self):
        result=shuffle_candidates([{'songid':1,'albumid':2,'genre':['Christmas']}],
                                  [{'albumid':2,'genre':['Pop']}],expected_total=1)
        self.assertEqual(result['eligible_ids'],[])

    def test_unknown_genre_is_not_silently_lost(self):
        result=shuffle_candidates([{'songid':1,'genre':[]}],[],expected_total=1)
        self.assertEqual(result['eligible_ids'],[1])
        self.assertEqual(result['unclassified_eligible'],1)

    def test_incomplete_song_or_album_inventory_fails_closed(self):
        with self.assertRaises(ValueError):shuffle_candidates([],[],expected_total=17113)
        with self.assertRaises(ValueError):shuffle_candidates([{'songid':1,'albumid':2}],[],expected_total=1)

    def test_duplicate_or_missing_ids_are_not_silently_deduplicated(self):
        for songs in ([{'songid':1},{'songid':1}], [{'title':'No id'}], [{'songid':True}]):
            with self.assertRaises(ValueError):shuffle_candidates(songs,[],expected_total=len(songs))

    def test_full_library_over_500_and_source_state_untouched(self):
        songs=[{'songid':index+1,'genre':['Rock']} for index in range(17113)]
        original=copy.deepcopy(songs)
        result=shuffle_candidates(songs,[],expected_total=17113)
        randomized=shuffled_ids(result,random.Random(42))
        self.assertEqual(len(randomized),17113)
        self.assertEqual(set(randomized),set(range(1,17114)))
        self.assertNotEqual(randomized,result['eligible_ids'])
        self.assertEqual(songs,original)


if __name__=='__main__':unittest.main()
