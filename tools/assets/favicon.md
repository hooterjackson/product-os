# The mark

`favicon-source.png` is the master as Marcelo supplied it: 1254x1254, the POS
monogram in warm white on black. `favicon.png` is derived from it and is what
ships.

## Why the shipped file is cropped

Measured, not eyeballed — the PNG was decoded and the light pixels bounded:

    content bbox   777 x 713 inside 1254 x 1254
    padding        left 20%  right 17%  top 17%  bottom 26%

So the mark occupied about 62% of the frame's width. At a 16px tab that padding
is roughly six of the sixteen pixels spent on black, and the three overlapping
letterforms have to survive in the remaining ten. The shipped icon is a square
crop of the content plus 6% breathing room, scaled to 256 — about 1.6x more
linear resolution for the mark at every size a browser renders it.

To regenerate after replacing the master:

    python3 tools/assets/refresh-favicon.py

The warm white here is essentially `--fg-0` (#F2EEE6), the theme's own ink, so
the mark and the page were already the same palette.
