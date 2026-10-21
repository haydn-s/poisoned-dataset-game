"""Who wins a match: defender scores first, then tiebreakers.

A round scores 4/8 or 8/8, so equal scores are common. The tiebreakers decide only
the match winner; no round's accuracy changes, so evaluation protocol v1.0 is
untouched. Simulations here use development seeds and the fixed decks, never the
main seeds.
"""

from dataclasses import dataclass

from .core import accuracy, audit, fit, flip_labels, generate, poison, rng_for
from . import decks

FLIPS, AUDITS = 4, 4


@dataclass(frozen=True)
class Defence:
    points: int  # test cards right, out of eight
    found: int   # audits that changed a tag; each one found a flipped label
    spent: int   # audit tokens used


def winner(a: Defence, b: Defence, tiebreak: bool = True) -> str | None:
    """'A', 'B', or None for a draw: higher score, then more poison found, then fewer tokens spent."""
    keys = (lambda d: d.points, lambda d: d.found, lambda d: -d.spent)
    for key in keys if tiebreak else keys[:1]:
        if key(a) != key(b):
            return "A" if key(a) > key(b) else "B"
    return None


def play_round(cards, truth: str, defense: str, streams: tuple) -> Defence:
    """One automated round: a directed attack with FLIPS flips, then AUDITS audits by the given policy.
    The attack stream ignores the policy, so both policies face the same attacks."""
    clean = tuple(getattr(card, truth) for card in cards)
    flips = poison(cards, clean, FLIPS, "directed", rng_for(*streams, "attack"), truth)
    result = audit(cards, flip_labels(clean, flips), AUDITS, defense, clean.__getitem__,
                   rng_for(*streams, defense, "audit"))
    return Defence(round(8 * accuracy(fit(cards, result.labels), truth)),
                   sum(a.before != a.after for a in result.audits), len(result.audits))


def seeded_matches(defense: str, draws: int = 10) -> list[tuple[Defence, Defence]]:
    """Seeded-kit matches on development seeds s and s + 1, as `components --seed s` prints them."""
    out = []
    for seed in range(min(decks.DEV_SEEDS), max(decks.DEV_SEEDS)):
        rounds = [generate(seed + r, regime=decks.REGIME) for r in range(2)]
        for d in range(draws):
            out.append(tuple(play_round(s.cards, s.true_rule, defense, (s.seed, "match", d)) for s in rounds))
    return out


def fixed_matches(defense: str, draws: int = 3) -> list[tuple[Defence, Defence]]:
    """Fixed-edition matches: every ordered pair of different decks, every pair of truth cards."""
    out = []
    for first in decks.LETTERS:
        for second in decks.LETTERS:
            if first == second:
                continue
            for t1 in ("red", "round", "striped"):
                for t2 in ("red", "round", "striped"):
                    for d in range(draws):
                        out.append((play_round(decks.deck(first), t1, defense, (first, t1, second, t2, d, 1)),
                                    play_round(decks.deck(second), t2, defense, (first, t1, second, t2, d, 2))))
    return out


def draw_rates(matches: list[tuple[Defence, Defence]]) -> dict[str, float]:
    n = len(matches)
    return {"matches": n,
            "draws_by_score": sum(winner(a, b, tiebreak=False) is None for a, b in matches) / n,
            "draws_after_tiebreaks": sum(winner(a, b) is None for a, b in matches) / n}


def report() -> dict[str, dict]:
    """Draw rates for both editions with both automated defense policies."""
    return {f"{edition} · {defense}": draw_rates(make(defense))
            for edition, make in (("seeded kit", seeded_matches), ("fixed edition", fixed_matches))
            for defense in ("conflict", "random")}
