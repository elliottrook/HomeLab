from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_runtime_control_owner_v1 as controls
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4RuntimeControlOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(base, host_id="runtime-control-test-host")
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {
            "host_id": self.target.host_id, "path": self.target.path,
            "type": "regular-file", "follow_symlinks": False,
            "owner": "root", "group": "root", "mode": "0644"}
        self.plan_raw = contract.canonical(value)
        self.patchers = (
            patch.object(registry, "PRODUCTION_TARGETS", (self.target,)),
            patch.multiple(controls,
                           LOCAL_HOST_ID=self.target.host_id,
                           EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid(),
                           LOCK_PATH=str(self.root / "operation.lock"),
                           STOP_PATH=str(self.root / "emergency-stop")))
        for item in self.patchers: item.start()

    def tearDown(self):
        for item in reversed(self.patchers): item.stop()
        self.temporary.cleanup()

    def test_acquire_observe_and_terminal_release(self):
        owner = controls.RuntimeControlOwner(self.plan_raw); owner.acquire()
        observed = contract.decode_unique_json(owner.observe(100))
        self.assertEqual("held", observed["shared_operation_lock"])
        self.assertEqual("armed", observed["emergency_stop"])
        owner.release_terminal()
        self.assertFalse((self.root / "operation.lock").exists())
        self.assertFalse((self.root / "emergency-stop").exists())

    def test_existing_lock_fails_without_reuse(self):
        first = controls.RuntimeControlOwner(self.plan_raw); first.acquire()
        second = controls.RuntimeControlOwner(self.plan_raw)
        with self.assertRaises(FileExistsError): second.acquire()
        self.assertFalse(hasattr(second, "retry"))
        first.release_terminal()

    def test_operator_stop_mutation_fails_and_is_retained(self):
        owner = controls.RuntimeControlOwner(self.plan_raw); owner.acquire()
        descriptor = os.open(controls.STOP_PATH, os.O_WRONLY | os.O_TRUNC)
        try: os.write(descriptor, b"stop\n")
        finally: os.close(descriptor)
        with self.assertRaises(ValueError): owner.ensure_armed()
        owner.retain_uncertain()
        self.assertTrue((self.root / "operation.lock").exists())
        self.assertTrue((self.root / "emergency-stop").exists())


if __name__ == "__main__":
    unittest.main()
