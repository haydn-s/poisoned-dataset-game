"""Printable, self-contained HTML with separate public and secret materials."""

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from .core import LABELS, RULES, Card, generate, predict, test_deck

STYLE = """
@page { size: letter; margin: .4in; }
* { box-sizing: border-box; }
body { margin: 0; color: #172332; font: 12pt system-ui, sans-serif; background: #e8ecf0; }
.page { width: 7.65in; min-height: 9.8in; margin: .2in auto; padding: .1in;
        background: white; break-after: page; }
.page:last-child { break-after: auto; }
h1 { margin: 0 0 .08in; font-size: 17pt; }
p { margin: .05in 0 .12in; font-size: 10pt; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .08in; }
.card { height: 2.08in; border: 1px dashed #687587; padding: .09in; text-align: center;
        break-inside: avoid; display: flex; flex-direction: column; align-items: center;
        justify-content: space-between; }
.card strong { font-size: 12pt; }
.card svg { width: .82in; height: .82in; }
.card small { font-size: 10pt; }
.label-slot { border: 1px solid #687587; width: 95%; height: .33in; font-size: 10pt; padding: .04in; }
.compact .card { height: .94in; justify-content: center; gap: .05in; }
.compact { grid-template-columns: repeat(4, 1fr); }
.tokens { grid-template-columns: repeat(3, 1fr); justify-items: center; }
.tokens .card { width: 2in; height: .3in; padding: .02in; }
.private { border-top: 7px solid #9d2424; }
@media print { body { background: white; } .page { margin: 0; padding: 0; min-height: 0; } }
"""


def page(title: str, note: str, items: list[str], compact: bool = False, tokens: bool = False) -> str:
    return (f'<section class="page"><h1>{escape(title)}</h1><p>{escape(note)}</p>'
            f'<div class="grid{" compact" if compact else ""}{" tokens" if tokens else ""}">{"".join(items)}</div></section>')


def document(title: str, pages: list[str], private: bool = False) -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{escape(title)}</title><style>{STYLE}</style></head>'
            f'<body class="{"private" if private else ""}">{"".join(pages)}</body></html>\n')


def picture(card: Card) -> str:
    color = "#bd333d" if card.red else "#2759a8"
    shape = (f'<circle cx="50" cy="50" r="40" fill="{color}" stroke="#172332" stroke-width="3"/>'
             if card.round else
             f'<rect x="10" y="10" width="80" height="80" fill="{color}" stroke="#172332" stroke-width="3"/>')
    stripes = '<path d="M32 24v52 M50 16v68 M68 24v52" stroke="white" stroke-width="7"/>' if card.striped else ""
    return f'<svg viewBox="0 0 100 100" role="img" aria-label="{card.describe()}">{shape}{stripes}</svg>'


def card_face(card: Card, round_number: int, test: bool = False) -> str:
    slot = "Predict, then reveal" if test else "Place label token here"
    return (f'<div class="card"><strong>Round {round_number} · {card.id}</strong>'
            f'{picture(card)}<small>{card.describe()}</small><div class="label-slot">{slot}</div></div>')


def build(out: Path, seed: int, regime: str) -> None:
    scenarios = [generate(seed + r, regime=regime) for r in range(2)]
    out.mkdir(parents=True, exist_ok=False)
    public, private = [], []
    for r, scenario in enumerate(scenarios, 1):
        for start in (0, 12):
            public.append(page(f"Poisoned Dataset · Round {r} training cards",
                               f"Draft 0.1 · seed {scenario.seed} · {regime} · Cut dashed borders. Labels use movable tokens.",
                               [card_face(c, r) for c in scenario.cards[start:start + 12]]))
        public.append(page(f"Round {r} independent test deck",
                           "Keep aside until the learned rule is locked. These eight cards score uniform deployment.",
                           [card_face(c, r, True) for c in test_deck()]))
        slips = [f'<div class="card"><strong>Round {r} · {c.id}</strong><span>{LABELS[y]}</span></div>'
                 for c, y in zip(scenario.cards, scenario.clean_labels)]
        private.append(page(f"PRIVATE · Round {r} trusted audit slips",
                            "Attacker sets initial labels from these. Cut, fold with labels inside, and write IDs outside. Open only paid-for IDs.",
                            slips, True))
        private.append(page(f"PRIVATE · Round {r} final reveal",
                            f"Attacker only before play. True rule: {scenario.true_rule}. Keep test references covered until the rule is locked.",
                            [f'<div class="card"><strong>Round {r} · {c.id}</strong><span>{LABELS[predict(scenario.true_rule, c)]}</span></div>'
                             for c in test_deck()], True))
    rules = [f'<div class="card"><strong>Rule {i + 1}: {rule}</strong><span>STORE if {rule}; otherwise RECYCLE.</span>'
             f'<small>Wins a training-error tie against rules {", ".join(RULES[i + 1:]) or "none"}.</small></div>'
             for i, rule in enumerate(RULES)]
    rules += [f'<div class="card"><strong>Audit token {i + 1}</strong><span>Reveal one trusted label and replace its token.</span></div>' for i in range(4)]
    rules += ['<div class="card"><strong>Score</strong><span>Round 1 defender A: ___ / 8</span><span>Round 2 defender B: ___ / 8</span><small>Higher defender score wins. Equal scores draw.</small></div>']
    public.append(page("Candidate rules and four audit tokens",
                       "Pick the rule with the fewest mismatches to the current labels. Ties: red, round, striped.", rules))
    public.append(page("Movable label tokens",
                       "Cut the 2 × 0.3 inch tokens along the dashed borders. Reuse them in round two; do not write labels on feature cards.",
                       [f'<div class="card"><strong>{label}</strong></div>' for label in LABELS for _ in range(24)],
                       True, True))
    (out / "public.html").write_text(document("Poisoned Dataset public components", public), encoding="utf-8")
    (out / "private.html").write_text(document("Poisoned Dataset private references", private, True), encoding="utf-8")
    (out / "scenario.json").write_text(json.dumps([asdict(s) for s in scenarios], indent=2) + "\n", encoding="utf-8")
