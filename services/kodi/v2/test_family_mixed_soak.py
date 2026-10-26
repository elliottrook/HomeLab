import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).parent/'tools/live_family_mixed_soak.py'


class FamilyMixedSoakTests(unittest.TestCase):
    def test_private_fixture_harness_has_no_library_or_history_write(self):
        raw = SOURCE.read_text(); ast.parse(raw)
        self.assertIn('/storage/.aster-private/m7-fixtures/aster-m7-test.mov', raw)
        self.assertIn('/storage/.aster-staging/aster-readalong3/sample.wav', raw)
        self.assertIn("'18d5578584490a6a7c2db8899040ae1af236aa4044c1e28c66243b231391568f'", raw)
        self.assertIn("'99ae9edd408aa2fc6258d300c9d655cd4d81b88114f90fd609089a2541a5e039'", raw)
        for forbidden in ('VideoLibrary.Set', 'AudioLibrary.Set', 'Files.Set',
                          'SetEpisodeDetails', 'SetMovieDetails'):
            self.assertNotIn(forbidden, raw)
        self.assertIn("rpc('Player.Stop'", raw)
        self.assertIn("ActivateWindow(Home)", raw)


if __name__ == '__main__': unittest.main()
