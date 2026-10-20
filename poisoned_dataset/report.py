"""Figures and headline numbers from a finished experiment directory.

Reads only the runner's outputs (runs.csv, comparisons.csv) plus the seeded
scenario generator, so every figure is reproducible from committed results.
Charts follow one palette: conflict, random and no-audit keep fixed colours,
marker shapes and direct labels, and switch to dark steps with the viewer's theme.
"""

import csv
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from statistics import mean

from . import art
from .core import LABELS, flip_labels, generate

PRIMARY = {"regime": "correlated", "attack": "directed", "attack_budget": 4, "audit_budget": 4}
DEFENSES = (("conflict", "Conflict audit"), ("random", "Random audit"), ("none", "No audit"))
PANELS = (("independent", "random"), ("independent", "directed"), ("correlated", "random"), ("correlated", "directed"))
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"
STYLE = f"""<style>
text {{ font-family: {FONT}; }}
.bg {{ fill: #fcfcfb; }} .ink {{ fill: #0b0b0b; }} .ink2 {{ fill: #52514e; }} .muted {{ fill: #898781; }}
.grid {{ stroke: #e1e0d9; }} .axis {{ stroke: #c3c2b7; }} .ring {{ stroke: #fcfcfb; }}
.chip {{ fill: #f0efec; }} .flip {{ stroke: #d03b3b; }}
.c-conflict {{ fill: #2a78d6; }} .c-random {{ fill: #eb6834; }} .c-none {{ fill: #1baf7a; }}
.l-conflict {{ stroke: #2a78d6; fill: none; }} .l-random {{ stroke: #eb6834; fill: none; }}
.l-none {{ stroke: #1baf7a; fill: none; }} .l-clean {{ stroke: #898781; fill: none; }}
@media (prefers-color-scheme: dark) {{
  .bg {{ fill: #1a1a19; }} .ink {{ fill: #f0efec; }} .ink2 {{ fill: #c3c2b7; }}
  .grid {{ stroke: #2c2c2a; }} .axis {{ stroke: #383835; }} .ring {{ stroke: #1a1a19; }} .chip {{ fill: #383835; }}
  .c-conflict {{ fill: #3987e5; }} .c-random {{ fill: #d95926; }} .c-none {{ fill: #199e70; }}
  .l-conflict {{ stroke: #3987e5; }} .l-random {{ stroke: #d95926; }} .l-none {{ stroke: #199e70; }}
}}
</style>"""


def load(results: Path) -> tuple[list[dict], list[dict]]:
    with (results / "runs.csv").open(newline="", encoding="utf-8") as stream:
        runs = list(csv.DictReader(stream))
    with (results / "comparisons.csv").open(newline="", encoding="utf-8") as stream:
        comparisons = list(csv.DictReader(stream))
    for row in (*runs, *comparisons):
        for key in ("seed", "attack_budget", "audit_budget", "n_seeds"):
            if key in row:
                row[key] = int(row[key])
    return runs, comparisons


def cell(rows: list[dict], **where) -> list[dict]:
    return [r for r in rows if all(r[k] == v for k, v in where.items())]


def by_seed(rows: list[dict]) -> dict[int, dict[str, dict]]:
    seeds: dict[int, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        seeds[row["seed"]][row["defense"]] = row
    return seeds


def conflicting_duplicates(seed: int, regime: str, flipped: str) -> bool:
    """Whether the poisoned deck has any profile group holding both labels."""
    scenario = generate(seed, regime=regime)
    index = {c.id: i for i, c in enumerate(scenario.cards)}
    labels = flip_labels(scenario.clean_labels, [index[x] for x in flipped.split(";") if x])
    groups = defaultdict(set)
    for card, label in zip(scenario.cards, labels):
        groups[card.features].add(label)
    return any(len(v) > 1 for v in groups.values())


def headline(runs: list[dict], comparisons: list[dict]) -> dict:
    """The prespecified primary cell, plus an exploratory split by visible conflict."""
    seeds = by_seed(cell(runs, **PRIMARY))
    switched = {s: d for s, d in seeds.items() if d["none"]["poisoned_rule"] != d["none"]["clean_rule"]}
    restored = lambda group, defense: sum(d[defense]["final_rule"] == d[defense]["true_rule"] for d in group.values())
    split = {}
    for visible in (True, False):
        group = {s: d for s, d in switched.items()
                 if conflicting_duplicates(s, PRIMARY["regime"], d["none"]["flipped_cards"]) == visible}
        split["visible" if visible else "hidden"] = {
            "switched_seeds": len(group), **{f"{d}_restored": restored(group, d) for d in ("conflict", "random")}}
    comparison = cell(comparisons, **PRIMARY)[0]
    diffs = [float(d["conflict"]["final_accuracy"]) - float(d["random"]["final_accuracy"]) for d in seeds.values()]
    flips = defaultdict(int)
    for d in seeds.values():
        flips[int(d["none"]["flips_used"])] += 1
    return {
        "cell": PRIMARY, "n_seeds": len(seeds),
        "clean_accuracy": mean(float(d["none"]["clean_accuracy"]) for d in seeds.values()),
        "flips_used": dict(sorted(flips.items())),
        "attack_switched_rule": len(switched),
        "poisoned_accuracy": mean(float(d["none"]["poisoned_accuracy"]) for d in seeds.values()),
        "defenses": {name: {"final_accuracy": mean(float(d[name]["final_accuracy"]) for d in seeds.values()),
                            "restored_true_rule": restored(switched, name),
                            "corruption_found_per_seed": mean(int(d[name]["corruption_found"]) for d in seeds.values())}
                     for name, _ in DEFENSES},
        "paired_difference": {"mean": float(comparison["mean_conflict_minus_random"]),
                              "ci95": [float(comparison["ci95_low"]), float(comparison["ci95_high"])],
                              "wins": sum(x > 0 for x in diffs), "ties": sum(x == 0 for x in diffs),
                              "losses": sum(x < 0 for x in diffs)},
        "exploratory_by_visible_conflict": split,
    }


def svg(width: float, height: float, body: str, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>{STYLE}'
            f'<rect class="bg" width="{width}" height="{height}"/>{body}</svg>\n')


def label(x, y, s, cls="ink2", size=12, anchor="start", weight=400):
    return (f'<text class="{cls}" x="{art.f(x)}" y="{art.f(y)}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(s)}</text>')


def marker(kind: str, x: float, y: float, tip: str) -> str:
    shape = {"conflict": f'<circle cx="{art.f(x)}" cy="{art.f(y)}" r="4.5"',
             "random": f'<rect x="{art.f(x - 4.5)}" y="{art.f(y - 4.5)}" width="9" height="9" rx="1"',
             "none": f'<path d="M{art.f(x)} {art.f(y - 5.5)}L{art.f(x + 5.2)} {art.f(y + 4)}H{art.f(x - 5.2)}Z"'}[kind]
    return f'<g>{shape} class="c-{kind} ring" stroke-width="2"/><title>{escape(tip)}</title></g>'


def legend(x: float, y: float) -> str:
    out = []
    for k, (key, name) in enumerate(DEFENSES):
        cx = x + k * 140
        out.append(f'<path class="l-{key}" d="M{cx} {y}h22" stroke-width="2"/>' + marker(key, cx + 11, y, name)
                   + label(cx + 30, y + 4, name, "ink2", 12))
    out.append(f'<path class="l-clean" d="M{x + 420} {y}h22" stroke-width="1" stroke-dasharray="3 3"/>'
               + label(x + 450, y + 4, "Clean labels", "ink2", 12))
    return "".join(out)


def panel_frame(x0, y0, w, h, title, ys, fmt, xs, xlabel):
    out = [label(x0, y0 - 12, title, "ink", 13, weight=600)]
    lo, hi = ys[0], ys[-1]
    for v in ys:
        y = y0 + h - (v - lo) / (hi - lo) * h
        out.append(f'<path class="grid" d="M{x0} {art.f(y)}H{x0 + w}" stroke-width="1"/>'
                   + label(x0 - 8, y + 4, fmt(v), "muted", 11, "end"))
    for k, v in enumerate(xs):
        x = x0 + k * w / (len(xs) - 1)
        out.append(label(x, y0 + h + 18, str(v), "muted", 11, "middle"))
    out.append(label(x0 + w / 2, y0 + h + 36, xlabel, "ink2", 11, "middle"))
    return "".join(out), (lambda v: y0 + h - (v - lo) / (hi - lo) * h)


def accuracy_figure(runs: list[dict]) -> str:
    """Mean final accuracy against the attack ceiling, at four audits, for each regime and attack."""
    budgets = sorted({r["attack_budget"] for r in runs})
    means = defaultdict(list)
    for r in runs:
        if r["audit_budget"] == 4:
            means[(r["regime"], r["attack"], r["attack_budget"], r["defense"])].append(float(r["final_accuracy"]))
            means[(r["regime"], r["attack"], r["attack_budget"], "clean")].append(float(r["clean_accuracy"]))
    W, H, w, h = 980, 700, 380, 210
    body = [label(40, 34, "Final accuracy against attack ceiling, with four audits", "ink", 18, weight=600),
            label(40, 56, "Mean over 200 main seeds per point. Accuracy is 1.0 for the true rule and 0.5 for any "
                          "other, so 0.5 is the floor.", "ink2", 12), legend(64, 86)]
    for k, (regime, attack) in enumerate(PANELS):
        x0, y0 = 90 + (k % 2) * 470, 140 + (k // 2) * 290
        frame, ymap = panel_frame(x0, y0, w, h, f"{regime.title()} training · {attack} attack",
                                  [.5, .6, .7, .8, .9, 1.0], lambda v: f"{v:.1f}", budgets, "Attack ceiling (flips)")
        body.append(frame)
        xmap = lambda b: x0 + budgets.index(b) * w / (len(budgets) - 1)
        clean = " ".join(f"{art.f(xmap(b))},{art.f(ymap(mean(means[(regime, attack, b, 'clean')])))}" for b in budgets)
        body.append(f'<polyline class="l-clean" points="{clean}" stroke-width="1" stroke-dasharray="3 3"/>')
        placed = []
        for key, name in DEFENSES:
            pts = [(xmap(b), ymap(mean(means[(regime, attack, b, key)])), b, mean(means[(regime, attack, b, key)]))
                   for b in budgets]
            body.append(f'<polyline class="l-{key}" points="{" ".join(f"{art.f(x)},{art.f(y)}" for x, y, _, _ in pts)}" '
                        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
            body.extend(marker(key, x, y, f"{name}, {regime} {attack}, k = {b}: {v:.3f}") for x, y, b, v in pts)
            x, y, _, v = pts[-1]
            if all(abs(y - other) >= 14 for other in placed):  # never stack colliding end labels
                placed.append(y)
                body.append(label(x + 10, y + 4, f"{v:.2f}", "ink2", 11))
        if (regime, attack) == (PRIMARY["regime"], PRIMARY["attack"]):
            x = xmap(PRIMARY["attack_budget"])
            body.append(f'<path class="axis" d="M{art.f(x)} {y0}V{y0 + h}" stroke-width="1"/>'
                        + label(x + 6, y0 + 12, "primary cell", "ink2", 11))
    return svg(W, H, "".join(body), "Final accuracy against attack ceiling with four audits, by regime and attack")


def paired_figure(comparisons: list[dict]) -> str:
    """Conflict minus random final accuracy, with 95% bootstrap intervals, against the audit budget at k = 4."""
    audits = sorted({c["audit_budget"] for c in comparisons})
    W, H, w, h = 980, 660, 380, 200
    body = [label(40, 34, "Conflict minus random final accuracy, attack ceiling 4", "ink", 18, weight=600),
            label(40, 56, "Mean paired difference over 200 main seeds, in percentage points, with 95% percentile "
                          "bootstrap intervals (2,000 resamples).", "ink2", 12)]
    for k, (regime, attack) in enumerate(PANELS):
        x0, y0 = 90 + (k % 2) * 470, 110 + (k // 2) * 280
        frame, ymap = panel_frame(x0, y0, w, h, f"{regime.title()} training · {attack} attack",
                                  [-5, 0, 5, 10, 15, 20, 25], lambda v: f"{v:+d}" if v else "0", audits,
                                  "Audit budget (tokens)")
        body.append(frame + f'<path class="axis" d="M{x0} {art.f(ymap(0))}H{x0 + w}" stroke-width="1"/>')
        for a in audits:
            c = cell(comparisons, regime=regime, attack=attack, attack_budget=PRIMARY["attack_budget"], audit_budget=a)[0]
            x = x0 + audits.index(a) * w / (len(audits) - 1)
            m = 100 * float(c["mean_conflict_minus_random"])
            lo, hi = (100 * float(c[key]) if c[key] != "" else m for key in ("ci95_low", "ci95_high"))
            tip = f"{regime} {attack}, k = 4, a = {a}: {m:+.1f} pp (95% CI {lo:+.1f} to {hi:+.1f})"
            body.append(f'<path class="l-conflict" d="M{art.f(x)} {art.f(ymap(lo))}V{art.f(ymap(hi))}" stroke-width="2" '
                        f'stroke-linecap="round"/>' + marker("conflict", x, ymap(m), tip)
                        + (label(x + 10, ymap(m) + 4, f"{m:+.1f}", "ink2", 11) if a else ""))
            if (regime, attack, a) == (PRIMARY["regime"], PRIMARY["attack"], PRIMARY["audit_budget"]):
                body.append(label(x - 10, ymap(hi) - 8, "primary", "ink2", 11, "end"))
    return svg(W, H, "".join(body), "Conflict minus random final accuracy against audit budget at attack ceiling 4")


def trace_case(runs: list[dict]) -> int | None:
    """The lowest primary-cell seed where conflict auditing ends wrong, random ends right,
    and the attack flipped a whole group of two or more look-alike cards, leaving no disagreement."""
    for seed, d in sorted(by_seed(cell(runs, **PRIMARY)).items()):
        if not (d["conflict"]["final_rule"] != d["conflict"]["true_rule"] == d["random"]["final_rule"]):
            continue
        scenario = generate(seed, regime=PRIMARY["regime"])
        flipped = set(d["none"]["flipped_cards"].split(";"))
        groups = defaultdict(list)
        for c in scenario.cards:
            groups[c.features].append(c.id)
        whole = [g for g in groups.values() if len(g) > 1 and set(g) <= flipped]
        if whole and not conflicting_duplicates(seed, PRIMARY["regime"], d["none"]["flipped_cards"]):
            return seed
    return None


def trace_figure(runs: list[dict], seed: int) -> str:
    """Every training card grouped by look-alike profile, with the flips and both audit sequences."""
    d = by_seed(cell(runs, **PRIMARY))[seed]
    scenario = generate(seed, regime=PRIMARY["regime"])
    flipped = set(d["none"]["flipped_cards"].split(";"))
    index = {c.id: i for i, c in enumerate(scenario.cards)}
    supplied = flip_labels(scenario.clean_labels, [index[x] for x in flipped])
    groups = defaultdict(list)
    for c in scenario.cards:
        groups[c.features].append(c)
    order = sorted(groups, key=lambda feats: (-len(groups[feats]), feats))
    audits = {name: json.loads(d[name]["audit_trace"]) for name in ("conflict", "random")}
    steps = {name: {scenario.cards[t["index"]].id: n + 1 for n, t in enumerate(trace)} for name, trace in audits.items()}
    col, W = 142, 50 + 142 * len(order)
    tallest = max(len(g) for g in groups.values())
    H = 250 + tallest * 24 + 76
    body = [label(30, 34, f"Seed {seed}: a whole look-alike group poisoned, so no labels disagree", "ink", 18, weight=600),
            label(30, 56, f"True rule {scenario.true_rule}; the directed attack flipped {len(flipped)} tags and the robot "
                          f"learned {d['none']['poisoned_rule']}. Red outlines mark flipped tags; numbers give audit "
                          "order.", "ink2", 12)]
    for k, feats in enumerate(order):
        x = 40 + k * col
        c0 = groups[feats][0]
        body.append(f'<g transform="translate({x + 61} 100)">{art.cargo_icon(*c0.features, 34)}</g>')
        words = c0.describe().split(", ")
        body.append(label(x + 61, 138, " · ".join(words[:2]), "ink2", 11, "middle")
                    + label(x + 61, 152, words[2], "ink2", 11, "middle"))
        for j, c in enumerate(groups[feats]):
            y = 168 + j * 24
            hit = c.id in flipped
            body.append(f'<rect class="chip{" flip" if hit else ""}" x="{x}" y="{y}" width="122" height="20" rx="4" '
                        f'stroke-width="{2 if hit else 0}"/>'
                        + label(x + 6, y + 14, f"{c.id} {LABELS[supplied[index[c.id]]]}", "ink", 11))
            for m, name in enumerate(("conflict", "random")):
                if c.id in steps[name]:
                    cx = x + 92 + m * 19
                    body.append(f'<g><circle class="c-{name}" cx="{cx}" cy="{y + 10}" r="8"/>'
                                + label(cx, y + 14, str(steps[name][c.id]), "bg", 10, "middle", 700)
                                + f'<title>{escape(name)} audit {steps[name][c.id]}: {c.id}</title></g>')
    y = 190 + tallest * 24
    for m, (name, title) in enumerate((("conflict", "Conflict audit"), ("random", "Random audit"))):
        trace = audits[name]
        row = ", ".join(f"{scenario.cards[t['index']].id} {'fixed' if t['before'] != t['after'] else 'already right'}"
                        for t in trace)
        body.append(f'<circle class="c-{name}" cx="38" cy="{y + m * 40 - 4}" r="6"/>'
                    + label(52, y + m * 40, f"{title}: {row}.", "ink", 12)
                    + label(52, y + m * 40 + 16, f"Learned rule after each audit: "
                                                  f"{', '.join(t['learned_rule'] for t in trace)}; final accuracy "
                                                  f"{float(d[name]['final_accuracy']):.1f}.", "ink2", 11))
    return svg(W, H, "".join(body), f"Audit trace for seed {seed} in the primary cell")


def build(results: Path, out: Path) -> dict:
    runs, comparisons = load(results)
    out.mkdir(parents=True, exist_ok=True)
    seed = trace_case(runs)
    numbers = {**headline(runs, comparisons), "trace_seed": seed}
    (out / "headline.json").write_text(json.dumps(numbers, indent=2) + "\n", encoding="utf-8")
    (out / "accuracy-vs-attack.svg").write_text(accuracy_figure(runs), encoding="utf-8")
    (out / "paired-difference.svg").write_text(paired_figure(comparisons), encoding="utf-8")
    if seed is not None:
        (out / f"trace-seed-{seed}.svg").write_text(trace_figure(runs, seed), encoding="utf-8")
    return numbers
