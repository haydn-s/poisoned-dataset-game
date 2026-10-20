import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from poisoned_dataset.components import build
from poisoned_dataset.experiments import run


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class ExperimentTests(unittest.TestCase):
    def test_paired_inputs_controls_export_and_deterministic_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "one", Path(tmp) / "two"
            meta = run(first, [0, 1], 6, [0, 2], [0, 2], 20)
            run(second, [0, 1], 6, [0, 2], [0, 2], 20)
            self.assertEqual(meta["rows"], 96)
            for file in ("runs.csv", "summary.csv", "paired.csv", "comparisons.csv", "scenarios.json"):
                self.assertEqual((first / file).read_bytes(), (second / file).read_bytes())
            rows = read_csv(first / "runs.csv")
            cells = defaultdict(list)
            for row in rows:
                key = tuple(row[k] for k in ("seed", "regime", "attack", "attack_budget", "audit_budget"))
                cells[key].append(row)
                if row["audit_budget"] == "0" or row["defense"] == "none":
                    self.assertEqual(row["final_accuracy"], row["poisoned_accuracy"])
                    self.assertEqual(row["audits_used"], "0")
                    self.assertEqual(row["recovery_per_audit"], "")
                if row["attack_budget"] == "0":
                    self.assertEqual(row["final_accuracy"], row["clean_accuracy"])
                trace = json.loads(row["audit_trace"])
                self.assertEqual(len(trace), int(row["audits_used"]))
            paired = read_csv(first / "paired.csv")
            self.assertEqual(len(paired), 32)
            for row in paired:
                key = tuple(row[k] for k in ("seed", "regime", "attack", "attack_budget", "audit_budget"))
                members = cells[key]
                self.assertEqual(len({r["flipped_cards"] for r in members}), 1)
                self.assertEqual(len({r["poisoned_rule"] for r in members}), 1)
                by_defense = {r["defense"]: float(r["final_accuracy"]) for r in members}
                self.assertEqual(float(row["conflict_minus_random"]), by_defense["conflict"] - by_defense["random"])
            with self.assertRaises(FileExistsError):
                run(first, [0], 6, [0], [0], 0)

    def test_single_seed_has_no_spurious_interval(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "single"
            run(out, [0], 6, [0], [0], 20)
            for row in read_csv(out / "comparisons.csv"):
                self.assertEqual(row["ci95_low"], "")
                self.assertEqual(row["ci95_high"], "")

    def test_printable_kit_separates_public_features_and_secret_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "kit"
            build(out, 19, "correlated")
            public = (out / "public.html").read_text()
            private = (out / "private.html").read_text()
            self.assertNotIn("True rule:", public)
            self.assertIn("True rule:", private)
            counts = {kind: public.count(f'data-kind="{kind}"') for kind in
                      ("training", "test", "rule", "score", "aid", "role")}
            self.assertEqual(counts, {"training": 48, "test": 16, "rule": 3, "score": 1, "aid": 2, "role": 2})
            scenarios = json.loads((out / "scenario.json").read_text())
            self.assertEqual([s["seed"] for s in scenarios], [19, 20])
            self.assertEqual([len(s["cards"]) for s in scenarios], [24, 24])

    def test_terminal_match_completes_both_roles(self):
        cases = ["\n" * 8,
                 "\n".join(("", "C22 C03 C23", "", "C05", "C10", "C03", "C22", "", "", "", "")) + "\n"]
        for responses in cases:
            with self.subTest(responses=responses):
                result = subprocess.run([sys.executable, "-m", "poisoned_dataset", "play", "--seed", "19"],
                                        input=responses, text=True, capture_output=True, check=True)
                self.assertIn("Final defender scores: A 8/8", result.stdout)
                self.assertIn("Defender A:", result.stdout)
                self.assertIn("Defender B:", result.stdout)
                self.assertIn("Match seed for your playtest record: 19", result.stdout)


if __name__ == "__main__":
    unittest.main()
