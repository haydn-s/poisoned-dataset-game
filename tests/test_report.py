import csv
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from poisoned_dataset import report
from poisoned_dataset.experiments import run

RESULTS = Path(__file__).resolve().parent.parent / "results" / "evaluation-v1.0"


class ReportTests(unittest.TestCase):
    def test_small_run_produces_valid_figures_and_consistent_headline(self):
        with tempfile.TemporaryDirectory() as tmp:
            results, out = Path(tmp) / "run", Path(tmp) / "report"
            run(results, list(range(8)), 24, [0, 4], [0, 4], 20)
            numbers = report.build(results, out)
            for svg in out.glob("*.svg"):
                ET.fromstring(svg.read_text())
            self.assertEqual(numbers["n_seeds"], 8)
            paired = numbers["paired_difference"]
            self.assertEqual(paired["wins"] + paired["ties"] + paired["losses"], 8)
            split = numbers["exploratory_by_visible_conflict"]
            self.assertEqual(split["visible"]["switched_seeds"] + split["hidden"]["switched_seeds"],
                             numbers["attack_switched_rule"])
            self.assertEqual(json.loads((out / "headline.json").read_text())["n_seeds"], 8)

    def test_committed_headline_matches_committed_runner_outputs(self):
        headline = json.loads((RESULTS / "report" / "headline.json").read_text())
        with (RESULTS / "comparisons.csv").open(newline="") as stream:
            primary = [r for r in csv.DictReader(stream)
                       if (r["regime"], r["attack"], r["attack_budget"], r["audit_budget"])
                       == ("correlated", "directed", "4", "4")][0]
        self.assertEqual(headline["paired_difference"]["mean"], float(primary["mean_conflict_minus_random"]))
        self.assertEqual(headline["paired_difference"]["ci95"], [float(primary["ci95_low"]), float(primary["ci95_high"])])
        metadata = json.loads((RESULTS / "metadata.json").read_text())
        self.assertEqual((metadata["protocol"], metadata["git"]["dirty"], metadata["rows"]), ("1.0", False, 36000))
        self.assertTrue((RESULTS / "report" / f"trace-seed-{headline['trace_seed']}.svg").is_file())


if __name__ == "__main__":
    unittest.main()
