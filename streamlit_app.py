"""Run with: streamlit run streamlit_app.py"""

from html import escape
import json
import os
from pathlib import Path

import streamlit as st

from poisoned_dataset import room_ui as ui
from poisoned_dataset.core import (LABELS, Card, conflict_scores,
                                   flip_labels, predict, test_deck)
from poisoned_dataset.rooms import RoomError, RoomStore
from poisoned_dataset.playtesting import ArchiveConfig, ArchiveSync, DEFAULT_REPOSITORY

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Poisoned Dataset · Playtest", page_icon="🌒", layout="wide", initial_sidebar_state="collapsed")


@st.cache_resource
def get_store(path, log_dir, directory):
    return RoomStore(path, log_dir=log_dir, archive_directory=directory)


@st.cache_resource
def get_archive(_store, path, config):
    return ArchiveSync(_store, config)


try:
    settings = dict(st.secrets.get("playtesting", {}))
except FileNotFoundError:
    settings = {}
archive_config = ArchiveConfig(
    repository=os.environ.get("PLAYTEST_GITHUB_REPOSITORY", settings.get("repository", DEFAULT_REPOSITORY)),
    directory=os.environ.get("PLAYTEST_GITHUB_DIRECTORY", settings.get("directory", "playtests")),
    token=os.environ.get("PLAYTEST_GITHUB_TOKEN", settings.get("github_token", "")).strip())
db_path = os.environ.get("POISONED_DATASET_DB", str(ROOT / "data" / "playtests.sqlite3"))
store = get_store(db_path, os.environ.get("POISONED_DATASET_LOG_DIR", settings.get("local_directory")), archive_config.directory)
archive = get_archive(store, db_path, archive_config)
store.materialize_logs()
archive.kick()

st.html("<style>" + (ROOT / "assets" / "game-room.css").read_text() + "</style>")


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
    ui.brand()
    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
    with left:
        ui.hero()
    with right:
        st.html('<div class="eyebrow">THE GAME ROOM</div><h2 class="lounge-heading">There’s a seat for you.</h2>'
                '<p class="room-intro">Bring a rival. Take turns sabotaging and protecting a sorting robot. '
                'The best defender takes the match.</p>')
        st.caption("Playtest notice: game actions and submitted reviews are collected for game design. "
                   "The project’s archive is public. Use an alias and leave out personal details.")
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
        with st.expander("New here? Read the table rules"):
            rules()
    st.html('<div class="house-rules"><span>01 / 02</span><p>One round on each side. '
            'Four flips. Four audits. Every label is a decision.<br>'
            'Play together on separate devices — around a table or over a call.</p></div>')


def act(view, action, payload=None):
    code, token = st.session_state["credentials"]
    try:
        store.act(code, token, view["revision"], action, payload)
    except RoomError as exc:
        st.session_state["notice"] = str(exc)
    st.rerun()


def board(cards, labels, verified=(), flipped=(), key="board"):
    st.html('<div class="table-label"><h3>The cargo table</h3><span>24 TRAINING CARDS</span></div>')
    sort = st.radio("Arrange cargo", ["Card order", "Look-alike groups", "Current label"],
                    horizontal=True, label_visibility="collapsed", key=f"sort_{key}")
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
                     f'<span>{escape(card.id)}</span><span class="stamp">{flag}</span></div>'
                     f'<img src="{ui.cargo_image(card.features)}" alt="{card.describe()}">'
                     f'<div class="cargo-features">{card.describe()}</div>'
                     f'<span class="tag {LABELS[labels[i]].lower()}">{LABELS[labels[i]]}</span></div>')
    st.html('<div class="cargo-table"><div class="cargo-grid">' + ''.join(tiles) + '</div></div>')


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
        ui.sealed_table("The cargo is being dealt.",
                        f'{view["players"][r["attacker"]]} is preparing the training set. '
                        'The cards stay face down until the attack is committed.')
        st.info("Your board will appear automatically. You will have four audit tokens to find the bad labels.")
        return
    cards = tuple(Card(**c) for c in r["cards"])
    with st.container(key="play_area"):
        table, controls = st.columns([3.2, 1.2], gap="large")
        with controls, st.container(key="controls_attack"):
            st.html('<div class="eyebrow">MALLORY’S MOVE</div><h2 class="control-heading">A little mischief.</h2>')
            st.info(f'Your secret truth: **STORE if {r["truth"].upper()}**, otherwise RECYCLE.')
            st.html('<p class="control-copy">Turn a few good labels bad. Watch the robot’s pick, '
                    'then send your cargo to the other side.</p>')
            chosen = st.multiselect("Labels to flip", list(range(24)), max_selections=4,
                                    format_func=lambda i: f"{cards[i].id} · {cards[i].describe()} · "
                                    f"{LABELS[r['clean'][i]]} → {LABELS[1 - r['clean'][i]]}",
                                    key=f"flips_{view['code']}_{r['number']}")
            ui.tokens(4 - len(chosen), "flip")
            if st.button(f"Commit attack · {len(chosen)}/4 flips", type="primary", width="stretch"):
                act(view, "attack", list(chosen))
            st.caption("Your opponent sees only the committed labels. Once sent, your attack is locked.")
        with table:
            labels = flip_labels(r["clean"], chosen)
            ui.learner(cards, labels, "Preview")
            board(cards, labels, flipped=chosen, key=f"attack_{r['number']}")


def defend(view):
    r = view["round"]
    cards = tuple(Card(**c) for c in r["cards"])
    verified = {a["index"] for a in r["audits"]}
    remaining = 4 - len(verified)
    found = sum(a["before"] != a["after"] for a in r["audits"])
    playing = view["seat"] == r["defender"]
    with st.container(key="play_area"):
        table, controls = st.columns([3.2, 1.2], gap="large")
        with controls, st.container(key="controls_audit"):
            st.html('<div class="eyebrow">SORTER’S MOVE</div><h2 class="control-heading">Trust, but verify.</h2>')
            if playing:
                st.html('<p class="control-copy">Which labels don’t add up? Spend a token to check one '
                        'card against its trusted reference.</p>')
            else:
                st.info(f'{view["players"][r["defender"]]} is auditing. Your attack is locked.')
            ui.tokens(remaining)
            st.caption(f"Poison found: {found}")
            if r["audits"]:
                last = r["audits"][-1]
                changed = last["before"] != last["after"]
                st.html(f'<div class="audit-receipt"><strong>✓ {last["card"]} · {LABELS[last["after"]]}</strong><br>'
                        + ("Poison found and repaired." if changed else "The label was already correct.") + '</div>')
            if playing:
                choices = [i for i in range(24) if i not in verified]
                selected = st.selectbox("Choose one card to audit", choices,
                                        format_func=lambda i: f"{cards[i].id} · {cards[i].describe()} · {LABELS[r['labels'][i]]}",
                                        disabled=remaining == 0, key=f"audit_choice_{r['number']}_{len(verified)}")
                if st.button("Spend 1 token · audit card", disabled=remaining == 0, type="primary", width="stretch"):
                    act(view, "audit", selected)
                st.caption("One token, one card. Even a correct label costs a token.")
                st.html(f'<div class="lock-box"><div class="eyebrow">READY TO DEPLOY?</div>'
                        f'<p>Your robot will use <strong>{r["rule"].upper()}</strong>. '
                        'Locking ends the round and reveals the truth.</p></div>')
                if st.button(f"Lock {r['rule'].upper()} & reveal", width="stretch"):
                    act(view, "lock")
            with st.expander("Optional conflict hint"):
                if st.checkbox("Show a suggestion based on visible labels", key=f"hint_{r['number']}"):
                    scores = conflict_scores(cards, r["labels"], verified)
                    best = max(scores.values())
                    st.write("Suggested cards: " + ", ".join(cards[i].id for i, score in scores.items() if score == best))
                    st.caption("Contradictions with verified copies come first, then disagreement among look-alikes. "
                               "This is a clue, not proof of poison.")
        with table:
            ui.learner(cards, r["labels"])
            board(cards, r["labels"], verified=verified, key=f"audit_{r['number']}")
            with st.expander(f"Audit trail · {len(verified)} checks"):
                audit_log(r["audits"])
                if not verified:
                    st.caption("No cards checked yet.")


def reveal(round_, players):
    result = round_["result"]
    st.html(f'<div class="reveal-banner"><div class="reveal-score">{result["points"]}<span> / 8</span></div>'
            f'<div><div class="eyebrow">ROUND {round_["number"]} · RESULTS ARE IN</div>'
            f'<h3>{escape(players[result["defender"]])}’s robot has spoken.</h3>'
            f'<p>True rule: <strong>{round_["truth"].upper()}</strong> · '
            f'Locked rule: <strong>{result["rule"].upper()}</strong><br>'
            f'Poison found: {result["found"]} · Tokens spent: {result["spent"]}</p></div></div>')
    st.caption("Changed labels: " + (", ".join(round_["cards"][i]["id"] for i in round_["flips"]) or "None"))
    st.write(f'Learner after poisoning: **{round_["attack_rule"].upper()}** → '
             f'after auditing: **{result["rule"].upper()}**')
    audit_log(round_["audits"])
    st.html('<div class="table-label"><h3>The deployment test</h3><span>8 UNSEEN CARDS</span></div>')
    tiles = []
    for c in test_deck():
        correct = predict(result["rule"], c) == predict(round_["truth"], c)
        tiles.append(f'<div class="test-card {"" if correct else "miss"}"><small>{c.id}</small>'
                     f'<img src="{ui.cargo_image(c.features)}" alt="{c.describe()}">'
                     f'<strong>{"✓ CORRECT" if correct else "× MISSED"}</strong></div>')
    st.html('<div class="test-row">' + ''.join(tiles) + '</div>')
    with st.expander("Compare predictions and trusted labels"):
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
    standings = []
    for r in view["history"]:
        result = r["result"]
        seat = result["defender"]
        won = outcome["winner"] == seat
        standings.append(f'<div class="standing {"winner" if won else ""}">'
                         f'<div class="eyebrow">{"MATCH WINNER" if won else "DEFENDER SCORE"}</div>'
                         f'<h3>{escape(players[seat])}</h3><div class="points">{result["points"]}<small> / 8</small></div>'
                         f'<p>Poison found: {result["found"]} · Tokens spent: {result["spent"]}</p></div>')
    st.html('<div class="standings">' + ''.join(standings) + '</div>')
    reviews, feedback = st.tabs(["Round reviews", "Leave a review & download"])
    with reviews:
        for r in view["history"]:
            with st.expander(f"Round {r['number']} · {r['deck']}", expanded=r["number"] == 2):
                reveal(r, players)
    with feedback:
        st.subheader("How was your time at the table?")
        st.caption("Reviews are optional and saved automatically when submitted. They are included in both "
                   "players’ downloads and the public playtest archive. Use your alias and leave out personal details.")
        saved = view["feedback"]
        with st.form("feedback"):
            review = st.text_area("Your review", value=saved.get("review", ""), max_chars=3000,
                                  placeholder="What worked, what didn’t, and would you play again?")
            clarity_col, enjoyment_col = st.columns(2)
            clarity = clarity_col.slider("Rule clarity · 1 confusing / 5 clear", 1, 5, saved.get("clarity", 3))
            enjoyment = enjoyment_col.slider("Enjoyment · 1 low / 5 high", 1, 5, saved.get("enjoyment", 3))
            with st.expander("Optional debrief · tell us more"):
                reasoning = st.text_area("Why did the robot select its final rule?", value=saved.get("reasoning", ""), max_chars=3000)
                decisions = st.text_area("Which choices mattered? Did the tiebreak feel fair?", value=saved.get("decisions", ""), max_chars=3000)
                improvement = st.text_area("What was confusing, and what would you change?", value=saved.get("improvement", ""), max_chars=3000)
            if st.form_submit_button("Save review", type="primary", width="stretch"):
                act(view, "feedback", {"clarity": clarity, "enjoyment": enjoyment, "reasoning": reasoning,
                                       "decisions": decisions, "improvement": improvement, "review": review})
        if saved:
            st.success("Your review is saved. You can update it using the same form.")
        st.write("Reviews saved: " + (", ".join(players[s] for s in view["feedback_received"]) or "none yet"))
        code, token = st.session_state["credentials"]
        record = store.export(code, token)
        st.download_button("Download playtest record (.json)", json.dumps(record, indent=2),
                           file_name=f"poisoned-dataset-{code}.json", mime="application/json")
        st.caption("The game log and reviews are saved automatically; this download is an extra copy. "
                   "Includes decks, seed, labels, attacks, audit order, timestamps, scores, and saved feedback. "
                   "Download again after both players save their feedback.")
    st.caption("For another match, leave this room and create a new one. Save the playtest record first.")


@st.fragment(run_every="2s")
def poll_room(code, token, revision):
    try:
        store.materialize_logs()
        archive.kick()
        if store.view(code, token)["revision"] != revision:
            st.rerun()
        status = store.logging_status(code, token)
        if not status["files"]:
            local = "Game logging begins with the next game action."
        else:
            local = "Game log saved on this server." if not status["local_pending"] else "Game log queued for a server file copy."
        if not archive_config.token:
            remote = "Online archive awaiting host setup."
        elif status["remote_pending"]:
            remote = "Online archive queued; saves retry automatically."
        else:
            remote = "Online archive up to date."
        st.caption(local + " " + remote)
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
    brand, menu = st.columns([5, 1], vertical_alignment="center", gap="small")
    with brand:
        ui.brand(code, view.get("round"))
    with menu, st.popover("Room & rules", width="stretch"):
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
        st.html('<div class="room-heading"><div><div class="eyebrow">YOUR PRIVATE TABLE</div>'
                '<h1>The table is set.</h1><p>Share this app’s address and your room code. '
                'Your rival has a seat waiting.</p></div>'
                f'<div class="invite-ticket"><small>ROOM CODE</small><strong>{code}</strong></div></div>')
        ui.players(view)
        both = len(view["players"]) == 2
        ui.sealed_table("Two rivals. One sorting robot." if both else "Waiting for your other half.",
                        "The cards are ready. Each of you gets one round to sabotage and one to defend."
                        if both else "Keep this table open. When your opponent joins, their seat will fill automatically.")
        if view["seat"] == "A":
            if st.button("Start two-round match", type="primary", disabled=not both, width="stretch"):
                act(view, "start")
        else:
            st.info("You're in. The host will start the match.")
        st.caption("Before you start: open Room & rules to save your private reconnect code. "
                   "You’ll need it if you refresh or close this tab.")
        with st.expander("Table rules · a quick briefing"):
            rules()
    elif phase == "complete":
        finished(view)
    else:
        r = view["round"]
        ui.players(view)
        ui.phases(view)
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
