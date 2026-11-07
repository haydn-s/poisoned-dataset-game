from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest

from poisoned_dataset.core import Card, errors, fit, predict
from poisoned_dataset.rooms import RoomError, RoomStore, new_round


class RoomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "rooms.sqlite3"
        self.store = RoomStore(self.path)
        self.code, self.a = self.store.create("Alice")
        _, self.b = self.store.join(self.code, "Bob")

    def view(self, token=None):
        return self.store.view(self.code, token or self.a)

    def act(self, token, action, payload=None):
        self.store.act(self.code, token, self.view(token)["revision"], action, payload)

    def start(self):
        self.act(self.a, "start")

    def round_two(self):
        self.act(self.a, "ready")
        self.act(self.b, "ready")

    def complete(self):
        self.start()
        self.act(self.b, "attack", [])
        self.act(self.a, "lock")
        self.round_two()
        self.act(self.a, "attack", [])
        self.act(self.b, "lock")

    def test_defender_never_receives_clean_labels_or_seeds_before_reveal(self):
        self.start()
        defender = self.view()
        for field in ("labels", "clean", "truth", "flips", "rule", "errors"):
            self.assertNotIn(field, defender["round"])
        for field in ("seed", "credential", "test_deck"):
            self.assertNotIn(field, json.dumps(defender))
        self.assertEqual(defender["history"], [])
        self.assertIn("truth", self.view(self.b)["round"])
        self.act(self.b, "attack", [0, 2])
        defender = self.view()
        for field in ("clean", "truth", "flips", "supplied"):
            self.assertNotIn(field, defender["round"])
        self.assertEqual(len(defender["round"]["labels"]), 24)
        with self.assertRaises(RoomError):
            self.store.export(self.code, self.a)

    def test_authorization_and_state_machine(self):
        for token in ("", "made-up-token"):
            with self.assertRaises(RoomError):
                self.store.view(self.code, token)
        with self.assertRaises(RoomError):
            self.act(self.b, "start")
        with self.assertRaises(RoomError):
            self.act(self.a, "lock")
        self.start()
        with self.assertRaises(RoomError):
            self.act(self.a, "attack", [])
        self.act(self.b, "attack", [])
        for action, payload in (("attack", []), ("audit", 0), ("lock", None)):
            with self.assertRaises(RoomError):
                self.act(self.b, action, payload)
        with self.assertRaises(RoomError):
            self.act(self.a, "ready")

    def test_attack_limits_are_atomic(self):
        self.start()
        for invalid in ([0, 0], list(range(5)), [-1], [24], [True], [1.0], "0", None):
            before = self.view(self.b)
            with self.assertRaises(RoomError):
                self.act(self.b, "attack", invalid)
            self.assertEqual(self.view(self.b), before)
        self.act(self.b, "attack", [0, 1, 2, 3])
        self.assertEqual(self.view()["phase"], "audit")

    def test_audit_repairs_only_one_copy_and_uses_existing_learner(self):
        self.start()
        r = self.view(self.b)["round"]
        cards = [Card(**c) for c in r["cards"]]
        i, j = next((i, j) for i in range(24) for j in range(i + 1, 24)
                    if cards[i].features == cards[j].features)
        self.act(self.b, "attack", [i, j])
        self.act(self.a, "audit", i)
        v = self.view()["round"]
        self.assertEqual(v["labels"][i], r["clean"][i])
        self.assertNotEqual(v["labels"][j], r["clean"][j])
        self.assertEqual(v["errors"], errors(cards, v["labels"]))
        self.assertEqual(v["rule"], fit(cards, v["labels"]))
        with self.assertRaises(RoomError):
            self.act(self.a, "audit", i)
        others = [k for k in range(24) if k not in (i, j)]
        for k in others[:3]:
            self.act(self.a, "audit", k)
        with self.assertRaises(RoomError):
            self.act(self.a, "audit", j)
        self.act(self.a, "lock")
        result = self.view()["round"]["result"]
        self.assertEqual({k: result[k] for k in ("found", "spent", "left", "clean")},
                         {"found": 1, "spent": 4, "left": 1, "clean": 3})

    def test_tiebreak_uses_poison_left_then_clean_audits(self):
        self.start()
        self.act(self.b, "attack", [0])  # one flip never switches a fixed deck's rule
        self.act(self.a, "audit", 0)
        self.act(self.a, "audit", 1)
        self.act(self.a, "lock")
        self.round_two()
        self.act(self.a, "attack", [])  # holding back as the round-2 attacker
        self.act(self.b, "lock")
        v = self.view()
        self.assertEqual([r["result"]["points"] for r in v["history"]], [8, 8])
        # Neither defender left poison. A's clean audit decides it, where "more poison found" gave A the win.
        self.assertEqual(v["outcome"], {"winner": "B", "decided_by": "clean"})
        with self.store.connection() as db:  # a room finished before left/clean were stored
            state = json.loads(db.execute("SELECT state FROM rooms WHERE code = ?", (self.code,)).fetchone()[0])
            for round_ in state["rounds"]:
                del round_["result"]["left"], round_["result"]["clean"]
            db.execute("UPDATE rooms SET state = ? WHERE code = ?", (json.dumps(state), self.code))
        self.assertEqual(self.view()["outcome"], v["outcome"])

    def test_two_round_match_roles_readiness_and_credential_free_export(self):
        self.start()
        self.act(self.b, "attack", [])
        self.act(self.a, "lock")
        first = self.view()["round"]
        self.act(self.a, "ready")
        self.assertEqual(self.view()["phase"], "reveal")
        with self.assertRaises(RoomError):
            self.act(self.a, "ready")
        self.act(self.b, "ready")
        second = self.view(self.a)["round"]
        self.assertEqual((second["attacker"], second["defender"]), ("A", "B"))
        self.assertNotEqual(first["deck"], second["deck"])
        self.assertNotIn("truth", self.view(self.b)["round"])
        self.act(self.a, "attack", [])
        self.act(self.b, "lock")
        v = self.view()
        self.assertEqual(v["phase"], "complete")
        self.assertEqual(v["outcome"], {"winner": None, "decided_by": "draw"})
        record = self.store.export(self.code, self.a)
        self.assertEqual([r["result"]["points"] for r in record["rounds"]], [8, 8])
        for secret in (self.a, self.b, "credential"):
            self.assertNotIn(secret, json.dumps(record))
        for r in record["rounds"]:
            self.assertTrue(all(predict(r["truth"], Card(**c)) == y
                                for c, y in zip(r["cards"], r["clean"])))
        self.assertEqual(len(record["test_deck"]), 8)

    def test_simultaneous_audits_spend_only_one_token(self):
        self.start()
        self.act(self.b, "attack", [0])
        rev = self.view()["revision"]
        def check(i):
            try:
                self.store.act(self.code, self.a, rev, "audit", i)
                return "ok"
            except RoomError:
                return "stale"
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(check, [0, 1])), ["ok", "stale"])
        self.assertEqual(len(self.view()["round"]["audits"]), 1)

    def test_room_capacity_is_atomic_and_rooms_are_isolated(self):
        code, token = self.store.create("Other host")
        def join(name):
            try:
                self.store.join(code, name)
                return "ok"
            except RoomError:
                return "full"
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(join, ["One", "Two"])), ["ok", "full"])
        with self.assertRaises(RoomError):
            self.store.view(code, self.a)
        self.start()
        self.assertEqual(self.store.view(code, token)["phase"], "lobby")

    def test_restart_and_reconnect_preserve_state(self):
        self.start()
        self.act(self.b, "attack", [3])
        self.act(self.a, "audit", 3)
        restarted = RoomStore(self.path)
        self.assertEqual(restarted.view(self.code.lower(), self.a), self.view())
        with self.assertRaises(RoomError):
            restarted.join(self.code, "Replacement")

    def test_feedback_saved_only_after_match_and_included_in_export(self):
        feedback = {"clarity": 4, "enjoyment": 5, "reasoning": "Fewest errors.",
                    "decisions": "Checking duplicates.", "improvement": "More rounds."}
        with self.assertRaises(RoomError):
            self.act(self.a, "feedback", feedback)
        self.complete()
        self.act(self.a, "feedback", feedback)
        self.assertEqual(self.view()["feedback"]["clarity"], 4)
        self.assertEqual(self.view(self.b)["feedback"], {})
        self.assertEqual(self.store.export(self.code, self.b)["feedback"]["A"]["enjoyment"], 5)
        for change in ({"clarity": 6}, {"enjoyment": True}, {"reasoning": "x" * 3001}):
            with self.assertRaises(RoomError):
                self.act(self.a, "feedback", feedback | change)

    def test_fresh_decks_reproduce_generated_kit(self):
        from poisoned_dataset.core import generate
        for number in range(2):
            round_ = new_round(12345, number, "fresh")
            original = generate(12345 + number, regime="correlated")
            self.assertEqual(tuple(Card(**c) for c in round_["cards"]), original.cards)
            self.assertEqual(round_["truth"], original.true_rule)
            self.assertEqual(round_["clean"], list(original.clean_labels))

    def test_names_and_editions(self):
        for name in ("", " ", "x" * 33):
            with self.assertRaises(RoomError):
                self.store.create(name)
        with self.assertRaises(RoomError):
            self.store.create("Name", "unknown")
        code, _ = self.store.create("Name")
        with self.assertRaises(RoomError):
            self.store.join(code, "name")


if __name__ == "__main__":
    unittest.main()
