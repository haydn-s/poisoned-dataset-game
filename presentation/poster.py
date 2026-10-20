"""Build the 36 x 24 in poster from the committed results and the game's own art.

Run from the repository root:  python3 presentation/poster.py
Every number and figure is computed from results/evaluation-v1.0, so the poster
cannot drift from the evaluation.
"""

import argparse
import json
import sys
from collections import defaultdict
from html import escape
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from poisoned_dataset import art, edition, report  # noqa: E402
from poisoned_dataset.art import C, INK  # noqa: E402
from poisoned_dataset.components import cargo_card, role_card, rule_card  # noqa: E402
from poisoned_dataset.core import LABELS, RULES, Card, flip_labels, generate  # noqa: E402
from poisoned_dataset.report import PRIMARY, label, marker  # noqa: E402

RESULTS = ROOT / "results" / "evaluation-v1.0"
AUTHOR = "[Author name]"  # fill in before printing
COURSE = "Explainable AI · Duke University · Fall 2026"
URL = "github.com/haydn-s/poisoned-dataset-game"

STYLE = """
@page { size: WIDTHin HEIGHTin; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #8a8178; color: #2a1c14; font-family: 'Inter', system-ui, sans-serif; }
.poster { width: WIDTHin; height: HEIGHTin; position: relative; overflow: hidden; background: #f3e8d0;
          margin: 0 auto; }
.backdrop { position: absolute; inset: 0; width: 100%; height: 100%; }
header { position: absolute; left: 0; right: 0; top: 0; height: 5in; }
header .scene { position: absolute; right: 0; top: 0; width: 7.5in; height: 5in; }
header .logo { position: absolute; left: .55in; top: .35in; width: 9.4in; }
header .titles { position: absolute; left: 10.4in; right: 8.1in; top: .55in; }
h1 { font: 900 56pt/1.05 'Inter Display', 'Inter', sans-serif; margin: 0 0 .18in; }
.byline { font: 600 26pt/1.3 'Inter', sans-serif; margin: 0; }
.byline b { font-weight: 800; }
.columns { position: absolute; left: .55in; right: .55in; top: 5.35in; bottom: .95in; display: grid;
           grid-template-columns: repeat(4, 1fr); gap: .45in; }
.col { display: flex; flex-direction: column; gap: .3in; min-height: 0; }
.col > section:last-child { flex: 1; }
section { background: #fffaf0; border: 4px solid #2a1c14; border-radius: .22in; padding: .28in .32in; }
h2 { font: 900 38pt/1.1 'Inter Display', 'Inter', sans-serif; margin: 0 0 .12in; }
h2 .n { display: inline-block; width: .62in; height: .62in; border-radius: 50%; background: #e2ad35;
        border: 3px solid #2a1c14; text-align: center; font-size: 30pt; line-height: .56in; margin-right: .12in; }
h3 { font: 800 26pt/1.2 'Inter Display', 'Inter', sans-serif; margin: .14in 0 .06in; }
p, li, td, th { font-size: 21pt; line-height: 1.3; }
p { margin: 0 0 .1in; }
ul { margin: 0; padding-left: .38in; }
li { margin-bottom: .05in; }
.lead { font-size: 25pt; font-weight: 600; }
.small { font-size: 17pt; line-height: 1.3; }
.hero { display: flex; align-items: baseline; gap: .2in; margin: .05in 0 .08in; }
.hero b { font: 900 104pt/1 'Inter Display', 'Inter', sans-serif; }
.hero span { font: 700 25pt/1.2 'Inter', sans-serif; }
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: .16in; margin: .12in 0 .06in; }
.tile { border: 3px solid #2a1c14; border-radius: .14in; padding: .12in .14in; background: #f3e8d0; }
.tile b { display: block; font: 900 31pt/1.05 'Inter Display', 'Inter', sans-serif; white-space: nowrap; }
.tile span { font-size: 17pt; line-height: 1.25; display: block; margin-top: .05in; }
table { border-collapse: collapse; width: 100%; margin: .06in 0; }
th, td { text-align: left; padding: .05in .08in; border-bottom: 2px solid #c9b48a; vertical-align: top; }
th { font-weight: 800; }
td.num, th.num { text-align: right; }
figure { margin: .06in 0; }
figure img, figure svg { display: block; width: 100%; height: auto; }
figcaption { font-size: 17pt; line-height: 1.3; margin-top: .06in; }
.strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: .1in; text-align: center; }
.strip svg { width: 100%; height: auto; }
.strip span { font-size: 15pt; font-weight: 700; line-height: 1.2; display: block; margin-top: .04in; }
.cards3 { width: 82%; margin: 0 auto .08in; }
code { font: 600 18pt 'JetBrains Mono', monospace; }
.refs { font-size: 14pt; line-height: 1.3; margin: 0; }
.url { font: 900 27pt/1.2 'Inter Display', 'Inter', sans-serif; margin: .04in 0 .1in; }
footer { position: absolute; left: .55in; right: .55in; bottom: .3in; display: flex; justify-content: space-between;
         font: 700 16pt 'Inter', sans-serif; letter-spacing: .06em; }
@media print { body { background: none; } }
"""


def svg(view: str, body: str, label: str) -> str:
    return f'<svg viewBox="{view}" role="img" aria-label="{escape(label)}">{body}</svg>'


def card_svg(card_markup: str) -> str:
    """Re-wrap a 250 x 350 card so CSS sizes it freely."""
    return card_markup.replace('<svg class="card"', '<svg', 1)


def local_figure(name: str, caption: str, alt: str) -> str:
    return (f'<figure><img src="figures/{name}" alt="{escape(alt)}"><figcaption>{escape(caption)}</figcaption>'
            "</figure>")


def primary_accuracy(runs: list[dict]) -> str:
    """One large panel: mean final accuracy against the attack ceiling in the primary condition, four audits."""
    means = defaultdict(list)
    for r in runs:
        if (r["regime"], r["attack"], r["audit_budget"]) == (PRIMARY["regime"], PRIMARY["attack"], 4):
            means[(r["attack_budget"], r["defense"])].append(float(r["final_accuracy"]))
    budgets = sorted({k for k, _ in means})
    x0, y0, w, h = 46, 54, 270, 190
    xmap = lambda k: x0 + budgets.index(k) * w / (len(budgets) - 1)
    ymap = lambda v: y0 + h - (v - .5) / .5 * h
    body = []
    for v in (.5, .6, .7, .8, .9, 1.0):
        body.append(f'<path class="grid" d="M{x0} {ymap(v):.1f}H{x0 + w}" stroke-width="1"/>'
                    + label(x0 - 7, ymap(v) + 4, f"{v:.1f}", "muted", 11, "end"))
    for k in budgets:
        body.append(label(xmap(k), y0 + h + 17, str(k), "muted", 11, "middle"))
    body.append(label(x0 + w / 2, y0 + h + 34, "Attack ceiling (flips)", "ink2", 11, "middle"))
    body.append(f'<path class="l-clean" d="M{x0} {ymap(1):.1f}H{x0 + w}" stroke-width="1" stroke-dasharray="3 3"/>')
    placed = []
    for key, name in report.DEFENSES:
        pts = [(xmap(k), ymap(mean(means[(k, key)])), k, mean(means[(k, key)])) for k in budgets]
        body.append(f'<polyline class="l-{key}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts)}" '
                    f'stroke-width="2" stroke-linejoin="round"/>')
        body.extend(marker(key, x, y, f"{name}, k = {k}: {v:.3f}") for x, y, k, v in pts)
        x, y, _, v = pts[-1]
        if all(abs(y - other) >= 13 for other in placed):
            placed.append(y)
            body.append(label(x + 9, y + 4, f"{name.split()[0]} {v:.2f}", "ink2", 11))
    for n, (key, name) in enumerate(report.DEFENSES):
        lx = 46 + n * 104
        body.append(f'<path class="l-{key}" d="M{lx} 22h18" stroke-width="2"/>' + marker(key, lx + 9, 22, name)
                    + label(lx + 24, 26, name, "ink2", 11))
    body.append('<path class="l-clean" d="M358 22h18" stroke-width="1" stroke-dasharray="3 3"/>'
                + label(380, 26, "Clean", "ink2", 11))
    return report.svg(420, 290, "".join(body), "Final accuracy against attack ceiling, correlated decks, "
                                                  "directed attack, four audits")


def conditions(comparisons: list[dict]) -> str:
    """Conflict minus random, k = 4 and a = 4, for all four regime and attack conditions."""
    x0, w = 150, 220
    xmap = lambda v: x0 + (v + 5) / 30 * w
    body = [label(x0 + w / 2, 186, "Conflict minus random, accuracy points", "ink2", 11, "middle")]
    for v in (-5, 0, 5, 10, 15, 20, 25):
        body.append(f'<path class="{"axis" if v == 0 else "grid"}" d="M{xmap(v):.1f} 14V160" stroke-width="1"/>'
                    + label(xmap(v), 174, f"{v:+d}" if v else "0", "muted", 11, "middle"))
    for n, (regime, attack) in enumerate(report.PANELS):
        c = report.cell(comparisons, regime=regime, attack=attack, attack_budget=4, audit_budget=4)[0]
        m, lo, hi = (100 * float(c[k]) for k in ("mean_conflict_minus_random", "ci95_low", "ci95_high"))
        y = 32 + n * 38
        primary = (regime, attack) == (PRIMARY["regime"], PRIMARY["attack"])
        body.append(label(x0 - 10, y + 4, f"{regime} · {attack}", "ink" if primary else "ink2", 11, "end",
                          700 if primary else 400)
                    + f'<path class="l-conflict" d="M{xmap(lo):.1f} {y}H{xmap(hi):.1f}" stroke-width="2.5" '
                      f'stroke-linecap="round"/>'
                    + marker("conflict", xmap(m), y, f"{regime} {attack}: {m:+.1f} ({lo:+.1f} to {hi:+.1f})")
                    + label(xmap(hi) + 8, y + 4, f"{m:+.1f}", "ink2", 11))
    return report.svg(420, 196, "".join(body), "Conflict minus random accuracy by condition at four flips and "
                                                  "four audits, with 95% intervals")


def failure_case(runs: list[dict], seed: int) -> str:
    """The poisoned cards and both audit sequences for the traced seed, sized for the poster."""
    d = report.by_seed(report.cell(runs, **PRIMARY))[seed]
    scenario = generate(seed, regime=PRIMARY["regime"])
    flipped = d["none"]["flipped_cards"].split(";")
    by_id = {c.id: c for c in scenario.cards}
    index = {c.id: i for i, c in enumerate(scenario.cards)}
    supplied = flip_labels(scenario.clean_labels, [index[x] for x in flipped])
    chip = lambda x, y, cid, cls="chip", extra="": (
        f'<rect class="{cls}" x="{x}" y="{y}" width="90" height="22" rx="4" {extra}/>'
        + label(x + 26, y + 15.5, f"{cid} {LABELS[supplied[index[cid]]]}", "ink", 10.5))
    body = [label(10, 22, f"Flipped by the attacker (true rule: {scenario.true_rule})", "ink", 12, weight=700)]
    for n, cid in enumerate(flipped):
        x = 10 + n * 98
        c = by_id[cid]
        body.append(chip(x, 32, cid, "chip flip", 'stroke-width="2"')
                    + f'<g transform="translate({x + 12} {43})">{art.cargo_icon(*c.features, 16)}</g>')
    rows = (("conflict", "Conflict audit", 76), ("random", "Random audit", 136))
    for key, name, y in rows:
        trace = json.loads(d[key]["audit_trace"])
        final = d[key]["final_rule"]
        body.append(label(10, y, f"{name}: learned {final}"
                                 f"{' (wrong)' if final != scenario.true_rule else ' (restored)'}", "ink", 12, weight=700))
        for n, t in enumerate(trace):
            cid = scenario.cards[t["index"]].id
            x = 10 + n * 98
            found = t["before"] != t["after"]
            body.append(f'<rect class="chip{" flip" if found else ""}" x="{x}" y="{y + 10}" width="90" height="22" '
                        f'rx="4" stroke-width="{2 if found else 0}"/>'
                        + f'<g transform="translate({x + 12} {y + 21})">{art.cargo_icon(*by_id[cid].features, 16)}</g>'
                        + label(x + 26, y + 25.5, f"{n + 1}. {cid}", "ink", 11)
                        + label(x + 45, y + 46, "found flip" if found else "was right", "ink2", 10, "middle"))
    return report.svg(410, 196, "".join(body), f"Failure case, seed {seed}")


def figures() -> dict[str, str]:
    runs, comparisons = report.load(RESULTS)
    seed = json.loads((RESULTS / "report" / "headline.json").read_text())["trace_seed"]
    return {"primary-accuracy.svg": primary_accuracy(runs), "conditions.svg": conditions(comparisons),
            "failure-case.svg": failure_case(runs, seed)}


def loop_strip() -> str:
    steps = [
        ("Poison: flip up to 4 tags", svg("0 0 250 350", f'<g transform="translate(10 20) scale(.8)">{art.mallory("pp")}</g>', "Mallory")),
        ("Inspect: count errors", card_svg(cargo_card(Card("C07", 1, 1, 1), 1))),
        ("Audit: up to 4 tokens", svg("0 0 250 350", f'<g transform="translate(125 115)">{art.hexbolt("AUDIT", 85, 1)}</g>'
                                     f'<g transform="translate(125 270)">{art.hexbolt("VERIFIED", 70)}</g>',
                      "Audit token flipping to verified")),
        ("Lock: fewest errors", card_svg(rule_card(0, RULES[0]))),
        ("Deploy: 8 new cargo", card_svg(cargo_card(Card("T08", 1, 1, 1), 1, True))),
    ]
    return "".join(f"<div>{s}<span>{escape(t)}</span></div>" for t, s in steps)


def printed_cards() -> list[str]:
    deck_a = ("DECK A", *edition.DECK_TONE["A"])
    return [card_svg(cargo_card(Card("A07", 1, 0, 1), 0, chip=deck_a)), card_svg(edition.reference_back((1, 0, 1))),
            card_svg(edition.reference_front((1, 0, 1), 1)), card_svg(edition.truth_back()),
            card_svg(role_card("ATTACKER", edition.ATTACKER))]


def build(width: float = 36, height: float = 24) -> str:
    h = json.loads((RESULTS / "report" / "headline.json").read_text())
    meta = json.loads((RESULTS / "metadata.json").read_text())
    d, p, split = h["defenses"], h["paired_difference"], h["exploratory_by_visible_conflict"]
    switched = h["attack_switched_rule"]
    pct = lambda n, k: f"{round(100 * n / k)}%"
    vis, hid = split["visible"], split["hidden"]

    header = (f'<header><svg class="backdrop" viewBox="0 0 3600 500" preserveAspectRatio="none" aria-hidden="true">'
              f'<rect width="3600" height="500" fill="url(#shop)"/>'
              f'<path d="M0 470H3600V500H0Z" fill="{C["mustard"]}"/>'
              + art.hatch(art.poly((0, 470), (3600, 470), (3600, 500), (0, 500)), INK, 30, 15, 45, "band")
              + f'</svg><svg class="scene" viewBox="0 0 900 600" role="img" aria-label="Key art: Mallory and the '
                f'sorter robot in the moon-colony warehouse">{art.cover_scene("poster")}</svg>'
                f'<svg class="logo" viewBox="0 0 660 270" role="img" aria-label="Poisoned Dataset">{art.logo()}</svg>'
                f'<div class="titles"><h1>Who changed the labels? A tabletop game and a paired simulation of '
                f'label poisoning under scarce audits</h1>'
                f'<p class="byline"><b>{escape(AUTHOR)}</b> · {escape(COURSE)}</p></div></header>')

    threat = (("Attacker knows", "Clean labels, true rule, candidate rules, tie order"),
              ("Attacker can", "Flip at most k labels, once, before any audit"),
              ("Defender sees", "Features and current labels; buys trusted labels"),
              ("Trusted oracle", "Always right; one card per token"),
              ("Test deck", "8 fresh records, kept out of training and audits"))
    col1 = (
        '<section><h2><span class="n">1</span>The question</h2>'
        '<p class="lead">With only four trusted checks, does auditing <b>conflicting look-alike labels</b> '
        "protect a learner better than checking at random?</p>"
        "<p>If someone can change training labels, a model can learn a rule that fits its data and fails in use. "
        "Checking every label costs too much, so defenders choose which few to verify. Changing labels before "
        "training is a poisoning attack in NIST’s adversarial ML taxonomy.</p></section>"
        '<section><h2><span class="n">2</span>The game</h2>'
        "<p>Two players, two rounds, roles swap. Cargo cards show public features; labels are separate "
        "hang-tags that the attacker may flip.</p>"
        f'<div class="strip">{loop_strip()}</div>'
        "<p class='small'>Ties between rules go red, then round, then striped. Each player defends once; "
        "the better deployment score wins.</p></section>"
        '<section><h3>A printed game, not only a script</h3>'
        f'<div class="strip">{"".join(f"<div>{s}</div>" for s in printed_cards())}</div>'
        "<p class='small'>Moon-colony art generated from code; a fixed-deck edition with truth and reference "
        "cards needs no per-game printing.</p></section>")

    col2 = (
        '<section><h2><span class="n">3</span>The learner</h2>'
        f'<div class="strip cards3" style="grid-template-columns:repeat(3,1fr)">'
        f'{"".join(f"<div>{card_svg(rule_card(i, r))}</div>" for i, r in enumerate(RULES))}</div>'
        "<p>The robot learns one rule: the one with the <b>fewest errors</b> against the current tags. "
        "A wrong rule scores 4/8 on the deployment deck, the true rule 8/8.</p></section>"
        '<section><h2><span class="n">4</span>Threat model</h2><table>'
        + "".join(f"<tr><th>{escape(a)}</th><td>{escape(b)}</td></tr>" for a, b in threat)
        + "</table></section>"
        '<section><h3>Two audit policies</h3><ul>'
        "<li><b>Random:</b> check any unchecked card.</li>"
        "<li><b>Conflict:</b> check a card whose identical look-alikes carry the other label, contradictions "
        "of verified cards first; recompute after each check.</li></ul>"
        '<h3>Method</h3>'
        f"<p>Protocol v{meta['protocol']} frozen before the run: {len(meta['seeds'])} main seeds × 2 regimes × "
        f"2 attacks × 5 flip budgets × 3 audit budgets = {meta['rows']:,} runs, each policy facing the same "
        f"poisoned labels. 95% percentile bootstrap over seeds.</p>"
        "</section>")

    col3 = (
        '<section><h2><span class="n">5</span>Results</h2>'
        f'<div class="hero"><b>+{100 * p["mean"]:.1f}</b><span>points of deployment accuracy, conflict over '
        f"random auditing</span></div>"
        f"<p class='small'>95% CI {100 * p['ci95'][0]:+.1f} to {100 * p['ci95'][1]:+.1f} · primary cell: correlated "
        f"decks, directed attack, 4 flips, 4 audits, {h['n_seeds']} seeds</p>"
        f'<div class="tiles"><div class="tile"><b>{d["conflict"]["restored_true_rule"]} vs '
        f'{d["random"]["restored_true_rule"]}</b><span>of {switched} poisoned rounds restored, conflict vs '
        f'random</span></div>'
        f'<div class="tile"><b>{d["conflict"]["corruption_found_per_seed"]:.2f} vs '
        f'{d["random"]["corruption_found_per_seed"]:.2f}</b><span>poisoned labels found per four audits</span></div>'
        f'<div class="tile"><b>{p["wins"]} · {p["ties"]} · {p["losses"]}</b><span>seeds won, tied and lost by '
        f"conflict auditing</span></div></div>"
        + local_figure("primary-accuracy.svg", "Correlated decks, directed attack, four audits: once any labels are "
                       "flipped, conflict auditing keeps the highest accuracy.", "Final accuracy against attack ceiling")
        + local_figure("conditions.svg", "With 4 flips and 4 audits, the mean difference is never negative; the "
                       "edge is largest where the attack bites hardest.", "Paired difference by condition")
        + "</section>")

    col4 = (
        '<section><h2><span class="n">6</span>Where it fails</h2>'
        f"<p>Conflict auditing needs a visible disagreement. The {switched} poisoned rounds, split "
        "(exploratory):</p><table>"
        '<tr><th>After the attack</th><th class="num">Rounds</th><th class="num">Conflict</th>'
        '<th class="num">Random</th></tr>'
        f'<tr><td>Look-alikes disagree</td><td class="num">{vis["switched_seeds"]}</td>'
        f'<td class="num">{pct(vis["conflict_restored"], vis["switched_seeds"])}</td>'
        f'<td class="num">{pct(vis["random_restored"], vis["switched_seeds"])}</td></tr>'
        f'<tr><td>No disagreement left</td><td class="num">{hid["switched_seeds"]}</td>'
        f'<td class="num">{pct(hid["conflict_restored"], hid["switched_seeds"])}</td>'
        f'<td class="num">{pct(hid["random_restored"], hid["switched_seeds"])}</td></tr></table>'
        + local_figure("failure-case.svg",
                       f"Seed {h['trace_seed']}: every flipped tag sits in a look-alike group with no dissent, so "
                       "conflict auditing had no signal and checked four correct cards.",
                       f"Audit trace for seed {h['trace_seed']}")
        + "</section>"
        '<section><h2><span class="n">7</span>Limits</h2><ul class="small">'
        "<li>Three rules, 24 cards, a perfect oracle at uniform cost.</li>"
        "<li>A heuristic attacker that ignores the defense; flipping whole look-alike groups could erase "
        "much of the edge.</li>"
        "<li>Simulated policies, not measured human play.</li></ul></section>"
        '<section><h2>Play it, rerun it</h2>'
        f'<p class="url">{escape(URL.split("/")[0])}/{escape(URL.split("/")[1])}/<br>{escape(URL.split("/")[2])}</p>'
        "<p class='small'><code>python3 -m poisoned_dataset play</code><br>No installs, Python 3.10+. Kit, "
        "rulebook, box, raw results and figure sources are in the repository.</p>"
        "<p class='refs'>Vassilev et al., <i>Adversarial Machine Learning: A Taxonomy and Terminology</i>, "
        "NIST AI 100-2e2025. Jha, Hayase and Oh, <i>Label Poisoning is All You Need</i>, NeurIPS 2023.</p>"
        "</section>")

    body = (f'<div class="poster"><svg class="backdrop" viewBox="0 0 {width * 100:g} {height * 100:g}" aria-hidden="true">'
            f'<rect width="100%" height="100%" fill="{C["paper"]}"/>'
            f'{art.grain(art.box(width * 100, height * 100), "poster", .3)}</svg>'
            f'{header}<div class="columns"><div class="col">{col1}</div><div class="col">{col2}</div>'
            f'<div class="col">{col3}</div><div class="col">{col4}</div></div>'
            f'<footer><span>POISONED DATASET · DRAFT 0.1 · APACHE 2.0</span>'
            f'<span>Protocol v{meta["protocol"]} · commit {meta["git"]["commit"][:7]} · generated from the '
            f"repository</span></footer></div>")
    style = STYLE.replace("WIDTH", f"{width:g}").replace("HEIGHT", f"{height:g}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Poisoned Dataset poster</title>'
            f"<style>{style}</style></head><body>{art.defs()}{body}</body></html>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Poisoned Dataset poster")
    parser.add_argument("--width", type=float, default=36, help="Poster width in inches")
    parser.add_argument("--height", type=float, default=24, help="Poster height in inches")
    parser.add_argument("--out", type=Path, default=HERE / "poster.html")
    args = parser.parse_args()
    (HERE / "figures").mkdir(exist_ok=True)
    for name, markup in figures().items():
        (HERE / "figures" / name).write_text(markup, encoding="utf-8")
    args.out.write_text(build(args.width, args.height), encoding="utf-8")
    print(f"Wrote {args.out} and presentation/figures/")


if __name__ == "__main__":
    main()
