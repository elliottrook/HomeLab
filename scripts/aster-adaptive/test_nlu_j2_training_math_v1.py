import math
import unittest

import nlu_j2_training_math_v1 as training


class J2TrainingMathTests(unittest.TestCase):
    def test_cross_entropy_is_max_shifted_and_exactly_normalized(self):
        loss, probabilities = training.cross_entropy([0.0] * 16, 0)
        self.assertAlmostEqual(math.log(16), loss)
        self.assertEqual((1 / 16,) * 16, probabilities)
        loss, probabilities = training.cross_entropy(
            [1000.0, 999.0] + [0.0] * 14, 0)
        self.assertTrue(math.isfinite(loss))
        self.assertAlmostEqual(1.0, sum(probabilities))
        self.assertGreater(probabilities[0], probabilities[1])

    def test_first_adamw_step_and_bias_decay_scope_are_fixed(self):
        weight, first, second = training.adamw_scalar(
            1.0, 0.5, 0.0, 0.0, 1, weight=True)
        bias, _, _ = training.adamw_scalar(
            1.0, 0.5, 0.0, 0.0, 1, weight=False)
        self.assertAlmostEqual(0.05, first)
        self.assertAlmostEqual(0.00025, second)
        self.assertAlmostEqual(0.99899990012, weight, places=15)
        self.assertAlmostEqual(0.99900000002, bias, places=15)
        self.assertLess(weight, bias)

    def test_second_step_bias_correction_replays(self):
        parameter, first, second = training.adamw_scalar(
            0.25, -0.2, 0.0, 0.0, 1, weight=True)
        result = training.adamw_scalar(
            parameter, 0.1, first, second, 2, weight=True)
        replay = training.adamw_scalar(
            parameter, 0.1, first, second, 2, weight=True)
        self.assertEqual(result, replay)

    def test_invalid_shapes_nonfinite_step_and_state_fail_closed(self):
        for logits, target in (([0.0] * 15, 0), ([0.0] * 16, 16),
                               ([float("nan")] * 16, 0)):
            with self.subTest(), self.assertRaises(ValueError):
                training.cross_entropy(logits, target)
        for args in ((1.0, 0.1, 0.0, 0.0, 0),
                     (1.0, float("inf"), 0.0, 0.0, 1),
                     (1.0, 0.1, 0.0, -1.0, 1)):
            with self.subTest(), self.assertRaises(ValueError):
                training.adamw_scalar(*args, weight=True)


if __name__ == "__main__": unittest.main()
