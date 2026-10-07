"""Jordan swivelled round in his chair to face screen-LEFT (the player stands on his left): the two
talk pairs, each mouth shut / mouth open.

  friendly   talking to "Aiden": brows up, eyes open, a warm smile; his far hand up in a wave
  glare      "You're Burak!": brows crushed, pupils pinned, teeth bared, the face flushed, an anger
             mark and steam; his far arm stabbing a finger at the player, the near fist clenched

His approved rig faces screen-right, so every part here is that rig's mirror, re-lit so the one light
stays upper-left (the house rule; the VS card turned Carter the same way):
  * the head is the approved head (the approved face rows, and my expressions written as row
    overrides of them, janim_heads style) mirrored, then re-lit the way pose_carter.turn_head_left
    does it: the face side, now turned into the light, one step up its ramp, the back of the skull
    one step down;
  * the tee, neck, arms and jeans are the rig's own shapes on mirrored geometry, lit by the rig's own
    rules (lit on the left, dark on the right), so they need no re-light;
  * the Peach print is NOT mirrored: a printed tee reads the right way round whichever way he turns;
  * the sneakers are the approved ones mirrored, their heels' lit edge put back in shadow.
The headset hangs round his neck (pulled down in the swivel).

Coordinates: parts are made in the approved rig's 96-frame space and moved by jfc_base.OFF into the
128 frame; the chair is jfc_chair at yaw -135 (facing down-left), its base the fixed one.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402
import jfc_chair as C  # noqa: E402

V = B.V2B
HD = B.HD
YAW = -135
DX, DY = 3, -6            # the mirrored upper body, moved over the seat's back half


def M(x):
    """The approved frame's mirror (its centre column 48 stays put)."""
    return 96 - x


def mb(pts, dx=DX, dy=DY):
    """Build-coordinate points of the approved rig -> mirrored 96-space, moved."""
    return [(M(x + B.ANCHOR_SHIFT) + dx, y + dy) for (x, y) in pts]


def mpart(part, dx=DX, dy=DY):
    return {(M(x + B.ANCHOR_SHIFT) + dx, y + dy): k for (x, y), k in part.items()}


#EXPRESSIONS (face rows over the approved ones, in the approved orientation: janim_heads' method)

IDLE, SHOUT, LAUGH = HD.IDLE, HD.SHOUT, HD.LAUGH
over = HD.over
_L = {y: LAUGH[y - HD.Y0] for y in range(21, 40)}

def edit(row, cols):
    """A face row with some columns replaced: {col: key}, col 0 = x 37."""
    r = list(row)
    for c, k in cols.items():
        r[c] = k
    return ''.join(r)


def _row(rows, y):
    return rows[y - HD.Y0]


# friendly: the brows lifted a row (laugh's), the heavy lid gone so the eyes open up, and the mouth's
# corners curled up past the ends of the thin moustache
F_LID = edit(_row(IDLE, 24), {9: 'c', 10: 'c', 11: 'c', 12: 'c', 13: 'c', 18: 'c', 19: 'c'})
F_CORNERS = edit(_row(IDLE, 30), {11: 'k', 18: 'k'})
F_SMILE = edit(_row(IDLE, 31), {11: 'd', 18: 'd'})
FRIENDLY_SHUT = over(IDLE, {22: _L[22], 23: _L[23], 24: F_LID, 30: F_CORNERS, 31: F_SMILE})
FRIENDLY_OPEN = over(SHOUT, {22: _L[22], 23: _L[23], 24: F_LID, 30: F_CORNERS})

# glare: the brows crushed down at the nose with a crease between them, the pupils pinned small
G_BROWS = {22: edit(_row(SHOUT, 22), {12: 'd', 13: 'd', 14: 'b', 15: 'd', 16: 'd'}),
           23: edit(_row(SHOUT, 23), {7: 'h', 8: 'h', 9: 'h', 10: 'h', 11: 'h', 12: 'i', 13: 'i', 14: 'i', 15: 'b'}),
           24: edit(_row(SHOUT, 24), {8: 'h', 9: 'h', 10: 'h', 14: 'b', 18: 'h', 19: 'b'}),
           26: edit(_row(IDLE, 26), {10: 'W', 18: 'W'})}
GLARE_SHUT = over(HD.rows('grit'), dict(G_BROWS))
GLARE_OPEN = over(LAUGH, {**G_BROWS, 25: _row(IDLE, 25), 27: _row(IDLE, 27)})

FACES = {'friendly_shut': FRIENDLY_SHUT, 'friendly_open': FRIENDLY_OPEN,
         'glare_shut': GLARE_SHUT, 'glare_open': GLARE_OPEN}
# brows that rise into row 21 (v2's hair row) lay their pixels over it, as janim_heads.ROW21 does
ROW21 = {'friendly_shut': {(x, 21): 'i' for x in list(range(44, 50)) + list(range(54, 58))},
         'friendly_open': {(x, 21): 'i' for x in list(range(44, 50)) + list(range(54, 58))}}

SKIN = ['a', 'b', 'c', 'd', 'e']
HAIR = ['h', 'i', 'j', 'l', 'm']
# the flush: the glare's upper face (above the beard) runs hot
FLUSH = {'e': 'T', 'd': 'T', 'c': 'R', 'b': 'V', 'a': 'v'}


EAR = {(x, y) for x in (37, 38, 39) for y in range(25, 30)}     # the approved head's ear (build space)
EAR_HOT = {'a': 'V', 'b': 'R', 'c': 'R', 'd': 'T', 'e': 'T'}


def face_part(name):
    """A face (rows 22 down) under v2's greasy hair, in build coordinates (unmirrored). The glare's
    ear burns red."""
    rows = FACES[name] if name in FACES else HD.rows(name)
    face = {q: k for q, k in B.amap(rows, HD.X0, HD.Y0).items() if q[1] >= 22}
    if name.startswith('glare'):
        for q in EAR:
            if face.get(q) in EAR_HOT:
                face[q] = EAR_HOT[face[q]]
    part = dict(face)
    part.update(B.V2H.hair())
    part.update(ROW21.get(name, {}))
    return part


def relight(part, cx, band=2, keep=()):
    """pose_carter.turn_head_left's re-light: the face side (left of cx, now toward the light) one
    step up its ramp, the back of the skull one step down. `keep` pixels (the eyes' irises and
    pupils, which borrow hair keys) are left alone."""
    keep = set(keep)
    out = {}
    for (x, y), k in part.items():
        step = 1 if x < cx - band else (-1 if x > cx + band else 0)
        if (x, y) in keep:
            step = 0
        if step and k in SKIN:
            out[(x, y)] = SKIN[max(0, min(4, SKIN.index(k) + step))]
        elif step and k in HAIR:
            out[(x, y)] = HAIR[max(0, min(4, HAIR.index(k) + step))]
        else:
            out[(x, y)] = k
    return out


# the eyes' own pixels in the approved head (build space): the re-light must not touch them
EYES = {(x, y) for y in (25, 26, 27) for x in list(range(44, 50)) + list(range(53, 58))}


def head(name, hx=3, hy=2, dx=DX, dy=DY, flush=False):
    """The head, mirrored and re-lit. (hx, hy) is v2's head offset (the slump), (dx, dy) the upper
    body's move."""
    part = B.shift(face_part(name), hx, hy)
    m = mpart(part, dx, dy)
    keep = {(M(x + hx + B.ANCHOR_SHIFT) + dx, y + hy + dy) for (x, y) in EYES}
    xs = [x for (x, y) in m]
    out = relight(m, (min(xs) + max(xs)) / 2.0, keep=keep)
    if flush:
        top = min(y for (x, y) in m)
        for (x, y), k in list(out.items()):
            # the forehead, brows' skin, eyes' surround, cheeks and nose: rows 22..29 of the face
            if k in FLUSH and top + 15 <= y <= top + 22 + (hy - 2):
                out[(x, y)] = FLUSH[k]
    return out


#BODY

# The Peach tee on the SKINNY build (the user, 2026-09-28: "i want jordan even skinnier and his shirt
# even more fitted", approved as "approve the skinnier one"; the FITTED tee before it, the same day),
# MATCHED to the fight sheets' in art_source/jordan_fit/jfit_body.py, which re-exports the v2 rig's
# (check_fit_matches() compares these numbers with that module whenever it exists). The skinny build:
# a 15px chest (x 42..56, the print's two side outline columns cropped) tapering under the print to a
# 13px waist (x 43..55), sleeves tighter and shorter (sleeve_outline), arms thinner (jfc_base.limb),
# thinner jeans (legs()). The fitted tee's notes, as they were:
#   the body is v2's narrow sloped shoulders into a close straight column, build x 40..58, two pixels
#   of cloth either side of the 15px Peach print (which stays where it is); the collar and its trim,
#   the drip and the smudge are v2's own; one dandruff flake moves in off the old sack's edge; the
#   sleeves are short and snug round the top of each stick arm. Seated, his hem gathers on his lap
#   two rows higher than standing (HEM_Y_SEATED). Build coordinates of the approved rig (facing
#   right), mirrored and moved like everything else here.
FIT_NEAR_X, FIT_FAR_X = 41.6, 56.4           # jfit_body.NEAR_X / FAR_X (the skinny chest's)
FIT_WAIST_NEAR, FIT_WAIST_FAR = 42.6, 55.4   # jfit_body.WAIST_NEAR / WAIST_FAR (the skinny waist's)
FIT_HEM_Y = 69.3                             # jfit_body.HEM_Y (standing)
HEM_Y_SEATED = 67.4
PRINT_X0, PRINT_X1 = V.PRINT_AT[0], V.PRINT_AT[0] + 14     # 42..56, the print's own 15 columns
FIT_DANDRUFF = {k: v for k, v in V.DANDRUFF.items() if k != (59, 49)}
FIT_DANDRUFF[(57, 49)] = 'W'
# the sleeves' roots, collar ends and shoulder lines (jfit_body.NEAR_* / FAR_*)
FIT_NEAR = dict(root=(40.6, 49.2), collar=(44.2, 43.2), shoulder=[(41.8, 44.4), (40.2, 46.2)], length=5.2)
FIT_FAR = dict(root=(57.8, 48.5), collar=(55.8, 43.4), shoulder=[(57.2, 44.6), (58.3, 46.0)], length=4.6)


def torso_outline(hem_y=HEM_Y_SEATED):
    """jfit_body.torso_outline (the v2 rig's, jv2_body.torso_outline) with the hem at `hem_y`."""
    n, f, wn, wf = FIT_NEAR_X, FIT_FAR_X, FIT_WAIST_NEAR, FIT_WAIST_FAR
    return [(44.4, 43.4), (55.6, 43.4), (57.2, 44.4), (58.0, 46.4),
            (f + 0.1, 50.0), (f, 56.0), (f, 60.4), (wf, 62.6), (wf, hem_y - 0.3),
            (54.0, hem_y), (52.6, hem_y + 0.9), (51.4, hem_y + 0.9), (49.8, hem_y), (46.0, hem_y - 0.1),
            (wn + 1.2, hem_y + 0.1), (wn, hem_y - 0.4),
            (wn, 62.6), (n, 60.4), (n, 56.0), (n - 0.1, 50.0),
            (41.2, 46.4), (42.4, 44.6)]


TORSO_SEATED = torso_outline()


def check_fit_matches():
    """None if the numbers above still equal the fight sheets' refit (art_source/jordan_fit), else a
    note of what differs (or that the module isn't there)."""
    folder = os.path.join(B.ART, 'jordan_fit')
    if not os.path.exists(os.path.join(folder, 'jfit_body.py')):
        return 'art_source/jordan_fit/jfit_body.py not found'
    if folder not in sys.path:
        sys.path.append(folder)
    import jfit_body as J
    diffs = []
    if (J.NEAR_X, J.FAR_X, J.HEM_Y) != (FIT_NEAR_X, FIT_FAR_X, FIT_HEM_Y):
        diffs.append('side seams / hem')
    if J.torso_outline(0) != torso_outline(FIT_HEM_Y):
        diffs.append('torso outline')
    if (J.NEAR_ROOT, J.NEAR_COLLAR, J.NEAR_SHOULDER) != (FIT_NEAR['root'], FIT_NEAR['collar'], FIT_NEAR['shoulder']):
        diffs.append('near sleeve')
    if (J.FAR_ROOT, J.FAR_COLLAR, J.FAR_SHOULDER) != (FIT_FAR['root'], FIT_FAR['collar'], FIT_FAR['shoulder']):
        diffs.append('far sleeve')
    if J.DANDRUFF != FIT_DANDRUFF:
        diffs.append('dandruff')
    return ('differs from jordan_fit: ' + ', '.join(diffs)) if diffs else None


def _shade_tee(part, band_y, dy):
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):
        lo, hi = B.span(part, y)
        t = (x - lo) / max(1, hi - lo)
        ramp = pink if y >= band_y else red
        k = ramp['base']
        if t <= 0.06:
            k = ramp['lit']
        elif t >= 0.95:
            k = ramp['deep']
        elif t >= 0.76:
            k = ramp['shade']
        elif y < band_y and 0.1 <= t <= 0.24 and 46 + dy <= y <= 52 + dy:
            k = ramp['lit']
        part[(x, y)] = k


def _m(x, y, dx, dy):
    """One build-coordinate pixel of the approved rig -> this mirrored, moved space."""
    return (M(x + B.ANCHOR_SHIFT) + dx, y + dy)


def tee(dx=DX, dy=DY):
    part = B.fill(B.poly(mb(TORSO_SEATED, dx, dy)), 'R')
    collar = {M(x + B.ANCHOR_SHIFT) + dx: y + dy for x, y in V.COLLAR.items()}     # v2's own collar
    for x, yc in collar.items():
        for y in range(10, yc):
            part.pop((x, y), None)
    band_y = V.BAND_Y + dy
    _shade_tee(part, band_y, dy)
    for x, yc in collar.items():
        if (x, yc) in part:
            part[(x, yc)] = '1'
    # the seam where the red meets the pink, either side of the print (jfit_body.shirt's rule)
    p0, p1 = sorted((_m(PRINT_X0, 0, dx, dy)[0], _m(PRINT_X1, 0, dx, dy)[0]))
    for (x, y) in list(part):
        if y == band_y and (x < p0 or x > p1):
            part[(x, y)] = 'k'
    # the print the right way round, on the same columns (it is centred on the approved's column 48),
    # its two side outline columns left off as the v2 rig leaves them (jv2_body.PRINT_CROP_COLS)
    rows = B.rows_of(B.rig_torso.PRINT)
    for q, k in B.amap(rows, p0, V.PRINT_AT[1] + dy).items():
        if q[0] - p0 in V.PRINT_CROP_COLS:
            continue
        if q in part:
            part[q] = k
    # sitting: the fitted cloth creases where it folds over his lap, a crease from the hem's rumple
    for (x, y) in ((43, 65), (44, 65), (45, 66), (46, 66), (47, 66), (52, 66), (53, 66), (52, 67)):
        q = _m(x, y, dx, dy)
        if part.get(q) in ('P', 'Q'):
            part[q] = 'q'
    for (x, y) in ((44, 64), (45, 65), (53, 65)):
        q = _m(x, y, dx, dy)
        if part.get(q) == 'P':
            part[q] = 'Q'
    # scruff: the drip off the collar and the smudge on the pink (v2's, same pixels, mirrored)
    for (x, y) in ((55, 46), (56, 46), (56, 47)):
        q = _m(x, y, dx, dy)
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for (x, y) in ((54, 66), (55, 66), (55, 67)):
        q = _m(x, y, dx, dy)
        if q in part and part[q] != 'k':
            part[q] = 'c'
    for (x, y), k in FIT_DANDRUFF.items():
        q = _m(x, y, dx, dy)
        if part.get(q) in ('R', 'T', 'V', 'v'):
            part[q] = k
    return part


def neck(dx=DX, dy=DY, hx=3):
    n = mpart(V.neck(hx), dx, dy)
    B.rim(n, 'd', -1, 0, only='cb')
    B.rim(n, 'b', 1, 0, only='cd')
    return n


def jeans_limb(segs, knobs=()):
    """Loose denim on a thin leg: capsules, lit along the top and left, dark underneath and right."""
    shape = set()
    for (p0, p1, r0, r1) in segs:
        shape |= B.capsule(p0, p1, r0, r1)
    for (cx, cy, r) in knobs:
        shape |= B.ellipse(cx, cy, r, r)
    part = B.fill(shape, 'N')
    B.rim(part, 's', -1, 0)
    B.rim(part, 'S', -1, 0, only='s')
    B.rim(part, 's', 0, -1, only='N')
    B.rim(part, 'n', 1, 0)
    B.rim(part, 'n', 0, 1, only='N')
    return part


def legs():
    """Seated: thin thighs over the seat to bony knees, shins down to the floor, the slack hems
    bunched at the ankles. SKINNY since 2026-09-28: the same joints, the jeans about a pixel thinner
    (the thighs 0.6 off the radius, the shins 0.5, the knees and the bunched hems 0.4)."""
    cv = B.Canvas(96, 96)
    far_thigh = jeans_limb([((49.5, 61.5), (39.5, 67.8), 2.4, 2.0)], knobs=((38.8, 68.2, 2.0),))
    far_shin = jeans_limb([((38.6, 69.5), (37.6, 84.5), 1.6, 1.5), ((37.6, 84.5), (37.4, 87.0), 2.2, 2.5)])
    near_thigh = jeans_limb([((55.5, 63.6), (45.4, 70.6), 2.7, 2.2)], knobs=((44.6, 71.0, 2.1),))
    near_shin = jeans_limb([((44.4, 72.4), (43.6, 87.5), 1.7, 1.6), ((43.6, 87.5), (43.4, 90.0), 2.3, 2.6)])
    cv.stamp(far_shin)
    cv.stamp(far_thigh)
    cv.stamp(near_shin)
    cv.stamp(near_thigh)
    px = cv.px
    for q in ((39, 67), (40, 67), (45, 70), (46, 70)):          # the kneecaps catch the light
        if px.get(q) in ('N', 'n'):
            px[q] = 's'
    for pts in (((36, 84), (38, 85), (39, 84)), ((42, 87), (44, 88), (45, 87))):   # the stacked hems
        for a, b in zip(pts, pts[1:]):
            for q in B.line(a[0], a[1], b[0], b[1]):
                if px.get(q) == 'N':
                    px[q] = 'n'
    return px


def shoes():
    """The approved sneakers, mirrored to point left, under the ankles; the heel's lit back edge
    (now facing away from the light) put in shadow."""
    far, near = V.shoes()
    out = []
    for s, ax, ay in ((far, 37.4, 87.6), (near, 43.4, 90.6)):
        m = {(M(x + B.ANCHOR_SHIFT), y): k for (x, y), k in s.items()}
        xs = [x for (x, y) in m]
        ys = [y for (x, y) in m]
        dx = int(round(ax - (max(xs) - 3)))
        dy = int(round(ay + 3 - max(ys)))
        m = {(x + dx, y + dy): k for (x, y), k in m.items()}
        hx = max(x for (x, y) in m if m[(x, y)] != 'k')
        for (x, y), k in list(m.items()):
            if x == hx and k == '2':
                m[(x, y)] = '1'
        out.append(m)
    return out


#HEADSET, PULLED DOWN ROUND HIS NECK

# Pulled down round his neck: the band sits round the back of his neck just under his beard, the cups
# rest on his collarbones either side. The near cup (his left, screen-right) turns its outer face to us,
# the pink light ring round its dark middle; the far cup (screen-left) shows edge-on under his beard.
CUP_NEAR = [
    ".kkkkk.",
    "k32222k",
    "k2QPPqk",
    "kQ111qk",
    "kP111qk",
    "k2qqq1k",
    ".kkkkk.",
]
CUP_FAR = [
    ".kkk.",
    "k332k",
    "kQ22k",
    "kP21k",
    "kq11k",
    ".kkk.",
]


def headset(dx=DX, dy=DY):
    """(near cup, far cup, band) as parts, in the mirrored 96-space."""
    nx, ny = 48 + dx, 40 + dy          # about the base of his neck, under the chin
    near = B.amap(B.rows_of(CUP_NEAR), nx + 5, ny - 1)
    far = B.amap(B.rows_of(CUP_FAR), nx - 10, ny - 2)
    band = {}
    for x in range(nx - 7, nx + 7):
        band[(x, ny)] = '3' if x < nx - 2 else '2'
        band[(x, ny + 1)] = '1'
    return near, far, band


#HANDS (drawn for this view: lit from the upper left)

WAVE = [                    # his right hand up, palm to us, fingers spread, thumb toward his face
    ".k.k.k...",
    "kekekdk..",
    "kekedck..",
    "kdedddk..",
    "kddddddkk",
    "kcddddddk",
    "kcddddcdk",
    ".kcddcck.",
    "..kcddk..",
    "..kcdck..",
]
POINT = [                   # his right hand stabbing a finger left: index out, the rest curled
    ".........kkkk.",
    "kkkkkkkkkdedk.",
    "keeeeddddddcck",
    "kkkkkkkkkcddck",
    ".......kbcdcbk",
    ".......kkbcbk.",
    "........kkkk..",
]
FIST = [                    # his left fist clenched at his chest (in shade), knuckles to us
    ".kkkkkk.",
    "kdcdcdck",
    "kdcdcdbk",
    "kccccbbk",
    "kkkkcbbk",
    ".kdcckk.",
    "..kkkk..",
]
REST = [                    # his left hand draped over the armrest's end (in shade)
    ".kkkk.",
    "kcddck",
    "kccdck",
    "kbccbk",
    ".kbbk.",
    "..kk..",
]


def _unit(dx, dy):
    import math
    ln = math.hypot(dx, dy) or 1.0
    return dx / ln, dy / ln


def sleeve_outline(root, elbow, collar, shoulder, outward, length=5.2, half=2.5):
    """jfit_body.sleeve_outline (the v2 rig's, jv2_body.sleeve_outline), as it is: from the collar end
    of the shoulder, along the shoulder line, down the outer side of the arm a pixel clear of it, across
    the hem `length` down the arm, back up the inner side to the armpit and up the seam. `length` and
    `half` are the fitted tee's measures; the skinny sleeve is SLEEVE_LEN of that length and 0.5
    tighter (jv2_body.SLEEVE_LEN / SLEEVE_HALF)."""
    length = length * V.SLEEVE_LEN
    half = V.SLEEVE_HALF + (half - 2.5)
    dx, dy = _unit(elbow[0] - root[0], elbow[1] - root[1])
    ox, oy = -dy * outward, dx * outward
    ix, iy = -ox, -oy
    rx, ry = root

    def at(s_, w, sx, sy):
        return (rx + dx * s_ + sx * w, ry + dy * s_ + sy * w)
    top = at(0.0, half, ox, oy)
    out_mid = at(length * 0.5, half, ox, oy)
    out_hem = at(length, half, ox, oy)
    in_hem = at(length, half, ix, iy)
    pit = at(length * 0.3, half + 0.2, ix, iy)
    seam = ((pit[0] + collar[0]) / 2.0 + ix * 0.6, (pit[1] + collar[1]) / 2.0 + iy * 0.6)
    return [collar] + list(shoulder) + [top, out_mid, out_hem, in_hem, pit, seam], (out_hem, in_hem)


def render_sleeve(pts, hem, lit):
    """jfit_body.sleeve: red, lit on the side toward the light, its dark underside, the trim."""
    s = B.fill(B.poly(pts), 'R')
    B.rim(s, 'T' if lit else 'R', -1, 0)
    B.rim(s, 'V', 1, 0)
    B.rim(s, 'v', 0, 1, only='RV')
    B.stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


def sleeve(side, elbow, dx=DX, dy=DY):
    """The fitted sleeve on this side ('far' = screen-left, his right arm; 'near' = screen-right, his
    left), jordan_fit's geometry mirrored: the outline is built on mirrored points, so its lit rim
    still falls on its left, toward the light."""
    spec = FIT_FAR if side == 'far' else FIT_NEAR

    def mp(q):
        return (M(q[0] + B.ANCHOR_SHIFT) + dx, q[1] + dy)
    outward = 1 if side == 'far' else -1          # a mirror turns the arm's normal round
    pts, hem = sleeve_outline(mp(spec['root']), elbow, mp(spec['collar']), [mp(q) for q in spec['shoulder']],
                              outward, length=spec['length'])
    return render_sleeve(pts, hem, lit=(side == 'far'))


def shoulders(dx=DX, dy=DY):
    """Where each upper arm leaves its fitted sleeve (mirrored 96-space): far (screen-left), near."""
    fr, nr = FIT_FAR['root'], FIT_NEAR['root']
    return ((M(fr[0] + B.ANCHOR_SHIFT) + dx, fr[1] + dy), (M(nr[0] + B.ANCHOR_SHIFT) + dx, nr[1] + dy))


def far_arm(pose, dx=DX, dy=DY):
    """His right arm (screen-left, the lit side), as [(part, outline)] back to front."""
    sx, sy = shoulders(dx, dy)[0]
    if pose == 'wave':
        el, hand_at = (sx - 8.4, sy + 4.4), (sx - 18.0, sy - 14.0)
        arm = B.limb([((sx, sy), el, 1.5, 1.4), (el, (hand_at[0] + 3.6, hand_at[1] + 8.2), 1.4, 1.25)],
                     knobs=((el[0], el[1], 1.8),))
        hand = B.close_gaps(B.amap(B.rows_of(WAVE), int(round(hand_at[0])), int(round(hand_at[1]))))
    else:   # 'point'
        el, hand_at = (sx - 8.4, sy + 1.6), (sx - 25.0, sy - 3.0)
        arm = B.limb([((sx, sy), el, 1.5, 1.4), (el, (hand_at[0] + 11.0, hand_at[1] + 3.0), 1.4, 1.3)],
                     knobs=((el[0], el[1], 1.8),))
        hand = B.close_gaps(B.amap(B.rows_of(POINT), int(round(hand_at[0])), int(round(hand_at[1]))))
    sl = sleeve('far', el, dx, dy)
    return [(arm, True), (sl, True), (hand, False)]


def near_arm(pose, dx=DX, dy=DY):
    """His left arm (screen-right, in shade), as [(part, outline)] back to front."""
    sx, sy = shoulders(dx, dy)[1]
    if pose == 'rest':
        el, hand_at = (sx + 3.6, sy + 9.0), (sx - 4.0, sy + 13.0)
        arm = B.limb([((sx, sy), el, 1.5, 1.4), (el, (hand_at[0] + 3.0, hand_at[1] + 1.0), 1.4, 1.3)],
                     knobs=((el[0], el[1], 1.8),), base='c', lit='d', shade='b')
        hand = B.close_gaps(B.amap(B.rows_of(REST), int(round(hand_at[0])), int(round(hand_at[1]))))
    else:   # 'fist'
        el, hand_at = (sx + 3.0, sy + 9.4), (sx - 6.0, sy + 0.6)
        arm = B.limb([((sx, sy), el, 1.5, 1.4), (el, (hand_at[0] + 4.0, hand_at[1] + 5.0), 1.4, 1.3)],
                     knobs=((el[0], el[1], 1.8),), base='c', lit='d', shade='b')
        hand = B.close_gaps(B.amap(B.rows_of(FIST), int(round(hand_at[0])), int(round(hand_at[1]))))
    sl = sleeve('near', el, dx, dy)
    return [(arm, True), (sl, True), (hand, False)]


#EFFECTS

ANGER = [                   # the cross-popping vein, Matt's approved mark: '.' keeps the hair under it
    "..kk.kk..",
    ".kTRkRRk.",
    "kTRk.kRVk",
    "kRk...kVk",
    ".k.....k.",
    "kRk...kVk",
    "kRRk.kRVk",
    ".kRRkRVk.",
    "..kk.kk..",
]
STEAM = [                   # a puff (no keyline: an effect)
    "..W0..",
    ".W00W.",
    "W0099W",
    ".999W.",
    "..99..",
]
STEAM_S = [
    ".W0.",
    "W009",
    ".99.",
]


#FRAMES

def chair_back(cv):
    parts = {}
    for n, p, d in C.solids(YAW):
        if n in ('back', 'seat', 'pad-1', 'pad+1', 'bolster-1', 'bolster+1'):
            C.pad(p)
        parts[n] = (p, d)
    for n in sorted(parts, key=lambda n: -parts[n][1]):
        cv.stamp(parts[n][0])
    for q, k in C.decals(YAW).items():
        if q in parts['back'][0] and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = k
    return parts


def build(face, far_pose, near_pose, flush=False, lean=0, fx_on=False):
    cv = B.Canvas(B.FW, B.FH)
    chair_back(cv)
    at = lambda p: B.shift(p, *B.OFF)  # noqa: E731
    dx, dy = DX - lean, DY
    for s in shoes():
        cv.stamp(at(s), outline=False)
    cv.stamp(at(legs()), outline=False)
    far = far_arm(far_pose, dx, dy)
    cv.stamp(at(far[0][0]))
    cv.stamp(at(far[1][0]))                   # the far sleeve hangs behind the tee, as jordan_fit stamps it
    cv.stamp(at(neck(dx, dy)))
    cv.stamp(at(tee(dx, dy)))
    cup_n, cup_f, band = headset(dx, dy)
    cv.stamp(at(band))
    cv.stamp(at(cup_f), outline=False)
    hd = head(face, 3, 2, dx, dy, flush=flush)
    cv.stamp(at(hd), outline=False)
    cv.stamp(at(cup_n), outline=False)
    cv.stamp(at(far[2][0]), outline=False)
    for part, ol in near_arm(near_pose, dx, dy):
        cv.stamp(at(part), outline=ol)
    fx = set()
    if fx_on:
        x0 = min(x for x, y in hd) + B.OFF[0]
        x1 = max(x for x, y in hd) + B.OFF[0]
        y0 = min(y for x, y in hd) + B.OFF[1]
        # the vein pops on the dark back of his hair; steam blows off either side of his head
        for q, k in B.amap(B.rows_of(ANGER), x1 - 12, y0 + 6).items():
            cv.px[q] = k
        for rows, sx, sy in ((STEAM, x0 - 6, y0 + 14), (STEAM_S, x0 - 9, y0 + 10),
                             (STEAM, x1 + 2, y0 + 12), (STEAM_S, x1 + 5, y0 + 8)):
            for q, k in B.amap(B.rows_of(rows), sx, sy).items():
                if q not in cv.px:
                    cv.px[q] = k
                    fx.add(q)
    return cv, fx


def builders():
    return [lambda: build('friendly_shut', 'wave', 'rest'),
            lambda: build('friendly_open', 'wave', 'rest'),
            lambda: build('glare_shut', 'point', 'fist', lean=1, fx_on=True),
            lambda: build('glare_open', 'point', 'fist', lean=1, fx_on=True)]


def frames():
    return [(cv.px, fx) for cv, fx in (b() for b in builders())]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: round(v, 4) if isinstance(v, float) else v for k, v in st.items()},
              {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()})
