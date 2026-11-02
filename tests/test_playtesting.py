from hashlib import sha1
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from poisoned_dataset.playtesting import ArchiveConfig, ArchiveError, ArchiveSync, GitHubArchive
from poisoned_dataset.rooms import RoomError, RoomStore


class LoggingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = RoomStore(Path(self.tmp.name) / "rooms.db")
        self.code, self.a = self.store.create("Alice")
        _, self.b = self.store.join(self.code, "Bob")

    def act(self, token, action, payload=None):
        self.store.act(self.code, token, self.store.view(self.code, token)["revision"], action, payload)

    def log(self):
        return json.loads(next(self.store.log_dir.rglob("game.json")).read_text())

    def complete(self):
        self.act(self.a, "start")
        self.act(self.b, "attack", [0])
        self.act(self.a, "audit", 0)
        self.act(self.a, "lock")
        self.act(self.a, "ready")
        self.act(self.b, "ready")
        self.act(self.a, "attack", [])
        self.act(self.b, "lock")

    def feedback(self, text):
        return dict(review=text, clarity=4, enjoyment=5, reasoning="Fewest errors.",
                    decisions="An audit mattered.", improvement="More cards.")

    def test_actions_are_logged_and_rejected_actions_leave_no_event(self):
        self.act(self.a, "start")
        self.act(self.b, "attack", [0])
        before = self.log()
        with self.assertRaises(RoomError):
            self.act(self.b, "audit", 0)
        self.assertEqual(self.log(), before)
        self.act(self.a, "audit", 0)
        record = self.log()
        self.assertEqual([e["action"] for e in record["events"]], ["create", "join", "start", "attack", "audit"])
        self.assertEqual([e["revision"] for e in record["events"]], list(range(5)))
        self.assertEqual(record["events"][-1]["audit"]["index"], 0)
        self.assertTrue(all(e["at"] for e in record["events"]))
        for secret in (self.a, self.b, "credential"):
            self.assertNotIn(secret, json.dumps(record))

    def test_public_in_progress_logs_do_not_spoil_either_round(self):
        self.act(self.a, "start")
        first = self.log()["rounds"][0]
        for key in ("truth", "seed", "clean", "labels", "flips"):
            self.assertNotIn(key, first)
        self.act(self.b, "attack", [0, 1])
        during = self.log()
        for key in ("truth", "clean", "flips", "supplied"):
            self.assertNotIn(key, during["rounds"][0])
        self.assertNotIn("seed", during)
        self.assertNotIn("payload", during["events"][-1])
        self.act(self.a, "lock")
        self.assertEqual(self.log()["rounds"][0]["flips"], [0, 1])
        self.assertNotIn("seed", self.log())
        self.act(self.a, "ready")
        self.act(self.b, "ready")
        second = self.log()
        self.assertNotIn("truth", second["rounds"][1])
        self.assertNotIn("seed", second)

    def test_complete_game_and_two_reviews_have_separate_stable_files(self):
        self.complete()
        self.act(self.a, "feedback", self.feedback("Great game"))
        self.act(self.b, "feedback", self.feedback("Interesting choices"))
        self.act(self.a, "feedback", self.feedback("Updated review"))
        files = list(self.store.log_dir.rglob("*.json"))
        self.assertEqual(len(files), 3)
        reviews = {p.stem: json.loads(p.read_text()) for p in files if p.parent.name == "reviews"}
        self.assertEqual(reviews["A"]["review"], "Updated review")
        self.assertEqual(reviews["B"]["review"], "Interesting choices")
        game = self.log()
        self.assertIn("seed", game)
        self.assertIn("outcome", game)
        self.assertEqual(len(game["rounds"]), 2)
        self.assertEqual(len(self.store.pending_uploads()), 3)
        self.assertEqual(self.store.logging_status(self.code, self.a)["local_pending"], 0)
        self.assertEqual(self.store.export(self.code, self.a)["events"], game["events"])

    def test_local_write_failure_retains_work_and_restart_materializes_it(self):
        with patch.object(Path, "write_text", side_effect=OSError("disk not available")):
            self.act(self.a, "start")
        self.assertEqual(self.store.view(self.code, self.a)["phase"], "attack")
        self.assertEqual(self.store.logging_status(self.code, self.a)["local_pending"], 1)
        restarted = RoomStore(self.store.path)
        self.assertEqual(restarted.logging_status(self.code, self.a)["local_pending"], 0)
        self.assertEqual(self.log()["phase"], "attack")

    def test_upload_ack_cannot_discard_a_newer_action(self):
        in_flight = self.store.pending_uploads()[0]
        self.act(self.a, "start")
        self.store.upload_succeeded(in_flight)
        self.assertEqual(len(self.store.pending_uploads()), 1)
        current = self.store.pending_uploads()[0]
        self.assertNotEqual(current["digest"], in_flight["digest"])
        self.store.upload_succeeded(current)
        self.assertEqual(self.store.pending_uploads(), [])

    def test_sync_failure_queues_retry_and_preserves_files(self):
        class Unavailable:
            def write(self, path, payload):
                raise ArchiveError("GitHub HTTP 401. Check the archive token.")
        sync = ArchiveSync(self.store, ArchiveConfig(token="private-test-token"), Unavailable())
        sync.flush()
        self.assertEqual(self.store.pending_uploads(), [])  # Backoff, not deletion.
        status = self.store.logging_status(self.code, self.a)
        self.assertEqual(status["remote_pending"], 1)
        self.assertIn("401", status["error"])
        self.assertTrue(next(self.store.log_dir.rglob("game.json")).exists())
        with patch("poisoned_dataset.rooms.time.time", return_value=10 ** 12):
            pending = self.store.pending_uploads()
        self.assertEqual(len(pending), 1)
        class Available:
            def write(self, path, payload):
                pass
        with patch("poisoned_dataset.rooms.time.time", return_value=10 ** 12):
            ArchiveSync(self.store, ArchiveConfig(token="test"), Available()).flush()
        self.assertEqual(self.store.logging_status(self.code, self.a)["remote_pending"], 0)

    def test_unconfigured_sync_never_calls_github(self):
        class Forbidden:
            def write(self, path, payload):
                raise AssertionError("No token should mean no network request")
        ArchiveSync(self.store, ArchiveConfig(), Forbidden()).flush()
        self.assertEqual(len(self.store.pending_uploads()), 1)

    def test_unique_ids_survive_room_code_reuse(self):
        first = self.log()["match_id"]
        other, _ = self.store.create("Another")
        games = [json.loads(p.read_text()) for p in self.store.log_dir.rglob("game.json")]
        self.assertEqual(len({g["match_id"] for g in games}), 2)
        self.assertTrue(any(g["match_id"] == first for g in games))


class Response(BytesIO):
    def __init__(self, data, url):
        super().__init__(json.dumps(data).encode())
        self.url = url

    def geturl(self):
        return self.url


class GitHubTests(unittest.TestCase):
    def test_new_file_is_created_without_a_sha(self):
        writes = []
        def opener(request, timeout):
            if request.method == "GET":
                raise HTTPError(request.full_url, 404, "not found", {}, None)
            writes.append(json.loads(request.data))
            return Response({}, request.full_url)
        GitHubArchive(ArchiveConfig(token="test"), opener).write("playtests/date/id/game.json", "{}")
        self.assertEqual(len(writes), 1)
        self.assertNotIn("sha", writes[0])
        self.assertEqual(writes[0]["branch"], "play-testing")

    def test_writer_creates_and_updates_only_the_data_branch(self):
        calls = []
        def opener(request, timeout):
            calls.append(request)
            self.assertEqual(timeout, 10)
            if request.method == "GET":
                return Response({"sha": "previous-version"}, request.full_url)
            return Response({}, request.full_url)
        config = ArchiveConfig(token="never-print-this")
        GitHubArchive(config, opener).write("playtests/date/id/game.json", '{"revision": 2}')
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].full_url.endswith("?ref=play-testing"))
        body = json.loads(calls[1].data)
        self.assertEqual(body["branch"], "play-testing")
        self.assertEqual(body["sha"], "previous-version")
        self.assertNotIn(config.token, repr(config))
        self.assertNotIn(config.token, json.dumps(body))

    def test_lost_response_retry_does_not_create_another_commit(self):
        content = '{"revision": 2}\n'
        expected = sha1(f"blob {len(content)}\0".encode() + content.encode()).hexdigest()
        calls = []
        def opener(request, timeout):
            calls.append(request.method)
            return Response({"sha": expected}, request.full_url)
        GitHubArchive(ArchiveConfig(token="test"), opener).write("playtests/date/id/game.json", content)
        self.assertEqual(calls, ["GET"])

    def test_concurrent_update_rereads_sha_before_retry(self):
        puts = []
        def opener(request, timeout):
            if request.method == "GET":
                return Response({"sha": f"revision-{len(puts)}"}, request.full_url)
            puts.append(json.loads(request.data))
            if len(puts) == 1:
                raise HTTPError(request.full_url, 409, "conflict", {}, None)
            return Response({}, request.full_url)
        GitHubArchive(ArchiveConfig(token="test"), opener).write("playtests/date/id/game.json", "{}")
        self.assertEqual([p["sha"] for p in puts], ["revision-0", "revision-1"])

    def test_auth_errors_are_safe_and_paths_are_validated(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 401, "a body containing secret data", {}, None)
        writer = GitHubArchive(ArchiveConfig(token="private"), opener)
        with self.assertRaisesRegex(ArchiveError, "HTTP 401") as caught:
            writer.write("playtests/date/id/game.json", "{}")
        self.assertNotIn("secret", str(caught.exception))
        with self.assertRaises(ArchiveError):
            writer.write("README.md", "{}")
        for directory in ("../main", ".github", "/playtests", "playtests/../main", ""):
            with self.assertRaises(ValueError):
                ArchiveConfig(directory=directory)


if __name__ == "__main__":
    unittest.main()
