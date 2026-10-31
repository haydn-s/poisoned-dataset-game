# Poisoned Dataset

A two-player tabletop prototype about training-data integrity. One player changes labels in a robot's training set; the other spends a limited budget checking labels before a transparent learner chooses its sorting rule.

**Status: draft 0.1; digital playtest added October 31, 2026.** The prototype has a multiplayer Streamlit app, a terminal helper, and printable components. These mechanics, budgets, and evaluation choices are working hypotheses. Match length, balance, usability, and learning outcomes have not been established through playtesting.

## Play digitally with Streamlit

Two players join a private room from separate browsers or devices. Multiple pairs can play in independent rooms on the same server. The app handles secret setup, four label flips, four paid audits, the learner's error counts, two rounds with roles reversed, and the current match tiebreakers. It uses the existing mechanics, not a new rules variant.

The game room uses the original Mallory and Sorter portraits, illustrated cargo cards on a workshop table, a turn track, rule tiles, and audit tokens. Actions sit beside the table on desktop and above it on phones. **Room & rules** holds reconnect details and the rule reference.

Use Python **3.12** (the tested interpreter) and run these commands from the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0
```

Open the **Local URL** printed by Streamlit. For another device on the same Wi-Fi, use the **Network URL** printed by Streamlit, usually `http://<host-LAN-IP>:8501`. Keep the host computer awake and the server running; allow local network access if your firewall asks. `localhost` only works on the host computer. If the network blocks device-to-device traffic, use a hosted deployment instead. No accounts, external API keys, or dataset downloads are required.

1. Choose an alias and **Create room**. The fixed edition is the default: two different decks drawn from A–D, with an independently drawn secret truth each round. **Fresh decks** reproduces the correlated generated-kit rules with a private random match seed.
2. Share the app's address and the six-character room code. The other player chooses **Join room**. Each player should save their own **private reconnect code** from **Room & rules** before refreshing or closing the page.
3. The host starts the match. Seat A defends first; seat B attacks first. Only the attacker sees the truth and clean labels during setup. The defender's board appears after the attack is committed.
4. Flip labels using the attack selector. During defense, arrange the board by card order, look-alike groups, or current label; audit cards individually or stop early with **Lock & reveal**. The optional conflict hint uses only visible evidence.
5. Review round one and both choose **Ready** to switch roles. After round two, submit feedback and download the JSON playtest record. It contains both rounds, the seed, labels, actions, timestamps, scores, tiebreaker, and saved feedback, with no reconnect codes. Download again after both players save feedback.

Refreshing a browser starts a new Streamlit session. Use **Reconnect** with the room code and your private code to restore your seat. Leaving a room reserves the seat; joining again with an alias does not reclaim it. Losing a private code means starting a new room. You can test both seats on one computer using two browser tabs, but avoid looking at the other seat's secrets during a real playtest.

### Hosting for remote players

Deploy this repository to a Python host that supports Streamlit and WebSockets, with `streamlit_app.py` as the entry point and `requirements.txt` as its dependencies. For Streamlit Community Cloud, select this repository, branch, and entry point, and choose Python 3.12 in advanced settings; see the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). All players must use the same deployed app address. This repository does not automatically publish the app or create a cloud account.

Room state is stored server-side in `data/playtests.sqlite3` (ignored by Git), shared by all browser sessions. SQLite transactions and revision checks reject stale actions and simultaneous attempts to take the second seat. Only role-appropriate state is rendered; truth, clean labels, future rounds, and the match seed are withheld from the defender until their permitted reveal. The app deals correct references automatically, so the printed edition's mislaid-reference penalty cannot occur.

For durable hosting, point `POISONED_DATASET_DB` at a file on a persistent local disk. Use **one host/replica**; do not put SQLite on a shared network filesystem or scale to independent replicas. Restarting with the same database preserves rooms. Community Cloud does **not** guarantee local-file persistence, so download playtest records before the app sleeps, restarts, or redeploys; see [Streamlit's storage guidance](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data). This is a small-group playtest app, not a public matchmaking service: room codes are invitations, reconnect codes grant access to one seat, and the server operator can inspect the database. Feedback is visible in both players' completed-match downloads. Use aliases.

The app polls room revisions every two seconds using a [Streamlit fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment). Waiting does not rerun the full page unless another player changes the room. The two-round flow, role privacy, reconnect behavior, concurrent actions, and feedback are covered by backend and Streamlit AppTest checks:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The UI tests skip when Streamlit is not installed; the original terminal and print tools still have no third-party dependencies.

## Run the prototype

For the terminal helper and print tools, use Python **3.10 or newer**, from this repository's root directory. These tools have **no third-party dependencies**, downloads, accounts, or installation steps. Check your interpreter with `python3 --version`.

```sh
python3 -m poisoned_dataset demo
python3 -m poisoned_dataset play
```

`demo` reveals one automatic scenario, including secrets, for inspection. `play` runs two rounds with roles reversed on a shared terminal, choosing a fresh seed by default and printing it after the match for your records. Players look away during attacker setup; the terminal helper relies on honest play, including leaving scrollback and source files alone. You can also specify a seed; use one whose secrets the defender has not already seen:

```sh
python3 -m poisoned_dataset play --seed 42 --attack-budget 4 --audit-budget 4
```

For tabletop play, generate a two-round kit with its rulebook and box mockup:

```sh
python3 -m poisoned_dataset components --seed 42 --out artifacts/kit-42
```

Open the files in a browser and print at 100% (actual size):

| File | Paper | Contents |
| --- | --- | --- |
| `public.html` | US Letter, landscape | 48 training cards, two eight-card test decks, three rule cards, a score card, two quick references, two role cards, 27 fold-over STORE/RECYCLE tags and four AUDIT/VERIFIED tokens |
| `private.html` | US Letter, landscape | Each round's attacker setup panel, 24 Z-fold trusted audit slips and a sealed deployment key |
| `backs.html` | US Letter, landscape | Optional card backs; print on the reverse of the matching sheets |
| `rulebook.html` / `rulebook-booklet.html` | 5.5 × 8.5 in / Letter, duplex, flip on short edge | The 12-page illustrated rulebook, in reading order or imposed for folding and stapling |
| `box.html` | 11 × 17 in, plus one Letter page | Lid and base dielines with cover art, and the packing plan |

Cards are poker size (2.5 × 3.5 in), edge to edge with crop marks. Keep `private.html` and `scenario.json` away from the defender, and keep each round's private material apart. Add `--cover-image path/to/key-art.png` to put raster key art on the box lid instead of the generated cover. See [prototype rules](docs/prototype-rules.md) for setup and a complete match, and the [art direction](docs/art-direction.md) for the visual system.

A complete rendered kit is committed in [`print/kit-seed-42/`](print/kit-seed-42): every HTML file above, a PDF of each, `scenario.json`, and `box-lid-art.png` (a 240 dpi preview export of the lid). The rulebook and box files do not depend on the seed. That folder includes seed 42's private answers, so treat seeds 42 and 43 as spoiled for real play and generate a fresh seed instead.

For the professionally printed copy, `--edition fixed` builds a reusable set instead: four fixed training decks, three truth cards drawn in secret, and sixteen reference cards that replace the private slips and keys, so nothing is printed per game. It writes `cards.html` (one-sided), `duplex.html` (double-sided), `backs.html`, the edition's rulebook, and its box; a rendered copy is in [`print/fixed-edition/`](print/fixed-edition). See the [fixed-deck edition](docs/fixed-deck-edition.md) for the rules changes and how the decks were chosen.

Both editions include the painted Mallory/Sorter portraits and label-swapping cover. [Artwork originals and prompts](assets/art/README.md) are committed; HTML embeds them for offline printing. The current lid illustration is about 169 effective ppi at full size, so the professional order still needs the supplier's template, resolution check and a physical proof.

To export a newly generated kit to PDF, install Chrome or Chromium and run the optional authoring tool:

```sh
python3 tools/render_print.py artifacts/kit-42
```

It uses the HTML's paper sizes, prints backgrounds, and omits browser headers and footers. The committed PDFs are ready for prototype printing; the helper and HTML generator do not need a browser installed.

Generated output directories must be new; commands refuse to overwrite an existing directory. The `artifacts/` directory is ignored by Git. Keep important releases outside that scratch directory or add them intentionally when publishing a version.

## Inspect and reproduce

```sh
python3 -m unittest discover -s tests -v
python3 -m poisoned_dataset experiment --seeds 5 --bootstrap-resamples 100 --out artifacts/smoke
```

The smoke command produces 900 simulation rows to check the pipeline. It is not the main evaluation. The main run under the frozen protocol v1.0 is committed in [`results/evaluation-v1.0/`](results/evaluation-v1.0) and written up in the [main evaluation results](docs/evaluation-results.md). To reproduce it and its figures in new directories:

```sh
python3 -m poisoned_dataset experiment --seed-start 1000 --seeds 200 --bootstrap-resamples 2000 --out artifacts/evaluation-v1.0-rerun
python3 -m poisoned_dataset report --results results/evaluation-v1.0 --out artifacts/report-rerun
```

Every output includes raw results, paired defense comparisons, summary statistics, percentile bootstrap intervals, generated scenarios, seeds, configuration, Python version, and Git revision/dirty status. Generate synthetic data locally; no dataset download is required. Record the interpreter version alongside results because exact pseudorandom sequences need not be portable across all Python versions.

## Design and evaluation drafts

- [Design brief](docs/design-brief.md): contribution, scope, assumptions, and open design decisions.
- [Prototype rules](docs/prototype-rules.md): two-player setup, turn sequence, scoring, and debrief.
- [Evaluation plan](docs/evaluation-plan.md): threat model, exact policies, metrics, uncertainty, and limitations.
- [Main evaluation results](docs/evaluation-results.md): protocol v1.0 run on seeds 1000–1199, primary contrast, figures, and a failure case.
- [Poster](presentation/README.md): the 36 × 24 in showcase poster, generated from the committed results.
- [Delivery roadmap](docs/roadmap.md): work within 9–15 hours per week and the November deadlines.
- [Shareable playtest guide](playtest.md): player instructions and a short feedback form to send to volunteers.
- [Playtest record](docs/playtest-record.md): an observation sheet for small formative sessions or solo walkthroughs.
- [Initial prototype checks](docs/prototype-check.md): automated validation, development diagnostics, and outstanding physical checks.
- [Art direction](docs/art-direction.md): review of the earlier kit, the key-art brief, the visual system, and production notes.
- [Fixed-deck edition](docs/fixed-deck-edition.md): the reusable printed set, its rules changes, and the deck selection.
- [Match tiebreakers](docs/match-tiebreakers.md): how tied matches are decided, and simulated draw rates.

The learner selects the feature rule with the fewest training-label errors, breaking ties in the order **red, round, striped**. Defense policies cannot see the secret true rule or test labels. The deployment deck enumerates all eight feature combinations, so scores are exact for a uniform toy deployment distribution. Repeated feature combinations in training and testing are distinct records in this finite feature space.

This models label poisoning and trusted auditing of a deliberately small learner. It does not establish robustness for general ML systems or educational effectiveness. With these three rules and uniform deployment, accuracy has only two levels, 50% and 100%; frequent match ties are a known design risk.

## Repository structure

```text
streamlit_app.py                 Multiplayer Streamlit playtest interface
poisoned_dataset/room_ui.py      Player seats, rule tiles, tokens and shared game-room visuals
assets/game-room.css            Responsive workshop table and interface styling
poisoned_dataset/rooms.py        Private room views, transactional turns and playtest records
poisoned_dataset/core.py         Learning, data generation, attacks, auditing
poisoned_dataset/cli.py          Shared-terminal match and command-line interface
poisoned_dataset/components.py   Printable cards, tokens and private references
poisoned_dataset/decks.py        Fixed decks for the printed edition, chosen from development seeds
poisoned_dataset/edition.py      The fixed-deck edition: truth cards, reference cards, print sheets
poisoned_dataset/match.py        Match winner and tiebreakers, with simulated draw rates
poisoned_dataset/art.py          SVG game symbols and shared painted artwork
assets/art/                     Painted originals, concept references and exact prompts
tools/render_print.py           Optional Chrome/Chromium PDF exporter
poisoned_dataset/rulebook.py     Illustrated 12-page rulebook and booklet imposition
poisoned_dataset/box.py          Box dielines, cover layout and packing plan
poisoned_dataset/experiments.py  Paired simulation and result export
poisoned_dataset/report.py       Figures and headline numbers from experiment outputs
docs/                           Versioned design and evaluation drafts
presentation/                   Poster generator, generated poster, figures and PDF
tests/                          Mechanics and experiment-integrity checks
```

The project uses the [Apache 2.0 license](LICENSE).
