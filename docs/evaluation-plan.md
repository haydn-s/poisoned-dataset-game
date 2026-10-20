# Poisoned Dataset evaluation plan

Protocol v1.0 · frozen October 20, 2026, before the main run · drafted October 19 as draft 0.1

The evaluation asks **when a fixed budget of conflict-based label audits protects this game's classifier better than uniform random audits**. Paired simulations provide the main evidence. Small walkthroughs and optional playtests examine whether people can use the resulting game. Version 1.0 freezes every parameter below, unchanged from draft 0.1; see the [freeze record](#freeze-record-v10).

## Threat model

| Element | Operational definition |
| --- | --- |
| Learning task | Binary classification using one of three public feature rules |
| Attacker goal | Reduce overall accuracy under the fixed uniform deployment distribution |
| Attacker knowledge | All clean training features and labels, the true rule, candidate library, tie order, and generation/deployment distributions |
| Attacker access | Change labels on at most k distinct existing training records before auditing |
| Attacker restrictions | No feature edits, insertion/deletion, oracle edits, test edits, post-audit changes, or test-label queries |
| Defender knowledge | Current training features and labels, rules, tie order, attack ceiling, and previously purchased reference labels |
| Trusted reference | A deterministic oracle returning the true label of one selected training card for unit cost |
| Test access | Separate scoring module only; no test features or labels passed to fitting, attack generation, or audit selection |
| Adaptivity | Auditing is sequential and may use previous answers; the attack is fixed before auditing and is not optimized against a particular defense |

The attacker knows the true function and deployment distribution, so the scoring deck is protected from modification and direct access, not a claim of secrecy against logical inference. Both automated attacks receive the same privileged clean training information. This is a training-time label attack against overall performance, with no special trigger or selected victim class. The terms follow the organizing dimensions in [NIST AI 100-2e2025](https://doi.org/10.6028/NIST.AI.100-2e2025).

## Data generation and learner

Each independent dataset seed selects one true rule uniformly from **red, round, striped**. Generate **24 training records** with binary features and exact labels from that rule. Two training regimes are included:

- **Independent:** all three features are independent fair bits.
- **Correlated:** red is a fair bit; round copies red with probability 0.85 and striped copies red with probability 0.75, with their copy decisions conditionally independent given red.

Generate the same true rule for a given seed across regimes using a separate random stream. Use separate streams for training, attacks, and defense selections. No random stream is shared in a way that lets one defense's draws alter the other defense's input.

Fit by counting mismatches to the supplied labels and selecting the minimum-error rule. Ties always favor **red, then round, then striped**. Record ties and the selected clean rule when reviewing ambiguous cases; a true rule in the library does not guarantee its selection from an uninformative sample.

The scoring module constructs **eight fresh records**, one for every feature combination, after fitting. Training records and test records have different IDs and no shared mutable objects. Repeated feature combinations across the sets are expected in an eight-profile world. The deployment distribution assigns each profile probability 1/8, so this is exact enumeration rather than an estimate from eight random samples. All regimes use the same uniform deployment distribution. The correlated regime intentionally introduces a mismatch between training and deployment frequencies; report this qualification with regime comparisons.

The current rule library produces exact deployment accuracy of **1.0 for the true rule and 0.5 for any other rule**. Report rule-switch rates and accuracy together to make this granularity clear. More deployment cards repeating the same profiles would not add statistical information.

## Attack policies

**Random corruption:** choose k distinct training indices uniformly without replacement and flip their binary labels. This is an unstructured corruption baseline, using exactly k flips.

**Directed poisoning:** find the false candidate rule with the fewest mismatches on the clean training labels; break rival ties in library order. Let D be the indices where that rival disagrees with the clean labels. Choose `min(k, |D|)` distinct indices uniformly from D and flip them. Each such flip reduces that rival's error margin against the true rule by two. Stop at the budget or when D is exhausted.

This is a reproducible heuristic aimed at a rival rule, not a globally optimal attack or a defense-aware adversary. If a rival already matches all training labels, D can be empty; record zero flips rather than silently replacing the attack. Compare at the same **maximum budget** and report actual flips used. The directed attacker can have fewer changes than random corruption. Retain the same attacked labels for every defense and audit budget within a seed/regime/attack/attack-budget cell.

## Defense policies and costs

All auditing policies start with the same poisoned training labels. One audit buys the true label of one unaudited record, replaces only that record's label, and costs one token whether or not it finds corruption. No policy receives the hidden true rule. Verified examples are not re-audited or reweighted. Manual inference cannot relabel unqueried records for free.

| Policy | Selection procedure | Expenditure |
| --- | --- | --- |
| none | Train on the supplied labels without reference queries | Zero; repeated as a shared baseline in each budget cell |
| random | Choose uniformly from all unaudited records at each step | Exactly a audits |
| conflict | Recompute the score below after each query and choose a highest-scoring unaudited record; randomize equal scores | Exactly a audits |

For an eligible record i, define its group as all training records with the **same complete feature tuple**. Its score is the lexicographically ordered pair:

1. **Trusted contradiction:** 1 if a verified record in that group has a label opposite to i's current label, otherwise 0.
2. **Duplicate disagreement:** the number of other records in the group with an opposite current label, divided by the number of other group records. Use 0 for a singleton.

Choose the largest pair; break ties uniformly using the defense's seed. If all scores are `(0, 0)`, this becomes uniform random sampling among the remaining records. Recompute after every correction. No candidate's test accuracy enters the score. This is one explicit interpretation of conflicting examples, not a comparison of every possible targeting policy.

Simulated defenders spend the entire assigned budget for a fair cost comparison. Human players may stop early, and their choices need not match either automated policy. Simulation findings describe the specified policies, not optimal human strategy or measured player performance.

## Experiment matrix

| Factor | Values |
| --- | --- |
| Development seeds | 0–49, reserved for debugging and tuning |
| Main seeds | 1000–1199, 200 independently generated datasets per regime |
| Training regimes | independent, correlated |
| Attack types | random, directed |
| Attack ceilings | 0, 2, 4, 6, 8 out of 24 records |
| Audit budgets | 0, 2, 4 |
| Defenses | none, random, conflict |
| Deployment | Fixed uniform enumeration of eight profiles |

The main grid has **36,000 rows**, including deliberately duplicated no-audit controls, and **12,000 per-seed paired differences**. Rows sharing a seed are not independent participant or dataset observations. Within each fixed condition, the uncertainty calculation has 200 seed observations. One random attack draw and one audit trajectory per defense occur in each seed/cell; this captures their variation across seeds without treating individual queries as independent trials.

**Primary contrast:** conflict minus random accuracy under **correlated training, directed poisoning, k = 4, a = 4**. Secondary contrasts cover the full matrix, especially independent training and random corruption. Commit the final protocol, primary contrast, and seed ranges before running the main grid. If pilot findings require changes, revise the protocol version and explain the change; do not tune on the main seeds and then describe them as untouched evaluation data.

## Metrics and analysis

For each run, retain selected rules and the following quantities. Accuracy differences are proportions; multiply by 100 when presenting percentage points.

- **Clean accuracy:** deployment accuracy after fitting clean labels.
- **Poisoned accuracy:** deployment accuracy after attack and before auditing.
- **Final accuracy:** deployment accuracy after the specified defense.
- **Attack effectiveness:** clean accuracy minus poisoned accuracy. Also derive the selected-rule change frequency from the recorded rules.
- **Accuracy recovered:** final minus poisoned accuracy.
- **Verification cost:** actual oracle calls; corruption found counts changed labels among those calls.
- **Recovery per audit:** accuracy recovered divided by actual oracle calls; undefined for zero calls, stored as an empty field.
- **Paired defense difference:** conflict final accuracy minus random final accuracy for the same seed and poisoned input.

Report the mean paired difference and its **95% percentile bootstrap interval**, resampling complete per-seed differences within each condition, 2,000 resamples for the main run. The runner uses a fixed, separate bootstrap seed. Report win and tie fractions alongside the mean, because these outcomes are coarse. Intervals describe simulation variability under this generator, not human learning, other model families, or uncertainty about real-world attacks. With one seed or zero bootstrap resamples, the runner leaves interval fields blank.

Present the prespecified primary cell first, followed by all budget curves or a complete table. Secondary cells are exploratory, with no claim of multiplicity-corrected significance. Keep negative and zero differences, unsuccessful attacks, and no-damage cells. A higher rate of finding corrupted labels need not imply a higher final-accuracy recovery.

Planned poster figures are accuracy versus attack budget at four audits, paired improvement versus audit budget, and one attack/audit trace explaining a failure or recovery. Include the clean and no-audit controls. An annotated failure case can be useful even when the primary difference is near zero.

## Reproduction and records

From the repository root, using a clean committed implementation:

```sh
python3 -m unittest discover -s tests -v
python3 -m poisoned_dataset experiment --seed-start 1000 --seeds 200 --bootstrap-resamples 2000 --out results/evaluation-v1.0
```

The runner refuses to overwrite existing directories. Outputs are:

| File | Contents |
| --- | --- |
| metadata.json | Configuration, seeds, protocol version, Python version, UTC run time, commit, dirty flag, and random-stream convention |
| scenarios.json | Generated training records, clean labels, and true rules; private during human play |
| runs.csv | Each policy's rules, changed card IDs, query trace, costs, and accuracy metrics; trace indices are zero-based training indices |
| paired.csv | Per-seed conflict-minus-random differences |
| summary.csv | Means and final-accuracy standard deviations by condition and defense |
| comparisons.csv | Mean paired differences, bootstrap intervals, win fractions, and tie fractions |

Archive a clean protocol/code revision and these outputs for the final release. The v1.0 main-run outputs are committed under `results/evaluation-v1.0/`; a rerun needs a new output directory. Scratch outputs under `artifacts/` are ignored by Git. The automatic demo uses separate random streams and is illustrative, not a main-grid result.

## Freeze record v1.0

Frozen on October 20, 2026, in the commit that introduces this section, before any main seed was generated. Seeds 1000–1199 had not been run or inspected; development used seeds 0–49 only.

- **Frozen without change from draft 0.1:** the threat model, data generation, learner and tie order, attack and defense policies, the experiment matrix, the primary contrast (correlated training, directed poisoning, k = 4, a = 4), the metrics, and the 2,000-resample percentile bootstrap.
- **Runner:** `experiments.PROTOCOL = "1.0"` is recorded in `metadata.json`, together with the commit and a dirty flag. The main run must come from a clean checkout of this commit or a later commit that changes only documentation or analysis code.
- **Pre-freeze checks:** the test suite covers the manual error-count example, tie handling, maximum attack budgets, identical poisoned inputs across defenses, exact oracle-call budgets, distinct audit selections, deterministic reruns, scoring and training separation, zero-attack and zero-audit controls, and the handcrafted consistent-poison and minority-correct cases.
- **Timing:** this freeze comes before the planned playtests, earlier than the November 1 date in the roadmap. If playtests change any frozen parameter, the change becomes protocol v1.1 with a stated reason. All main seeds are then rerun, and the v1.0 results are kept and reported next to v1.1, rather than presented as untouched evaluation data for v1.1.

## Verification and failure analysis

Before freezing the protocol, verify a manual error-count example, tie handling, maximum attack budgets, unchanged inputs across defenses, exact oracle-call budgets, distinct audit selections, deterministic reruns, and the separation between scoring and training. Check both zero-attack and zero-audit controls. Tests should fail if a defense is silently given the secret labels outside the oracle interface.

Include a handcrafted **consistent-poison group** with no conflicting duplicates, for which conflict scores are initially all zero. Also inspect a minority of correct labels surrounded by poisoned copies: a majority-based conflict signal can initially prefer a correct record. These are diagnostic scenarios, separate from the main aggregate grid. The trusted contradiction term may help after a query, but a tight budget can expire before enough influential labels are fixed.

If feasible within the 15-hour week, rerun the frozen protocol with 36 training records and proportional budgets as a sensitivity check. An additional tiny-deck exhaustive attack search could bound the directed heuristic's quality. Neither extension is required to deliver the core evaluation, and neither should replace the prespecified primary analysis.

## Formative human evaluation

Run a solo scripted walkthrough first. If a few volunteers are available, aim for **two to four complete matches**, recording the actual number rather than treating this as a statistical sample. Use [the playtest record](playtest-record.md) to log setup and play time, mistakes, rule questions, audit decisions, interventions, perceived choices, and enjoyment. Ask each player to explain one changed rule and one limitation after the reveal.

Use simple descriptive counts and concrete observations to revise the rulebook. A playtest can support a claim such as “three of four players needed a reminder about the tie order,” with an accurate denominator. It cannot establish general educational effectiveness or a population enjoyment rate. If nobody can be recruited, report solo walkthroughs and the simulation as the evaluation, and explicitly leave multiplayer usability and enjoyment unresolved.

## Limits on the final claims

The world is small, the true function is in the candidate library, labels begin noise-free, and the oracle is perfect with uniform costs. Duplicate profiles make a particular conflict signal available. The attacker is strong in its knowledge but uses a restricted heuristic. Correlated training is evaluated against uniform deployment. Performance and scoring are coarse, and changing library order can resolve ties differently. The experiment tests this specified game system; general robustness, demographic fairness, and educational effectiveness remain outside its evidence.
