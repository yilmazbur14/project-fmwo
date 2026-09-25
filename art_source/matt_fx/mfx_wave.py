"""matt_trueshot_wave.png: Matt's Trueshot Barrage wave. 20 frames of 96x96, one strip:
  frames 0-3     heading 0 degrees     (travelling right)
  frames 4-7     heading 22.5
  frames 8-11    heading 45
  frames 12-15   heading 67.5
  frames 16-19   heading 90            (travelling down)
4 frames per heading at 0.05 s, looping. Godot angles (y down). The code covers the other quadrants with
flips only: flip_h for a leftward heading (180 - t), flip_v for an upward one (-t), both for (180 + t).

THE PIVOT IS THE FRAME CENTRE (48, 48), the middle of the crescent, for every heading. Each heading is the
same crescent rotated about that point, so a flip keeps the pivot where it is (the Sprite2D needs no
offset), and TRUESHOT_HIT_POLY, traced on the 0 degree drawing relative to the pivot, rotated by the
actual heading angle (Vector2.rotated), lies on the drawing for every heading and every flip (the crescent
is symmetric about its travel axis, so a flip of the drawn heading equals the rotation to the flipped one).

The design (0 degrees, texels, x forward, relative to the pivot):
  leading edge  a circular arc of radius 60 bulging forward; its apex is 11 texels ahead of the pivot and
                its horns 45 above and below (a 90-texel chord), 20 texels behind the apex
  thickness     16 at the middle, measured radially in from the leading edge, easing to 2-3 at the horns,
                whose last texel comes to a point
  colour        the leading edge #FFFFF0 then #FFF3A8 (one texel each, eroded off the front so they stay
                crisp), then #FFCB3C, #F2A51E, then #C87414 in 3 alpha steps (176, 112, 56) toward the
                inner curve. No dither.
  streaks       faint 1-texel speed streaks along the travel direction: brighter lines crossing the body's
                back half, and fading tails trailing behind the inner curve whose lengths change per frame
  shimmer       hot spots of #FFFFF0 slide along the #FFF3A8 band from frame to frame
"""
import math

import mfx_pal as pal

W = H = 96
PX, PY = 48.0, 48.0            # the pivot, continuous
HEADINGS = (0.0, 22.5, 45.0, 67.5, 90.0)
FRAMES = 4

# The crescent is a lune: inside the leading circle, outside the (larger, further back) trailing circle.
# Both arcs pass through the horn tips, 45 texels either side of the travel axis.
HALF_CHORD = 45.0
APEX = 12.0                     # the leading edge's apex, x relative to the pivot
T_MID = 16.0                    # thickness at the middle
SAG_OUT, SAG_IN = 25.0, 9.0     # sagittas of the leading and trailing arcs over the horn-to-horn chord
TIP_X = APEX - SAG_OUT          # the horn tips' x (-13)
R = (HALF_CHORD ** 2 + SAG_OUT ** 2) / (2 * SAG_OUT)          # 53
OX = APEX - R                                                 # leading circle's centre x
R_IN = (HALF_CHORD ** 2 + SAG_IN ** 2) / (2 * SAG_IN)         # 117
OX_IN = (APEX - T_MID) - R_IN                                 # trailing circle's centre x
PHI_TIP = math.atan2(HALF_CHORD, TIP_X - OX)                  # the tips' angle seen from the leading centre

# Band edges in depth (texels in from the leading edge), for the body behind the eroded edge bands.
# Depth is scaled by the local thickness relative to the middle, so the bands narrow into the horns.
BANDS = [(7.0, 'G'), (10.4, 'O'), (12.3, 'a'), (14.2, 'b'), (99.0, 'c')]


def thickness(phi):
    """Thickness along the ray from the leading circle's centre at angle phi: the gap between the arcs."""
    c, s = math.cos(phi), math.sin(phi)
    # Solve |O + rho (c, s) - O_in| = R_IN for the ray's exit from the trailing circle.
    dx = OX - OX_IN
    b = dx * c
    disc = b * b - (dx * dx - R_IN * R_IN)
    if disc < 0:
        return 0.0
    rho = -b + math.sqrt(disc)
    return max(0.0, R - rho)


def design(X, Y):
    """(inside, depth, local thickness, phi) of a point in 0-degree design coordinates."""
    r = math.hypot(X - OX, Y)
    phi = math.atan2(Y, X - OX)
    inside = r <= R and math.hypot(X - OX_IN, Y) >= R_IN and X >= TIP_X - 1.0
    return inside, R - r, thickness(phi), phi


def to_design(x, y, theta):
    """A texel centre in the frame -> 0-degree design coordinates (rotate by -theta about the pivot)."""
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    px, py = x + 0.5 - PX, y + 0.5 - PY
    return px * c + py * s, -px * s + py * c


def to_frame(X, Y, theta):
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return PX + X * c - Y * s, PY + X * s + Y * c


def inner_x(Y):
    """The trailing curve's x at lateral Y (0 degrees), or None past the horns."""
    if abs(Y) >= HALF_CHORD - 1.0:
        return None
    return OX_IN + math.sqrt(R_IN * R_IN - Y * Y)


def mask(theta):
    m = {}
    for y in range(H):
        for x in range(W):
            X, Y = to_design(x, y, theta)
            inside, d, t, phi = design(X, Y)
            if inside:
                m[(x, y)] = (d, t, phi)
    return m


def front_rings(m, theta):
    """Erosion depth from the LEADING side only: 0 for texels touching the outside in front of the arc."""
    front = {}
    cur = set()
    for (x, y) in m:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in m:
                X, Y = to_design(q[0], q[1], theta)
                if math.hypot(X - OX, Y) > R - 0.25:      # the neighbour is outside in front
                    cur.add((x, y))
                    break
    r = 0
    seen = set()
    while cur and r < 3:
        for p in cur:
            front[p] = r
        seen |= cur
        nxt = set()
        for (x, y) in cur:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in m and q not in seen:
                    nxt.add(q)
        cur = nxt
        r += 1
    return front


def shimmer_hot(phi, f):
    """Hot spots that slide along the #FFF3A8 band: True where this texel flashes #FFFFF0 this frame."""
    a = phi / PHI_TIP                         # -1..1 along the arc
    ph = (a * 5.0 + f * 0.5) % 2.0
    return ph < 0.42


STREAK_Y = [-33.5, -22.5, -14.5, -6.5, 3.5, 10.5, 19.5, 29.5]
# Tail length behind the inner curve per streak and frame (texels); 0 = no tail this frame.
STREAK_TAIL = [
    [2, 0, 3, 1], [5, 2, 0, 4], [0, 6, 3, 7], [7, 3, 8, 0], [3, 8, 0, 6], [6, 0, 5, 2],
    [0, 4, 2, 5], [3, 1, 0, 2],
]


def streak_texels(theta, f, m):
    """Speed streaks: (texel -> key). Inside the body a streak is one step brighter than the band it
    crosses (from the #F2A51E band back); behind the inner curve it trails off in the fade's alphas."""
    out = {}
    for i, Y in enumerate(STREAK_Y):
        xi = inner_x(Y)
        if xi is None:
            continue
        tail = STREAK_TAIL[i][f]
        if tail == 0:
            continue
        start = xi + 4.5 if abs(Y) < 28 else xi + 2.0
        end = xi - tail
        pts = []
        X = start
        while X >= end:
            fx, fy = to_frame(X, Y, theta)
            p = (int(math.floor(fx)), int(math.floor(fy)))
            if not pts or pts[-1][0] != p:
                pts.append((p, X - xi))
            X -= 0.1
        pts = pixel_perfect(pts)
        for p, rel in pts:
            if p in m:
                out[p] = ('in', rel)
            else:
                behind = -rel
                out[p] = ('out', behind / max(1.0, tail))
    return out


def pixel_perfect(run):
    out = list(run)
    i = 1
    while i < len(out) - 1:
        (ax, ay), (bx, by), (cx, cy) = out[i - 1][0], out[i][0], out[i + 1][0]
        if abs(ax - cx) == 1 and abs(ay - cy) == 1 and (ax == bx or ay == by):
            del out[i]
        else:
            i += 1
    return out


BRIGHTER = {'b': 'a', 'c': 'b'}         # a streak lifts the translucent fade one alpha step


def frame(theta, f):
    m = mask(theta)
    fr = front_rings(m, theta)
    g = pal.blank(W, H)
    for (x, y), (d, t, phi) in m.items():
        ring = fr.get((x, y))
        a = abs(phi) / PHI_TIP                  # 0 at the middle, 1 at a horn tip
        if ring == 0:
            k = 'H' if a < 0.86 else 'Y'
        elif ring == 1:
            if a >= 0.9:
                k = 'G'
            else:
                k = 'H' if (a < 0.3 or shimmer_hot(phi, f)) else 'Y'
        elif ring == 2 and a < 0.62:
            k = 'Y'
        else:
            scale = t / T_MID
            k = 'c'
            for edge, key in BANDS:
                if d < max(2.0, edge * scale):
                    k = key
                    break
            if t < 5.0 and k in 'abc':          # the thin horns stay solid gold
                k = 'O'
        g[y][x] = k
    for (x, y), (where, v) in streak_texels(theta, f, m).items():
        if not (0 <= x < W and 0 <= y < H):
            continue
        if where == 'in':
            cur = g[y][x]
            if cur in BRIGHTER:
                g[y][x] = BRIGHTER[cur]
        else:
            g[y][x] = 'b' if v < 0.3 else 'c'
    return pal.rows(g)


def frames():
    out = []
    by = {}
    for theta in (0.0, 22.5, 45.0):
        by[theta] = [frame(theta, f) for f in range(FRAMES)]
    by[67.5] = [pal.transpose(fr) for fr in by[22.5]]
    by[90.0] = [pal.transpose(fr) for fr in by[0.0]]
    for theta in HEADINGS:
        out.extend(by[theta])
    return out


# The in-between headings, shipped as their own sheet (matt_trueshot_wave_mid.png) so the live sheet above
# never changes: 16 frames of 96x96, 11.25 deg f0-3, 33.75 f4-7, 56.25 f8-11, 78.75 f12-15. The same
# crescent rotated about the same pivot (the frame centre); 56.25 and 78.75 are the exact transposes of
# 33.75 and 11.25, as 67.5 and 90 are of 22.5 and 0 in the live sheet.
HEADINGS_MID = (11.25, 33.75, 56.25, 78.75)


def frames_mid():
    by = {}
    for theta in (11.25, 33.75):
        by[theta] = [frame(theta, f) for f in range(FRAMES)]
    by[56.25] = [pal.transpose(fr) for fr in by[33.75]]
    by[78.75] = [pal.transpose(fr) for fr in by[11.25]]
    out = []
    for theta in HEADINGS_MID:
        out.extend(by[theta])
    return out


def body_mask_at(theta):
    """The crescent's body texels (fade included, streak tails not) as drawn for a sheet heading, whichever
    sheet it is on: rendered headings from mask(), transposed ones from the transpose of their partner."""
    if theta in (67.5, 90.0, 56.25, 78.75):
        return {(y, x) for (x, y) in mask(90.0 - theta)}
    return set(mask(theta).keys())


if __name__ == '__main__':
    print('\n'.join(frame(0.0, 0)))
