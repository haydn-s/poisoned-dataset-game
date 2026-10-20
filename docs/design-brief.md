# Poisoned Dataset design brief draft

Draft 0.1 · October 19, 2026

Poisoned Dataset is a playable demonstration of how changing training labels can change a classifier's decision rule, and how a limited verification budget can help or fail. The intended contribution combines a two-player tabletop game, a small transparent learning helper, and a reproducible evaluation of its auditing mechanics.

## Project commitments and working choices

The selected concept is a defender training a classifier while an attacker secretly poisons its training data. Final deliverables are due **November 23, 2026**. The poster must reach the printer **November 13**, with the main evaluation targeted for completion **November 8** and **November 9–12** reserved for poster preparation. Available effort is approximately **9–15 hours per week**.

| Working choice | First implementation | Reason to reconsider |
| --- | --- | --- |
| Format | Two-player tabletop game plus Python helper | Replace the interface if bookkeeping dominates play |
| Setting | Rival companies training moon-colony supply robots | Change flavor if it obscures the data decisions |
| Match | Two rounds with roles reversed; target 15–20 minutes | Measure teaching time and play time separately |
| Training deck | 24 cards per round; repeated profiles allowed | Adjust redundancy if auditing offers few meaningful choices |
| Features | Red/blue, round/square, striped/plain | Text descriptions support play without relying on color |
| Labels | STORE or RECYCLE | Keep binary labels while testing the core interaction |
| Learner | Minimum-error selection among red, round, striped rules | Expand only if coarse outcomes or ties undermine the game |
| Attack | Flip up to four existing labels once before auditing | Tune after checking damage and counterplay |
| Defense | Four one-card trusted audits, then lock the rule | Tune budget after pilot simulation and walkthroughs |
| Scoring | Eight independent test records; compare defender scores | Three candidate rules give only 4/8 or 8/8 scores |

These choices establish a testable prototype rather than a final specification. Collecting additional examples, extra attacks, multiple defense currencies, a graphical app, and a video game are deferred. The first round loop is **receive poisoned data → inspect → audit → fit → lock → test → discuss**. Training-error counts update after each audit; test results appear only after locking.

## Intended player experience

The defender sees the current labels and the mismatch counts for every candidate rule. The attacker sees the true rule and clean labels, then chooses where to spend a small flip budget. The defender must decide which labels deserve a costly check. Audits can find poison without changing the winning rule, which makes the distinction between label correctness and downstream model behavior visible.

The true rule is secret from the defender until scoring. Revealing it at setup would remove the central uncertainty. A trusted reference returns only the selected card's true label for one token; it does not repair all equivalent cards automatically. Players may use an audited example to reason about other cards, but only paid audits change the training labels.

## Responsible AI contribution

The game makes an integrity threat and a governance decision tangible: whose labels enter training, who can alter them, what counts as a trusted reference, and how scarce oversight is allocated. It presents provenance and verification as assumptions that must be specified, including the idealization that the reference is always correct and accessible at a fixed cost.

The research question is: **Under a fixed verification budget, when does auditing conflicting duplicate examples preserve deployment accuracy better than uniform random auditing?** A negative or mixed answer is useful: visible disagreement can be informative, but a consistent poisoned group can evade this signal. Simulation provides substantive evaluation without requiring a large participant study. Small playtests assess the artifact's usability and choices.

The project should claim a playable, evaluated explanation of this simplified attack-defense system. Claims of improved student understanding require a separate study; no such claim follows from a runnable game or favorable enjoyment feedback. Synthetic colors and shapes are not demographic groups, so the current evaluation does not establish fairness across human populations.

## Design risks and revision triggers

| Risk | Evidence to collect | Decision after the pilot |
| --- | --- | --- |
| Four label flips rarely change the rule | Rule-switch rate and clean/poisoned accuracy across seeds | Adjust flip budget or training correlation |
| Attacks almost always succeed despite four audits | Final accuracy and recovery by defense | Tune audit budget before adding defenses |
| Conflict targeting misses consistent poisoned groups | Prespecified failure case and raw audit traces | Explain the limitation; consider a second targeting signal later |
| Match scoring produces frequent draws | Counts from walkthroughs and small playtests | Tiebreakers adopted for testing: more poison found, then fewer tokens spent ([match tiebreakers](match-tiebreakers.md)); a fourth rule would need protocol v1.1 |
| Repeated bookkeeping consumes the session | Time per audit, counting errors, facilitator interventions | Keep counts in the helper and simplify physical setup |
| One role feels predetermined | Each player's meaningful decisions and reasons | Tune parameters and scenario selection, documenting changes |

Feature correlation is an intentional experimental variable. The correlated training generator makes red and round agree with probability 0.85, and red and striped agree with probability 0.75. Uniform deployment includes combinations that can be rare during training. Consequently, differences between regimes reflect both training correlation and its mismatch with deployment; they do not isolate a universal effect of correlation.

## Completion criteria for the first prototype

- A new user can run the helper without installing external packages and complete a match using the written rules.
- The same candidate rules, costs, tie order, and oracle semantics govern tabletop and simulation play.
- Public printable cards and private references reproduce a seed, and a manual learner calculation agrees with the helper.
- Experiments compare the same poisoned labels across defenses and retain raw data, configuration, and audit traces.
- Known failure cases and provisional choices are documented before the main evaluation.

## Related work and boundaries

[NIST AI 100-2e2025](https://doi.org/10.6028/NIST.AI.100-2e2025), by Vassilev and colleagues, organizes adversarial ML threats by attack stage, goals, capabilities, and knowledge. This motivates the explicit threat model in the evaluation plan. The game's label changes occur before learning and aim to reduce overall deployment accuracy.

[Jha, Hayase, and Oh, Label Poisoning is All You Need, NeurIPS 2023](https://proceedings.nips.cc/paper_files/paper/2023/hash/e0c9b65fb3e41aaa86576df3ec33ad2e-Abstract-Conference.html) studies label-only backdoors in image classifiers. It motivates treating label integrity seriously. This prototype instead studies a tiny rule selector and overall accuracy loss; it neither implements FLIP nor reproduces that paper's backdoor results.
