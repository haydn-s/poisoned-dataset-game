"""Pure game mechanics. Defenses receive labels only through paid oracle calls."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from random import Random
from typing import Callable, Sequence

RULES = ("red", "round", "striped")
REGIMES = ("independent", "correlated")
ATTACKS = ("random", "directed")
DEFENSES = ("none", "random", "conflict")
LABELS = ("RECYCLE", "STORE")


@dataclass(frozen=True)
class Card:
    id: str
    red: int
    round: int
    striped: int

    @property
    def features(self) -> tuple[int, int, int]:
        return self.red, self.round, self.striped

    def describe(self) -> str:
        return ", ".join(("red" if self.red else "blue",
                          "round" if self.round else "square",
                          "striped" if self.striped else "plain"))


@dataclass(frozen=True)
class Scenario:
    seed: int
    regime: str
    true_rule: str
    cards: tuple[Card, ...]
    clean_labels: tuple[int, ...]


@dataclass(frozen=True)
class Audit:
    index: int
    before: int
    after: int
    learned_rule: str


@dataclass(frozen=True)
class AuditResult:
    labels: tuple[int, ...]
    audits: tuple[Audit, ...]


def rng_for(seed: int, *parts: object) -> Random:
    """Separate reproducible streams so a policy cannot change the attack draw."""
    key = repr((seed, parts)).encode("utf-8")
    return Random(int.from_bytes(sha256(key).digest(), "big"))


def predict(rule: str, card: Card) -> int:
    if rule not in RULES:
        raise ValueError(f"Unknown rule: {rule}")
    return getattr(card, rule)


def _validate_labels(cards: Sequence[Card], labels: Sequence[int]) -> None:
    if not cards or len(cards) != len(labels) or any(y not in (0, 1) for y in labels):
        raise ValueError("Supply one binary label per card in a nonempty deck")


def errors(cards: Sequence[Card], labels: Sequence[int]) -> dict[str, int]:
    _validate_labels(cards, labels)
    return {rule: sum(predict(rule, card) != y for card, y in zip(cards, labels))
            for rule in RULES}


def fit(cards: Sequence[Card], labels: Sequence[int]) -> str:
    """Minimum training errors, with public ties red, round, then striped."""
    counts = errors(cards, labels)
    return min(RULES, key=counts.__getitem__)


def generate(seed: int, n: int = 24, regime: str = "independent") -> Scenario:
    if n < 1 or regime not in REGIMES:
        raise ValueError("Use a positive deck size and a known training regime")
    rng = rng_for(seed, "training", regime)
    truth = rng_for(seed, "truth").choice(RULES)
    cards = []
    for i in range(n):
        red = rng.randrange(2)
        if regime == "independent":
            round_, striped = rng.randrange(2), rng.randrange(2)
        else:
            round_ = red if rng.random() < 0.85 else 1 - red
            striped = red if rng.random() < 0.75 else 1 - red
        cards.append(Card(f"C{i + 1:02}", red, round_, striped))
    deck = tuple(cards)
    return Scenario(seed, regime, truth, deck, tuple(predict(truth, c) for c in deck))


def test_deck() -> tuple[Card, ...]:
    """New records covering all eight profiles; never supplied to fit or poison."""
    return tuple(Card(f"T{i + 1:02}", *features)
                 for i, features in enumerate(product((0, 1), repeat=3)))


def accuracy(rule: str, true_rule: str) -> float:
    """Exact accuracy for the specified uniform deployment distribution."""
    deck = test_deck()
    return sum(predict(rule, c) == predict(true_rule, c) for c in deck) / len(deck)


def flip_labels(labels: Sequence[int], indices: Sequence[int]) -> tuple[int, ...]:
    if len(set(indices)) != len(indices) or any(i < 0 or i >= len(labels) for i in indices):
        raise ValueError("Flip each valid card index at most once")
    result = list(labels)
    for i in indices:
        result[i] = 1 - result[i]
    return tuple(result)


def poison(cards: Sequence[Card], clean_labels: Sequence[int], budget: int,
           attack: str, rng: Random, true_rule: str) -> tuple[int, ...]:
    """Return changed indices. No scoring deck, test labels, or audit feedback."""
    _validate_labels(cards, clean_labels)
    if not 0 <= budget <= len(cards) or attack not in ATTACKS:
        raise ValueError("Use a known attack and a budget between zero and deck size")
    if attack == "random":
        return tuple(rng.sample(range(len(cards)), budget))
    # Closest false rule on the clean training set, using the public tie order.
    # The attacker knows the secret true rule, including when training rules tie.
    counts = errors(cards, clean_labels)
    if true_rule not in RULES or counts[true_rule] != 0:
        raise ValueError("Directed attack expects clean labels from a candidate rule")
    target = min((r for r in RULES if r != true_rule), key=counts.__getitem__)
    candidates = [i for i, c in enumerate(cards) if predict(target, c) != clean_labels[i]]
    return tuple(rng.sample(candidates, min(budget, len(candidates))))


def conflict_scores(cards: Sequence[Card], labels: Sequence[int],
                    verified: set[int]) -> dict[int, tuple[int, float]]:
    """Rank contradictions to trusted duplicates, then disagreement fractions."""
    _validate_labels(cards, labels)
    groups: dict[tuple[int, int, int], list[int]] = {}
    for i, card in enumerate(cards):
        groups.setdefault(card.features, []).append(i)
    scores = {}
    for members in groups.values():
        counts = Counter(labels[i] for i in members)
        for i in members:
            if i in verified:
                continue
            trusted_conflict = any(j in verified and labels[j] != labels[i] for j in members)
            fraction = counts[1 - labels[i]] / (len(members) - 1) if len(members) > 1 else 0.0
            scores[i] = int(trusted_conflict), fraction
    return scores


def audit(cards: Sequence[Card], supplied_labels: Sequence[int], budget: int,
          defense: str, oracle: Callable[[int], int], rng: Random) -> AuditResult:
    _validate_labels(cards, supplied_labels)
    if not 0 <= budget <= len(cards) or defense not in DEFENSES:
        raise ValueError("Use a known defense and a budget between zero and deck size")
    current = list(supplied_labels)
    verified: set[int] = set()
    history = []
    for _ in range(0 if defense == "none" else budget):
        if defense == "random":
            choices = [i for i in range(len(cards)) if i not in verified]
        else:
            scores = conflict_scores(cards, current, verified)
            best = max(scores.values())
            choices = [i for i, score in scores.items() if score == best]
        i = rng.choice(choices)
        before = current[i]
        answer = oracle(i)  # The only trusted label access in this policy.
        if answer not in (0, 1):
            raise ValueError("Trusted oracle must return a binary label")
        current[i] = answer
        verified.add(i)
        history.append(Audit(i, before, answer, fit(cards, current)))
    return AuditResult(tuple(current), tuple(history))
