# Poisoned Dataset initial prototype checks

October 19, 2026, updated October 20 · Draft 0.1 · Python 3.14.7, then 3.10.20, 3.11.17 and 3.13.16

The initial prototype passed **15 automated tests**, including a manual rule-count example, tie order, attack ceilings, counted oracle access, separate scoring records, repeatable simulation exports, and scripted two-round matches with and without poisoning and auditing. Handcrafted cases verify that conflict auditing can miss consistently poisoned groups and can underperform random auditing when the correct label is the minority among copies.

The print-kit update added seven tests, for **22** in total; all pass on Python 3.10.20, 3.11.17 and 3.13.16 as of October 20. The new tests check that:

- Public sheets and card backs are byte-identical when the secret rule changes, so the art cannot leak answers.
- Kit builds reproduce exactly.
- Fold-over tags have both faces.
- The rulebook's booklet page order covers every page once.
- The box fits its contents and an 11 × 17 in sheet.
- A raster cover image is embedded.
- The generated grain texture is a valid, deterministic PNG.

The evaluation report and fixed-deck edition added eight more, for **30** tests that pass on Python 3.10.20 and 3.13.16 after merging the three October 20 pull requests. They check that:

- A small run produces valid figures, and the committed `headline.json` matches the committed runner outputs.
- The fixed decks reproduce from the documented selection on development seeds.
- Face-down truth and reference cards reveal nothing.
- The fixed edition has every component the right number of times, and its rulebook and box follow the edition.
- The command line builds the fixed edition.
- Every committed print file matches what the generators produce.

## Development diagnostics

The development run used seeds **0–49**, 24 training cards, the full draft budget grid, and 200 bootstrap resamples. It produced **9,000 policy rows** and **3,000 paired differences**. These are engineering and design diagnostics. The protocol was frozen as v1.0 on October 20, and the main seeds 1000–1199 were then run; see the [main evaluation results](evaluation-results.md).

Mean final deployment accuracy at an attack ceiling of four flips and four audit tokens:

| Training regime | Attack | No auditing | Random auditing | Conflict auditing |
| --- | --- | --- | --- | --- |
| Independent | Random | 1.00 | 1.00 | 1.00 |
| Independent | Directed | 0.97 | 0.99 | 1.00 |
| Correlated | Random | 0.95 | 0.96 | 1.00 |
| Correlated | Directed | 0.50 | 0.60 | 0.74 |

Each cell averages 50 generated scenarios; all policies share the same poisoned data within a condition. The directed attack in the correlated four-flip cell used one to four flips. The table suggests the correlated setup can expose the intended attack/defense interaction. It does not establish human game balance, an optimized attack, or a general advantage for targeted auditing. The complete budget grid, including zero and negative paired differences, remains available in the generated output.

Reproduce these diagnostics from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m poisoned_dataset experiment --seeds 50 --bootstrap-resamples 200 --out artifacts/pilot-v01
```

Choose another new output directory if that one already exists. The first development outputs were generated before the initial source commit and have `dirty: true` metadata. A fresh run from the committed code records its revision. Raw pilot files are local scratch outputs under `artifacts/pilot-v01/` and are ignored by Git; the numbers and reproduction command above are versioned. Archive complete raw outputs from the eventual main evaluation with the final release.

## Checks still needed

The printable kit's public/secret separation and component counts passed structural checks. Label tags are 1.6 × 0.55 inch fold-overs (STORE on one side, RECYCLE on the other) that fit the 1.6 × 0.55 inch slot on each poker-size card. Every print file was rendered to PDF in headless Chromium at 100% and inspected; the rendered seed-42 kit, rulebook, and box are committed in `print/kit-seed-42/`. Physical assembly, folding, and cutting still need a check. No human playtest or timing study has been completed. Next, print the fixed edition, time a solo walkthrough, and decide how drawn matches are broken. Scores are coarse: a defender scores 4/8 or 8/8. A match-level tiebreaker leaves the frozen v1.0 evaluation untouched.
