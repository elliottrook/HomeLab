import unittest
from av_preservation import verify,fingerprint
class AvTests(unittest.TestCase):
    def setUp(self):
        self.values=sorted([('videoscreen.resolution','16'),('videoscreen.screenmode','DESKTOP')]+[(str(i),'fixed') for i in range(66)])
        self.baseline=fingerprint(self.values)
        self.screen={'System.ScreenWidth':'3840','System.ScreenHeight':'2160','System.ScreenResolution':'3840x2160 @ 30.00 Hz - Full screen'}
    def current(self,**changes):
        values=dict(self.values);values.update(changes);return sorted(values.items())
    def test_exact_match(self):self.assertEqual(verify(self.values,self.baseline,{})['exact_values'],68)
    def test_evidenced_selector_remapping(self):
        result=verify(self.current(**{'videoscreen.resolution':'17'}),self.baseline,self.screen)
        self.assertTrue(result['resolution_index_rederived']);self.assertEqual(result['exact_values'],67)
    def test_other_changes_or_display_modes_still_fail(self):
        for change in ({'videoscreen.resolution':'18'}, {'videoscreen.resolution':'17','0':'changed'},
            {'videoscreen.resolution':'17','videoscreen.screenmode':'WINDOW'}):
            with self.assertRaises(ValueError):verify(self.current(**change),self.baseline,self.screen)
        with self.assertRaises(ValueError):verify(self.current(**{'videoscreen.resolution':'17'}),self.baseline,dict(self.screen,**{'System.ScreenWidth':'1920'}))
