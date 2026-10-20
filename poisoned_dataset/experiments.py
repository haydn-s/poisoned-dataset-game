"""Paired simulation with immutable scenarios and an explicit trusted oracle."""

import csv
import json
import platform
import subprocess
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev

from . import __version__
from .core import (ATTACKS, DEFENSES, REGIMES, accuracy, audit, errors, fit, flip_labels,
                   generate, poison, rng_for)

PROTOCOL = "1.0"  # docs/evaluation-plan.md; bump and rerun the main seeds if any frozen parameter changes


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def git_state() -> dict:
    try:
        root = Path(__file__).resolve().parent.parent
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        return {"commit": head, "dirty": bool(status.strip())}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def bootstrap_interval(values: list[float], resamples: int, key: tuple) -> tuple:
    if len(values) < 2 or resamples == 0:
        return "", ""
    rng = rng_for(20261019, "bootstrap", *key)
    draws = sorted(mean(rng.choices(values, k=len(values))) for _ in range(resamples))
    return draws[int(0.025 * (resamples - 1))], draws[int(0.975 * (resamples - 1))]


def run(out: Path, seeds: list[int], n: int, attack_budgets: list[int],
        audit_budgets: list[int], resamples: int = 1000) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Supply unique dataset seeds")
    if n < 1 or resamples < 0:
        raise ValueError("Deck size must be positive and resamples nonnegative")
    for budgets in (attack_budgets, audit_budgets):
        if not budgets or len(set(budgets)) != len(budgets) or any(not 0 <= b <= n for b in budgets):
            raise ValueError("Budgets must be unique and between zero and deck size")
    out.mkdir(parents=True, exist_ok=False)
    rows, paired, scenarios = [], [], []
    for regime in REGIMES:
        for seed in seeds:
            scenario = generate(seed, n, regime)
            scenarios.append(asdict(scenario))
            clean_rule = fit(scenario.cards, scenario.clean_labels)
            clean_accuracy = accuracy(clean_rule, scenario.true_rule)
            for attack in ATTACKS:
                for k in attack_budgets:
                    flips = poison(scenario.cards, scenario.clean_labels, k, attack,
                                   rng_for(seed, "attack", regime, attack, k), scenario.true_rule)
                    supplied = flip_labels(scenario.clean_labels, flips)
                    poisoned_rule = fit(scenario.cards, supplied)
                    poisoned_accuracy = accuracy(poisoned_rule, scenario.true_rule)
                    for a in audit_budgets:
                        cell = {"seed": seed, "regime": regime, "attack": attack,
                                "attack_budget": k, "audit_budget": a}
                        finals = {}
                        for defense in DEFENSES:
                            result = audit(scenario.cards, supplied, a, defense,
                                           scenario.clean_labels.__getitem__,
                                           rng_for(seed, "audit", regime, attack, k, a, defense))
                            final_rule = fit(scenario.cards, result.labels)
                            final_accuracy = accuracy(final_rule, scenario.true_rule)
                            used = len(result.audits)
                            recovery = final_accuracy - poisoned_accuracy
                            finals[defense] = final_accuracy
                            rows.append({**cell, "defense": defense, "n_train": n,
                                         "true_rule": scenario.true_rule, "clean_rule": clean_rule,
                                         "poisoned_rule": poisoned_rule, "final_rule": final_rule,
                                         "clean_errors": json.dumps(errors(scenario.cards, scenario.clean_labels)),
                                         "poisoned_errors": json.dumps(errors(scenario.cards, supplied)),
                                         "final_errors": json.dumps(errors(scenario.cards, result.labels)),
                                         "flips_used": len(flips),
                                         "flipped_cards": ";".join(scenario.cards[i].id for i in flips),
                                         "audits_used": used,
                                         "corruption_found": sum(x.before != x.after for x in result.audits),
                                         "clean_accuracy": clean_accuracy,
                                         "poisoned_accuracy": poisoned_accuracy,
                                         "final_accuracy": final_accuracy,
                                         "attack_effectiveness": clean_accuracy - poisoned_accuracy,
                                         "accuracy_recovered": recovery,
                                         "recovery_per_audit": recovery / used if used else "",
                                         "audit_trace": json.dumps([asdict(x) for x in result.audits])})
                        paired.append({**cell, "conflict_minus_random": finals["conflict"] - finals["random"]})

    keys = ("regime", "attack", "attack_budget", "audit_budget")
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in (*keys, "defense"))].append(row)
    summaries = []
    for key, members in groups.items():
        metrics = ("final_accuracy", "attack_effectiveness", "accuracy_recovered",
                   "audits_used", "corruption_found")
        values = [r["final_accuracy"] for r in members]
        summaries.append({**dict(zip((*keys, "defense"), key)), "n_seeds": len(members),
                          **{f"mean_{m}": mean(r[m] for r in members) for m in metrics},
                          "sd_final_accuracy": stdev(values) if len(values) > 1 else ""})
    paired_groups: dict[tuple, list[float]] = defaultdict(list)
    for row in paired:
        paired_groups[tuple(row[k] for k in keys)].append(row["conflict_minus_random"])
    comparisons = []
    for key, values in paired_groups.items():
        lo, hi = bootstrap_interval(values, resamples, key)
        comparisons.append({**dict(zip(keys, key)), "n_seeds": len(values),
                            "mean_conflict_minus_random": mean(values),
                            "ci95_low": lo, "ci95_high": hi,
                            "conflict_win_fraction": mean(v > 0 for v in values),
                            "tie_fraction": mean(v == 0 for v in values)})
    metadata = {"prototype_version": __version__, "protocol": PROTOCOL,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "git": git_state(),
                "seeds": seeds, "n_train": n, "regimes": REGIMES, "attacks": ATTACKS,
                "defenses": DEFENSES, "attack_budgets": attack_budgets,
                "audit_budgets": audit_budgets, "deployment": "uniform eight-profile enumeration",
                "bootstrap_resamples": resamples, "bootstrap_seed": 20261019,
                "rng": "sha256(repr((dataset_seed, stream_parts))) -> random.Random",
                "rows": len(rows), "paired_rows": len(paired)}
    write_csv(out / "runs.csv", rows)
    write_csv(out / "summary.csv", summaries)
    write_csv(out / "paired.csv", paired)
    write_csv(out / "comparisons.csv", comparisons)
    (out / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata
