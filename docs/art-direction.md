# Poisoned Dataset art direction and art review

Draft 0.1 · October 20, 2026

This document records the original visual review and the selected direction now used for every card, the rulebook, and the box. The October 20 polish pass adds painted characters and a narrative cover to the procedural game symbols. Both the seeded kit and fixed-deck edition use the same artwork through `python3 -m poisoned_dataset components`; see the README for the file list and print settings.

## October 20 polish pass

- More expressive painted Mallory and Sorter portraits replace the geometric robot drawings. Cream/orange Mallory remains the attacker; mustard Sorter remains the defender.
- The cover shows Mallory removing a dark tag and attaching a cream one while Sorter inspects other cargo. The shipping-tag logo stays editable and occupies the reserved title area.
- Text panels, tags and token faces have quiet, solid backgrounds. Light texture remains in the workshop panels and box walls.
- Plain cargo faces have no broad braces, pale paint chips or scratches. Only striped cargo has the cream diagonal pattern; small edge hardware, shape silhouettes and the feature manifests remain.

Original PNGs and exact generation records are in [`assets/art/`](../assets/art/README.md). The printed rules, component sizes, four fixed decks, budgets and frozen evaluation are unchanged by this pass.

## Review of the committed art

At the initial review after [PR #1](https://github.com/haydn-s/poisoned-dataset-game/pull/1), the repository had no committed image files. Its visual material was the HTML kit that `components.py` generated. Rendering it at 100% showed a usable layout with no visual identity:

| Area | Finding before this pass | Change |
| --- | --- | --- |
| Identity | Flat circles and squares in red and blue on white; no setting, characters, or title treatment | Moon-colony cargo, two robot characters, a hang-tag logo, painted texture |
| Card size | 2.5 × 2.08 in with gaps between dashed borders, so every edge needed its own cut | Poker size (2.5 × 3.5 in), edge to edge with crop marks; one straight cut separates neighbours |
| Colour reliance | The text descriptions helped, but the pictures differed only by colour, outline, and three white bars | Each card carries a feature manifest: colour word and swatch, filled shape glyph, striped or plain swatch |
| Labels | 48 single-sided 2 × 0.3 in strips; flipping a label meant finding and swapping a different strip | 27 fold-over tags; turning a tag over is the label flip |
| Audit tokens | Text-only rectangles with no "spent" state; "mark the card verified" had no physical piece | Hex AUDIT tokens that flip to VERIFIED and stay on the audited card |
| Audit slips | Players wrote IDs by hand and folded once; a single fold can show the label through the paper | Printed IDs and a three-panel Z-fold with a dense tint panel that hides the label from both sides |
| Test deck | Identical in look to training cards apart from the ID | Night-sky deployment art, TEST header, and its own back |
| Backs, rulebook, box | None | Optional backs per deck, a 12-page illustrated rulebook, lid and base dielines, and a packing plan |

## Previews

Rendered from the updated seed-42 kit at actual print size and reduced for the web. Private sheets are not shown because they reveal answers.

![Cover: Mallory swaps the tags while Sorter checks other cargo](art/cover.jpg)

![Fixed-edition role cards with the painted Mallory and Sorter portraits](art/role-cards.jpg)

![Training cards: pods and crates on pallets, with feature manifests and tag slots](art/training-cards.jpg)

![Rule cards, score card, quick references, and role cards featuring Mallory and the sorter](art/reference-cards.jpg)

![Fold-over STORE/RECYCLE tags and AUDIT/VERIFIED hex tokens](art/tags-and-tokens.jpg)

![All twelve rulebook pages](art/rulebook.jpg)

![Lid dieline with cover art](art/box-lid.jpg)

![Base dieline; its centre panel is the back of the box](art/box-base.jpg)

## Key art exhibits

The two exhibits were generated during the art-direction conversation and are preserved in [`assets/art/concepts/`](../assets/art/concepts). The user selected B's texture with A's robots. The default cover now uses the resulting narrative illustration; `--cover-image` still accepts an alternate lid image.

- **Exhibit A** sets the cast and the staging. A shell-white robot with orange panels, a black visor screen, yellow eyes, an ear disc, and an antenna holds a blank tag beside a red, round, hazard-striped pod. A small mustard tread-bot hangs a tag on a blue, square, plain crate. Earth hangs over the Moon in a round porthole. The scene already uses the game's grammar: features belong to the cargo, labels are separate tags.
- **Exhibit B** sets the rendering. It has inked contours with uneven weight, chipped paint showing bare metal, gouache grain, warm amber shop light against cool porthole blue, and cargo on yellow pallets.

The brief was to use exhibit A's robots in exhibit B's style. The robots keep A's silhouettes, visor faces, and palettes. B supplies the hand-inked wobble, paint chips, rust, grain, and lighting.

## Cast

| Character | Role in the art | Design notes |
| --- | --- | --- |
| Mallory | The rival robot; attacker role card, reference backs, box | Shell-white with orange panels, wide rounded helmet, black visor, sly yellow eyes looking sideways, orange ear discs, red-tipped antenna, one cream tag raised and a dark tag partly hidden. The name follows the security convention for an active attacker. |
| Sorter | The defender's learning robot; defender role card, training backs, score card | Mustard boxy head, black visor, round earnest eyes, short antenna, treads, inspection glass and open claw |
| Trent | Never drawn; the trusted reference | The wax seal on audit slips. In security writing, Trent is the trusted third party. |

The names are suggestions in flavour text only; no rule depends on them.

## Visual grammar

The three features always use the same visual cues, on every card and in the rulebook:

| Feature | Value | Drawing |
| --- | --- | --- |
| Colour | red / blue | Painted body colour `#c63d2f` / `#2f62b0`; manifest chip says RED or BLUE |
| Shape | round / square | Round pod with top handle and small edge latch / framed crate with corner caps, both on a yellow pallet |
| Pattern | striped / plain | A horizontal band of cream diagonal hazard stripes across the middle / no band |

On playable cargo cards, labels are separate movable components, never baked into the cargo picture. Narrative cover art shows the removable tags being exchanged. **STORE** tags are light cream with a box-into-tray icon. **RECYCLE** tags are dark slate with a chasing-arrows icon. The two differ in tone, icon, and word, so neither colour nor reading alone is required. Tag colours avoid the red and blue used for features.

Round 1 pieces use a mustard round chip, and round 2 pieces use teal with light lettering. Training art is lit by the amber shop. Test-deck art shows the lunar surface at night, so deployment cards cannot be mistaken for training data.

## Palette and type

| Token | Hex | Use |
| --- | --- | --- |
| Ink | `#2a1c14` | All outlines and body text |
| Paper | `#f3e8d0` | Card stock, STORE tags, rulebook pages |
| Shop amber | `#e7a443` → `#94592a` | Training scenes, box |
| Mustard | `#e2ad35` | Pallets, sorter, AUDIT tokens, round 1 |
| Teal | `#2f7f74` | VERIFIED tokens, round 2 |
| Slate | `#3b302a` | RECYCLE tags |
| Night | `#091230` → `#2f4f8f` | Test deck, deployment key, porthole |
| Orange | `#e0632a` | Mallory's panels |

Headings use Inter Display Black and body text uses Inter. Card IDs use JetBrains Mono so that C01 and CO1 are never confused. Browsers substitute similar fonts if these are missing, and tag lettering is fitted to its box, so substitutes cannot overflow. Exported PDFs embed whatever fonts were used.

## How the art is made

The art combines procedural SVG in `poisoned_dataset/art.py` with committed painted PNGs. The generator has no third-party dependencies and needs no image service at runtime. The built-in image generation tool created the portraits and cover from the two concept references; prompts and provenance are committed beside the images. Generation itself is stochastic; the versioned PNGs make print generation repeatable.

- **Seeded wear.** Decorative hardware, pallets, stars and craters come from the project's seeded random streams. Broad cargo faces stay clean so wear does not imitate a feature. Kits reproduce byte for byte from the committed sources.
- **Ink wobble.** A displacement filter makes outlines look hand-inked. Chromium rasterises filtered groups at 300 ppi when printing, so the wobble prints cleanly. Text is kept outside filters and stays vector.
- **Gouache grain.** A single 192-pixel seamless grain tile is generated in pure Python, then reused with `<use>`. Grain is restricted to illustration panels and quiet box-wall texture; card paper, rulebook body backgrounds, tags, tokens and logo lettering have no grain overlay.
- **Painted characters.** Each transparent portrait is embedded once per HTML document as an SVG symbol and reused at its placements. The cover is included only in box and rulebook documents. Generated files are self-contained and work offline.
- **No SVG patterns.** Hazard stripes and the slip tint are drawn as vector hatching because Chromium re-rasterises every pattern instance when printing. That change cut the private sheet from 19 MB to under 2 MB.

## Production notes

- Cards are poker size. Home kits print edge to edge on Letter with paper-coloured edges that hide small cutting errors. A vendor export would need 0.125 in bleed per card; the card art already extends to the trim, so this needs an export step, not a redesign.
- The box is a telescoping two-piece box: the base is 8.75 × 5.75 × 1.5 in and the lid is 0.0625 in larger. The half-letter rulebook lies on top of three card wells and a front strip for tags, tokens, and the two private-slip envelopes. The dielines are for a cardstock mockup; confirm a supplier template before ordering.
- The 1536 × 1024 cover supplies about 169 effective ppi over the lid artwork including bleed. A 240 dpi preview export does not increase that source detail. Obtain a higher-resolution master if the selected supplier requires 300 ppi; review a physical proof before ordering. Portraits exceed 300 ppi at the current placements.
- `python3 tools/render_print.py <kit folder>` exports its HTML files to PDF with Chrome/Chromium. This optional authoring tool uses a temporary browser profile and adds no dependency to the game helper or HTML generator.
- A professionally printed copy cannot regenerate seeded decks. Decided: the [fixed-deck edition](fixed-deck-edition.md) prints four fixed decks, three truth cards, and sixteen reference cards once. Nothing is seed-specific, so no private sheets are needed.

## Checks before the art is frozen

- Print a kit and fold the tags, tokens, slips, and keys. Confirm that the Z-fold hides labels against a lamp and that tags stay on their pegs during play.
- Test the cards with a colour-vision simulator and in greyscale. The manifest should carry every feature.
- Time a setup with the new components and record it in the playtest record.
- Recheck the rulebook against `docs/prototype-rules.md` whenever the rules change; the copy is maintained in `rulebook.py`.
