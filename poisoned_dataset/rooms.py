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

from . import decks
from .core import (Card, LABELS, RULES, accuracy, errors, fit, flip_labels,
                   generate, predict, rng_for, test_deck)
from .match import AUDITS, FLIPS, Defence, winner

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

    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS rooms "
                       "(code TEXT PRIMARY KEY, state TEXT NOT NULL)")

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

    def _save(self, db, state):
        state["revision"] += 1
        db.execute("UPDATE rooms SET state = ? WHERE code = ?", (json.dumps(state), state["code"]))

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
            db.execute("INSERT INTO rooms VALUES (?, ?)", (code, json.dumps(state)))
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
            self._save(db, state)
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
                               for k in ("reasoning", "decisions", "improvement"))):
                    raise RoomError("Supply ratings from 1 to 5 and notes of at most 3,000 characters.")
                state["feedback"][seat] = {k: payload[k] for k in
                                          ("clarity", "enjoyment", "reasoning", "decisions", "improvement")}
                state["feedback"][seat]["at"] = now()
            else:
                raise RoomError("Unknown game action.")
            self._save(db, state)

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
        return record
