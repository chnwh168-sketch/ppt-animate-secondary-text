# Keynote and PowerPoint animation workflow

## Choose the authoring application

- Prefer the application that produced the approved sample animation.
- On macOS, use Keynote when the deck was previously validated through Keynote.
- Use PowerPoint when the user explicitly requires native PowerPoint editing or
  when Keynote changes unsupported deck features during import/export.
- Never edit animation XML directly. Use OOXML only for read-only inspection.

## Apply the approved effect in Keynote

1. Open a clean duplicate of the source `.pptx`.
2. Select the approved sample text object. Use **Copy Animation**.
3. Navigate to the target slide and select one semantic secondary text object.
   Confirm the object itself is selected, not its container or background.
4. Use **Paste Animation**. Open the animation/build-order panel and confirm the
   new entry targets the intended text and starts **On Click**.
5. Repeat steps 3–4 serially for the next target. Do not start the next UI action
   until the previous build entry is visible.
6. Reorder builds to match the target plan. Each click must reveal exactly one
   item; remove accidental concurrent or automatic starts.
7. Preview the slide from its start and step through every click. Confirm static
   objects never disappear or move.
8. Save after each completed slide. Export a new PowerPoint file only after the
   whole deck passes in-app playback.

If there is no sample animation, add **Appear** or a short, no-motion
**Dissolve/Fade** build-in to the first approved target, set it to **On Click**,
and use that object as the animation source.

## Apply the effect in PowerPoint

1. Open a clean duplicate and use **Animation Painter** from an approved sample,
   or add a simple **Appear/Fade** entrance.
2. Use the Animation Pane to set every target to **On Click** and to arrange the
   exact plan order.
3. Use paragraph delivery only for a multi-paragraph text box that must reveal
   one paragraph at a time and only when it preserves the original object.
4. Play the slide from its start and click through the full sequence before
   moving to the next slide.

## Prevent common failures

- Never issue concurrent clicks, menu commands, or paste-animation actions.
  Keynote may silently skip a target or assign builds in the wrong order.
- Never use ordinary copy/paste when the intention is to copy only animation;
  ordinary paste can duplicate or shift the text object.
- If a click selects a panel or group instead of the text, undo the animation,
  use the object list/selection pane, and reapply it to the text shape.
- If import/export changes content or layout, discard the partial output and
  restart from the clean source with the other application.
- If a build-order entry cannot be mapped to a semantic text object, stop and
  inspect it before continuing.

## Verify interactively

For each slide, compare the animation pane with the JSON plan, then run the
slideshow and press the advance key once per expected item. Verify that:

- nothing changes before the first click except the slide appearing;
- exactly one planned secondary text item appears per click;
- the order matches the slide's reading or process order;
- the final state is visually identical to the clean source slide;
- no title, background, panel, bullet glyph, arrow, icon, or decoration moves.
