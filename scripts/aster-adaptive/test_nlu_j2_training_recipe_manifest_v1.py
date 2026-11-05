import copy
import json
from pathlib import Path
import unittest

import nlu_j2_training_recipe_manifest_v1 as recipe


MANIFEST = Path(__file__).parent / "fixtures" / "nlu-j2-training-recipe-manifest-v1.json"


class J2TrainingRecipeManifestTests(unittest.TestCase):
    def value(self):
        return json.loads(MANIFEST.read_text())

    def test_exact_source_only_manifest_is_accepted(self):
        result = recipe.validate(MANIFEST.read_bytes())
        self.assertEqual("source-only-not-trained", result["status"])
        self.assertEqual(512, result["input_bytes"])
        self.assertEqual(16, result["labels"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_duplicate_keys_and_extra_fields_fail_closed(self):
        with self.assertRaises(ValueError):
            recipe.validate(b'{"schema":"one","schema":"two"}')
        value = self.value(); value["corpus_sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            recipe.validate(recipe.canonical(value))

    def test_utf8_truncation_and_padding_are_frozen(self):
        for field, changed in (
                ("encoding", "utf-8-replace"),
                ("input_bytes", 511),
                ("overlength", "keep-last-512-encoded-bytes"),
                ("padding_token_id", 0)):
            value = self.value(); value["input"][field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_architecture_and_initialization_are_frozen(self):
        mutations = (
            lambda value: value["architecture"]["convolution"].update(padding="valid"),
            lambda value: value["architecture"]["convolution"].update(
                operation="kernel-reversal"),
            lambda value: value["architecture"]["convolution"].update(activation="gelu"),
            lambda value: value["architecture"].update(pretrained_weights=True),
            lambda value: value["architecture"]["embedding"].update(
                padding_row="trainable"),
            lambda value: value["initialization"].update(seed=1),
            lambda value: value["initialization"].update(prng="platform-random"),
            lambda value: value["initialization"]["fan_in_out"].update(
                {"byte-embedding": [256, 32]}),
            lambda value: value["initialization"].update(
                tensor_scalar_order="column-major"),
            lambda value: value["initialization"].update(
                initialization_replay_sha256="0" * 64),
        )
        for mutation in mutations:
            value = self.value(); mutation(value)
            with self.subTest(), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_optimizer_order_and_offline_boundary_are_frozen(self):
        mutations = (
            lambda value: value["training"]["optimizer"].update(learning_rate=.01),
            lambda value: value["training"]["optimizer"].update(
                epsilon_placement="inside-sqrt"),
            lambda value: value["training"].update(shuffle=True),
            lambda value: value["training"].update(row_order="random"),
            lambda value: value["training"].update(
                relu_derivative_at_zero=1.0),
            lambda value: value["training"].update(
                global_max_tie_gradient="all-tied-positions"),
            lambda value: value["training"].update(
                batch_update_boundary="one-step-per-row"),
            lambda value: value["training"].update(network="allowed"),
            lambda value: value["training"].update(evaluation_inputs="allowed"),
        )
        for mutation in mutations:
            value = self.value(); mutation(value)
            with self.subTest(), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_validation_selection_and_coverage_are_frozen(self):
        mutations = (
            lambda value: value["validation_selection"].update(source="sealed-evaluation"),
            lambda value: value["validation_selection"].update(minimum_accepted=0),
            lambda value: value["validation_selection"]["threshold_grid"].update(step=.01),
            lambda value: value["validation_selection"].update(
                accepted_row_requirement="raw-label-exact"),
        )
        for mutation in mutations:
            value = self.value(); mutation(value)
            with self.subTest(), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_quantization_artifact_pin_and_replay_are_frozen(self):
        mutations = (
            lambda value: value["artifact"]["weight_quantization"].update(
                decimal_places=8),
            lambda value: value["artifact"].update(
                externally_pinned_artifact_digest_required=False),
            lambda value: value["artifact"]["replay"].update(rows=191),
            lambda value: value["artifact"]["replay"].update(
                require_two_clean_cpu_reproductions=False),
            lambda value: value["artifact"]["replay"].update(
                recompute_from_validation_truth=False),
        )
        for mutation in mutations:
            value = self.value(); mutation(value)
            with self.subTest(), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_guard_cpu_and_no_effect_boundary_are_frozen(self):
        mutations = (
            lambda value: value["runtime_boundary"].update(
                guard_projection="use-guard-output-unconditionally"),
            lambda value: value["runtime_boundary"].update(
                personal_sensitivity_floor=False),
            lambda value: value["runtime_boundary"].update(tools="allowed"),
            lambda value: value["runtime_boundary"].update(route_effects="allowed"),
            lambda value: value.update(authority="granted"),
            lambda value: value.update(automatic_routing="on"),
        )
        for mutation in mutations:
            value = self.value(); mutation(value)
            with self.subTest(), self.assertRaises(ValueError):
                recipe.validate(recipe.canonical(value))

    def test_manifest_pins_current_ontology_and_guard_sources(self):
        value = self.value()
        expected = recipe.expected_manifest()["runtime_boundary"]
        self.assertEqual(expected["ontology_source_sha256"],
                         value["runtime_boundary"]["ontology_source_sha256"])
        self.assertEqual(expected["deterministic_guard_source_sha256"],
                         value["runtime_boundary"]["deterministic_guard_source_sha256"])
        self.assertEqual(expected["reference_primitives_source_sha256"],
                         value["runtime_boundary"]["reference_primitives_source_sha256"])
        self.assertEqual(expected["reference_forward_source_sha256"],
                         value["runtime_boundary"]["reference_forward_source_sha256"])
        self.assertEqual(expected["validation_selection_source_sha256"],
                         value["runtime_boundary"]["validation_selection_source_sha256"])
        self.assertEqual(expected["training_math_source_sha256"],
                         value["runtime_boundary"]["training_math_source_sha256"])
        self.assertEqual(expected["reference_training_source_sha256"],
                         value["runtime_boundary"]["reference_training_source_sha256"])


if __name__ == "__main__":
    unittest.main()
