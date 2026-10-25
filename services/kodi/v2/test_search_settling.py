"""Exercise the actual native-controller restoration body with delayed controls."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace
from global_search import Group,Hit,SearchUnavailable
from search_handoff import Cursor,restore_cursor

class SearchSettlingTests(unittest.TestCase):
    def run_restore(self,*,leaves=False,never=False):
        tree=ast.parse((Path(__file__).parent/'search_native/default.py').read_text())
        body=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='select_cursor')
        tick=[0];ready=[];positions={};selected=dict(group=0,result=0,focus=False);requests={}
        class Control:
            def __init__(self,key):self.key=key
            def selectItem(self,value):requests[self.key]=value
            def getSelectedPosition(self):return selected[self.key]
        class Monitor:
            def waitForAbort(self,_):
                tick[0]+=1
                if tick[0]>=1:selected['group']=requests.get('group',0);selected['focus']=True
                if tick[0]>=2 and not never:selected['result']=requests.get('result',0)
                return False
        def require(value,reason):
            if not value:raise SearchUnavailable(reason)
        groups=(Group('tvshow','TV','ready',(Hit('tvshow',1,'T',''),),1),
                Group('movie','Movies','ready',(Hit('movie',1,'One',''),Hit('movie',2,'Two','')),2))
        scope=dict(home=SimpleNamespace(clearProperty=lambda _:ready.append(('clear',tick[0])),
            setProperty=lambda key,value:ready.append((value,tick[0]))),PREFIX='AsterSearch.',
            restore_cursor=restore_cursor,groups=groups,categories=Control('group'),results=Control('result'),
            display=lambda _:None,positions=positions,source_visible=lambda:not leaves or tick[0]<1,
            require=require,monitor=Monitor(),time=SimpleNamespace(monotonic=lambda:tick[0]*.05),
            xbmc=SimpleNamespace(executebuiltin=lambda _:None,
                getInfoLabel=lambda _:str(groups[1].hits[selected['result']].identity),
                getCondVisibility=lambda _:selected['focus']))
        exec(compile(ast.Module(body=[body],type_ignores=[]),'settle.py','exec'),scope)
        return scope,ready,positions,tick
    def test_delayed_category_and_row_never_publish_early_ready(self):
        scope,ready,positions,tick=self.run_restore()
        self.assertTrue(scope['select_cursor'](Cursor('a','movie',2)))
        self.assertEqual(positions,{1:1});self.assertEqual(ready[0],('clear',0))
        self.assertEqual(ready[-1][0],'true');self.assertGreaterEqual(ready[-1][1],4)
    def test_home_during_settling_is_not_a_failed_playback_or_forced_return(self):
        scope,ready,_,_=self.run_restore(leaves=True)
        self.assertFalse(scope['select_cursor'](Cursor('a','movie',2)))
        self.assertFalse(any(value=='true' for value,_ in ready))
    def test_stuck_control_never_marks_wrong_result_ready(self):
        scope,ready,_,_=self.run_restore(never=True)
        with self.assertRaisesRegex(SearchUnavailable,'search-return-selection-not-ready'):
            scope['select_cursor'](Cursor('a','movie',2))
        self.assertFalse(any(value=='true' for value,_ in ready))

if __name__=='__main__':unittest.main()
