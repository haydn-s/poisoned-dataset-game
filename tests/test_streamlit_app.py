"""End-to-end UI checks with two independent Streamlit sessions and one store."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Install requirements.txt for UI tests")
class StreamlitTests(unittest.TestCase):
    def setUp(self):
        from streamlit.testing.v1 import AppTest
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"POISONED_DATASET_DB": str(Path(self.tmp.name) / "ui.sqlite3")})
        env.start()
        self.addCleanup(env.stop)
        app = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
        self.a = AppTest.from_file(app, default_timeout=15).run()
        self.b = AppTest.from_file(app, default_timeout=15).run()

    def click(self, app, label):
        next(b for b in app.button if b.label == label).click().run()
        self.assertEqual(list(app.exception), [])

    def test_two_browsers_complete_match_and_save_feedback(self):
        self.assertEqual(list(self.a.exception), [])
        self.a.text_input[0].set_value("Alice")
        self.click(self.a, "Create room")
        code = self.a.session_state["credentials"][0]
        self.b.text_input[1].set_value(code)
        self.b.text_input(key="join_alias").set_value("Bob")
        self.click(self.b, "Join room")
        self.a.run()
        self.click(self.a, "Start two-round match")
        self.assertEqual(len(self.a.multiselect), 0)
        self.assertFalse(any("secret truth" in x.value for x in self.a.info))
        self.b.run()
        self.b.multiselect[0].set_value([0, 1]).run()
        self.click(self.b, "Commit attack · 2/4 flips")
        self.a.run()
        self.click(self.a, "Spend 1 token · audit card")
        lock = next(b.label for b in self.a.button if b.label.startswith("Lock "))
        self.click(self.a, lock)
        self.click(self.a, "Ready · switch roles for round 2")
        self.b.run()
        self.click(self.b, "Ready · switch roles for round 2")
        self.a.run()
        self.click(self.a, "Commit attack · 0/4 flips")
        self.b.run()
        lock = next(b.label for b in self.b.button if b.label.startswith("Lock "))
        self.click(self.b, lock)
        self.assertTrue(any("wins the match" in t.value or "draw" in t.value for t in self.b.title))
        self.click(self.b, "Save feedback")
        self.assertTrue(any("Feedback saved: Bob" in m.value for m in self.b.markdown))
        self.a.run()
        self.assertEqual(list(self.a.exception), [])

    def test_reload_can_reconnect_without_creating_another_player(self):
        self.a.text_input[0].set_value("Alice")
        self.click(self.a, "Create room")
        code, token = self.a.session_state["credentials"]
        self.b.text_input(key="resume_room").set_value(code)
        next(t for t in self.b.text_input if t.label == "Private reconnect code").set_value(token)
        self.click(self.b, "Return to my seat")
        self.assertEqual(tuple(self.b.session_state["credentials"]), (code, token))
        self.assertTrue(next(b for b in self.b.button if b.label == "Start two-round match").disabled)


if __name__ == "__main__":
    unittest.main()
