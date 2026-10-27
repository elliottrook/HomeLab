import unittest

import nlu_encoder_head_runtime_v1 as runtime


class DenseHeadRuntimeTests(unittest.TestCase):
    def test_runtime_schema_is_distinct_and_non_authoritative(self):
        self.assertEqual("aster-nlu-encoder-head-crossset-result.v1", runtime.SCHEMA)


if __name__ == "__main__":
    unittest.main()
