"""The printed rulebook: a 12-page half-letter booklet, in reading order and imposed.

Copy follows docs/prototype-rules.md; update both together when the rules change.
"""

import re
from html import escape
from pathlib import Path

from . import art
from .art import C, INK, f, text
from .components import aid_card, back, cargo_card, role_card, rule_card, score_card, slip
from .core import LABELS, RULES, Card, errors, fit, predict

STYLE = """
@page { size: 5.5in 8.5in; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #8a8178; color: #2a1c14; font: 9.6pt/1.4 'Inter', system-ui, sans-serif; }
.page { width: 5.5in; height: 8.5in; position: relative; overflow: hidden; break-after: page;
        margin: .2in auto; box-shadow: 0 2px 10px #0004; }
.page:last-child { break-after: auto; }
.bg { position: absolute; inset: 0; width: 5.5in; height: 8.5in; z-index: 0; }
.content { position: relative; z-index: 1; padding: .48in .45in .6in; }
h1 { font: 900 22pt/1.05 'Inter Display', 'Inter', sans-serif; margin: 0 0 .1in; letter-spacing: .01em; }
h2 { font: 900 11.5pt/1.2 'Inter Display', 'Inter', sans-serif; margin: .16in 0 .04in; letter-spacing: .02em; }
p { margin: 0 0 .08in; }
ol, ul { margin: 0 0 .08in; padding-left: .2in; }
li { margin-bottom: .04in; }
.kicker { font: 800 7.5pt 'Inter', sans-serif; letter-spacing: .14em; text-transform: uppercase; color: #8c2a21; }
.note { border-left: 3px solid #e2ad35; padding: .04in .1in; background: #e2d1ae66; margin: .1in 0; font-size: 8.8pt; }
.folio { position: absolute; z-index: 1; left: .45in; right: .45in; bottom: .28in; display: flex;
         justify-content: space-between; font: 700 6.8pt 'Inter', sans-serif; letter-spacing: .12em; }
.fig { display: block; margin: .06in auto; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .1in .12in; margin-top: .08in; }
.grid figure { margin: 0; text-align: center; font-size: 7.8pt; line-height: 1.25; }
.grid figure svg { display: block; margin: 0 auto .04in; }
.grid b { display: block; font-size: 8.4pt; }
.step { display: grid; grid-template-columns: 1.25in 1fr; gap: .14in; align-items: center; margin: .1in 0 .14in; }
.step h2 { margin-top: 0; }
.num { display: inline-block; width: .24in; height: .24in; border-radius: 50%; background: #e2ad35;
       border: 1.2px solid #2a1c14; text-align: center; font: 900 9pt/.22in 'Inter', sans-serif; margin-right: .05in; }
.dark { color: #f3e8d0; }
.dark .kicker { color: #e2ad35; }
.sheet { width: 11in; height: 8.5in; display: flex; break-after: page; margin: .2in auto; }
.sheet .page { margin: 0; box-shadow: none; }
@media print { body { background: none; } .page, .sheet { margin: 0; box-shadow: none; } }
"""

EXAMPLE = (Card("C01", 1, 0, 0), Card("C02", 0, 1, 0), Card("C03", 1, 1, 1), Card("C04", 0, 0, 1))
EXAMPLE_LABELS = (1, 0, 1, 0)


def bg(fill: str = C["paper"], scene: str = "") -> str:
    return (f'<svg class="bg" viewBox="0 0 550 850" aria-hidden="true"><rect width="550" height="850" fill="{fill}"/>'
            f'{scene}{art.grain(art.box(550, 850), "page", .32)}</svg>')


def fig(w: float, h: float, body: str, label: str, scale: float = 1) -> str:
    return (f'<svg class="fig" viewBox="0 0 {f(w)} {f(h)}" style="width:{w * scale / 100:.2f}in;'
            f'height:{h * scale / 100:.2f}in" role="img" aria-label="{escape(label)}">{body}</svg>')


def nest(card_svg: str, x: float, y: float, w: float) -> str:
    """Place a 250 x 350 card SVG inside another drawing."""
    return re.sub(r'^<svg class="card"', f'<svg x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(w * 1.4)}"',
                  card_svg, count=1)


def folio(n: int, dark: bool = False) -> str:
    return (f'<div class="folio{" dark" if dark else ""}"><span>POISONED DATASET · DRAFT 0.1</span>'
            f'<span>{n}</span></div>')


def page(n: int, body: str, background: str = "", dark: bool = False) -> str:
    return (f'<section class="page" data-page="{n}">{background or bg()}'
            f'<div class="content{" dark" if dark else ""}">{body}</div>{folio(n, dark) if n > 1 else ""}</section>')


def cover() -> str:
    scene = (f'<rect width="550" height="850" fill="url(#shop)"/>'
             f'<g transform="translate(0 480) scale(.6111)">{art.cover_scene("book")}</g>'
             f'<rect y="470" width="550" height="60" fill="url(#fade)"/>'
             f'<g transform="translate(30 60) scale(.76)">{art.logo()}</g>'
             + text(275, 318, "Who changed the labels?", 22, INK, 900)
             + text(275, 346, "A two-player game of data poisoning and scarce audits", 11, INK, 600)
             + text(275, 382, "2 PLAYERS · TARGET 15–20 MINUTES · DRAFT 0.1", 8.5, INK, 800, spacing=1.6))
    return page(1, "", bg(scene=scene))


def mission() -> str:
    held = f'<g transform="translate(176 80) rotate(84)">{art.tag("", 54, 22, "bk", blank=True)}</g>'
    duo = (f'<g transform="translate(0 6) scale(.6)">{art.mallory("book")}</g>'
           f'<g transform="translate(230 70) scale(.78)">{art.sorter("book", holding=held)}</g>')
    body = (
        '<div class="kicker">The story</div><h1>Your mission</h1>'
        "<p>You work for rival companies on a moon colony. The <b>defender</b> trains a supply-sorting robot to "
        "tag cargo <b>STORE</b> or <b>RECYCLE</b>. The <b>attacker</b> secretly changes a few training labels to "
        "make the robot learn the wrong rule.</p>"
        "<p>Play two rounds and switch roles after the first, so each player defends once. The better defender "
        "wins.</p>"
        + fig(460, 230, f'<rect width="460" height="230" rx="10" fill="url(#shop)"/>{duo}'
                        f'{art.grain(art.box(460, 230), "duo", .8)}'
                        f'<rect width="460" height="230" rx="10" fill="none" stroke="{INK}" stroke-width="2"/>',
              "Mallory, the rival robot, eyes the sorter as it tags a crate")
        + "<h2>What the game is about</h2>"
        "<p>Machine-learning systems learn from labelled examples. If someone can change the labels, the system "
        "can learn a rule that looks right on its training data and fails in use. Checking every label is "
        "expensive, so defenders choose which few to verify.</p>"
        '<p class="note">This is a deliberately tiny learner. The game explains label poisoning and trusted '
        "audits; it does not show that any real ML system is robust, and it is not a measured teaching "
        "intervention.</p>")
    return page(2, body)


def components() -> str:
    mini = lambda svg: nest(svg, 0, 0, 92)
    item = lambda w, h, svg, title, note: (f'<figure>{fig(w, h, svg, title)}<b>{escape(title)}</b>'
                                           f'{escape(note)}</figure>')
    hexes = (f'<g transform="translate(46 50)">{art.hexbolt("AUDIT", 40, 1)}</g>'
             f'<g transform="translate(115 50)">{art.hexbolt("VERIFIED", 40)}</g>')
    tags = (f'<g transform="translate(2 8)">{art.tag("STORE", 150, 50, "cpS")}</g>'
            f'<g transform="translate(2 66)">{art.tag("RECYCLE", 150, 50, "cpR")}</g>')
    items = [
        item(92, 129, mini(cargo_card(Card("C07", 1, 1, 1), 1)), "48 training cards", "24 per round, IDs C01–C24"),
        item(92, 129, mini(back("test", 1)), "16 test cards", "8 per round, kept face down"),
        item(92, 129, mini(rule_card(0, RULES[0])), "3 rule cards", "red, round, striped + tie order"),
        item(160, 122, tags, "27 fold-over tags", "STORE one side, RECYCLE the other"),
        item(160, 100, hexes, "4 audit tokens", "AUDIT side, then VERIFIED side"),
        item(92, 129, mini(score_card()), "Score card", "plus 2 quick references"),
        item(92, 129, mini(role_card("ATTACKER")), "2 role cards", "attacker and defender"),
        item(160, 70, f'<g transform="translate(0 9) scale(.485)">{slip(Card("C07", 1, 1, 1), 1, 1)}</g>',
             "48 sealed audit slips", "private; one per training card"),
        item(92, 129, mini(back("training", 1)), "Card backs", "optional duplex print"),
    ]
    body = ('<div class="kicker">In the box</div><h1>Components</h1>'
            "<p>Everything public is printed on the public sheets. The attacker’s private sheets hold the "
            "trusted labels and the sealed deployment keys; keep each round’s private material hidden from "
            "the defender.</p>"
            f'<div class="grid">{"".join(items)}</div>'
            '<p class="note">Also private: one attacker setup panel and one sealed deployment key per round.</p>')
    return page(3, body)


def anatomy() -> str:
    card = nest(cargo_card(Card("C07", 1, 1, 1), 1), 24, 8, 210)
    marks = [(1, 14, 34, "Card ID and round. Audits and scores name cards by ID."),
             (2, 14, 120, "The cargo. Three features: colour, shape and pattern."),
             (3, 14, 205, "The manifest spells out each feature, so colour is never the only cue."),
             (4, 14, 257, "Hang the label tag here. The label is separate from the cargo.")]
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="{C["mustard"]}" stroke="{INK}" stroke-width="1.6"/>'
                   + text(x, y + 4, str(n), 11, INK, 900) for n, x, y, _ in marks)
    notes = "".join(f'<circle cx="246" cy="{f(36 + k * 74)}" r="11" fill="{C["mustard"]}" stroke="{INK}" '
                    f'stroke-width="1.6"/>' + text(246, 40 + k * 74, str(n), 11, INK, 900)
                    + art.para(264, 32 + k * 74, note, 10.2, 190, weight=500)[0]
                    for k, (n, _, _, note) in enumerate(marks))
    flip = (f'<g transform="translate(20 0)">{art.tag("STORE", 150, 50, "anS")}</g>'
            f'<g transform="translate(250 0)">{art.tag("RECYCLE", 150, 50, "anR")}</g>'
            f'<path d="M180 14q35-22 62 0M242 40q-30 22-62 0" fill="none" stroke="{INK}" stroke-width="2.4"/>'
            f'<path d="M236 6l7 8-10 3M186 48l-7-8 10-3" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    body = ('<div class="kicker">Reading the cards</div><h1>Cargo and labels</h1>'
            "<p>Every training card is red or blue, round or square, and striped or plain. Features never "
            "change. The label is a separate hang-tag that says <b>STORE</b> or <b>RECYCLE</b>.</p>"
            + fig(460, 320, card + dots + notes, "Anatomy of a training card")
            + "<h2>Flip the tag, flip the label</h2>"
            "<p>Each tag is folded so one side reads STORE and the other RECYCLE. Changing a label means "
            "turning its tag over; that is all an attacker may do.</p>"
            + fig(420, 56, flip, "Turning a tag over changes STORE to RECYCLE"))
    return page(4, body)


def learner() -> str:
    counts = errors(EXAMPLE, EXAMPLE_LABELS)
    winner = fit(EXAMPLE, EXAMPLE_LABELS)
    rows = []
    for k, (c, y) in enumerate(zip(EXAMPLE, EXAMPLE_LABELS)):
        top = 52 + k * 46
        rows.append(f'<g transform="translate(22 {top + 18})">{art.cargo_icon(c.red, c.round, c.striped, 28)}</g>'
                    + text(46, top + 14, c.id, 10, INK, 800, "start", family=art.MONO)
                    + text(46, top + 28, c.describe(), 8.5, INK, 500, "start")
                    + f'<g transform="translate(150 {top + 6}) scale(.42)">{art.tag(LABELS[y], 160, 55, "ex" + c.id)}</g>')
        for j, rule in enumerate(RULES):
            x = 270 + j * 64
            mark = (art.icon("check", C["teal"], 18) if predict(rule, c) == y else
                    f'<path d="M2 2l14 14M16 2L2 16" stroke="{C["red_dk"]}" stroke-width="3" stroke-linecap="round"/>')
            rows.append(f'<g transform="translate({x - 9} {top + 9})">{mark}</g>')
    heads = "".join(text(270 + j * 64, 34, rule.upper(), 10, INK, 900) for j, rule in enumerate(RULES))
    totals = "".join(f'<rect x="{248 + j * 64}" y="238" width="44" height="30" rx="6" '
                     f'fill="{C["mustard"] if rule == winner else C["paper"]}" stroke="{INK}" stroke-width="1.6"/>'
                     + text(270 + j * 64, 259, str(counts[rule]), 15, INK, 900) for j, rule in enumerate(RULES))
    table = (f'<rect width="460" height="285" rx="10" fill="{C["paper"]}" stroke="{INK}" stroke-width="1.6"/>'
             + text(22, 34, "CARD", 9, INK, 900, "start", spacing=1) + text(150, 34, "CURRENT TAG", 9, INK, 900,
                                                                           "start", spacing=1)
             + heads + "".join(rows) + text(22, 259, "ERRORS", 10, INK, 900, "start", spacing=1) + totals)
    order = "".join(f'<g transform="translate({20 + k * 145} 6)">'
                    f'<path d="{art.hexagon(22, 22, 22)[0]}" fill="{C["mustard"]}" stroke="{INK}" stroke-width="1.6"/>'
                    + text(22, 29, str(k + 1), 17, INK, 900) + text(52, 28, rule.upper(), 15, INK, 900, "start")
                    + (f'<path d="M{122} 22h14M131 16l6 6-6 6" fill="none" stroke="{INK}" stroke-width="2"/>'
                       if k < 2 else "") + "</g>" for k, rule in enumerate(RULES))
    body = ('<div class="kicker">How the robot learns</div><h1>Fewest errors wins</h1>'
            "<p>The robot can learn exactly one of three rules: <b>STORE if red</b>, <b>STORE if round</b>, or "
            "<b>STORE if striped</b>; anything else is RECYCLE. For each rule, count how many current tags it "
            "gets wrong. The rule with the fewest errors is the one the robot learns.</p>"
            + fig(460, 285, table, f"Worked example: {winner} makes {counts[winner]} errors and wins")
            + f"<p>Here red makes {counts['red']} errors, round {counts['round']} and striped {counts['striped']}, "
              f"so the robot learns <b>{winner}</b>. These tags alone do not prove red is the true rule.</p>"
            "<h2>Ties always break the same way</h2>"
            + fig(460, 52, order, "Tie order: red, then round, then striped")
            + "<p>The defender cannot pick a favourite rule; the counts decide.</p>")
    return page(5, body)


def setup() -> str:
    lay = "".join(nest(cargo_card(Card(f"C{k + 1:02}", k % 2, (k // 2) % 2, k % 3 == 0), 1), 6 + k * 46, 6, 40)
                  for k in range(6))
    body = ('<div class="kicker">Before each round</div><h1>Setup</h1>'
            "<ol>"
            "<li><b>Print and cut</b> the kit from the helper (see the README). Fold the tags, audit tokens, "
            "slips and keys once; they are reused.</li>"
            "<li><b>Lay out the round’s 24 training cards</b> face up in ID order. Put its 8 test cards face "
            "down to one side. Set out the three rule cards and the score card.</li>"
            "<li><b>The defender looks away.</b> The attacker takes this round’s private sheet and hangs a tag on "
            "every training card, matching the clean labels on the setup panel.</li>"
            "<li><b>The attacker poisons</b> (step 1 of the round), then hides the setup panel and the other "
            "round’s private material.</li>"
            "<li><b>Stack the sealed audit slips</b> in ID order where both players can see them, and keep the "
            "round’s sealed deployment key face down.</li>"
            "<li><b>The defender returns</b> and takes four audit tokens, AUDIT side up.</li>"
            "</ol>"
            + fig(290, 64, lay, "Training cards laid out in ID order")
            + '<p class="note">Features and rules are public. The defender first sees the labels <b>after</b> '
              "poisoning; remembering a clean layout is not part of the challenge.</p>"
              "<h2>Playing with the helper instead</h2>"
              "<p>Run <code>python3 -m poisoned_dataset play</code> on a shared screen. It keeps the counts "
              "and hides secrets at each handoff; look away when it says so.</p>")
    return page(6, body)


def vignette(kind: str) -> str:
    w, h = 125, 96
    shop = f'<rect width="{w}" height="{h}" rx="8" fill="url(#shop)"/>'
    edge = f'<rect width="{w}" height="{h}" rx="8" fill="none" stroke="{INK}" stroke-width="1.6"/>'
    draw = {
        "poison": (f'<g transform="translate(-6 12) scale(.32)">{art.mallory("v1")}</g>'
                   f'<g transform="translate(64 20) scale(.32)">{art.tag("STORE", 160, 55, "v1a")}</g>'
                   f'<g transform="translate(64 60) scale(.32)">{art.tag("RECYCLE", 160, 55, "v1b")}</g>'
                   f'<path d="M98 42q10 6 0 14" fill="none" stroke="{INK}" stroke-width="2.2"/>'
                   f'<path d="M94 54l4 3 3-4" fill="none" stroke="{INK}" stroke-width="2"/>'),
        "inspect": "".join(f'<g transform="translate({10 + k * 37} 10) scale(.13)">{art.cargo(k % 2, k < 2, k == 1)}</g>'
                           for k in range(3))
                   + "".join(f'<rect x="{f(10 + k * 9.6)}" y="50" width="7" height="7" '
                             f'fill="{C["paper"]}" stroke="{INK}" stroke-width=".8"/>' for k in range(11))
                   + text(62, 82, "COUNT ERRORS", 9, INK, 900, spacing=1),
        "audit": (f'<g transform="translate(30 48)">{art.hexbolt("AUDIT", 24)}</g>'
                  f'<path d="M58 48h12M66 43l5 5-5 5" fill="none" stroke="{INK}" stroke-width="2"/>'
                  f'<g transform="translate(96 48)">{art.hexbolt("VERIFIED", 24)}</g>'),
        "lock": (nest(rule_card(0, RULES[0]), 30, 6, 60)
                 + f'<g transform="translate(70 46)"><circle r="17" fill="{C["mustard"]}" stroke="{INK}" '
                   f'stroke-width="1.6"/><g transform="translate(-11 -12)">{art.icon("lock", INK, 22)}</g></g>'),
        "score": (nest(cargo_card(Card("T08", 1, 1, 1), 1, True), 10, 6, 60)
                  + f'<g transform="translate(78 30) scale(.27)">{art.tag("STORE", 160, 55, "v5")}</g>'
                  + f'<g transform="translate(86 56)">{art.icon("check", C["teal"], 26)}</g>'),
        "switch": (f'<g transform="translate(-4 20) scale(.26)">{art.mallory("v6")}</g>'
                   f'<g transform="translate(66 34) scale(.3)">{art.sorter("v6", reach=False)}</g>'
                   f'<path d="M48 18q14-12 28 0M76 86q-14 12-28 0" fill="none" stroke="{C["paper"]}" stroke-width="2.6"/>'),
    }[kind]
    return fig(w, h, shop + draw + art.grain(art.box(w, h), "vig" + kind, .7) + edge, kind)


def step(n: int, kind: str, title: str, copy: str) -> str:
    return (f'<div class="step">{vignette(kind)}<div><h2><span class="num">{n}</span>{escape(title)}</h2>'
            f"{copy}</div></div>")


def round_one() -> str:
    body = ('<div class="kicker">Each round</div><h1>Playing a round</h1>'
            + step(1, "poison", "Secret poisoning",
                   "<p>With the defender looking away, the attacker may turn over the tags of up to <b>four "
                   "different</b> training cards. Nothing else changes: no features, cards, references or test "
                   "cards. The attack is finished before auditing starts.</p>")
            + step(2, "inspect", "Inspect the data",
                   "<p>The defender sees all 24 cards and their current tags. Count each rule’s errors on the "
                   "rule cards and announce the current winner. Looking, grouping and counting are free.</p>")
            + step(3, "audit", "Spend audit tokens",
                   "<p>Up to <b>four</b>, one at a time. Name an unaudited card and pay a token. Open that card’s "
                   "sealed slip and turn its tag to the trusted label, even if it was already right. Flip the "
                   "token to <b>VERIFIED</b> and leave it on the card. Recount after every audit.</p>"))
    return page(7, body)


def round_two() -> str:
    body = (step(4, "lock", "Lock the learned rule",
                 "<p>When the defender stops or runs out of tokens, the rule with the fewest errors is locked, "
                 "using the tie order. Unused tokens give no bonus.</p>")
            + step(5, "score", "Reveal and score",
                   "<p>Turn the eight test cards over. For each, place the tag the locked rule predicts, then "
                   "open the sealed deployment key. Score one point per correct prediction, out of eight.</p>")
            + step(6, "switch", "Review and switch",
                   "<p>Reveal the true rule, the flipped tags and the audits. Talk about what changed the "
                   "learned rule. Then set out round two’s cards and switch attacker and defender.</p>")
            + '<h2>The fine print</h2><ul>'
              "<li>A verified card cannot be audited again.</li>"
              "<li>An audit repairs only its own card. Identical-looking copies keep their tags until they are "
              "audited too.</li>"
              "<li>No free relabelling, deleting or adding cards in this version.</li>"
              "<li>The helper’s audit hints are suggestions from visible evidence, not proof of poisoning.</li>"
              "</ul>")
    return page(8, body)


def winning() -> str:
    report = nest(score_card(), 0, 0, 150)
    body = ('<div class="kicker">After two rounds</div><h1>Winning</h1>'
            "<p>Compare the scores the two players earned as <b>defender</b>. The higher score wins; equal "
            "scores are a draw. Both players have the same four-flip and four-audit budgets, but different "
            "scenarios are not guaranteed to be equally hard.</p>"
            + fig(150, 210, report, "Deployment report score card")
            + '<p class="note">With three rules and an eight-card test deck that covers every combination, a '
              "wrong rule always scores 4/8 and the true rule 8/8. Draws may be common. That is a known risk in "
              "draft 0.1: record draws rather than inventing a tiebreaker.</p>"
              "<h2>Why the test deck is separate</h2>"
              "<p>The robot is judged on new cargo it never trained on, just as a deployed system is. The "
              "test cards never join the training data, and their reference labels stay sealed until the rule "
              "is locked.</p>")
    return page(9, body)


def debrief() -> str:
    qs = ("Which flipped tags changed the competition between rules, and why?",
          "Did finding a wrong tag immediately repair the score? What would one fewer audit have changed?",
          "Could an attacker flip a whole group of look-alike cards so no disagreement remains?",
          "What makes the sealed slips trustworthy here? What changes if checks cost more or can be wrong?",
          "What does this tiny rule library help explain, and what does it leave out about real ML systems?")
    body = ('<div class="kicker">Talk it over</div><h1>Debrief</h1>'
            "<p>The most interesting part of a match is often the reveal. Use these questions after both rounds:"
            "</p><ol>" + "".join(f"<li>{escape(q)}</li>" for q in qs) + "</ol>"
            "<h2>What this models, and what it does not</h2>"
            "<p>The game models label poisoning before training and a fixed budget of perfectly trustworthy "
            "audits against a three-rule learner. Real systems have far more features, noisier references and "
            "attackers who adapt. Treat the discussion as feedback on the game, not proof that anyone learned "
            "something.</p>"
            + fig(460, 150, f'<rect width="460" height="150" rx="10" fill="url(#night)"/>'
                            f'{art.stars("debrief", 460, 150, 40)}'
                            f'<g transform="translate(110 75)">{art.porthole(52, "db")}</g>'
                            + text(300, 70, "Locked rules meet", 15, C["paper"], 900)
                            + text(300, 92, "new cargo.", 15, C["paper"], 900)
                            + f'<rect width="460" height="150" rx="10" fill="none" stroke="{INK}" stroke-width="2"/>',
                  "Earth over the Moon through a porthole"))
    return page(10, body)


def reference() -> str:
    aid = nest(aid_card(), 0, 0, 200)
    body = ('<div class="kicker">At a glance</div><h1>Quick reference</h1>'
            + fig(200, 280, aid, "Quick reference card", 1.1)
            + "<h2>Budgets in draft 0.1</h2>"
            "<p>24 training cards per round · up to 4 flips · 4 audit tokens · 8 test cards · ties go "
            "red, then round, then striped.</p>"
            "<h2>Playtesting?</h2>"
            "<p>Share the short feedback form in <code>playtest.md</code> after both rounds. Note which text, "
            "symbols or pieces were hard to read or handle.</p>")
    return page(11, body)


def back_cover() -> str:
    scene = (f'<rect width="550" height="850" fill="url(#night)"/>{art.stars("backcover", 550, 850, 120)}'
             f'<g transform="translate(275 300)">{art.porthole(150, "bc")}</g>'
             f'<g transform="translate(95 560) scale(.56)">{art.logo(dark=True)}</g>')
    body = ('<div style="position:absolute;left:.45in;right:.45in;top:7.1in;text-align:center;color:#f3e8d0;'
            'font-size:8.5pt">Draft 0.1 · rules and art are working hypotheses, not measured results.<br>'
            "Source, helper and printable kit: github.com/haydn-s/poisoned-dataset-game · Apache 2.0</div>")
    return page(12, body, bg(C["night"], scene), dark=True)


PAGES = (cover, mission, components, anatomy, learner, setup, round_one, round_two, winning, debrief,
         reference, back_cover)


def imposition(n: int) -> list[tuple[int, int]]:
    """Saddle-stitch order: each printed side holds (left, right) page numbers."""
    if n % 4:
        raise ValueError("A saddle-stitched booklet needs a multiple of four pages")
    sides = []
    for i in range(n // 4):
        sides += [(n - 2 * i, 1 + 2 * i), (2 + 2 * i, n - 1 - 2 * i)]
    return sides


def document(title: str, body: str, page_size: str) -> str:
    style = STYLE.replace("size: 5.5in 8.5in", f"size: {page_size}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title>'
            f"<style>{style}</style></head><body>{art.defs()}{body}</body></html>\n")


def build(out: Path) -> None:
    pages = [make() for make in PAGES]
    (out / "rulebook.html").write_text(document("Poisoned Dataset rulebook", "".join(pages), "5.5in 8.5in"),
                                       encoding="utf-8")
    sheets = "".join(f'<div class="sheet">{pages[a - 1]}{pages[b - 1]}</div>' for a, b in imposition(len(pages)))
    (out / "rulebook-booklet.html").write_text(
        document("Poisoned Dataset rulebook (booklet imposition)", sheets, "11in 8.5in"), encoding="utf-8")
