import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from poisoned_dataset import box, components, decks, edition, rulebook
from poisoned_dataset.core import RULES

ROOT = Path(__file__).resolve().parent.parent


def visible_text(svg: str) -> str:
    return " ".join(re.findall(r"<text[^>]*>(.*?)</text>", svg)).lower()


class FixedEditionTests(unittest.TestCase):
    def test_decks_come_from_the_documented_selection_on_development_seeds(self):
        self.assertEqual(decks.select(), decks.FIXED_DECKS)
        self.assertTrue(all(seed in decks.DEV_SEEDS for seed in decks.FIXED_DECKS.values()))
        for letter, seed in decks.FIXED_DECKS.items():
            self.assertTrue(decks.eligible(decks.assess(seed)), letter)
            deck = decks.deck(letter)
            self.assertEqual([c.id for c in deck], [f"{letter}{n:02}" for n in range(1, 25)])
            self.assertEqual([c.features for c in deck], [c.features for c in decks.deck_cards(seed)])

    def test_face_down_cards_reveal_nothing(self):
        for profile in edition.PROFILES:
            back = visible_text(edition.reference_back(profile))
            self.assertNotIn("store", back)
            self.assertNotIn("recycle", back)
            self.assertNotEqual(edition.reference_front(profile, 1), edition.reference_front(profile, 0))
        self.assertFalse(any(rule in visible_text(edition.truth_back()) for rule in RULES))
        self.assertEqual(edition.mirrored(list("abcdefgh")), list("dcbahgfe"))

    def test_build_has_every_component_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fixed"
            edition.build(out)
            html = "".join((out / name).read_text() for name in ("cards.html", "duplex.html"))
            counts = {kind: html.count(f'data-kind="{kind}"') for kind in
                      ("training", "test", "trusted-reference", "back-trusted-reference", "truth", "back-truth",
                       "rule", "score", "aid", "role")}
            self.assertEqual(counts, {"training": 96, "test": 8, "trusted-reference": 16, "back-trusted-reference": 16,
                                      "truth": 3, "back-truth": 3, "rule": 3, "score": 1, "aid": 2, "role": 2})
            self.assertNotIn("True rule:", html)

    def test_rulebook_and_box_follow_the_edition(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rulebook.build(out, "fixed")
            box.build(out, edition="fixed")
            book, lid = (out / "rulebook.html").read_text(), (out / "box.html").read_text()
            self.assertIn("reference row", book)
            self.assertNotIn("sealed audit slips", book)
            self.assertNotIn("deployment key", book)
            self.assertIn("16 reference cards", lid)
            self.assertNotIn("sealed audit slips", lid)

    def test_cli_builds_the_fixed_edition(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "kit"
            subprocess.run([sys.executable, "-m", "poisoned_dataset", "components", "--edition", "fixed",
                            "--out", str(out)], check=True, capture_output=True, cwd=ROOT)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["backs.html", "box.html", "cards.html", "duplex.html", "rulebook-booklet.html",
                              "rulebook.html"])

    def test_committed_print_files_match_the_generators(self):
        with tempfile.TemporaryDirectory() as tmp:
            seeded, fixed = Path(tmp) / "seeded", Path(tmp) / "fixed"
            components.build(seeded, 42, "correlated")
            edition.build(fixed)
            for out, name in ((seeded, "seeded"), (fixed, "fixed")):
                rulebook.build(out, name)
                box.build(out, edition=name)
            for out, folder in ((seeded, "kit-seed-42"), (fixed, "fixed-edition")):
                for built in out.iterdir():
                    committed = ROOT / "print" / folder / built.name
                    self.assertEqual(built.read_bytes(), committed.read_bytes(), f"{folder}/{built.name} is stale")


if __name__ == "__main__":
    unittest.main()
