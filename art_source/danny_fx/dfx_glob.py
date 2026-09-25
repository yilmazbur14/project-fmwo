"""danny_worm_glob.png: the glob of worms Danny spits, in flight. 4 frames of 24x24, looping at 0.06 s, one strip.
THE PIVOT IS THE FRAME CENTRE (12, 12): the glob. Round, so it reads the same whichever way it flies: never
rotated, never flipped; the code moves it along its arc.
A ball of dark slime (x 6 D, lit on its upper left, gloss 1) packed with pink worms (1-5) wrapped round it,
three short worm ends poking out of it and wriggling. About 17 texels across (51 px at scale 3).
"""
import math

import dfx_pal as pal
import dfx_worms as wm

W, H = 24, 24
CX, CY = 12.0, 12.0
R = 7.2
FRAME_SIZE = (W, H)
NOTE = '4 frames of 24x24 looping at 0.06 s; pivot = centre (12,12); round, never rotated or flipped'


def frame(f):
    g = pal.blank(W, H)
    ph = f * math.pi / 2
    ball = set()
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            r = R * (1.0 + 0.05 * math.sin(3 * math.atan2(dy, dx) + ph))
            if math.hypot(dx, dy) <= r:
                ball.add((x, y))
    for (x, y) in ball:
        dx, dy = x + 0.5 - CX, y + 0.5 - CY
        d = math.hypot(dx, dy)
        lit = (-dx - dy) / (d + 1e-6)
        k = '6'
        if d > R - 1.3:
            k = 'D' if lit > 0.2 else 'x'
        elif (dx + 1.5) ** 2 + (dy + 1.5) ** 2 > (R * 0.95) ** 2 and lit < -0.2:
            k = 'x'
        g[y][x] = k
    # worms wrapped round the ball: arcs across it, wriggling
    for (a0, a1, rr, p) in ((200, 330, 5.0, 0.0), (20, 150, 4.2, 1.5), (250, 400, 2.4, 3.0)):
        pts = []
        for i in range(25):
            a = math.radians(a0 + (a1 - a0) * i / 24)
            wob = 0.7 * math.sin(3 * a + ph + p)
            pts.append((CX + (rr + wob) * math.cos(a), CY + (rr + wob) * 0.9 * math.sin(a)))
        wm.worm(g, pts, width=2.4, clip=ball, saddle=0.4, glint_every=7)
    # worm ends sticking out and wriggling
    for (ang, L, p) in ((-165, 2.6, 0.0), (-70, 3.2, 2.0), (20, 2.4, 4.0)):
        a = math.radians(ang)
        x0, y0 = CX + (R - 1.5) * math.cos(a), CY + (R - 1.5) * math.sin(a)
        x1, y1 = CX + (R + L) * math.cos(a), CY + (R + L) * math.sin(a)
        pts = wm.wiggle(x0, y0, x1, y1, 0.9, 0.8, ph * 1.5 + p, n=12)
        wm.worm(g, pts, width=2.2, saddle=-1, glint_every=0)
    wm.gloss(g, [(8, 8), (9, 7), (10, 7)])
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
