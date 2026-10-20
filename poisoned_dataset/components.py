"""Printable, self-contained HTML with separate public and secret materials.

Cards are poker size (2.5 x 3.5 in) drawn in SVG at 0.01 in per unit, eight to a
landscape Letter sheet, edge to edge with crop marks so straight cuts separate them.
"""

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from . import art
from .art import C, INK, MONO, f, para, rrect, text
from .core import LABELS, RULES, Card, generate, predict, test_deck

ROUND_TONE = {1: (C["mustard"], INK), 2: (C["teal"], C["paper"])}
TAGS, SPARE_TAGS = 24, 3

STYLE = """
@page { size: 11in 8.5in; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; color: #2a1c14; font: 10pt 'Inter', system-ui, sans-serif; background: #8a8178; }
.sheet { width: 11in; height: 8.5in; position: relative; margin: .25in auto; background: #fffdf8;
         break-after: page; overflow: hidden; box-shadow: 0 2px 12px #0004; }
.sheet:last-child { break-after: auto; }
.sheet header { position: absolute; left: .5in; right: .5in; top: .16in; height: .5in; }
.sheet h1 { margin: 0; font: 900 13pt 'Inter Display', 'Inter', sans-serif; letter-spacing: .02em; }
.sheet p { margin: .02in 0 0; font-size: 8pt; line-height: 1.3; }
.cards { position: absolute; left: .5in; top: .75in; display: grid; grid-template-columns: repeat(4, 2.5in);
         grid-auto-rows: 3.5in; }
.card { width: 2.5in; height: 3.5in; display: block; }
.marks { position: absolute; left: 0; top: 0; width: 11in; height: 8.5in; pointer-events: none; }
.free { position: absolute; left: .5in; top: .75in; width: 10in; height: 7.5in; }
.private header h1 { color: #8c2a21; }
.private .sheet { border-top: .1in solid #8c2a21; }
@media print { body { background: none; } .sheet { margin: 0; box-shadow: none; } }
"""


def document(title: str, sheets: list[str], private: bool = False) -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{escape(title)}</title><style>{STYLE}</style></head>'
            f'<body class="{"private" if private else "public"}">{art.defs()}{"".join(sheets)}</body></html>\n')


def crop_marks(cols: int = 4, rows: int = 2) -> str:
    x0, y0, w, h, out = 50, 75, 250, 350, []
    for c in range(cols + 1):
        x = x0 + c * w
        out.append(f'<path d="M{x} {y0 - 30}V{y0 - 8}M{x} {y0 + rows * h + 8}V{y0 + rows * h + 30}"/>')
    for r in range(rows + 1):
        y = y0 + r * h
        out.append(f'<path d="M{x0 - 30} {y}H{x0 - 8}M{x0 + cols * w + 8} {y}H{x0 + cols * w + 30}"/>')
    return (f'<svg class="marks" viewBox="0 0 1100 850" aria-hidden="true">'
            f'<g stroke="{INK}" stroke-width=".8">{"".join(out)}</g></svg>')


def sheet(title: str, note: str, body: str, cards: bool = True) -> str:
    inner = f'<div class="cards">{body}</div>{crop_marks()}' if cards else f'<div class="free">{body}</div>'
    return (f'<section class="sheet"><header><h1>{escape(title)}</h1><p>{escape(note)}</p></header>'
            f'{inner}</section>')


def card(kind: str, label: str, body: str, frame: bool = True) -> str:
    edge = (f'<path d="{rrect(9, 9, 232, 332, 12)[0]}" fill="none" stroke="{INK}" stroke-width="2"/>'
            if frame else "")
    return (f'<svg class="card" data-kind="{kind}" viewBox="0 0 250 350" role="img" aria-label="{escape(label)}">'
            f'<rect width="250" height="350" fill="{C["paper"]}"/>{art.grain(art.box(250, 350), "card", .35)}'
            f'{body}{edge}</svg>')


def header(ident: str, middle: str, round_number: int, chip: tuple[str, str, str] | None = None) -> str:
    """ID plate, card kind, and a chip naming the round (or, in the fixed edition, the deck)."""
    label, tone, ink = chip or (f"ROUND {round_number}", *ROUND_TONE[round_number])
    return (f'<path d="{rrect(16, 16, 76, 30, 7)[0]}" fill="{INK}"/>'
            + text(54, 38, ident, 20, C["paper"], 800, family=MONO)
            + text(125, 35, middle, 8.5, INK, 800, spacing=1.2)
            + f'<path d="{rrect(158, 16, 76, 30, 15)[0]}" fill="{tone}" stroke="{INK}" stroke-width="1.5"/>'
            + text(196, 36, label, 10.5, ink, 900, spacing=.6))


def panel(content: str, key: str) -> str:
    d = rrect(0, 0, 226, 162, 8)[0]
    return (f'<svg x="12" y="52" width="226" height="162" viewBox="0 0 226 162">'
            f'{art.clipped(d, content, key)}<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.4"/></svg>')


def manifest(c: Card) -> str:
    """Features spelled out with shape cues, so colour is never the only signal."""
    chips = (("RED" if c.red else "BLUE", art.swatch(c.red, 15)),
             ("ROUND" if c.round else "SQUARE",
              f'<path d="{art.circle(7.5, 7.5, 7)[0] if c.round else rrect(.5, .5, 14, 14, 1.5)[0]}" fill="{INK}"/>'),
             ("STRIPED" if c.striped else "PLAIN",
              f'<path d="{rrect(.5, 2.5, 14, 10, 2)[0]}" fill="{C["paper"]}" stroke="{INK}" stroke-width="1.4"/>'
              + ('<path d="M3 12l6-9M7.5 12.5l6-9" stroke="#2a1c14" stroke-width="1.6"/>' if c.striped else "")))
    out = []
    for k, (word, glyph) in enumerate(chips):
        x = 12 + k * 77
        out.append(f'<path d="{rrect(x, 222, 72, 26, 6)[0]}" fill="{C["paper_dk"]}" stroke="{INK}" stroke-width="1.2"/>'
                   f'<g transform="translate({x + 6} 227.5)">{glyph}</g>'
                   + text(x + 46, 239.5, word, 9.2, INK, 800, spacing=.3))
    return "".join(out)


def tag_slot(caption: str) -> str:
    x, y, w, h = 45, 270, 160, 55
    hole = (x + h * .32 * 1.15, y + h / 2)
    return (f'<path transform="translate({x} {y})" d="{art.tag_path(w, h)}" fill="{C["paper_dk"]}" fill-opacity=".45" '
            f'fill-rule="evenodd" stroke="{INK}" stroke-width="1.3" stroke-dasharray="5 4"/>'
            f'<circle cx="{f(hole[0])}" cy="{f(hole[1])}" r="5.5" fill="{C["metal"]}" stroke="{INK}" stroke-width="1.5"/>'
            + text(x + w / 2 + 14, y + h / 2 + 3.5, caption, 8.5, INK, 700, spacing=.8, extra='opacity=".6"'))


def cargo_card(c: Card, round_number: int, test: bool = False, chip: tuple[str, str, str] | None = None) -> str:
    kind = "test" if test else "training"
    body = (header(c.id, "TEST" if test else "TRAINING", round_number, chip)
            + panel(art.cargo(c.red, c.round, c.striped, c.id, night=test), (kind, c.id, round_number))
            + manifest(c) + tag_slot("PLACE PREDICTED TAG" if test else "HANG LABEL TAG HERE"))
    owner = chip[0].title() if chip else f"Round {round_number}"
    return card(kind, f"{owner} {kind} card {c.id}: {c.describe()}", body)


# --- Card backs (optional duplex sheet) ------------------------------------------

def hazard_ring() -> str:
    ring = (rrect(4, 4, 242, 342, 16)[0] + rrect(16, 16, 218, 318, 9)[0], (4, 4, 242, 342))
    return (f'<path d="{ring[0]}" fill="{C["mustard"]}" fill-rule="evenodd"/>'
            + art.hatch(ring, INK, 14, 7, 45, "ring", evenodd=True))


def back(kind: str, round_number: int = 0, tone: str | None = None, subtitle: str | None = None) -> str:
    subtitle = subtitle if subtitle is not None else (f"ROUND {round_number}" if round_number else "")
    if kind == "test":
        scene = ('<rect width="250" height="350" fill="url(#night)"/>' + art.stars(f"back{round_number}", 250, 350, 60)
                 + f'<g transform="translate(125 132)">{art.porthole(70, f"tb{round_number}")}</g>')
        words = (text(125, 252, "DEPLOYMENT TEST", 17, C["paper"], 900, spacing=1.5)
                 + text(125, 272, f"{subtitle} · KEEP FACE DOWN" if subtitle else "KEEP FACE DOWN", 9, C["paper"],
                        700, spacing=1)
                 + text(125, 300, "Reveal only after the rule is locked.", 9, C["paper"], 500))
    else:
        tone = tone or (ROUND_TONE[round_number][0] if round_number else C["amber"])
        bot = (f'<g transform="translate(66 150) scale(.62)">{art.sorter("back")}</g>' if kind == "training" else
               f'<g transform="translate(78 118) scale(.48)">{art.mallory("back")}</g>')
        scene = ('<rect width="250" height="350" fill="url(#shop)"/>'
                 + hazard_ring() +
                 f'<rect x="16" y="16" width="218" height="318" rx="9" fill="none" stroke="{tone}" stroke-width="3"/>'
                 f'<g transform="translate(38 28) scale(.27)">{art.logo()}</g>' + bot)
        words = (text(125, 300, "TRAINING DATA" if kind == "training" else "REFERENCE", 16, INK, 900, spacing=1.5)
                 + (text(125, 318, subtitle, 10, INK, 800, spacing=2) if subtitle else ""))
    return card(f"back-{kind}", f"{kind} card back", scene + art.grain(art.box(250, 350), "back", .5) + words,
                frame=False)


# --- Reference cards ---------------------------------------------------------------

def sort_columns(rule: str, y: float = 104) -> str:
    """STORE and RECYCLE tags, each above the four cargo types the rule sends there."""
    column = lambda x, label, group: (
        f'<g transform="translate({x} {y}) scale(.62)">{art.tag(label, 160, 55, "rc" + label)}</g>'
        + "".join(f'<g transform="translate({x + 24 + (k % 2) * 46} {y + 56 + (k // 2) * 44})">'
                  f'{art.cargo_icon(c.red, c.round, c.striped, 34)}</g>' for k, c in enumerate(group)))
    return (column(22, "STORE", [c for c in test_deck() if predict(rule, c)])
            + column(132, "RECYCLE", [c for c in test_deck() if not predict(rule, c)]))


def rule_card(i: int, rule: str) -> str:
    later, earlier = RULES[i + 1:], RULES[:i]
    tie = (f"Wins ties against {' and '.join(later)}." if later else "") + (
        f" Loses ties to {' and '.join(earlier)}." if earlier else "")
    tally = "".join(f'<rect x="{f(22 + (k % 12) * 17.4)}" y="{256 + (k // 12) * 18}" width="14" height="14" rx="2" '
                    f'fill="{C["paper"]}" stroke="{INK}" stroke-width="1.1"/>' for k in range(24))
    nut = art.hexagon(206, 44, 27)
    body = (text(22, 34, f"RULE {i + 1}", 10, INK, 800, "start", spacing=2)
            + text(22, 66, rule.upper(), 32, INK, 900, "start")
            + art.painted(art.part(nut, C["mustard"], "rule" + rule, 2, 2, lw=2))
            + text(206, 52, str(i + 1), 24, INK, 900) + text(206, 84, "TIE ORDER", 7, INK, 800, spacing=.8)
            + text(125, 96, f"STORE if {rule}; otherwise RECYCLE.", 10.5, INK, 700)
            + f'<path d="M125 106V236" stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>'
            + sort_columns(rule)
            + text(22, 250, "COUNT TRAINING ERRORS", 8, INK, 800, "start", spacing=1) + tally
            + para(125, 312, tie, 8.5, 200, anchor="middle")[0])
    return card("rule", f"Rule {i + 1}: STORE if {rule}", body)


def score_card() -> str:
    boxes = lambda y: "".join(f'<rect x="{f(22 + k * 23)}" y="{y}" width="19" height="19" rx="3" fill="{C["paper"]}" '
                              f'stroke="{INK}" stroke-width="1.3"/>' for k in range(8))
    body = (f'<g transform="translate(150 22) scale(.42)">{art.sorter("score", reach=False)}</g>'
            + text(22, 48, "DEPLOYMENT", 17, INK, 900, "start") + text(22, 68, "REPORT", 17, INK, 900, "start")
            + text(22, 120, "ROUND 1 · DEFENDER A", 9, INK, 800, "start", spacing=1) + boxes(128)
            + text(226, 143, "/ 8", 11, INK, 800, "end")
            + text(22, 190, "ROUND 2 · DEFENDER B", 9, INK, 800, "start", spacing=1) + boxes(198)
            + text(226, 213, "/ 8", 11, INK, 800, "end")
            + para(125, 262, "Tick one box per test card the locked rule predicts correctly. "
                   "The higher defender score wins; equal scores draw.", 9, 200, anchor="middle")[0])
    return card("score", "Score card", body)


STEPS = ("Attacker secretly flips up to 4 tags.",
         "Defender counts each rule's errors. Looking is free.",
         "Audit: pay 1 token, open that card's slip, set its tag, flip the token to VERIFIED on it.",
         "Lock the fewest-error rule. Ties: red, round, striped.",
         "Turn the test deck: 1 point per correct prediction.",
         "Reveal flips and audits; switch roles.")


def aid_card(steps: tuple[str, ...] = STEPS) -> str:
    out, y = [], 66
    for n, step in enumerate(steps, 1):
        out.append(f'<circle cx="30" cy="{y - 4}" r="9.5" fill="{C["mustard"]}" stroke="{INK}" stroke-width="1.3"/>'
                   + text(30, y, str(n), 10.5, INK, 900))
        svg, lines = para(46, y, step, 10.5, 184, lead=1.25, weight=600)
        out.append(svg)
        y += 12 + lines * 13.1
    body = (text(22, 38, "ONE ROUND", 17, INK, 900, "start") + text(228, 38, "QUICK REFERENCE", 7.5, INK, 800, "end",
                                                                      spacing=1) + "".join(out))
    return card("aid", "Quick reference", body)


def role_card(role: str, blurb: str | None = None) -> str:
    attacker = role == "ATTACKER"
    figure = (f'<g transform="translate(46 70) scale(.58)">{art.mallory("role")}</g>' if attacker else
              f'<g transform="translate(40 92) scale(.84)">{art.sorter("role")}</g>'
              f'<g transform="translate(192 120)">{art.hexbolt("VERIFIED", 26)}</g>')
    blurb = blurb or ("You know the true rule and the clean labels. Before the defender looks, flip up to four tags."
                      if attacker else
                      "Inspect the tags, spend up to four audits, then lock the rule your sorter learns.")
    scene = (f'<svg x="12" y="52" width="226" height="200" viewBox="0 0 226 200">'
             f'<rect width="226" height="200" fill="url(#shop)"/>{figure}</svg>'
             f'<path d="{rrect(12, 52, 226, 200, 8)[0]}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    body = (text(22, 40, role, 22, INK, 900, "start", spacing=1)
            + text(228, 40, "MALLORY" if attacker else "SORTER", 8, INK, 800, "end", spacing=1.5)
            + scene + para(125, 276, blurb, 10, 205, weight=600, anchor="middle")[0])
    return card("role", f"{role.title()} role card", body)


# --- Tokens --------------------------------------------------------------------------

def tag_strip(k: int) -> str:
    """One fold-over tag: RECYCLE on the left, STORE on the right; flipping it flips the label."""
    w, h, c = 160, 55, 55 * .32
    outline = f"M0 0H{f(w - c)}L{w} {f(c)}L{f(w + c)} 0H{2 * w}V{h}H{f(w + c)}L{w} {f(h - c)}L{f(w - c)} {h}H0Z"
    return (art.tag("RECYCLE", w, h, f"tr{k}", mirror=True, outline=False)
            + f'<g transform="translate({w} 0)">{art.tag("STORE", w, h, f"ts{k}", outline=False)}</g>'
            f'<path d="{outline}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
            f'<path d="M{w} {f(c)}V{f(h - c)}" stroke="{INK}" stroke-width="1" stroke-dasharray="3 3"/>')


def tokens_sheet() -> str:
    strips = "".join(f'<g class="tag-strip" transform="translate({col * 340} {row * 62})">{tag_strip(row * 3 + col)}</g>'
                     for row in range((TAGS + SPARE_TAGS) // 3) for col in range(3))
    r, nuts = 48, []
    for k in range(4):
        x = 60 + k * 240
        nuts.append(f'<g transform="translate({x} 0)">'
                    f'<g transform="translate({f(r * .866)} {r})">{art.hexbolt("AUDIT", r, k + 1)}</g>'
                    f'<g transform="translate({f(r * .866 * 3)} {r})">{art.hexbolt("VERIFIED", r)}</g>'
                    f'<path d="M{f(r * .866 * 2)} {f(r * .5)}V{f(r * 1.5)}" stroke="{INK}" stroke-width="1.2" '
                    f'stroke-dasharray="3 3"/></g>')
    return (f'<svg viewBox="0 0 1000 750" width="10in" height="7.5in" role="img" '
            f'aria-label="Label tags and audit tokens">'
            f'<g transform="translate(0 4)">{strips}</g>'
            + text(0, 588, "AUDIT TOKENS · fold each pair on the dotted edge; spend AUDIT side up, "
                           "then flip to VERIFIED on the audited card",
                   9, INK, 800, "start", spacing=.5)
            + f'<g transform="translate(0 604)">{"".join(nuts)}</g></svg>')


# --- Private references --------------------------------------------------------------

def slip(c: Card, label: int, round_number: int) -> str:
    """A Z-fold slip: ID panel | trusted label | security tint. Fold so the label sits inside."""
    ident = (f'<rect width="110" height="52" fill="{C["paper"]}"/>'
             + text(40, 32, c.id, 19, INK, 800, family=MONO)
             + text(40, 45, f"ROUND {round_number}", 7, INK, 800, spacing=1)
             + f'<circle cx="88" cy="26" r="15" fill="{C["red_dk"]}" stroke="{INK}" stroke-width="1.4"/>'
             + text(88, 31, "T", 15, C["paper"], 900) + text(88, 49, "TRENT", 5.5, INK, 800, spacing=.6))
    trusted = (f'<g transform="translate(110 0)"><rect width="110" height="52" fill="{C["paper"]}"/>'
               f'<g transform="translate(6 10) scale(.6)">{art.tag(LABELS[label], 160, 55, "slip" + c.id)}</g>'
               + text(55, 9, f"{c.id} TRUSTED LABEL", 5.5, INK, 800, spacing=.5) + "</g>")
    tint = ('<rect x="220" width="110" height="52" fill="#5a4a3e"/>'
            + art.hatch(rrect(220, 0, 110, 52, 0), INK, 4.5, 2.2, 30, "tint")
            + art.hatch(rrect(220, 0, 110, 52, 0), "#8c7a66", 7, 1, -30, "tint2")
            + text(275, 30, "FOLD ME OVER THE LABEL", 6, C["paper"], 800, spacing=.6, extra='opacity=".6"'))
    folds = (f'<path d="M110 0V52M220 0V52" stroke="{C["paper"]}" stroke-width="1.6" stroke-dasharray="3 3"/>'
             f'<path d="M110 0V52M220 0V52" stroke="{INK}" stroke-width=".8" stroke-dasharray="3 3"/>'
             f'<rect width="330" height="52" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    return ident + trusted + tint + folds


def slips_sheet(scenario, round_number: int) -> str:
    slips = "".join(f'<g transform="translate({(k // 12) * 350} {(k % 12) * 57})">{slip(c, y, round_number)}</g>'
                    for k, (c, y) in enumerate(zip(scenario.cards, scenario.clean_labels)))
    rows = "".join(text(730 + (k // 12) * 130, 128 + (k % 12) * 21, f"{c.id}  {LABELS[y]}", 10.5, INK, 700, "start",
                        family=MONO) for k, (c, y) in enumerate(zip(scenario.cards, scenario.clean_labels)))
    setup = (f'<rect x="712" y="0" width="288" height="420" rx="10" fill="{C["paper"]}" stroke="{C["red_dk"]}" stroke-width="2"/>'
             + text(730, 28, "ATTACKER SETUP", 13, C["red_dk"], 900, "start", spacing=1)
             + text(730, 50, f"True rule: STORE if {scenario.true_rule}", 11, INK, 800, "start")
             + para(730, 72, "Hang these clean tags first, then flip up to four. Hide this panel before the "
                    "defender returns.", 10, 255, weight=600)[0] + rows
             + para(712, 470, "Fold each slip like a zig-zag: ID panel in front, label in the middle, tinted panel "
                    "behind. Open only a slip the defender has paid for.", 11, 280, weight=600)[0])
    return f'<svg viewBox="0 0 1000 750" width="10in" height="7.5in">{slips}{setup}</svg>'


def key_card(scenario, round_number: int) -> str:
    """The sealed deployment key: a cover flap folded over the eight reference labels."""
    rows = []
    for k, c in enumerate(test_deck()):
        y = 96 + k * 29
        rows.append(f'<g transform="translate(34 {y})">{art.cargo_icon(c.red, c.round, c.striped, 20)}</g>'
                    + text(52, y + 4, f"{c.id}  {c.describe()}", 8.5, INK, 700, "start")
                    + f'<g transform="translate(168 {y - 10}) scale(.42)">'
                      f'{art.tag(LABELS[predict(scenario.true_rule, c)], 160, 55, "key" + c.id)}</g>')
    inside = (text(22, 38, f"DEPLOYMENT KEY · R{round_number}", 14, INK, 900, "start")
              + text(22, 60, f"True rule: STORE if {scenario.true_rule}", 10, INK, 800, "start")
              + text(22, 76, "Reference labels for the test deck", 8, INK, 600, "start") + "".join(rows))
    cover = ('<rect width="250" height="350" fill="url(#night)"/>' + art.stars(f"key{round_number}", 250, 350, 50)
             + f'<g transform="translate(125 140)">{art.porthole(64, f"k{round_number}")}</g>'
             + text(125, 250, "SEALED", 22, C["paper"], 900, spacing=3)
             + text(125, 272, f"ROUND {round_number} DEPLOYMENT KEY", 9, C["paper"], 800, spacing=1)
             + text(125, 296, "Open only after the rule is locked.", 9, C["paper"], 500))
    return (f'<svg viewBox="0 0 500 350" width="5in" height="3.5in" role="img" aria-label="Sealed deployment key">'
            f'<rect width="250" height="350" fill="{C["paper"]}"/>{inside}'
            f'<g transform="translate(250 0)">{cover}</g>'
            f'<rect width="500" height="350" fill="none" stroke="{INK}" stroke-width="1.5"/>'
            f'<path d="M250 0V350" stroke="{C["paper"]}" stroke-width="2" stroke-dasharray="4 4"/>'
            f'<path d="M250 0V350" stroke="{INK}" stroke-width="1" stroke-dasharray="4 4"/></svg>')


def build(out: Path, seed: int, regime: str) -> None:
    scenarios = [generate(seed + r, regime=regime) for r in range(2)]
    out.mkdir(parents=True, exist_ok=False)
    public, private, backs = [], [], []
    tag_note = "Cut on the crop marks. Cards are 2.5 x 3.5 in; print at 100% (actual size) on US Letter, landscape."
    for r, scenario in enumerate(scenarios, 1):
        for start in range(0, len(scenario.cards), 8):
            public.append(sheet(f"Round {r} training cards {start + 1}-{start + 8}",
                                f"Draft 0.1 · seed {scenario.seed} · {regime}. {tag_note}",
                                "".join(cargo_card(c, r) for c in scenario.cards[start:start + 8])))
        public.append(sheet(f"Round {r} independent test deck",
                            "Keep face down until the learned rule is locked. These eight cards score uniform deployment.",
                            "".join(cargo_card(c, r, True) for c in test_deck())))
        private.append(sheet(f"PRIVATE · Round {r} trusted audit slips",
                             "Attacker only. Cut the slips apart, fold each one, and keep this round's material "
                             "hidden from the other player's eyes.", slips_sheet(scenario, r), cards=False))
        private.append(sheet(f"PRIVATE · Round {r} final reveal",
                             "Attacker only before play. Cut out the key, fold the SEALED cover over the labels, "
                             "and keep it face down until the rule is locked.",
                             f'<div style="display:flex;justify-content:center;padding-top:1.6in">'
                             f'{key_card(scenario, r)}</div>', cards=False))
        backs.append(sheet(f"Optional backs · Round {r} training",
                           "Print on the reverse of each round's training sheets (duplex, any flip).",
                           back("training", r) * 8))
        backs.append(sheet(f"Optional backs · Round {r} test deck",
                           "Print on the reverse of the matching test-deck sheet.", back("test", r) * 8))
    public.append(sheet("Candidate rules, score card and player aids",
                        "Pick the rule with the fewest mismatches to the current tags. Ties: red, round, striped.",
                        "".join(rule_card(i, rule) for i, rule in enumerate(RULES))
                        + score_card() + aid_card() + aid_card() + role_card("ATTACKER") + role_card("DEFENDER")))
    public.append(sheet("Label tags and audit tokens",
                        f"{TAGS} tags plus {SPARE_TAGS} spares, reused in round two. Cut each strip out, fold on the "
                        "dotted line, glue back to back, and trim the notches: one side STORE, the other RECYCLE.",
                        tokens_sheet(), cards=False))
    backs.append(sheet("Optional backs · reference cards", "Print on the reverse of the rules sheet.",
                       back("reference") * 8))
    (out / "public.html").write_text(document("Poisoned Dataset public components", public), encoding="utf-8")
    (out / "private.html").write_text(document("Poisoned Dataset private references", private, True), encoding="utf-8")
    (out / "backs.html").write_text(document("Poisoned Dataset optional card backs", backs), encoding="utf-8")
    (out / "scenario.json").write_text(json.dumps([asdict(s) for s in scenarios], indent=2) + "\n", encoding="utf-8")
