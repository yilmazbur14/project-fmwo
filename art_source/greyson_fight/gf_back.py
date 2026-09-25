"""Greyson from BEHIND, for the rear poses (the rear V, the three-quarter back twist). Drawn on
the approved rig's grid (112x112, feet on row 111, column 56 the axis) with its tools and its
light (upper left): the silhouettes match the approved front (the same torso, legs and mane
outlines), and only what faces the viewer changes.

  back_head()      the mane from behind: the whole head a sheet of hair from the crown down the
                   back, over the traps, splitting into pointed locks. Its outline is the approved
                   mane's; the face's place is hair.
  back_torso(f)    traps, the upper back round the shoulder blades, the lats flaring into the V
                   (more with f), the spine's groove, the erectors either side of it, the
                   obliques low at the sides.
  back_trunks()    the purple trunks over the glutes: two rounded halves, a centre seam.
  back_leg(side)   hamstrings, the crease behind the knee, the calf's diamond (the two heads of
                   the gastrocnemius), the heel's tendon into the boot.
  back_boot(side)  the approved boot's outline, seen from the heel: no laces, a heel counter.

Muscle lines are dark skin tones, black only where a limb crosses the body (the house rule).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
from gr_muscle import Bump, Form, Layer  # noqa: E402

K, gr_fig, gr_face = B.K, B.gr_fig, B.gr_face
poly, sym, mpts, fill = K.poly, K.sym, K.mpts, K.fill
CUTS = gr_fig.CUTS


def both(bumps):
    return bumps + [b.mirrored() for b in bumps]


def side_bumps(bumps, side):
    return [b.mirrored() for b in bumps] if side else bumps


# ------------------------------------------------------------------------------------ head

def _outer_edge():
    """The approved mane's outer keyline column on the left, per row (from gr_face.HAIR_L)."""
    edge = {}
    for r, row in enumerate(gr_face.HAIR_L):
        for c, ch in enumerate(row):
            if ch != '.':
                edge[gr_face.Y0 + r] = gr_face.X0 + c
                break
    return edge


# The locks the sheet splits into at the bottom (left half; mirrored): (x0, x1, tip row, the row
# its cut starts). Irregular on purpose: widths, cut starts and tips all differ, the outer lock
# longest like the front's. The cuts are black, like the approved front locks'.
LOCKS = [(40, 43, 59, 46), (45, 48, 55, 48), (50, 52, 57, 45), (54, 56, 53, 49)]


def back_head():
    """The mane from behind. Every pixel inside the approved outline is hair: a dome lit from
    the upper left with a ring of highlight, strands falling from the crown, and below the
    shoulders the sheet splitting into locks with black cuts, the outer lock longest like the
    front's."""
    edge = _outer_edge()
    left = {}
    for y in range(26, 61):
        if y not in edge:
            continue
        x_out = edge[y]
        if y >= 46:
            x_out = max(x_out, 38 + min(4, (y - 44) // 2))
        for x in range(x_out, 57):
            left[(x, y)] = 'k' if (x == x_out or y == 26) else 'b'
    # the bottom: locks, each tapering to its tip; cuts between them
    first_cut = min(c for (_, _, _, c) in LOCKS)
    for (x, y) in list(left):
        if y < first_cut or left[(x, y)] == 'k':
            continue
        inside = False
        for (a0, a1, tip, cut) in LOCKS:
            taper = max(0, y - (tip - 4)) * 0.6
            lo = a0 - (1 if a0 == LOCKS[0][0] else 0)
            if lo + taper <= x <= a1 + 1 - taper * 0.6 and y <= tip:
                inside = True
        if not inside and y >= min(c for (_, _, _, c) in LOCKS) + 3:
            left[(x, y)] = None
    left = {p: k for p, k in left.items() if k is not None}
    # tones: the dome's light, strands, the ring
    for (x, y), k in list(left.items()):
        if k == 'k':
            continue
        u, v = (x - 56) / 18.0, (y - 44) / 22.0
        lit = -(u * 0.62 + v * 0.55) + 0.28
        tone = 'a' if lit > 0.62 else 'b' if lit > 0.22 else 'c' if lit > -0.18 else 'd'
        # strands: grooves every third column, bending outward over the dome
        bend = int(round(max(0, 36 - y) * 0.18 * (56 - x) / 9.0))
        if (x + bend) % 3 == 0 and y > 28:
            tone = K.DARKER.get(tone, tone)
        # the ring of highlight across the back of the head
        ring = abs((x - 56) ** 2 / 180.0 + (y - 22) ** 2 / 110.0 - 1.0)
        if ring < 0.12 and x < 54 and tone in 'bc':
            tone = K.LIGHTER[tone]
        left[(x, y)] = tone
    # keyline every hair pixel that touches the outside (the tips, the lock edges)
    for (x, y), k in list(left.items()):
        if k == 'k':
            continue
        for q in ((x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)):
            if q not in left and q[0] <= 56:
                left[q] = 'k'
    # the cuts between locks, and each tip darkened
    for (a0, a1, tip, cut) in LOCKS:
        for y in range(cut, tip + 1):
            if (a1 + 1, y) in left and a1 + 1 <= 56:
                left[(a1 + 1, y)] = 'k'
        for x in range(a0, a1 + 1):
            if (x, tip) in left and left[(x, tip)] != 'k':
                left[(x, tip)] = K.DARKER[left[(x, tip)]]
    out = {}
    for (x, y), k in left.items():
        out[(x, y)] = k
        if x != 56:
            out[(112 - x, y)] = RELIGHT.get(k, k)
    return out


RELIGHT = gr_face.RELIGHT


# ------------------------------------------------------------------------------------ torso

def back_torso(f=2.0):
    """The trunk from behind, on the approved torso's outline with the lats flared by f."""
    half = [(56, 41.0), (49.6, 41.2), (45.6, 43.2), (41.0, 45.6), (36.4, 48.4), (32.6, 51.2),
            (31.6, 53.6), (33.2, 56.0), (32.4 - f, 61.2), (32.6 - f, 64.6), (34.6 - f * 0.5, 68.0),
            (38.6, 71.2), (43.4, 74.0), (45.6, 75.6), (46.0, 77.5), (56, 77.5)]
    pix = poly(sym(half))
    bumps = both([
        Bump('trap', (45.0, 50.0), 10.5, 5.2, ang=24, amp=1.5, cast=2, depth=2),
        Bump('trap_lo', (51.2, 58.4), 6.2, 3.2, ang=64, amp=1.1, cast=2, depth=2),
        Bump('infra', (41.6, 56.8), 5.6, 4.2, ang=-18, amp=1.3, cast=2, depth=3),
        Bump('teres', (37.0, 60.6), 4.0, 2.6, ang=40, amp=1.0, cast=2, depth=3),
        Bump('lat', (39.0 - f * 0.4, 65.0), 11.4, 5.8 + f * 0.3, ang=64, amp=1.6, cast=2, depth=1,
             taper=-0.25),
        Bump('erector', (52.6, 69.4), 7.4, 2.6, ang=90, amp=1.2, cast='6', depth=4),
        Bump('obl', (44.6, 72.4), 4.4, 3.0, ang=70, amp=0.9, cast=2, depth=2),
    ])
    form = Form(ellipsoid=(55, 60, 25, 24))
    lay = Layer(pix, form, bumps, floor=0.25, strength=1.0)
    part = lay.shade_owned(cuts=CUTS, floor_cast=1)[0]
    # the spine's groove between the erectors, and the hair's shadow across the top of the back
    for y in range(58, 77):
        if (56, y) in part:
            part[(56, y)] = K.DARKER[K.DARKER[part[(56, y)]]]
    for (x, y) in list(part):
        if 40 <= x <= 72 and y <= 58:
            part[(x, y)] = K.DARKER[part[(x, y)]]
    return part


# ------------------------------------------------------------------------------------ trunks

def back_trunks():
    """The trunks over the glutes: the approved trunks' outline carried a little lower at the
    back, two rounded halves lit from the upper left, a seam down the middle."""
    pts = sym([(56, 74.2), (46.0, 74.2), (45.0, 77.0), (44.2, 80.4), (45.4, 83.0), (49.6, 85.0),
               (54.0, 85.6), (56, 85.4)])
    part = fill(poly(pts), 'C')
    for side in (0, 1):
        c = (50.2, 79.6) if not side else (61.8, 79.6)
        half = {p: 'C' for p in part if (p[0] < 56 if not side else p[0] > 56)}
        K.ellipsoid(half, c[0] - 1.2, c[1] - 1.5, 7.5, 7.0, 'ABCDE', (0.86, 0.58, 0.20, -0.25))
        part.update(half)
    for y in range(77, 86):
        if (56, y) in part:
            part[(56, y)] = 'k'
    return part


def back_waistband():
    pts = sym([(56, 73.8), (45.8, 73.8), (45.3, 75.6), (56, 75.6)])
    part = fill(poly(pts), 'B')
    K.ellipsoid(part, 50, 72, 16, 6, 'ABCDE', (0.8, 0.45, 0.0, -0.4))
    return part


# ------------------------------------------------------------------------------------ legs

BACK_LEG_BUMPS = [
    Bump('ham_out', (42.4, 88.4), 8.6, 4.6, ang=95, amp=1.6, cast=2, depth=2),
    Bump('ham_in', (49.6, 88.0), 8.4, 4.2, ang=92, amp=1.5, cast=2, depth=2),
    Bump('knee', (46.2, 96.6), 3.6, 1.6, amp=0.4, cast=2, depth=1),
    Bump('calf_out', (42.4, 100.0), 4.8, 3.4, ang=102, amp=1.6, cast=2, depth=3, taper=-0.3),
    Bump('calf_in', (50.2, 100.4), 4.6, 3.4, ang=78, amp=1.6, cast=2, depth=3, taper=-0.3),
]


def back_leg(side):
    """The approved leg's outline, seen from behind."""
    bumps = side_bumps(BACK_LEG_BUMPS, side)
    pts = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6), (53.4, 98.8),
           (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]
    pix = poly(mpts(pts) if side else pts)
    c = (112 - 46.2, 90) if side else (46.2, 90)
    form = Form(axis=[(c[0], 80), (c[0], 104)], r=9.5)
    part = Layer(pix, form, bumps, floor=0.2, strength=1.0).shade_owned(cuts=CUTS)[0]
    # the crease behind the knee
    for x in range(40, 53):
        xx = (112 - x) if side else x
        if (xx, 96) in part:
            part[(xx, 96)] = K.DARKER[K.DARKER[part[(xx, 96)]]]
    return part


def back_boot(side):
    """The approved boot seen from behind: its outline, a heel counter instead of laces."""
    part = B.gr_boots.boot(side)
    for (x, y), k in list(part.items()):
        if k == 'x' and 102 <= y <= 105:          # the laces: gone from the back
            part[(x, y)] = 'X'
    cx = (112 - 45.6) if side else 45.6
    for (x, y), k in list(part.items()):
        if 103 <= y <= 108 and abs(x - cx) <= 1.2 and k not in ('k', 'L', 'M'):
            part[(x, y)] = 'x'                     # the heel counter's seam
    return part


# ------------------------------------------------------------------------------------ profile

# The head turned to his left (screen left), in profile, for the three-quarter back twist. The
# mane (the crown, the back of the head, the fall down the back) is a traced outline shaded like
# the back mane; the face and the ear are drawn by hand: the forehead with its vein, the brow,
# the eye behind the gold lens, the temple arm running back to the ear, the nose, the moustache,
# the mouth, the square chin and the jaw back under the ear.
PROFILE_HAIR = [(49.6, 26.4), (64.0, 26.0), (67.0, 28.0), (68.6, 31.0), (68.6, 35.0), (67.6, 38.4),
                (66.6, 42.0), (66.2, 48.0), (64.6, 54.6), (61.0, 56.4), (57.4, 55.2), (55.6, 49.0),
                (55.4, 44.0), (55.2, 37.4), (51.2, 36.4), (49.6, 34.4), (47.6, 32.4), (45.6, 30.4),
                (44.8, 28.8), (46.4, 27.4)]

# face and ear, x 38-55 (18 columns), rows 30-50
FACE_X0, FACE_Y0 = 38, 30
PROFILE_FACE = [
    # x: 38-42 43-47 48-52 53-55      y
    "..... .kk.. ..... ...",   # 30  the forehead under the hairline
    "..... k11k. ..... ...",   # 31
    "....k 1v22k ..... ...",   # 32
    "....k 1v222 k.... ...",   # 33  the vein on the forehead
    "...k1 1v223 3k... ...",   # 34
    "...kd ddd23 33k.. ...",   # 35  the brow
    "..kGk kGGGG GGG.. ...",   # 36  the lens, the lash, the temple arm back to the ear
    "..kGO 23333 334kk k..",   # 37  the eye; the ear's top
    "..kG2 23333 34k23 k..",   # 38
    ".k112 23333 34k34 k..",   # 39  the nose's bridge
    "k1122 22333 34k43 k..",   # 40
    "k1122 22233 34k34 k..",   # 41  the nose tip
    ".k453 22233 34kk4 k..",   # 42  the nostril
    "..kdc c2333 344kk ...",   # 43  moustache
    "..kdd 54333 4444k ...",   # 44  the mouth's corner
    "...kd 23334 444k. ...",   # 45
    "...k2 23334 44k.. ...",   # 46  the chin
    "...k2 23344 4k... ...",   # 47
    "...k3 33444 k.... ...",   # 48
    "....k kkkkk ..... ...",   # 49  the jaw's keyline
]


def _profile_face():
    out = {}
    for r, row in enumerate(PROFILE_FACE):
        row = row.replace(' ', '')
        assert len(row) == 18, (FACE_Y0 + r, row, len(row))
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FACE_X0 + c, FACE_Y0 + r)] = ch
    return out


def profile_head():
    """(hair part, face part): stamp the hair WITH an outline, then the face without one (it
    carries its own lines, and its skin cuts the hairline where it overlaps)."""
    hair = {}
    for (x, y) in poly(PROFILE_HAIR):
        u, v = (x - 60) / 10.0, (y - 34) / 14.0
        lit = -(u * 0.6 + v * 0.6) + 0.25
        tone = 'a' if lit > 0.70 else 'b' if lit > 0.25 else 'c' if lit > -0.25 else 'd'
        if y > 38 and (x + int((y - 38) * 0.15)) % 3 == 0:
            tone = K.DARKER[tone]             # the fall down the back: straight strands
        elif y <= 38 and y > 27:
            rr = ((x - 58.0) ** 2 + ((y - 40.0) * 1.15) ** 2) ** 0.5
            if int(rr) % 3 == 0:
                tone = K.DARKER[tone]         # over the skull: arcs round it
        hair[(x, y)] = tone
    return hair, _profile_face()
