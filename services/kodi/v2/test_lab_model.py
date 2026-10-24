import unittest
from lab_model import LabModel
from test_music_catalogue import FakeLibrary
from music_catalogue import read_catalogue


class LabTests(unittest.TestCase):
    def setUp(self): self.model=LabModel(read_catalogue(FakeLibrary()))

    def test_genre_opens_album_view_and_back_restores_same_tile(self):
        self.model.enter(2)
        self.assertEqual((self.model.category,self.model.kind),('Rock & Alternative','album'))
        self.model.genres()
        self.assertEqual(self.model.index,2)

    def test_genre_search_empty_is_truthful(self):
        self.model.search('no such category')
        self.assertEqual(self.model.page()['total'],0)
        self.assertEqual(self.model.move_grid('down'),'search')

    def test_detail_search_and_tab_context_survive_return(self):
        self.model.enter(2);self.model.set_kind('song');self.model.search('Cambodia')
        self.assertEqual(self.model.page()['total'],1)
        self.model.set_kind('artist');self.model.set_kind('song')
        self.assertEqual(self.model.query,'Cambodia')
        self.model.genres();self.model.enter(2);self.model.set_kind('song')
        self.assertEqual(self.model.query,'Cambodia')

    def test_column_survives_short_last_row(self):
        self.model.index=self.model.column=3
        self.model.move_grid('down');self.assertEqual(self.model.index,6)
        self.model.move_grid('up');self.assertEqual(self.model.index,3)

    def test_left_edge_enters_rail_and_right_edge_search(self):
        self.assertEqual(self.model.move_grid('left'),'rail')
        self.model.index=3
        self.assertEqual(self.model.move_grid('right'),'search')

    def test_top_row_reaches_browse_without_losing_selection(self):
        self.model.index=2
        self.assertEqual(self.model.move_grid('up'),'browse')
        self.assertEqual(self.model.index,2)

    def test_detail_selection_returns_metadata_not_playback(self):
        self.model.enter(2);self.model.set_kind('song')
        row=self.model.enter(0)
        self.assertEqual(row['songid'],1)
        self.assertNotIn('file',row)

    def test_page_and_last_short_row_are_bounded(self):
        fake=FakeLibrary()
        fake.data['songs']=[{'songid':i+1,'label':str(i),'genre':['Rock'],'albumid':1,'artistid':[1]} for i in range(11)]
        model=LabModel(read_catalogue(fake));model.enter(2);model.set_kind('song')
        model.index=model.column=3
        model.turn_page(1);self.assertEqual(model.offset,4)
        self.assertEqual(model.index,3)
        model.turn_page(1);self.assertEqual(len(model.page()['rows']),3)
        model.turn_page(1);self.assertEqual(model.offset,8)
        model.turn_page(-1);self.assertEqual(model.offset,4)

    def test_header_kind_entry_remembers_genre_position(self):
        self.model.index=2;self.model.set_kind('artist');self.model.genres()
        self.assertEqual(self.model.index,2)

    def test_bad_kind_is_rejected(self):
        with self.assertRaises(ValueError):self.model.set_kind('play')
