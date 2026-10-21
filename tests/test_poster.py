import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRESENTATION = ROOT / "presentation"


def load_poster():
    spec = importlib.util.spec_from_file_location("poster", PRESENTATION / "poster.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.poster = load_poster()

    def test_committed_poster_and_figures_match_generator(self):
        self.assertEqual((PRESENTATION / "poster.html").read_text(encoding="utf-8"), self.poster.build())
        for name, markup in self.poster.figures().items():
            ET.fromstring(markup)
            self.assertEqual((PRESENTATION / "figures" / name).read_text(encoding="utf-8"), markup, name)

    def test_poster_reports_the_frozen_headline(self):
        html = self.poster.build()
        headline = json.loads((self.poster.RESULTS / "report" / "headline.json").read_text())
        paired, defenses = headline["paired_difference"], headline["defenses"]
        self.assertIn(f"+{100 * paired['mean']:.1f}", html)
        self.assertIn(f"{100 * paired['ci95'][0]:+.1f} to {100 * paired['ci95'][1]:+.1f}", html)
        self.assertIn(f"{paired['wins']} · {paired['ties']} · {paired['losses']}", html)
        self.assertIn(f"{defenses['conflict']['restored_true_rule']} vs {defenses['random']['restored_true_rule']}",
                      html)
        self.assertIn(f"Seed {headline['trace_seed']}", html)
        self.assertIn("size: 36in 24in", html)

    def test_size_is_a_parameter(self):
        self.assertIn("size: 48in 36in", self.poster.build(48, 36))

    def test_all_reused_svg_art_has_a_definition(self):
        html = self.poster.build()
        ids = set(re.findall(r'\bid="([^"]+)"', html))
        references = set(re.findall(r'<use\b[^>]*\bhref="#([^"]+)"', html))
        self.assertTrue(references)
        self.assertFalse(references - ids, f"Missing SVG definitions: {references - ids}")


if __name__ == "__main__":
    unittest.main()
