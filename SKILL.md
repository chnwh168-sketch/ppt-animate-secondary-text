---
name: ppt-animate-secondary-text
description: >-
  Edit existing PowerPoint (.pptx) decks so that, from a requested slide onward
  (default slide 3), only semantic secondary text appears one item per click or
  key press while slide titles, backgrounds, cards, bullet glyphs, arrows,
  icons, and decorations remain static. Use when users ask for “二级标题/二级
  文字逐句出现”, “按键一条一条播放”, “其他元素不要动”, or the
  approved foreign-trade training-deck animation style, without changing any
  content, layout, typography, position, size, or color.
---

# Animate Secondary PPT Text

## Honor the editing contract

- Preserve every visible word, line break, font, size, color, position, shape,
  background, and slide dimension.
- Preserve the source file. Export a new `.pptx` unless the user explicitly
  requests an in-place edit.
- Start at the slide requested by the user; default to slide 3 for this approved
  workflow. Leave all earlier slides completely untouched and unanimated.
- Add entrance animation only. Never add exit, emphasis, motion-path, or slide
  transition animation unless explicitly requested.
- Make each semantic secondary text item appear on a separate click/key press.
  Do not use `With Previous` or `After Previous` for those items.
- Keep slide titles, backgrounds, color blocks, cards, lines, icons, photos,
  videos, bullets such as `•`, arrows such as `↓` and `→`, plus signs, and
  decorative labels such as standalone `AI` static.
- Treat one semantically complete text box as one reveal unit. If several
  sentences share one text box, use paragraph-level delivery only when the app
  can do so without changing structure or layout. Otherwise report the
  ambiguity instead of rebuilding the text.
- If a bullet glyph and its text are inseparable in one object, do not split or
  reconstruct the object without approval.

## Use the required workflow

1. Read the `Presentations` skill for inspection, rendering, and final PPTX QA.
   Read the `computer-use` skill before operating Keynote or PowerPoint.
2. Locate the clean source deck and choose a separate final output path. Work
   from the clean source for the full run, not from a partially animated draft.
3. Render and inspect every slide. Build an exhaustive target plan in a
   temporary JSON file before editing. Record the exact reveal order for every
   slide from the start slide through the end.
4. Determine reading order from the slide's meaning: follow explicit process
   arrows first; otherwise order top-to-bottom and then left-to-right within the
   same row. Containers and decorations never enter the sequence.
5. If the user already approved this animation style in the current task,
   proceed. Otherwise animate one representative slide and obtain approval
   before applying the style to the full deck.
6. Apply animation through Keynote or PowerPoint's animation UI. Prefer copying
   the already-approved animation from the sample object. When no approved
   sample exists, use a quiet, no-motion `Appear` or short `Dissolve/Fade`
   entrance set to `On Click`.
7. Apply animation to exactly one target at a time and immediately verify the
   selection and build-order entry. Never pipeline, batch, or concurrently send
   animation UI actions; this causes skipped or misordered builds.
8. Finish and verify one slide before continuing. Save checkpoints, then export
   the completed deck as PowerPoint.
9. Run the audit script, render every final slide, inspect each at full size,
   and run the presentation overflow test before delivery.

For detailed Keynote/PowerPoint operating guidance and recovery rules, read
[`references/keynote-workflow.md`](references/keynote-workflow.md).

## Write the target plan

Use exact displayed text in reveal order. Include every slide from the start
slide to the final slide, even when a slide intentionally has no targets:

```json
{
  "start_slide": 3,
  "slides": {
    "3": [
      "国内大模型",
      "豆包",
      "元宝",
      "Kimi",
      "DeepSeek",
      "千问",
      "国外大模型",
      "ChatGPT",
      "Claude"
    ],
    "4": []
  }
}
```

Duplicate text is allowed; list it twice in the actual reveal order. Keep the
plan under the temporary build directory, not next to the final deliverable.

## Audit before delivery

Run:

```bash
python3 "$SKILL_DIR/scripts/audit_pptx_animations.py" \
  --source "$SOURCE_PPTX" \
  --final "$FINAL_PPTX" \
  --plan "$TARGET_PLAN" \
  --report "$TMP_DIR/animation-audit.json"
```

The audit must pass all of these gates:

- the PPTX archive is readable and contains the same number of slides;
- visible text content matches the clean source;
- every slide before the requested start has zero animation targets;
- each animated target is a real text shape, not a title placeholder or
  decorative symbol;
- target count and target order exactly match the plan;
- no unplanned slide or object is animated.

Treat a failed gate as a blocker. Fix the deck and rerun the audit. The script
checks structure and text; it does not replace full-slide visual inspection or
slideshow playback.

## Deliver

Return only the final edited `.pptx` plus a concise summary. State the start
slide and confirm that only secondary text reveals one item per click while all
other elements remain static. Do not deliver target plans, temporary exports,
or audit reports unless the user asks.
