from dataclasses import replace
import inspect
import unittest

import sa4_target_registry_v1 as registry


class SA4TargetRegistryTests(unittest.TestCase):
    def test_production_registry_is_empty_and_fails_closed(self):
        self.assertEqual((), registry.PRODUCTION_TARGETS)
        with self.assertRaises(ValueError):
            registry.resolve_production("sa4-synthetic-fixture")

    def test_fixture_is_separate_immutable_and_digest_bound(self):
        item = registry.resolve_schema_fixture("sa4-synthetic-fixture")
        self.assertEqual("/synthetic/aster/example.conf", item.path)
        self.assertRegex(registry.registration_sha256(item), r"^[0-9a-f]{64}$")
        with self.assertRaises(Exception):
            item.path = "/etc/shadow"
        with self.assertRaises(ValueError):
            registry.resolve_schema_fixture("missing")

    def test_resolvers_accept_no_registry_or_path_override(self):
        self.assertEqual(["target_id"], list(inspect.signature(
            registry.resolve_production).parameters))
        self.assertEqual(["target_id"], list(inspect.signature(
            registry.resolve_schema_fixture).parameters))

    def test_duplicate_identity_and_location_fail_closed(self):
        item = registry.SCHEMA_FIXTURES[0]
        with self.assertRaises(ValueError):
            registry.validate_registry((item, item), synthetic=True)
        second = replace(item, target_id="sa4-other-fixture")
        with self.assertRaises(ValueError):
            registry.validate_registry((item, second), synthetic=True)

    def test_unsafe_registration_fields_fail_closed(self):
        item = registry.SCHEMA_FIXTURES[0]
        variants = (
            replace(item, path="/etc/shadow"),
            replace(item, owner="aster"),
            replace(item, follow_symlinks=True),
            replace(item, one_link=False),
            replace(item, service_restart_required=True),
            replace(item, postcheck_program_sha256=("1" * 64,)),
            replace(item, owner_review_sha256="0"),
        )
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                registry.validate_registry((value,), synthetic=False)


if __name__ == "__main__":
    unittest.main()
