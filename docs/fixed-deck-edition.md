# Fixed-deck edition for the printed copy

Draft 0.1 · October 20, 2026 · decision record

The professionally made copy cannot regenerate a training deck for every match, and printing 48 sealed slips and two deployment keys for each game is impractical. The decision is to print **one reusable set**:

- four fixed training decks;
- three truth cards, one drawn in secret each round;
- sixteen reference cards that serve as the trusted oracle.

The seeded kit (`components --seed`) remains for home printing and playtests with fresh decks.

## Why fixed decks lose nothing secret

Training features are public in every version of the game; only labels are secret. Clean labels are the true rule applied to visible features. So the secrets in a round are exactly two: which rule is true, and which tags the attacker turned over. A fixed deck exposes neither. Knowing a deck in advance tells a player only what they would see on the table anyway.

## What changes at the table

| Step | Seeded kit | Fixed edition |
| --- | --- | --- |
| Training deck | Generated for the seed, printed per match | One of decks A–D (IDs A01–D24), any not yet used this match |
| True rule | Printed on the private sheet | Attacker shuffles three truth cards face down and draws one; the other two go back unseen |
| Clean tags | Copied from the attacker setup panel | Attacker applies the truth card: STORE wherever it says STORE |
| Trusted reference | 24 sealed Z-fold slips per round | The **reference row**: for each of the eight cargo types, the attacker lays face down the reference card whose label agrees with the truth. The other eight go back unseen. |
| Audit | Pay a token, open that card's slip | Pay a token, turn over the reference card for the audited card's cargo type, set the tag to match. The reference card stays face up; each look-alike still costs its own token to fix. |
| Scoring | Open the sealed deployment key | Reveal the truth card; each test card scores if the locked rule's prediction agrees with it |
| Check | None needed | Turn every reference card face up. If any disagrees with the truth card, the setup was wrong and the defender scores 8 for the round. |

The candidate rules, tie order, budgets (four flips, four audits), cost of an audit, and scoring are unchanged. One reference card per cargo type gives the same information as one slip per card, because clean labels depend only on features. The setup check is the one new rule: it makes a mislaid or dishonest reference row visible at the reveal, and the defender gets the benefit of the error.

## Choosing the decks

Decks come from development seeds 0–49 in the correlated regime, the regime the printed kit uses. The main evaluation seeds 1000–1199 were not used. `decks.select()` makes the choice reproducibly, and a test pins its output.

A deck is eligible if, under each of the three possible truths:

1. On clean tags, the learner chooses the truth.
2. Switching the learned rule takes **2 to 4 flips**. One flip never suffices, and four always can.
3. Over 40 seeded directed attacks with four flips, a defender using conflict auditing with four tokens restores the truth in **15% to 85%** of them. Neither role is predetermined.

Eligible decks are ranked by their mean distance from an even 50% contest. Exactly four of the 50 development decks are eligible, so the ranking only sets their letters.

| Deck | Dev seed | Cargo types | Truth red: flips · conflict · random | Truth round | Truth striped | Distance from even |
| --- | ---: | ---: | --- | --- | --- | ---: |
| A | 10 | 6 | 3 · 18 · 5 | 2 · 10 · 1 | 3 · 29 · 4 | 0.17 |
| B | 46 | 7 | 3 · 13 · 3 | 3 · 33 · 3 | 3 · 15 · 3 | 0.21 |
| C | 36 | 6 | 2 · 10 · 2 | 2 · 12 · 0 | 3 · 32 · 2 | 0.25 |
| D | 33 | 6 | 2 · 10 · 1 | 2 · 8 · 1 | 2 · 6 · 0 | 0.30 |

Each cell gives the flips needed to switch the rule, then how many of the 40 attacks four conflict audits recover from, then how many four random audits recover from. Random auditing rarely rescues these decks (at most 5 of 40), so they reward a defender who looks for disagreeing look-alikes. Deck D favours the attacker most.

## Relation to the evaluation

Protocol v1.0 evaluates the deck generator over 200 fresh seeds, not these four decks. The fixed decks are four samples from the same generator, picked by the criteria above using development seeds only, so the main results are untouched. Balance was measured with the automated policies. Human attackers and defenders may do better or worse, and playtests should record which deck and truth each round used.

## Printing

`python3 -m poisoned_dataset components --edition fixed --out <new folder>` writes the set. A rendered copy is committed in [`print/fixed-edition/`](../print/fixed-edition):

| File | Print | Contents |
| --- | --- | --- |
| `cards.html` | One-sided, Letter landscape | Decks A–D, the test deck, quick reference, role cards, tags, and audit tokens |
| `duplex.html` | Double-sided, flip on the short edge | Reference cards (STORE and RECYCLE sides) with their backs, plus the truth cards, rule cards, score card, and quick reference with theirs |
| `backs.html` | Optional | Backs for each deck and the test deck |
| `rulebook.html`, `rulebook-booklet.html`, `box.html` | As for the seeded kit | Edition-specific setup, audit and scoring pages, box contents, and packing plan |

Backs on the duplex sheets are mirrored, so they land behind their fronts with a short-edge flip.

Before ordering, check two things on a home proof:

- Reference card fronts must not show through to their identical backs. Both labels sit on the same dark ground to help with this.
- Duplex alignment.
