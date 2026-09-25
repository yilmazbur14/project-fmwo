# VS card poses: style guide

This guide covers every fighter on the VS card. The model is Pokémon Platinum's VS portraits: waist-up, one clear gesture, framed inside the panel. The finish is Matt's intro set (`Assets/Characters/Matt/matt_talk.png`, `matt_roar.png`), which the user named as the standard on 2026-09-23. Burak, Eric and Carter follow this guide (`build_mocks.py`), so check those three before drawing a new pose.

## Framing

- The band is 640 x 132 texels, drawn at 3x. Each pose lives inside its own half. The top and bottom rules crop it, and the seam cuts it: the seam's black rule and accent lines are drawn over the pose, like a panel border. Nothing breaks the band and nothing crosses into the other half. Eric's blade stops at the seam. (`halves.py`)
- The halves stay 640 x 132 at `BAND_AT`, so they drop straight into the game with no code change.
- Keep clear of:
  - the VS: x 289-363, y 40-92;
  - the name plate: lower right, y 93-118, from x 525 (ERIC) to x 436 (COMPUTAH). LIAM & BIXBY on one line would reach x 393, so it goes on two lines at 55, as `vs_card/bosses.py` already plans.
  The name may overlap a shoulder or cape. It must never cover the face or the gesture.
- **Eye line: band row 58 ± 2** for everyone, so the two fighters look at each other on one line.
- Crop at the chest or waist. The top rule may cut hair spikes, an aura or a hat, but never the face.

## Scale

- **One magnification for everyone: 2x of the 64-96 px sheets** (Eric, Carter, Computah, Matt, Mason, Josh, Liam, Jordan, Captain Burak), enlarged with **Scale2x** (`pxkit.scale2x`), never NEAREST. Heads then come out 44-64 texels by each character's own build: Eric, Carter and Matt at 56-64, and slim Jordan and Josh at about 46. Don't go to 3x to even that out; a 3-texel keyline breaks the outline rule.
- Danny's and Bixby's big sheets already have card-sized heads at 1x. Use them at 1x, and grow the silhouette keyline outward by one texel so it matches everyone else's 2.
- Burak has no sprite big enough, so he is drawn as a 1x sprite at a head of about 30 px and gets the same Scale2x.

## Light

- There is one light for every pose: **upper left**, a little toward the viewer (`volume.LIGHT`). It is the house light every boss sheet already uses.
- Never ship a mirrored figure: a mirror moves the light. Mirror only what is shaded along its length (Eric's blade), and move lit parts by translation instead (his hilt and arms). Where a turn is unavoidable, re-light it: Carter's head is mirrored, its dome takes its tones from the unmirrored sphere, and the face side steps one tone up its own ramp.

## Outline

- The keyline is **pure black**, except Computah, whose keyline is `#0C111A`. Measure it per character (`measure_cast.py`).
- It is drawn at sprite scale and doubled by Scale2x, so it is 2 texels on the card. The 2x pass never thins or thickens it.
- Every internal shape gets a black separation: a limb over the body, a glove, a headband, a collar, each aura spike. Muscle-on-muscle lines use a dark tone of the skin.
- The 2x pass may add 1-texel interior lines (a keyline inside a spike, a crease) and 1-texel lights.

## Shading and palette

- Use clean cel shading: 3-4 working tones per material from the character's **own approved ramp**, plus at most one light accent (a rim or shine) and one crease tone.
- No gradients. No dithering unless the sprite already has it (Carter's 天 bloom).
- **No semi-alpha.** Alpha is 0 or 255.
- Lock every pose to the character's palette (`pxkit.lock`).
- Burak keeps his approved 17 colours with no white anywhere. His eye glint is his lightest skin tone.

## Expression and gesture

- Faces must read at 3x: black brows, and eyes built the way Matt's are (black lid, black iris, one glint on the lit side), with a clear mouth shape.
- Give each character one clear gesture (a fist, a blade, a turned back) and at most one effect (a glint, an eye flash, sound rings).

## Build from their own pixels

1. Crop the frame that already holds the gesture.
2. Cut it into parts along its own keylines (`segment.py`).
3. Move, swap or mirror parts under the light rule.
4. Scale2x, then the 2x detail pass.

Every pose script says which frames it uses and what moved. Measure the result against the source view it came from: **within ±2 points of black and ±3 colours**, and report both numbers.

## Numbers

Measured with `measure_cast.py`: the share of opaque pixels that are the keyline colour (pure black unless noted), and the colour count.

| Character | Source | Black / colours | Pose (2x) |
|---|---|---|---|
| Burak | `player_4dir_sheet.png` (approved card bust 19.0% / 17) | 13.9% / 7 | 26.1% / 17, raised past his sheet by the user's approval; hold him inside the cast's 20-28% |
| Eric | `eric_sheet_v2.png` idle frame (sheet 19.6% / 44) | 20.1% / 39 | 21.6% / 38, from frame 3 (20.8% / 38) |
| Carter | `carter_look_back.png` back view (front `carter_polish` 24.0% / 50) | 19.2% / 47 | 21.2% / 47 |
| Computah | `computah_idle.png` | 21.3% `#0C111A` (0% black) / 41 | not yet |
| Matt | `matt_roar.png` (talk sheet 24.7% / 39) | 25.5% / 39 | 24.0% / 40, roar frame 2 plus `matt.png` frame 1's rings |
| Mason | `mason.png` (sheet 24.1% / 25) | 22.6% / 15 | not yet |
| Josh | `josh_cards.png` | 28.3% / 38 | 29.0% / 38, frame 1 |
| Danny | `danny_sumo_redesign.png` | 16.6% / 26 | not yet |
| Liam | `liam.png` | 28.2% / 35 | not yet |
| Bixby | `bixby_beast.png` | 25.0% / 38 | not yet |
| Jordan | `jordan_redesign_v2.png` (v2, approved 2026-09-24; f0 28.2% / 40, f1 29.2% / 40) | 28.8% / 40 | 29.7% / 40, drawn with his v2 rig: frame 1's fist-pump, frame 0's box arm (the v1 card was `jordan_taunt` frame 2, 27.6% / 40) |
| Captain Burak | `BurakBoss/burak_boss.png` (f0 idle 24.8% / 38, f1 shot 25.9% / 38) | 25.4% / 38 | 25.2% / 38, drawn with his rig: frame 1's body and gun hand, frame 0's smirk |

## Poses

The style was approved on 2026-09-23. Burak, Eric, Carter, Jordan, Matt and Josh have shipped to `Assets/UI/VsCard` with their flags on (`ship.py`). Each pose is one gesture, framed waist-up, built from the frames named.

- **Burak:** the fist up, his lead glove raised in front of his chest, three-quarters to the VS, headband tails trailing. Drawn. *Shipped.*
- **Eric:** the greatsword levelled overhead at Burak, cut by the seam, a glint where it points. Frame 3. *Shipped.*
- **Carter:** back turned, the 天 burning, one red eye glaring back at Burak with a flash. `look_back` 3 and `victory` 4. *Shipped; epithet THE DEMON.*
- **Jordan (v2, since 2026-09-24):** the fist punched skyward with the pink pop and gold star, the chase box held up by his face on his other stick arm, mid-shout. Drawn with his v2 rig (`art_source/jordan_v2`, read-only, `pose_jordan_v2.py`). It is frame 1 as drawn, except the far arm is frame 0's, which holds the box up by his face; frame 1 hangs the box at his hip, below the crop. `rebuild_check()` proves the file still draws both sheet frames exactly. He faces screen-right as his sheet does and, like Josh, is not mirrored, so he no longer turns to Burak as the v1 card did. *Shipped over the v1 card, which was `jordan_taunt` 2; epithet THE ADMIN.*
- **Matt:** mid-roar, jaws wide and eyes red, fists braced, with his two sound rings behind him. `matt_roar` 2 plus `matt.png` frame 1's rings, redrawn at 2x. His band has no ghosted emblem, because the rings are his mark. *Shipped; epithet THE WALL OF SOUND, proposed.*
- **Josh:** the card fan held toward Burak, the gold spade card glowing up by his face, the wink. `josh_cards` 1, as drawn. He faces screen-right in his v3 sheet, and is kept that way rather than mirrored. *Shipped; epithet THE CARD SHARK.*
- **Computah:** the cannon levelled at Burak, the muzzle charging green, the battery full. `computah_beam_ready`/`_charge`, with the barrel mirrored (shaded along its length) and the arm translated.
- **Mason:** the nugget bucket hugged to his chest, grinning over the rim. The bucket frame of `mason_sheet`.
- **Danny:** the slap drawn back, one palm thrust at Burak and the other raised, eyes half shut behind the snot bubble. `danny_sumo_redesign` 1, with 0's bubble face.
- **Liam & Bixby:** Liam's glasses push with its glint; Bixby's centre head looms over his shoulder, cropped by the top rule. `liam_glasses_push`, `bixby_beast`. The name goes on two lines.
- **Captain Burak (boss 1, Burak vs Burak):** the cutlass on his shoulder, the bell-mouthed flintlock raised beside his head and aimed at the viewer, the cocky smirk. Drawn with his own rig (`art_source/burak_boss`, imported read-only, `pose_captain.py`). The body, cocked head, rakish hat and sword arm are frame 1's. The smirk is frame 0's. Frame 1's gun hand is moved up whole to eye level, and only the arm is re-laid with the rig's own sleeve, cuff and forearm. `rebuild_check()` proves the file still draws frame 1 exactly. The tricorn's tips go under the top rule. His half is key `burak` (`build_captain.py`). *Shipped as art only, with no flag and no table entry yet. Epithet THE CAPTAIN, proposed. The band is sea teal with his gold on the seam, and there is no watermark because his head and gun fill the emblem box.* Frame 1's wink-and-grin is one word away (`FACE = "shot"`).

## Bands

Each boss's half keeps a ramp, a pair of seam hairlines and a ghosted emblem (`bands.py`). The ramp is chosen **against** the boss's biggest colour mass, so the figure never sinks into it. Eric's is shipped and unchanged.

## Placement

`build_mocks.PLACE`, `build_trio.PLACE` and `build_captain.PLACE` hold where each pose's canvas sits in the band. Put the eyes on row 58, then slide the figure until its face and gesture clear the name plate.

## Safety

- `build_mocks.py`, `build_trio.py` and `build_captain.py` refuse any path inside `Assets/`. Only `ship.py --ship` writes there. It backs up what it replaces, reads each card's number and rank from `Scripts/VsCardArtLayout.gd`, and writes whole files by atomic rename.
- After shipping, run one headless `--import` (with `project.godot` backed up and compared afterwards), load every new texture headlessly, then flip the flag. That order means the game never loads a missing file.
- Save a `.aseprite` beside every PNG and prove the round trip with `imgdiff.pixel_diff`.
- Nothing here ships until the user approves it.
