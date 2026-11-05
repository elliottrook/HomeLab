import unittest

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_reference_training_v1 as training


def zeros():
    return {name: [0.0] * artifact._count(shape)
            for name, shape in artifact.SHAPES.items()}


class J2ReferenceTrainingTests(unittest.TestCase):
    def test_zero_relu_derivative_and_lowest_pool_tie_are_frozen(self):
        tensors = zeros()
        loss, gradients = training.loss_and_gradients("xx", 1, tensors)
        self.assertGreater(loss, 0.0)
        # Zero preactivations mean ReLU derivative zero throughout the feature
        # path; only the output bias receives the softmax gradient.
        for name in training.PARAMETER_ORDER:
            if name != "output-bias":
                self.assertEqual({0.0}, set(gradients[name]))
        self.assertAlmostEqual(-15 / 16, gradients["output-bias"][1])
        self.assertAlmostEqual(1 / 16, gradients["output-bias"][0])

    def test_sparse_backward_routes_pool_gradient_to_first_maximum(self):
        tensors = zeros()
        tensors["byte-embedding"][ord("x") * 32] = 1.0
        tensors["conv-width-3-weight"][(1 * 32) * 48] = 1.0
        tensors["hidden-weight"][0] = 1.0
        tensors["output-weight"][1] = 1.0
        _, gradients = training.loss_and_gradients("xx", 0, tensors)
        # Both x positions tie at one, but only the lowest-position receptive
        # field contributes to the selected max-pool derivative.
        self.assertNotEqual(0.0, gradients["conv-width-3-weight"][(1 * 32) * 48])
        self.assertNotEqual(0.0, gradients["byte-embedding"][ord("x") * 32])

    def test_sparse_backward_matches_centered_finite_differences(self):
        tensors = zeros()
        tensors["byte-embedding"][ord("x") * 32] = 0.7
        convolution_index = (1 * 32) * 48
        tensors["conv-width-3-weight"][convolution_index] = 0.8
        tensors["hidden-weight"][0] = 0.9
        tensors["output-weight"][1] = 1.1
        _, gradients = training.loss_and_gradients("x", 0, tensors)
        epsilon = 1e-6
        for name, index in (("byte-embedding", ord("x") * 32),
                            ("conv-width-3-weight", convolution_index),
                            ("hidden-weight", 0), ("output-weight", 1)):
            original = tensors[name][index]
            tensors[name][index] = original + epsilon
            plus, _ = training.loss_and_gradients("x", 0, tensors)
            tensors[name][index] = original - epsilon
            minus, _ = training.loss_and_gradients("x", 0, tensors)
            tensors[name][index] = original
            measured = (plus - minus) / (2.0 * epsilon)
            self.assertAlmostEqual(measured, gradients[name][index], places=7,
                                   msg=f"finite difference mismatch for {name}")

    def test_batch_requires_unique_sorted_ids_and_means_rows(self):
        tensors = zeros()
        rows = [{"id": "a", "text": "x", "label_id": training.inference.LABELS[0]},
                {"id": "b", "text": "y", "label_id": training.inference.LABELS[1]}]
        loss, gradients = training.mean_gradients(rows, tensors)
        self.assertGreater(loss, 0.0)
        self.assertAlmostEqual((-15 / 16 + 1 / 16) / 2,
                               gradients["output-bias"][0])
        for changed in ((rows[1], rows[0]), (rows[0], rows[0])):
            with self.subTest(), self.assertRaises(ValueError):
                training.mean_gradients(changed, tensors)

    def test_epoch_is_exactly_24_unshuffled_complete_batches(self):
        rows = [{"id": f"j2-train-{index:04d}", "text": f"row {index}",
                 "label_id": training.inference.LABELS[index % 16]}
                for index in range(768)]
        batches = training.epoch_batches(rows)
        self.assertEqual(24, len(batches))
        self.assertTrue(all(len(batch) == 32 for batch in batches))
        self.assertEqual(rows[0], batches[0][0])
        self.assertEqual(rows[-1], batches[-1][-1])
        changed = list(rows); changed[0], changed[1] = changed[1], changed[0]
        with self.assertRaises(ValueError): training.epoch_batches(changed)

    def test_one_batch_means_one_adam_step_and_biases_do_not_decay(self):
        tensors = zeros()
        tensors["output-weight"][0] = 1.0
        tensors["output-bias"][0] = 1.0
        gradients = zeros()
        state = training.optimizer_state()
        updated, next_state = training.apply_batch(tensors, gradients, state, 1)
        self.assertLess(updated["output-weight"][0], 1.0)
        self.assertEqual(1.0, updated["output-bias"][0])
        self.assertEqual(0.0, next_state["output-weight"]["first"][0])

    def test_invalid_target_batch_and_optimizer_shape_fail_closed(self):
        with self.assertRaises(ValueError):
            training.loss_and_gradients("x", 16, zeros())
        with self.assertRaises(ValueError):
            training.mean_gradients([], zeros())
        bad = training.optimizer_state(); bad["output-bias"]["first"].pop()
        with self.assertRaises(ValueError):
            training.apply_batch(zeros(), zeros(), bad, 1)


if __name__ == "__main__": unittest.main()
