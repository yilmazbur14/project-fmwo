# Greyson redesign: APPROVED 2026-09-24, stored for future use

The user: "approve greysons redesign and store it somewhere for future use".

**This is Greyson's design of record.** Any future Greyson art starts from it: full animation sheets, a VS card, a portrait or a cameo.

**It is NOT wired into the game.** Greyson left the boss order on 2026-09-22, and Computah now fights solo, so nothing references these files. Wire them only when the user brings Greyson back.

## Files
- **The sprite:** `Assets/Characters/Greyson/greyson_redesign.png` and its `.aseprite`, a 224x112 strip of 2 frames, frame 0 on the left.
- **The rig:** this folder. The figure is built in `gr_fig.py` from `gr_kit.py`, `gr_muscle.py`, `gr_arms.py`, `gr_hands.py`, `gr_face.py` and `gr_boots.py`.
- **The previews:** `approved/`, with both frames at 4x, each frame alone, and `lineup_game_scale.png` (at game scale beside the player, Computah and Matt, feet on one line).
- **Checked 2026-09-24:** the rig renders pixel-identical to the shipped PNG. The `.aseprite` re-exports identical too (`art_source/imgdiff.py`).

## Frames and wiring numbers
- **Frames:** 112x112, with the feet at (56,111).
- **f0 is the ready stance:** arms pushed out by the lats, fists clenched beside the thighs, a big grin.
- **f1 is a front double biceps:** a clenched grimace, the forehead vein swollen and forked, brows crushed into a V, a sweat bead.
- **Sprite2D:** `hframes = 2`, `vframes = 1`, scale 3, offset (0, -56) so the feet sit on the node.
- **Size:**
  - 86 texels tall (258 px on screen). Computah is 79 to his helmet and 90 to his antenna tip, so Greyson's head is about 21 px above Computah's helmet and he's far heavier.
  - 79 texels wide idle, 97 flexing.
- **Numbers:**
  - The keyline is pure `#000000`, like the rest of the human cast.
  - Black is 17.3% idle, 18.3% flexing and 17.8% for the sheet, in line with the skin-heavy cast (muscle lines are dark skin tones, not black).
  - 28 colours.
  - No semi-alpha, and no keyline gaps, strays or pinholes. The silhouette is mirror-symmetric apart from the sweat bead.

## The design
- **Build:** a bodybuilder V-taper with steep traps, capped delts, a six-pack and quad sweep. It's not Danny's sumo mass.
- **Hair:** long and centre-parted, golden with strawberry-copper shadows. A black cut splits it into two pointed locks.
- **Face:**
  - The user's portrait's red chevron forehead vein (`#D95763`) and blue eyes (`#639BFF`).
  - Thin gold wire glasses.
  - A thin moustache with a horseshoe drop at the corners.
- **Outfit:**
  - Purple trunks in Computah's own paint ramp, so the robot wears its maker's colours.
  - White boots with a folded cuff, laces and charcoal soles.
- **Sources:**
  - The user's two photos of Greyson: a mirror selfie and a close-up.
  - The user's own portrait drawing (`Assets/Characters/Greyson/portrait.png`).
  - The house standard of Matt's art.
  - The photos are private and stay out of this public repo.
- **Left out, but any can come back:** the inner-forearm tattoo (at 3x it reads as a vein), the silver chain (it clutters the traps), and the photos' crop tank and paint-dripped trousers (which lost to trunks and boots).

## Re-exporting
`gr_export.py` is guarded:
- A bare run writes nothing.
- A scratch folder inside Assets is refused, 8.3 short names included.
- `--ship` never overwrites without `--replace`.

Preview into a scratch folder first, as with every exporter in `art_source`.
