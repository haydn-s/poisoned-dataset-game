# Match tiebreakers

Draft 0.1 · October 20, 2026 · provisional until playtests confirm it

## The problem

A defender scores either 4/8 (the robot learned a wrong rule) or 8/8 (it learned the true rule). Two rounds of such coarse scores often tie, which the design brief lists as a risk. In simulation, half or more of all matches tie on score.

## The rule

The higher defender score wins. If scores are equal:

1. **More poison found wins.** Count the audits that changed a tag while each player defended. An audit changes a tag exactly when that tag had been flipped, so the count needs no extra component and cannot be disputed.
2. **Then fewer tokens spent wins.**
3. **Otherwise the match is a draw.**

The score card now has *poison found* and *tokens spent* tallies for each defender. The terminal helper reports both and applies the same rule (`match.winner`).

## Why these tiebreakers

- **They leave the evaluation alone.** The tiebreakers decide who wins a match, never a round's accuracy. The learner, attacks, audits, and deployment scoring evaluated under protocol v1.0 are unchanged. A fourth candidate rule or finer deployment scoring would change the learner or the metric, so it would need protocol v1.1 and a full rerun.
- **They reward the skill that matters.** The main evaluation found that recovery depends on locating disagreeing look-alikes. Finding poison is that skill.
- **They price oversight.** Spending fewer tokens for the same outcome makes verification cost visible, which is the governance point of the game.
- **They add attacker strategy.** An attacker now also gains from stealth: fewer flips, or whole look-alike groups flipped together, leave less poison to find.

## Simulated effect

Each automated round has a directed attack with four flips, then four audits by one policy; both players defend with the same policy. Seeded-kit matches use development seeds *s* and *s* + 1 for *s* = 0–48, with 10 random draws each. Fixed-edition matches use every ordered pair of different decks and every pair of truth cards, with 3 draws each. Main seeds were not used.

| Matches | Defenders audit by | Matches | Tied on score | Still tied after tiebreakers |
| --- | --- | ---: | ---: | ---: |
| Seeded kit | conflict | 490 | 50.6% | 23.5% |
| Seeded kit | random | 490 | 66.3% | 36.1% |
| Fixed edition | conflict | 324 | 52.2% | 25.9% |
| Fixed edition | random | 324 | 82.4% | 43.5% |

The tiebreakers settle about half of the score ties. Automated defenders always spend all four tokens, so in simulation the second tiebreaker never decides anything; in human play, stopping early will separate more matches. Many of the remaining draws are matches where neither defender found any poison.

## What to watch in playtests

- **Over-auditing:** whether defenders keep auditing after restoring the rule, to find more poison, and whether that tension with "fewer tokens" feels interesting or confusing.
- **Stealthy attacks:** whether attackers flip fewer tags to deny the first tiebreaker.
- **Bookkeeping:** whether players tally found and spent correctly without help.
- **Fairness:** how often a match is decided by tiebreak rather than score, and whether players accept it. Record this in the playtest record's *match decided by* field.

Reproduce the table with `python3 -c "from poisoned_dataset import match; print(match.report())"`.
