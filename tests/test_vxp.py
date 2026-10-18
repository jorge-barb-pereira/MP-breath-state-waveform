import contextlib
from dataclasses import asdict
import io
from pathlib import Path
import tempfile
import unittest

from signal_demo.__main__ import main
from signal_demo.vxp import (
    MAX_ROWS, MAX_TEXT_SIZE, VXPError, parse_vxp, read_vxp, smooth_valid,
    synthetic_vxp_text, window_features,
)


def fixture(rows, extra_header=""):
    """All values in these tests are invented, including identifier sentinels."""
    return (
        "[Header]\nVersion=1.6\n"
        "Data_layout=amplitude,phase,timestamp,validflag,ttlin,mark,ttlout\n"
        "Samples_per_second=4\nScale_factor=2\n"
        + extra_header + "[Data]\n" + "\n".join(rows) + "\n"
    )


class VXPTests(unittest.TestCase):
    def test_time_origin_and_scaling_are_independent_of_header_identity(self):
        text = fixture(["1,0,8000,0,0,,0", "3,0,8250,0,0,,0"],
                       "Patient_ID=INVENTED_PRIVATE_SENTINEL\nDate=INVENTED_DATE\nCRC=0\n")
        trace = parse_vxp(text)
        self.assertEqual([sample.seconds for sample in trace.samples], [0.0, 0.25])
        self.assertEqual([sample.amplitude_mm for sample in trace.samples], [2.0, 6.0])
        self.assertNotIn("SENTINEL", repr(asdict(trace)))
        self.assertNotIn("INVENTED_DATE", repr(trace))
        self.assertEqual(set(asdict(trace)), {"samples_per_second", "samples"})

    def test_layout_order_aliases_and_crlf_are_supported(self):
        text = fixture(["1,0,250,0,0,,0"])
        text = text.replace("amplitude,phase,timestamp,validflag,ttlin,mark,ttlout",
                            "Time_Stamp,Value_of_respiratory_wave,Phase_value,Valid_Flag,TTL_In,Mark,TTL_Out")
        text = text.replace("1,0,250,0,0,,0", "250,1,0,0,0,,0")
        trace = parse_vxp("\ufeff" + text.replace("\n", "\r\n"))
        self.assertEqual(trace.samples[0].amplitude_mm, 2.0)

    def test_invalid_samples_and_gaps_are_not_bridged(self):
        trace = parse_vxp(fixture([
            "0,0,0,0,0,,0", "1,0,250,0,0,,0", "99,0,500,-1,0,,0",
            "4,0,750,0,0,,0", "10,0,2500,0,0,,0",
        ]))
        self.assertEqual(smooth_valid(trace), (1.0, 1.0, None, 8.0, 20.0))
        windows = window_features(trace)
        self.assertEqual([window.start_seconds for window in windows], [0.0, 2.0])
        self.assertEqual(windows[0].valid_count, 3)
        self.assertAlmostEqual(windows[0].mean_mm, 10 / 3)
        self.assertEqual(windows[0].mean_step_mm, 2.0)
        self.assertIsNone(windows[1].mean_step_mm)

    def test_empty_valid_window_reports_missing_values(self):
        trace = parse_vxp(fixture(["99,0,0,-1,0,,0", "88,0,250,-2,0,,0"]))
        window = window_features(trace)[0]
        self.assertEqual(window.valid_count, 0)
        self.assertIsNone(window.mean_mm)
        self.assertIsNone(window.spread_mm)
        self.assertIsNone(window.range_mm)
        self.assertIsNone(window.mean_step_mm)
        self.assertEqual(smooth_valid(trace), (None, None))

    def test_known_statistics_and_partial_window(self):
        trace = parse_vxp(fixture(["0,0,0,0,0,,0", "1,0,250,0,0,,0", "2,0,500,0,0,,0"]))
        window = window_features(trace)[0]
        self.assertEqual(window.sample_count, 3)
        self.assertEqual(window.mean_mm, 2.0)
        self.assertAlmostEqual(window.spread_mm, (8 / 3) ** 0.5)
        self.assertEqual(window.range_mm, 4.0)
        self.assertEqual(window.mean_step_mm, 2.0)
        for duration in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(VXPError):
                window_features(trace, duration)

    def test_unknown_versions_layouts_and_headers_fail_closed(self):
        base = fixture(["1,0,0,0,0,,0"])
        invalid = [
            base.replace("Version=1.6", "Version=2.0"),
            base.replace("Scale_factor=2\n", ""),
            base.replace("Scale_factor=2", "Scale_factor=0"),
            base.replace("Samples_per_second=4", "Samples_per_second=-4"),
            base.replace("[Data]", "[Unsupported]"),
            base.replace("phase,timestamp", "amplitude,timestamp"),
            base.replace("phase,timestamp", "unknown,timestamp"),
            base.replace("Version=1.6", "Version=1.6\nVersion=1.6"),
        ]
        for text in invalid:
            with self.subTest(case=invalid.index(text)), self.assertRaises(VXPError):
                parse_vxp(text)

    def test_malformed_rows_and_nonfinite_values_fail_without_echo(self):
        bad_rows = [
            "INVENTED_SECRET_SENTINEL,0,0,0,0,,0", "nan,0,0,0,0,,0",
            "inf,0,0,0,0,,0", "1,0,-1,0,0,,0", "1,0,0,1,0,,0",
            "1,0,0,0.5,0,,0", "1,0,0,0,2,,0", "1,0,0,0,0,X,0",
            "1,0,0,0,0,,0,extra", "1,0,0,0,0",
        ]
        for row in bad_rows:
            with self.assertRaises(VXPError) as caught:
                parse_vxp(fixture([row]))
            self.assertNotIn("SENTINEL", str(caught.exception))
        for timestamp in (0, -1):
            with self.assertRaises(VXPError):
                parse_vxp(fixture(["1,0,0,0,0,,0", f"1,0,{timestamp},0,0,,0"]))

    def test_resource_limits_and_empty_data(self):
        for text in ("", "x" * (MAX_TEXT_SIZE + 1), fixture([]),
                     fixture(["1,0,0,0,0,,0"] * (MAX_ROWS + 1)),
                     fixture(["1,0,0,0,0,,0"]) + "\x00"):
            with self.assertRaises(VXPError):
                parse_vxp(text)

    def test_arithmetic_overflow_is_reported_with_fixed_diagnostics(self):
        trace = parse_vxp(fixture(["8e307,0,0,0,0,,0", "8e307,0,250,0,0,,0"]))
        for operation in (smooth_valid, window_features):
            with self.assertRaises(VXPError) as caught:
                operation(trace)
            self.assertNotIn("8e307", str(caught.exception))

    def test_local_reader_and_cli_do_not_echo_paths_or_header_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "INVENTED_FILENAME_SENTINEL.vxp"
            path.write_text(fixture(["INVENTED_VALUE_SENTINEL,0,0,0,0,,0"]), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(["--vxp", str(path)]), 2)
            self.assertNotIn("SENTINEL", stderr.getvalue())
            path.write_bytes(b"\xff")
            with self.assertRaises(VXPError):
                read_vxp(path)
            path.write_text(synthetic_vxp_text(), encoding="utf-8")
            self.assertEqual(len(read_vxp(path).samples), 600)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(main(["--vxp", str(path) + ".missing"]), 2)
            self.assertNotIn(str(path), stderr.getvalue())

    def test_generated_fixture_matches_reviewed_artifact(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root / "examples/synthetic.vxp").read_text(encoding="utf-8"),
                         synthetic_vxp_text())
        trace = parse_vxp(synthetic_vxp_text())
        self.assertEqual(len(trace.samples), 600)
        self.assertEqual(sum(sample.valid for sample in trace.samples), 595)

    def test_cli_demo_and_file_match_the_reviewed_summary(self):
        root = Path(__file__).resolve().parents[1]
        expected = (root / "examples/vxp-output.txt").read_text(encoding="utf-8")
        for arguments in (["--vxp-demo"], ["--vxp", str(root / "examples/synthetic.vxp")]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(arguments), 0)
            self.assertEqual(output.getvalue(), expected)
            self.assertNotIn("SYNTHETIC_ONLY", output.getvalue())


if __name__ == "__main__":
    unittest.main()
