"""demon_darkness.png and demon_spotlight*.png - the stage the sequence plays on.

DARKNESS is one 640x360 image drawn at exactly 3x, not a tile.  A tile cannot do
the job: the requirement is that the crowd stays faintly visible, and in
ArenaScene the crowd is a band across the top hundred pixels of the screen while
the ring floor is everything below it.  That is a vertical gradient keyed to the
arena's actual layout, which is a property of the whole screen and not of any
repeating unit.  640x360 is the largest texture that still lands on an integer
3x, so it needs no filtering and its pixels line up with every other sprite's.

Banding is the obvious risk in a near-flat 8-bit gradient, so no alpha here is
ever laid down flat: the float alpha is ordered-dithered to integers through an
8x8 Bayer matrix, which spreads each 1/255 step over an area instead of drawing
a contour line across the screen.

SPOTLIGHT ships as two files on purpose, and the reason is the layer order.  The
darkness has to sit ABOVE the floor and the crowd but BELOW the fighters, or the
player and the clones get dimmed along with the scenery and nothing looks lit.
That puts the floor pool under the fighters too - it is light landing on the
ground.  But the cone is light in the air BETWEEN the camera and the fighters,
so it has to go over them.  One file cannot be in both places.

  demon_spotlight.png       pool + cone in one, ONE node, below the fighters.
  demon_spotlight_pool.png  the pool alone, below the fighters.
  demon_spotlight_cone.png  the cone alone, above the fighters.

All three share the canvas and the anchor, so they are drop-in for each other.
Use demon_spotlight.png on its own, OR pool+cone as a pair - never the whole
image and the cone together, which lays the shaft down twice and doubles it.

Both are additive.  Additive white on a stage darkened to about #171718 lifts
the pool to a warm grey rather than back to green, which is what a real
spotlight on a dark stage does anyway.
"""
from fxlib import (Cv, Mask, ell, poly, quant, bayer01, hexc, rgba,
                   write_png, CLEAR)

# ------------------------------------------------------------------ spotlight

SW, SH = 160, 224          # texels; at 3x this is 480 x 672 on screen
PX, PY = 80.0, 186.0       # pool centre = the anchor = where the player stands
PRX, PRY = 66.0, 58.0      # 396 x 348 px of pool at 3x

WARM = hexc('f0d8a4')
PALE = hexc('fff2d6')
WHITE = hexc('ffffff')

# (colour, additive strength).  The top of the ramp is deliberately short of
# blowing out: +132 of fff2d6 lifts the darkened floor to about (143,135,116),
# a warm lit sand, and leaves the player readable as a dark shape inside it
# instead of a silhouette against white.
POOL_STEPS = [None,
              rgba(WARM, 18), rgba(WARM, 34), rgba(PALE, 54), rgba(PALE, 76),
              rgba(PALE, 100), rgba(PALE, 124), rgba(WHITE, 146)]
CONE_STEPS = [None,
              rgba(WARM, 10), rgba(WARM, 17), rgba(PALE, 25), rgba(PALE, 34),
              rgba(PALE, 44), rgba(PALE, 54)]

CONE_TOP_HALF = 15.0       # half width of the shaft where it leaves the frame
CONE_BOT_HALF = 52.0       # tucked inside the pool's rim: flaring wider than
# the pool leaves the shaft visibly overhanging the light it is supposed to be
# casting
CONE_BOT = 196.0


def _cone_field():
    """bright up the middle of the shaft, fading out sideways and upward"""
    f = [[0.0] * SW for _ in range(SH)]
    for y in range(SH):
        cy = y + 0.5
        if cy > CONE_BOT:
            continue
        t = cy / CONE_BOT
        half = CONE_TOP_HALF + (CONE_BOT_HALF - CONE_TOP_HALF) * t
        for x in range(SW):
            d = abs(x + 0.5 - PX) / half
            if d >= 1.0:
                continue
            # near zero where the shaft leaves the top of the canvas: a 30%
            # floor there cuts the beam off with a straight edge across the
            # screen
            f[y][x] = (1.0 - d * d) ** 1.1 * (0.05 + 0.95 * t ** 0.85)
    return f


def _pool_field():
    f = [[0.0] * SW for _ in range(SH)]
    for y in range(SH):
        dy = (y + 0.5 - PY) / PRY
        for x in range(SW):
            dx = (x + 0.5 - PX) / PRX
            d = (dx * dx + dy * dy) ** 0.5
            if d < 1.0:
                # a soft shoulder rather than a cone: flat-ish in the middle,
                # most of the falloff happening near the rim
                f[y][x] = (1.0 - d * d) ** 1.15
    return f


def _draw(cv, fld, steps):
    idx = quant(fld, len(steps))
    for y in range(cv.h):
        for x in range(cv.w):
            i = idx[y][x]
            if i > 0:
                cv.px[y][x] = steps[i]


def _pool_onto(cv):
    _draw(cv, _pool_field(), POOL_STEPS)
    # a crisp rim just inside the pool's edge: without it the pool has no
    # boundary at all and reads as fog rather than as a light
    rim = (ell(SW, SH, PX, PY, PRX, PRY).erode(2)
           - ell(SW, SH, PX, PY, PRX, PRY).erode(5))
    cv.paint(rim.dither(5, off=1), rgba(WARM, 30))
    return cv


def spotlight():
    cv = Cv(SW, SH)
    _draw(cv, _cone_field(), CONE_STEPS)
    return _pool_onto(cv)


def pool_only():
    return _pool_onto(Cv(SW, SH))


def cone_only():
    cv = Cv(SW, SH)
    _draw(cv, _cone_field(), CONE_STEPS)
    return cv


# ------------------------------------------------------------------- darkness

DW, DH = 640, 360          # exactly 3x -> 1920x1080, no filtering
INK = (12, 6, 24)
CROWD_ROWS = 33            # screen y 0..100 is the crowd band
FADE_ROWS = 23             # blend from the crowd's alpha to the floor's
A_CROWD = 150.0            # crowd survives at ~41%
A_FLOOR = 236.0
A_VIGNETTE = 15.0          # extra ink toward the edges


def darkness():
    rows = []
    cx, cy = DW / 2.0, DH / 2.0
    for y in range(DH):
        row = []
        if y < CROWD_ROWS:
            base = A_CROWD
        elif y < CROWD_ROWS + FADE_ROWS:
            t = (y - CROWD_ROWS) / float(FADE_ROWS)
            base = A_CROWD + (A_FLOOR - A_CROWD) * (t * t * (3 - 2 * t))
        else:
            base = A_FLOOR
        for x in range(DW):
            dx, dy = (x + 0.5 - cx) / cx, (y + 0.5 - cy) / cy
            v = min(1.0, (dx * dx + dy * dy) / 2.0)
            a = base + A_VIGNETTE * v * (0.25 if y < CROWD_ROWS else 1.0)
            # ordered dither to integer alpha: a flat round() here draws a
            # visible contour wherever the ramp crosses a whole number
            ai = int(a)
            if (a - ai) > bayer01(x, y):
                ai += 1
            row.append((INK[0], INK[1], INK[2], min(255, ai)))
        rows.append(row)
    return rows


def build(path_light, path_pool, path_cone, path_dark):
    spotlight().save(path_light)
    pool_only().save(path_pool)
    cone_only().save(path_cone)
    write_png(path_dark, DW, DH, darkness())
    return path_light, path_pool, path_cone, path_dark
