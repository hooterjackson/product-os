# PROP-0002 — EL-001's evidence rule cannot fire, and the item is mostly done

**Status:** open. Nothing here has been accepted.
**Raised:** 2026-08-19, work-laptop, from the cold-start test's finding.
**Cites:** `CLAUDE.md` § *A mechanical signal is not the primary source* ·
`standing-orders.md` § Money · `wiki/ruled-out.md` `R-056`.

---

## The defect

`EL-001`'s evidence rule names exactly one path:

```json
"evidence": [{"repo": "engineered-lighting-site",
              "paths": ["docs/bom-checklist.md"], ...}]
```

That file is a **browser-local checkbox UI.** Its own second line, verified by
grep against `origin/main`:

> state persists in your browser (nothing leaves your device)

Ticking every box in it writes **nothing** to the repository. So the rule is
**structurally unsatisfiable**: no amount of ordering, receiving or installing
parts can ever cause that path to change in a way that records the purchase.
`EL-001` could never close, and it has been ranked #1 in this portfolio since
the seed was written.

## What the evidence actually shows

`docs/04a-wire-the-zones.md` (`52c5048` … `ac827cd`, 2026-08-16/17) carries
**17 photographs**, and they are photographs *of the parts on the bench*:

| Doc 4 BoM row | photographed |
|---|---|
| PCA9685 breakout | `photo-pca9685-hub`, `photo-pca9685-a0`, `photo-pca9685-channels` |
| ULN2803A | `photo-uln2803` |
| Pololu buck | `photo-buck-5v` |
| Fuse holder + fuses | `photo-fuse-kit` |
| WAGO 221 assortment | `photo-wago-kit` |
| Wire (solid + stranded) | `photo-wire-kits` |
| LED tape | `photo-tape-pads` |
| PSU | `photo-psu-irm90` |
| — | `photo-bulk-cap`, `photo-e26-adapter` |

The PicoBuck is confirmed differently and more strongly — Doc 4a line 179 reads
the chips off the actual unit:

> This is the BoM's PicoBuck-class driver (this unit's chips read AL8860;
> ~330 mA per channel)

You cannot read a part number off a part you have not bought.

## What is NOT confirmed

**The Cree 3-up star and the Carclo 10507 optics trio.** Doc 4a never mentions
them, and says why:

> Set it aside until spotlight day.

M18's capture (`8bc2b5d`) says the bench has *a* star — the maker's own warm
XP-E2 + cool XP-E2 + PC Amber — but the **Carclo optics are unphotographed and
unmentioned anywhere.** That row is $15–25 of the BoM.

**Which tape was bought is also unconfirmed, and stays yours.** The 1800 K
channel implies Valent X, but that is an inference from a spec, not a
photograph — exactly the class of reasoning `CLAUDE.md` now opens on. It is
Q-005's to settle, and the difference is ~$456.

## Proposed

**1 · Repoint the evidence rule** (human authority):

```json
"paths": ["docs/04a-wire-the-zones.md", "docs/assets/photo-*.jpg"]
```

A photograph of a part on the bench is a repo artifact that a purchase actually
causes. A checkbox is not.

**2 · Reduce the item to its residual**, rather than closing it. The honest
title is *"Order the Carclo optics trio"* — everything else in the Doc 4 BoM is
photographed or read first-hand. **I have not made this change**: narrowing an
item's scope is a decision with taste in it, and the `title` change would enact
a scope call I am not entitled to make even though `title` is agent-authority.

**3 · `cost_usd: 205 → 20`** if (2) is accepted — the midpoint of the optics
row's published $15–25. If you would rather close `EL-001` outright and raise
the optics as a new item, that is cleaner and I have no preference.

**4 · Do not touch Q-005.** Whichever tape was bought, it was bought.

## What this costs, said plainly

`EL-001` is the flagship example in `README.md`, in the plan, and in every recap
I have given you — the 20-minute, $205, 14-day-lead order that ranks #1 at
`8.000 × 1.250 × 3.000 = 30.00`. **If it is done, that example has been wrong
every time it was published.**

The README is rewritten either way, because the arithmetic is still the right
demonstration and the item under it is not. See `R-056`.
