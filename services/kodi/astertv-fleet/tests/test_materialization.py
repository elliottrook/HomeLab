import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("family_restart_materializer", ROOT / "materialize_family_kodi_restart.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
GUARD_SPEC = importlib.util.spec_from_file_location("release_guard_materializer", ROOT / "materialize_release_guard.py")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_SPEC.loader.exec_module(GUARD_MODULE)
WIFI_SPEC = importlib.util.spec_from_file_location("bedroom_wifi_materializer", ROOT / "materialize_bedroom_wifi.py")
WIFI_MODULE = importlib.util.module_from_spec(WIFI_SPEC)
WIFI_SPEC.loader.exec_module(WIFI_MODULE)
REMOTE_SPEC = importlib.util.spec_from_file_location("remote_client_materializer", ROOT / "materialize_remote_client.py")
REMOTE_MODULE = importlib.util.module_from_spec(REMOTE_SPEC)
REMOTE_SPEC.loader.exec_module(REMOTE_MODULE)
TV_SPEC = importlib.util.spec_from_file_location("tv_details_materializer", ROOT / "materialize_tv_details.py")
TV_MODULE = importlib.util.module_from_spec(TV_SPEC)
TV_SPEC.loader.exec_module(TV_MODULE)
NEWS_SPEC = importlib.util.spec_from_file_location("news_playback_materializer", ROOT / "materialize_news_playback.py")
NEWS_MODULE = importlib.util.module_from_spec(NEWS_SPEC)
NEWS_SPEC.loader.exec_module(NEWS_MODULE)
MEDIA_SPEC = importlib.util.spec_from_file_location("family_media_materializer", ROOT / "materialize_family_media_lifecycle.py")
MEDIA_MODULE = importlib.util.module_from_spec(MEDIA_SPEC)
MEDIA_SPEC.loader.exec_module(MEDIA_MODULE)
EQUIPMENT_SPEC = importlib.util.spec_from_file_location("family_equipment_materializer", ROOT / "materialize_family_equipment_bridge.py")
EQUIPMENT_MODULE = importlib.util.module_from_spec(EQUIPMENT_SPEC)
EQUIPMENT_SPEC.loader.exec_module(EQUIPMENT_MODULE)
ACCOUNT_SPEC = importlib.util.spec_from_file_location("jen_account_materializer", ROOT / "materialize_jen_account_registry.py")
ACCOUNT_MODULE = importlib.util.module_from_spec(ACCOUNT_SPEC)
ACCOUNT_SPEC.loader.exec_module(ACCOUNT_MODULE)
CLIENT_SPEC = importlib.util.spec_from_file_location("jen_client_materializer", ROOT / "materialize_jen_aster_client.py")
CLIENT_MODULE = importlib.util.module_from_spec(CLIENT_SPEC)
CLIENT_SPEC.loader.exec_module(CLIENT_MODULE)
NEWS_ICON_SPEC = importlib.util.spec_from_file_location("jen_news_icon_materializer", ROOT / "materialize_jen_news_icons.py")
NEWS_ICON_MODULE = importlib.util.module_from_spec(NEWS_ICON_SPEC)
NEWS_ICON_SPEC.loader.exec_module(NEWS_ICON_MODULE)
PODCAST_SPEC = importlib.util.spec_from_file_location("jen_podcast_materializer", ROOT / "materialize_jen_podcast_requests.py")
PODCAST_MODULE = importlib.util.module_from_spec(PODCAST_SPEC)
PODCAST_SPEC.loader.exec_module(PODCAST_MODULE)
GUEST_SPEC = importlib.util.spec_from_file_location("jen_guest_materializer", ROOT / "materialize_jen_guest_catalogue.py")
GUEST_MODULE = importlib.util.module_from_spec(GUEST_SPEC)
GUEST_SPEC.loader.exec_module(GUEST_MODULE)
HOME_SPEC = importlib.util.spec_from_file_location("jen_home_materializer", ROOT / "materialize_jen_home_cameras.py")
HOME_MODULE = importlib.util.module_from_spec(HOME_SPEC)
HOME_SPEC.loader.exec_module(HOME_MODULE)
MOVIE_YT_SPEC = importlib.util.spec_from_file_location("jen_movie_youtube_materializer", ROOT / "materialize_jen_movie_youtube.py")
MOVIE_YT_MODULE = importlib.util.module_from_spec(MOVIE_YT_SPEC)
MOVIE_YT_SPEC.loader.exec_module(MOVIE_YT_MODULE)
LOW_SPEC = importlib.util.spec_from_file_location("jen_low_spec_materializer", ROOT / "materialize_jen_low_spec_runtime.py")
LOW_SPEC_MODULE = importlib.util.module_from_spec(LOW_SPEC)
LOW_SPEC.loader.exec_module(LOW_SPEC_MODULE)


class MaterializationTests(unittest.TestCase):
    def test_family_restart_outputs_are_deterministic_and_manifest_bound(self):
        artifact = ROOT.parent / "dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            outputs_one, manifest_one = MODULE.transform(artifact)
            outputs_two, manifest_two = MODULE.transform(artifact)
            MODULE.write_tree(Path(first), outputs_one, manifest_one)
            MODULE.write_tree(Path(second), outputs_two, manifest_two)
            tree_one = {p.relative_to(first).as_posix(): p.read_bytes() for p in Path(first).rglob("*") if p.is_file()}
            tree_two = {p.relative_to(second).as_posix(): p.read_bytes() for p in Path(second).rglob("*") if p.is_file()}
            self.assertEqual(tree_one, tree_two)
            manifest = json.loads(tree_one["materialization-manifest.json"])
            self.assertEqual(manifest["id"], "family-kodi-restart")
            self.assertEqual(len(manifest["outputs"]), 4)
            self.assertIn("Restart AsterTV", tree_one["skin.asterhome/1080i/Settings.xml"].decode())
            self.assertIn("RestartApp", tree_one["skin.asterhome/tools/restart_astertv.py"].decode())

    def test_release_guard_has_exact_host_bound_units_and_no_accepted_state(self):
        files, manifest = GUARD_MODULE.render()
        self.assertEqual(set(manifest["targets"]), {"astertv-family", "astertv-bedroom", "astertv-jen"})
        self.assertEqual(len(files), 7)
        for device_id, hostname in GUARD_MODULE.TARGETS.items():
            unit = files[f"targets/{device_id}/{GUARD_MODULE.UNIT_DESTINATION}"][0]
            self.assertIn(("--host " + hostname).encode(), unit)
            self.assertNotIn(b"--host %H", unit)
        self.assertFalse(manifest["generated_state"][0]["bundled"])
        self.assertFalse(any("accepted" in name for name in files))

    def test_bedroom_wifi_payload_is_host_bound_and_asserted(self):
        unit, manifest = WIFI_MODULE.render()
        self.assertIn(b"ConditionHost=AsterTV-Bedroom", unit)
        self.assertIn(b"power_save off", unit)
        self.assertEqual(manifest["files"][0]["destination"], "/" + WIFI_MODULE.DESTINATION)
        self.assertEqual(manifest["assertions"][0]["expected"], "disabled")

    def test_remote_client_materializes_current_accepted_lineage_for_each_target(self):
        files, manifest = REMOTE_MODULE.render()
        self.assertEqual(manifest["lineage"]["current_sha256"],
                         "0eba8fc5deaa22805a11c88b1fb402de552dcb876095cafd1610f9a4a5ab75ec")
        self.assertEqual(set(manifest["targets"]), {"astertv-family", "astertv-bedroom", "astertv-jen"})
        destinations = {(row["scope"], row["destination"]) for row in manifest["files"]}
        self.assertIn(("astertv-jen", "/storage/.config/system.d/astertv-v3-m8-jen.service"), destinations)
        self.assertIn(("astertv-family", "/storage/.config/system.d/astertv-v3-m8-remote.service"), destinations)
        self.assertTrue(all(not row["path"].startswith("common/") for row in manifest["mutable_state"]))

    def test_tv_details_materializes_one_reconciled_hash_bound_tree(self):
        files, manifest = TV_MODULE.render()
        self.assertEqual(len(files), 12)
        self.assertEqual(manifest["id"], "tv-details-v3")
        self.assertEqual(len(manifest["provenance"]["renderers"]), 7)
        self.assertEqual(
            files["script.asterruntime/aster-series-preview24/manifest.json"],
            (TV_MODULE.RECOVERED / "manifest.json").read_bytes(),
        )
        self.assertNotIn("script.asterruntime/family-manifest.json", files)
        self.assertEqual(
            {row["sha256"] for row in manifest["files"]},
            {TV_MODULE.EXPECTED[path] for path in files},
        )

    def test_news_playback_replays_each_hosts_exact_predecessor(self):
        files, manifest = NEWS_MODULE.render()
        self.assertEqual(len(files), 6)
        self.assertEqual(manifest["targets"], ["astertv-family", "astertv-jen"])
        self.assertEqual({row["scope"] for row in manifest["files"]},
                         {"astertv-family", "astertv-jen"})
        for device_id, expected in NEWS_MODULE.EXPECTED_FINAL.items():
            rows = {row["destination"].removeprefix("/storage/.kodi/addons/"): row["sha256"]
                    for row in manifest["files"] if row["scope"] == device_id}
            self.assertEqual(rows, expected)
        self.assertFalse(any(path.endswith("family-manifest.json") for path in files))

    def test_family_media_lifecycle_replays_checkpoint_and_excludes_shared_state(self):
        files, manifest = MEDIA_MODULE.render()
        self.assertEqual({path: MEDIA_MODULE.sha(data) for path, data in files.items()},
                         MEDIA_MODULE.EXPECTED_FINAL)
        self.assertEqual(len(files), 4)
        self.assertFalse(any(path.endswith("family-manifest.json") for path in files))
        self.assertEqual(manifest["checkpoint"],
                         "astertv-media-lifecycle-AsterTV-Family-20261105-031033")

    def test_family_equipment_payload_is_external_and_secrets_are_excluded(self):
        files, manifest = EQUIPMENT_MODULE.render()
        self.assertGreaterEqual(len(files), 10)
        self.assertTrue(all(row["scope"] == "external" for row in manifest["files"]))
        self.assertEqual(
            next(row for row in manifest["files"]
                 if row["destination"] == "/opt/aster-agent/aster_remote.py")["sha256"],
            EQUIPMENT_MODULE.PINNED["/opt/aster-agent/aster_remote.py"],
        )
        self.assertTrue(all(not row.get("bundled", True) for row in manifest["mutable_state"]))

    def test_jen_account_payload_excludes_mutable_profile_authority(self):
        files, manifest = ACCOUNT_MODULE.render()
        self.assertEqual(len(files), 9)
        self.assertIn("addons/script.asterprofiles.v3lab/registry.py", files)
        self.assertFalse(any(path.endswith("profiles.json") or path.endswith("authority.json")
                             for path in files))
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))

    def test_jen_aster_client_owns_only_addon_and_excludes_identity_and_key_state(self):
        files, manifest = CLIENT_MODULE.render()
        self.assertEqual(len(files), 8)
        self.assertIn("addon.xml", files)
        self.assertIn("resources/skins/default/1080i/search.xml", files)
        self.assertEqual(manifest["dependencies"], ["jen-account-registry"])
        self.assertFalse(any("asterprofiles" in path for path in files))
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))

    def test_jen_news_icons_replay_exact_accepted_base(self):
        files, manifest = NEWS_ICON_MODULE.render()
        self.assertEqual(len(files), 4)
        self.assertEqual(manifest["provenance"]["base_sha256"], NEWS_ICON_MODULE.BASE_SHA256)
        final = files["skin.asterhome/1080i/custom_1111_digest.xml"][0]
        self.assertEqual(NEWS_ICON_MODULE.sha(final), NEWS_ICON_MODULE.FINAL_SHA256)
        self.assertIn("system.d/astertv-v3-m5n-jen.service", files)

    def test_jen_podcast_request_payload_excludes_private_client_state(self):
        files, manifest = PODCAST_MODULE.render()
        self.assertEqual(len(files), 14)
        self.assertEqual(PODCAST_MODULE.sha(
            files["skin.asterhome/1080i/IncludesBooks.xml"][0]), PODCAST_MODULE.FINAL_INCLUDES)
        self.assertEqual(PODCAST_MODULE.sha(
            files["skin.asterhome/1080i/custom_1120_podcasts.xml"][0]), PODCAST_MODULE.FINAL_PODCASTS)
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))
        self.assertFalse(any("client.json" in path for path in files))

    def test_jen_guest_catalogue_owns_adapter_not_account_or_credentials(self):
        files, manifest = GUEST_MODULE.render()
        self.assertEqual(len(files), 5)
        self.assertEqual(manifest["dependencies"], ["jen-account-registry"])
        self.assertFalse(any("asterprofiles" in path or "jellyfin-guest.json" in path
                             for path in files))
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))
        self.assertEqual(manifest["external_state"][0]["sha256"], GUEST_MODULE.POLICY_SHA256)

    def test_jen_home_cameras_owns_presentation_not_identity_or_voice(self):
        files, manifest = HOME_MODULE.render()
        self.assertEqual(len(files), 11)
        self.assertEqual(HOME_MODULE.sha(
            files["skin.asterhome/1080i/custom_1112_home.xml"][0]), HOME_MODULE.FINAL_HOME_SHA256)
        self.assertFalse(any("asterprofiles" in path or "astertv.voice" in path for path in files))
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))
        runtime = files["stable/apply_jen_home_cameras.py"][0].decode()
        self.assertNotIn("PROFILE_STATE", runtime)
        self.assertIn('disable", "--now", "aster-camera.service', runtime)

    def test_jen_movie_youtube_excludes_session_and_account_state(self):
        files, manifest = MOVIE_YT_MODULE.render()
        self.assertEqual(len(files), 22)
        self.assertEqual(MOVIE_YT_MODULE.sha(
            files["live/skin.asterhome/1080i/custom_1130_movie.xml"][0]),
            MOVIE_YT_MODULE.EXPECTED["movie/custom_1130_movie.xml"])
        self.assertFalse(any("plugin.video.youtube" in path or "asterprofiles" in path
                             for path in files))
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))
        runtime = files["stable/apply.py"][0].decode()
        self.assertNotIn("ACCOUNT", runtime)
        self.assertNotIn("profiles.json", runtime)

    def test_jen_low_spec_owns_only_unclaimed_host_gates_and_policy_code(self):
        files, manifest = LOW_SPEC_MODULE.render()
        self.assertEqual(len(files), 24)
        destinations = {row["destination"] for row in manifest["files"]}
        self.assertFalse(any(path in destinations for path in (
            "/storage/.kodi/addons/script.asterruntime/aster-global-search-ui22/movie.py",
            "/storage/.kodi/addons/script.asterruntime/aster-series-preview24/default.py",
            "/storage/.kodi/addons/skin.asterhome/tools/aster_v2_digest.py",
            "/storage/.kodi/addons/skin.asterhome/tools/aster_v2_series.py",
        )))
        self.assertEqual(len(manifest["provenance"]["excluded_outputs"]), 4)
        self.assertTrue(all(not row["bundled"] for row in manifest["mutable_state"]))
        self.assertEqual(manifest["external_state"][0]["expected_sha256"],
                         "e4715278558f7956030b92b34677dab71776cf7820f1787b1f68e8ff11d6d89b")


if __name__ == "__main__":
    unittest.main()
