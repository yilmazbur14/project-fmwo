"""josh_glider.png  - the giant card Josh rides, 3 frames of 64x28, pivot (32, 14).
   josh_shadow.png  - his ground shadow, 4 frames of 80x24, pivot (40, 12).

Fit, measured off Assets/Characters/Josh/josh_glide.png (80x80 frames):
  - his soles bottom out at local y = 74-75, foot contact spans x = 21..57, centre x = 39
  - rows 76..79, x 24..55 ALREADY CONTAIN a baked gold card stub ('8a5a1c' / 'c48a2c')

So the deck's top surface sits at glider-local y = 6 and the glider is placed at Josh-local
(7, 70).  Rows 6..9 of the deck are painted in that same dark-gold ramp, which makes the baked
stub land on matching colour and disappear into the deck instead of showing as a seam.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

# --------------------------------------------------------------------------- glider
GW, GH = 64, 28
DECK_TOP = 6                 # the row Josh's soles rest on
DECK_BOT = 15                # last row of the visible top face
CXG = 32.0
THICK = 3                    # card-stock edge below the face

# per frame: bank (end-drop in texels), vertical bob, trail phase.  Three phases of one cycle,
# so a plain 0-1-2 loop is continuous.
BANK = [(0.0, 0, 0), (1.0, -1, 1), (-1.0, 0, 2)]


def deck_hw(t):
    """Half-width of the top face at row fraction t (0 = far edge, 1 = near edge)."""
    return 25.0 + 3.0 * t


def build_frame(i):
    bank, bob, ph = BANK[i]
    c = Cv(GW, GH)

    def tilt(x):
        """The card banks about its centre: one end dips, the other lifts."""
        k = (x - CXG) / 32.0
        return bank * math.copysign(k * k, k)

    # ---- top face ---------------------------------------------------------
    face = {}
    for y in range(DECK_TOP - 2, DECK_BOT + 3):
        for x in range(GW):
            dy = y + bob + tilt(x)
            t = (dy - DECK_TOP) / float(DECK_BOT - DECK_TOP)
            if t < -0.05 or t > 1.05:
                continue
            hw = deck_hw(max(0.0, min(1.0, t)))
            u = (x + 0.5 - CXG) / hw
            if abs(u) > 1.0:
                continue
            # rounded ends
            if abs(u) > 0.90:
                k = (abs(u) - 0.90) / 0.10
                if abs(t - 0.5) * 2.0 > math.sqrt(max(0.0, 1.0 - k * k)):
                    continue
            face[(x, y)] = (u, max(0.0, min(1.0, t)))

    for (x, y), (u, t) in face.items():
        au = abs(u)
        if t < 0.42:
            # The lit top lip.  Josh's own glide frames already paint a gold stub over rows
            # 6..9 of this deck, so these rows use the same dark-gold ramp and the stub
            # vanishes into the card instead of showing as a seam across his feet.
            c.p[y][x] = 'D' if t < 0.10 else ('A' if t < 0.28 else 'K')
        elif t > 0.92:
            c.p[y][x] = 'A'                       # gold lip along the near edge
        elif au > 0.90:
            c.p[y][x] = 'A'                       # gold rim at the card's short ends
        elif au > 0.82:
            c.p[y][x] = 'K'
        else:
            # cream face, with the red medallion squashed into a band across the middle
            mu, mv = u / 0.30, (t - 0.70) / 0.26
            if mu * mu + mv * mv <= 1.0:
                if abs(mu) < 0.34 and mv < 0.45:
                    c.p[y][x] = 'x'               # the spade, flattened to a wedge
                else:
                    c.p[y][x] = 'R' if (mu + mv) < -0.35 else 'Q'
            else:
                lit = (-u) * 0.28 + (1.0 - t) * 0.72
                c.p[y][x] = 'n' if lit > 0.40 else ('N' if lit > 0.18 else 'u')

    # ---- card-stock edge under the face ------------------------------------
    wall = ['U', 'i', 'I', 'I']
    for x in range(GW):
        col = [y for y in range(GH) if c.p[y][x] != '.']
        if not col:
            continue
        ymax = max(col)
        for k in range(THICK):
            y = ymax + 1 + k
            if y < GH:
                c.p[y][x] = wall[min(k, len(wall) - 1)]

    outline(c)

    # ---- gold energy bloom under the deck ----------------------------------
    # The silhouette's lower profile is sampled ONCE, before anything is written.  Reading it
    # per-pixel while painting makes each new glow pixel extend the profile, and the bloom
    # cascades down and floods the whole lower half of the frame.
    floor = []
    for x in range(GW):
        col = [y for y in range(GH) if c.p[y][x] != '.']
        floor.append(max(col) if col else None)
    ramp = ['K', 'A', 'D']
    for x in range(GW):
        if floor[x] is None:
            continue
        for d in range(1, 6):
            y = floor[x] + d
            if not c.inb(x, y) or c.p[y][x] != '.':
                continue
            v = (1.0 - (d - 1) / 5.0) * 1.05
            if hashf(x, y, 17 + ph * 7) < 0.42:
                v *= 0.35
            k = int(v * len(ramp))
            if k > 0:
                c.p[y][x] = ramp[min(k - 1, len(ramp) - 1)]

    # ---- trail streaming off the back (he travels RIGHT, so it streams left) -
    # The deck is nearly as wide as the canvas, so there is no room for a trail beside it: it
    # runs off the card's lower-left corner and sags away underneath instead.
    tr = ['A', 'D', 'F', 'Y']
    tail_x, tail_y = 8.0, DECK_BOT + THICK + 1 + bob + tilt(8.0)
    for x in range(0, 22):
        t = 1.0 - x / 21.0                       # 1 at the card, 0 at the tail tip
        half = 0.4 + t * t * 3.4
        base = tail_y + (1.0 - t) * 4.5 + math.sin((1.0 - t) * 3.2 + ph * 2.1) * 1.2
        for dy in range(-int(half) - 1, int(half) + 2):
            y = int(round(base + dy))
            if not c.inb(x, y) or c.p[y][x] != '.':
                continue
            fall = 1.0 - abs(dy) / (half + 0.8)
            if fall <= 0:
                continue
            v = (0.35 + t * 0.95) * fall ** 0.6
            if hashf(x, y, 29 + ph * 5) < 0.30:
                v *= 0.55
            k = int(v * len(tr))
            if k > 0:
                c.p[y][x] = tr[min(k - 1, len(tr) - 1)]
    # a couple of sparks shed off the tail
    for k in range(3):
        a = hashf(k, ph, 13)
        c.set(int(2 + a * 9), int(tail_y + 3 + a * 5 + (k - 1) * 2), 'F' if a > 0.4 else 'D')
    return c


def build():
    return [build_frame(i) for i in range(3)]


DURATIONS = [110, 110, 110]
TAGS = [('ride', 0, 2)]

# where the glider goes, in Josh's 80x80 frame coordinates
JOSH_ANCHOR = (7, 70)          # glider canvas origin inside Josh's frame


# --------------------------------------------------------------------------- shadow
SW, SH = 80, 24
SHADOW_CX, SHADOW_CY = 39.0, 12.0

# per frame: radius x, radius y, solid-core fraction, overall density
SHADOW = [(20.0, 6.2, 1.00, 1.00),
          (16.5, 5.2, 0.55, 0.90),
          (13.0, 4.3, 0.35, 0.70),
          (10.0, 3.4, 0.15, 0.50)]

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def shadow_frame(i):
    """Pure black, alpha 0/255 only - exactly like Bixby's shadow_ground.  Height is expressed
    by an ORDERED (Bayer) dither over a solid core: a random dither at these sizes reads as
    static rather than as a soft shadow."""
    rx, ry, core, dens = SHADOW[i]
    c = Cv(SW, SH)
    for y in range(SH):
        for x in range(SW):
            u = (x + 0.5 - SHADOW_CX) / rx
            v = (y + 0.5 - SHADOW_CY) / ry
            d = math.hypot(u, v)
            if d > 1.0:
                continue
            k = dens if d <= core else dens * (1.0 - (d - core) / (1.0 - core))
            if (BAYER4[y & 3][x & 3] + 0.5) / 16.0 < k:
                c.p[y][x] = '#'
    return c


def build_shadow():
    return [shadow_frame(i) for i in range(4)]


SHADOW_DURATIONS = [100, 100, 100, 100]
SHADOW_TAGS = [('heights', 0, 3)]
