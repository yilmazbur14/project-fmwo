# matt_echo: approval pass notes (2026-10-04)

These notes match PLAN.md section 5, which replaced the first brief's three separate sheets with one sheet.

## Sheet
- **Files:** `matt_echo.png`, one strip of 6 frames at 96x96 (576x96). `matt_echo.aseprite` round-trips through Aseprite with identical pixels. `matt_echo_3x.png` is a nearest-neighbour preview.
- **Approval frames:** f0, f1 and f4, also saved alone as `matt_echo_approval.png` and `_3x.png`.
- **Layout:** front-facing and never flipped. The soles are on row 95, the centre line is x 48, and nothing is drawn above row 1.
- **Nothing baked in:** no rings, badges or FX.

| f | Name | Black | Colours | Crest top (CROWNS) | Dome crown | Mouth | Sole centres |
|---|---|---|---|---|---|---|---|
| 0 * | echo_inhale | 24.81% | 29 | (48,1) | (48,14) | (48,43) | 33 / 63 |
| 1 * | echo_psych | 25.23% | 35 | (48,1) | (48,15) | (48,50) | 33 / 63 |
| 2 | psych laugh | 25.36% | 35 | (48,2) | (48,17) | (48,50) | 33 / 63 |
| 3 | boomburst_windup | 24.73% | 29 | (48,1) | (48,14) | (48,43) | 28 / 68 |
| 4 * | boomburst_blast | 25.19% | 39 | (48,8) | (48,17) | (48,52) | 28 / 68 |
| 5 | blast hold | 25.38% | 39 | (48,5) | (48,17) | (48,50) | 28 / 68 |

\* = approval frame.

- **Sheet totals:** 25.12% black, 39 colours.

## APPROVED 2026-10-04 ("approve all"), with the default feet fix
- **The fix:** f0, f1 and f2 now stand on `matt_roar`'s own legs: the rig's trousers and feet at stance 2, sole centres 33 / 63.
  - Inhale → roar, inhale → psych and psych → roar never move the feet.
  - Rows 84–95 of f0–f2 are pixel-identical to live `matt_roar` f1.
- **What changed:** only rows 72–95 of f0–f2 (the legs). f0 keeps its knee creases, re-placed on the roar's legs.
- **What didn't change:** f3–f5 are pixel-identical to the approved frames and keep their deliberate 28 / 68 sumo stance. All poses, faces and colours are as approved.
- **Before/after:** `feet_fix_before_after.png`. The approved strip before the fix is kept in `../work/approved_v1/`.
- **Crown:** "crown" in MattArtLayout.CROWNS means the top texel of the crest, and it is ≤ 13 on every frame. The mi_anchors dome crown is listed too.
- **Mouth:** the mouth is the centre of the box round the mouth-coloured texels. f1, f2, f4 and f5 are within 2 texels of (48,51).
- **Ring origin:** the roar mouth (48,51) sits at screen (961.5, 486.5) at HOME, at scale 3.

## Numbers vs his live sheets (measured)
- **Keyline:** pure `#000000` on every live Matt sheet, and here.
- **Black, live sheets:**
  - fight set sheets: idle 25.1, recover 25.0, hit 25.2, mystic 25.2, defeat 25.0, teleport 24.9;
  - yell_tell 24.2, spent 24.3, trueshot charge 25.7, trueshot fire 26.0;
  - roar 25.5 (its f1–3 frames are 25.7–25.9).
- **Black, this sheet:** every frame is gated to 24.7–25.5% in the export.
- **Palette:** only the approved 41 keys, with no semi-alpha. The audit is clean: no keyline gaps, lone texels or pinholes.

## What each frame reuses
Everything comes from the approved rig (a scratch copy, checked to rebuild 8 live sheets plus matt.png pixel for pixel), with these parts:
- **f0:** the Trueshot megaphone hands, the yell_tell puffed cheeks, and brows knit with eyes squeezed (straining to hold the breath).
- **f1:** the megaphone hands spread round an open grin.
- **f2:** the hands drop and the shoulders go up, eyes shut in arcs.
- **f3:** fists clenched with elbows cocked, cheeks puffed, wide eyes, and a neck under a lifted chin.
- **f4:** the approved deep-roar face (ROAR_DEEP), with red eyes.
- **f5:** the roar's red eyes and snarl over the intro's yell jaw.

## Invented (please confirm)
- **The psych face (f1):** a wink with both brows hitched up, a D-shaped open grin whose right corner curls up, a near-empty plum mouth, and the tongue stuck out over the chin. It is built on the roar's own jaw outline.
- **The splayed hands on f4:** a new hand map with the fingers fanned, generated in the rig's skin ramp and lit from the upper left.
- **The blast crest "blown back":** the centre spike is foreshortened and the side spikes are swept flat.
- **The arms on f4:** "Arms thrown back" is read as flung back and up BEHIND him. They are drawn behind the body, so his torso hides half of each shoulder port and his crest overlaps the hands.
- **Puffed-chest sweatshirt:** a broader, higher chest silhouette on f0, f3, f4 and f5.
- **Trouser creases:** short black creases at the inner knee on f0 and f3, the trousers pulled tight by the stance. They also lift those two frames into the black range.

## Notes for the coder
- **Feet jump (resolved):** see the fix above.
- **The BOOMBURST spreads wider than his usual body.** f4's hands reach x 3–94 and the windup's fists x 8–88, outside BODY_BOX (x 17–79). His roar already spans x 7–89, and he isn't punchable during the Echo.
- **The feet do step out for the BOOMBURST.** Going f2/roar → f3, they move from 33/63 to 28/68: the deliberate sumo plant.

## Arena mockups
- **`arena_mockup.png`:**
  - Built at 1920x1080 from ArenaScene.tscn's own textures and transforms: ringside, crowds, mat, ropes and poles.
  - Matt's f4 at HOME and Burak (the 4-dir sheet's UP frame) at (1290, 772).
  - All four ring kinds at once, in the plan's colours and widths, at 1800 px/s spacing.
  - The boss-bar block is outlined.
- **`arena_moments.png`:** three single moments (roar plus echo, psych plus ghost, BOOMBURST) at half size.
- **`contact_sheet.png`:** the live idle and roar f0–3 beside the new 6 frames at 4x, then game scale (3x) on the mat.

## Rig
- **Location:** `../tools/`, which imports the copy in `../rig/art_source/`. `ea_verify_rig.py` checks the copy against the live sheets.
- **Export:** `ea_export.py` writes nothing when run bare; `<dir>` refuses any folder inside the project; `--ship [--replace]` writes only `matt_echo.png` and `.aseprite`. `ea_preview.py <dir>` makes the previews.
- **Guard:** `guard.py` refuses every write into the project unless a `--ship` names the exact file, and refuses any process except Aseprite.
- **Moving it:** copied to `art_source/matt_echo/`, `env.py` switches to the live sibling rigs automatically.
