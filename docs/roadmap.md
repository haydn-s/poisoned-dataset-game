# Poisoned Dataset delivery roadmap draft

Draft 0.1 · October 19, 2026

Protect the November 8 evaluation target and November 13 printer submission by keeping the core project small. Budget **9 hours of essential work per week**, with up to **6 additional hours** for improvements when available. The primary outcome is a playable artifact with reproducible evaluation, clear limitations, and a polished explanation.

## Work through the main evaluation

| Dates in 2026 | Essential work within 9 hours | Optional work up to 6 hours | Exit condition |
| --- | --- | --- | --- |
| October 19–25 | 2h review drafts; 3h solo/manual walkthroughs; 2h inspect pilot simulations; 2h revise budgets and rules | Improve printable layout; recruit a few playtesters | One complete match walkthrough; mechanics and bookkeeping problems logged |
| October 26–November 1 | 3h formative sessions or additional walkthroughs; 3h revise game and rerun pilot; 3h freeze protocol and confirm reproducibility | Better physical components or one bounded sensitivity check | Versioned rules, threat model, primary contrast, code, and seed list frozen |
| November 2–8 | 2h run and verify main evaluation; 3h analyze paired results and failure cases; 2h produce figures; 2h write findings and limitations | Extra participant feedback or prespecified sensitivity run | Main evaluation complete November 8; raw outputs and figures archived |

The first three weeks provide approximately **27–45 hours before evaluation completion**. The small rule learner, synthetic data, and automatic runner fit this window better than a full video game. Keep development and main seeds separate while making revisions.

## Physical prototype after the initial draft

The intended deliverable includes **one professionally made physical copy**. The next phase after merging the initial draft is a prototype of the artwork, a printed rulebook, and a box. Develop these together with the playtest revisions so the physical game is ready for production planning before the final release week.

| Workstream | Next prototype | Check before professional production |
| --- | --- | --- |
| Artwork and components | A consistent moon-colony visual direction; sample card fronts and backs, labels, audit tokens, and rule cards | Legible at actual size, features distinguishable without color alone, and no secret information exposed by backs or layout |
| Printed rulebook | A compact booklet with setup, an illustrated round, tie order, scoring, and a quick reference | New players can complete a match; pages fit the proposed box and remain readable when printed |
| Box and storage | A paper mockup of the box, cover layout, and a packing plan for all components | Fit the complete physical set, including movable labels and folded audit slips or envelopes, before choosing final dimensions |
| Production preparation | Component inventory, editable source files, and vendor-specific print exports | Confirm the supplier's templates, bleed and safe areas, materials, price, proof process, and production plus shipping schedule against the November 23 deadline |

Confirm supplier requirements and timing early, then test a home-printed physical proof before committing to professional production. Reserve time for one proof revision. Ordering the finished copy is a separate step after the specifications, quote, and delivery date are settled. Keep the November 8 evaluation and November 13 poster submission milestones protected while planning this work.

## Poster and final release

**November 9–12:** reserve the poster production block for approximately 8–12 hours of layout, concise findings, figure integration, citations, proofreading, and export checks. Choose a poster at least **24 × 24 inches** and confirm the printer's required dimensions and file settings before final layout. Include the research question, game loop, threat model, actual results, failure case, and limitations. Use a legible link or QR code to the playable artifact and reproducibility materials.

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

If the first walkthrough is slow, simplify physical bookkeeping and retain the terminal helper. If meaningful choices are rare, change a budget or the deck distribution in the development phase before adding a new mechanic. If scores tie too often, test a single rule-library or scoring change and record it as a new protocol version. Freeze changes before the main seed range is evaluated.

If participants are unavailable, complete the synthetic experiments, diagnostic cases, and solo walkthroughs; describe the usability gap honestly. If conflict auditing does not outperform random auditing, explain the conditions and failure mechanism instead of changing the question to find a positive result. If optional work competes with the poster window, remove optional work.

Collection actions, multiple attack types in the game, networked play, a full graphical interface, and broad educational-outcome studies remain outside the minimum release. The portfolio can explain these as future directions after the core artifact is complete.
