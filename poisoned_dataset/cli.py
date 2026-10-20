"""A small shared-screen helper and reproducible experiment entry points."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from secrets import randbits

from .core import (LABELS, REGIMES, RULES, accuracy, conflict_scores, errors, fit,
                   flip_labels, generate, poison, predict, rng_for, test_deck)


def budget_list(value: str) -> list[int]:
    try:
        return [int(x) for x in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use comma-separated integer budgets") from exc


def show(cards, labels) -> None:
    for card, label in zip(cards, labels):
        print(f"  {card.id}  {card.describe():25} {LABELS[label]}")
    print("Training errors:", errors(cards, labels), "-> learned rule:", fit(cards, labels))


def ask_cards(prompt, cards, maximum, excluded=()) -> list[int]:
    lookup = {c.id: i for i, c in enumerate(cards)}
    while True:
        ids = input(prompt).upper().replace(",", " ").split()
        if len(ids) != len(set(ids)) or len(ids) > maximum:
            print(f"Choose at most {maximum} distinct cards.")
        elif any(x not in lookup or lookup[x] in excluded for x in ids):
            print("Choose listed, unverified card IDs such as C03.")
        else:
            return [lookup[x] for x in ids]


def clear() -> None:
    print("\033[2J\033[H", end="", flush=True)


def play(seed: int, regime: str, attack_budget: int, audit_budget: int) -> None:
    print("POISONED DATASET — draft 0.1. Two rounds; each player defends once.")
    print("Use player names A and B. Ask the other player to look away at handoffs.")
    print("The helper relies on honest play and is not a secure secret-keeping system.")
    scores = []
    for round_number, defender in enumerate(("A", "B")):
        scenario = generate(seed + round_number, 24, regime)
        input(f"\nRound {round_number + 1}: defender {defender} looks away; attacker presses Enter. ")
        clear()
        print("ATTACKER ONLY. True rule:", scenario.true_rule)
        show(scenario.cards, scenario.clean_labels)
        flips = ask_cards(f"Flip up to {attack_budget} labels (IDs, or Enter for none): ",
                          scenario.cards, attack_budget)
        labels = list(flip_labels(scenario.clean_labels, flips))
        input("Remember your choices. Press Enter to hide this screen, then call the defender back. ")
        clear()
        print(f"DEFENDER {defender}: each audit costs one token, even if the label is correct.")
        print("Audits replace only the selected label. Other copies still need separate audits.")
        verified: set[int] = set()
        history = []
        show(scenario.cards, labels)
        for remaining in range(audit_budget, 0, -1):
            scores_by_card = conflict_scores(scenario.cards, labels, verified)
            best = max(scores_by_card.values())
            hints = [scenario.cards[i].id for i, score in scores_by_card.items() if score == best]
            print("Conflict policy's top choices (not proof of poisoning):", ", ".join(hints))
            chosen = ask_cards(f"{remaining} tokens left. Audit one card, or Enter to lock the rule: ",
                               scenario.cards, 1, verified)
            if not chosen:
                break
            i = chosen[0]
            before = labels[i]
            labels[i] = scenario.clean_labels[i]
            verified.add(i)
            history.append((scenario.cards[i].id, LABELS[before], LABELS[labels[i]]))
            print("Trusted reference:", scenario.cards[i].id, LABELS[labels[i]])
            show(scenario.cards, labels)
        rule = fit(scenario.cards, labels)
        print("\nRule locked:", rule, "— revealing the independent scoring deck.")
        for card in test_deck():
            print(card.id, card.describe(), "predicted", LABELS[predict(rule, card)],
                  "reference", LABELS[predict(scenario.true_rule, card)])
        points = round(8 * accuracy(rule, scenario.true_rule))
        scores.append(points)
        print(f"Defender {defender}: {points}/8. True rule: {scenario.true_rule}.")
        print("Flipped cards:", [scenario.cards[i].id for i in flips], "Audits:", history)
        print("Discuss: why did this rule win, and which audit changed the evidence?")
    print(f"\nFinal defender scores: A {scores[0]}/8; B {scores[1]}/8.")
    print("Draw." if scores[0] == scores[1] else f"Player {'A' if scores[0] > scores[1] else 'B'} wins.")
    print("Match seed for your playtest record:", seed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Poisoned Dataset tabletop helper, draft 0.1")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Reveal one automatic worked scenario")
    demo.add_argument("--seed", type=int, default=19)
    demo.add_argument("--regime", choices=REGIMES, default="correlated")
    demo.add_argument("--attack-budget", type=int, default=4)
    demo.add_argument("--audit-budget", type=int, default=4)
    game = sub.add_parser("play", help="Run a two-player match on a shared terminal")
    game.add_argument("--seed", type=int, help="Omit for a fresh match; printed after scoring")
    game.add_argument("--regime", choices=REGIMES, default="correlated")
    game.add_argument("--attack-budget", type=int, default=4)
    game.add_argument("--audit-budget", type=int, default=4)
    experiment = sub.add_parser("experiment", help="Run a paired simulation grid")
    experiment.add_argument("--seed-start", type=int, default=0)
    experiment.add_argument("--seeds", type=int, default=200, help="Number of consecutive dataset seeds")
    experiment.add_argument("--n-train", type=int, default=24)
    experiment.add_argument("--attack-budgets", type=budget_list, default=[0, 2, 4, 6, 8])
    experiment.add_argument("--audit-budgets", type=budget_list, default=[0, 2, 4])
    experiment.add_argument("--bootstrap-resamples", type=int, default=1000)
    experiment.add_argument("--out", type=Path, required=True, help="New output directory")
    components = sub.add_parser("components", help="Create the printable kit: cards, references, rulebook and box")
    components.add_argument("--seed", type=int, default=19)
    components.add_argument("--regime", choices=REGIMES, default="correlated")
    components.add_argument("--out", type=Path, required=True, help="New output directory")
    components.add_argument("--cover-image", type=Path, help="Optional PNG/JPEG/WebP key art for the box lid")
    components.add_argument("--edition", choices=("seeded", "fixed"), default="seeded",
                            help="seeded: a two-round kit for one seed; fixed: the reusable printed edition")
    args = parser.parse_args()
    try:
        if args.command in ("demo", "play"):
            if not 0 <= args.attack_budget <= 24 or not 0 <= args.audit_budget <= 24:
                parser.error("Budgets must be between zero and 24")
        if args.command == "play":
            play(args.seed if args.seed is not None else randbits(32),
                 args.regime, args.attack_budget, args.audit_budget)
        elif args.command == "demo":
            s = generate(args.seed, regime=args.regime)
            flips = poison(s.cards, s.clean_labels, args.attack_budget, "directed",
                           rng_for(s.seed, "demo attack"), s.true_rule)
            supplied = flip_labels(s.clean_labels, flips)
            from .core import audit
            result = audit(s.cards, supplied, args.audit_budget, "conflict",
                           s.clean_labels.__getitem__, rng_for(s.seed, "demo audit"))
            print(json.dumps({"seed": s.seed, "regime": s.regime, "true_rule": s.true_rule,
                              "flipped_cards": [s.cards[i].id for i in flips],
                              "clean_rule": fit(s.cards, s.clean_labels),
                              "poisoned_rule": fit(s.cards, supplied),
                              "final_rule": fit(s.cards, result.labels),
                              "final_accuracy": accuracy(fit(s.cards, result.labels), s.true_rule),
                              "audit_trace": [asdict(x) for x in result.audits]}, indent=2))
        elif args.command == "experiment":
            if args.seeds < 1:
                parser.error("--seeds must be positive")
            from .experiments import run
            result = run(args.out, list(range(args.seed_start, args.seed_start + args.seeds)),
                         args.n_train, args.attack_budgets, args.audit_budgets,
                         args.bootstrap_resamples)
            print(f"Wrote {result['rows']} runs and {result['paired_rows']} paired comparisons to {args.out}")
        else:
            from . import box, components, rulebook
            if args.cover_image and not args.cover_image.is_file():
                parser.error(f"Cover image not found: {args.cover_image}")
            if args.edition == "fixed":
                from . import edition
                edition.build(args.out)
                print(f"Wrote the fixed edition (cards, duplex, backs, rulebook, rulebook-booklet, box) to {args.out}")
            else:
                components.build(args.out, args.seed, args.regime)
                print(f"Wrote public, private, backs, rulebook, rulebook-booklet and box HTML plus scenario.json "
                      f"to {args.out}")
            rulebook.build(args.out, args.edition)
            box.build(args.out, args.cover_image, args.edition)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    except (EOFError, KeyboardInterrupt):
        print("\nMatch stopped.")
