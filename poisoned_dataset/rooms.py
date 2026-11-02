"""Transactional multiplayer rooms, independent of Streamlit.

Only ``view`` crosses the UI boundary. It constructs a role-specific projection;
the database's private round state and credential hashes never go to a browser.
"""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import secrets
import sqlite3
import os
import time
from uuid import uuid4

from . import decks
from .core import (Card, LABELS, RULES, accuracy, errors, fit, flip_labels,
                   generate, predict, rng_for, test_deck)
from .match import AUDITS, FLIPS, Defence, winner
from .playtesting import game_record, target_directory

VERSION = "digital-0.1"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class RoomError(ValueError):
    """An expected, safe-to-display failure of a player action."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(token):
    return sha256(token.encode()).hexdigest()


def alias(value):
    value = " ".join(value.split())
    if not 1 <= len(value) <= 32 or not value.isprintable():
        raise RoomError("Use a player alias between 1 and 32 characters.")
    return value


def cards_of(round_):
    return tuple(Card(**c) for c in round_["cards"])


def new_round(seed, number, edition):
    if edition == "fixed":
        letter = rng_for(seed, "digital", "decks").sample(list(decks.LETTERS), 2)[number]
        cards = decks.deck(letter)
        truth = rng_for(seed, "digital", "truth", number).choice(RULES)
        deck_name = f"Deck {letter}"
    else:
        scenario = generate(seed + number, regime="correlated")
        cards, truth, deck_name = scenario.cards, scenario.true_rule, "Fresh deck"
    clean = [predict(truth, c) for c in cards]
    return {"number": number + 1, "defender": "A" if number == 0 else "B",
            "attacker": "B" if number == 0 else "A", "deck": deck_name,
            "cards": [asdict(c) for c in cards], "truth": truth, "clean": clean,
            "labels": clean[:], "flips": [], "audits": [], "ready": [],
            "started_at": now()}


def result_of(round_):
    cards = cards_of(round_)
    rule = fit(cards, round_["labels"])
    return {"defender": round_["defender"], "rule": rule,
            "points": round(8 * accuracy(rule, round_["truth"])),
            "found": sum(a["before"] != a["after"] for a in round_["audits"]),
            "spent": len(round_["audits"])}


def outcome_of(rounds):
    results = [r["result"] for r in rounds]
    a, b = (Defence(**{k: r[k] for k in ("points", "found", "spent")}) for r in results)
    decided = next((name for name in ("points", "found", "spent")
                    if getattr(a, name) != getattr(b, name)), "draw")
    return {"winner": winner(a, b), "decided_by": decided}


class RoomStore:
    """One SQLite file shared by all rooms and browser sessions on one host.

    Each write takes a transaction lock and checks a revision. Stale tabs and
    double clicks cannot spend a second token or commit a second attack.
    """

    def __init__(self, path, log_dir=None, archive_directory="playtests"):
        self.path = Path(path).expanduser().resolve()
        self.log_dir = Path(log_dir).expanduser().resolve() if log_dir else self.path.parent / "playtest-archive"
        self.archive_directory = target_directory(archive_directory)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS rooms "
                       "(code TEXT PRIMARY KEY, state TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS playtest_outbox ("
                       "path TEXT PRIMARY KEY, room TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT NOT NULL, "
                       "local_digest TEXT, sent_digest TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0, "
                       "retry_at REAL NOT NULL DEFAULT 0)")
        self.materialize_logs()

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _load(self, db, code):
        row = db.execute("SELECT state FROM rooms WHERE code = ?", (code.strip().upper(),)).fetchone()
        if row is None:
            raise RoomError("Room not found. Check the room code and the app address.")
        return json.loads(row[0])

    def _save(self, db, state, seat, action):
        state["revision"] += 1
        self._record(db, state, seat, action)
        db.execute("UPDATE rooms SET state = ? WHERE code = ?", (json.dumps(state), state["code"]))

    def _queue(self, db, state, path, record):
        payload = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        fingerprint = sha256(payload.encode()).hexdigest()
        db.execute("INSERT INTO playtest_outbox (path, room, payload, digest) VALUES (?, ?, ?, ?) "
                   "ON CONFLICT(path) DO UPDATE SET payload=excluded.payload, digest=excluded.digest, "
                   "error=NULL, attempts=0, retry_at=0 WHERE playtest_outbox.digest != excluded.digest",
                   (path, state["code"], payload, fingerprint))

    def _record(self, db, state, seat, action):
        # Old rooms acquire logging on their next action; no credentials are
        # backfilled into the public record, and no previous rooms are uploaded.
        state.setdefault("match_id", uuid4().hex)
        state.setdefault("events", [])
        event = {"revision": state["revision"], "at": now(), "actor": seat, "action": action,
                 "phase": state["phase"], "round": len(state["rounds"])}
        if action == "audit":
            event["audit"] = deepcopy(state["rounds"][-1]["audits"][-1])
        # Attack choices stay in the private room state until the round reveal.
        state["events"].append(event)
        folder = f'{self.archive_directory}/{state["created_at"][:10]}/{state["match_id"]}'
        record = game_record(state)
        if state["phase"] == "complete":
            record.update(outcome=outcome_of(state["rounds"]),
                          rules={"priority": list(RULES), "labels": list(LABELS), "regime": "correlated"},
                          test_deck=[asdict(c) for c in test_deck()])
        self._queue(db, state, folder + "/game.json", record)
        if action == "feedback":
            self._queue(db, state, folder + f"/reviews/{seat}.json",
                        {"schema_version": 1, "match_id": state["match_id"], "code": state["code"],
                         "seat": seat, "alias": state["players"][seat]["name"],
                         "revision": state["revision"], **state["feedback"][seat]})

    def materialize_logs(self):
        """Atomically write the latest queued files, serializing competing tabs.

        SQLite remains authoritative if the directory is temporarily unwritable.
        Every action and app rerun retries unfinished local writes.
        """
        try:
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                rows = db.execute("SELECT path, payload, digest FROM playtest_outbox "
                                  "WHERE local_digest IS NULL OR local_digest != digest").fetchall()
                for path, payload, fingerprint in rows:
                    destination = self.log_dir / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary = destination.with_suffix(".json.tmp")
                    temporary.write_text(payload, encoding="utf-8")
                    os.replace(temporary, destination)
                    db.execute("UPDATE playtest_outbox SET local_digest=? WHERE path=?", (fingerprint, path))
        except OSError:
            return  # The durable outbox retains the work for the next attempt.

    def pending_uploads(self):
        with self.connection() as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute(
                "SELECT path, payload, digest, attempts FROM playtest_outbox "
                "WHERE (sent_digest IS NULL OR sent_digest != digest) AND retry_at <= ? "
                "ORDER BY path LIMIT 20", (time.time(),))]

    def upload_succeeded(self, item):
        with self.connection() as db:
            db.execute("UPDATE playtest_outbox SET sent_digest=?, error=NULL, attempts=0, retry_at=0 "
                       "WHERE path=? AND digest=?", (item["digest"], item["path"], item["digest"]))

    def upload_failed(self, item, error):
        with self.connection() as db:
            delay = min(300, 10 * 2 ** min(item["attempts"], 5))
            db.execute("UPDATE playtest_outbox SET error=?, attempts=attempts+1, retry_at=? "
                       "WHERE path=? AND digest=?", (error, time.time() + delay, item["path"], item["digest"]))

    def logging_status(self, code, token):
        with self.connection() as db:
            state = self._load(db, code)
            self._seat(state, token)
            rows = db.execute("SELECT local_digest = digest, sent_digest = digest, error "
                              "FROM playtest_outbox WHERE room=?", (state["code"],)).fetchall()
        return {"files": len(rows), "local_pending": sum(not local for local, _, _ in rows),
                "remote_pending": sum(not sent for _, sent, _ in rows),
                "error": next((error for _, _, error in rows if error), None)}

    def _seat(self, state, token):
        for seat, player in state["players"].items():
            if secrets.compare_digest(player["credential"], digest(token)):
                return seat
        raise RoomError("That reconnect code does not belong to this room.")

    def create(self, name, edition="fixed"):
        name = alias(name)
        if edition not in ("fixed", "fresh"):
            raise RoomError("Choose the fixed or fresh deck edition.")
        token = secrets.token_urlsafe(24)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            while True:
                code = "".join(secrets.choice(ALPHABET) for _ in range(6))
                if not db.execute("SELECT 1 FROM rooms WHERE code = ?", (code,)).fetchone():
                    break
            state = {"version": VERSION, "code": code, "created_at": now(),
                     "revision": 0, "phase": "lobby", "edition": edition,
                     "seed": secrets.randbits(52), "players": {
                         "A": {"name": name, "credential": digest(token)}},
                     "rounds": [], "feedback": {}}
            self._record(db, state, "A", "create")
            db.execute("INSERT INTO rooms VALUES (?, ?)", (code, json.dumps(state)))
        self.materialize_logs()
        return code, token

    def join(self, code, name):
        name = alias(name)
        token = secrets.token_urlsafe(24)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._load(db, code)
            if len(state["players"]) == 2 or state["phase"] != "lobby":
                raise RoomError("This room is full. Use Reconnect to return to your existing seat.")
            if name.casefold() == state["players"]["A"]["name"].casefold():
                raise RoomError("Choose a different alias so the two players are easy to tell apart.")
            state["players"]["B"] = {"name": name, "credential": digest(token)}
            self._save(db, state, "B", "join")
        self.materialize_logs()
        return state["code"], token

    def act(self, code, token, revision, action, payload=None):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._load(db, code)
            seat = self._seat(state, token)
            if revision != state["revision"]:
                raise RoomError("The room changed. Your view has refreshed; review it and try again.")
            phase = state["phase"]
            round_ = state["rounds"][-1] if state["rounds"] else None
            if action == "start":
                if phase != "lobby" or seat != "A" or len(state["players"]) != 2:
                    raise RoomError("The host can start once both players have joined.")
                state["started_at"] = now()
                state["rounds"].append(new_round(state["seed"], 0, state["edition"]))
                state["phase"] = "attack"
            elif action == "attack":
                self._require(phase == "attack" and seat == round_["attacker"])
                if (not isinstance(payload, list) or len(payload) > FLIPS
                        or any(type(i) is not int or not 0 <= i < 24 for i in payload)
                        or len(payload) != len(set(payload))):
                    raise RoomError("Choose up to four distinct training cards.")
                round_["flips"] = sorted(payload)
                round_["labels"] = list(flip_labels(round_["clean"], payload))
                round_["supplied"] = round_["labels"][:]
                round_["attack_rule"] = fit(cards_of(round_), round_["labels"])
                round_["attack_committed_at"] = now()
                state["phase"] = "audit"
            elif action == "audit":
                self._require(phase == "audit" and seat == round_["defender"])
                if len(round_["audits"]) >= AUDITS:
                    raise RoomError("All four audit tokens have been spent. Lock the learned rule.")
                if type(payload) is not int or not 0 <= payload < 24:
                    raise RoomError("Choose a training card from this round.")
                if any(a["index"] == payload for a in round_["audits"]):
                    raise RoomError("That card is already verified. Choose a different card.")
                before = round_["labels"][payload]
                round_["labels"][payload] = round_["clean"][payload]
                round_["audits"].append({"index": payload, "card": round_["cards"][payload]["id"],
                                          "before": before, "after": round_["labels"][payload],
                                          "rule": fit(cards_of(round_), round_["labels"]), "at": now()})
            elif action == "lock":
                self._require(phase == "audit" and seat == round_["defender"])
                round_["result"] = result_of(round_)
                round_["finished_at"] = now()
                state["phase"] = "reveal" if len(state["rounds"]) == 1 else "complete"
                if state["phase"] == "complete":
                    state["finished_at"] = now()
            elif action == "ready":
                self._require(phase == "reveal")
                if seat in round_["ready"]:
                    raise RoomError("You are already ready. Waiting for the other player.")
                round_["ready"].append(seat)
                if len(round_["ready"]) == 2:
                    state["rounds"].append(new_round(state["seed"], 1, state["edition"]))
                    state["phase"] = "attack"
            elif action == "feedback":
                self._require(phase == "complete")
                if (not isinstance(payload, dict)
                        or any(type(payload.get(k)) is not int or not 1 <= payload[k] <= 5
                               for k in ("clarity", "enjoyment"))
                        or any(not isinstance(payload.get(k), str) or len(payload[k]) > 3000
                               for k in ("reasoning", "decisions", "improvement"))
                        or not isinstance(payload.get("review", ""), str) or len(payload.get("review", "")) > 3000):
                    raise RoomError("Supply ratings from 1 to 5 and notes of at most 3,000 characters.")
                state["feedback"][seat] = {k: payload[k] for k in
                                          ("clarity", "enjoyment", "reasoning", "decisions", "improvement")}
                state["feedback"][seat]["at"] = now()
                state["feedback"][seat]["review"] = payload.get("review", "").strip()
            else:
                raise RoomError("Unknown game action.")
            self._save(db, state, seat, action)
        self.materialize_logs()

    @staticmethod
    def _require(condition):
        if not condition:
            raise RoomError("It is not your turn to do that action.")

    def view(self, code, token):
        with self.connection() as db:
            state = self._load(db, code)
        seat = self._seat(state, token)
        view = {k: state[k] for k in ("version", "code", "revision", "phase", "edition")}
        view.update(seat=seat, players={s: p["name"] for s, p in state["players"].items()},
                    history=[deepcopy(r) for r in state["rounds"] if "result" in r])
        if state["rounds"]:
            round_ = state["rounds"][-1]
            active = {k: deepcopy(round_[k]) for k in
                      ("number", "defender", "attacker", "deck", "cards", "ready")}
            phase = state["phase"]
            if phase != "attack" or seat == round_["attacker"]:
                active["labels"] = round_["labels"][:]
                active["errors"] = errors(cards_of(round_), round_["labels"])
                active["rule"] = fit(cards_of(round_), round_["labels"])
                active["audits"] = deepcopy(round_["audits"])
            if seat == round_["attacker"] or phase in ("reveal", "complete"):
                active.update(truth=round_["truth"], clean=round_["clean"][:], flips=round_["flips"][:])
            if "result" in round_:
                active["result"] = deepcopy(round_["result"])
            view["round"] = active
        if state["phase"] == "complete":
            view["outcome"] = outcome_of(state["rounds"])
            view["feedback"] = deepcopy(state["feedback"].get(seat, {}))
            view["feedback_received"] = list(state["feedback"])
        return view

    def export(self, code, token):
        with self.connection() as db:
            state = self._load(db, code)
        self._seat(state, token)
        if state["phase"] != "complete":
            raise RoomError("The playtest record is available after both rounds finish.")
        record = {k: deepcopy(state[k]) for k in
                  ("version", "code", "edition", "seed", "created_at", "started_at", "finished_at",
                   "rounds", "feedback")}
        record["players"] = {s: p["name"] for s, p in state["players"].items()}
        record["budgets"] = {"flips": FLIPS, "audits": AUDITS}
        record["outcome"] = outcome_of(state["rounds"])
        record["test_deck"] = [asdict(c) for c in test_deck()]
        record["rules"] = {"priority": list(RULES), "labels": list(LABELS), "regime": "correlated"}
        record["events"] = deepcopy(state.get("events", []))
        record["match_id"] = state.get("match_id")
        return record
