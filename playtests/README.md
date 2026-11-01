# Poisoned Dataset playtest archive

Streamlit saves game logs and player reviews in this directory on the `play-testing` branch. Deploy the application from its source branch (currently `codex/streamlit-multiplayer`, or `main` after the PR is merged), not from this data branch.

## Layout

```text
playtests/YYYY-MM-DD/<match-id>/game.json
playtests/YYYY-MM-DD/<match-id>/reviews/A.json
playtests/YYYY-MM-DD/<match-id>/reviews/B.json
```

Dates and event timestamps use UTC. Match IDs are random and stable across reconnects. `game.json` includes aliases, edition, the round decks, accepted actions in revision order, audits and results. In-progress logs omit unrevealed truth rules, clean labels, attack choices, and the match seed. Round details appear at that round's reveal; the seed appears after the match ends. Review files contain the player's optional text, ratings, and debrief answers; updates replace that player's file.

Files are updated automatically from a durable SQLite queue. A write failure leaves the current version queued for retry. No reconnect codes, credential hashes, GitHub tokens, IP addresses, or browser identifiers are collected in these files. Player reviews and logs are public in this repository; players should use aliases and leave out personal details.

The schema is versioned inside each JSON file. The default target directory is `playtests`; the app's secrets configuration can change it. See the application source branch's README and `.streamlit/secrets.toml.example` for setup. No real playtest data has been added during setup.
