import subprocess
import sys
import unittest

from poisoned_dataset import match
from poisoned_dataset.match import Defence, decided_by, winner


class MatchTests(unittest.TestCase):
    def test_score_then_poison_left_then_clean_audits(self):
        # Defence(points, flips, found, spent): poison left = flips - found, clean audits = spent - found.
        self.assertEqual(winner(Defence(8, 4, 0, 4), Defence(4, 4, 4, 4)), "A")
        self.assertEqual(winner(Defence(4, 4, 1, 4), Defence(4, 4, 2, 4)), "B")
        self.assertEqual(winner(Defence(8, 3, 2, 2), Defence(8, 3, 2, 4)), "A")
        self.assertIsNone(winner(Defence(8, 2, 2, 2), Defence(8, 4, 4, 4)))  # both found everything
        self.assertIsNone(winner(Defence(8, 3, 1, 3), Defence(8, 3, 1, 3)))
        self.assertIsNone(winner(Defence(4, 4, 0, 4), Defence(4, 4, 3, 3), tiebreak=False))
        self.assertEqual(decided_by(Defence(8, 4, 4, 4), Defence(8, 4, 3, 4)), "left")
        self.assertEqual(decided_by(Defence(8, 2, 2, 3), Defence(8, 4, 4, 4)), "clean")
        self.assertEqual(decided_by(Defence(8, 4, 4, 4), Defence(8, 4, 4, 4)), "draw")

    def test_holding_back_as_attacker_cannot_win_the_tiebreak(self):
        a = Defence(8, 4, 4, 4)  # as round-1 defender, A found all four flips
        # A flips nothing in round 2. Under "more poison found" A won 4-0; now it is a draw at best.
        self.assertIsNone(winner(a, Defence(8, 0, 0, 0)))
        # Only poison the opponent misses can win the tiebreak for the attacker.
        self.assertEqual(winner(a, Defence(8, 4, 3, 4)), "A")

    def test_documented_draw_rates_reproduce(self):
        rates = {k: (v["matches"], round(100 * v["draws_by_score"], 1), round(100 * v["draws_after_tiebreaks"], 1))
                 for k, v in match.report().items()}
        self.assertEqual(rates, {"seeded kit · conflict": (490, 50.6, 10.2), "seeded kit · random": (490, 66.3, 13.5),
                                 "fixed edition · conflict": (324, 52.2, 11.1),
                                 "fixed edition · random": (324, 82.4, 18.2)})

    def test_terminal_match_reports_tiebreaks(self):
        # Seed 19, second case: A finds 2 of 3 flips as defender, then flips nothing as attacker.
        # B leaves no poison and wins; under "more poison found" A would have won by holding back.
        cases = [("\n" * 8, "Draw."),
                 ("\n".join(("", "C22 C03 C23", "", "C05", "C10", "C03", "C22", "", "", "", "")) + "\n",
                  "Player B wins.")]
        for responses, outcome in cases:
            with self.subTest(outcome=outcome):
                result = subprocess.run([sys.executable, "-m", "poisoned_dataset", "play", "--seed", "19"],
                                        input=responses, text=True, capture_output=True, check=True)
                self.assertIn("Tied on score.", result.stdout)
                self.assertIn(outcome, result.stdout)
        self.assertIn("Poison left: A 1, B 0. Clean audits: A 2, B 0.", result.stdout)


if __name__ == "__main__":
    unittest.main()
