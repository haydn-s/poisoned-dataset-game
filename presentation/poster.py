"""Build the 36 x 24 in game and teaching poster from the project's own art.

Run from the repository root: python3 presentation/poster.py
The small simulation panel reads frozen evaluation results; classroom activities
are proposed uses, not claims of measured learning gains.
"""

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from poisoned_dataset import art  # noqa: E402
from poisoned_dataset.art import C, INK  # noqa: E402
from poisoned_dataset.components import cargo_card  # noqa: E402
from poisoned_dataset.core import Card  # noqa: E402

RESULTS = ROOT / "results" / "evaluation-v1.0"
AUTHOR = "D. Haydn Stucker"
COURSE = "AIPI 590 · Explainable AI · Duke University · Fall 2026"
URL = "github.com/haydn-s/poisoned-dataset-game"

STYLE = """
@page { size: WIDTHin HEIGHTin; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; color: #2a1c14; font-family: 'Inter', system-ui, sans-serif; background: #8a8178; }
.poster { position: relative; width: WIDTHin; height: HEIGHTin; overflow: hidden; margin: 0 auto; background: #f3e8d0; }
.backdrop { position: absolute; inset: 0; width: 100%; height: 100%; }
header { position: absolute; inset: 0 0 auto; height: 3.7in; }
header .logo { position: absolute; left: .55in; top: .2in; width: 8in; }
header .scene { position: absolute; right: 0; top: 0; width: 5.55in; height: 3.7in; }
header .titles { position: absolute; left: 9.25in; right: 5.85in; top: .43in; }
h1 { font: 900 57pt/1.04 'Inter Display', 'Inter', sans-serif; margin: 0 0 .15in; }
.subtitle { font: 650 30pt/1.2 'Inter', sans-serif; margin: 0 0 .18in; }
.byline { font: 600 23pt/1.2 'Inter', sans-serif; margin: 0; }
.columns { position: absolute; left: .55in; right: .55in; top: 4.05in; bottom: 1.15in;
           display: grid; grid-template-columns: 1fr 1.14fr 1fr; gap: .42in; }
.col { display: flex; flex-direction: column; gap: .3in; min-height: 0; }
.col > :last-child { flex: 1; }
section, aside { background: #fffaf0; border: 4px solid #2a1c14; border-radius: .22in; padding: .3in .34in; }
h2 { font: 900 38pt/1.08 'Inter Display', 'Inter', sans-serif; margin: 0 0 .18in; }
h3 { font: 800 27pt/1.15 'Inter', sans-serif; margin: 0 0 .06in; }
p, li { font-size: 23pt; line-height: 1.3; margin: 0; }
p + p { margin-top: .12in; }
.lead { font-size: 25pt; line-height: 1.26; }
.small { font-size: 19pt; line-height: 1.28; }
.kicker { font: 800 18pt/1.1 'Inter', sans-serif; letter-spacing: .08em; text-transform: uppercase; margin: 0 0 .12in; }
.roles { display: grid; grid-template-columns: 1fr 1fr; gap: .22in; margin: .18in 0; }
.role { border: 2px solid #c9b48a; border-radius: .14in; padding: .12in .18in .18in; background: #f3e8d0; text-align: center; }
.role > svg { display: block; height: 2.4in; width: 100%; }
.role h3 { font-size: 29pt; }
.role p { font-size: 21pt; line-height: 1.22; }
.facts { display: grid; grid-template-columns: repeat(3, 1fr); border-top: 2px solid #c9b48a; padding-top: .15in; gap: .16in; }
.facts b { font: 900 34pt/1 'Inter', sans-serif; display: block; }
.facts span { font-size: 20pt; display: block; margin-top: .05in; }
.steps { list-style: none; margin: .08in 0 0; padding: 0; display: flex; flex-direction: column; gap: .17in; }
.steps li { display: grid; grid-template-columns: .65in 1fr; gap: .18in; }
.step-number { width: .62in; height: .62in; border: 2px solid #2a1c14; border-radius: 50%; background: #e2ad35;
               font: 900 28pt/.57in 'Inter', sans-serif; text-align: center; }
.steps h3 { font-size: 28pt; }
.steps p { font-size: 22pt; }
.round { display: flex; flex-direction: column; }
.round .rule-note { margin-top: auto; padding-top: .24in; }
.rule-note { font-size: 21pt; line-height: 1.28; }
.rule-note b { color: #346e60; }
.tabletop { background: #153e35; color: #fff7e5; padding: .3in .36in; }
.tabletop .kicker { color: #edc36c; }
.tabletop h2 { font-size: 41pt; }
.tabletop .lead { font-size: 24pt; }
.example-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: .2in; margin: .32in .12in .25in; }
.example-cards > div > svg { display: block; width: 100%; height: auto; }
.example-cards > div:nth-child(1) { transform: rotate(-3deg); }
.example-cards > div:nth-child(3) { transform: rotate(3deg); }
.audit-budget { display: flex; align-items: center; gap: .22in; margin: .14in 0 .18in; }
.tokens { display: flex; gap: .08in; flex: none; }
.tokens > svg { width: .72in; height: .82in; }
.audit-budget p { font-size: 23pt; line-height: 1.22; }
.discussion { border-top: 2px solid #e6d4ac66; padding-top: .16in; font-size: 23pt; }
.model { display: flex; flex-direction: column; }
.rules { display: grid; grid-template-columns: repeat(3, 1fr); gap: .16in; margin: .16in 0; }
.rule { background: #f3e8d0; border: 2px solid #c9b48a; border-radius: .12in; padding: .15in; }
.rule b { display: block; font: 900 28pt/1.1 'Inter', sans-serif; }
.rule span { display: block; font-size: 19pt; line-height: 1.2; margin-top: .06in; }
figure { margin: .16in 0 0; }
.shot-crop { position: relative; width: 100%; aspect-ratio: 5.7; overflow: hidden;
             border: 3px solid #2a1c14; border-radius: .1in; background: #16342b; }
.shot-crop img { position: absolute; width: 160%; max-width: none; left: -9.5%; top: -107%; }
figcaption { font-size: 18pt; line-height: 1.25; margin-top: .1in; }
.model .key-point { margin-top: auto; padding-top: .18in; font-size: 23pt; font-weight: 650; }
.objectives { display: grid; gap: .18in; }
.objectives > div { border-left: 6px solid #e2ad35; padding-left: .16in; }
.objectives h3 { font-size: 26pt; }
.objectives p { font-size: 22pt; }
.lesson { background: #f6edda; }
.lesson > p { font-size: 21pt; }
.lesson ol { margin: .16in 0 .16in; padding-left: .35in; }
.lesson li { font-size: 21pt; margin: 0 0 .12in; padding-left: .04in; }
.lesson .debrief { border-top: 2px solid #c9b48a; padding-top: .12in; font-size: 21pt; font-weight: 600; }
.evidence { border-color: #9d8b66; background: #efe7d5; }
.evidence h2 { font-size: 25pt; margin-bottom: .12in; }
.evidence p { font-size: 18pt; line-height: 1.25; }
.evidence .scope { margin-top: .12in; font-weight: 700; }
.access h2 { font-size: 31pt; }
.qrrow { display: flex; align-items: center; gap: .22in; }
.qrrow img { width: 1.6in; height: 1.6in; flex: none; }
.url { font: 900 25pt/1.16 'Inter', sans-serif; margin-bottom: .1in; }
.access .small { font-size: 19pt; }
footer { position: absolute; left: .55in; right: .55in; bottom: .24in; }
footer .line { display: flex; justify-content: space-between; font: 800 16pt/1.2 'Inter', sans-serif; margin-bottom: .12in; }
footer .refs { font: 400 13pt/1.25 'Inter', sans-serif; }
@media print { body { background: none; } }
"""


def svg(view: str, body: str, description: str) -> str:
    return f'<svg viewBox="{view}" role="img" aria-label="{escape(description)}">{body}</svg>'


def labeled_card(card: Card, tag: str) -> str:
    """Show a real cargo card with its separate label tag in the tag slot."""
    markup = cargo_card(card, 1, chip=("EXAMPLE", C["mustard"], INK)).replace('<svg class="card"', '<svg', 1)
    overlay = f'<g transform="translate(45 270)">{art.tag(tag, 160, 55, f"poster-{card.id}")}</g>'
    return markup.rsplit("</svg>", 1)[0] + overlay + "</svg>"


def role_scene(attacker: bool) -> str:
    if attacker:
        body = f'<g transform="translate(45 32) scale(.65)">{art.mallory("poster-role")}</g>'
    else:
        body = f'<g transform="translate(30 44) scale(.85)">{art.sorter("poster-role")}</g>'
    return svg("0 0 220 220", body, "Mallory, the attacker" if attacker else "Sorter, the defender’s robot")


def percentage(value: float) -> str:
    return f'{(Decimal(str(value)) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)}%'


def build(width: float = 36, height: float = 24) -> str:
    headline = json.loads((RESULTS / "report" / "headline.json").read_text())
    paired, defenses = headline["paired_difference"], headline["defenses"]

    header = (
        '<header><svg class="backdrop" viewBox="0 0 3600 500" preserveAspectRatio="none" aria-hidden="true">'
        '<rect width="3600" height="500" fill="url(#shop)"/>'
        f'<path d="M0 470H3600V500H0Z" fill="{C["mustard"]}"/>'
        + art.hatch(art.poly((0, 470), (3600, 470), (3600, 500), (0, 500)), INK, 30, 15, 45, "band")
        + '</svg><svg class="scene" viewBox="0 0 900 600" role="img" aria-label="Robots in a moon-colony warehouse">'
        + art.cover_scene("poster") + '</svg>'
        + f'<svg class="logo" viewBox="0 0 660 270" role="img" aria-label="Poisoned Dataset">{art.logo()}</svg>'
        + '<div class="titles"><h1>Play the attack.<br>Explain the defense.</h1>'
        '<p class="subtitle">A hands-on game for teaching data poisoning &amp; explainable AI</p>'
        f'<p class="byline"><b>{escape(AUTHOR)}</b> · {escape(COURSE)}</p></div></header>'
    )

    roles = (
        '<div class="roles"><div class="role">' + role_scene(True)
        + '<h3>Attacker</h3><p>Secretly change labels.<br>Teach the robot the wrong rule.</p></div>'
        '<div class="role">' + role_scene(False)
        + '<h3>Defender</h3><p>Choose which labels to verify.<br>Protect the robot’s training data.</p></div></div>'
    )
    steps = (
        ("Poison", "The attacker knows the truth and flips up to four labels before the defender looks."),
        ("Inspect", "Compare cargo features, current labels and each rule’s error count. Looking is free."),
        ("Audit", "Spend one of four tokens to reveal and repair one card’s label. Recount the errors."),
        ("Lock & test", "Lock the lowest-error rule, then score its predictions on eight unseen cargo cards."),
        ("Reveal & swap", "Explain the result, switch roles and play a second round. Compare defender scores."),
    )
    step_list = ''.join(
        f'<li><span class="step-number">{number}</span><div><h3>{escape(title)}</h3><p>{escape(text)}</p></div></li>'
        for number, (title, text) in enumerate(steps, 1)
    )
    col1 = (
        '<section><p class="kicker">The game</p><h2>Two players. One robot.<br>A question of trust.</h2>'
        '<p class="lead">Rival crews train a moon-colony supply robot. One sabotages its data; '
        'the other has just four checks to defend it.</p>'
        + roles
        + '<div class="facts"><div><b>2</b><span>players</span></div><div><b>2</b><span>rounds; swap roles</span></div>'
        '<div><b>24</b><span>training cards / round</span></div></div></section>'
        '<section class="round"><h2>How a round unfolds</h2>'
        f'<ol class="steps">{step_list}</ol>'
        '<p class="rule-note"><b>Every check costs a token.</b> It verifies only the chosen card, '
        'even when several cards look identical.</p></section>'
    )

    examples = (
        (Card("A", 1, 0, 0), "STORE"),
        (Card("B", 1, 0, 0), "RECYCLE"),
        (Card("C", 0, 1, 1), "STORE"),
    )
    hand = ''.join(f'<div>{labeled_card(card, tag)}</div>' for card, tag in examples)
    tokens = ''.join(svg("0 0 90 100", f'<g transform="translate(45 50)">{art.hexbolt("AUDIT", 43, i)}</g>',
                         f"Audit token {i}") for i in range(1, 5))
    rules = ''.join(f'<div class="rule"><b>{name}</b><span>STORE if {name.lower()};<br>otherwise RECYCLE</span></div>'
                    for name in ("RED", "ROUND", "STRIPED"))
    col2 = (
        '<section class="tabletop"><p class="kicker">Try a decision</p><h2>Which label would you check?</h2>'
        '<p class="lead">Three example cards from a 24-card training deck.</p>'
        f'<div class="example-cards">{hand}</div>'
        f'<div class="audit-budget"><div class="tokens">{tokens}</div>'
        '<p><b>Four checks.</b> One trusted label per token.<br>Explain your choice before the reveal.</p></div>'
        '<p class="discussion">A and B have identical features but different labels. '
        '<b>At least one is wrong. What evidence would tell you which?</b></p></section>'
        '<section class="model"><h2>Make the robot’s reasoning visible</h2>'
        '<p>The robot chooses from three simple rules. Count each rule’s mistakes against the current labels; '
        '<b>the rule with the fewest errors wins.</b></p>'
        f'<div class="rules">{rules}</div>'
        '<figure><div class="shot-crop"><img src="images/game-room.jpg" '
        'alt="Online game showing the RED, ROUND and STRIPED rule-error counts and the selected rule">'
        '</div><figcaption>The online game updates error counts after each audit. '
        'The printed edition makes the same process tangible with cards, tags and tokens.</figcaption></figure>'
        '<p class="key-point">Did fixing that label change the winning rule? '
        'Use the error counts to explain why.</p></section>'
    )

    objectives = (
        ("Data integrity", "Changing labels can change what the robot learns, even when the cargo stays the same."),
        ("Explainability", "Visible rules and error counts let players trace why the robot chooses a rule."),
        ("Limited oversight", "Four checks force players to justify where they spend their verification budget."),
        ("Generalization", "Testing on unseen cargo separates fitting the training labels from getting the task right."),
    )
    objectives_html = ''.join(f'<div><h3>{escape(title)}</h3><p>{escape(text)}</p></div>' for title, text in objectives)
    col3 = (
        '<section><p class="kicker">Teaching opportunities</p><h2>What players can explore</h2>'
        f'<div class="objectives">{objectives_html}</div></section>'
        '<section class="lesson"><h2>Bring it into a lesson</h2>'
        '<p><b>Suggested session:</b> about 30 minutes for introduction, play and discussion. '
        'Designed for learners new to machine learning.</p>'
        '<ol><li><b>Introduce:</b> separate features, labels and predictions with one cargo card.</li>'
        '<li><b>Play &amp; swap:</b> ask each player to explain an audit choice before the reveal.</li>'
        '<li><b>Debrief:</b> trace how a changed label affected the selected rule.</li></ol>'
        '<p class="debrief">Discussion challenge: could every look-alike label agree and still be wrong?</p></section>'
        '<aside class="evidence"><h2>Supporting evidence: simulation</h2>'
        f'<p>In {headline["n_seeds"]} paired simulated decks, checking conflicting labels reached '
        f'<b>{percentage(defenses["conflict"]["final_accuracy"])}</b> accuracy versus '
        f'<b>{percentage(defenses["random"]["final_accuracy"])}</b> for random checks '
        f'(+{100 * paired["mean"]:.1f} percentage points; 95% CI '
        f'{100 * paired["ci95"][0]:+.1f} to {100 * paired["ci95"][1]:+.1f}).</p>'
        '<p>Correlated decks, directed attacks, up to four flips and four audits. '
        'Consistently poisoned groups can hide the disagreement signal.</p>'
        '<p class="scope">These are automated policies. Learning gains and classroom timing have not been measured.</p></aside>'
        '<section class="access"><h2>Play it. Teach with it.</h2><div class="qrrow">'
        f'<img src="images/qr-repo.svg" alt="QR code for {escape(URL)}"><div>'
        f'<p class="url">github.com/haydn-s/<br>poisoned-dataset-game</p>'
        '<p class="small">Print kit · online setup<br>Playtest guide · code &amp; results</p></div></div></section>'
    )

    body = (
        f'<div class="poster"><svg class="backdrop" viewBox="0 0 {width * 100:g} {height * 100:g}" aria-hidden="true">'
        '<rect width="100%" height="100%" fill="#f3e8d0"/>'
        + art.grain(art.box(width * 100, height * 100), "poster", .3) + '</svg>'
        + header + f'<div class="columns"><div class="col">{col1}</div><div class="col">{col2}</div>'
        f'<div class="col">{col3}</div></div>'
        '<footer><div class="line"><span>POISONED DATASET · AIPI 590 · APACHE 2.0</span>'
        '<span>PRINTABLE + DIGITAL · LEARN THROUGH PLAY, EXPLAIN THROUGH DISCUSSION</span></div>'
        '<p class="refs">Related work: Vassilev et al., <i>Adversarial Machine Learning: A Taxonomy and Terminology</i>, '
        'NIST AI 100-2e2025. Jha, Hayase and Oh, <i>Label Poisoning is All You Need</i>, NeurIPS 2023. '
        'Simulation: protocol v1.0; full methods and results in the repository.</p></footer></div>'
    )
    style = STYLE.replace("WIDTH", f"{width:g}").replace("HEIGHT", f"{height:g}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Poisoned Dataset teaching poster</title>'
            f'<style>{style}</style></head><body>{art.defs(include_cover=True)}{body}</body></html>\n')


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Poisoned Dataset teaching poster")
    parser.add_argument("--width", type=float, default=36, help="Poster width in inches")
    parser.add_argument("--height", type=float, default=24, help="Poster height in inches")
    parser.add_argument("--out", type=Path, default=HERE / "poster.html")
    args = parser.parse_args()
    args.out.write_text(build(args.width, args.height), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
