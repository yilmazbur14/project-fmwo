"""danny_worm_puddle.png: the worm puddle Danny's spat glob leaves on the mat. 4 frames of 100x52, looping at
0.12 s, one strip. It stays until the attack ends; stepping in it roots the player.
THE PIVOT IS THE FRAME CENTRE (50, 26): the puddle's centre on the floor. Never flipped.
A dark glossy stain of slime (his darkest browns: body 6, deep x, a 1-texel wet rim D lit on its upper left,
curved gloss 1/e) splattered round its edge, with pink earthworms wriggling in it (the worms' own ramp 1-5,
each with its saddle band), three arching out of the slime, and two bubbles swelling and popping: a dark,
crawling stain on the green mat that reads as "don't step here".
THE STAIN'S BODY IS THE TRIGGER, texel for texel: every texel whose centre lies inside the ellipse rx 43,
ry 17 texels round the pivot (129x51 px of radius at scale 3), and no other. The splatter drops round it are
kept a texel clear of it, so they read as decoration. (The user's playtest, 2026-09-24, grew it about 1.6x
from rx 27, ry 10.5, with more worms in it.)
"""
import math

import dfx_pal as pal
import dfx_worms as wm

W, H = 100, 52
CX, CY = 50.0, 26.0
RX, RY = 43.0, 17.0
FRAME_SIZE = (W, H)
NOTE = '4 frames of 100x52 looping at 0.12 s; pivot = centre (50,26) on the floor; stain body = the trigger, rx 43 ry 17 texels'
# splatter drops round the stain: (x, y, rx, ry), in the frame
DROPS = [(CX - 46.0, CY + 3.0, 2.2, 1.5), (CX + 46.5, CY - 3.0, 2.0, 1.4), (CX - 30.0, CY + 18.5, 2.1, 1.4),
         (CX + 29.0, CY - 19.0, 2.1, 1.4), (CX + 39.0, CY + 12.0, 1.8, 1.2), (CX - 39.0, CY - 11.5, 1.8, 1.2),
         (CX + 6.0, CY + 20.0, 1.6, 1.1)]

# worms lying in the slime: (x0, y0, x1, y1 relative to the centre, amplitude, waves, phase, width, saddle)
WORMS = [(-34, -4, -16, -9, 1.6, 1.4, 0.0, 2.8, 0.30), (-6, 4, 15, 2, 1.8, 1.3, 1.7, 3.0, 0.65),
         (8, -10, 27, -6, 1.4, 1.1, 3.1, 2.6, 0.35), (-28, 7, -10, 10, 1.3, 1.0, 4.4, 2.5, 0.70),
         (18, 6, 36, 3, 1.5, 1.2, 0.9, 2.7, 0.40), (-13, -12, 3, -13, 1.2, 1.0, 2.6, 2.4, 0.55),
         (-4, 11, 12, 13, 1.3, 1.1, 5.2, 2.5, 0.30), (27, -1, 38, 1, 1.1, 0.9, 3.8, 2.4, 0.60)]
# worms arching out of the slime: (x, y of the base relative to the centre, span, height, phase)
ARCHES = [(-15, -1, 7, 4.5, 0.0), (18, 8, 6, 3.6, 2.1), (-23, 3, 6, 3.8, 4.0)]
# bubbles: (x, y relative to the centre, radius per frame; 0 = the pop)
BUBBLES = [(25.5, -2.0, [1.0, 1.5, 2.0, 0]), (-19.5, 6.5, [2.0, 0, 1.0, 1.5])]


def body_mask():
    """The stain's body: the trigger ellipse, texel for texel."""
    return {(x, y) for y in range(H) for x in range(W)
            if ((x + 0.5 - CX) / RX) ** 2 + ((y + 0.5 - CY) / RY) ** 2 <= 1.0}


def drops_mask():
    m = set()
    for (ox, oy, r, rr) in DROPS:
        for y in range(int(oy) - 3, int(oy) + 4):
            for x in range(int(ox) - 3, int(ox) + 4):
                if ((x + 0.5 - ox) / r) ** 2 + ((y + 0.5 - oy) / rr) ** 2 <= 1.0 and 0 <= x < W and 0 <= y < H:
                    m.add((x, y))
    return m


def gloss_arc(a0, a1, q, n):
    """Texel points along the ellipse at q of its radius, from angle a0 to a1 (degrees; 180 is the left)."""
    out = []
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / max(1, n - 1))
        p = (int(CX + RX * q * math.cos(a)), int(CY + RY * q * math.sin(a)))
        if not out or out[-1] != p:
            out.append(p)
    return out


def frame(f):
    g = pal.blank(W, H)
    ph = f * math.pi / 2
    mask = body_mask() | drops_mask()
    wm.stain(g, mask)
    wm.gloss(g, gloss_arc(197, 222, 0.8, 9))
    wm.gloss(g, gloss_arc(252, 266, 0.82, 6))
    body = {(x, y) for (x, y) in mask if math.hypot((x + 0.5 - CX) / RX, (y + 0.5 - CY) / RY) < 0.86}
    for (x0, y0, x1, y1, amp, waves, p, w, sad) in WORMS:
        pts = wm.wiggle(CX + x0, CY + y0, CX + x1, CY + y1, amp, waves, p + ph)
        wm.worm(g, pts, width=w, clip=body, saddle=sad)
    for (bx, by, span, hgt, p) in ARCHES:
        lift = hgt * (0.75 + 0.25 * math.sin(ph + p))
        # its shadow on the slime, then the arch
        for t in range(int(span) + 1):
            pal.put(g, int(CX + bx - span / 2 + t), int(CY + by + 1), 'x')
        pts = [(CX + bx - span / 2 + span * t, CY + by - lift * math.sin(math.pi * t)) for t in [i / 16 for i in range(17)]]
        wm.worm(g, pts, width=2.4, taper=False, saddle=-1, glint_every=6)
    for (ox, oy, rs) in BUBBLES:
        bx, by = CX + ox, CY + oy
        r = rs[f]
        if r:
            for y in range(int(by) - 3, int(by) + 4):
                for x in range(int(bx) - 3, int(bx) + 4):
                    d = math.hypot(x + 0.5 - bx, y + 0.5 - by)
                    if d <= r:
                        g[y][x] = 'D' if d > r - 0.9 else '6'
            pal.put(g, int(bx - r * 0.5), int(by - r * 0.5), '1')
        else:
            for (x, y) in ((-2, 0), (2, -1), (0, -2), (1, 1)):
                pal.put(g, int(bx) + x, int(by) + y, 'd')
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
