import subprocess
import sys
import unittest

from poisoned_dataset import match
from poisoned_dataset.match import Defence, winner


class MatchTests(unittest.TestCase):
    def test_score_then_poison_found_then_tokens_spent(self):
        self.assertEqual(winner(Defence(8, 0, 4), Defence(4, 4, 0)), "A")
        self.assertEqual(winner(Defence(4, 1, 4), Defence(4, 2, 4)), "B")
        self.assertEqual(winner(Defence(8, 2, 2), Defence(8, 2, 4)), "A")
        self.assertIsNone(winner(Defence(8, 1, 3), Defence(8, 1, 3)))
        self.assertIsNone(winner(Defence(4, 0, 4), Defence(4, 3, 1), tiebreak=False))

    def test_documented_draw_rates_reproduce(self):
        rates = {k: (v["matches"], round(100 * v["draws_by_score"], 1), round(100 * v["draws_after_tiebreaks"], 1))
                 for k, v in match.report().items()}
        self.assertEqual(rates, {"seeded kit · conflict": (490, 50.6, 23.5), "seeded kit · random": (490, 66.3, 36.1),
                                 "fixed edition · conflict": (324, 52.2, 25.9),
                                 "fixed edition · random": (324, 82.4, 43.5)})

    def test_terminal_match_reports_tiebreaks(self):
        cases = [("\n" * 8, "Draw."),
                 ("\n".join(("", "C22 C03 C23", "", "C05", "C10", "C03", "C22", "", "", "", "")) + "\n",
                  "Player A wins.")]
        for responses, outcome in cases:
            with self.subTest(outcome=outcome):
                result = subprocess.run([sys.executable, "-m", "poisoned_dataset", "play", "--seed", "19"],
                                        input=responses, text=True, capture_output=True, check=True)
                self.assertIn("Tied on score.", result.stdout)
                self.assertIn(outcome, result.stdout)
        self.assertIn("Poison found: A 2, B 0. Tokens spent: A 4, B 0.", result.stdout)


if __name__ == "__main__":
    unittest.main()
