"""danny_worm_root.png: worms rooting the player's feet, then letting go. 8 frames of 48x32, one strip:
  f0-3   ROOTED, a loop at 0.08 s: a slime pool under his feet and worms coiled round both ankles, their
         coils sliding and their loose ends wriggling up his shins
  f4-7   RELEASE, once at 0.05 s: the coils snap loose and fly off, the slime splashes, the bits fall away
THE PIVOT IS (24, 26): the floor under the player's feet (on his own 32x32 frame that is (16, 29), 13
texels below the frame centre). Draw it OVER the player. Never flipped (it wraps both feet).
The worms' own pinks (1-5) on his darkest-brown slime (x 6 D), no keyline.
"""
import math

import dfx_pal as pal
import dfx_worms as wm

W, H = 48, 32
PX, PY = 24.0, 26.0
FRAME_SIZE = (W, H)
NOTE = '8 frames of 48x32: f0-3 rooted loop at 0.08 s, f4-7 release once at 0.05 s; pivot (24,26) = the floor under his feet'
FEET = (19.0, 29.0)          # the two ankles' x (his feet span x 9-23 of his frame: 17-31 here)


def pool(g, rx, ry, drops=()):
    mask, _ = wm.blob_mask(W, H, PX, PY + 0.5, rx, ry, seed=4, drops=drops)
    wm.stain(g, mask)
    return mask


def coil(g, ax, ph, turns=2, top=9.0):
    """Worm coils round an ankle at ax: loops of a helix seen from the front (their front halves, drawn over
    his leg), rising from the slime to `top` texels up his shin, sliding with ph."""
    for t in range(turns):
        y = PY - 1.5 - t * (top / turns) - 0.8 * math.sin(ph + t)
        pts = [(ax - 3.4 + 6.8 * (i / 14), y + 1.6 * math.sin(math.pi * i / 14)) for i in range(15)]
        wm.worm(g, pts, width=2.3, taper=False, saddle=-1, glint_every=5)


def frame(f):
    g = pal.blank(W, H)
    if f < 4:
        ph = f * math.pi / 2
        pool(g, 12.5, 3.4, drops=[(10.0, 26.5, 1.3, 1.0), (38.5, 27.0, 1.2, 1.0)])
        for n, ax in enumerate(FEET):
            coil(g, ax, ph + n * 1.3)
            # a loose end wriggling up the shin
            x0, y0 = ax + (2.0 if n else -2.0), PY - 8.5
            pts = wm.wiggle(x0, y0, x0 + (1.5 if n else -1.5), y0 - 5.0, 1.1, 1.0, ph * 1.3 + n, n=14)
            wm.worm(g, pts, width=2.1, saddle=-1, glint_every=0)
        return pal.rows(g)
    k = f - 4
    # the release: the slime pool splashing and shrinking, the worm pieces flung up and out, falling
    pool(g, [11.5, 9.0, 6.5, 4.0][k], [3.1, 2.6, 2.0, 1.4][k])
    t = [0.0, 0.05, 0.10, 0.15][k] + 0.03
    for (vx, vy, L, p) in ((-70, -120, 5, 0.0), (80, -110, 5, 1.1), (-98, -60, 4, 2.2), (100, -70, 4, 3.3), (-20, -150, 4, 4.4), (30, -140, 4, 5.5)):
        x = PX + vx * t
        y = PY - 5 + vy * t + 0.5 * 900 * t * t
        if not (0 <= x < W and 0 <= y < H):
            continue
        a = math.atan2(vy + 900 * t, vx) + p
        pts = wm.wiggle(x - L / 2 * math.cos(a), y - L / 2 * math.sin(a), x + L / 2 * math.cos(a), y + L / 2 * math.sin(a), 0.8, 1.0, p + k, n=12)
        wm.worm(g, pts, width=2.0, saddle=-1, glint_every=0)
    # slime drops flung off
    for (vx, vy) in ((-90, -90), (95, -80), (-40, -130), (50, -125)):
        x, y = int(PX + vx * t), int(PY - 3 + vy * t + 0.5 * 900 * t * t)
        pal.put(g, x, y, 'D')
        pal.put(g, x + 1, y, 'x')
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(8)]
