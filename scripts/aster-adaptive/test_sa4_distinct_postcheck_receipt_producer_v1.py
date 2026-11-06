import unittest
from unittest import mock

import sa4_distinct_postcheck_receipt_producer_v1 as source
import sa4_independent_receipt_producer_v1 as previous
import sa4_target_registry_v1 as registry_v1
import sa4_target_registry_v3 as registry_v3


class Tests(unittest.TestCase):
    def test_complete_observer_binding_is_temporary(self):
        source.LOCAL_HOST_ID = "lxc104"
        observed = {}

        def inspect(*args, **kwargs):
            observed.update(registry=previous.registry,
                            bytes=previous.bytes_check,
                            metadata=previous.metadata_check,
                            consumer=previous.consumer_check,
                            host=previous.LOCAL_HOST_ID)
            return b"receipt\n"

        with mock.patch.object(previous, "observe", side_effect=inspect):
            self.assertEqual(b"receipt\n", source.observe(b"plan"))
        self.assertIs(registry_v3, observed["registry"])
        self.assertEqual("lxc104", observed["host"])
        self.assertIs(registry_v1, previous.registry)
        self.assertEqual("unconfigured", previous.LOCAL_HOST_ID)
        source.LOCAL_HOST_ID = "unconfigured"


if __name__ == "__main__":
    unittest.main()
