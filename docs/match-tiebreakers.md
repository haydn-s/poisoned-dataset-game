# Match tiebreakers

Draft 0.2 · November 6, 2026 · provisional until playtests confirm it

## The problem

A defender scores either 4/8 (the robot learned a wrong rule) or 8/8 (it learned the true rule). Two rounds of such coarse scores often tie, which the design brief lists as a risk. In simulation, half or more of all matches tie on score.

## The rule

The higher defender score wins. If scores are equal:

1. **Less poison left wins.** Count the flipped labels that were never audited while each player defended. At the reveal, these are the flipped tags without a VERIFIED token.
2. **Then fewer clean audits wins.** A clean audit checks a label that was already correct, so it leaves the tag unchanged.
3. **Otherwise the match is a draw.**

Each player's numbers come only from the round they defended. The score card has *poison left* and *clean audits* tallies for each defender. The app, the terminal helper, and the simulations apply the same rule (`match.winner`).

## What changed from draft 0.1

Draft 0.1 used *more poison found*, then *fewer tokens spent*. A simulated AI playtest on November 6, 2026 found two problems with it. The report is `docs/ai-playtests/2026-11-06.md` on branch `claude/confident-fermat-35m0lt`; its players were AI agents, not people.

- **Holding back won.** The round-2 attacker already knows how much poison the opponent found in round 1. Flipping fewer labels caps what the opponent can find, and flipping none guarantees they find nothing. In the playtest, a round-2 attacker flipped only two labels on purpose. The defender found both and restored the rule, and still lost on the tiebreak.
- **The two tiebreakers pulled in opposite directions.** The first rewarded auditing after the rule was already restored; the second rewarded stopping. Defenders spent tokens only to chase the first, and the second never decided a match.

Poison left fixes the first problem: holding back only leaves less poison for the opponent to miss, so the attacker's tiebreak interest matches the attack. Clean audits fix the second: an audit that finds poison never counts against you, so both tiebreakers reward accurate auditing.

## Why these tiebreakers

- **They leave the evaluation alone.** The tiebreakers decide who wins a match, never a round's accuracy. The learner, attacks, audits, and deployment scoring evaluated under protocol v1.0 are unchanged. A fourth candidate rule or finer deployment scoring would change the learner or the metric, so it would need protocol v1.1 and a full rerun.
- **They reward the skill that matters.** The main evaluation found that recovery depends on locating disagreeing look-alikes. Finding every flipped label without wasting checks on correct ones is that skill.
- **They price oversight.** A clean audit is verification that found nothing, which makes the cost of oversight visible. That is the governance point of the game.
- **They give the attacker real choices.** A flip the defender misses counts against them even if it does not change the rule. A flip pattern that draws checks onto correct labels, such as flipping most of a look-alike group so the honest card looks odd, earns clean audits.

## Simulated effect

Each automated round has a directed attack with up to four flips, then four audits by one policy; both players defend with the same policy. Seeded-kit matches use development seeds *s* and *s* + 1 for *s* = 0–48, with 10 random draws each. Fixed-edition matches use every ordered pair of different decks and every pair of truth cards, with 3 draws each. Main seeds were not used.

| Matches | Defenders audit by | Matches | Tied on score | Still tied after tiebreakers | Draft 0.1 tiebreakers |
| --- | --- | ---: | ---: | ---: | ---: |
| Seeded kit | conflict | 490 | 50.6% | 10.2% | 23.5% |
| Seeded kit | random | 490 | 66.3% | 13.5% | 36.1% |
| Fixed edition | conflict | 324 | 52.2% | 11.1% | 25.9% |
| Fixed edition | random | 324 | 82.4% | 18.2% | 43.5% |

The tiebreakers now settle about four in five score ties, up from about half. Part of that gain is an artifact of the automated attacker. It flips only cards its target rule gets wrong, so it sometimes runs out before four flips. When the two defenders then find the same number, the one who faced the smaller attack has less poison left. This decides 13–25% of simulated matches. Under these rules a human attacker has a reason to use all four flips, so expect the tiebreakers to decide fewer matches in human play than this table suggests. Automated defenders always spend all four tokens, so clean audits decide only when poison left is equal but the number found differs (5–13% of matches).

## What to watch in playtests

- **Holding back:** whether attackers still flip fewer labels than they could, now that it cannot help them.
- **Stopping:** whether defenders stop auditing once they believe every flip is found, and how often they are right.
- **Misdirection:** whether attackers try flip patterns that draw clean audits.
- **Bookkeeping:** whether players tally poison left and clean audits correctly without help. Poison left is only known at the reveal.
- **Fairness:** how often a match is decided by tiebreak rather than score, and whether players accept it. Record this in the playtest record's *match decided by* field.

Reproduce the table with `python3 -c "from poisoned_dataset import match; print(match.report())"`. The draft 0.1 column is from the previous version of this file.
