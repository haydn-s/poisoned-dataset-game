import base64
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from poisoned_dataset import art, box, components, rulebook
from poisoned_dataset.core import RULES, generate, predict


class PrintKitTests(unittest.TestCase):
    def test_public_sheets_do_not_depend_on_secrets(self):
        def other_truth(seed, regime):
            s = generate(seed, regime=regime)
            rule = RULES[(RULES.index(s.true_rule) + 1) % 3]
            return replace(s, true_rule=rule, clean_labels=tuple(predict(rule, c) for c in s.cards))

        with tempfile.TemporaryDirectory() as tmp:
            components.build(Path(tmp) / "real", 19, "correlated")
            with mock.patch.object(components, "generate", lambda seed, regime: other_truth(seed, regime)):
                components.build(Path(tmp) / "swapped", 19, "correlated")
            for name in ("public.html", "backs.html"):
                self.assertEqual((Path(tmp) / "real" / name).read_bytes(), (Path(tmp) / "swapped" / name).read_bytes())
            self.assertNotEqual((Path(tmp) / "real" / "private.html").read_bytes(),
                                (Path(tmp) / "swapped" / "private.html").read_bytes())

    def test_kit_is_reproducible_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            outs = [Path(tmp) / "a", Path(tmp) / "b"]
            for out in outs:
                components.build(out, 7, "independent")
                rulebook.build(out)
                box.build(out)
            names = sorted(p.name for p in outs[0].iterdir())
            self.assertEqual(names, ["backs.html", "box.html", "private.html", "public.html", "rulebook-booklet.html",
                                     "rulebook.html", "scenario.json"])
            for name in names:
                self.assertEqual((outs[0] / name).read_bytes(), (outs[1] / name).read_bytes(), name)
            public = (outs[0] / "public.html").read_text()
            private = (outs[0] / "private.html").read_text()
            self.assertEqual(public.count('class="tag-strip"'), components.TAGS + components.SPARE_TAGS)
            self.assertEqual(private.count("TRUSTED LABEL"), 48)
            self.assertEqual(private.count("DEPLOYMENT KEY · R"), 2)
            for name in ("public.html", "backs.html", "rulebook.html", "box.html"):
                self.assertNotIn("True rule:", (outs[0] / name).read_text(), name)
            for name in ("public.html", "backs.html"):
                self.assertNotIn("TRUSTED LABEL", (outs[0] / name).read_text(), name)

    def test_tag_strips_flip_between_labels(self):
        strip = components.tag_strip(0)
        self.assertLess(strip.index("RECYCLE"), strip.index("STORE"))

    def test_rulebook_imposition_covers_every_page_once(self):
        pages = len(rulebook.PAGES)
        self.assertEqual(pages % 4, 0)
        sides = rulebook.imposition(pages)
        self.assertEqual(sorted(p for side in sides for p in side), list(range(1, pages + 1)))
        self.assertTrue(all(a + b == pages + 1 for a, b in sides))
        with self.assertRaises(ValueError):
            rulebook.imposition(10)

    def test_box_fits_contents_and_paper(self):
        (bl, bw, _), (ll, lw, _) = box.BASE, box.LID
        self.assertGreater(ll, bl)
        self.assertGreater(lw, bw)
        self.assertLessEqual(max(box.RULEBOOK), bl - .2)
        self.assertLessEqual(min(box.RULEBOOK), bw - .2)
        self.assertLessEqual(3 * box.WELL[0] + .4, bl)
        self.assertGreater(box.WELL[0], 2.5)
        self.assertGreater(box.WELL[1], 3.5)
        for length, width, depth in (box.BASE, box.LID):
            flat = (length + 2 * depth + 2 * box.TAB + 2 * box.BLEED, width + 2 * depth + 2 * box.BLEED)
            self.assertLessEqual(flat[0], 16.5)
            self.assertLessEqual(flat[1], 10.5)

    def test_cover_image_is_embedded(self):
        png = art._png(2, 2, bytearray(16))
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "cover.png"
            image.write_bytes(png)
            box.build(Path(tmp), image)
            self.assertIn("data:image/png;base64," + base64.b64encode(png).decode(), (Path(tmp) / "box.html").read_text())
            with self.assertRaises(ValueError):
                box.image_uri(Path(tmp) / "box.html")

    def test_grain_tile_is_a_png(self):
        data = base64.b64decode(art.grain_tile().split(",", 1)[1])
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(art.grain_tile(), art.grain_tile())


if __name__ == "__main__":
    unittest.main()
