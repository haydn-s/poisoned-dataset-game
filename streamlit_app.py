"""Run with: streamlit run streamlit_app.py"""

from base64 import b64encode
from html import escape
import json
import os
from pathlib import Path

import streamlit as st

from poisoned_dataset import art
from poisoned_dataset.core import (LABELS, RULES, Card, conflict_scores, errors,
                                   fit, flip_labels, predict, test_deck)
from poisoned_dataset.rooms import RoomError, RoomStore

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Poisoned Dataset · Playtest", page_icon="🌒", layout="wide")


@st.cache_resource
def get_store(path):
    return RoomStore(path)


store = get_store(os.environ.get("POISONED_DATASET_DB", str(ROOT / "data" / "playtests.sqlite3")))

st.html("""<style>
.block-container {max-width: 1260px; padding-top: 2rem;}
h1,h2,h3 {letter-spacing: -.035em;}
.eyebrow {font-size: .75rem; letter-spacing: .16em; font-weight: 700; color: #8b5841; margin-bottom: .6rem;}
.intro {font-size: 1.14rem; line-height: 1.65; max-width: 620px; color: #635749;}
.cargo-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px;}
.cargo-card {border: 1px solid #d7cbbb; border-radius: 10px; padding: 11px; background: #fffaf1; margin: 7px 0;}
.cargo-card.verified {border: 2px solid #458174; padding: 10px;}
.cargo-card.flipped {border: 2px solid #b65036; padding: 10px;}
.cargo-top {display:flex; justify-content:space-between; font: 700 .75rem monospace; min-height: 20px;}
.cargo-card img {width: 100%; height: 94px; object-fit: contain; margin: 4px 0;}
.cargo-features {font-size: .78rem; color:#655b4f; margin-bottom: 7px;}
.tag {display: inline-block; border:1px solid #c3b6a1; border-radius:4px; padding:4px 10px; font-size:.72rem; letter-spacing:.08em; font-weight:800;}
.tag.recycle {background:#3c3931;color:#fff7e8;border-color:#3c3931;}
.tag.store {background:#f2e1b8;color:#382c1e;}
.steps {display:flex; gap:8px; flex-wrap:wrap; margin: 12px 0 22px;}
.step {padding: 6px 12px; border-radius: 20px; background:#ebe3d5; font-size:.8rem;}
.step.active {background:#3c5b53; color:white;}
[data-testid="stMetric"] {border-top: 2px solid #d4c3a6; padding-top:10px;}
@media (max-width: 800px) {.cargo-grid {grid-template-columns:repeat(3,minmax(0,1fr));}}
@media (max-width: 640px) {.block-container {padding:1rem;} .cargo-card img {height:75px;}
  .cargo-grid {grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}}
</style>""")


def rules():
    st.markdown("""
    **Two players · Two rounds · Four flips · Four audits**

    Each cargo card is red/blue, round/square, and striped/plain. The secret true
    rule says **STORE if red**, **STORE if round**, or **STORE if striped**;
    otherwise RECYCLE. Only the attacker knows it before scoring.

    1. **Poison:** the attacker flips up to four distinct training labels, then commits.
    2. **Audit:** the defender checks up to four cards, one at a time. Each check
       reveals and repairs only that card. A correct label still costs one token.
    3. **Lock:** the robot must use the rule with the fewest training errors.
       Ties always go **red → round → striped**. Verified cards have normal weight.
    4. **Reveal:** score one point per correct test card, out of eight. Switch roles
       for round two so each player defends once.

    **Match winner:** higher defender score, then more poisoned labels found,
    then fewer tokens spent. Otherwise it is a draw. An unused token does not
    change a round's score. Identical cargo copies each need their own paid audit.
    """)
    st.caption("The app deals and verifies the reference labels automatically. Inspection, sorting, "
               "and counting are free. Use a call or sit together to discuss the reveal.")


def enter(credentials):
    st.session_state["credentials"] = credentials
    st.query_params["room"] = credentials[0]
    st.rerun()


def landing():
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.html('<div class="eyebrow">A MOON-COLONY GAME OF DATA SABOTAGE</div>')
        st.title("Poisoned Dataset")
        st.html('<p class="intro">One robot. A few bad labels. Can you find the sabotage '
                'before your sorting rule is set?</p>')
        st.image(str(ROOT / "assets/art/illustrations/label-swap-v02.png"), width="stretch")
        st.caption("DIGITAL PLAYTEST · 2 PLAYERS PER ROOM · ABOUT 15–20 MINUTES")
    with right:
        st.subheader("Pull up a seat")
        st.write("Play on separate devices. Create a room, then share this app's address and your room code.")
        create, join, resume = st.tabs(["Create room", "Join room", "Reconnect"])
        with create, st.form("create_room"):
            name = st.text_input("Your alias", max_chars=32)
            edition = st.selectbox("Training decks", ["fixed", "fresh"],
                                   format_func=lambda e: "Fixed edition · decks A–D" if e == "fixed"
                                   else "Fresh decks · generated each match")
            st.caption("Same rules in both editions. Fixed decks match the latest printed game; "
                       "fresh decks match the generated playtest kit.")
            if st.form_submit_button("Create room", type="primary", width="stretch"):
                try:
                    enter(store.create(name, edition))
                except RoomError as exc:
                    st.error(str(exc))
        with join, st.form("join_room"):
            code = st.text_input("Room code", value=st.query_params.get("room", ""), max_chars=6)
            name = st.text_input("Your alias", max_chars=32, key="join_alias")
            if st.form_submit_button("Join room", type="primary", width="stretch"):
                try:
                    enter(store.join(code, name))
                except RoomError as exc:
                    st.error(str(exc))
        with resume, st.form("reconnect"):
            code = st.text_input("Room code", value=st.query_params.get("room", ""), key="resume_room")
            token = st.text_input("Private reconnect code", type="password")
            if st.form_submit_button("Return to my seat", width="stretch"):
                try:
                    view = store.view(code, token.strip())
                    enter((view["code"], token.strip()))
                except RoomError as exc:
                    st.error(str(exc))
        with st.expander("How to play", expanded=True):
            rules()


def act(view, action, payload=None):
    code, token = st.session_state["credentials"]
    try:
        store.act(code, token, view["revision"], action, payload)
    except RoomError as exc:
        st.session_state["notice"] = str(exc)
    st.rerun()


def learner(cards, labels, prefix="Current"):
    counts, rule = errors(cards, labels), fit(cards, labels)
    cols = st.columns(3)
    for col, candidate in zip(cols, RULES):
        count = counts[candidate]
        col.metric(f"STORE if {candidate}", f"{count} error{'s' if count != 1 else ''}",
                   delta="Selected rule" if candidate == rule else None, delta_color="off")
    st.caption(f"{prefix} learner: **{rule.upper()}**. Fewest errors wins; ties go red → round → striped.")


@st.cache_data
def cargo_image(features):
    # Reuse the game's vector symbols. Self-contained images avoid shared SVG IDs.
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-48 -48 96 96">'
           + art.cargo_icon(*features, size=70) + '</svg>')
    return "data:image/svg+xml;base64," + b64encode(svg.encode()).decode()


def board(cards, labels, verified=(), flipped=(), key="board"):
    sort = st.radio("Arrange cargo", ["Card order", "Look-alike groups", "Current label"],
                    horizontal=True, key=f"sort_{key}")
    order = list(range(len(cards)))
    if sort == "Look-alike groups":
        order.sort(key=lambda i: (cards[i].features, cards[i].id))
    elif sort == "Current label":
        order.sort(key=lambda i: (labels[i], cards[i].id))
    tiles = []
    for i in order:
        card = cards[i]
        state = "verified" if i in verified else "flipped" if i in flipped else ""
        flag = "✓ VERIFIED" if i in verified else "↔ FLIPPED" if i in flipped else ""
        tiles.append(f'<div class="cargo-card {state}"><div class="cargo-top">'
                     f'<span>{escape(card.id)}</span><span>{flag}</span></div>'
                     f'<img src="{cargo_image(card.features)}" alt="{card.describe()}">'
                     f'<div class="cargo-features">{card.describe()}</div>'
                     f'<span class="tag {LABELS[labels[i]].lower()}">{LABELS[labels[i]]}</span></div>')
    st.html('<div class="cargo-grid">' + ''.join(tiles) + '</div>')


def audit_log(audits):
    if audits:
        st.dataframe([{"Check": n + 1, "Card": a["card"], "Before": LABELS[a["before"]],
                       "Trusted label": LABELS[a["after"]],
                       "Found poison": "Yes" if a["before"] != a["after"] else "No",
                       "Learner after check": a["rule"]} for n, a in enumerate(audits)],
                     hide_index=True, width="stretch")


def attack(view):
    r, seat = view["round"], view["seat"]
    if seat != r["attacker"]:
        st.info(f'{view["players"][r["attacker"]]} is preparing the poisoned training set. '
                'Your board will appear when the attack is committed.')
        st.write("You will have four audit tokens. Each check reveals and repairs one label. "
                 "Look for disagreeing copies of the same cargo type.")
        return
    st.subheader("Prepare your sabotage")
    st.info(f'Your secret truth: **STORE if {r["truth"].upper()}**, otherwise RECYCLE.')
    st.write("Choose up to four labels to flip. Preview the robot's rule, then commit your attack.")
    cards = tuple(Card(**c) for c in r["cards"])
    chosen = st.multiselect("Labels to flip", list(range(24)), max_selections=4,
                            format_func=lambda i: f"{cards[i].id} · {cards[i].describe()} · "
                            f"{LABELS[r['clean'][i]]} → {LABELS[1 - r['clean'][i]]}",
                            key=f"flips_{view['code']}_{r['number']}")
    labels = flip_labels(r["clean"], chosen)
    learner(cards, labels, "Preview")
    if st.button(f"Commit attack · {len(chosen)}/4 flips", type="primary"):
        act(view, "attack", list(chosen))
    st.caption("Only your committed labels are shown to the defender. You cannot change them after committing.")
    board(cards, labels, flipped=chosen, key=f"attack_{r['number']}")


def defend(view):
    r = view["round"]
    cards = tuple(Card(**c) for c in r["cards"])
    verified = {a["index"] for a in r["audits"]}
    remaining = 4 - len(verified)
    playing = view["seat"] == r["defender"]
    st.subheader("Inspect. Audit. Decide.")
    if not playing:
        st.info(f'{view["players"][r["defender"]]} is auditing. Your attack is locked; watch the learner update.')
    learner(cards, r["labels"])
    left, right = st.columns([2, 1], gap="large")
    with left:
        st.markdown(f"**{remaining}/4 audit tokens remain** · "
                    f"{sum(a['before'] != a['after'] for a in r['audits'])} poisoned labels found")
        if playing:
            choices = [i for i in range(24) if i not in verified]
            selected = st.selectbox("Choose one card to audit", choices,
                                    format_func=lambda i: f"{cards[i].id} · {cards[i].describe()} · {LABELS[r['labels'][i]]}",
                                    disabled=remaining == 0, key=f"audit_choice_{r['number']}_{len(verified)}")
            if st.button("Spend 1 token · audit card", disabled=remaining == 0, type="primary"):
                act(view, "audit", selected)
            st.caption("Even a correct label costs one token. Look-alike copies are not repaired automatically.")
    with right:
        if playing:
            st.write(f'Locking now deploys **{r["rule"].upper()}**.')
            st.caption("You may stop early. Locking ends this round and reveals the truth.")
            if st.button(f"Lock {r['rule'].upper()} & reveal", width="stretch"):
                act(view, "lock")
    with st.expander("Audit trail", expanded=bool(verified)):
        audit_log(r["audits"])
        if not verified:
            st.caption("No cards checked yet.")
    with st.expander("Optional conflict hint"):
        if st.checkbox("Show a suggestion based on visible labels", key=f"hint_{r['number']}"):
            scores = conflict_scores(cards, r["labels"], verified)
            best = max(scores.values())
            st.write("Suggested cards: " + ", ".join(cards[i].id for i, score in scores.items() if score == best))
            st.caption("Contradictions with verified copies come first, then disagreement among look-alikes. "
                       "This is a clue, not proof of poison.")
    board(cards, r["labels"], verified=verified, key=f"audit_{r['number']}")


def reveal(round_, players):
    result = round_["result"]
    st.subheader(f'Round {round_["number"]} · {players[result["defender"]]} scores {result["points"]}/8')
    st.write(f'True rule: **{round_["truth"].upper()}** · Locked rule: **{result["rule"].upper()}** · '
             f'{result["found"]} poison found · {result["spent"]} tokens spent')
    st.caption("Changed labels: " + (", ".join(round_["cards"][i]["id"] for i in round_["flips"]) or "None"))
    st.write(f'Learner after poisoning: **{round_["attack_rule"].upper()}** → '
             f'after auditing: **{result["rule"].upper()}**')
    audit_log(round_["audits"])
    with st.expander("Test all eight cargo types", expanded=True):
        st.dataframe([{"Test card": c.id, "Cargo": c.describe(),
                       "Robot": LABELS[predict(result["rule"], c)],
                       "Truth": LABELS[predict(round_["truth"], c)],
                       "Result": "Correct" if predict(result["rule"], c) == predict(round_["truth"], c)
                       else "Incorrect"} for c in test_deck()], hide_index=True, width="stretch")
    with st.expander("Review every training label"):
        st.dataframe([{"Card": c["id"], "Cargo": Card(**c).describe(), "Clean": LABELS[round_["clean"][i]],
                       "Supplied": LABELS[round_["supplied"][i]], "Final": LABELS[round_["labels"][i]],
                       "Flipped": i in round_["flips"]} for i, c in enumerate(round_["cards"])],
                     hide_index=True, width="stretch")
    st.info("Discuss: which labels changed the competition between rules? "
            "Did finding poison immediately change the robot's rule?")


def finished(view):
    outcome, players = view["outcome"], view["players"]
    name = players.get(outcome["winner"])
    st.title(f"{name} wins the match" if name else "The match is a draw")
    reason = {"points": "defender score", "found": "more poisoned labels found",
              "spent": "fewer audit tokens spent", "draw": "equal scores and tiebreakers"}
    st.caption("Decided by " + reason[outcome["decided_by"]] + ".")
    st.dataframe([{"Player": players[r["result"]["defender"]], "Score / 8": r["result"]["points"],
                   "Poison found": r["result"]["found"], "Tokens spent": r["result"]["spent"]}
                  for r in view["history"]], hide_index=True, width="stretch")
    reviews, feedback = st.tabs(["Round reviews", "Playtest feedback & download"])
    with reviews:
        for r in view["history"]:
            with st.expander(f"Round {r['number']} · {r['deck']}", expanded=r["number"] == 2):
                reveal(r, players)
    with feedback:
        st.subheader("Help shape the next playtest")
        st.caption("Use aliases. Your feedback is included in the record both players can download. "
                   "Ratings describe this playtest; they do not measure learning.")
        saved = view["feedback"]
        with st.form("feedback"):
            clarity = st.slider("Rule clarity · 1 confusing / 5 clear", 1, 5, saved.get("clarity", 3))
            enjoyment = st.slider("Enjoyment · 1 low / 5 high", 1, 5, saved.get("enjoyment", 3))
            reasoning = st.text_area("Why did the robot select its final rule?", value=saved.get("reasoning", ""), max_chars=3000)
            decisions = st.text_area("Which choices mattered? Did the tiebreak feel fair?", value=saved.get("decisions", ""), max_chars=3000)
            improvement = st.text_area("What was confusing, and what would you change?", value=saved.get("improvement", ""), max_chars=3000)
            if st.form_submit_button("Save feedback", type="primary"):
                act(view, "feedback", {"clarity": clarity, "enjoyment": enjoyment, "reasoning": reasoning,
                                       "decisions": decisions, "improvement": improvement})
        st.write("Feedback saved: " + (", ".join(players[s] for s in view["feedback_received"]) or "none yet"))
        code, token = st.session_state["credentials"]
        record = store.export(code, token)
        st.download_button("Download playtest record (.json)", json.dumps(record, indent=2),
                           file_name=f"poisoned-dataset-{code}.json", mime="application/json")
        st.caption("Includes decks, seed, labels, attacks, audit order, timestamps, scores, and saved feedback. "
                   "Download again after both players save their feedback.")
    st.caption("For another match, leave this room and create a new one. Save the playtest record first.")


@st.fragment(run_every="2s")
def poll_room(code, token, revision):
    try:
        if store.view(code, token)["revision"] != revision:
            st.rerun()
    except RoomError:
        st.rerun()


def room():
    code, token = st.session_state["credentials"]
    try:
        view = store.view(code, token)
    except RoomError as exc:
        st.error(str(exc))
        if st.button("Return to lobby"):
            del st.session_state["credentials"]
            st.rerun()
        return
    with st.sidebar:
        st.markdown("### 🌒 Poisoned Dataset")
        st.caption("ROOM CODE · SHARE WITH YOUR OPPONENT")
        st.code(code, language=None)
        st.write(f'Playing as **{view["players"][view["seat"]]}** · Seat {view["seat"]}')
        st.caption("Fixed edition" if view["edition"] == "fixed" else "Fresh generated decks")
        with st.expander("Save your private reconnect code", expanded=view["phase"] == "lobby"):
            st.caption("Save this before refreshing or closing the tab. It restores your seat. "
                       "Share the room code above; keep this code private.")
            st.code(token, language=None)
            st.download_button("Save reconnect details", f"Room: {code}\nPrivate reconnect code: {token}\n",
                               file_name=f"reconnect-{code}-{view['seat']}.txt", mime="text/plain")
        with st.expander("Rules & tie order"):
            rules()
        if st.button("Refresh room"):
            st.rerun()
        if st.button("Leave room"):
            del st.session_state["credentials"]
            st.query_params.clear()
            st.rerun()
        st.caption("Rooms update automatically. Leaving keeps your seat reserved for reconnecting.")
    if "notice" in st.session_state:
        st.warning(st.session_state.pop("notice"))
    phase = view["phase"]
    if phase == "lobby":
        st.html('<div class="eyebrow">MISSION CONTROL / WAITING ROOM</div>')
        st.title("Your rival is one room code away.")
        st.write(f'Share this app\'s address and room code **{code}**. Each player uses their own browser.')
        for seat in ("A", "B"):
            with st.container(border=True):
                st.write(f'**Seat {seat}** · {view["players"].get(seat, "Waiting for player…")}')
                st.caption("Defends first · attacks second" if seat == "A" else "Attacks first · defends second")
        if view["seat"] == "A":
            if st.button("Start two-round match", type="primary", disabled=len(view["players"]) < 2):
                act(view, "start")
        else:
            st.info("You're in. The host will start the match.")
        with st.expander("Mission briefing", expanded=True):
            rules()
    elif phase == "complete":
        finished(view)
    else:
        r = view["round"]
        role = "Attacker" if view["seat"] == r["attacker"] else "Defender"
        st.html(f'<div class="eyebrow">ROUND {r["number"]} OF 2 / {escape(r["deck"].upper())}</div>')
        st.title(f"You are the {role.lower()}.")
        st.caption(f'Attacker: {view["players"][r["attacker"]]} · Defender: {view["players"][r["defender"]]}')
        st.html('<div class="steps">' + ''.join(
            f'<span class="step {"active" if phase == p else ""}">{i}. {label}</span>'
            for i, (p, label) in enumerate((("attack", "Poison"), ("audit", "Audit & lock"),
                                            ("reveal", "Reveal")), 1)) + '</div>')
        if phase == "attack":
            attack(view)
        elif phase == "audit":
            defend(view)
        elif phase == "reveal":
            reveal(view["history"][-1], view["players"])
            ready = view["seat"] in r["ready"]
            if st.button("Ready · switch roles for round 2", type="primary", disabled=ready):
                act(view, "ready")
            if ready:
                st.info("You're ready. Waiting for the other player to finish the review.")
            else:
                st.caption("The second round begins when both players are ready.")
    poll_room(code, token, view["revision"])


if "credentials" in st.session_state:
    room()
else:
    landing()
