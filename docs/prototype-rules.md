# Poisoned Dataset prototype rules draft

Draft 0.1 · October 19, 2026 · Two players · Target match length 15–20 minutes, to be measured

Your moon-colony company is training a supply-sorting robot. Its competitor can change a few training labels. Protect your robot by checking the most useful labels before the model chooses a rule. Play two rounds and switch roles so each person defends once.

## Materials and setup

Use the Python helper (`python3 -m poisoned_dataset play`) or generate a printable kit following the README. Each round uses 24 training cards, eight test cards, three rule cards, four audit tokens, and STORE/RECYCLE label tokens. Each training card has three binary features: red or blue, round or square, striped or plain. A label is a movable token, separate from the card's features.

The reference contains a secret true rule: **STORE if red**, **STORE if round**, or **STORE if striped**; otherwise RECYCLE. The defender must not see this rule before scoring. The attacker knows it. A rule is selected afresh for each round; the two rounds need not have different true rules.

For printed play, give the attacker the private reference while the defender looks away. The attacker puts the clean labels on the training cards, then makes the permitted changes. Each trusted audit slip has its ID printed on the outside panel; Z-fold it so the label sits between the ID panel and the tinted panel, or place it in an envelope marked with the ID. Fold the sealed cover over the final test reference and keep it face down. Hide unused private material, including the secret rule, before the defender returns. Features and rules are public; the defender first sees the labels **after** poisoning. Remembering a clean layout is not part of the challenge.

The eight test cards are a separate deck kept aside for scoring. Do not add them to training or consult their reference labels during the round. Matching visual profiles across decks are allowed: records are separate even though the world contains only eight possible feature combinations.

## How the learner works

The learner can choose exactly one of these rules:

| Priority | Rule | Prediction |
| --- | --- | --- |
| 1 | red | STORE if red, otherwise RECYCLE |
| 2 | round | STORE if round, otherwise RECYCLE |
| 3 | striped | STORE if striped, otherwise RECYCLE |

Count how many current training labels each rule predicts incorrectly. The rule with the **fewest errors** wins. Break ties in the public priority order **red, then round, then striped**, even if a different rule won before the tie. Audited examples have the same training weight as all other examples.

For a small counting example, these are the current labels, which may be wrong:

| Card | Features | Current label |
| --- | --- | --- |
| C01 | red, square, plain | STORE |
| C02 | blue, round, plain | RECYCLE |
| C03 | red, round, striped | STORE |
| C04 | blue, square, striped | RECYCLE |

Red makes 0 errors, round makes 2, and striped makes 2, so the learner selects red. These labels alone do not certify that red is the true rule.

## Round sequence

1. **Secret poisoning.** With the defender looking away, the attacker may flip the labels of up to **four distinct training cards**. STORE becomes RECYCLE and vice versa. The attacker cannot change card features, add or remove cards, alter references, or change test cards. The attack is finished before the defender starts auditing.
2. **Inspect the supplied data.** The defender sees all 24 feature cards and their current labels. Count the errors for each rule and announce the current winning rule. Inspection, grouping cards, and calculation are free.
3. **Spend audit tokens.** The defender may spend up to **four tokens**, one at a time. Name one previously unaudited training card and pay one token. Reveal that card's trusted label and replace its current label with the reference label. Pay the cost even if the label was already correct. Mark the card verified. Recount the learner's errors after each audit.
4. **Lock the learned rule.** When the defender stops auditing or runs out of tokens, choose the minimum-error rule using the tie order. The defender cannot choose a favorite rule instead. Unused tokens provide no score bonus.
5. **Reveal and score.** Apply the locked rule to each of the eight test cards. Reveal their reference labels only now. Score one point per correct prediction, for a total out of eight. The attacker may not revise the attack or inspect the test labels earlier.
6. **Review and switch roles.** Reveal the true rule, the changed labels, and the audits. Discuss what changed the selected rule. Set out the second round's fresh training deck and private references; switch attacker and defender.

A verified card cannot be audited again. A check repairs only its own label; an identical-looking copy remains in training with its existing label until separately audited. No free relabeling, deleting examples, or adding new data is permitted in this version.

The helper displays conflict-policy hints, but the human defender may audit any eligible card. A hint is a choice suggested by visible evidence, not a guarantee that the label is poisoned.

## Fixed-deck edition

The professionally printed copy replaces per-seed printing with a reusable set. Use one of the four fixed training decks not yet used in the match. In secret, the attacker draws one of three truth cards, tags every card by it, and lays a face-down **reference row**: for each of the eight cargo types, the reference card whose label agrees with the truth. An audit turns over the reference card for the audited card's cargo type, and the tag is set to match. At scoring, reveal the truth card and turn every reference card face up. If any reference card disagrees with the truth card, the defender scores 8 for the round. Rules, budgets, and tie order are otherwise unchanged; see the [fixed-deck edition](fixed-deck-edition.md).

## Winning the match

Compare the scores players earned in their defender rounds. The higher defender score wins; equal scores are a draw. Both players have the same four-flip and four-audit budgets. Different scenarios are not guaranteed to have equal difficulty.

With these three rules and the uniform eight-card test deck, any incorrect feature rule scores 4/8 and the true rule scores 8/8. This coarse scoring may produce frequent draws; retain draws while testing rather than introducing an untested tiebreaker.

## Full information walkthrough

Run `python3 -m poisoned_dataset demo` to reveal a worked scenario. In draft 0.1, seed 19 uses a correlated training deck and true rule red. The automated directed attack changes C22, C03, and C23, moving the learner to round. Conflict auditing checks C05, C10, C03, and C22; the last check restores red and the final score is 8/8. The four-flip budget is a ceiling: this attack uses only three flips because the chosen rival disagrees with the clean labels on only three training cards. The demo uses its own documented random streams and is separate from the experiment grid.

## Questions for the debrief

- Which changed labels affected the competition between rules, and why?
- Did finding a wrong label immediately repair performance? What would one fewer audit have changed?
- Could an attacker change a whole group so no conflicting duplicates remain?
- What makes the reference trustworthy here, and what would change if checks were costly or fallible in different ways?
- What does this tiny rule library help explain, and what behavior of real ML systems does it leave out?

Observe whether players can explain the mechanism. Treat this discussion as formative feedback rather than evidence of educational effectiveness.
