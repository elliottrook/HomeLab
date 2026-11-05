import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("installer", ROOT / "install_jen_movie.py")
INSTALLER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(INSTALLER)


class JenMovieCandidateTests(unittest.TestCase):
    def test_xml_adds_trailer_and_person_action_without_autoplay(self):
        source = (
            '<onleft>200</onleft><onright>202</onright><onup>400</onup><ondown>500</ondown>'
            '    <control type="image"><left>1705</left><top>35</top>'
            '<onleft>201</onleft><onright>200</onright><onup>400</onup><ondown>200</ondown>'
            '<control type="list" id="500"><left>145</left>'
            '<onleft>500</onleft><onright>500</onright><visible>String.IsEqual(Window.Property(Movie.CastVisible),true)</visible>'
        )
        result = INSTALLER.patch_xml(source)
        self.assertIn('id="203"', result)
        self.assertIn('AsterMovie.Command,trailer', result)
        self.assertIn('AsterMovie.Command,person', result)
        self.assertNotIn('PlayMedia(', result)

    def test_runtime_requires_validated_trailer_and_existing_actor_route(self):
        source = "\n".join(
            [
                "import fcntl,json,os,sys,time",
                "from pathlib import Path",
                "sys.path.insert(0,str(ROOT/'resources/lib'))",
                "from movie_player import MovieSession,MovieUnavailable,READS,read_movie,idle,verify_stage",
                "require(method in READS|{'Player.Open','Player.Stop','Playlist.Clear'},'movie-rpc-boundary')",
                "def enrichment(movie):",
                "Playable='true' if value.available else 'false').items():window.setProperty('Movie.'+key,text)",
                "item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_items.append(item)",
                "fullscreen=False;return_until=0",
                "            if command in ('play','resume') and current==11130 and session.phase=='idle':",
                "            if session.phase=='playing' and not fullscreen and current==11130:",
                "                fullscreen=True;xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')",
                "if session.phase=='idle' and current!=11130 and time.monotonic()>=return_until:",
            ]
        )
        result = INSTALLER.patch_movie(source)
        self.assertIn("validated_kodi_youtube_plugin_url", result)
        self.assertIn("if not addon.get('enabled'):return None", result)
        self.assertIn("'Addons.GetAddonDetails'", result)
        self.assertIn("quote(person,safe='')", result)
        self.assertIn("require(idle(rpc),'idle-trailer-required')", result)
        self.assertIn("rpc('Player.Open',{'item':{'file':route}})", result)
        self.assertNotIn("search/?q=", result)

    def test_dispatch_routes_script_populated_movie_rails(self):
        source = """DYNAMIC_CONTROLS = {
    11129: frozenset((30,)),
}
    if window_id == 11121 and focus_id == 50:
        return 'RunScript(special://skin/tools/music_data.py,music-player,track)'
    return None
"""
        result = INSTALLER.patch_dispatch(source)
        self.assertIn("11130: frozenset((500, 501))", result)
        self.assertIn("AsterMovie.Command,person", result)
        self.assertIn("AsterMovie.Command,related", result)

    def test_family_authority_advances_with_dispatcher(self):
        source = (ROOT / "install_jen_movie.py").read_text()
        self.assertIn(
            'family["skin"]["tools/select_dispatch.py"] = digest(dispatch)',
            source,
        )


if __name__ == "__main__":
    unittest.main()
