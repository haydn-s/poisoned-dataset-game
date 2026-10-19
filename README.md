# Poisoned Dataset

A two-player tabletop prototype about training-data integrity. One player changes labels in a robot's training set; the other spends a limited budget checking labels before a transparent learner chooses its sorting rule.

**Status: draft 0.1, October 19, 2026.** The concept is selected; these mechanics, budgets, and evaluation choices are working hypotheses. The prototype has runnable mechanics and printable components. Match length, balance, usability, and learning outcomes have not been established through playtesting.

## Run the prototype

Use Python **3.10 or newer**, from this repository's root directory. There are **no third-party dependencies**, downloads, accounts, or installation steps. Check your interpreter with `python3 --version`.

```sh
python3 -m poisoned_dataset demo
python3 -m poisoned_dataset play
```

`demo` reveals one automatic scenario, including secrets, for inspection. `play` runs two rounds with roles reversed on a shared terminal, choosing a fresh seed by default and printing it after the match for your records. Players look away during attacker setup; the terminal helper relies on honest play, including leaving scrollback and source files alone. You can also specify a seed; use one whose secrets the defender has not already seen:

```sh
python3 -m poisoned_dataset play --seed 42 --attack-budget 4 --audit-budget 4
```

For tabletop play, generate a two-round kit:

```sh
python3 -m poisoned_dataset components --seed 42 --out artifacts/kit-42
```

Open `artifacts/kit-42/public.html` and `private.html` in a browser and print at 100% on US Letter paper. Public materials contain 48 training cards across two rounds, two eight-card test decks, three candidate rules, four audit tokens, a score card, and reusable label tokens. Keep the private reference and `scenario.json` away from the defender. Each private training slip can be folded and opened only for a paid audit. See [prototype rules](docs/prototype-rules.md) for setup and a complete match.

Generated output directories must be new; commands refuse to overwrite an existing directory. The `artifacts/` directory is ignored by Git. Keep important releases outside that scratch directory or add them intentionally when publishing a version.

## Inspect and reproduce

```sh
python3 -m unittest discover -s tests -v
python3 -m poisoned_dataset experiment --seeds 5 --bootstrap-resamples 100 --out artifacts/smoke
```

The smoke command produces 900 simulation rows to check the pipeline. It is not the main evaluation. A provisional full run is:

```sh
python3 -m poisoned_dataset experiment --seed-start 1000 --seeds 200 --bootstrap-resamples 2000 --out artifacts/evaluation-v01
```

Every output includes raw results, paired defense comparisons, summary statistics, percentile bootstrap intervals, generated scenarios, seeds, configuration, Python version, and Git revision/dirty status. Generate synthetic data locally; no dataset download is required. Record the interpreter version alongside results because exact pseudorandom sequences need not be portable across all Python versions.

## Design and evaluation drafts

- [Design brief](docs/design-brief.md): contribution, scope, assumptions, and open design decisions.
- [Prototype rules](docs/prototype-rules.md): two-player setup, turn sequence, scoring, and debrief.
- [Evaluation plan](docs/evaluation-plan.md): threat model, exact policies, metrics, uncertainty, and limitations.
- [Delivery roadmap](docs/roadmap.md): work within 9–15 hours per week and the November deadlines.
- [Shareable playtest guide](playtest.md): player instructions and a short feedback form to send to volunteers.
- [Playtest record](docs/playtest-record.md): an observation sheet for small formative sessions or solo walkthroughs.
- [Initial prototype checks](docs/prototype-check.md): automated validation, development diagnostics, and outstanding physical checks.

The learner selects the feature rule with the fewest training-label errors, breaking ties in the order **red, round, striped**. Defense policies cannot see the secret true rule or test labels. The deployment deck enumerates all eight feature combinations, so scores are exact for a uniform toy deployment distribution. Repeated feature combinations in training and testing are distinct records in this finite feature space.

This models label poisoning and trusted auditing of a deliberately small learner. It does not establish robustness for general ML systems or educational effectiveness. With these three rules and uniform deployment, accuracy has only two levels, 50% and 100%; frequent match ties are a known design risk.

## Repository structure

```text
poisoned_dataset/core.py         Learning, data generation, attacks, auditing
poisoned_dataset/cli.py          Shared-terminal match and command-line interface
poisoned_dataset/components.py   Printable HTML kit generator
poisoned_dataset/experiments.py  Paired simulation and result export
docs/                           Versioned design and evaluation drafts
tests/                          Mechanics and experiment-integrity checks
```

The project uses the [Apache 2.0 license](LICENSE).
