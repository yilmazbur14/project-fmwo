"""messatsu_beam / messatsu_flare / messatsu_head / messatsu_pulse - the beam,
the eruption it comes out of at his palms, its leading edge, and the surges
that carry hits 2 to 6.

WHY THESE FOUR ARE PAINTED, NOT ADDITIVE.  They are only ever seen with the
lights ON, over the green mat.  Violet is green's complement, so violet light
added to that mat mixes to grey-white - the placeholder beam's grey band is
exactly that - and no choice of violet fixes it: the mat's green channel
(156-190) is already most of the way to white and additive light cannot take
it back down.  Measured on the mat, an additive void-ramp beam lands between
#d6ccdb and white, and a demon_parry_break burst on it moves the pixels it
lands on by as little as nothing.  Painted, the same ramp stays Carter's violet
and the burst - which IS additive - reads gold-white on every part of it
(previews.py burst_check).  So all four are normal-blend, every pixel alpha 255.
The surge was already painted in the placeholder, for the same reason.

ONE CROSS-SECTION, THREE SHAPES.  The beam, the flare and the head are all the
same function of (flow column p, distance from the centre line d).  The beam
evaluates it straight; the flare fans it out of his palms (d scaled by how open
the cone is at that column) and runs it hotter toward the root; the head
squeezes it into a nose and runs it hotter toward the tip.  So the band's edge,
its zones and its streaks carry on unbroken from one piece to the next, and the
flare's full-width end is literally the beam - it can dither into the beam
without a seam.

THE BAND.  136 texels across is MESSATSU_DRAW_WIDTH at 3x:
  rows   0..7    glow: light and not damage, thinning out
  rows   8..127  the 120-texel hurting band, MESSATSU_HIT_WIDTH at 3x
  rows 128..135  glow
The band's edge is its brightest line (e2a2f4 over b45ae0), so the edge of
what hurts is the crispest thing on the beam.  Inside it: a dark edge zone,
the body, then the core.

THE CORE is about a third of the band (~42 texels, 126 px at 3x) but only its
middle 4-6 rows are white.  The rest is e2a2f4 and b45ae0, which an additive
parry break still visibly brightens.  The placeholder's white core was 136 px
of pure white and swallowed the burst whole.

TILING AND FLOW.  Everything that flows is a function of p = (x - 8*frame) mod
32, so every frame repeats every 32 texels along x and the four frames are one
pattern stepped 8 texels down the beam: at 0.05 s a frame that is 480 px/s of
flow away from his palms, and the loop closes on itself.  Only the crackle off
the rim is not a function of p - it flickers in place, which is what crackle
does.  The flare and the head share the same p (measured from his palms), so a
beam whose texture starts at his palms flows straight on out of the flare.
"""
import math
import random
from mpal import (Cv, ell, ray, bayer01, sheet, sn, W, P, Q, R, S, T, GL)

BH = 136
CY = 68.0                   # the beam's centre line, between rows 67 and 68
FLOW = 8                    # texels per frame, down the beam


def tongue(u):
    """-1..1 over one period: a slow rise then a fast fall, so each crest leans
    forward (+x) the way a flame licks in the direction it is going"""
    u %= 1.0
    k = 0.72
    if u < k:
        t = u / k
        return -1.0 + 2.0 * t * t * (3.0 - 2.0 * t)
    return 1.0 - 2.0 * (u - k) / (1.0 - k)


# per side (top, bottom) phases, so the two edges never undulate as mirror
# images of each other
_PH = [
    dict(w=0.40, p=0.05, p3=1.1, q=0.55, q2=0.20, r=0.30, r2=4.0),
    dict(w=0.85, p=0.60, p3=0.2, q=0.10, q2=0.70, r=0.80, r2=1.3),
]


def bounds(p, side, heat=0.0):
    """zone edges as distances from the centre line at flow column p.
    `heat` pushes them all outward: the flare's root and the head's tip run
    hotter than the beam."""
    h = _PH[side]
    u = p / 32.0
    bw = 1.6 + 1.3 * max(0.0, math.sin(2 * math.pi * (u + h['w']))) ** 2 + heat * 0.9
    bp = 8.2 + 2.0 * tongue(u + h['p']) + 0.6 * sn(3, p, h['p3']) + heat * 1.6
    bq = 20.5 + 3.0 * tongue(u + h['q']) + 1.1 * tongue(2 * u + h['q2']) + heat * 2.0
    br = 47.0 + 3.0 * tongue(u + h['r']) + 1.2 * sn(2, p, h['r2']) + heat * 1.2
    return bw, bp, bq, br


def _streaks():
    """speed lines, per side: (d, p0, length, zone, thick).  Longer and denser
    near the core, where the energy is fastest."""
    out = []
    for side in (0, 1):
        rnd = random.Random(1709 + side * 31)
        lst = []
        for zone, (d0, d1), n, (l0, l1) in (('P', (3, 7), 3, (3, 6)),
                                           ('Q', (10, 19), 5, (5, 11)),
                                           ('R', (24, 44), 9, (7, 17)),
                                           ('S', (50, 55), 3, (5, 9))):
            used = set()
            for i in range(n):
                for _ in range(12):
                    d = rnd.randint(d0, d1)
                    if d not in used and d - 1 not in used and d + 1 not in used:
                        break
                used.add(d)
                lst.append((d + 0.5, rnd.randrange(32), rnd.randint(l0, l1), zone,
                            zone == 'R' and i % 3 == 1))
        out.append(lst)
    return out


STREAKS = _streaks()
# body colour, head colour, per zone
_SC = {'P': (W, W), 'Q': (P, W), 'R': (Q, P), 'S': (R, Q)}
_ZC = {'W': W, 'P': P, 'Q': Q, 'R': R, 'S': S}


def zone_of(d, bw, bp, bq, br):
    if d < bw:
        return 'W'
    if d < bp:
        return 'P'
    if d < bq:
        return 'Q'
    if d < br:
        return 'R'
    return 'S'


def section(p, y, side, d, heat=0.0):
    """THE cross-section: the colour at flow column p, distance d from the
    centre line (0..68), or None where nothing is drawn"""
    if d > 68.0:
        return None
    if d > 60.0:
        return _glow(p, y, d)
    if d > 59.0:
        return P                       # the band's edge: its brightest line
    if d > 58.0:
        return Q
    bw, bp, bq, br = bounds(p, side, heat)
    z = zone_of(d, bw, bp, bq, br)
    c = _ZC[z]
    # the body/edge-zone boundary is the one soft step: a 2-row ordered dither
    if abs(d - br) < 1.0:
        c = R if (br - d) / 2.0 + 0.5 > bayer01(p, y) else S
        z = 'R' if c == R else 'S'
    # the edge zone's deepest shade, in flecks against the rim, so the rim has
    # something dark to stand off
    if z == 'S' and d > 56.0 and bayer01(p + 3, y) < 0.5:
        c = T
    # speed lines, which only ever run inside their own zone
    for (dr, p0, ln, zn, thick) in STREAKS[side]:
        if zn != z or not (abs(d - dr) < 0.01 or (thick and abs(d - dr - 1.0) < 0.01)):
            continue
        rel = (p - p0) % 32
        if rel >= ln:
            continue
        body, head = _SC[zn]
        if rel < 2 and rel % 2 == 0 and ln > 5:
            continue                   # a ragged tail
        c = head if rel >= ln - 2 else body
    return c


def _glow(p, y, d):
    """outside the band: light, not damage.  A dithered fringe against the rim
    and a few motes flowing further out"""
    if d < 61.0:
        return R if bayer01(p, y) < 0.5 else None
    if d < 62.0:
        return R if bayer01(p, y) < 0.22 else None
    h = (p * 7 + int(y) * 13) % 29
    if h == 0:
        return Q
    if h == 11 and d < 65.0:
        return R
    return None


def crackle(cv, f, x_lo, x_hi, top_row, bot_row, seed, wrap=None, reach=None):
    """lightning off the rim: 1-texel jagged spikes, flickering per frame.
    `wrap` makes them tile (the beam); `reach` is the room there is"""
    rnd = random.Random(seed * 97 + f * 13)
    for side in (0, 1):
        for i in range(3):
            x = rnd.randint(x_lo, x_hi)
            ln = rnd.randint(2, 6 if reach is None else reach)
            kink = rnd.choice((-1, 1))
            for j in range(ln):
                xx = x + (kink if j >= ln // 2 else 0)
                if wrap:
                    xx %= wrap
                yy = (top_row - 1 - j) if side == 0 else (bot_row + 1 + j)
                if 0 <= yy < cv.h and 0 <= xx < cv.w:
                    cv.set(xx, yy, P if j == ln - 1 else Q)


# ------------------------------------------------------------------- beam

BW = 32
BAND_TOP, BAND_BOT = 8, 127         # inclusive rows of the hurting band


def beam_frame(f):
    cv = Cv(BW, BH)
    for y in range(BH):
        dc = (y + 0.5) - CY
        d, side = abs(dc), (0 if dc < 0 else 1)
        for x in range(BW):
            c = section((x - FLOW * f) % 32, y, side, d)
            if c is not None:
                cv.set(x, y, c)
    crackle(cv, f, 0, 31, BAND_TOP, BAND_BOT, seed=1, wrap=32)
    return cv


def beam_sheet(path):
    return sheet([beam_frame(f) for f in range(4)], path)


# ------------------------------------------------------------------ flare

FW, FH = 64, 144
FCY = 72.0
FLARE_PIVOT = (6, 72)               # the texel that goes on his palms
FLARE_OPEN = 32                     # texels past the palms where it is full width
FLARE_FADE = (46, 63)               # columns over which it dithers into the beam
# The beam body starts BEAM_START texels past his palms, under the flare's
# full-width stretch (columns 38..45), so its flat start is always covered.
BEAM_START = FLARE_OPEN


def flare_half(x, f):
    """half-height of the burst at column x: a little over the ball's size at
    his palms, opening to the band's full drawn width FLARE_OPEN texels on.
    Ease-out, so it meets the beam's edge tangent; its steepest stretch is at
    the root, which his fist and forearm sit over."""
    t = x - FLARE_PIVOT[0]
    if t < 0:
        return 0.0
    k = min(1.0, t / float(FLARE_OPEN))
    root = 18.0 + (1.0 if f % 2 else 0.0)
    return root + (68.0 - root) * (1.0 - (1.0 - k) ** 2)


def flare_solid(t, de):
    """how much of the burst is there at `t` texels past his palms and fanned
    distance de: solid along the axis, but its flanks only fill in as it opens.
    Without this the flank of a 408 px beam opening out of a 100 px fist is a
    wall - rotated to 22.5 degrees it stands straight up under his hand."""
    kk = min(1.0, max(0.0, t) / float(FLARE_OPEN))
    return 0.35 + 1.4 * kk - 0.75 * (de / 68.0)


def flare_frame(f):
    """the beam erupting out of his palms.  It is the beam itself, fanned: at
    each column the cross-section is squeezed into the cone's height, and it
    runs hotter toward the root.  Past FLARE_OPEN it is exactly the beam, and it
    dithers away into the beam body that starts underneath it."""
    cv = Cv(FW, FH)
    px0 = FLARE_PIVOT[0]
    for y in range(FH):
        dc = (y + 0.5) - FCY
        d, side = abs(dc), (0 if dc < 0 else 1)
        for x in range(FW):
            h = flare_half(x, f)
            if h <= 0.0:
                continue
            de = d * 68.0 / h                 # fanned distance
            if de > 68.0:
                continue
            if x >= FLARE_FADE[0]:
                k = (FLARE_FADE[1] + 1 - x) / float(FLARE_FADE[1] + 1 - FLARE_FADE[0])
                if bayer01(x, y) >= k:
                    continue
            t = x - px0
            sol = flare_solid(t, de)
            if sol < 1.0 and bayer01(x + 2, y) >= sol:
                continue
            heat = 5.5 * max(0.0, 1.0 - t / 20.0) ** 1.5
            c = section((t - FLOW * f) % 32, y, side, de, heat)
            if c is not None:
                cv.set(x, y, c)
    ox = px0 + 3.0
    # a pressure wave rolling out of the palms, one ring a loop, over the
    # cone but under the root
    wave = (15.0, 22.0, 29.0, 36.0)[f]
    for y in range(FH):
        dy = (y + 0.5) - FCY
        for x in range(px0, FW):
            dx = (x + 0.5) - ox
            r = math.hypot(dx, dy * 0.62)
            if abs(r - wave) < 0.75 and abs(math.degrees(math.atan2(dy, dx))) < 70:
                h = flare_half(x, f)
                if abs(dy) * 68.0 / max(h, 1e-6) <= 58.0:
                    cv.set(x, y, P if f < 3 else Q)
    # the eruption at the root: where the ball was, white-hot, bursting
    rr = (13.0, 14.5, 12.5, 14.0)[f]
    cv.paint(ell(FW, FH, ox, FCY, rr * 0.95, rr * 1.12), Q)
    cv.paint(ell(FW, FH, ox + 0.5, FCY, rr * 0.74, rr * 0.88), P)
    cv.paint(ell(FW, FH, ox + 1.0, FCY, rr * 0.48, rr * 0.58), W)
    # light thrown out of it, down the horn
    for i, a in enumerate((-64, -44, -24, -8, 8, 24, 44, 64)):
        aa = a + (5 if (i + f) % 2 else -5)
        ln = rr + 9 + ((i * 5 + f * 3) % 10) - abs(a) * 0.07
        m = ray(FW, FH, ox, FCY, aa, rr * 0.6, ln, 1.8, 0.4)
        cv.paint(m, P)
        cv.paint(m.erode(1), W)
    # a corona of crackle off the horn's rim, so it bursts rather than bulges
    rnd = random.Random(77 + f * 5)
    for i in range(10):
        x = rnd.randint(px0 + 2, FLARE_FADE[0] - 2)
        h = flare_half(x, f)
        side = i % 2
        ln = rnd.randint(2, 5)
        kink = rnd.choice((-1, 1))
        edge = FCY - h * 60.0 / 68.0 if side == 0 else FCY + h * 60.0 / 68.0
        for j in range(ln):
            xx = x + (kink if j >= ln // 2 else 0)
            yy = int(edge) - 1 - j if side == 0 else int(edge) + 1 + j
            if 0 <= xx < FW and 0 <= yy < FH:
                cv.set(xx, yy, P if j == ln - 1 else Q)
    return cv


def flare_sheet(path):
    return sheet([flare_frame(f) for f in range(4)], path)


# ------------------------------------------------------------------- head

HW, HH = 24, 144
HCY = 72.0
HEAD_PIVOT = (5, 72)                # column 5 goes on the beam's reach
NOSE = 17.0                         # texels the nose runs past the reach


def head_half(rel, f):
    """half-height of the head at `rel` texels past the reach"""
    n = NOSE + (0.0, 1.0, -0.5)[f]
    if rel <= 0:
        return 68.0
    if rel >= n:
        return 0.0
    return 68.0 * math.sqrt(1.0 - (rel / n) ** 2)


def head_frame(f):
    """the front of the beam crossing to the player: the same cross-section
    squeezed into a rounded nose, hotter toward its tip, fading in over the
    beam's own end behind it"""
    cv = Cv(HW, HH)
    px0 = HEAD_PIVOT[0]
    front = {}
    for y in range(HH):
        dc = (y + 0.5) - HCY
        d, side = abs(dc), (0 if dc < 0 else 1)
        for x in range(HW):
            rel = x + 0.5 - px0
            h = head_half(rel, f)
            if h <= 0.0:
                continue
            de = d * 68.0 / h
            if de > 68.0:
                continue
            if de <= 58.0 and rel > 0:
                front[y] = x
            if x < 4 and bayer01(x, y) > (x + 1) / 5.0:
                continue                      # fade in over the beam's end
            heat = max(0.0, min(6.0, 1.5 + rel * 0.42))
            c = section((x - px0 - FLOW * f) % 32, y, side, de, heat)
            if c is not None:
                cv.set(x, y, c)
    # the shock front: the nose's own outline, white where the core meets it
    for y, x in front.items():
        d = abs((y + 0.5) - HCY)
        cv.set(x, y, W if d < 34.0 else P)
    # sparks thrown forward off the front
    rnd = random.Random(40 + f)
    for i in range(9):
        yy = rnd.randint(10, HH - 11)
        d = abs(yy + 0.5 - HCY)
        rel = NOSE * math.sqrt(max(0.0, 1.0 - (d / 68.0) ** 2))
        x0 = int(px0 + rel) + 1 + rnd.randint(0, 2)
        for j in range(rnd.randint(1, 3)):
            if 0 <= x0 + j < HW:
                cv.set(x0 + j, yy, P if j == 0 else Q)
    return cv


def head_sheet(path):
    return sheet([head_frame(f) for f in range(3)], path)


# ------------------------------------------------------------------ pulse

UW, UH = 20, 136
PULSE_PIVOT = (10, 68)
PK = GL[1]            # ffd2d8
PR = GL[2]            # ff5a62  parry red, the badge's family
PD = GL[3]            # e0203c
PT = GL[4]            # 90102a  the wake's cooled tail only


def pulse_frame(f):
    """a surge: a white-hot crescent across the whole beam, bulging forward, in
    a parry-red rim - the only red anywhere in the beam - with red speed lines
    trailing off the back of it.  Painted, like the placeholder: light would
    wash the red out over a beam this bright."""
    cv = Cv(UW, UH)
    half0 = 5.5
    for y in range(UH):
        d = abs((y + 0.5) - CY)
        if d > 66.5:
            continue
        k = max(0.0, 1.0 - (d / 66.5) ** 2)
        c = 8.5 + 4.5 * k + (0.5 if f == 1 else 0.0)       # the middle leads
        half = half0 if d < 60.0 else half0 * math.sqrt(max(0.0, 1.0 - ((d - 60.0) / 6.6) ** 2))
        for x in range(UW):
            u = (x + 0.5) - c
            a = abs(u)
            if a > half:
                continue
            e = half - a
            if e < 1.0:
                col = PD if u < 0 else PR     # the trailing edge deeper
            elif e < 2.4:
                col = PR
            elif e < 3.2:
                col = PK
            else:
                col = W
            if col == W and bayer01(x + f * 3, y + f * 5) < 0.08:
                col = PK
            cv.set(x, y, col)
    # the wake: red speed lines off the back of it, flickering
    rnd = random.Random(300 + f)
    for i in range(14):
        yy = rnd.randint(4, UH - 5)
        d = abs(yy + 0.5 - CY)
        k = max(0.0, 1.0 - (d / 66.5) ** 2)
        back = int(8.5 + 4.5 * k - half0) - 1
        ln = rnd.randint(2, 6)
        for j in range(ln):
            x = back - j - rnd.randint(0, 1) * (j > 1)
            if 0 <= x < UW:
                # hot off the surge, cooling to a deep red at the tail
                cv.set(x, yy, PR if j < ln - 2 else (PD if j == ln - 2 else PT))
    return cv


def pulse_sheet(path):
    return sheet([pulse_frame(f) for f in range(3)], path)
