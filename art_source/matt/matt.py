"""Matt, the loud one: the initial sprite. 2 frames of 96x96, feet on row 95, column 48 the anchor
and the mirror axis (x' = 96 - x). Frame 0 is the idle, frame 1 the signature roar.

Design: Matt's own likeness (round face, dark cropped hair, light-tan skin, stocky build, black
trousers, white socks with black stripes) wearing Exploud: the hair gelled into five thick spikes
with yellow-dyed tips (the crest), a lavender crewneck with yellow ribbing at the collar, cuffs and
hem (the tube rims), speaker ports on the shoulders (the side holes), ridged sleeves (the ridged
arms), and lavender trainers whose white toe bumpers split into three claws (Exploud's feet).
The mouth is the character.

Build order is back to front. Parts stamped with an outline cut a 1px black keyline into whatever
is under their edge; that is where the interior separations come from. Hand-drawn maps carry their
own keylines. Light comes from the upper left; right-hand parts are built from mirrored points
rather than mirrored pixels so they keep that light.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pal  # noqa: F401  (installs the palette into the toolkit)
from pal import lib
from lib import Canvas, amap, ellipse, fill, poly
from shapes import AX, capsule, mir_set, sym, tuft_frames
import details
import face as faces
import shading as sh

W = H = 96

LAV = ('ABCDE', (0.93, 0.74, 0.34, 0.0))
YEL = ('abcde', (0.9, 0.62, 0.25, -0.1))


def mpts(pts, side):
    return [(AX - x, y) for (x, y) in pts] if side else pts


def mpt(p, side):
    return (AX - p[0], p[1]) if side else p


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


# ------------------------------------------------------------------ pose

class Pose:
    """Everything that differs between the idle and the roar, in one place."""

    def __init__(self, roar=False):
        self.roar = roar
        # crest: (angle, r_base, r_tip, w0, w1, bend) for the centre, inner and outer spikes
        if roar:
            self.spikes = [(0, 8, 28, 6.4, 2.0, 0.0), (-37, 8, 30, 6.4, 2.0, 0.5),
                           (-80, 9, 30, 7.2, 2.4, 1.0)]
        else:
            self.spikes = [(0, 8, 27, 6.2, 1.9, 0.0), (-31, 8, 26, 6.2, 1.9, 1.5),
                           (-66, 9, 27, 7.0, 2.2, 2.5)]
        self.head_dy = 1 if roar else 0          # he leans in: the head drops
        self.shoulder_dy = -3 if roar else 0     # and the shoulders hunch up round it
        self.upper_rot = 30 if roar else 0       # upper arms flare out from the shoulder (deg)
        self.fore_rot = 6 if roar else 0         # forearms hang, flared a little less
        self.stance = 2 if roar else 0           # feet braced wider (px each side)


def rot(p, c, deg):
    """Rotate p about c; positive swings a left-hand limb outward (screen coordinates, y down)."""
    a = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


# ------------------------------------------------------------------ lower body

def trousers(P):
    s = P.stance
    left = poly([(48, 70), (31.5, 70), (30 - s * 0.4, 74), (28.5 - s * 0.7, 79), (28 - s, 83),
                 (43.5 - s, 83), (44.5 - s * 0.7, 80), (46 - s * 0.3, 77.5), (48, 76.5)])
    part = fill(left | mir_set(left), 'L')
    lp = {p: k for p, k in part.items() if p[0] < 48}
    rp = {p: k for p, k in part.items() if p[0] > 48}
    sh.cylinder(lp, (38.5, 71), (36 - s, 87), 8.5, 'NMLK', (0.84, 0.62, 0.2))
    sh.cylinder(rp, (57.5, 71), (60 + s, 87), 8.5, 'NMLK', (0.84, 0.62, 0.2))
    part.update(lp)
    part.update(rp)
    for y in range(70, 80):
        if (48, y) in part:
            part[(48, y)] = 'k'                 # the split between the legs, up to the hem
    return part


def feet(P):
    """Both feet: striped socks and lavender trainers, from the structure map, form shaded."""
    out = []
    for side in (0, 1):
        f = moved(details.foot_structure(side), P.stance if side else -P.stance, 0)
        sock = {p: 'W' for p, k in f.items() if k == 'S'}
        upper = {p: 'C' for p, k in f.items() if k == 'U'}
        rubber = {p: 'W' for p, k in f.items() if k == 'W'}
        laces = {p: 'b' for p, k in f.items() if k == 'Y'}
        c = mpt((35.5 - P.stance, 87), side)
        sh.cylinder(sock, (c[0], 80), (c[0], 95), 7.0, 'WXx', (0.35, -0.2))
        u = mpt((35 - P.stance, 92), side)
        sh.ellipsoid(upper, u[0], u[1], 11, 5, 'BCDE', (0.8, 0.45, 0.05))
        sh.ellipsoid(rubber, u[0], u[1] - 2, 11, 5, 'WXx', (0.2, -0.45))
        sh.ellipsoid(laces, u[0], u[1] - 3, 5, 3, 'abc', (0.7, 0.3))
        for d in (sock, upper, rubber, laces):
            f.update(d)
        out.append(f)
    return out


# ------------------------------------------------------------------ torso

def sweatshirt(P):
    part = fill(poly(sym([(48, 48.5), (41, 49), (36, 50.5), (31.5, 52.5), (30.5, 56), (31, 61),
                          (32, 65), (32.5, 68.5), (33, 71), (48, 71)])), 'C')
    sh.ellipsoid(part, 47, 58, 19, 15, 'ABCDE', (0.93, 0.76, 0.36, 0.0))
    # occlusion: the flanks sit in the arms' shadow, and the collar shades the chest under it
    for (x, y) in list(part):
        edge = min(x - min(px for (px, py) in part if py == y), max(px for (px, py) in part if py == y) - x)
        if 57 <= y <= 70 and edge <= 1:
            part[(x, y)] = pal.DARKER[part[(x, y)]]
        if not P.roar and 57 <= y <= 58 and 40 <= x <= 56:
            part[(x, y)] = pal.DARKER[part[(x, y)]]
    return part


def hem_band(P):
    part = fill(poly(sym([(48, 68.5), (33.5, 68.5), (32.5, 70.5), (33.5, 72.5), (48, 72.5)])), 'c')
    sh.ellipsoid(part, 46, 66, 17, 8, 'abcde', (0.9, 0.62, 0.28, -0.1))
    return part


ELBOW0, WRIST0 = (17.5, 65.5), (18.5, 70)


def arm_geometry(P):
    """The left arm for this pose: deltoid centre, shoulder, elbow, wrist, and how far the wrist
    moved from the idle (the cuff and fist follow it)."""
    dy = P.shoulder_dy
    pivot = (26, 56 + dy)
    dc = rot((25, 57 + dy), pivot, P.upper_rot * 0.25)
    s0 = rot((24, 60 + dy), pivot, P.upper_rot)
    s1 = rot((ELBOW0[0], ELBOW0[1] + dy), pivot, P.upper_rot)
    v = rot((WRIST0[0] - ELBOW0[0], WRIST0[1] - ELBOW0[1]), (0, 0), P.fore_rot)
    s2 = (s1[0] + v[0], s1[1] + v[1])
    return dc, s0, s1, s2, (s2[0] - WRIST0[0], s2[1] - WRIST0[1])


def arm_parts(P, side):
    """One sleeve and cuff, built from mirrored points so the light stays upper left.
    Returned in stamp order as (part, outline)."""
    dcl, s0l, s1l, s2l, _ = arm_geometry(P)
    dc, s0, s1, s2 = (mpt(p, side) for p in (dcl, s0l, s1l, s2l))
    delt = ellipse(dc[0], dc[1], 7.4, 6.8)
    up = capsule(s0, s1, 5.6, 5.2)
    fo = capsule(s1, s2, 5.2, 4.9)
    sleeve = {p: 'C' for p in (delt | up | fo) if p[1] <= s2[1]}
    upper = {p: 'C' for p in sleeve if p in delt}
    rest = {p: 'C' for p in sleeve if p not in delt}
    sh.ellipsoid(upper, dc[0], dc[1], 7.8, 7.2, *LAV)
    sh.cylinder(rest, s0, s2, 6.0, *LAV)
    sleeve.update(upper)
    sleeve.update(rest)
    # the bunched, ridged forearm: two fold grooves across it with a lit crest under each
    ax, ay = s2[0] - s1[0], s2[1] - s1[1]
    al = math.hypot(ax, ay)
    ax, ay = ax / al, ay / al
    for d in (-0.5, 2.5):
        for (x, y) in list(sleeve):
            if (x, y) in delt:
                continue
            along = (x - s1[0]) * ax + (y - s1[1]) * ay
            if d - 0.5 <= along < d + 0.5:
                sleeve[(x, y)] = 'k'            # a black ridge line, as Exploud's arms have
            elif d + 0.5 <= along < d + 1.5 and sleeve[(x, y)] in 'CD':
                sleeve[(x, y)] = pal.LIGHTER[sleeve[(x, y)]]
    # the cuff: the idle band, turned with the forearm and carried to the wrist
    band = [(12.5, 71), (24.5, 71), (25, 72.8), (12, 72.8)]
    band = [rot(p, WRIST0, P.fore_rot) for p in band]
    band = [(x + s2l[0] - WRIST0[0], y + s2l[1] - WRIST0[1]) for (x, y) in band]
    cuff = {p: 'c' for p in poly(mpts(band, side))}
    cc = mpt((s2l[0], s2l[1] + 1.5), side)
    sh.cylinder(cuff, (cc[0], cc[1] - 5), (cc[0], cc[1] + 7), 7.0, *YEL)
    for (x, y) in list(cuff):
        if round(x - cc[0]) % 2 == 0 and cuff[(x, y)] in 'bc':
            cuff[(x, y)] = pal.DARKER[cuff[(x, y)]]
    return [(sleeve, True), (cuff, True)]


def arm_offsets(P):
    """Whole-pixel offsets that carry the hand-drawn ports and fists with the arms (left side;
    the right is the mirror)."""
    dcl, _, _, _, wd = arm_geometry(P)
    port = (round(dcl[0] - 25), round(dcl[1] - 57))
    fist = (round(wd[0]), round(wd[1]))
    return port, fist


# ------------------------------------------------------------------ hair

def radial(cx, cy, ang_deg, r0, r1):
    a = math.radians(ang_deg)
    return ((cx + math.sin(a) * r0, cy - math.cos(a) * r0),
            (cx + math.sin(a) * r1, cy - math.cos(a) * r1))


DOME = sym([(48, 15.5), (42, 16), (38, 18), (35, 21.5), (33.8, 26), (33.8, 31), (34.3, 35.5),
            (35.9, 35.5), (36.2, 31.5), (37.8, 29.2), (41, 28.3), (48, 28)])

LIGHT = (-0.72, -0.69)          # toward the light: up and to the left


def spike_specs(P):
    """(base, tip, w0, w1, bend) for all five spikes, back to front: outer pair, inner pair, centre.
    The right-hand ones are built from mirrored points (not mirrored pixels) so each is lit from
    the same upper-left light."""
    out = []
    centre, inner, outer = P.spikes
    for (ang, r0, r1, w0, w1, bend) in (outer, inner):
        for sgn in (1, -1):
            base, tip = radial(48, 30, ang * sgn, r0, r1)
            out.append((base, tip, w0, w1, bend * sgn))
    ang, r0, r1, w0, w1, bend = centre
    base, tip = radial(48, 30, ang, r0, r1)
    out.append((base, tip, w0, w1, bend))
    return out


def hair(P):
    """The dome and the five spikes as one mass: each spike lit on its upper-left face with a
    streak, a slanted dye line to yellow tips, and a short dark cut running down from each V
    between spikes. Returned as a single part (keylined once, round the whole mass)."""
    dome = poly(DOME)
    spikes = [tuft_frames(base, tip, w0, w1, bend) for (base, tip, w0, w1, bend) in spike_specs(P)]
    part = {}
    for (x, y) in dome:
        u = (x - 48) / 15.0
        v = (y - 22) / 7.0
        lit = -(u * 0.75 + v * 0.65)
        part[(x, y)] = 'j' if lit > 0.55 else ('h' if lit < -0.55 else 'i')
    owner = {}
    for idx, (px, fr) in enumerate(spikes):
        for p in px:
            t, s, nx, ny = fr[p]
            t = min(1.0, t)
            lit = s * (nx * LIGHT[0] + ny * LIGHT[1])
            if t >= 0.64 - 0.06 * lit and p not in dome:
                k = 'c'
                if lit > 0.15:
                    k = 'b'
                if lit > 0.45 and t < 0.93:
                    k = 'a'
                if lit < -0.3:
                    k = 'd'
                if lit < -0.75:
                    k = 'e'
            else:
                k = 'i'
                if lit > 0.2:
                    k = 'j'
                if lit > 0.5 and 0.3 < t < 0.62:
                    k = 'l'
                if lit < -0.35:
                    k = 'h'
            part[p] = k
            owner[p] = idx
    # the cuts between spikes: a front spike's pixels bordering a spike behind it (not the dome)
    for idx, (px, fr) in enumerate(spikes):
        for p in px:
            if owner.get(p) != idx:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in owner and owner[q] < idx and q not in dome:
                    part[p] = 'k' if fr[p][0] > 0.42 else 'h'
                    break
    return part


# Strands combed up from the hairline toward the spike bases, so the dome under the spikes is not
# a flat mass: lit strands on the left, dark partings between them, the right side kept in shade.
# (x, y, key) at the idle position; only ever laid over hair tones.
STRANDS = [
    (36, 26, 'j'), (36, 25, 'j'), (37, 24, 'j'), (37, 23, 'l'), (38, 22, 'j'),
    (39, 27, 'h'), (39, 26, 'h'), (40, 25, 'h'), (40, 24, 'h'), (41, 23, 'h'),
    (41, 27, 'j'), (42, 26, 'j'), (42, 25, 'l'), (43, 24, 'j'), (43, 23, 'j'),
    (44, 27, 'h'), (45, 26, 'h'), (45, 25, 'h'),
    (46, 27, 'j'), (47, 26, 'j'), (47, 25, 'j'),
    (50, 27, 'h'), (50, 26, 'h'), (49, 25, 'h'),
    (52, 27, 'j'), (52, 26, 'i'), (53, 25, 'j'), (53, 24, 'i'),
    (55, 27, 'h'), (55, 26, 'h'), (56, 25, 'h'), (56, 24, 'h'),
    (58, 26, 'i'), (58, 25, 'i'), (59, 24, 'i'),
]


def comb(cv, dy):
    for (x, y, k) in STRANDS:
        q = (x, y + dy)
        if cv.px.get(q) in ('i', 'j', 'h', 'l'):
            cv.px[q] = k


# ------------------------------------------------------------------ frames

RINGS = (
    # (rx, ry, half-thickness): the inner ring bolder, the outer one thinning as it spreads
    (31, 27, 1.1),
    (42, 37, 0.8),
)


def rings(P, cv):
    """Sound rings spreading from the roaring mouth, drawn behind him: a near-white core, pale
    lavender flanks and a dark-lavender edge so they hold up on the light mat. Effects carry no
    black keyline in this house (Carter's aura, Josh's card glow)."""
    if not P.roar:
        return
    cx, cy = 48, 51
    add = {}
    for (rx, ry, th) in RINGS:
        for y in range(H):
            for x in range(W):
                if (x, y) in cv.px:
                    continue
                u, v = (x - cx) / rx, (y - cy) / ry
                d = (math.sqrt(u * u + v * v) - 1.0) * (rx + ry) / 2.0
                if abs(d) <= th:
                    add[(x, y)] = 'z' if abs(d) <= 0.7 else 'Z'
    body = set(add)
    for (x, y) in list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and q not in cv.px and 0 <= q[0] < W and 0 <= q[1] < H:
                add.setdefault(q, 'E')
    cv.px.update(add)


def build(roar=False):
    P = Pose(roar)
    cv = Canvas(W, H)
    cv.stamp(trousers(P))
    for f in feet(P):
        cv.stamp(f, outline=False)
    cv.stamp(sweatshirt(P))
    cv.stamp(hem_band(P))
    for side in (0, 1):
        for part, outline in arm_parts(P, side):
            cv.stamp(part, outline=outline)
    (pdx, pdy), (fdx, fdy) = arm_offsets(P)
    pl, pr = details.ports()
    cv.stamp(moved(pl, pdx, pdy), outline=False)
    cv.stamp(moved(pr, -pdx, pdy), outline=False)
    fl, fr = details.fists()
    cv.stamp(moved(fl, fdx, fdy), outline=False)
    cv.stamp(moved(fr, -fdx, fdy), outline=False)
    if not roar:
        cv.stamp(details.collar(), outline=False)
    cv.stamp(moved(hair(P), 0, P.head_dy))
    comb(cv, P.head_dy)
    if roar:
        cv.stamp(moved(amap(faces.ROAR, faces.X0, faces.ROAR_Y0), 0, P.head_dy), outline=False)
    else:
        cv.stamp(amap(faces.IDLE, faces.X0, faces.IDLE_Y0), outline=False)
    rings(P, cv)
    return cv


def frames():
    return build(False).image(), build(True).image()


if __name__ == '__main__':
    out = os.path.join(pal.HERE, 'out')
    os.makedirs(out, exist_ok=True)
    f0, f1 = frames()
    f0.save(os.path.join(out, 'f0.png'))
    f1.save(os.path.join(out, 'f1.png'))
    print('f0', lib.stats(f0))
    print('f1', lib.stats(f1))
