import math
import unittest

from signal_demo.core import analyze, ascii_trace, moving_average, synthetic_signal


class SignalTests(unittest.TestCase):
    def test_generation_is_finite_and_reproducible(self):
        samples = synthetic_signal()
        self.assertEqual(len(samples), 600)
        self.assertTrue(all(math.isfinite(value) for value in samples))
        self.assertEqual(samples, synthetic_signal())
        self.assertNotEqual(samples, synthetic_signal(seed=8))

    def test_smoothing_preserves_constant_and_normalizes_edges(self):
        self.assertEqual(moving_average([4.0] * 5), [4.0] * 5)
        self.assertEqual(moving_average([0, 3, 0]), [1.5, 1.0, 1.5])
        self.assertEqual(moving_average([2.0], 5), [2.0])

    def test_smoothing_reduces_alternating_variation(self):
        source = [1.0, -1.0] * 50
        smoothed = moving_average(source)
        self.assertLess(sum(value * value for value in smoothed),
                        sum(value * value for value in source))

    def test_invented_phases_have_expected_descriptive_states(self):
        windows = analyze(synthetic_signal())
        self.assertEqual([window.state for window in windows],
                         ["quiet"] * 4 + ["oscillating"] * 4 + ["varying"] * 4)
        self.assertEqual([window.start_seconds for window in windows], list(range(12)))

    def test_known_feature_values(self):
        window = analyze([0, 2, 0, 2], sample_rate=4)[0]
        self.assertAlmostEqual(window.spread, 1.0)
        self.assertAlmostEqual(window.mean_step, 2.0)
        self.assertEqual(analyze([5.0] * 50)[0].state, "quiet")

    def test_invalid_and_incomplete_samples_are_rejected(self):
        for samples in ([], [float("nan")] * 50, [float("inf")] * 50):
            for operation in (analyze, moving_average, ascii_trace):
                with self.assertRaises(ValueError):
                    operation(samples)
        with self.assertRaises(ValueError):
            analyze([0] * 51)
        for rate in (0, 1, 2.5, True):
            with self.assertRaises(ValueError):
                analyze([0] * 50, rate)
        for width in (0, 2, -1, 1.5, True):
            with self.assertRaises(ValueError):
                moving_average([0, 1, 0], width)

    def test_trace_has_bounded_ascii_output(self):
        trace = ascii_trace([-100, 0, 100], columns=3)
        self.assertEqual(trace, " =@")
        self.assertEqual(len(ascii_trace(synthetic_signal())), 72)
        for columns in (0, 1, 2.5, True):
            with self.assertRaises(ValueError):
                ascii_trace([0], columns)


if __name__ == "__main__":
    unittest.main()
