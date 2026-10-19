# Poisoned Dataset initial prototype checks

October 19, 2026 · Draft 0.1 · Python 3.14.7

The initial prototype passed **15 automated tests**, including a manual rule-count example, tie order, attack ceilings, counted oracle access, separate scoring records, repeatable simulation exports, and scripted two-round matches with and without poisoning and auditing. Handcrafted cases verify that conflict auditing can miss consistently poisoned groups and can underperform random auditing when the correct label is the minority among copies.

## Development diagnostics

The development run used seeds **0–49**, 24 training cards, the full draft budget grid, and 200 bootstrap resamples. It produced **9,000 policy rows** and **3,000 paired differences**. These are engineering and design diagnostics; the main seed range 1000–1199 has not been run. The implementation and protocol have not yet undergone the planned November 1 freeze.

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

The printable kit's public/secret separation and component counts passed structural checks. Label tokens are specified as 2 × 0.3 inches to fit the card slots. Rendered print layout and physical assembly still need a check: automated browser preview was unavailable for local files. No human playtest or timing study has been completed. Next, print a kit, perform a timed walkthrough, and review the coarse 4/8 versus 8/8 scoring before freezing the mechanics.
