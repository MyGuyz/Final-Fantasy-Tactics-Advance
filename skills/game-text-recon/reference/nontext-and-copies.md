# Non-text boundary and duplicate copies

Detail for Steps 5 and 6.

## The text / graphic / video evidence test

Decide what an on-screen element is by **counting its string in the raw image via the codec**, not by
looking at it:

- `codec-count(string) > 0` → **text** in a block; translatable.
- `codec-count(string) == 0`, but the element clearly shows those words → **not text**:
  - **Graphic/texture** if it uses a stylized/logo font unlike the in-game VWF — e.g. title menu
    (START/LOAD/OPTIONS), inventory tabs (Keys/Treasures/Map/Files/Exit), button hints ("△ Move
    selection"). Translating these means redrawing texture images — a different pipeline.
  - **FMV video** if it is narration/credits over a movie — e.g. RE4's English intro ("grisly murders …
    Arklay Mountains") returns 0 codec hits while other-language copies exist (PAL builds render text
    overlays; the shipped English is baked into the video). Translating means subtitling the FMV.

Report the count as the evidence. "0 hits, other-language copies present → baked in FMV" is a finding;
"looks like a graphic" is a guess.

## List titles live elsewhere than their bodies

A menu that lists documents/items usually pulls the **titles** from a name table, not from the document
bodies. e.g. RE4: the Files-menu shows titles from the item-name block (Core#17), while the document text
is in a different file (ss_file). Locate the real source of each visible label before translating it —
don't assume the label sits with its content.

## Find every copy by raw codec-byte scan

The block-walker only sees standard blocks. The same text can also be duplicated, sometimes embedded in
non-standard containers it skips (e.g. RE4 item descriptions exist in 4 places; two are embedded inside
puzzle containers the walker returns 0 blocks for). Find them all:

- `needle = block_bytes[:512]` (or `encode(a distinctive substring)`).
- `while (j = image.find(needle, i)) >= 0:` collect `j`, advance `i = j + 1`.

Every hit is a copy that must be patched, or that copy renders untranslated in-game. Record all offsets
so the apply phase patches each.
