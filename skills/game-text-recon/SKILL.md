---
name: game-text-recon
description: >-
  Reverse-engineer how a console game (PS1/PS2/PSP-era) stores its text: locate and extract
  the archive, derive and verify the character codec, enumerate and classify text blocks, dump
  a translation corpus, and map which on-screen text is editable versus baked into graphics or
  video. Use at the start of a new game-translation project, or when text seen in-game cannot be
  found in the corpus.
---

# Game text recon

Phase one of localizing a console game: turn an opaque game image into a **corpus** you can
translate, and a clear map of what is even translatable. The worked example is RE4 PS2; the method
is game-agnostic. Output feeds `game-text-localize` and `complex-script-game-font`.

## Ground Rules

- **Text is glyph codes, not ASCII.** In-game text is u16 codes mapped through the font charmap.
  Searching the raw image for ASCII will miss real text — go through the **codec**.
- **This is phase one of three.** A playable result later needs TEXT + FONT + ELF; recon scopes all
  three by revealing the atlas, the codec, and what is text vs non-text.
- **Atlas pixels are palette indices, not ink/no-ink.** Histogram the atlas and read its CLUT before
  judging any glyph — a font that looks 1-bit is often 4bpp anti-aliased, with the darkest index as the
  body and near-white indices as a halo. Detail: `~/.claude/skills/game-text-tools/reference/font-reuse.md`.
- Recon is read-only. It writes tools and data, never the game image.

## Steps

### 1. Locate and extract the archive

Identify the container format (e.g. AFS) and unpack its files. Note each file's offset and size in
the image — the apply phase later patches blocks in place by absolute offset.

**Record the pristine image's SHA-1 and byte size now**, before anything is written. It identifies which
dump this work targets, and the release patch at the end of the project is verified against it.

**Done when** the image's files are enumerated with their offsets, known text-bearing files are
identified, and the source image's SHA-1 + size are written down.

### 2. Derive and verify the codec

Build the charmap (byte ↔ token) that maps glyph codes to characters. **Verify it round-trips against
the image, not just against itself:** `encode(a known in-game string)` and confirm those bytes occur
in the raw image. A codec that round-trips in isolation but scores 0 hits in the image is wrong.

**Done when** encoding a known string finds it in the raw image, and tokenize/encode round-trip a
sampled block byte-for-byte.

### 3. Enumerate and classify blocks

Walk each file's MDT (text) blocks — a file may hold many (e.g. RE4 cutscene files hold ~13). For each
block record its **kind** (multi-language vs single-language) and, for multi-language, the index of the
target/English section. This classification drives budget and reclaim later.

**Done when** every standard block is classified with kind + English-section index.

### 4. Dump the corpus

Emit a corpus JSON of one row per string: `file, mdt, off, lang, text` (text as codec tokens). This is
the input to translation and the map for all later work.

**A lossy step inside the dumper can silently drop real text, and every check built on that corpus will
agree it's fine** — a leak scanner, a TODO scanner, and a coverage census all reading the same corpus is
one blind spot wearing three hats. e.g. a dumper that blanks a control byte's printable operand to 0x00,
then refuses to join two runs across a 0x00 (correct on its own), quietly halves any string that straddles
one — and it stays invisible until a screenshot shows text no census reported missing. Guard it the way
Step 2 guards the codec: write one coverage check **against the image, not against the corpus** — it walks
the raw bytes directly rather than trusting the corpus's own row count.

**Done when** the corpus JSON exists, its row count matches the blocks walked, and a raw-byte coverage
check independent of the corpus confirms nothing was silently dropped.

### 5. Map text vs graphic vs video

Not everything on screen is editable text. Before promising to translate an element, prove which it is —
see `reference/nontext-and-copies.md` for the evidence test (codec count in the raw image) and the
common traps: title/menu/HUD labels are usually **graphics** (a logo-style font, not the in-game VWF),
and some narration is baked into **FMV video** (other-language versions may be text overlays while the
shipped-language one is in the video).

**Done when** each in-game element the owner cares about is labeled text / graphic / video, each with
evidence (a codec-count number), not a guess.

### 6. Find every copy, including hidden ones

The same string can exist in several places, and list-view titles often live in a *different* block
from the body they name (e.g. RE4 Files-menu titles are in the item-name table, not the document). Some
copies sit in non-standard containers the block-walker misses. Locate them by scanning the raw image for
codec bytes — see `reference/nontext-and-copies.md`.

**Done when** every copy of each to-be-patched block is located (so none renders untranslated later).

## Reference

- `reference/nontext-and-copies.md` — the text/graphic/video evidence test; finding duplicate copies and
  non-standard containers by raw codec-byte scan.
