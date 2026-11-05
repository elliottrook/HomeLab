import copy
import unittest

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_reference_forward_v1 as forward


def zeros():
    return {name: [0.0] * artifact._count(shape)
            for name, shape in artifact.SHAPES.items()}


class J2ReferenceForwardTests(unittest.TestCase):
    def test_zero_state_is_uniform_with_stable_label_tie_break(self):
        result = forward.forward("bounded synthetic request", zeros())
        self.assertEqual(forward.LABELS[0], result["label_id"])
        self.assertAlmostEqual(1 / 16, result["confidence"])
        self.assertEqual(0.0, result["margin"])
        self.assertAlmostEqual(1.0, sum(result["probabilities"]))

    def test_output_bias_selects_exact_label(self):
        tensors = zeros(); tensors["output-bias"][7] = 2.0
        result = forward.forward("x", tensors)
        self.assertEqual(forward.LABELS[7], result["label_id"])
        self.assertGreater(result["confidence"], result["probabilities"][0])
        self.assertGreater(result["margin"], 0.0)

    def test_sparse_embedding_convolution_hidden_output_layout(self):
        tensors = zeros()
        tensors["byte-embedding"][ord("x") * 32] = 1.0
        tensors["conv-width-3-weight"][(1 * 32) * 48] = 1.0
        tensors["hidden-weight"][0] = 1.0
        tensors["output-weight"][5] = 2.0
        result = forward.forward("x", tensors)
        self.assertEqual(forward.LABELS[5], result["label_id"])
        self.assertGreater(result["margin"], 0.0)

    def test_tensor_shape_type_and_input_fail_closed(self):
        variants = []
        changed = zeros(); changed["output-bias"].pop(); variants.append(changed)
        changed = zeros(); changed["extra"] = []; variants.append(changed)
        changed = zeros(); changed["hidden-bias"][0] = float("nan"); variants.append(changed)
        for changed in variants:
            with self.subTest(), self.assertRaises(ValueError):
                forward.forward("x", changed)
        with self.assertRaises(ValueError): forward.forward("", zeros())


if __name__ == "__main__": unittest.main()
