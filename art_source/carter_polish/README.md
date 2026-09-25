# Carter polish rig

This rig draws Carter (Akuma/Satsui no Hado) in the polish style that was approved on 2026-09-23. It
works in pixel space: a pixel written is the pixel shipped, and nothing is rescaled.

- **Frame:** 96x96.
- **Feet:** soles on row 95.
- **Mirror axis:** `x' = 95 - x`, centre 47.5.
- **Light:** from the upper left.
- **Keyline:** pure `#000000` around every part.
- **Palette:** every colour is in `lib.PAL`, which uses the approved sheet's own hexes. The aura
  keeps its dark-violet edge `#19062a` and never takes black.

Import these modules read-only. Their function names and signatures are stable. Put new work in a
new module.

```python
import sys; sys.path.insert(0, 'art_source/carter_polish'); sys.dont_write_bytecode = True
import lib, frame0, frame1, back, stand, faces, rig34, poses34, combat
cv = frame0.build()          # a lib.Canvas: cv.px is {(x, y): palette key}; cv.image() is an RGBA PIL image
```

This folder's `lib.py` has the same module name as `art_source/carter_akuma/lib.py`, so never load
both in one interpreter. `mark.py` shows how to run the old rig in a subprocess.

## The frames

| call | what |
|---|---|
| `frame0.build()` | standing, with the idle aura. This is the approved `carter_polish.png` frame 0, `carter_akuma` frame 0 and `carter_idle` frame 0. |
| `frame1.build()` | arms crossed, with the flare. This is the approved frame 1, `carter_akuma` frame 1 and `carter_akuma_pose`. |
| `back.build()` / `back.body()` | the back view with the 天, with or without the aura. This is `carter_akuma` frame 2. |
| `combat.SHEETS[name]` | `(frame_fn, count)` for every core combat sheet; `frame_fn(i)` returns a Canvas. |

**THE ENTRANCE MUST END ON `frame0.build()`.** `CarterArtLayout` cuts from the intro's last frame
straight to `carter_idle` frame 0, and the two must be byte-identical.

The back view's feet and the 天 sit exactly where `carter_akuma` frame 2 has them. `mark.ten_back()`
gives the mark at x 32..62, y 53..67, and `carter_mark_glow.png` is registered to those pixels
(offset (16, 32)). Any back-turned sheet built on `back.body()` keeps the glow aligned.

## Parts, for building new poses

**The standing body, `stand.py`:**

- `stand.body(eye=0, jaw=0, hdx=0, hdy=0)` builds the standing body without its aura. The head can be
  moved, and its eyes and jaw set to any state.
- `stand.aura(cv, level, seed, heat)` adds the flames behind him:
  - `level` runs from 0 (the idle aura) to 1 (the full flare);
  - `seed` picks a flicker variant, where 0 gives the approved shapes;
  - `heat` runs from 0 to 1 and controls how hot the flames burn.
- Effects: `stand.breathe`, `stand.shunt`, `stand.face_glow`, `stand.spokes`, `stand.pool`,
  `stand.streaks`.

**The head, `faces.py`:**

- `faces.head_part(eye, jaw, dx, dy)` gives the front head. `eye` is the glow level:
  - `-2` beaten;
  - `-1` strained;
  - `0` deadpan, the approved look;
  - `1` glaring;
  - `2` white-hot;
  - `3` blow-out, used with `faces.lances()`.
- `jaw` is `0` shut, `1` panting or `2` open.
- `faces.neck_part(dx, dy)` fills the gap when the head lifts or shifts.
- The earring and the back of the head: `faces.earring_part`, `faces.back_head_part` and
  `faces.back_earring_part`. From behind, the cross is on the screen RIGHT.

**The 3/4 rig, `rig34.py`:**

- `rig34.draw(pose)` draws the three-quarter figure from one joint dictionary, facing RIGHT. The
  format is in `rig34`'s docstring and the examples are in `poses34.py`: RUSH, PASS, SPENT and
  DEFEAT, the approved joints converted to pixels.
- Its parts can be used on their own:
  - `rig34.limb(segs)` for a continuous limb, toned in bands;
  - `rig34.fist(wrist, fist)` for a wrapped fist;
  - `rig34.foot(ankle, deg)` for a foot at any angle;
  - `rig34.flat_hand`, `rig34.trousers`, `rig34.jacket`, `rig34.belt` and `rig34.caps`.
- `fx34.py` has the 3/4 effects: `dash`, `tails`, `gutter` and `sweat`.

**The flames, `aura.py`:**

- `aura.flames(specs, body_pixels, order, heat=0)` draws flame tongues.
- `aura.IDLE`, `aura.FLARE` and their `*_ORDER` lists are the approved sets.
- `aura_overlay.frame(i)` is the ambient `carter_aura.png`.

**Front-view maps:** `head.py`, `chest.py` (with the beads), `arms.py` (with the fists), `jacket.py`,
`lower.py` (belt, knot, trousers, shins and feet) and `cross.py` (the crossed arms) hold the
approved front-view pieces as ASCII maps and functions. `lib.amap`, `lib.patch` and `lib.dump` are
the hand-edit tools.

## Building and shipping

- `python build.py [--ship]`: `carter_polish.png`, the approval sheet.
- `python ship_all.py [--ship]`: the core combat set. With no flag it only renders, lints and
  writes previews to the scratchpad. `--ship` writes each PNG whole (to a temp file, then
  `os.replace`), saves the `.aseprite` beside it and round-trips it with `imgdiff.pixel_diff`.
