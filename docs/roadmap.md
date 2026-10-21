# Poisoned Dataset delivery roadmap

Draft 0.1 · October 19, 2026 · updated October 20

The main evaluation finished early: protocol v1.0 was frozen and seeds 1000–1199 were run on October 20. The remaining milestones are the **November 13** poster submission and the **November 23** final deliverables, including one professionally made copy. Budget **9 hours of essential work per week**, with up to **6 additional hours** for improvements when available. The primary outcome is a playable artifact with reproducible evaluation, clear limitations, and a polished explanation.

## Status on October 20

| Workstream | Status | Record |
| --- | --- | --- |
| Main evaluation | Done. Protocol v1.0 was frozen before playtests, then seeds 1000–1199 were run. A change to any frozen parameter becomes v1.1 with a full rerun, reported alongside v1.0. | [Evaluation results](evaluation-results.md) |
| Artwork and components | First full pass done: cards, tags, tokens, backs, and private references for the seeded kit | [Art direction](art-direction.md), `print/kit-seed-42/` |
| Printed rulebook | 12-page half-letter booklet in both editions, in reading order and imposed | `print/*/rulebook*.pdf` |
| Box and storage | Mockup dielines, cover art, and packing plan for both editions | `print/*/box.pdf` |
| Printed-copy design | Decided: the fixed-deck edition, with no per-game printing | [Fixed-deck edition](fixed-deck-edition.md), `print/fixed-edition/` |
| Print vendor | Not chosen; no templates, quote, or delivery date yet | — |
| Playtests | None yet; no solo walkthrough of the printed set | [Playtest record](playtest-record.md) |
| Poster | Not started | — |

## Revised schedule

| Dates in 2026 | Essential work | Optional work | Exit condition |
| --- | --- | --- | --- |
| October 20–25 | Choose a vendor and request templates, a quote, and turnaround; print and assemble a home proof of the fixed edition; time a solo walkthrough | Recruit playtesters; start the poster draft | Vendor shortlisted with dates; proof problems logged |
| October 26–November 1 | Run two to four formative matches; revise rules and components from what they show | One bounded sensitivity check | Rules for the printed copy settled; any frozen-parameter change versioned as protocol v1.1 |
| November 2–8 | Approve the vendor proof and order the copy; revise the poster draft | Exploratory analyses, such as a defense-aware attacker | Copy ordered with a confirmed delivery date |

Finishing the evaluation early freed most of the November 2–8 block, about nine essential hours. Spend it on the vendor, the playtests, and an earlier poster. Keep development and main seeds separate: tune only on seeds 0–49.

## Physical prototype after the initial draft

The intended deliverable includes **one professionally made physical copy**. The first prototype of each workstream now exists; what remains are the checks before production.

| Workstream | Prototype now | Check before professional production |
| --- | --- | --- |
| Artwork and components | Moon-colony art on every card, fold-over tags, hex audit tokens, and the fixed-deck edition's truth and reference cards | Legible at actual size, features distinguishable without color alone, no secret information exposed by backs or show-through |
| Printed rulebook | 12-page booklet with setup, an illustrated round, tie order, scoring, and a quick reference | New players can complete a match; pages remain readable when printed |
| Box and storage | Telescoping box dielines, cover art, and packing plans | The complete printed set fits, with tags and tokens, before final dimensions are chosen |
| Production preparation | Component inventory and editable SVG source in code | Vendor templates, bleed and safe areas, materials, price, proof process, and production plus shipping against November 23; then per-card exports in the vendor's format |

Confirm supplier requirements and timing early, then test a home-printed physical proof before committing to professional production. Reserve time for one proof revision. Ordering the finished copy is a separate step after the specifications, quote, and delivery date are settled. Keep the November 13 poster submission protected while planning this work.

## Poster and final release

**November 9–12:** reserve the poster block for approximately 8–12 hours of final layout, proofreading, and export checks, working from a draft started earlier now that results exist. The draft is 36 × 24 inches; confirm the printer's required dimensions and file settings before final layout. Include the research question, game loop, threat model, actual results, failure case, and limitations. Use a legible link or QR code to the playable artifact and reproducibility materials.

**November 13:** submit the final poster PDF to the printer. This is the printing deadline, not the start of layout. Keep the submitted PDF and a receipt or confirmation with the release materials.

**November 14–22:** finish the portfolio README, printable release, rulebook, demonstration assets, setup check, and presentation rehearsal within approximately 9–15 hours for the week plus a small final buffer. If submitting as an online student, record and check a demonstration video **no longer than five minutes**. A useful outline is context (30 seconds), one attack/audit sequence (2 minutes), evaluation and failure case (1.5 minutes), limitations and artifact link (30 seconds).

**November 23:** submit the artifact link and poster PDF, plus the online demonstration video if applicable. Verify that the artifact link is accessible to the graders and that the README reproduces a fresh run.

## Match the grading criteria

| Criterion | Points | Evidence to deliver |
| --- | --- | --- |
| Project artifact | 100 | Playable match, printable components, helper, clear setup and dependencies, rules, design documentation, release link |
| Responsible AI rigor and evaluation | 75 | Explicit threat model, paired defenses, protected scoring data, seeds, raw results, uncertainty, failure analysis, limitations |
| Poster and presentation | 50 | Readable poster PDF of the required size, actual findings and citations, practiced explanation, optional required online video |
| Creativity and ambition | 25 | Original interaction around label integrity, transparent learner, meaningful resource decisions, and a carefully evaluated design |

## Scope control and contingencies

If the first walkthrough is slow, simplify physical bookkeeping and retain the terminal helper. If meaningful choices are rare, change a budget or the deck distribution; that changes frozen parameters, so record it as protocol v1.1 and rerun the main seeds. If matches tie too often, prefer a tiebreaker in the match rules: it decides who wins, not any round's accuracy, so it leaves the frozen evaluation untouched. A change to the rule library or deployment scoring would need v1.1.

If participants are unavailable, complete the synthetic experiments, diagnostic cases, and solo walkthroughs; describe the usability gap honestly. If conflict auditing does not outperform random auditing, explain the conditions and failure mechanism instead of changing the question to find a positive result. If optional work competes with the poster window, remove optional work.

Collection actions, multiple attack types in the game, networked play, a full graphical interface, and broad educational-outcome studies remain outside the minimum release. The portfolio can explain these as future directions after the core artifact is complete.
