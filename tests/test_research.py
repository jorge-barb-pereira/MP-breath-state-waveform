import math
import unittest

from signal_demo.research import Cycle, difference_metrics, evaluate_cycle, invented_cases
from signal_demo.vxp import Sample, Trace, parse_vxp, synthetic_vxp_text


def triangle(valid=None, times=None):
    values = [1, .5, 0, -.5, -1, -.5, 0, .5, 1]
    return Trace(4, tuple(Sample(index / 4 if times is None else times[index], value,
                                 True if valid is None else valid[index])
                          for index, value in enumerate(values)))


class ResearchTests(unittest.TestCase):
    def test_maximum_to_maximum_anchors_and_continuous_values(self):
        result = evaluate_cycle(triangle(), Cycle(0, 1, 2))
        rows = result['rows']
        self.assertEqual([rows[index]['amplitude_state'] for index in (0, 4, 8)], [0, .5, 1])
        self.assertEqual([row['phase'] for row in rows], [row['amplitude_state'] for row in rows])
        self.assertEqual(result['metrics']['rms_difference'], 0)
        self.assertIsNone(rows[-1]['phase_bin'])
        self.assertEqual(result['metrics']['compared_samples'], 8)
        self.assertEqual(sum(result['metrics']['phase_bin_counts']), 8)
        self.assertEqual(sum(result['metrics']['amplitude_bin_counts']), 8)
        self.assertEqual(result['metrics']['bin_offset_counts'], {'0': 8})

    def test_dual_phase_places_trough_at_half_without_changing_time_phase(self):
        data = triangle(times=[0, .125, .25, .375, .5, .875, 1.25, 1.625, 2])
        result = evaluate_cycle(data, Cycle(0, .5, 2))
        self.assertEqual(result['rows'][4]['phase'], .25)
        self.assertEqual(result['rows'][4]['dual_phase'], .5)
        self.assertEqual(result['rows'][4]['amplitude_state'], .5)

    def test_rms_is_time_normalized_and_l2_scales_with_duration(self):
        for times in ([0, 1, 2], [0, .1, 8]):
            metrics = difference_metrics(times, [.25] * 3, 10)
            self.assertAlmostEqual(metrics['rms_difference'], .25)
            self.assertAlmostEqual(metrics['l2_difference'], .25 * math.sqrt(times[-1]))
        linear = difference_metrics([0, 2], [0, 1], 3)
        self.assertAlmostEqual(linear['rms_difference'], math.sqrt(1 / 3))

    def test_undefined_intervals_and_timing_gaps_do_not_produce_full_cycle_rms(self):
        for values, limit in (([0, None, 1], 2), ([0, .5, 1], .5)):
            metrics = difference_metrics([0, 1, 2], values, limit)
            self.assertIsNone(metrics['rms_difference'])
        data = triangle([True, True, False, True, True, True, True, True, True])
        result = evaluate_cycle(data, Cycle(0, 1, 2))
        self.assertIsNone(result['rows'][2]['amplitude_state'])
        self.assertIsNone(result['rows'][2]['amplitude_velocity_per_second'])
        self.assertIsNone(result['metrics']['rms_difference'])

    def test_out_of_calibration_samples_are_undefined_not_clipped(self):
        result = evaluate_cycle(triangle(), Cycle(0, 1, 2), calibration=(-.75, .75))
        self.assertIsNone(result['rows'][0]['amplitude_state'])
        self.assertIsNone(result['rows'][4]['amplitude_state'])
        self.assertIsNone(result['metrics']['rms_difference'])

    def test_plateau_has_zero_amplitude_velocity_with_positive_phase_velocity(self):
        result = invented_cases()['valley_plateau']
        plateau = [row for row in result['rows'] if 2.1 < row['seconds'] < 2.5]
        self.assertTrue(plateau)
        self.assertTrue(all(row['amplitude_velocity_per_second'] == 0 for row in plateau))
        self.assertTrue(all(row['phase_velocity_per_second'] > 0 for row in plateau))

    def test_small_continuous_difference_does_not_imply_same_bin(self):
        # An invented counterexample at a bin boundary.
        left, right, bins = .099, .101, 10
        self.assertLess(abs(left - right), .5 / bins)
        self.assertNotEqual(int(left * bins), int(right * bins))

    def test_vxp_adapter_uses_relative_time_without_header_identity(self):
        trace = parse_vxp(synthetic_vxp_text())
        # This is only API integration on invented input, not peak detection.
        start = max((sample for sample in trace.samples if 4 <= sample.seconds <= 4.3), key=lambda sample: sample.amplitude_mm)
        trough = min((sample for sample in trace.samples if 4.3 <= sample.seconds <= 4.7), key=lambda sample: sample.amplitude_mm)
        stop = max((sample for sample in trace.samples if 4.7 <= sample.seconds <= 5), key=lambda sample: sample.amplitude_mm)
        cycle = Cycle(start.seconds, trough.seconds, stop.seconds)
        result = evaluate_cycle(trace, cycle, calibration=(-2, 2))
        self.assertEqual(result['rows'][0]['seconds'], start.seconds)
        self.assertNotIn('SYNTHETIC_ONLY', repr(result))

    def test_invalid_cycles_calibration_and_bins_are_rejected(self):
        for cycle in (Cycle(0, 0, 2), Cycle(0, 1, 3), Cycle(0, math.nan, 2)):
            with self.assertRaises(ValueError):
                evaluate_cycle(triangle(), cycle)
        for bins in (True, 1, 65, 2.5):
            with self.assertRaises(ValueError):
                evaluate_cycle(triangle(), Cycle(0, 1, 2), bins=bins)
        with self.assertRaises(ValueError):
            evaluate_cycle(triangle(), Cycle(0, 1, 2), calibration=(1, 1))

    def test_examples_are_reproducible_and_not_claimed_as_measured_results(self):
        cases = invented_cases()
        self.assertEqual(cases, invented_cases())
        for case in cases.values():
            self.assertEqual(len(case['rows']), 401)
            self.assertAlmostEqual(case['metrics']['coverage_fraction'], 1)
            self.assertGreaterEqual(case['metrics']['rms_difference'], 0)
            self.assertTrue(all(row['phase_velocity_per_second'] > 0 for row in case['rows']))


if __name__ == '__main__':
    unittest.main()
