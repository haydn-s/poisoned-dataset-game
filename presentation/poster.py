"""Build the 36 x 24 in poster from the committed results and the game's own art.

Run from the repository root:  python3 presentation/poster.py
Evaluation numbers and charts come from results/evaluation-v1.0. Conceptual
audit illustrations use the same cargo icons as the game.
"""

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from poisoned_dataset import art, report  # noqa: E402
from poisoned_dataset.art import C, INK  # noqa: E402
from poisoned_dataset.components import cargo_card, rule_card  # noqa: E402
from poisoned_dataset.core import LABELS, RULES, Card, flip_labels, generate  # noqa: E402
from poisoned_dataset.report import PRIMARY, label, marker  # noqa: E402

RESULTS = ROOT / "results" / "evaluation-v1.0"
AUTHOR = "D. Haydn Stucker"
COURSE = "AIPI 590 · Explainable AI · Duke University · Fall 2026"
URL = "github.com/haydn-s/poisoned-dataset-game"

STYLE = """
@page { size: WIDTHin HEIGHTin; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #8a8178; color: #2a1c14; font-family: 'Inter', system-ui, sans-serif; }
.poster { width: WIDTHin; height: HEIGHTin; position: relative; overflow: hidden; background: #f3e8d0;
          margin: 0 auto; }
.backdrop { position: absolute; inset: 0; width: 100%; height: 100%; }
header { position: absolute; left: 0; right: 0; top: 0; height: 3.65in; }
header .scene { position: absolute; right: 0; top: 0; width: 5.475in; height: 3.65in; }
header .logo { position: absolute; left: .55in; top: .2in; width: 8in; }
header .titles { position: absolute; left: 9.25in; right: 5.8in; top: .6in; }
h1 { font: 900 62pt/1.05 'Inter Display', 'Inter', sans-serif; margin: 0 0 .16in; }
.subtitle { font: 700 35pt/1.2 'Inter', sans-serif; margin: 0 0 .24in; }
.byline { font: 600 26pt/1.3 'Inter', sans-serif; margin: 0; }
.byline b { font-weight: 800; }
.columns { position: absolute; left: .55in; right: .55in; top: 4in; bottom: .95in; display: grid;
           grid-template-columns: repeat(4, 1fr); gap: .45in; }
.col { display: flex; flex-direction: column; gap: .28in; min-height: 0; }
.col > section:last-child { flex: 1; }
section { background: #fffaf0; border: 4px solid #2a1c14; border-radius: .22in; padding: .25in .32in; }
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
.hero { display: flex; align-items: center; gap: .2in; margin: .05in 0 .12in; }
.hero b { font: 900 98pt/1 'Inter Display', 'Inter', sans-serif; }
.hero span { font: 700 25pt/1.2 'Inter', sans-serif; }
.comparison { display: flex; gap: .22in; align-items: center; margin: .12in 0; }
.comparison div { flex: 1; border-left: 6px solid #2a78d6; padding-left: .15in; }
.comparison div:last-child { border-color: #eb6834; }
.comparison b { display: block; font: 900 42pt/1.05 'Inter Display', 'Inter', sans-serif; }
.comparison span { display: block; font-size: 20pt; margin-top: .06in; }
.tiles { display: grid; grid-template-columns: repeat(2, 1fr); gap: .16in; margin: .14in 0; }
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
.cards3 { width: 94%; margin: 0 auto .1in; }
.shot-crop { position: relative; width: 100%; aspect-ratio: 1.9; overflow: hidden;
             border: 3px solid #2a1c14; border-radius: .1in; background: #16342b; }
.shot-crop img { position: absolute; width: 160%; max-width: none; left: -9.5%; top: -30%; }
.learner { display: flex; flex-direction: column; }
.learner .refs { margin-top: auto; padding-top: .2in; }
.key-point { border-left: 6px solid #e2ad35; padding-left: .14in; margin-top: .14in; }
.restoration th, .restoration td { font-size: 19pt; }
.restoration caption { text-align: left; font-size: 19pt; font-weight: 800; margin-bottom: .06in; }
.figure-heading { font: 800 24pt/1.2 'Inter', sans-serif; margin: .18in 0 .06in; }
.qrrow { display: flex; gap: .25in; align-items: center; margin: .06in 0 .12in; }
.qrrow img { width: 1.8in; height: 1.8in; flex: none; border: 3px solid #2a1c14; border-radius: .08in; }
.qrrow .url { margin: 0 0 .08in; }
.takeaway { font-size: 22pt; font-weight: 600; line-height: 1.28; margin-bottom: .14in; }
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
    x0, y0, w, h = 62, 88, 324, 190
    xmap = lambda k: x0 + budgets.index(k) * w / (len(budgets) - 1)
    ymap = lambda v: y0 + h - (v - .5) / .5 * h
    primary_x = xmap(PRIMARY["attack_budget"])
    body = [f'<rect x="{primary_x - 14}" y="{y0}" width="28" height="{h}" fill="#e2ad35" opacity=".25"/>',
            f'<path d="M{primary_x} {y0}V{y0 + h}" stroke="#9b721c" stroke-dasharray="4 4"/>',
            label(primary_x, y0 - 12, "Headline condition", "ink", 12, "middle", 700),
            f'<text class="ink2" font-size="13" text-anchor="middle" '
            f'transform="translate(17 {y0 + h / 2}) rotate(-90)">Deployment accuracy (%)</text>']
    for v in (.5, .6, .7, .8, .9, 1.0):
        body.append(f'<path class="grid" d="M{x0} {ymap(v):.1f}H{x0 + w}" stroke-width="1"/>'
                    + label(x0 - 8, ymap(v) + 4, f"{100 * v:.0f}", "ink2", 12, "end"))
    for k in budgets:
        body.append(label(xmap(k), y0 + h + 19, str(k), "ink2", 12, "middle", 700 if k == 4 else 400))
    body.append(label(x0 + w / 2, y0 + h + 40, "Attack ceiling (maximum label flips)", "ink2", 12, "middle"))
    body.append(f'<path class="l-clean" d="M{x0} {ymap(1):.1f}H{x0 + w}" stroke-width="1" stroke-dasharray="3 3"/>')
    for key, name in report.DEFENSES:
        pts = [(xmap(k), ymap(mean(means[(k, key)])), k, mean(means[(k, key)])) for k in budgets]
        body.append(f'<polyline class="l-{key}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts)}" '
                    f'stroke-width="2" stroke-linejoin="round"/>')
        body.extend(marker(key, x, y, f"{name}, k = {k}: {v:.3f}") for x, y, k, v in pts)
    for n, (key, name) in enumerate(report.DEFENSES):
        lx, ly = 62 + (n % 2) * 172, 22 + (n // 2) * 24
        body.append(f'<path class="l-{key}" d="M{lx} {ly}h18" stroke-width="2"/>' + marker(key, lx + 9, ly, name)
                    + label(lx + 24, ly + 4, name, "ink2", 12))
    body.append('<path class="l-clean" d="M234 46h18" stroke-width="1" stroke-dasharray="3 3"/>'
                + label(258, 50, "Clean labels", "ink2", 12))
    return report.svg(420, 330, "".join(body), "Final accuracy against attack ceiling, correlated decks, "
                                                  "directed attack, four audits")


def conditions(comparisons: list[dict]) -> str:
    """Conflict minus random, k = 4 and a = 4, for all four regime and attack conditions."""
    x0, w = 150, 220
    xmap = lambda v: x0 + (v + 5) / 30 * w
    body = [label(410, 20, "Points: means · bars: 95% CI", "ink2", 12, "end"),
            label(x0 + w / 2, 214, "Accuracy gain (percentage points)", "ink2", 12, "middle")]
    for v in (-5, 0, 5, 10, 15, 20, 25):
        body.append(f'<path class="{"axis" if v == 0 else "grid"}" d="M{xmap(v):.1f} 32V182" stroke-width="1"/>'
                    + label(xmap(v), 196, f"{v:+d}" if v else "0", "ink2", 12, "middle"))
    for n, (regime, attack) in enumerate(report.PANELS):
        c = report.cell(comparisons, regime=regime, attack=attack, attack_budget=4, audit_budget=4)[0]
        m, lo, hi = (100 * float(c[k]) for k in ("mean_conflict_minus_random", "ci95_low", "ci95_high"))
        y = 50 + n * 40
        primary = (regime, attack) == (PRIMARY["regime"], PRIMARY["attack"])
        body.append(label(x0 - 10, y + 4, f"{regime} · {attack}", "ink" if primary else "ink2", 12, "end",
                          700 if primary else 400)
                    + f'<path class="l-conflict" d="M{xmap(lo):.1f} {y}H{xmap(hi):.1f}" stroke-width="2.5" '
                      f'stroke-linecap="round"/>'
                    + marker("conflict", xmap(m), y, f"{regime} {attack}: {m:+.1f} ({lo:+.1f} to {hi:+.1f})")
                    + label(xmap(hi) + 8, y + 4, f"{m:+.1f}", "ink2", 12))
    return report.svg(420, 226, "".join(body), "Conflict minus random accuracy by condition at up to four flips and "
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


def cargo_tag(x: int, y: int, tag: str, *, width: int = 186, height: int = 56,
              poisoned: bool = False, verified: bool = False) -> str:
    """Identical cargo with a separate, editable label for the audit illustrations."""
    border = "#d03b3b" if poisoned else "#347769" if verified else INK
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="7" '
            f'fill="#f3e8d0" stroke="{border}" stroke-width="2"/>'
            f'<g transform="translate({x + 26} {y + height / 2})">{art.cargo_icon(1, 0, 0, 25)}</g>'
            + label(x + 51, y + height / 2 + 5, tag, "ink", 15, weight=700))


def audit_example() -> str:
    body = [label(12, 22, "Same features. Different labels.", "ink", 15, weight=700),
            cargo_tag(12, 36, "STORE"), cargo_tag(222, 36, "RECYCLE"),
            label(210, 116, "Trusted check: the first label should be RECYCLE.", "ink2", 12, "middle"),
            '<path d="M210 125v18m-6-6 6 6 6-6" fill="none" stroke="#347769" stroke-width="3"/>',
            cargo_tag(12, 153, "RECYCLE", verified=True), cargo_tag(222, 153, "RECYCLE"),
            label(210, 234, "Repair one label, then recount the rule errors.", "ink", 13, "middle", 700)]
    return report.svg(420, 246, "".join(body), "Two identical red, square, plain cargo cards disagree. A trusted "
                      "audit corrects the first card from STORE to RECYCLE; the second stays RECYCLE.")


def failure_mechanism() -> str:
    body = []
    for x, hidden in ((12, False), (222, True)):
        body.extend([label(x + 93, 22, "Labels agree" if hidden else "Labels disagree", "ink", 14, "middle", 700),
                     cargo_tag(x, 34, "STORE", height=38, poisoned=True),
                     cargo_tag(x, 81, "STORE" if hidden else "RECYCLE", height=38, poisoned=hidden),
                     label(x + 93, 143, "No initial signal" if hidden else "Useful audit signal", "ink", 13,
                           "middle", 700)])
    body.append(label(210, 169, "Red outlines: poisoned labels. True label: RECYCLE.", "ink2", 12, "middle"))
    return report.svg(420, 182, "".join(body), "Identical cargo with conflicting labels provides an audit signal. "
                      "Consistently poisoned identical cargo agrees and provides no initial signal.")


def figures() -> dict[str, str]:
    runs, comparisons = report.load(RESULTS)
    seed = json.loads((RESULTS / "report" / "headline.json").read_text())["trace_seed"]
    return {"primary-accuracy.svg": primary_accuracy(runs), "conditions.svg": conditions(comparisons),
            "failure-case.svg": failure_case(runs, seed), "audit-example.svg": audit_example(),
            "failure-mechanism.svg": failure_mechanism()}


def loop_strip() -> str:
    steps = [
        ("Poison: flip up to 4 tags", svg("0 0 250 350", f'<g transform="translate(44 70) scale(.78)">{art.mallory("pp")}</g>', "Mallory")),
        ("Inspect: count errors", card_svg(cargo_card(Card("C07", 1, 1, 1), 1))),
        ("Audit: up to 4 tokens", svg("0 0 250 350", f'<g transform="translate(125 115)">{art.hexbolt("AUDIT", 85, 1)}</g>'
                                     f'<g transform="translate(125 270)">{art.hexbolt("VERIFIED", 70)}</g>',
                      "Audit token flipping to verified")),
        ("Lock: fewest errors", card_svg(rule_card(0, RULES[0]))),
        ("Deploy: 8 new cargo", card_svg(cargo_card(Card("T08", 1, 1, 1), 1, True))),
    ]
    return "".join(f"<div>{s}<span>{escape(t)}</span></div>" for t, s in steps)


def percentage(value: float) -> str:
    """Use decimal half-up rounding for the displayed one-decimal accuracy rates."""
    return f'{(Decimal(str(value)) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)}%'


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
                f'<div class="titles"><h1>Who changed the labels?</h1>'
                f'<p class="subtitle">A tabletop game about data poisoning</p>'
                f'<p class="byline"><b>{escape(AUTHOR)}</b> · {escape(COURSE)}</p></div></header>')

    col1 = (
        '<section><h2><span class="n">1</span>The question</h2>'
        '<p class="lead">With four trusted checks, does auditing <b>conflicting look-alike labels</b> '
        "protect a learner better than random checks?</p>"
        "<p>Poisoned labels can teach the wrong rule. When verification is costly, "
        "which labels should we check?</p></section>"
        '<section><h2><span class="n">2</span>The game</h2>'
        "<p>Two players swap roles. In each 24-card round, the attacker flips up to four "
        "STORE / RECYCLE tags.</p>"
        f'<div class="strip">{loop_strip()}</div>'
        "<p class='small'>Audit, lock the rule, then test on eight held-out cards. Higher deployment "
        "score wins.</p></section>"
        '<section class="learner"><h2><span class="n">3</span>The learner</h2>'
        f'<div class="strip cards3" style="grid-template-columns:repeat(3,1fr)">'
        f'{"".join(f"<div>{card_svg(rule_card(i, r))}</div>" for i, r in enumerate(RULES))}</div>'
        "<p>The robot picks the rule with the <b>fewest errors</b> against current labels. "
        "On eight held-out cards: true rule 8/8; wrong rule 4/8.</p>"
        "<p class='key-point'><b>Explainability in play:</b> visible error counts explain how a corrected "
        "label can change the selected rule.</p>"
        "<p class='refs'>Related work: Vassilev et al., <i>Adversarial Machine Learning: A Taxonomy and "
        "Terminology</i>, NIST AI 100-2e2025. Jha, Hayase and Oh, <i>Label Poisoning is All You Need</i>, "
        "NeurIPS 2023.</p></section>")

    col2 = (
        '<section><h2><span class="n">4</span>What to audit?</h2>'
        '<figure><img src="figures/audit-example.svg" alt="Identical cargo cards with different labels; '
        'one trusted check corrects STORE to RECYCLE"></figure>'
        '<ul><li><b>Random:</b> uniformly check an unchecked card.</li>'
        '<li><b>Conflict:</b> prioritize disagreement among identical cards, especially with verified labels. '
        'Recompute after each check; without conflict, choose randomly.</li></ul></section>'
        '<section><h3>Threat model &amp; experiment</h3>'
        '<p><b>Attacker:</b> knows truth and learner; flips labels once before audits. '
        '<b>Defender:</b> sees features and labels; pays one token per trusted label.</p>'
        '<p><b>Correlated</b> decks link feature values; <b>independent</b> decks sample them separately. '
        '<b>Directed</b> attacks imitate a wrong rule; <b>random</b> attacks flip arbitrary labels.</p>'
        f'<p class="small">{len(meta["seeds"])} paired seeds per condition; three policies on the same attacks '
        f'({meta["rows"]:,} policy runs). Protocol v{meta["protocol"]} frozen before evaluation; '
        '95% bootstrap intervals over seeds.</p></section>'
        '<section><h3>Print it or play on two devices</h3>'
        '<figure class="shot"><div class="shot-crop"><img src="images/game-room.jpg" '
        'alt="Close-up of the online game: each candidate rule’s error count and a verified cargo card">'
        '</div><figcaption>Online error counts update after audits. Also available as a reusable '
        'print edition.</figcaption></figure></section>')

    col3 = (
        '<section><h2><span class="n">5</span>Results</h2>'
        f'<div class="hero"><b>+{100 * p["mean"]:.1f}</b><span>percentage points<br>of deployment accuracy</span></div>'
        '<div class="comparison">'
        f'<div><b>{percentage(d["conflict"]["final_accuracy"])}</b><span>Conflict auditing</span></div>'
        f'<div><b>{percentage(d["random"]["final_accuracy"])}</b><span>Random auditing</span></div></div>'
        f"<p class='small'>95% CI {100 * p['ci95'][0]:+.1f} to {100 * p['ci95'][1]:+.1f} percentage points.<br>"
        f"Primary condition: correlated decks, directed attack, <b>up to 4 flips</b>, 4 audits, {h['n_seeds']} seeds.</p>"
        f'<div class="tiles"><div class="tile"><b>{d["conflict"]["restored_true_rule"]} vs '
        f'{d["random"]["restored_true_rule"]}</b><span>true rules restored<br>(conflict vs random)</span></div>'
        f'<div class="tile"><b>{p["wins"]} · {p["ties"]} · {p["losses"]}</b><span>seeds: conflict wins · ties · '
        f"losses</span></div></div>"
        '<h3 class="figure-heading">As the attack budget grows</h3>'
        + local_figure("primary-accuracy.svg", "Four audits; shaded band marks the headline condition.",
                       "Deployment accuracy (%) against attack ceiling")
        + '<h3 class="figure-heading">Conflict auditing’s advantage</h3>'
        + local_figure("conditions.svg", "Up to four flips, four audits. Exploratory intervals crossing zero "
                       "do not establish an advantage.", "Paired accuracy gain by condition with 95% confidence intervals")
        + "</section>")

    col4 = (
        '<section><h2><span class="n">6</span>Where it fails</h2>'
        '<figure><img src="figures/failure-mechanism.svg" alt="Conflicting labels reveal an audit signal; '
        'consistently poisoned look-alikes provide no initial signal"></figure>'
        f'<table class="restoration"><caption>True-rule restoration (%) · {switched} rules changed by attack</caption>'
        '<tr><th>After attack</th><th class="num">Seeds</th><th class="num">Conflict</th>'
        '<th class="num">Random</th></tr>'
        f'<tr><td>Look-alikes disagree</td><td class="num">{vis["switched_seeds"]}</td>'
        f'<td class="num">{pct(vis["conflict_restored"], vis["switched_seeds"])}</td>'
        f'<td class="num">{pct(vis["random_restored"], vis["switched_seeds"])}</td></tr>'
        f'<tr><td>No disagreement left</td><td class="num">{hid["switched_seeds"]}</td>'
        f'<td class="num">{pct(hid["conflict_restored"], hid["switched_seeds"])}</td>'
        f'<td class="num">{pct(hid["random_restored"], hid["switched_seeds"])}</td></tr></table>'
        '<p class="small">Exploratory split. A random find can reveal a new conflict.</p>'
        + local_figure("failure-case.svg",
                       f"Seed {h['trace_seed']}: no initial conflict. Four clean audits missed the poison; "
                       "random auditing found two flips.",
                       f"Audit trace for seed {h['trace_seed']}")
        + "</section>"
        '<section><h2><span class="n">7</span>What it means</h2>'
        "<p class='takeaway'>Audit disagreement first. Agreement alone does not prove labels are correct.</p>"
        '<ul class="small">'
        "<li>Three rules, 24 cards, a perfect oracle at uniform cost.</li>"
        "<li>The attacker ignores the defense; deliberately hiding conflicts could reduce the advantage.</li>"
        "<li>Simulated policies, not measured human play.</li></ul></section>"
        '<section><h2>Game, rules &amp; results</h2>'
        f'<div class="qrrow"><img src="images/qr-repo.svg" alt="QR code for {escape(URL)}"><div>'
        f'<p class="url">{escape(URL.split("/")[0])}/{escape(URL.split("/")[1])}/<br>{escape(URL.split("/")[2])}</p>'
        "<p class='small'>Scan to get print files, setup instructions, raw results and reproducible figures.</p></div></div>"
        "</section>")

    body = (f'<div class="poster"><svg class="backdrop" viewBox="0 0 {width * 100:g} {height * 100:g}" aria-hidden="true">'
            f'<rect width="100%" height="100%" fill="{C["paper"]}"/>'
            f'{art.grain(art.box(width * 100, height * 100), "poster", .3)}</svg>'
            f'{header}<div class="columns"><div class="col">{col1}</div><div class="col">{col2}</div>'
            f'<div class="col">{col3}</div><div class="col">{col4}</div></div>'
            f'<footer><span>POISONED DATASET · AIPI 590 · APACHE 2.0</span>'
            f'<span>Protocol v{meta["protocol"]} · evaluation commit {meta["git"]["commit"][:7]} · generated from '
            f"the repository</span></footer></div>")
    style = STYLE.replace("WIDTH", f"{width:g}").replace("HEIGHT", f"{height:g}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Poisoned Dataset poster</title>'
            f"<style>{style}</style></head><body>{art.defs(include_cover=True)}{body}</body></html>\n")


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
