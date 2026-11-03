"""Check that publishable SVG fixtures reject active or identifying additions."""

from pathlib import Path
import unittest

from tools.check_release import check_sorting_svg


class SortingFigureReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.figure = (root / 'docs/figures/sorting-continuous.svg').read_bytes()

    def test_independently_generated_svg_is_passive(self):
        check_sorting_svg(self.figure)

    def test_active_content_and_external_resources_are_rejected(self):
        variants = (
            self.figure.replace(b'</svg>', b'<script>1</script></svg>'),
            self.figure.replace(b'<svg ', b'<svg onload="1" ', 1),
            self.figure.replace(b'</svg>', b'<use href="https://example.invalid/asset"/></svg>'),
            self.figure.replace(b'</svg>', b'<path style="fill:url(https://example.invalid/asset)"/></svg>'),
            self.figure.replace(b'</svg>', b'<path clip-path="url(https://example.invalid/asset)"/></svg>'),
            self.figure.replace(b'</svg>', b'<style>@import "https://example.invalid/asset";</style></svg>'),
        )
        for content in variants:
            with self.subTest(content=content[-100:]):
                with self.assertRaises(ValueError):
                    check_sorting_svg(content)

    def test_unreviewed_metadata_and_entity_declarations_are_rejected(self):
        for content in (
            self.figure.replace(b'Breath State Laboratory synthetic study', b'Unreviewed creator'),
            self.figure.replace(b'</metadata>', b'<date>Unreviewed date</date></metadata>'),
            self.figure.replace(b'<svg ', b'<!ENTITY injected "unreviewed"><svg ', 1),
        ):
            with self.subTest(content=content[:100]):
                with self.assertRaises(ValueError):
                    check_sorting_svg(content)


if __name__ == '__main__':
    unittest.main()
