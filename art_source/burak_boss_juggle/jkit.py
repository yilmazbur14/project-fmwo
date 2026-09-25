"""Juggle-frame machinery for Captain Burak.

His approved look lives in art_source/burak_boss (kit, head, burak), checked against burak_boss.png
pixel for pixel. Nothing here redraws him: the rig renders his CORE (head, hair, coat, tee, sash,
thighs) upright in its own 96x96 frame, and this module PLACES that render into the bigger juggle
frame under a rotation, so a pose can turn without hand-redrawing the face or the coat's trim.

Three rules keep a rotated pixel sprite clean and lit like the cast (the juggle contract's trap):

  1. Never resample the outer keyline. The core's outer black is filled with the colour beside it
     first (fill_keyline), the rotation samples that, and a fresh 1px keyline is drawn on the rotated
     silhouette (reoutline).
  2. Inverse-map, never forward-map: every frame pixel asks the core what is under it, so a rotation
     cannot punch holes. Pivots sit on pixel corners, so quarter turns are exact.
  3. Rotate the NORMAL, not the light. Each relit part has a volume (the head and hair are
     ellipsoids, the coat, tee and sash a cylinder round his spine, each thigh a cylinder). A pixel's
     tone moves by how far the rotation turned its normal toward or away from the cast's upper-left
     light: at 0 degrees that is exactly nothing, so the approved shading, folds and trim survive, and
     at 180 degrees the lit side comes back round to the screen's left.

Limbs, props and effects are drawn straight into the frame, where the rig's own shading already
uses the fixed upper-left light, so they need no relight.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.join(os.path.dirname(HERE), 'burak_boss')
for _p in (RIG, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import burak as B  # noqa: E402
import head as H  # noqa: E402
import jhead  # noqa: E402
import kit  # noqa: E402
from kit import LIGHT3, amap, capsule, cylinder, ellipse, fill, line, poly, rim  # noqa: E402,F401

# ------------------------------------------------------------------ the frame
FW, FH = 192, 144                   # holds his whole body at every rotation, the props and the dust
FEET = (96, 143)                    # the ground frames' bottom-centre texel (his feet / the mat line)
GROUND_SHIFT = (48, 48)             # upright core -> frame: his approved feet (48, 95) land on FEET
PIVOT_LOCAL = (48, 58)              # his middle in his own frame (between chest and sash), on a corner
TUMBLE_AT = (96, 86)                # where that middle sits in every air frame (the tumble centre):
                                    # 20px over its standing place (96, 106), as low as a full turn
                                    # (his head reaches ~56px from it) allows in 144 rows
LOCAL = 96

# The approved sheet's palette, as keys. Relit tones stay on these ramps, so nothing new appears.
APPROVED_KEYS = set('k23456psmljihutrqYOoGgTRVvyXxWweBAZz097') - {'6'}
MERGE = B.MERGE                      # '1'->'2', '6'->'9', '8'->'7', as the approved sheet does

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


# ------------------------------------------------------------------ the core, upright
def core(expr='dizzy', head_dy=0, head_dx=0, flare=False, lock_short=True):
    """His head, hair, coat, tee, sash and thighs, upright in his own frame, with each pixel's
    owner recorded for the relight. No arms, boots, hat or weapons: those are posed in the frame."""
    cv = kit.Canvas(LOCAL, LOCAL)

    def put(part, dx=0, dy=0, outline=True, owner=None):
        cv.stamp({(x + dx, y + dy): k for (x, y), k in part.items()} if (dx or dy) else part,
                 outline, owner)

    put(B.coat_back(), owner='coat')
    put(B.legs(), owner='legs')
    put(B.tee(), owner='tee')
    band, tails = B.sash()
    put(band, owner='sash')
    put(amap(B.BUCKLE, 45, 65), outline=False, owner='detail')
    put(B.coat_panel(1, flare=flare), owner='coat')
    put(B.coat_panel(0), owner='coat')
    put(tails, owner='sash')
    put(B.collar(), owner='coat')
    # the neck stretches when the head is snapped up
    neck = H.neck()
    if head_dy < 0:
        for y in range(44 + head_dy, 44):
            for x in range(42, 55):
                neck[(x, y)] = '5' if x < 52 else '5'
    put(neck, dx=head_dx, owner='skin')
    put(B.tee_collar(), outline=False, owner='tee')
    put(B.chain(), outline=False, owner='detail')
    l, r = H.ears()
    put(l, head_dx, head_dy, owner='skin')
    put(r, head_dx, head_dy, owner='skin')
    put(H.face_base(), head_dx, head_dy, owner='skin')
    put(jhead.features(expr), head_dx, head_dy, outline=False, owner='face')
    put(jhead.hair_hatless(short_lock=lock_short), head_dx, head_dy, owner='hair')
    put(jhead.flyaways_hatless(), head_dx, head_dy, outline=False, owner='detail')
    return dict(cv.px), dict(cv.own)


def hat_local(ribbons=True):
    """The tricorn on its own, upright, with the bandana's red tails trailing from its band (they
    fly off with it). In the approved sheet's own coordinates."""
    cv = kit.Canvas(LOCAL, 40)
    if ribbons:
        for t in B.bandana_tails(0.0):
            cv.stamp(t, owner='ribbon')
    cv.stamp(H.hat(0.0), outline='soft', owner='hat')
    return dict(cv.px), dict(cv.own)


# ------------------------------------------------------------------ placing it in the frame
def fill_keyline(px, own):
    """The core's outer black keyline, replaced by the interior colour beside it (and its owner)."""
    def op(q):
        return q in px

    outer = {q for q, k in px.items() if k == 'k' and any(not op((q[0] + dx, q[1] + dy)) for dx, dy in N4)}
    out, oown = dict(px), dict(own)
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in todo:
            cands = []
            for dx, dy in N8:
                q = (x + dx, y + dy)
                if q in px and q not in todo and out[q] != 'k':
                    cands.append((out[q], oown.get(q)))
            if cands:
                # ties broken in a fixed order: set order follows Python's per-process string hashing,
                # which made the build differ run to run
                best = max(sorted(set(cands), key=lambda c: (str(c[0]), str(c[1]))), key=cands.count)
                out[(x, y)], oown[(x, y)] = best
                done.append((x, y))
        if not done:
            break
        todo -= set(done)
    return out, oown


def matrix(angle, sx=1.0, sy=1.0):
    """Rotation (clockwise on screen, positive degrees), then a frame-space squash."""
    t = math.radians(angle)
    c, s = math.cos(t), math.sin(t)
    return (c * sx, -s * sx, s * sy, c * sy)


def inverse(M):
    a, b, c, d = M
    det = a * d - b * c
    return (d / det, -b / det, -c / det, a / det)


def to_frame(M, p, pl, pf):
    dx, dy = p[0] - pl[0], p[1] - pl[1]
    return (M[0] * dx + M[1] * dy + pf[0], M[2] * dx + M[3] * dy + pf[1])


def place(px, own, angle, pl, pf, sx=1.0, sy=1.0):
    """Sample a local part into the frame through the matrix, backwards. Returns the frame's keys,
    owners and, for every pixel, the local pixel it came from (for the relight)."""
    fpx, fown = fill_keyline(px, own)
    M = matrix(angle, sx, sy)
    Mi = inverse(M)
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    corners = [to_frame(M, (x, y), pl, pf) for x in (min(xs), max(xs) + 1) for y in (min(ys), max(ys) + 1)]
    x0 = int(math.floor(min(c[0] for c in corners))) - 1
    x1 = int(math.ceil(max(c[0] for c in corners))) + 1
    y0 = int(math.floor(min(c[1] for c in corners))) - 1
    y1 = int(math.ceil(max(c[1] for c in corners))) + 1
    P, O, U = {}, {}, {}
    for Y in range(max(0, y0), min(FH, y1)):
        for X in range(max(0, x0), min(FW, x1)):
            dx, dy = X + 0.5 - pf[0], Y + 0.5 - pf[1]
            u = Mi[0] * dx + Mi[1] * dy + pl[0]
            v = Mi[2] * dx + Mi[3] * dy + pl[1]
            q = (int(math.floor(u)), int(math.floor(v)))
            if q in fpx:
                P[(X, Y)], O[(X, Y)], U[(X, Y)] = fpx[q], fown.get(q), q
    return P, O, U


# ------------------------------------------------------------------ the relight
# Each relit owner's volume, in its own upright frame: an ellipsoid (cx, cy, rx, ry), a vertical
# cylinder round his spine (cx, r), or one cylinder per thigh.
VOLUMES = {
    'skin': ('ell', 48.0, 35.0, 24.0, 26.0),       # flatter than his head: the approved face is cel-flat
    'hair': ('ell', 48.0, 21.0, 20.0, 15.0),
    'coat': ('cyl', 48.0, 21.0),
    'tee': ('cyl', 48.0, 21.0),
    'sash': ('cyl', 48.0, 21.0),
    'legs': ('thighs',),
    'hat': ('ell', 48.0, 8.0, 22.0, 9.0),
    'ribbon': ('flat',),
}
# The ramps a relit pixel may move along, light -> dark, all on the approved palette.
RAMPS = {
    'skin': ['2345'],
    'hair': ['mljih'],
    'coat': ['TRVv', 'YOoGg'],
    'tee': ['Wwe'],
    'sash': ['yXx'],
    'legs': ['0987'],
    'hat': ['utrq', 'YOoGg'],
    'ribbon': ['yXx'],
}
STEP = 0.45                          # light per tone on his coat's ramp, measured off the approved shading
# How far a relit pixel may move along its ramp. The face is drawn in flat cels (a lit edge, a base, a
# shaded side), so a turn may move it one tone; the coat and hair carry real volume and may move more.
MAX_SHIFT = {'skin': 1, 'hair': 2, 'coat': 3, 'tee': 2, 'sash': 2, 'legs': 2, 'hat': 3, 'ribbon': 1}


def normal(owner, u, v):
    vol = VOLUMES[owner]
    x, y = u + 0.5, v + 0.5
    if vol[0] == 'ell':
        _, cx, cy, rx, ry = vol
        nx, ny = (x - cx) / rx, (y - cy) / ry
        d2 = nx * nx + ny * ny
        if d2 > 1.0:
            s = math.sqrt(d2)
            return nx / s, ny / s, 0.0
        return nx, ny, math.sqrt(1.0 - d2)
    if vol[0] == 'cyl':
        _, cx, r = vol
        nx = max(-1.0, min(1.0, (x - cx) / r))
        return nx, 0.0, math.sqrt(1.0 - nx * nx)
    if vol[0] == 'thighs':
        cx = 44.5 if x < 48.5 else 53.5
        nx = max(-1.0, min(1.0, (x - cx) / 4.5))
        return nx, 0.0, math.sqrt(1.0 - nx * nx)
    return 0.0, 0.0, 1.0                                  # flat: faces the viewer, turns with nothing


def lum(n):
    return n[0] * LIGHT3[0] + n[1] * LIGHT3[1] + n[2] * LIGHT3[2]


def relight(P, O, U, angle):
    """Move each relit pixel along its ramp by how far the rotation turned its normal toward or away
    from the light. At angle 0 this changes nothing."""
    t = math.radians(angle)
    c, s = math.cos(t), math.sin(t)
    for q, k in list(P.items()):
        owner = O.get(q)
        if owner not in VOLUMES or q not in U:
            continue
        ramp = next((r for r in RAMPS[owner] if k in r), None)
        if ramp is None:
            continue
        n = normal(owner, *U[q])
        nr = (n[0] * c - n[1] * s, n[0] * s + n[1] * c, n[2])
        shift = int(round((lum(n) - lum(nr)) / STEP))
        cap = MAX_SHIFT.get(owner, 3)
        shift = max(-cap, min(cap, shift))
        if shift:
            P[q] = ramp[max(0, min(len(ramp) - 1, ramp.index(k) + shift))]


def reoutline(P):
    """Every pixel on the placed part's silhouette edge becomes the 1px black keyline."""
    edge = [q for q in P if any((q[0] + dx, q[1] + dy) not in P for dx, dy in N4)]
    for q in edge:
        P[q] = 'k'


def placed(px, own, angle, pl, pf, sx=1.0, sy=1.0, relit=True):
    P, O, U = place(px, own, angle, pl, pf, sx, sy)
    if relit:
        relight(P, O, U, angle)
    reoutline(P)
    return P, O


def body_point(p, angle, pl, pf, sx=1.0, sy=1.0):
    """Where a point of his own upright frame lands in the juggle frame (a shoulder, a knee)."""
    return to_frame(matrix(angle, sx, sy), p, pl, pf)


# ------------------------------------------------------------------ limbs, in the frame
SHOULDER_L, SHOULDER_R = (31.5, 53.0), (64.5, 53.0)     # the coat's shoulders (the approved sleeves' roots)
KNEE_L, KNEE_R = (42.0, 81.0), (54.5, 81.0)            # where the boots come out from under the coat


def arm(cv, shoulder, elbow, hand, hand_part=None, lit=True):
    """A coat sleeve pushed up to the elbow, the bunched gold-edged cuff, a bare forearm, a hand.
    Shaded in the frame against the fixed light, so it is right whichever way he is turned."""
    sl = fill(capsule(shoulder, elbow, 4.6, 4.0), 'R')
    cylinder(sl, shoulder, elbow, 4.6, 'TRVv', (0.55, 0.2, -0.25))
    cv.stamp(sl, owner='arm')
    ax, ay = hand[0] - elbow[0], hand[1] - elbow[1]
    L = math.hypot(ax, ay) or 1.0
    ux, uy = ax / L, ay / L
    cuff_c = (elbow[0] + ux * 0.8, elbow[1] + uy * 0.8)
    cv.stamp(B.cuff_d(cuff_c, (ux, uy), 1.5, 4.0), owner='arm')
    fore_end = (hand[0] - ux * 2.2, hand[1] - uy * 2.2)
    cv.stamp(B.limb([((elbow[0] + ux * 2.3, elbow[1] + uy * 2.3), fore_end, 2.9, 2.6)], '3', '2', '4', '5'),
             owner='arm')
    cv.stamp(hand_part if hand_part is not None else open_hand(hand, (ux, uy)), owner='arm')


def open_hand(c, d, r=3.3):
    """A limp open hand: a palm with the thumb off one side, rim-lit from the upper left."""
    cx, cy = c
    ux, uy = d
    shape = ellipse(cx, cy, r, r) | ellipse(cx + ux * 2.2 - uy * 1.8, cy + uy * 2.2 + ux * 1.8, 1.6, 1.6)
    shape |= capsule((cx, cy), (cx + ux * 3.4, cy + uy * 3.4), 2.2, 1.6)          # the fingers
    p = fill(shape, '3')
    rim(p, '2', -1, 0)
    rim(p, '2', 0, -1, only='3')
    rim(p, '4', 1, 0)
    rim(p, '5', 0, 1, only='34')
    return p


def boot(cv, knee, ankle, toe):
    """A tall black boot from under the coat: the shaft with its turned-down cuff, the foot."""
    sh = fill(capsule(knee, ankle, 4.0, 3.6), 'r')
    cylinder(sh, knee, ankle, 4.0, 'utrq', (0.6, 0.25, -0.2))
    ft = fill(capsule(ankle, toe, 3.4, 2.6), 'r')
    cylinder(ft, ankle, toe, 3.4, 'utrq', (0.6, 0.25, -0.2))
    ax, ay = ankle[0] - knee[0], ankle[1] - knee[1]
    L = math.hypot(ax, ay) or 1.0
    ux, uy = ax / L, ay / L
    cuff = fill(capsule((knee[0] - ux * 0.5, knee[1] - uy * 0.5), (knee[0] + ux * 2.8, knee[1] + uy * 2.8), 5.1, 4.9), 't')
    cylinder(cuff, knee, ankle, 5.1, 'utrq', (0.5, 0.1, -0.3))
    cv.stamp(ft, owner='boot')
    cv.stamp(sh, owner='boot')
    cv.stamp(cuff, owner='boot')


# ------------------------------------------------------------------ props
def cutlass(cv, guard, tip, bow=2.2):
    """His cutlass, anywhere at any angle: the blade, then the brass hilt at the guard end."""
    cv.stamp(B.cutlass(guard, tip, bow=bow), owner='prop')
    gx, gy = guard
    dx, dy = tip[0] - gx, tip[1] - gy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    # the grip back from the guard, the shell guard across it, the knuckle-bow arcing round
    grip = fill(capsule((gx, gy), (gx - ux * 6.0, gy - uy * 6.0), 1.4, 1.4), '9')
    rim(grip, '0', -1, 0)
    rim(grip, '7', 1, 0)
    cv.stamp(grip, owner='prop')
    shell = fill(capsule((gx - nx * 2.8, gy - ny * 2.8), (gx + nx * 2.8, gy + ny * 2.8), 1.3, 1.3), 'O')
    rim(shell, 'G', 1, 0)
    rim(shell, 'G', 0, 1)
    bow_pts = [(gx + nx * 2.6, gy + ny * 2.6), (gx - ux * 3.0 + nx * 4.2, gy - uy * 3.0 + ny * 4.2),
               (gx - ux * 6.6 + nx * 1.4, gy - uy * 6.6 + ny * 1.4)]
    bw = {}
    for a, b in zip(bow_pts, bow_pts[1:]):
        for q in capsule(a, b, 0.7, 0.7):
            bw[q] = 'o'
    cv.stamp(bw, owner='prop')
    cv.stamp(shell, owner='prop')
    pom = fill(ellipse(gx - ux * 7.2, gy - uy * 7.2, 1.5, 1.5), 'O')
    rim(pom, 'G', 1, 0)
    cv.stamp(pom, owner='prop')


def pistol(cv, breech, barrel_dir, grip_dir, **kw):
    for part in B.pistol_parts(breech, barrel_dir, grip_dir, **kw):
        cv.stamp(part, owner='prop')


def hat_placed(cv, angle, at, pivot=(48.0, 9.0)):
    """The tricorn flying, turned by `angle` about its crown, relit like the body."""
    px, own = hat_local()
    P, O = placed(px, own, angle, pivot, at)
    cv.stamp(P, outline=False, owner='prop')


# ------------------------------------------------------------------ effects
def arc(cv, cx, cy, r, a0, a1, key='W', ry=None):
    """A motion streak: the trail he has just swept."""
    ry = r if ry is None else ry
    steps = max(8, int(abs(a1 - a0) * 1.6))
    pts = [(int(round(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)))),
            int(round(cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / steps))))) for i in range(steps + 1)]
    for a, b in zip(pts, pts[1:]):
        for q in line(a[0], a[1], b[0], b[1]):
            if q not in cv.px and 0 <= q[0] < FW and 0 <= q[1] < FH:
                cv.px[q] = key
                cv.own[q] = 'fx'


def lines(cv, segs, key='k'):
    for (x0, y0, x1, y1) in segs:
        for q in line(x0, y0, x1, y1):
            if 0 <= q[0] < FW and 0 <= q[1] < FH:
                cv.px[q] = key
                cv.own[q] = 'fx'


def puff(cv, cx, cy, r):
    """A round dust ball off the mat, keylined, lit top-left."""
    shape = ellipse(cx, cy, r, r)
    p = fill(shape, 'W')
    for q in shape:
        u, v = (q[0] - cx) / r, (q[1] - cy) / r
        if u * 0.62 + v * 0.78 > 0.35:
            p[q] = 'w'
        if u * 0.62 + v * 0.78 > 0.8:
            p[q] = 'e'
    cv.stamp(p, owner='fx')


STAR = [
    "...k...",
    "..kOk..",
    "kkkOkkk",
    "kOOYOok",
    ".koOok.",
    ".kokok.",
    ".kk.kk.",
]


def star(cv, cx, cy):
    """A dizzy star: five points, gold, keylined, lit from the upper left."""
    cv.stamp(amap(STAR, cx - 3, cy - 3), outline=False, owner='fx')


def specks(cv, pts, key='W'):
    for q in pts:
        if q not in cv.px and 0 <= q[0] < FW and 0 <= q[1] < FH:
            cv.px[q] = key
            cv.own[q] = 'fx'


def drop(cv, x, y):
    """A comedy sweat drop, pale steel, keylined."""
    p = {(x, y): 'B', (x, y + 1): 'B', (x - 1, y + 2): 'B', (x, y + 2): 'A', (x + 1, y + 2): 'A',
         (x, y + 3): 'A'}
    cv.stamp(p, owner='fx')


# ------------------------------------------------------------------ clean-up
def body_pixels(cv):
    return {q for q, o in cv.own.items() if o != 'fx'}


def despeckle(cv):
    """Rotation crumbs: body and prop pixels with fewer than two drawn 4-neighbours, removed until
    none are left (dropping one can strand the next)."""
    while True:
        drop_ = [q for q in body_pixels(cv)
                 if sum((q[0] + dx, q[1] + dy) in cv.px for dx, dy in N4) < 2]
        if not drop_:
            break
        for q in drop_:
            cv.px.pop(q, None)
            cv.own.pop(q, None)


def pinholes(cv):
    """Single transparent pixels walled in by the body, which rotation opens up."""
    for _ in range(2):
        add = []
        for y in range(FH):
            for x in range(FW):
                if (x, y) in cv.px:
                    continue
                n = [cv.px.get((x + dx, y + dy)) for dx, dy in N4]
                if all(n):
                    cands = [k for k in n if k != 'k']
                    add.append(((x, y), max(sorted(set(cands)), key=cands.count) if cands else 'k'))
        for q, k in add:
            cv.px[q] = k
            cv.own[q] = 'fill'


def finish(cv):
    despeckle(cv)
    pinholes(cv)
    return {q: MERGE.get(k, k) for q, k in cv.px.items()}


def frame_canvas():
    return kit.Canvas(FW, FH)
