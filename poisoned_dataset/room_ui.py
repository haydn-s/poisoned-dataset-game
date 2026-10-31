"""Presentation for the digital game room. Receives only the player's safe view."""

from base64 import b64encode
from html import escape

import streamlit as st

from . import art
from .core import RULES, errors, fit


def brand(code=None, round_=None):
    detail = f'ROOM <strong>{escape(code)}</strong>' if code else '2 PLAYERS · ONE SHARED TABLE'
    if round_:
        detail = f'ROUND {round_["number"]}/2 · {escape(round_["deck"].upper())} &nbsp; / &nbsp; ' + detail
    st.html('<div class="brandbar"><div class="brand"><span class="brandmark">◒</span>'
            f'Poisoned Dataset</div><div class="room-badge">{detail}</div></div>')


def hero():
    st.html(f'<div class="hero"><img src="{art.asset_uri("illustrations/label-swap-v02.png")}" '
            'alt="Mallory swaps a cargo label while Sorter inspects the moon-colony workshop.">'
            '<div class="hero-copy"><div class="eyebrow">WELCOME TO THE MOON COLONY</div>'
            '<h1>A little<br>sabotage.<br>A lot at stake.</h1>'
            '<p>A rival has tampered with your robot’s training data. Pull up a chair. '
            'Find the bad labels. Outsmart the other side.</p></div>'
            '<div class="hero-footer"><span>2 PLAYERS</span><span>2 ROUNDS</span>'
            '<span>15–20 MIN</span></div></div>')


def players(view):
    r = view.get("round", {"attacker": "B", "defender": "A"})
    phase = view["phase"]
    acting = r.get("attacker") if phase == "attack" else r.get("defender") if phase == "audit" else None
    scores = {item["result"]["defender"]: item["result"]["points"] for item in view["history"]}
    for col, seat in zip(st.columns(2), ("A", "B")):
        is_attacker = seat == r["attacker"]
        role = "attacker" if is_attacker else "defender"
        character = "mallory" if is_attacker else "sorter"
        active = seat == acting
        name = view["players"].get(seat, "Open seat")
        if seat not in view["players"]:
            status = "Waiting for player…"
        elif phase == "lobby":
            status = "Attacks first" if is_attacker else "Defends first"
        elif phase == "complete":
            status = "Match complete"
        elif phase == "reveal":
            status = "Ready for round two" if seat in r["ready"] else "Reviewing the round"
        else:
            status = "Your move" if active and seat == view["seat"] else "Making a move" if active else "At the table"
        with col, st.container(key=f"player_{seat}_{'active' if active else 'waiting'}"):
            portrait, nameplate, score = st.columns([1, 3.2, .9], gap="small", vertical_alignment="center", wrap=False)
            portrait.image(str(art.ASSET_ROOT / "characters" / f"{character}-v02.png"), width=74)
            you = '<span class="player-you">YOU</span>' if seat == view["seat"] else ''
            nameplate.html(f'<div class="player-role {role}">{character.upper()} · {role}</div>'
                           f'<div class="player-name">{escape(name)}{you}</div>'
                           f'<div class="player-status {"active" if active else ""}">{status}</div>')
            score.html(f'<div class="player-score">{scores.get(seat, "—")}<small>OUT OF 8</small></div>')


def phases(view):
    current = ("attack", "audit", "reveal").index(view["phase"])
    labels = ("Secret sabotage", "Audit & lock", "The reveal")
    steps = ''.join(f'<div class="phase {"active" if i == current else "done" if i < current else ""}">'
                    f'<b>{"✓" if i < current else f"0{i + 1}"}</b>{label}</div>' for i, label in enumerate(labels))
    st.html(f'<div class="phase-track" aria-label="Round progress">{steps}</div>')
    r = view["round"]
    if current == 2:
        message = "Round complete. Compare notes before switching seats."
    else:
        seat = r["attacker"] if current == 0 else r["defender"]
        whose = "Your turn" if view["seat"] == seat else f'{view["players"][seat]}’s turn'
        message = f'{whose} · ' + ("up to four labels can be flipped" if current == 0 else "each audit checks one label")
    st.html(f'<div class="turn-note"><span class="light"></span>{escape(message)}</div>')


def learner(cards, labels, prefix="Current"):
    counts, rule = errors(cards, labels), fit(cards, labels)
    symbols = {"red": "●", "round": "○", "striped": "▧"}
    tiles = []
    for priority, candidate in enumerate(RULES, 1):
        badge = '<span class="rule-selected">ROBOT’S PICK</span>' if rule == candidate else ''
        tiles.append(f'<div class="rule-tile {"selected" if candidate == rule else ""}">{badge}'
                     f'<div class="rule-icon">{symbols[candidate]}</div><div><small>RULE 0{priority}</small>'
                     f'<div class="rule-title">STORE if {candidate}</div></div>'
                     f'<div class="rule-count">{counts[candidate]}<small>error{"s" if counts[candidate] != 1 else ""}</small></div></div>')
    st.html('<div class="rule-rack">' + ''.join(tiles) + '</div>')
    st.caption(f"{prefix} learner: **{rule.upper()}** · Fewest errors wins. Ties: red → round → striped.")


def tokens(remaining, kind="audit"):
    glyph = "⌕" if kind == "audit" else "↔"
    chips = ''.join(f'<span class="token {"spent" if i >= remaining else ""}" aria-hidden="true">'
                    f'{glyph if i < remaining else "×"}</span>' for i in range(4))
    label = "audit tokens remain" if kind == "audit" else "flips available"
    st.html(f'<div class="token-tray" aria-label="{remaining} of 4 {label}">{chips}</div>'
            f'<div class="token-label">{remaining}/4 {label}</div>')


def sealed_table(title, text):
    st.html('<div class="waiting-table"><div class="card-fan" aria-hidden="true">'
            '<div class="card-back">◒</div><div class="card-back">◒</div><div class="card-back">◒</div></div>'
            f'<h2>{escape(title)}</h2><p>{escape(text)}</p></div>')


@st.cache_data
def cargo_image(features):
    # The same precise illustrated cargo used by the printed game, in an isolated SVG.
    defs = art.DEFS_BASE.replace('</defs>', f'<image id="grain" href="{art.grain_tile()}" width="64" height="64"/></defs>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 226 162">'
           + defs + art.cargo(*features, key="digital") + '</svg>')
    return "data:image/svg+xml;base64," + b64encode(svg.encode()).decode()
