# Greyson's final brawl FX: APPROVED 2026-09-24

The user: "approve everything so far". That covers every sheet below, the revised close-quarters hook and straight, and the adopted rubble layout rule.

**This is the design of record** for the FX of `FinalBrawl`, the Punch-Out phase of the Computah + Greyson fight (`PLAN_BRAWL.md`). Any change to these sheets is a new approval.

## Files
- **The sheets:** `Assets/Characters/Greyson/Brawl/brawl_*.png`, each with its `.aseprite` beside it. Each `.aseprite` round-trips pixel-identical through `art_source/imgdiff.py`'s `pixel_diff`.
- **The rig:** this folder.
  - `gb_pal.py`: the palette and grid helpers.
  - `gb_debris.py`, `gb_rubble.py`, `gb_arrow.py` and `gb_punch.py`: the art.
  - `gb_build.py`: the build.
  - `gb_preview.py`: the zoom 1.0 previews.
  - `gb_preview15.py`: the brawl as the plan stages it, at zoom 1.5 with the player at 2x.
  - `gb_look.py`: zoomed contact sheets.
- **Imports, not copies:** the rig imports Matt's arrow shape (`matt_fx/mfx_arrow.UP`) and the house dust puff (`matt_fx/mfx_dustlib`). The previews import the arena compositor from `carter_messatsu_fx/previews.py`.

## Rebuilding
- `python gb_build.py <scratch_dir>` makes a scratch build anywhere except `Assets/`.
- `python gb_build.py --ship` writes the shipped sheets.
- There is no default output. Only `--ship` can write into `Assets/`.
- After a ship, re-save each PNG as `.aseprite` with the Aseprite CLI:
  `"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe" -b f.png --save-as f.aseprite`
  Then round-trip each one through `pixel_diff`, never a bare `getbbox()`.
- Previews: `python gb_preview15.py <sheet_dir> <out_dir>` and `python gb_look.py <out_dir> [debris land rubble arrow punch]`. Both write only where they're told.

## The conventions (Matt's effects set them)
- No keyline, hard edges and no dither.
- Partial alpha only at 176 and 96. Black only in the shadow sprite, which the code modulates.
- Nothing is rotated in the engine. Tumbling and direction are drawn frames.
- The rubble heaps are lit from the top left, so they are **never flipped**.
- **Gold appears only in the arrows** (the dodge colour). **No red anywhere** (red is the parry). The punch FX are white on Greyson's pale steel greys, so nothing reads as a tell.

## Where every colour comes from
| Use | Colours | Source |
|---|---|---|
| Concrete and dust | `#FBF7EE #EDE4D6 #C7BBAB #948779 #6B6157` | The house dust ramp, from Josh's `card_giant_impact` plume, used by Matt's stomp dust |
| Crevices and floor contact | `#332B2B` | `arena_ringside.png`'s warm near-black |
| Steel, and the whooshes' trailing band | `#D5D9EC #9DA1C0 #3F3F52 #2A2A38` | Greyson's own greys |
| Rebar | `#C27434 #8C4522` | His hair-shade browns |
| The arrows | `#FFFCE0 #FFE45C #FFC21E #D68A12` | The shared dodge tell (`Assets/Effects/dodge_tell.png`) |
| The arrows' disc | `#391555` | His darkest trunk purple |

## The contract
Every sheet is a horizontal strip, frame 0 leftmost, at scale 3. The pivot is the texel placed on the world point given (world px from `PLAN_BRAWL.md` §4).

| Sheet | Frame × count | Layout | Pivot → world point | Timing |
|---|---|---|---|---|
| `brawl_debris` | 32×56 ×8 | frame = shape×2 + spin. Shape 0 block, 1 slab, 2 beam, 3 clump. The chunk is the bottom 32 rows; its dust trail is above it | (16,56), bottom centre → the piece's base (centred offset (0,−28)) | Spin swaps every 0.06 s. It falls 0.40 s ease-in from 420 px above its base, in FxLayer |
| `brawl_debris_shadow` | 36×12 ×1 | Solid black | (18,6), centre → the base | The code scales it 0.3→1.0 and fades alpha 0.15→0.5 over the fall |
| `brawl_debris_land` | 80×48 ×6 | f0 the smack; f1–3 the dust rolls out; f4–5 it thins (176, then 96) | (40,40) → the base | 0.05 s per frame. Swap the heap in under f2 |
| `brawl_rubble_mound` | 64×48 ×10 | 0–1 big with a beam; 2–4 big; 5–7 medium; 8–9 low ridges | (32,46), footprint centre (centred offset (0,−22)) | Static. Y-sorted by base. Never flipped. About 132 px apart along a wall |
| `brawl_rubble_bits` | 16×12 ×8 | Loose chunks for the foot of a wall | (8,11), bottom centre | Static |
| `brawl_arrow` | 28×28 ×8 | frame = dir×4 + state. Dir 0 LEFT, 1 RIGHT. States: 0 pop, 1 live, 2 answered, 3 missed | (14,25), disc bottom → the tell point (960,308) | Pop 0.05 s, then live held to the resolve (never pulses), then answered or missed for about 0.10–0.15 s, then ParryTell's 0.09 s fade |
| `brawl_hook` | 64×32 ×8 | 0–3 his LEFT hook (from screen-right, the LEFT arrow's); 4–7 the RIGHT hook, drawn mirrored, not flipped. Step 0 leaves the wind-up; 1 the fist on the head's rest point; 2 the follow-through; 3 a wisp | (22,19) / (42,19) → the player's head at rest (960,446), slipped or not | 0.04 s per step. z 2 |
| `brawl_straight` | 32×32 ×4 | Converging lines, then the core and ring, then the ring breaking, then gone | (16,16), centre → the parry contact (957,416) | 0.04 s per step. z 2, so behind the player's gloves |
| `brawl_impact` | 48×48 ×5 | The star and burst, the ring, then the ring breaking and sparks | (24,24), centre → the player's head (960,446) | 0.04 s per frame. z 4 |

**The details that go with it:**
- **Heap heights,** in texels for frames 0–9: 40, 37, 38, 34, 36, 28, 26, 24, 16, 13. Any of frames 7–9 along the clearing's front edge (y about 700–730) stays below the player's soles (572).
- **The hook's arc,** in texels from its pivot: wind-up (+34,−14), then the head (0,0), then past (−10,−3), dipping 0.3 texels at the head. The RIGHT hook mirrors it.
- **Resolve timing:** step 1 of the hook and the straight must be on screen on the resolve frame. Start the strip 0.04 s before, or start it at step 1. The impact's f0 goes on the resolve of a hit.
- **The red indicator is the shared ParryTell badge, unchanged:** `Assets/Effects/parry_tell.png`, 32×24 ×6, pivot (16,24), fired by `ParryTell.telegraph(body, &"greyson_brawl_straight", lead, tell_point)`.
- **The dodge afterimage is code, not a sheet:** 3 copies of the player's current frame in `#5FCDE4` (the perfect-dodge cyan) at alpha 0.45, 0.30 and 0.15, spaced between the rest position and the slip, fading over 0.15 s.

## The rubble layout rule (ADOPTED)
- **The rule:** no heap may be drawn over x 840–1080, y 225–560. That box is where his silhouette and the tell stand.
- **Why:** it replaces the first-written rule (no heap top above y 330 within 120 px of x 960), which emptied a lane behind him up to the top rope.
- **Where:** `gb_preview15.rubble()` defaults to the adopted rule, and `rule='plan_literal'` renders the old one for comparison. It's recorded in `PLAN_BRAWL.md`'s coordinator amendments.

## Approval material
In the session scratchpad `...\scratchpad\greyson_brawl_fx\`:
- `prev15\`: the zoom 1.5 beats, 1:1 crops, GIFs and the kit sheet.
- `prev\`: the zoom 1.0 cutscene, debris GIFs and tells.
