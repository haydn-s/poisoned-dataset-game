# Poisoned Dataset playtest guide

Thank you for trying an early version of **Poisoned Dataset**, a two-player game about protecting a robot's training data from sabotage. We are testing whether the rules are clear, the choices matter, and the game is enjoyable. No machine-learning experience is needed.

**Version:** draft 0.1 · **Plan for:** about 30 minutes including explanation and feedback. The target playing time is 15–20 minutes, which we still need to check.

## Before you start

Use two players and either the printed prototype kit or the computer helper. Your host can prepare both using the [setup instructions](README.md). For a helper match, run this from the repository folder:

```sh
python3 -m poisoned_dataset play
```

Please leave the demo, private files, and worked examples closed before playing; they reveal answers. During setup, only the current attacker sees the current round's secret reference. Keep the other round's reference hidden. On a shared computer, look away at the handoff prompts and leave terminal scrollback alone.

## Your mission

You work for rival companies on a moon colony. The **defender** trains a supply-sorting robot. The **attacker** secretly changes some training labels to make the robot learn the wrong rule. Play two rounds, switching roles after the first.

Each round has 24 training cards. Every card is red or blue, round or square, and striped or plain. Its label says **STORE** or **RECYCLE**. The label is separate from the features and can be changed.

The robot must choose one of three rules:

| Rule | Robot prediction |
| --- | --- |
| Red | STORE if red; otherwise RECYCLE |
| Round | STORE if round; otherwise RECYCLE |
| Striped | STORE if striped; otherwise RECYCLE |

For each rule, count how many current training labels it predicts incorrectly. The robot selects the rule with the **fewest errors**. Ties always go to **red, then round, then striped**. The defender cannot simply choose a different rule. The helper handles these counts if you use it.

## Play a round

1. **Attacker sets up in secret.** The attacker sees the true rule and correct training labels, then flips up to **four distinct labels**: STORE becomes RECYCLE or vice versa. Leave features, cards, and references unchanged. The defender first sees the labels after this step. The attacker makes no further changes.
2. **Defender inspects.** Look at the supplied training cards and labels, group cards if useful, and check which rule currently wins. Looking and counting are free.
3. **Defender buys checks.** You have **four audit tokens**. Spend one to reveal one previously unchecked card's trusted label and replace that card's current label. A check costs a token even when the label was correct. Recalculate the winning rule after each check. A check repairs only the chosen card; identical-looking copies need their own paid checks. You may stop early. The helper's hints are optional suggestions, not proof of sabotage.
4. **Lock and test.** Lock the rule selected by the error counts. Only then reveal the eight separate test cards and their reference labels. Score one point per correct prediction, out of eight. Keep test labels hidden during training and auditing.
5. **Reveal and switch.** Discuss the changed labels and checks. Use the fresh second-round scenario and switch roles. Compare the scores you each earned as defender; the higher score wins. Equal scores are a draw.

Ask your host whenever a rule is unclear. If comfortable, say what you are considering before making a choice. Honest confusion, unexpected tactics, and criticism are useful feedback.

## Feedback after both rounds

Copy this section into a message and send it to the person who invited you. Short answers are welcome; use an alias rather than your full name.

- **Date and player aliases:**
- **Printed kit or computer helper:**
- **Match seed, if available:** The helper prints this after the match.
- **Approximate explanation time / playing time:**
- **Defender scores:** Player A ___ / 8; Player B ___ / 8.
- **Clarity, 1–5:** 1 = very confusing; 5 = very clear. What caused confusion?
- **Enjoyment, 1–5:** 1 = not enjoyable; 5 = very enjoyable. What drove your rating?
- **Which choice felt most consequential?** Mention the role and card if you remember.
- **Which choice felt obvious, arbitrary, or missing?**
- **In your own words, why did the robot select its final rule?**
- **Did anything about the reveal surprise you?**
- **What one change would most improve the next match?**

If you played with printed pieces, also tell us which text, symbols, labels, or components were hard to read or handle. A first pass of artwork, an illustrated rulebook, and a box mockup now exist; tell us which parts helped or got in the way.

## Notes for the host

Prepare and separate the two rounds' private references before players arrive. For printed play, cut the pieces, fold the tags and audit tokens, and Z-fold the audit slips; include this preparation time in your own notes. Use a scenario whose answers the players have not seen. Keep the current four-flip/four-audit budgets for this test and record any deviations.

Explain the tie order and demonstrate an audit without revealing either round's true rule. Record rules questions, counting errors, requests for help, time spent on bookkeeping, and whether each role offered meaningful choices. Ask the feedback questions after both rounds so the prompts do not guide players' earlier decisions. Use the [host observation sheet](docs/playtest-record.md) for detailed notes. Ask permission before recording audio or video.

Feedback from this session will guide revisions to the game. It does not by itself measure educational effectiveness.
