"""The fixed-deck edition: one printed set that serves every match.

Four fixed training decks replace per-seed printing. Three truth cards and sixteen
reference cards replace the private audit slips and deployment keys: the attacker
draws a truth card in secret, and for each of the eight cargo types lays the matching
reference card face down. Rules and deck selection: docs/fixed-deck-edition.md.
"""

from itertools import product
from pathlib import Path

from . import art, decks
from .art import C, INK, para, rrect, text
from .components import (TAGS, SPARE_TAGS, aid_card, back, card, cargo_card, document, manifest, panel, role_card,
                         rule_card, score_card, sheet, sort_columns, tokens_sheet)
from .core import LABELS, RULES, Card, test_deck

DECK_TONE = {"A": (C["mustard"], INK), "B": (C["teal"], C["paper"]), "C": ("#8c9a3a", INK), "D": ("#6b4f9e", C["paper"])}
DEPLOY = ("DEPLOY", "#24407e", C["paper"])
PROFILES = tuple(product((1, 0), repeat=3))  # red, round, striped
STEPS = ("Attacker secretly flips up to 4 tags.",
         "Defender counts each rule's errors. Looking is free.",
         "Audit: pay a token, turn that cargo's reference card, set the tag to match.",
         "Lock the fewest-error rule. Ties: red, round, striped.",
         "Reveal the truth card. 1 point per test card the locked rule gets right.",
         "Check every reference card against the truth; switch roles.")
ATTACKER = "Draw a truth card in secret, tag the deck by it, lay the reference row, then flip up to four tags."
PRINT_NOTE = "Cut on the crop marks. Cards are 2.5 x 3.5 in; print at 100% (actual size) on US Letter, landscape."
DUPLEX_NOTE = "Duplex: flip on the short edge; check one sheet against a lamp first."


def truth_front(rule: str) -> str:
    band = (f'<path d="{rrect(9, 9, 232, 86, 12)[0]}" fill="url(#night)"/>' + art.stars("truth" + rule, 232, 86, 14)
            + text(125, 50, "TRUTH", 30, C["paper"], 900, spacing=4)
            + text(125, 74, "SECRET UNTIL SCORING", 8.5, C["paper"], 800, spacing=1.5))
    body = (band + text(125, 122, f"STORE if {rule}", 19, INK, 900)
            + text(125, 140, "otherwise RECYCLE", 10, INK, 700) + sort_columns(rule, 150)
            + para(125, 302, "Tag every training card by this rule, lay the reference row, then flip up to four tags.",
                   9, 205, anchor="middle", weight=600)[0])
    return card("truth", f"Truth card: STORE if {rule}", body)


def truth_back() -> str:
    scene = (f'<rect width="250" height="350" fill="url(#night)"/>{art.stars("truthback", 250, 350, 60)}'
             f'<g transform="translate(125 130)">{art.porthole(68, "truthback")}</g>'
             + art.grain(art.box(250, 350), "truthback", .5)
             + text(125, 250, "TRUTH", 24, C["paper"], 900, spacing=4)
             + text(125, 274, "ATTACKER DRAWS ONE IN SECRET", 8.5, C["paper"], 800, spacing=1)
             + text(125, 296, "Shuffle all three face down first.", 9, C["paper"], 500))
    return card("back-truth", "Truth card back", scene, frame=False)


def reference_front(features: tuple[int, int, int], label: int) -> str:
    """One trusted label for one cargo type. Both labels share a dark ground so neither shows through."""
    c = Card("REF", *features)
    seal = (f'<circle cx="206" cy="40" r="18" fill="{C["red_dk"]}" stroke="{C["paper"]}" stroke-width="1.5"/>'
            + text(206, 47, "T", 18, C["paper"], 900) + text(206, 70, "TRENT", 7, C["paper"], 800, spacing=.8))
    body = (f'<rect width="250" height="350" fill="url(#night)"/>{art.stars("ref", 250, 90, 14)}' + seal
            + text(22, 38, "TRUSTED", 15, C["paper"], 900, "start", spacing=1.5)
            + text(22, 56, "REFERENCE", 15, C["paper"], 900, "start", spacing=1.5)
            + f'<g transform="translate(125 125)">{art.cargo_icon(*features, 70)}</g>'
            + text(125, 186, c.describe(), 11, C["paper"], 700)
            + f'<g transform="translate(29 206) scale(1.2)">{art.tag(LABELS[label], 160, 55, "refl" + LABELS[label])}</g>'
            + para(125, 302, "Set the audited card's tag to this label. Leave this card face up.", 9.5, 200,
                   anchor="middle", weight=600, fill=C["paper"])[0])
    return card("trusted-reference", f"Reference card: {c.describe()} is {LABELS[label]}", body)


def reference_back(features: tuple[int, int, int]) -> str:
    """Identical for the STORE and RECYCLE card of a cargo type, so the face-down row reveals nothing."""
    c = Card("REF", *features)
    body = (text(22, 38, "REFERENCE", 15, INK, 900, "start", spacing=1.5)
            + text(228, 37, "AUDIT ONLY", 8, INK, 800, "end", spacing=1)
            + panel(art.cargo(*features, "refback"), ("refback", features)) + manifest(c)
            + para(125, 282, "Turn over only when you pay to audit a training card with this cargo.", 9.5, 200,
                   anchor="middle", weight=600)[0])
    return card("back-trusted-reference", f"Reference card back: {c.describe()}", body)


def mirrored(faces: list[str]) -> list[str]:
    """Back-sheet order for a 4 x 2 sheet printed duplex with a short-edge flip."""
    return [face for row in range(0, len(faces), 4) for face in reversed(faces[row:row + 4])]


def build(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=False)
    cards, duplex, backs = [], [], []
    for letter in decks.LETTERS:
        tone, ink = DECK_TONE[letter]
        deck = decks.deck(letter)
        for start in range(0, len(deck), 8):
            cards.append(sheet(f"Deck {letter} training cards {start + 1}-{start + 8}",
                               f"Fixed edition · deck {letter} (development seed {decks.FIXED_DECKS[letter]}). "
                               f"{PRINT_NOTE}",
                               "".join(cargo_card(c, 0, chip=(f"DECK {letter}", tone, ink))
                                       for c in deck[start:start + 8])))
        backs.append(sheet(f"Optional backs · deck {letter}", f"Print on the reverse of deck {letter}'s three sheets.",
                           back("training", tone=tone, subtitle=f"DECK {letter}") * 8))
    cards.append(sheet("Test deck", "Eight deployment cargo cards, one per type, shared by every round. Keep them "
                       "aside until the rule is locked.", "".join(cargo_card(c, 0, True, DEPLOY) for c in test_deck())))
    backs.append(sheet("Optional backs · test deck", "Print on the reverse of the test deck sheet.",
                       back("test", subtitle="DEPLOYMENT") * 8))
    for label in (1, 0):
        duplex.append(sheet(f"Reference cards · {LABELS[label]} side up",
                            f"Eight trusted {LABELS[label]} labels, one per cargo type. {DUPLEX_NOTE}",
                            "".join(reference_front(p, label) for p in PROFILES)))
        duplex.append(sheet("Reference card backs", "Backs for the sheet before this one; mirrored for duplex.",
                            "".join(mirrored([reference_back(p) for p in PROFILES]))))
    faces = [truth_front(rule) for rule in RULES] + [rule_card(i, rule) for i, rule in enumerate(RULES)]
    faces += [score_card(), aid_card(STEPS)]
    duplex.append(sheet("Truth cards, rule cards, score card and quick reference",
                        f"The truth cards share one back, so a drawn truth stays secret. {DUPLEX_NOTE}",
                        "".join(faces)))
    duplex.append(sheet("Backs for the truth and rules sheet", "Mirrored for duplex.",
                        "".join(mirrored([truth_back()] * 3 + [back("reference")] * 5))))
    cards.append(sheet("Quick reference and role cards", "The second quick reference and the two role cards.",
                       aid_card(STEPS) + role_card("ATTACKER", ATTACKER) + role_card("DEFENDER")))
    cards.append(sheet("Label tags and audit tokens",
                       f"{TAGS} tags plus {SPARE_TAGS} spares, reused every round. Cut each strip out, fold on the "
                       "dotted line, glue back to back, and trim the notches: one side STORE, the other RECYCLE.",
                       tokens_sheet(), cards=False))
    (out / "cards.html").write_text(document("Poisoned Dataset fixed edition: single-sided sheets", cards),
                                    encoding="utf-8")
    (out / "duplex.html").write_text(document("Poisoned Dataset fixed edition: double-sided sheets", duplex),
                                     encoding="utf-8")
    (out / "backs.html").write_text(document("Poisoned Dataset fixed edition: optional backs", backs), encoding="utf-8")
