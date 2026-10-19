import unittest
from random import Random

from poisoned_dataset.core import (ATTACKS, DEFENSES, REGIMES, Card, accuracy,
                                   audit, conflict_scores, errors, fit,
                                   flip_labels, generate, poison, predict,
                                   rng_for, test_deck)


class LearningTests(unittest.TestCase):
    def test_manual_rulebook_example(self):
        cards = (Card("C01", 1, 0, 0), Card("C02", 0, 1, 0),
                 Card("C03", 1, 1, 1), Card("C04", 0, 0, 1))
        self.assertEqual(errors(cards, (1, 0, 1, 0)), {"red": 0, "round": 2, "striped": 2})
        self.assertEqual(fit(cards, (1, 0, 1, 0)), "red")

    def test_public_tie_order(self):
        cards = (Card("C01", 1, 1, 1), Card("C02", 0, 0, 0))
        self.assertEqual(fit(cards, (1, 0)), "red")
        cards = (Card("C01", 1, 0, 0),)
        self.assertEqual(fit(cards, (0,)), "round")

    def test_exact_deployment_and_distinct_record_ids(self):
        deck = test_deck()
        self.assertEqual(len({c.features for c in deck}), 8)
        self.assertTrue(all(c.id.startswith("T") for c in deck))
        self.assertEqual(accuracy("red", "red"), 1.0)
        self.assertEqual(accuracy("red", "round"), 0.5)
        self.assertEqual(accuracy("round", "striped"), 0.5)
        self.assertEqual(len(set(deck).intersection(generate(19).cards)), 0)

    def test_generation_is_repeatable_without_mutable_shared_cards(self):
        a, b = generate(19), generate(19)
        self.assertEqual(a, b)
        self.assertIsNot(a.cards[0], b.cards[0])
        self.assertEqual(generate(19, regime="correlated").true_rule, a.true_rule)


class AttackAndAuditTests(unittest.TestCase):
    def test_attack_budgets_clean_label_consistency_and_input_preservation(self):
        for regime in REGIMES:
            for seed in range(10):
                s = generate(seed, regime=regime)
                before = s.clean_labels
                for kind in ATTACKS:
                    for budget in (0, 4, 24):
                        indices = poison(s.cards, s.clean_labels, budget, kind,
                                         rng_for(seed, kind, budget), s.true_rule)
                        changed = flip_labels(s.clean_labels, indices)
                        self.assertEqual(len(set(indices)), len(indices))
                        self.assertLessEqual(len(indices), budget)
                        self.assertEqual(sum(a != b for a, b in zip(changed, before)), len(indices))
                        if kind == "random":
                            self.assertEqual(len(indices), budget)
                self.assertEqual(s.clean_labels, before)
                self.assertEqual(s.clean_labels, tuple(predict(s.true_rule, c) for c in s.cards))

    def test_directed_attack_respects_known_truth_when_clean_rules_tie(self):
        # Red and round are indistinguishable in training; the real rule is round.
        cards = (Card("C01", 1, 1, 0), Card("C02", 0, 0, 1))
        indices = poison(cards, (1, 0), 2, "directed", Random(0), "round")
        self.assertEqual(indices, ())  # Closest false rival is red, with no disagreements.

    def test_oracle_calls_are_paid_distinct_and_not_made_by_baseline(self):
        s = generate(19)
        supplied = flip_labels(s.clean_labels, (0, 1, 2))
        for defense in DEFENSES:
            calls = []

            def oracle(i):
                calls.append(i)
                return s.clean_labels[i]

            result = audit(s.cards, supplied, 4, defense, oracle, Random(4))
            self.assertEqual(len(calls), 0 if defense == "none" else 4)
            self.assertEqual(len(set(calls)), len(calls))
            self.assertEqual(tuple(x.index for x in result.audits), tuple(calls))
            for i in range(24):
                self.assertEqual(result.labels[i], s.clean_labels[i] if i in calls else supplied[i])
            self.assertEqual(supplied, flip_labels(s.clean_labels, (0, 1, 2)))

    def test_minority_correct_labels_can_make_conflict_worse_than_random(self):
        cards = tuple(Card(f"C{i}", 1, 0, 0) for i in range(3))
        labels = (1, 1, 0)  # First two are poisoned; the minority label is correct.
        oracle = (0, 0, 0).__getitem__
        targeted = audit(cards, labels, 1, "conflict", oracle, Random(1))
        random = audit(cards, labels, 1, "random", oracle, Random(1))
        self.assertEqual(targeted.audits[0].index, 2)
        self.assertEqual(targeted.audits[0].before, targeted.audits[0].after)
        self.assertEqual(accuracy(fit(cards, targeted.labels), "round"), 0.5)
        self.assertEqual(accuracy(fit(cards, random.labels), "round"), 1.0)
        scores = conflict_scores(cards, labels, {2})
        self.assertTrue(all(score[0] == 1 for score in scores.values()))

    def test_consistently_poisoned_group_has_no_visible_conflict(self):
        cards = (Card("C01", 0, 0, 0), Card("C02", 0, 0, 0),
                 Card("C03", 1, 0, 0), Card("C04", 1, 0, 0))
        clean, supplied = (0, 0, 0, 0), (0, 0, 1, 1)
        self.assertEqual(set(conflict_scores(cards, supplied, set()).values()), {(0, 0.0)})
        self.assertEqual(fit(cards, supplied), "red")
        result = audit(cards, supplied, 4, "conflict", clean.__getitem__, Random(1))
        self.assertEqual(result.labels, clean)
        self.assertEqual(fit(cards, result.labels), "round")

    def test_zero_budget_and_full_audit_controls(self):
        s = generate(19)
        supplied = flip_labels(s.clean_labels, (0, 2, 4, 6))

        def forbidden(_):
            self.fail("A zero-budget defense queried the reference")

        for defense in DEFENSES:
            self.assertEqual(audit(s.cards, supplied, 0, defense, forbidden, Random(1)).labels, supplied)
        for defense in ("random", "conflict"):
            result = audit(s.cards, supplied, 24, defense, s.clean_labels.__getitem__, Random(1))
            self.assertEqual(result.labels, s.clean_labels)

    def test_reject_invalid_budgets_and_repeat_flips(self):
        s = generate(0)
        with self.assertRaises(ValueError):
            flip_labels(s.clean_labels, (0, 0))
        for budget in (-1, 25):
            with self.assertRaises(ValueError):
                poison(s.cards, s.clean_labels, budget, "random", Random(1), s.true_rule)
            with self.assertRaises(ValueError):
                audit(s.cards, s.clean_labels, budget, "random", s.clean_labels.__getitem__, Random(1))


if __name__ == "__main__":
    unittest.main()
