import importlib.util
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


PLANS = module("astertv_release_plans", ROOT / "build_release_plans.py")
GUARD = module("astertv_composition_guard", ROOT / "composition_guard.py")
TRANSACTION = module("astertv_transaction", ROOT / "transaction.py")
COLLECTOR = module("astertv_observation_collector", ROOT / "collect_composition_observation.py")
DOCTOR = module("astertv_fleet_doctor", ROOT / "doctor_fleet.py")
APPLY = module("astertv_bundle_apply", ROOT / "apply_composition_bundle.py")


class ReleasePipelineTests(unittest.TestCase):
    def build(self, destination):
        return PLANS.build(ROOT, Path(destination))

    def test_plans_are_deterministic_and_plan_only(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = self.build(first)
            two = self.build(second)
            self.assertEqual(one, two)
            first_files = {p.relative_to(first).as_posix(): p.read_bytes() for p in Path(first).rglob("*") if p.is_file()}
            second_files = {p.relative_to(second).as_posix(): p.read_bytes() for p in Path(second).rglob("*") if p.is_file()}
            self.assertEqual(first_files, second_files)
            self.assertEqual(one["deployable_devices"], 0)
            self.assertEqual(one["verified_artifacts"], 0)

    def test_every_device_has_plan_sbom_and_guard(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            for device in ("astertv-family", "astertv-bedroom", "astertv-jen", "astertv-guest"):
                self.assertTrue((Path(destination) / "plans" / f"{device}.json").is_file())
                self.assertTrue((Path(destination) / "sbom" / f"{device}.cdx.json").is_file())
                self.assertTrue((Path(destination) / "guards" / f"{device}.json").is_file())

    def test_guard_contracts_hash_installed_destinations_not_repository_sources(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            family = json.loads((Path(destination) / "guards/astertv-family.json").read_text())
            bedroom = json.loads((Path(destination) / "guards/astertv-bedroom.json").read_text())
        family_rows = {row["path"]: row for row in family["expected_payloads"]}
        bedroom_rows = {row["path"]: row for row in bedroom["expected_payloads"]}
        self.assertIn("/storage/.config/system.d/astertv-release-guard.service", family_rows)
        self.assertIn("/storage/.config/system.d/astertv-wifi-stability.service", bedroom_rows)
        self.assertIn("/storage/.kodi/addons/skin.asterhome/tools/restart_astertv.py", family_rows)
        self.assertFalse(any(path.startswith("services/") for path in family_rows))
        guard_path = "/storage/.config/system.d/astertv-release-guard.service"
        self.assertNotEqual(family_rows[guard_path]["sha256"], bedroom_rows[guard_path]["sha256"])

    def test_guest_is_explicitly_non_deployable(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            plan = json.loads((Path(destination) / "plans/astertv-guest.json").read_text())
            self.assertIn("candidate-not-deployable", plan["promotion_blockers"])
            self.assertFalse(plan["deployable"])

    def test_device_specific_performance_ceiling_is_preserved(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            jen = json.loads((Path(destination) / "plans/astertv-jen.json").read_text())
            family = json.loads((Path(destination) / "plans/astertv-family.json").read_text())
            self.assertEqual(jen["performance_budget"]["output_ceiling"], "1080p-media-stereo-device-only")
            self.assertNotEqual(family["performance_budget"]["output_ceiling"], jen["performance_budget"]["output_ceiling"])
            assertions = {row["key"]: row["expected"] for overlay in jen["overlays"]
                          for row in overlay["assertions"]}
            self.assertNotIn("display.output", assertions)
            self.assertEqual(assertions["policy.hevc-direct-play-max-width"], 1920)
            self.assertEqual(assertions["policy.max-bitrate-kbps"], 18000)
            self.assertEqual(assertions["audio.channels"], "2.0")
            self.assertFalse(assertions["audio.passthrough"])
            self.assertEqual(assertions["accepted-file-count"], 532)

    def test_guard_classifies_clean_unknown_missing_and_dependency_drift(self):
        contract = {"schema_version": 1, "kind": "composition-guard-contract", "device_id": "box", "composition_sha256": "abc", "expected_resources": ["a", "b"], "registered_extras": ["c"]}
        clean = {"schema_version": 1, "kind": "composition-observation", "device_id": "box", "composition_sha256": "abc", "resources": ["a", "b"], "dependencies": {"jellyfin": "available"}}
        self.assertEqual(GUARD.inspect(contract, clean)["outcome"], "clean")
        extra = dict(clean, resources=["a", "b", "c"])
        self.assertEqual(GUARD.inspect(contract, extra)["outcome"], "registered-extra")
        drift = dict(clean, resources=["a", "unknown"], dependencies={"jellyfin": "unavailable"})
        result = GUARD.inspect(contract, drift)
        self.assertEqual(result["outcome"], "drift")
        self.assertEqual(result["missing"], ["b"])
        self.assertEqual(result["unknown"], ["unknown"])
        self.assertEqual(result["unavailable_dependencies"], ["jellyfin"])

    def test_guard_fails_closed_on_identity_or_composition_mismatch(self):
        contract = {"schema_version": 1, "kind": "composition-guard-contract", "device_id": "box", "composition_sha256": "abc", "expected_resources": [], "registered_extras": []}
        wrong = {"schema_version": 1, "kind": "composition-observation", "device_id": "other", "composition_sha256": "abc", "resources": []}
        with self.assertRaisesRegex(ValueError, "device-identity-mismatch"):
            GUARD.inspect(contract, wrong)
        mismatch = dict(wrong, device_id="box", composition_sha256="def")
        self.assertTrue(GUARD.inspect(contract, mismatch)["composition_mismatch"])

    def test_doctor_fails_closed_on_missing_stale_and_drifted_observations(self):
        from datetime import datetime, timezone, timedelta
        with tempfile.TemporaryDirectory() as temporary:
            observed = Path(temporary)
            now = datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc)
            missing = DOCTOR.report(ROOT, observed, now, timedelta(hours=24))
            self.assertEqual(missing["outcome"], "attention")
            self.assertEqual(missing["counts"]["unobserved"], 3)
            guard = json.loads((ROOT / "generated-release-plans/guards/astertv-jen.json").read_text())
            observation = {
                "schema_version": 1, "kind": "composition-observation",
                "device_id": "astertv-jen", "composition_sha256": "0" * 64,
                "observed_at": (now - timedelta(hours=25)).isoformat(),
                "resources": guard["expected_resources"], "payloads": [],
                "dependencies": {}, "assertions": {},
            }
            (observed / "astertv-jen.json").write_text(json.dumps(observation))
            stale = DOCTOR.report(ROOT, observed, now, timedelta(hours=24))
            self.assertEqual(stale["counts"]["stale"], 1)
            observation["observed_at"] = now.isoformat()
            (observed / "astertv-jen.json").write_text(json.dumps(observation))
            drift = DOCTOR.report(ROOT, observed, now, timedelta(hours=24))
            self.assertEqual(drift["counts"]["drift"], 1)

    def test_real_artifact_builds_hash_bound_bundles_and_only_complete_device_promotes(self):
        artifact_root = ROOT.parent / "dist"
        with tempfile.TemporaryDirectory() as destination:
            result = PLANS.build(ROOT, Path(destination), artifact_root)
            self.assertEqual(result["verified_artifacts"], 4)
            self.assertEqual(result["built_bundles"], 4)
            self.assertEqual(result["deployable_devices"], 3)
            family = json.loads((Path(destination) / "plans/astertv-family.json").read_text())
            bedroom = json.loads((Path(destination) / "plans/astertv-bedroom.json").read_text())
            jen = json.loads((Path(destination) / "plans/astertv-jen.json").read_text())
            self.assertTrue(family["artifact"]["verified"])
            self.assertNotIn("release-artifact-not-locally-verified", family["promotion_blockers"])
            self.assertNotIn("composition-bundle-not-built", family["promotion_blockers"])
            self.assertFalse(any(item.startswith("overlay-payload-incomplete:") for item in family["promotion_blockers"]))
            bundle = Path(destination) / "bundles" / family["bundle"]["name"]
            self.assertEqual(PLANS.file_sha256(bundle), family["bundle"]["sha256"])
            with tarfile.open(bundle, "r:gz") as archive:
                manifest = json.load(archive.extractfile("manifest.json"))
            self.assertEqual(manifest["composition_sha256"], family["composition_sha256"])
            self.assertEqual(len(manifest["install_payloads"]),
                             len(manifest["guard"]["expected_payloads"]))
            with tarfile.open(bundle, "r:gz") as archive:
                names = set(archive.getnames())
                for payload in manifest["install_payloads"]:
                    self.assertIn(payload["archive_path"], names)
                    data = archive.extractfile(payload["archive_path"]).read()
                    self.assertEqual(PLANS.file_sha256_from_bytes(data), payload["sha256"])
            self.assertTrue(family["deployable"])
            self.assertEqual(family["promotion_blockers"], [])
            self.assertTrue(bedroom["deployable"])
            self.assertEqual(bedroom["promotion_blockers"], [])
            self.assertTrue(jen["deployable"])
            self.assertEqual(jen["promotion_blockers"], [])

    def test_verified_bundle_build_is_byte_deterministic(self):
        artifact_root = ROOT.parent / "dist"
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = PLANS.build(ROOT, Path(first), artifact_root)
            two = PLANS.build(ROOT, Path(second), artifact_root)
            self.assertEqual(one, two)
            one_bundles = {path.name: path.read_bytes() for path in (Path(first) / "bundles").glob("*.tar.gz")}
            two_bundles = {path.name: path.read_bytes() for path in (Path(second) / "bundles").glob("*.tar.gz")}
            self.assertEqual(one_bundles, two_bundles)

    def test_install_tree_rejects_destination_escape(self):
        desired = {"overlays": ["bad"], "payloads": {"bad": [{
            "path": "README.md", "sha256": PLANS.file_sha256(ROOT / "README.md"),
            "bytes": (ROOT / "README.md").stat().st_size,
        }]}}
        installed = {"bad": [{
            "destination": "/storage/../etc/escape",
            "sha256": desired["payloads"]["bad"][0]["sha256"],
            "bytes": desired["payloads"]["bad"][0]["bytes"], "mode": "0644",
        }]}
        with self.assertRaisesRegex(PLANS.FLEET.FleetError, "install-destination"):
            PLANS.resolve_install_members(ROOT, desired, installed)

    def test_bundle_runner_checkpoints_applies_and_rolls_back_offline(self):
        import gzip
        import hashlib
        import io
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            live = root / "storage/app/value"
            live.parent.mkdir(parents=True)
            live.write_bytes(b"old")
            payload = b"new"
            row = {"overlay": "test", "path": "/storage/app/value",
                   "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                   "mode": "0644", "archive_path": "install/storage/app/value"}
            guard = {"schema_version": 1, "kind": "composition-guard-contract",
                     "device_id": "astertv-test", "hostname": "AsterTV-Test",
                     "composition_sha256": "a" * 64,
                     "expected_payloads": [{key: row[key] for key in
                                            ("overlay", "path", "sha256", "bytes", "mode")}]}
            manifest = {"schema_version": 1, "kind": "astertv-composition-bundle",
                        "device_id": "astertv-test", "composition_sha256": "a" * 64,
                        "install_payloads": [row]}
            bundle = base / "bundle.tar.gz"
            with bundle.open("wb") as output:
                with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as zipped:
                    with tarfile.open(fileobj=zipped, mode="w") as archive:
                        for name, data in (("manifest.json", PLANS.canonical(manifest)),
                                           ("guard-contract.json", PLANS.canonical(guard)),
                                           (row["archive_path"], payload)):
                            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
                            archive.addfile(info, io.BytesIO(data))
            loaded, _, payloads = APPLY.load_bundle(bundle, PLANS.file_sha256(bundle))
            self.assertEqual(APPLY.plan(root, loaded)["replace"], 1)
            checkpoint = APPLY.checkpoint(root, loaded, base / "checkpoints", "test-1")
            staged = APPLY.stage(root, loaded, payloads, base / "stages", "test-1")
            self.assertEqual(APPLY.install(root, loaded, staged), ["/storage/app/value"])
            self.assertEqual(live.read_bytes(), b"new")
            self.assertEqual(APPLY.restore(root, checkpoint)["outcome"], "rolled-back")
            self.assertEqual(live.read_bytes(), b"old")

    def test_bundle_runner_removes_and_restores_guard_boot_edge(self):
        from unittest.mock import patch
        with patch.object(APPLY, "run") as command:
            APPLY.suspend_guard()
            self.assertEqual(command.call_args_list, [
                unittest.mock.call(["systemctl", "stop", "kodi.service"]),
                unittest.mock.call(["systemctl", "disable", "astertv-release-guard.service"]),
                unittest.mock.call(["systemctl", "daemon-reload"]),
            ])
        with patch.object(APPLY, "run") as command:
            APPLY.resume_guard()
            self.assertEqual(command.call_args_list, [
                unittest.mock.call(["systemctl", "enable", "astertv-release-guard.service"]),
                unittest.mock.call(["systemctl", "daemon-reload"]),
                unittest.mock.call(["systemctl", "start", "kodi.service"]),
            ])

    def test_bundle_runner_reconciles_only_declared_systemd_assertions(self):
        guard = {"expected_assertions": [
            {"authority": "systemd", "key": "new.service", "expected": "enabled"},
            {"authority": "systemd", "key": "old.service", "expected": "disabled"},
            {"authority": "systemd", "key": "camera.service", "expected": "disabled-inactive"},
            {"authority": "systemd", "key": "policy.path", "expected": "enabled-active"},
            {"authority": "kodi", "key": "unrelated", "expected": True},
        ]}
        from unittest.mock import patch
        with patch.object(APPLY, "run") as command:
            APPLY.reconcile_systemd(guard)
            self.assertEqual(command.call_args_list, [
                unittest.mock.call(["systemctl", "enable", "new.service"]),
                unittest.mock.call(["systemctl", "disable", "old.service"]),
                unittest.mock.call(["systemctl", "disable", "--now", "camera.service"]),
                unittest.mock.call(["systemctl", "enable", "--now", "policy.path"]),
            ])

    def test_bundle_runner_rollback_allows_predecessor_unit_absence(self):
        from unittest.mock import patch
        rows = [
            {"unit": "new.service", "enabled": "not-found", "active": "inactive"},
            {"unit": "old.service", "enabled": "enabled", "active": "inactive"},
        ]
        with patch.object(APPLY, "run") as command:
            APPLY.restore_systemd(rows)
            self.assertEqual(command.call_args_list, [
                unittest.mock.call(["systemctl", "enable", "old.service"]),
                unittest.mock.call(["systemctl", "stop", "old.service"]),
            ])

    def test_guard_detects_payload_and_required_dependency_drift(self):
        contract = {
            "schema_version": 1, "kind": "composition-guard-contract",
            "device_id": "box", "composition_sha256": "abc",
            "expected_resources": [], "registered_extras": [],
            "required_dependencies": ["jellyfin"],
            "expected_payloads": [{"overlay": "ui", "path": "file.xml", "sha256": "a" * 64}],
        }
        clean = {
            "schema_version": 1, "kind": "composition-observation",
            "device_id": "box", "composition_sha256": "abc", "resources": [],
            "dependencies": {"jellyfin": "available"},
            "payloads": [{"overlay": "ui", "path": "file.xml", "sha256": "a" * 64}],
        }
        self.assertEqual(GUARD.inspect(contract, clean)["outcome"], "clean")
        drift = dict(clean, dependencies={"jellyfin": "unavailable"}, payloads=[{"overlay": "ui", "path": "file.xml", "sha256": "b" * 64}])
        result = GUARD.inspect(contract, drift)
        self.assertEqual(result["outcome"], "drift")
        self.assertEqual(result["payload_mismatches"], ["ui:file.xml"])
        self.assertEqual(result["unavailable_dependencies"], ["jellyfin"])

    def test_guard_detects_typed_assertion_drift(self):
        contract = {
            "schema_version": 1, "kind": "composition-guard-contract",
            "device_id": "box", "composition_sha256": "abc",
            "expected_resources": [], "registered_extras": [],
            "expected_assertions": [{"overlay": "audio", "authority": "kodi",
                                     "key": "audio.passthrough", "expected": True,
                                     "sensitive": False}],
        }
        observed = {"schema_version": 1, "kind": "composition-observation",
                    "device_id": "box", "composition_sha256": "abc",
                    "resources": [], "dependencies": {}, "payloads": [],
                    "assertions": {"kodi:audio.passthrough": False}}
        result = GUARD.inspect(contract, observed)
        self.assertEqual(result["outcome"], "drift")
        self.assertEqual(result["assertion_mismatches"], ["audio:kodi:audio.passthrough"])

    def test_collector_is_hostname_bound_and_missing_files_fail_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "storage/payload"
            target.parent.mkdir(parents=True)
            target.write_text("accepted")
            contract = {
                "schema_version": 1, "kind": "composition-guard-contract",
                "device_id": "box", "hostname": "AsterTV-Box",
                "composition_sha256": "abc", "expected_resources": [],
                "registered_extras": [], "required_dependencies": [],
                "expected_payloads": [
                    {"overlay": "guard", "path": "/storage/payload",
                     "sha256": PLANS.file_sha256(target), "bytes": 8, "mode": "0644"},
                    {"overlay": "guard", "path": "/storage/missing",
                     "sha256": "a" * 64, "bytes": 1, "mode": "0644"},
                ],
            }
            with self.assertRaisesRegex(ValueError, "device-hostname-mismatch"):
                COLLECTOR.collect(contract, "wrong", root)
            observed = COLLECTOR.collect(contract, "AsterTV-Box", root)
            result = GUARD.inspect(contract, observed)
            self.assertEqual(result["outcome"], "drift")
            self.assertEqual(result["missing_payloads"], ["guard:/storage/missing"])

    def test_wrong_artifact_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as artifacts, tempfile.TemporaryDirectory() as destination:
            release = json.loads((ROOT / "releases/astertv-v2.0.7-2026-10-31.yaml").read_text())
            (Path(artifacts) / release["artifact"]["name"]).write_bytes(b"not-the-release")
            with self.assertRaisesRegex(PLANS.FLEET.FleetError, "artifact-hash-mismatch"):
                PLANS.build(ROOT, Path(destination), Path(artifacts))

    def test_interrupted_promotion_restores_predecessor_and_clean_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            target = base / "live"
            source.mkdir()
            target.mkdir()
            (source / "version").write_text("new")
            (target / "version").write_text("old")
            expected = TRANSACTION.inventory(source)
            with self.assertRaisesRegex(RuntimeError, "synthetic-interruption"):
                TRANSACTION.promote(source, target, expected, "after-predecessor-move")
            self.assertEqual((target / "version").read_text(), "old")
            result = TRANSACTION.promote(source, target, expected)
            self.assertEqual(result["outcome"], "promoted")
            self.assertEqual((target / "version").read_text(), "new")
            self.assertEqual(TRANSACTION.rollback(target)["outcome"], "rolled-back")
            self.assertEqual((target / "version").read_text(), "old")


if __name__ == "__main__":
    unittest.main()
