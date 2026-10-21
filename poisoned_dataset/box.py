"""Box mockup: telescoping lid and base dielines with cover art, plus a packing plan.

Dimensions are in inches; drawings use 0.01 in per unit. These are paper-mockup
dielines for sizing and cover layout, not a vendor template: confirm the printer's
own template, bleed and board thickness before production.
"""

import mimetypes
from base64 import b64encode
from html import escape
from pathlib import Path

from . import art
from .art import C, INK, f, para, text
from .components import TAGS, SPARE_TAGS

BASE = (8.75, 5.75, 1.5)          # outer length, width and wall height of the base tray
CLEARANCE = .0625                 # lid panels exceed the base so the lid slides over it
LID = (BASE[0] + CLEARANCE, BASE[1] + CLEARANCE, BASE[2])
BLEED, TAB = .125, .5
WELL = (2.7, 3.7)                 # one poker-card well, with finger room
RULEBOOK = (5.5, 8.5)
PACKING = {
    "seeded": {
        "contents": ("48 training cards", "16 test cards", "3 rule cards", "Score card and 2 quick references",
                     "2 role cards", f"{TAGS + SPARE_TAGS} fold-over STORE/RECYCLE tags", "4 audit tokens",
                     "48 sealed audit slips and 2 deployment keys", "12-page rulebook"),
        "wells": (("ROUND 1", "24 training + 8 test"), ("ROUND 2", "24 training + 8 test"),
                  ("REFERENCE", "rules, score, aids, roles, 2 keys")),
        "strip": (("TAGS", f"{TAGS + SPARE_TAGS} folded tags", 2.2), ("TOKENS", "4 audit tokens", 1.5),
                  ("PRIVATE R1", "24 slips", 2.2), ("PRIVATE R2", "24 slips", 2.2)),
        "check": "Private slips travel in their own envelopes so the defender never handles them before an audit.",
    },
    "fixed": {
        "contents": ("96 training cards in four decks", "8 test cards", "3 truth cards", "16 reference cards",
                     "3 rule cards", "Score card and 2 quick references", "2 role cards",
                     f"{TAGS + SPARE_TAGS} fold-over STORE/RECYCLE tags", "4 audit tokens", "12-page rulebook"),
        "wells": (("DECKS A + B", "48 training cards"), ("DECKS C + D", "48 training cards"),
                  ("REFERENCE", "test, truth, reference, rules, aids")),
        "strip": (("TAGS", f"{TAGS + SPARE_TAGS} folded tags", 4.1), ("TOKENS", "4 audit tokens", 4.1)),
        "check": "Unused truth and reference cards go back face down in the reference well between rounds.",
    },
}

STYLE = """
@page sheet { size: 17in 11in; margin: 0; }
@page plan { size: 11in 8.5in; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; background: #8a8178; color: #2a1c14; font: 9pt 'Inter', system-ui, sans-serif; }
.tabloid { page: sheet; width: 17in; height: 11in; position: relative; overflow: hidden; background: #fff;
           break-after: page; margin: .25in auto; }
.letter { page: plan; width: 11in; height: 8.5in; position: relative; overflow: hidden; background: #fffdf8;
          margin: .25in auto; padding: .45in .5in; }
.tabloid > svg { position: absolute; inset: 0; width: 17in; height: 11in; }
h1 { font: 900 15pt 'Inter Display', 'Inter', sans-serif; margin: 0 0 .06in; }
h2 { font: 900 10.5pt 'Inter Display', 'Inter', sans-serif; margin: .12in 0 .04in; }
table { border-collapse: collapse; font-size: 8.4pt; width: 100%; }
td, th { border-bottom: 1px solid #c9b48a; padding: .03in .06in; text-align: left; vertical-align: top; }
.cols { display: grid; grid-template-columns: 5.1in 1fr; gap: .3in; }
@media print { body { background: none; } .tabloid, .letter { margin: 0; } }
"""


def inches(x: float) -> float:
    return x * 100


def outline(L: float, W: float, D: float) -> str:
    """Cut path for a tray: centre panel, four walls, glue tabs on the long walls."""
    L, W, D, T = inches(L), inches(W), inches(D), inches(TAB)
    pts = [(D, 0), (D + L, 0), (D + L + T, .12 * D), (D + L + T, .88 * D), (D + L, D), (2 * D + L, D),
           (2 * D + L, D + W), (D + L, D + W), (D + L + T, D + W + .12 * D), (D + L + T, D + W + .88 * D),
           (D + L, 2 * D + W), (D, 2 * D + W), (D - T, D + W + .88 * D), (D - T, D + W + .12 * D), (D, D + W),
           (0, D + W), (0, D), (D, D), (D - T, .88 * D), (D - T, .12 * D)]
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def folds(L: float, W: float, D: float) -> str:
    L, W, D = inches(L), inches(W), inches(D)
    return (f"M{f(D)} {f(D)}H{f(D + L)}M{f(D)} {f(D + W)}H{f(D + L)}M{f(D)} {f(D)}V{f(D + W)}"
            f"M{f(D + L)} {f(D)}V{f(D + W)}M{f(D)} 0V{f(D)}M{f(D + L)} 0V{f(D)}"
            f"M{f(D)} {f(D + W)}V{f(2 * D + W)}M{f(D + L)} {f(D + W)}V{f(2 * D + W)}")


def wall(w: float, h: float, words: str, key: str) -> str:
    """Wall art drawn upright in a w x h box (units), bleeding past its outer (bottom) edge."""
    b = inches(BLEED)
    stripe = art.poly((-b, h - 26), (w + b, h - 26), (w + b, h + b), (-b, h + b))
    return (f'<rect x="{f(-b)}" y="0" width="{f(w + 2 * b)}" height="{f(h + b)}" fill="url(#shop)"/>'
            f'<path d="{stripe[0]}" fill="{C["mustard"]}"/>' + art.hatch(stripe, INK, 18, 9, 45, key)
            + art.grain(art.box(w, h), key, .12) + words)


def panel_art(L: float, W: float, D: float, top: str, walls: dict[str, str], key: str) -> str:
    """Place the top panel and the four walls, each rotated so it reads upright on the box."""
    Lu, Wu, Du = inches(L), inches(W), inches(D)
    out = [f'<svg x="{f(Du)}" y="{f(Du)}" width="{f(Lu)}" height="{f(Wu)}" viewBox="0 0 {f(Lu)} {f(Wu)}" '
           f'overflow="visible">{top}</svg>']
    placements = {
        "front": (f"translate({f(Du)} {f(Du + Wu)})", Lu),
        "back": (f"translate({f(Du + Lu)} {f(Du)}) rotate(180)", Lu),
        "left": (f"translate({f(Du)} {f(Du)}) rotate(90)", Wu),
        "right": (f"translate({f(Du + Lu)} {f(Du + Wu)}) rotate(-90)", Wu),
    }
    for side, (transform, length) in placements.items():
        out.append(f'<g transform="{transform}">{wall(length, Du, walls.get(side, ""), key + side)}</g>')
    tab_fill = art.poly((-inches(TAB), 0), (Lu + 2 * Du + inches(TAB), 0), (Lu + 2 * Du + inches(TAB), Wu + 2 * Du),
                        (-inches(TAB), Wu + 2 * Du))
    return f'<path d="{tab_fill[0]}" fill="{C["paper_dk"]}"/>' + "".join(out)


def cover_top(L: float, W: float, image: str = "") -> str:
    Lu, Wu = inches(L), inches(W)
    b = inches(BLEED)
    if image:
        scene = (f'<image href="{image}" x="{f(-b)}" y="{f(-b)}" width="{f(Lu + 2 * b)}" height="{f(Wu + 2 * b)}" '
                 f'preserveAspectRatio="xMidYMid slice"/>')
        logo = f'<g transform="translate({f(Lu / 2 - 230)} {f(Wu - 210)}) scale(.72)">{art.logo()}</g>'
    else:
        scene = (f'<svg x="{f(-b)}" y="{f(-b)}" width="{f(Lu + 2 * b)}" height="{f(Wu + 2 * b)}" viewBox="0 0 900 600" '
                 f'preserveAspectRatio="xMidYMid slice">{art.cover_scene("box")}</svg>')
        logo = f'<g transform="translate(26 14) scale(.72)">{art.logo()}</g>'
    return scene + logo


def back_panel(L: float, W: float, edition: str = "seeded") -> str:
    """The underside of the base: what the game is, what is inside, how a round goes."""
    Lu, Wu, b = inches(L), inches(W), inches(BLEED)
    contents = PACKING[edition]["contents"]
    steps = ("Poison: flip up to four tags in secret.", "Audit: spend four tokens to check labels.",
             "Deploy: lock the rule and score eight new cargo.")
    blurb = ("A rival robot has swapped some labels in your training data. Count, suspect, spend your few "
             "trusted checks, and find out whether your sorter learned the right rule.")
    return (f'<rect x="{f(-b)}" y="{f(-b)}" width="{f(Lu + 2 * b)}" height="{f(Wu + 2 * b)}" fill="{C["paper"]}"/>'
            + text(40, 64, "Who changed the labels?", 26, INK, 900, "start")
            + para(40, 96, blurb, 12, 470, weight=500)[0]
            + text(40, 190, "HOW A ROUND GOES", 10, C["red_dk"], 900, "start", spacing=1.5)
            + "".join(f'<circle cx="52" cy="{216 + k * 30}" r="11" fill="{C["mustard"]}" stroke="{INK}" '
                      f'stroke-width="1.4"/>' + text(52, 220 + k * 30, str(k + 1), 11, INK, 900)
                      + text(72, 221 + k * 30, s, 12, INK, 600, "start") for k, s in enumerate(steps))
            + text(40, 330, "INSIDE", 10, C["red_dk"], 900, "start", spacing=1.5)
            + "".join(text(40 + (k // 5) * 240, 354 + (k % 5) * 20, "· " + s, 10.5, INK, 500, "start")
                      for k, s in enumerate(contents))
            + f'<svg x="{f(Lu - 330)}" y="40" width="300" height="300" viewBox="0 0 300 300">'
              f'<rect width="300" height="300" rx="14" fill="url(#shop)"/>'
              f'<g transform="translate(36 32) scale(.62)">{art.mallory("bp")}</g>'
              f'<g transform="translate(140 130) scale(.68)">{art.sorter("bp")}</g>'
              f'<rect width="300" height="300" rx="14" fill="none" stroke="{INK}" stroke-width="2.4"/></svg>'
            + text(Lu - 180, 372, "2 PLAYERS · TARGET 15–20 MIN", 10, INK, 900, spacing=1)
            + para(40, Wu - 52, "Draft 0.1 prototype. Rules, budgets and playing time are working hypotheses "
                   "that playtests have not yet confirmed. github.com/haydn-s/poisoned-dataset-game · Apache 2.0",
                   9, Lu - 80, weight=500)[0])


def lid_walls() -> dict[str, str]:
    L, W, D = (inches(x) for x in LID)
    small = lambda length, words: text(length / 2, D * .52, words, 15, INK, 900, spacing=2.2)
    return {
        "front": f'<g transform="translate({f(L / 2 - 134)} 8) scale(.42)">{art.logo()}</g>',
        "back": small(L, "WHO CHANGED THE LABELS?"),
        "left": small(W, "2 PLAYERS · 15–20 MIN"),
        "right": small(W, "DRAFT 0.1 · PROTOTYPE"),
    }


def sheet_svg(L: float, W: float, D: float, artwork: str, title: str, note: str) -> str:
    flat_w, flat_h = inches(L + 2 * D), inches(W + 2 * D)
    ox, oy = (1700 - flat_w) / 2, (1100 - flat_h) / 2 + 20
    cut, fold = outline(L, W, D), folds(L, W, D)
    i = art.uid("bleedclip", L, W, D)
    b = inches(BLEED)
    bleed = (f"M{f(-b - inches(TAB))} {f(-b)}H{f(flat_w + b + inches(TAB))}V{f(flat_h + b)}"
             f"H{f(-b - inches(TAB))}Z")
    legend = (text(60, 60, title, 22, INK, 900, "start")
              + text(60, 84, note, 11, INK, 500, "start")
              + f'<path d="M60 1040h40" stroke="{INK}" stroke-width="1.4"/>' + text(108, 1044, "cut", 10, INK, 600, "start")
              + f'<path d="M160 1040h40" stroke="{INK}" stroke-width="1.2" stroke-dasharray="6 4"/>'
              + text(208, 1044, "fold (valley: printed side out)", 10, INK, 600, "start")
              + f'<rect x="420" y="1033" width="40" height="14" fill="{C["amber"]}" opacity=".5"/>'
              + text(468, 1044, f"bleed {BLEED} in beyond the cut", 10, INK, 600, "start")
              + text(1640, 1044, f"flat {L + 2 * D:.3f} x {W + 2 * D:.3f} in · print at 100% on 11 x 17 in",
                     10, INK, 600, "end"))
    dims = (f'<path d="M{f(ox + inches(D))} {f(oy - 30)}H{f(ox + inches(D + L))}" stroke="{INK}" stroke-width=".8"/>'
            + text(ox + inches(D + L / 2), oy - 36, f'{L:.4g} in', 10, INK, 700)
            + f'<path d="M{f(ox - 40 - inches(TAB))} {f(oy + inches(D))}V{f(oy + inches(D + W))}" stroke="{INK}" stroke-width=".8"/>'
            + text(ox - 46 - inches(TAB), oy + inches(D + W / 2), f'{W:.4g} in', 10, INK, 700, "end")
            + f'<path d="M{f(ox + flat_w + 40 + inches(TAB))} {f(oy + inches(D + W))}V{f(oy + flat_h)}" '
              f'stroke="{INK}" stroke-width=".8"/>'
            + text(ox + flat_w + 46 + inches(TAB), oy + inches(D + W) + inches(D) / 2, f'{D:.4g} in deep', 10, INK, 700,
                   "start"))
    return (f'<svg viewBox="0 0 1700 1100" role="img" aria-label="{escape(title)}">'
            f'<rect width="1700" height="1100" fill="#fff"/>{legend}{dims}'
            f'<g transform="translate({f(ox)} {f(oy)})">'
            f'<clipPath id="{i}"><path d="{bleed}"/></clipPath><g clip-path="url(#{i})">{artwork}</g>'
            f'<path d="{cut}" fill="none" stroke="{INK}" stroke-width="1.4"/>'
            f'<path d="{fold}" fill="none" stroke="#fff" stroke-width="1.6" stroke-dasharray="6 4"/>'
            f'<path d="{fold}" fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="6 4"/></g></svg>')


def packing_plan(edition: str = "seeded") -> str:
    L, W, D = BASE
    s = 70  # pixels per inch in this diagram
    wells = []
    for k, (name, items) in enumerate(PACKING[edition]["wells"]):
        x = 20 + .1 * s + k * (WELL[0] + .1) * s
        wells.append(f'<rect x="{f(x)}" y="{f(20 + .1 * s)}" width="{f(WELL[0] * s)}" height="{f(WELL[1] * s)}" rx="6" '
                     f'fill="{C["paper_dk"]}" stroke="{INK}" stroke-width="1.4"/>'
                     + f'<rect x="{f(x + (WELL[0] - 2.5) / 2 * s)}" y="{f(20 + .2 * s)}" width="{f(2.5 * s)}" '
                       f'height="{f(3.5 * s)}" rx="5" fill="{C["paper"]}" stroke="{INK}" stroke-dasharray="4 3"/>'
                     + text(x + WELL[0] * s / 2, 20 + 1.9 * s, name, 12, INK, 900)
                     + text(x + WELL[0] * s / 2, 20 + 2.15 * s, items, 9, INK, 500))
    y2 = 20 + (WELL[1] + .2) * s
    x = 20 + .1 * s
    for name, items, width in PACKING[edition]["strip"]:
        wells.append(f'<rect x="{f(x)}" y="{f(y2)}" width="{f(width * s)}" height="{f((W - WELL[1] - .6) * s)}" rx="6" '
                     f'fill="{C["paper_dk"] if "PRIVATE" not in name else "#e9c9bf"}" stroke="{INK}" stroke-width="1.4"/>'
                     + text(x + width * s / 2, y2 + .55 * s, name, 11, INK if "PRIVATE" not in name else C["red_dk"], 900)
                     + text(x + width * s / 2, y2 + .8 * s, items, 9, INK, 500))
        x += (width + .1) * s
    book = (f'<rect x="{f(20 + (L - RULEBOOK[1]) / 2 * s)}" y="{f(20 + (W - RULEBOOK[0]) / 2 * s)}" '
            f'width="{f(RULEBOOK[1] * s)}" height="{f(RULEBOOK[0] * s)}" rx="4" fill="none" stroke="{C["red_dk"]}" '
            f'stroke-width="2" stroke-dasharray="10 6"/>'
            + text(20 + L * s / 2, 20 + W * s - 16, "rulebook (5.5 x 8.5 in) lies on top", 10, C["red_dk"], 800))
    plan = (f'<svg viewBox="0 0 {f(L * s + 40)} {f(W * s + 40)}" style="width:5in" role="img" '
            f'aria-label="Top-down packing plan of the base">'
            f'<rect x="20" y="20" width="{f(L * s)}" height="{f(W * s)}" rx="8" fill="#fff" stroke="{INK}" '
            f'stroke-width="2.4"/>{"".join(wells)}{book}</svg>')
    rows = [("Base (tray)", f"{BASE[0]} x {BASE[1]} x {BASE[2]} in outer",
             f"flat {BASE[0] + 2 * BASE[2]:.3f} x {BASE[1] + 2 * BASE[2]:.3f} in"),
            ("Lid", f"{LID[0]:.4g} x {LID[1]:.4g} x {LID[2]} in, {CLEARANCE} in over the base",
             f"flat {LID[0] + 2 * LID[2]:.3f} x {LID[1] + 2 * LID[2]:.3f} in"),
            ("Card wells", f"three {WELL[0]} x {WELL[1]} in", "poker cards 2.5 x 3.5 in, sleeve room"),
            ("Rulebook", "5.5 x 8.5 in, 12 pages, saddle-stitched", "lies flat over the wells"),
            ("Bleed / safe", f"{BLEED} in bleed; keep text {BLEED} in inside folds", "glue tabs 0.5 in")]
    table = "".join(f"<tr><th>{escape(a)}</th><td>{escape(b)}</td><td>{escape(c)}</td></tr>" for a, b, c in rows)
    checks = ("Print the dielines on 11 x 17 in cardstock at 100%, score the folds, and fit the real kit before "
              "choosing final dimensions.",
              "Board thickness changes the clearance: rigid box board needs about 0.1 in more than cardstock.",
              "Confirm the supplier's own template, bleed, safe area, proof process, price and delivery date "
              "against the November 23 deadline before ordering.",
              PACKING[edition]["check"])
    return (f'<section class="letter"><h1>Packing plan and box specification</h1>'
            f'<p>Telescoping two-piece box. Everything fits in one layer under the rulebook.</p>'
            f'<div class="cols"><div>{plan}</div><div><h2>Dimensions</h2><table>{table}</table>'
            f'<h2>Before production</h2><ul>{"".join(f"<li>{escape(c)}</li>" for c in checks)}</ul></div></div>'
            f"</section>")


def image_uri(path: Path) -> str:
    kind = mimetypes.guess_type(path.name)[0]
    if kind not in ("image/png", "image/jpeg", "image/webp"):
        raise ValueError("Cover image must be a PNG, JPEG or WebP file")
    return f"data:{kind};base64,{b64encode(path.read_bytes()).decode('ascii')}"


def build(out: Path, cover_image: Path | None = None, edition: str = "seeded") -> None:
    image = image_uri(cover_image) if cover_image else ""
    L, W, D = LID
    lid = sheet_svg(L, W, D, panel_art(L, W, D, cover_top(L, W, image), lid_walls(), "lid"),
                    "Lid dieline", "Printed side shown. Cut, score the dashed folds, fold the walls down and glue "
                                   "the tabs inside the short walls.")
    bL, bW, bD = BASE
    base = sheet_svg(bL, bW, bD, panel_art(bL, bW, bD, back_panel(bL, bW, edition), {}, "base"),
                     "Base dieline", "The centre panel is the underside of the box. Fold the walls up, printed side "
                                     "out, and glue the tabs inside the short walls.")
    body = f'<section class="tabloid">{lid}</section><section class="tabloid">{base}</section>{packing_plan(edition)}'
    (out / "box.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Poisoned Dataset box mockup</title>'
        f"<style>{STYLE}</style></head><body>{art.defs(include_cover=True)}{body}</body></html>\n", encoding="utf-8")
