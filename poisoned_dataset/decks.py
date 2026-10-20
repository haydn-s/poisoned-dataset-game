"""Fixed training decks for the printed edition, chosen from development seeds only.

A printed game cannot regenerate a deck for every match, but it does not need to:
training features are public, and the secret labels follow from a truth card drawn
at the table. A few fixed decks therefore serve every game. They are picked from
development seeds 0-49 by the balance test below; main seeds 1000-1199 are never used.
"""

from .core import RULES, Card, audit, errors, fit, flip_labels, generate, poison, predict, rng_for

DEV_SEEDS = range(50)
REGIME = "correlated"
FLIPS, AUDITS, DRAWS = 4, 4, 40
LETTERS = "ABCD"
CONTESTED = (.15, .85)  # share of attacks a four-token conflict auditor must neither almost always win nor lose
FIXED_DECKS = {"A": 10, "B": 46, "C": 36, "D": 33}  # the output of select(); tests pin the two together


def deck_cards(seed: int, letter: str = "") -> tuple[Card, ...]:
    cards = generate(seed, regime=REGIME).cards
    return tuple(Card(f"{letter}{c.id[1:]}", *c.features) for c in cards) if letter else cards


def clean_labels(cards, rule: str) -> tuple[int, ...]:
    return tuple(predict(rule, c) for c in cards)


def flips_needed(cards, rule: str) -> int | None:
    """Fewest flips that move the learner to the nearest rival, or None if it cannot win."""
    labels = clean_labels(cards, rule)
    counts = errors(cards, labels)
    if fit(cards, labels) != rule:
        return None
    rival = min((r for r in RULES if r != rule), key=counts.__getitem__)
    for f in range(1, counts[rival] + 1):
        left = counts[rival] - f
        if left < f or (left == f and RULES.index(rival) < RULES.index(rule)):
            return f
    return None


def assess(seed: int) -> dict[str, dict]:
    """Per truth rule: flips needed, and over repeated directed attacks with FLIPS flips,
    how often the rule switches and how often each audit policy with AUDITS tokens restores it."""
    cards = deck_cards(seed)
    report = {}
    for rule in RULES:
        labels = clean_labels(cards, rule)
        switched, restored = 0, {"random": 0, "conflict": 0}
        for draw in range(DRAWS):
            flips = poison(cards, labels, FLIPS, "directed", rng_for(seed, "deck", rule, draw, "attack"), rule)
            supplied = flip_labels(labels, flips)
            switched += fit(cards, supplied) != rule
            for defense in restored:
                result = audit(cards, supplied, AUDITS, defense, labels.__getitem__,
                               rng_for(seed, "deck", rule, draw, defense))
                restored[defense] += fit(cards, result.labels) == rule
        report[rule] = {"learns_truth": fit(cards, labels) == rule, "flips_needed": flips_needed(cards, rule),
                        "switch_rate": switched / DRAWS,
                        **{f"{d}_final_true": n / DRAWS for d, n in restored.items()}}
    return report


def profiles(seed: int) -> int:
    return len({c.features for c in deck_cards(seed)})


def eligible(report: dict[str, dict]) -> bool:
    """Under every truth: one flip never switches the rule, four always can, and the defender is contested."""
    lo, hi = CONTESTED
    return all(r["learns_truth"] and r["flips_needed"] is not None and 2 <= r["flips_needed"] <= FLIPS
               and lo <= r["conflict_final_true"] <= hi for r in report.values())


def balance(report: dict[str, dict]) -> float:
    """Mean distance from an even contest; smaller is better."""
    return sum(abs(r["conflict_final_true"] - .5) for r in report.values()) / len(report)


def select() -> dict[str, int]:
    """The four most balanced eligible development decks, lettered in rank order."""
    reports = {seed: assess(seed) for seed in DEV_SEEDS}
    ranked = sorted((balance(r), seed) for seed, r in reports.items() if eligible(r))
    return {letter: seed for letter, (_, seed) in zip(LETTERS, ranked)}


def deck(letter: str) -> tuple[Card, ...]:
    """A printed deck: the chosen seed's features with IDs such as A01-A24."""
    return deck_cards(FIXED_DECKS[letter], letter)
