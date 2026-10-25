import hashlib,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from build_series_integration import dispatcher as series_dispatcher
from search_integration import BEFORE,dispatcher,window_dispatcher,home_entry

class SearchIntegrationTests(unittest.TestCase):
    def source(self):
        return series_dispatcher((Path(__file__).parent.parent/'skin.asterhome/tools/select_dispatch.py').read_text()).encode()
    def test_predecessor_and_no_arbitrary_source(self):
        self.assertEqual(hashlib.sha256(self.source()).hexdigest(),BEFORE)
        with self.assertRaises(ValueError):dispatcher(b'other')
    def test_exact_dialog_control_readiness(self):
        for dialog,focus,ready,handled in ((11127,30,'true',True),(11127,10,'true',False),
                                         (11127,30,'',False),(11128,30,'true',False),(0,30,'true',False)):
            calls=[];home=SimpleNamespace(getProperty=lambda key:ready)
            window=SimpleNamespace(getFocusId=lambda:focus)
            gui=SimpleNamespace(getCurrentWindowDialogId=lambda:dialog,getCurrentWindowId=lambda:10000,
                                Window=lambda identity:home if identity==10000 else window)
            # Home focus is required by the original untouched fallback.
            home.getFocusId=lambda:100
            core=SimpleNamespace(executebuiltin=calls.append)
            namespace={'__name__':'test_dispatch'}
            exec(compile(dispatcher(self.source()),'select.py','exec'),namespace)
            with patch.dict('sys.modules',xbmc=core,xbmcgui=gui):namespace['main']()
            self.assertEqual(calls,['SetProperty(AsterSearch.Command,details,home)'] if handled else ['Action(Select)'])
    def test_existing_music_and_books_routes_preserved(self):
        a={};b={};exec(self.source(),a);exec(dispatcher(self.source()),b)
        for window in (10025,10502,11110,11113,11114,11115,11116,11117,11121,11111):
            for focus in (50,500,501,502,503):
                self.assertEqual(a['dispatched_action'](window,focus),b['dispatched_action'](window,focus))

    def test_native_window_hook_leaves_modals_and_other_pages_alone(self):
        for current,dialog,handled in ((11127,9999,True),(11127,0,True),(11127,11128,False),(11127,10103,False),(10000,9999,False)):
            calls=[];home=SimpleNamespace(getProperty=lambda key:'true',getFocusId=lambda:30)
            gui=SimpleNamespace(getCurrentWindowId=lambda:current,getCurrentWindowDialogId=lambda:dialog,Window=lambda _:home)
            core=SimpleNamespace(executebuiltin=calls.append)
            namespace={'__name__':'test'};exec(window_dispatcher(dispatcher(self.source())),namespace)
            with patch.dict('sys.modules',xbmc=core,xbmcgui=gui):namespace['main']()
            self.assertEqual(calls,['SetProperty(AsterSearch.Command,details,home)'] if handled else ['Action(Select)'])

if __name__=='__main__':unittest.main()
