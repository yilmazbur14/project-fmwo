# Bixby beast, Hades redesign — the rig

Approved by the user 2026-09-23 (`Assets/Characters/Bixby/bixby_beast_redesign.png`). Everything the
look is built from lives here. Import it **read-only**; function names and signatures in these modules
stay stable, and new work goes into new modules.

```python
import sys
sys.path.insert(0, r'C:/Users/theyi/OneDrive/Documents/new-game-project/art_source/bixby_redesign')
import frame                      # pulls in pal, heads, body, wings, midmaps, sidemaps
im = frame.build('up', 0).image() # a 192x160 RGBA frame
```

Nothing in this folder writes into `Assets/` unless you pass `--write` to a script. Import the
modules; don't run other folders' export scripts bare.

## Conventions
- Frame 192x160, feet/hover anchor **(96,151)**, symmetry axis **x = 95.5** (a pixel at x mirrors to
  `191 - x`). Right side is authored; `pal.mir(part)` / `pal.both(part)` make the left.
- Keyline is pure `#000000`, 1px, round every part as it is stamped (`BCanvas.stamp(part)`), plus
  black separations/cuts inside forms. Target ~24.6% black, 38–45 colours, no semi-alpha.
- A *part* is a dict `{(x, y): key}`; keys are the palette letters in `pal.PAL` (one letter per colour).
- Light is top-front and mirrored; Hades rims: violet `e`/`f` on black and shadow edges, ember `u`/`v`
  on torn and burning edges.

## Palette (`pal.PAL`)
| ramp | keys dark→light |
|---|---|
| blood-red fur (Bixby's tan) | `q r s t u` + `v` hot ember |
| charcoal saddle (Bixby's black) | `a b c d` + `e f` violet rim |
| bone (Bixby's white) | `z y x w` |
| gold (spikes, studs) | `g G o O` |
| wine collar leather | `l L m M` |
| mint eyes | `h i j` (+ `W` glint) |
| tongue / fire | `n N p P Y` |
| steel (Liam's headband) | `S T U W` |
| wing membrane | `A B C` |

## Modules
- `pal.py` — palette, `BCanvas` (subclass of josh_redesign's keylining Canvas at 192x160; pass `w, h`),
  `mir`, `both`, `stats`. Re-exports `poly, ellipse, fill, rim, stroke, amap, dump, patch` from the Josh lib.
- `shapes.py` — `capsule`, `chain` (tapered limb/tail), `half` (symmetric polygon), `edge`, `recolor`, `poly_line`.
- `heads.py` — one head design in "head space" (the middle head's frame-0 coordinates + depth z).
  `Xf(cx, cy, phi, s, theta)` projects it: `phi` turns the head (3/4 view), `s` scales, `theta` tilts.
  `build(cv, xf, tongue_flip, with_collar, with_headband, features, low, brows)` stamps ears, crest,
  collar, ruff, skull, nose (+ procedural mouth/eyes when `features=True`). `headband_tails(xf, wave)`.
- `midmaps.py` — hand-drawn middle-head maps: `mouth_part`, `tongue_part`, `eye_parts` (snarl) and
  `inhale_glow`, `inhale_mouth`, `inhale_tongue` (jaw dropped, fire in the throat). All take `(dx, dy)`.
- `sidemaps.py` — hand-drawn face of the RIGHT side head, drawn against the head at `(156, 74)`;
  `parts(dx, dy, roar)`. The left head is its mirror.
- `body.py` — tail + white flame tip (`tail`, `tail_tip`, pose `'up'|'down'`), `hind_leg`, `front_leg`,
  hand-drawn paws `paw_map(front, dy)`, `mantle` (black saddle ruff), `chest`, `belly`, `side_neck`.
- `wings.py` — tattered bony wings, `build(cv, pose, mirror_fn)`, poses in `POSES` (`'up'`, `'down'`).
- `frame.py` — the approved composition: `build(pose, bob)` for `'up'`, `'down'`, `'sig'`;
  `side_head(bob, roar)`; `MID` / `SIDE` head placements.
- `lint.py` — islands, unkeylined edges, extents. `export.py` — numbers + previews (scratchpad).

## Head placement (frame 0)
- Middle head: `Xf(cx=95.5, cy=43)` (identity scale) — mouth maps at `dy = 3`.
- Side heads: `Xf(cx=156, cy=70, phi=-28, s=0.7, theta=12)`, face maps at `dy = -4`; turned in toward
  the player, top tilted out. The left head is `mir()` of the right.

## Animation rig (what the live sheets are built with)
One pose dict in, one frame out, in the approved stamp order. `python rig.py` proves the rig still
reproduces the approved frames pixel for pixel (`HOVER_UP`, `HOVER_DOWN`, `SIGNATURE`).

```python
import rig, rig_poses as RP, rig_wings as RW, rig_fx as FX
P = RP.grounded(14, RW.FOLD, front_x=124, hind_x=156,          # body 14px down, paws planted on y 151
                mid=dict(mouth='snarl', eyes='tired'), side=dict(eyes='tired'),
                fx=[FX.dust(40, 2, drift=-1)])
im = rig.build(P).image()                                        # 192x160 (pass H=256 in P for taller)
```

- `rig.py` — `pose(base, **fields)`, `build(P)`. Fields (see its docstring): `wings`/`wings_left`,
  `bob`, `tail_path`/`tail_tip`, `torso`, `front`/`front_left`, `hind`/`hind_left`, `planted`,
  `neck`, `side`/`side_left`, `mid`, `tails_wave`, `fx`, plus `side_face='right'` (both side heads
  face right, for the fly), `tails_mirror` (headband tails stream left), `front_over_sides` (front
  legs drawn over the side heads: a strike toward us), `shift` (whole frame), `shear` (lean into a
  flight; the feet row stays put), `hide` (any of 'wings','tails','tail','side','mid'), `H`.
- `rig_stance.py` — `stance(drop, ...)`: two-bone IK legs, paws planted on `GROUND = 151`;
  `front_joints(shoulder, paw)`, `hind_joints(hip, paw)`, `planted_front(x)`, `planted_hind(x)`.
- `rig_poses.py` — `grounded(drop, wings, mid=, side=, fx=, **stance_kw)` and every sheet's pose
  list (`hover`, `fly`, `takeoff`, `land`, `roar`, `recover`/`slump`, `hit`, `dizzy`, `pound`).
- `rig_body.py` — posable parts (`front_leg(J)`, `hind_leg(J)`, `paw(front, centre, planted)`,
  `torso`, `side_neck`, `tail(path)`, `tail_tip(at)`); defaults = the approved hover.
- `rig_wings.py` — wing poses `UP`, `DOWN` (approved), `MID`, `MID_UP`, `FLARE`, `DRAPE` (flat on the
  floor, spent), `FOLD`; `moved(P, dx, dy, sx, sy)`, `lerp(A, B, t)`, `build(cv, P, mir, P_left)`.
- `rig_heads.py` + `rig_faces.py` + `rig_faces2.py` — expressions. Middle mouths `snarl`, `inhale`
  (jaw dropped, fire in the throat; pass `low_dy=5` so the collar stays on the neck), `yelp`; eyes
  `open`, `tired`, `shut`, `dizzy`; `tongue=rig_faces2.mid_tongue_long` to pant. Side mouths `snarl`,
  `roar`; the same eyes; `tongue=rig_faces2.side_tongue_long()`. Heads move with `dx`/`dy`.
- `rig_fx.py` — `dust`, `speed_lines`, `sweat`, `star4`, `star5`, `rays`, `pebbles`,
  `ground_flash`, `motion_arc` (each returns an fx callable for a pose's `fx` list).
- `rig_fire.py`, `rig_spin.py`, `rig_shadow.py` — the fire-breath, spin and shadow sheets.
- `anims.py` — builds every sheet. `python anims.py` (SAFE: scratchpad only, with GIFs and a 3x
  contact sheet); `python anims.py --write` writes the live sheets + .aseprite and round-trips them.

Import note: `pal.py` appends `josh_redesign` to `sys.path` (it has its own `rig.py`/`export.py`),
so `import rig` resolves here. Put this folder first on your path.
