"""Greyson's punches: brawl_hook (the hook's whoosh), brawl_straight (the straight's burst) and
brawl_impact (a punch that lands). White air on his own pale steel greys, trailing off in the 176 and 96
alpha steps; no gold (that is the dodge) and no red (that is the parry), so nothing here reads as a tell.

CLOSE QUARTERS (PLAN_BRAWL.md 4 and 7). The player stands at 2x right in front of him and the camera is
at zoom 1.5, so the hooks come ACROSS and slightly down onto the player's head, and the straight comes
straight AT the viewer. Every pivot below is a world point in the plan's 4.

brawl_hook.png   8 frames of 64x32, one strip.  frame = hook * 4 + step, 0.04 s a step.
  hook 0 the LEFT hook (his left, the cannon gauntlet, from the screen's right; the LEFT arrow's). In
         texels from the pivot: wind-up (+34,-14) -> the head's rest point (0,0) -> 10 texels past,
         rising: (-10,-3).
  hook 1 the RIGHT hook: the same arc mirrored, drawn, not flipped.
  step 0 the swing leaving the wind-up, 1 the fist ON the head's rest point (his strike frame), 2 the
         follow-through past it, thinning, 3 the last wisp.
  THE PIVOT IS THE HEAD'S REST POINT: (22, 19) on the left hook, (42, 19) on the right. It goes on the
  player's head centre at rest, (960,446), whether or not they slipped: a slip is the whoosh going
  through where their head was.
brawl_straight.png   4 frames of 32x32, 0.04 s a step. The gauntlet driven at the viewer: speed lines
  converging on the contact, a white core where it arrives, a ring thrown off it. Step 1 is the strike.
  THE PIVOT IS THE CENTRE (16, 16): the parry contact, (957,416).
brawl_impact.png   5 frames of 48x48 at 0.04 s. A punch that lands: a white star, a ring blown out and
  broken, sparks thinning out in the alpha steps. THE PIVOT IS THE CENTRE (24, 24): the player's head,
  (960,446).
"""
import math

import gb_pal as pal

# ------------------------------------------------------------------- hook
# The arc runs through the plan's three points, in texels from the pivot (the head's rest point):
#   wind-up (+34, -14)  ->  the head (0, 0)  ->  past (-10, -3), rising as it goes
# A parabola through them dips 0.3 texels below the head, 4 texels short of it, and rises either side.
# Its outer (lower) edge is the swing's leading edge, and the brightest.

HW, HH = 64, 32
HOOK_PIVOT = (22, 19)                 # the head's rest point on the LEFT hook; the RIGHT hook's is (42, 19)
_A = -24.2 / 1496.0
_B = 10.0 * _A + 0.3
# per step: (the smear's tail x, the fist's x), in texels from the pivot; the fist travels +34 -> -10
HOOK_STEPS = {0: (34.0, 14.0), 1: (34.0, 0.0), 2: (22.0, -10.0), 3: (6.0, -10.0)}
HOOK_HEAD = {0: 14.0, 1: 0.0, 2: -10.0, 3: None}


def _path(x):
    """the arc: y (down the screen) from the pivot, x texels from it. Solved in screen coordinates:
    _path(34) = -14 (the wind-up, above), _path(0) = 0, _path(-10) = -3 (past, rising)"""
    return _A * x * x + _B * x


def hook_frame(step, mirrored=False):
    g = pal.blank(HW, HH)
    px, py = HOOK_PIVOT
    x_tail, x_front = HOOK_STEPS[step]
    head = HOOK_HEAD[step]
    fade = (1.0, 1.0, 0.72, 0.45)[step]
    n = 360
    for i in range(n + 1):
        t = i / float(n)                               # 0 tail .. 1 front
        x = x_tail + (x_front - x_tail) * t
        y = _path(x)
        # the normal, on the outside of the curve (below it)
        slope = 2 * _A * x + _B
        nx, ny = -slope, 1.0
        ln = math.hypot(nx, ny)
        nx, ny = nx / ln, ny / ln
        thick = (0.5 + 6.0 * math.sin(math.pi * 0.5 * t) ** 1.5) * fade
        lo = -thick * 0.4
        s = lo
        while s <= thick:
            u = (s - lo) / max(0.01, thick - lo)       # 0 inner edge .. 1 outer (leading) edge
            # a value ramp across the smear, white leading edge to mid steel trailing edge: at close
            # quarters it crosses his skin, and white on #FBD6B0 alone has next to no edge
            if step == 3:
                k = 'y' if t > 0.5 else 'z'
            elif step == 2:
                k = ('x' if u > 0.5 else 'z') if t > 0.45 else ('y' if t > 0.2 else 'z')
            elif t > 0.6:
                k = 'W' if u > 0.62 else ('S' if u > 0.3 else 'T')
            elif t > 0.28:
                k = 'S' if u > 0.55 else ('T' if u > 0.2 else 'z')
            else:
                k = 'x' if u > 0.5 else 'z'
            pal.put(g, int(px + x + nx * s), int(py + y + ny * s), k)
            s += 0.5
        # speed lines under the smear, broken
        if step in (1, 2) and 0.2 < t < 0.85 and int(t * 30) % 3 != 0:
            for off, k in ((thick + 2.5, 'x'), (thick + 4.5, 'y')):
                pal.put(g, int(px + x + nx * off), int(py + y + ny * off), k)
    if head is not None:
        hx, hy = px + head, py + _path(head)
        r = (3.0, 4.5, 3.0)[step]
        for yy in range(HH):
            for xx in range(HW):
                d = math.hypot(xx + 0.5 - hx, (yy + 0.5 - hy) * 1.15)
                if d <= r:
                    g[yy][xx] = 'W' if d <= r - 1.3 else 'S'
    if mirrored:
        g = [row[::-1] for row in g]
    return pal.rows(g)


def hook_frames():
    return [hook_frame(s, False) for s in range(4)] + [hook_frame(s, True) for s in range(4)]


def hook_pivot(mirrored=False):
    return (HW - HOOK_PIVOT[0], HOOK_PIVOT[1]) if mirrored else HOOK_PIVOT


# --------------------------------------------------------------- straight
# His wind-up (984,428) is only 9 texels right and 4 down of the parry contact (957,416): the gauntlet
# comes at the viewer, so what reads is the burst ON the contact.

SW, SH = 32, 32
STRAIGHT_PIVOT = (16, 16)
_LINES = [(12, 1.0), (57, 0.8), (101, 1.0), (148, 0.75), (193, 1.0), (239, 0.85), (284, 1.0), (330, 0.8)]


def straight_frame(step):
    g = pal.blank(SW, SH)
    cx, cy = STRAIGHT_PIVOT
    # the converging lines: step 0 far out, step 1 closing on the core, step 2 spent, then gone
    rin = (7.5, 5.5, 9.0, None)[step]
    rout = (15.0, 13.0, 14.0, None)[step]
    if rin is not None:
        for (a, frac) in _LINES:
            ang = math.radians(a)
            r1 = rin + (1.0 - frac) * 2.0
            r2 = min(15.0, rout - (1.0 - frac) * 3.0)
            r = r1
            while r <= r2:
                t = (r - r1) / max(0.01, r2 - r1)          # 0 inner end .. 1 outer end
                if step == 2:
                    k = 'y'
                else:
                    k = 'W' if t < 0.3 else ('S' if t < 0.65 else 'x')
                pal.put(g, int(cx + math.cos(ang) * r), int(cy + math.sin(ang) * r), k)
                r += 0.5
    # the ring thrown off the contact, breaking as it grows
    ring = (None, 8.0, 11.0, 13.5)[step]
    if ring is not None:
        rk = ('W', 'x', 'y')[step - 1]
        w = (2.0, 1.5, 1.0)[step - 1]
        for yy in range(SH):
            for xx in range(SW):
                d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                if ring - w < d <= ring:
                    if step >= 2:
                        a = math.degrees(math.atan2(yy + 0.5 - cy, xx + 0.5 - cx)) % 360
                        if any(abs((a - c + 180) % 360 - 180) < 10 + step * 4 for c in (45, 135, 225, 315)):
                            continue
                    g[yy][xx] = rk
    # the core: where the gauntlet arrives
    core = (3.0, 4.5, 2.5, 0.0)[step]
    for yy in range(SH):
        for xx in range(SW):
            d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
            if d <= core:
                g[yy][xx] = 'W' if (d <= core - 1.2 or step == 0) else 'S'
    return pal.rows(g)


def straight_frames():
    return [straight_frame(s) for s in range(4)]


# ----------------------------------------------------------------- impact

IW, IH = 48, 48
IC = 24.0


def impact_frame(f):
    g = pal.blank(IW, IH)
    star = (17.0, 13.5, 8.0, 0.0, 0.0)[f]
    ring = (0.0, 10.0, 14.0, 17.0, 18.5)[f]
    ring_k = (None, 'W', 'S', 'x', 'y')[f]
    # a jagged burst behind the star on the first two steps: the weight of it
    if f < 2:
        jag = []
        for i in range(24):
            a = math.radians(i * 15 - 90 + 7)
            r = (15.0 if i % 2 == 0 else 10.0) * (1.0 if f == 0 else 1.2)
            jag.append((IC + math.cos(a) * r, IC + math.sin(a) * r))
        burst = pal.blank(IW, IH)
        pal.poly_fill(burst, jag, 'S' if f == 0 else 'x')
        for y in range(IH):
            for x in range(IW):
                if burst[y][x] != '.':
                    g[y][x] = burst[y][x]
    # the ring, broken from step 2
    if ring > 0:
        for y in range(IH):
            for x in range(IW):
                d = math.hypot(x + 0.5 - IC, y + 0.5 - IC)
                w = 2.0 if f < 3 else 1.0
                if ring - w < d <= ring:
                    a = math.degrees(math.atan2(y + 0.5 - IC, x + 0.5 - IC)) % 360
                    if f >= 2 and any(abs((a - c + 180) % 360 - 180) < (10 + f * 6) for c in (20, 110, 200, 290)):
                        continue
                    g[y][x] = ring_k
    # the star: four long points and four short, white with a steel edge
    if star > 0:
        pts = []
        for i in range(16):
            a = math.radians(i * 22.5 - 90)
            r = star if i % 4 == 0 else (star * 0.55 if i % 2 == 0 else star * 0.3)
            pts.append((IC + math.cos(a) * r, IC + math.sin(a) * r))
        body = pal.blank(IW, IH)
        pal.poly_fill(body, pts, 'W')
        for y in range(IH):
            for x in range(IW):
                if body[y][x] == '.':
                    continue
                edge = any(not (0 <= x + dx < IW and 0 <= y + dy < IH) or body[y + dy][x + dx] == '.'
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                g[y][x] = 'S' if edge else 'W'
    # sparks flying out along the diagonals
    for i in range(8):
        a = math.radians(i * 45 + 22.5 + f * 4)
        r0 = (7, 11, 15, 17, 18)[f]
        ln = (5, 6, 4, 3, 2)[f]
        k = ('W', 'W', 'S', 'x', 'y')[f]
        for j in range(ln):
            x = int(IC + math.cos(a) * (r0 + j))
            y = int(IC + math.sin(a) * (r0 + j))
            pal.put(g, x, y, k)
    return pal.rows(g)


def impact_frames():
    return [impact_frame(f) for f in range(5)]
