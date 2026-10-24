import unittest
from music_queue import QueueSnapshot
from music_scrub import ScrubPreview


class ScrubTests(unittest.TestCase):
    def test_preview_steps_clamp_and_do_not_mutate_queue(self):
        queue=QueueSnapshot((1,2,1),0);preview=ScrubPreview.start(queue,180000,25000)
        self.assertEqual(preview.adjust(1).target_ms,30000)
        self.assertEqual(preview.adjust(-1).target_ms,20000)
        low=ScrubPreview.start(queue,180000,1000).adjust(-1);self.assertEqual(low.target_ms,0)
        high=ScrubPreview.start(queue,180000,179500).adjust(1);self.assertEqual(high.target_ms,179000)
        self.assertLess(high.percentage,100);self.assertEqual(queue.song_ids,(1,2,1))
    def test_invalid_or_nonplaying_previews_are_refused(self):
        for snapshot,duration,elapsed in ((QueueSnapshot((1,),None),10000,1000),
                                          (QueueSnapshot((1,),0),0,0),(QueueSnapshot((1,),0),10000,10000),
                                          (QueueSnapshot((1,),0),True,0)):
            with self.assertRaises(ValueError):ScrubPreview.start(snapshot,duration,elapsed)
    def test_duplicate_occurrences_have_different_preview_identity(self):
        one=ScrubPreview.start(QueueSnapshot((1,2,1),0),180000,25000)
        two=ScrubPreview.start(QueueSnapshot((1,2,1),2),180000,25000)
        self.assertNotEqual(one.queue_fingerprint,two.queue_fingerprint)
        for direction in (True,0,2):
            with self.assertRaises(ValueError):one.adjust(direction)
