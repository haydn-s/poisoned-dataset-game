# Painted artwork

The selected direction is **B's ink and gouache texture with A's visor robots**.
Mallory is the cream/orange attacker; Sorter is the mustard defender. These
identities are consistent on the role cards, card backs, rulebook and box.

| File | Pixels | Use |
| --- | --- | --- |
| `characters/mallory-v02.png` | 1254 × 1254, RGBA | Expressive attacker holding the two contrasting tags |
| `characters/sorter-v02.png` | 1254 × 1254, RGBA | Defender with inspection glass and open claw |
| `illustrations/label-swap-v02.png` | 1536 × 1024, RGB | Mallory swaps a label while Sorter is distracted; quiet title area |
| `concepts/01-painted-workshop-v01.png` | 1536 × 1024, RGB | Original A reference: robot designs |
| `concepts/02-inked-workshop-v01.png` | 1536 × 1024, RGB | Original B reference: rendering treatment |

Generated with the **built-in image_gen tool**, using the two original concept
images as references. No external game artwork was supplied to the generator.
Exact prompts, reference paths and tool output records are in
[`prompts-v02.json`](prompts-v02.json); the concept prompts are in
[`concepts/prompts.json`](concepts/prompts.json). The PNGs are unchanged copies
of the selected tool outputs, retaining the portraits' actual alpha channels.
Prompts document the process; rerunning a generative model does not promise
identical images. The committed image bytes make kit generation reproducible.

`poisoned_dataset/art.py` embeds these assets as shared SVG symbols. Generated
HTML has inline image data and can be copied and printed offline. The game and
HTML generator still require only Python's standard library. Cargo features,
manifests, lettering, logo, label icons and audit tokens remain procedural SVG.
This keeps the three binary features precise and the text editable.

The cover provides about **169 effective ppi** at the current lid's full artwork
area including bleed. Rendering a larger preview does not add source detail.
Before a professional order, compare a physical proof with the supplier's
resolution requirement; obtain a higher-resolution cover master if 300 ppi is
required. Portraits exceed 300 ppi at their present print sizes. The box and
card sheets remain prototype layouts pending the supplier's production template.
