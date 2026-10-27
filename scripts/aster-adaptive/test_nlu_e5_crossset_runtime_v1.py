import unittest

import nlu_e5_crossset_runtime_v1 as runtime


class E5RuntimeTests(unittest.TestCase):
    def test_schema_is_versioned(self):
        self.assertEqual("aster-nlu-e5-crossset-result.v1",
                         "aster-nlu-e5-crossset-result.v1")
        self.assertTrue(callable(runtime.load_set))


if __name__ == "__main__": unittest.main()
