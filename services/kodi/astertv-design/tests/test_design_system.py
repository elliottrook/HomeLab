import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astertv_design_build", HERE / "build_pattern_library.py")
BUILD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILD
SPEC.loader.exec_module(BUILD)


class DesignSystemTests(unittest.TestCase):
    def test_outputs_are_deterministic(self):
        first = BUILD.outputs()
        second = BUILD.outputs()
        self.assertEqual(first, second)

    def test_focus_graphs_are_closed(self):
        self.assertEqual(BUILD.validate_focus(BUILD.load("focus-graphs.json")), [])

    def test_icon_context_is_exclusive(self):
        contexts = BUILD.load("tokens.json")["icon_context"]
        self.assertEqual(contexts["stone"], ["floating-side-rail", "launcher"])
        self.assertFalse(set(contexts["stone"]) & set(contexts["plain"]))

    def test_component_catalogue_has_required_states(self):
        components = {item["id"]: item for item in BUILD.load("catalogue.json")["components"]}
        self.assertTrue({"rest", "focus", "pressed", "disabled"} <= set(components["button"]["states"]))
        self.assertTrue({"rest", "focus", "watched", "unwatched", "missing-art"} <= set(components["artwork-tile"]["states"]))

    def test_fixtures_are_privacy_safe(self):
        raw = (HERE / "catalogue.json").read_text().lower()
        for forbidden in ["password", "api_key", "token_value", "camera_url"]:
            self.assertNotIn(forbidden, raw)

    def test_runtime_assets_have_hashes(self):
        records = BUILD.runtime_assets()
        self.assertGreater(len(records), 10)
        for record in records:
            self.assertRegex(record["sha256"], r"^[0-9a-f]{64}$")

    def test_asset_ingestion_policy_is_fail_closed(self):
        catalogue = BUILD.load("catalogue.json")
        policy = BUILD.load("asset-policy.json")
        records = BUILD.runtime_assets()
        self.assertEqual(BUILD.validate_asset_policy(catalogue, policy, records), [])
        injected = records + [{
            "path": "services/kodi/astertv-v3/overlay/skin.asterhome.v3pilot/media/unregistered.png",
            "sha256": "0" * 64,
            "bytes": 1,
            "consumer": "test",
        }]
        self.assertIn(
            "asset-policy: unregistered raster added or frozen legacy raster changed",
            BUILD.validate_asset_policy(catalogue, policy, injected),
        )

    def test_semantic_assets_are_svg_first_and_exports_are_placement_bound(self):
        catalogue = BUILD.load("catalogue.json")
        for asset in catalogue["semantic_assets"]:
            master = asset.get("master") or asset.get("repository_path")
            self.assertEqual(Path(master).suffix.lower(), ".svg", asset["id"])
            for export in asset.get("runtime_exports", []):
                self.assertEqual(export["derived_from_svg_sha256"], asset["master_sha256"])
                self.assertTrue(export["placement"])
                self.assertEqual(len(export["dimensions"]), 2)
                self.assertTrue(export["export_recipe"])
                self.assertIs(export["runtime_resize_allowed"], False)

    def test_plain_compass_resolves_to_exact_approved_exports(self):
        catalogue = BUILD.load("catalogue.json")
        assets = {item["id"]: item for item in catalogue["semantic_assets"]}
        plain = assets["plain-compass"]
        self.assertEqual(plain["master"], "SVG/15-aster-compass.svg")
        self.assertRegex(plain["master_sha256"], r"^[0-9a-f]{64}$")
        self.assertGreaterEqual(len(plain["runtime_exports"]), 3)
        self.assertNotIn("floating-side-rail", plain["allowed_contexts"])
        self.assertIn("floating-side-rail", plain["forbidden_contexts"])
        for export in plain["runtime_exports"]:
            self.assertRegex(export["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(len(export["dimensions"]), 2)
            self.assertTrue(export["export_recipe"])

    def test_games_top_rail_uses_exact_approved_plain_compass_export(self):
        rendered = BUILD.games_page_render(
            next(page for page in BUILD.load("catalogue.json")["pages"] if page["id"] == "games"),
            BUILD.load("tokens.json"),
            "focus",
        )
        root = BUILD.ET.fromstring(rendered)
        images = [
            node for node in root.iter("{http://www.w3.org/2000/svg}image")
            if node.attrib.get("data-brand-asset") == "plain-compass-32"
        ]
        self.assertEqual(len(images), 4)
        for node in images:
            self.assertEqual((node.attrib["width"], node.attrib["height"]), ("32", "32"))
            href = node.attrib["{http://www.w3.org/1999/xlink}href"]
            payload = base64.b64decode(href.split(",", 1)[1])
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                "ebd08d8a6224120a0a8b873e1f469572578fe8167089d2baaa1d70f338642030",
            )

    def test_games_uses_official_side_rail_with_temporary_games_icon(self):
        tokens = BUILD.load("tokens.json")
        rendered = BUILD.games_page_render(
            next(page for page in BUILD.load("catalogue.json")["pages"] if page["id"] == "games"),
            tokens,
            "focus",
        )
        root = BUILD.ET.fromstring(rendered)
        images = [
            node for node in root.iter("{http://www.w3.org/2000/svg}image")
            if node.attrib.get("data-shell-destination")
        ]
        self.assertEqual(
            [node.attrib["data-shell-destination"] for node in images],
            ["media", "books", "news", "home", "music", "games", "requests", "settings"],
        )
        manifest = BUILD.load("official-side-rail-assets.json")
        sources = {item["id"]: item for item in manifest["items"] if "data_uri" in item}
        for node in images:
            item = next(item for item in manifest["items"] if item["id"] == node.attrib["data-shell-destination"])
            source = sources[item.get("asset_ref", item["id"])]
            self.assertEqual((node.attrib["width"], node.attrib["height"]), ("32", "32"))
            payload = base64.b64decode(node.attrib["{http://www.w3.org/1999/xlink}href"].split(",", 1)[1])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), source["export_sha256"])
        games = next(node for node in images if node.attrib["data-shell-destination"] == "games")
        requests = next(node for node in images if node.attrib["data-shell-destination"] == "requests")
        self.assertEqual(games.attrib["data-asset-sha256"], requests.attrib["data-asset-sha256"])
        self.assertEqual(rendered.count('data-shell-region="side-rail"'), 1)
        self.assertEqual(rendered.count('data-shell-current="games"'), 1)

    def test_games_expanded_side_rail_preserves_order_and_focuses_games(self):
        rendered = BUILD.games_page_render(
            next(page for page in BUILD.load("catalogue.json")["pages"] if page["id"] == "games"),
            BUILD.load("tokens.json"),
            "side-rail-focus",
        )
        root = BUILD.ET.fromstring(rendered)
        rail = next(
            node for node in root.iter("{http://www.w3.org/2000/svg}rect")
            if node.attrib.get("data-shell-region") == "side-rail"
        )
        self.assertEqual((rail.attrib["x"], rail.attrib["y"], rail.attrib["width"], rail.attrib["height"]),
                         ("22", "268", "250", "544"))
        self.assertEqual(rail.attrib["data-shell-state"], "expanded")
        self.assertEqual(rendered.count('data-shell-node='), 8)
        self.assertEqual(rendered.count('data-shell-focus="games"'), 1)
        self.assertNotIn('data-shell-current="games"', rendered)

    def test_games_side_rail_first_and_last_states_clamp_edges(self):
        page = next(page for page in BUILD.load("catalogue.json")["pages"] if page["id"] == "games")
        tokens = BUILD.load("tokens.json")
        first = BUILD.games_page_render(page, tokens, "side-rail-first")
        last = BUILD.games_page_render(page, tokens, "side-rail-last")
        self.assertEqual(first.count('data-shell-focus="media"'), 1)
        self.assertEqual(last.count('data-shell-focus="settings"'), 1)
        self.assertEqual(first.count('data-shell-current="games"'), 1)
        self.assertEqual(last.count('data-shell-current="games"'), 1)
        graph = next(graph for graph in BUILD.load("focus-graphs.json")["graphs"] if graph["page"] == "games")
        self.assertEqual(graph["nodes"]["side-media"]["up"], "side-media")
        self.assertEqual(graph["nodes"]["side-settings"]["down"], "side-settings")

    def test_button_focus_does_not_change_geometry(self):
        tokens = BUILD.load("tokens.json")
        self.assertEqual(tokens["geometry"]["pill_radius"], 28)
        # One geometry token governs every state; state-specific geometry is forbidden.
        self.assertNotIn("focus_geometry", tokens)

    def test_generated_outputs_match(self):
        for path, expected in BUILD.outputs().items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_text(), expected, path)

    def test_all_required_page_families_are_mapped(self):
        catalogue = BUILD.load("catalogue.json")
        mapped = {page["family"] for page in catalogue["pages"]}
        self.assertEqual(set(catalogue["required_page_families"]) - mapped, set())
        for page in catalogue["pages"]:
            source = page.get("template") or page.get("design_spec")
            self.assertTrue(source, page["id"])
            self.assertTrue((BUILD.ROOT / source).is_file(), source)

    def test_games_is_design_only_and_integration_gated(self):
        catalogue = BUILD.load("catalogue.json")
        games = next(page for page in catalogue["pages"] if page["id"] == "games")
        self.assertEqual(games["status"], "candidate")
        self.assertNotIn("template", games)
        self.assertTrue(games["design_spec"].startswith("services/kodi/astertv-design/"))
        spec = json.loads((BUILD.ROOT / games["design_spec"]).read_text())
        self.assertEqual(spec["status"], "candidate-owner-review")
        self.assertIn("Kodi XML or add-on source", spec["approval_boundary"]["held_until_v3_acceptance"])
        self.assertEqual(spec["jen_performance_ceiling"]["memory_budget_mib"], 1536)
        self.assertEqual(spec["jen_performance_ceiling"]["prefetch_rows"], 2)
        self.assertEqual(spec["jen_performance_ceiling"]["art_cache_mib"], 256)

    def test_games_has_complete_review_fixture_set(self):
        index = json.loads(BUILD.outputs()[BUILD.GENERATED / "fixture-index.json"])
        states = {
            item.get("state") for item in index["fixtures"]
            if item["source"] == "games"
        }
        self.assertTrue({
            "rest", "focus", "side-rail-focus", "side-rail-first", "side-rail-last",
            "empty-library", "service-offline", "missing-art",
            "long-title", "detail", "install", "request", "save-conflict",
        } <= states)

    def test_games_focus_contract_covers_page_details_and_dialogs(self):
        graphs = {item["page"]: item for item in BUILD.load("focus-graphs.json")["graphs"]}
        self.assertTrue({
            "games", "game-detail-installed", "game-detail-available",
            "game-detail-absent", "game-install-dialog", "game-request-dialog",
            "game-save-conflict-dialog", "games-offline",
        } <= set(graphs))
        self.assertEqual(graphs["games"]["entry"], "continue-rail")
        self.assertEqual(graphs["game-save-conflict-dialog"]["entry"], "cancel")

    def test_games_art_focus_is_one_flowing_surface_without_resizing_art(self):
        outputs = BUILD.outputs()
        rest = BUILD.ET.fromstring(
            outputs[BUILD.GENERATED / "renders/pages/games.svg"]
        )
        focus = BUILD.ET.fromstring(
            outputs[BUILD.GENERATED / "renders/pages/games-focus.svg"]
        )
        namespace = "{http://www.w3.org/2000/svg}"
        surfaces = [
            node for node in focus.iter()
            if node.attrib.get("data-focus-surface") == "artwork-tile"
        ]
        self.assertEqual(len(surfaces), 1)
        self.assertEqual(surfaces[0].tag, namespace + "rect")
        self.assertEqual(surfaces[0].attrib["height"], "340")
        self.assertEqual(surfaces[0].attrib["fill"], BUILD.load("tokens.json")["colors"]["jade"])
        rest_art = [
            (node.attrib["x"], node.attrib["y"], node.attrib["width"], node.attrib["height"])
            for node in rest.iter() if node.attrib.get("data-artwork-tile") == "true"
        ]
        focus_art = [
            (node.attrib["x"], node.attrib["y"], node.attrib["width"], node.attrib["height"])
            for node in focus.iter() if node.attrib.get("data-artwork-tile") == "true"
        ]
        self.assertEqual(rest_art, focus_art)

    def test_schema_documents_are_valid_json_schema(self):
        for path in sorted((HERE / "schemas").glob("*.schema.json")):
            schema = json.loads(path.read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")

    def test_every_component_and_page_has_1080p_fixture(self):
        catalogue = BUILD.load("catalogue.json")
        outputs = BUILD.outputs()
        for component in catalogue["components"]:
            path = BUILD.GENERATED / "renders/components" / f'{component["id"]}.svg'
            self.assertIn(path, outputs)
        for page in catalogue["pages"]:
            path = BUILD.GENERATED / "renders/pages" / f'{page["id"]}.svg'
            self.assertIn(path, outputs)
        for path, content in outputs.items():
            if path.suffix == ".svg":
                root = BUILD.ET.fromstring(content)
                self.assertEqual(root.attrib["width"], "1920")
                self.assertEqual(root.attrib["height"], "1080")


if __name__ == "__main__":
    unittest.main()
