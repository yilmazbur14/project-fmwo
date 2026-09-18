"""Carter's clone rush: a driving three-quarter lunge travelling RIGHT.

Why three-quarter and not a true profile: the entrance already proved that a
90-degree Carter collapses - the skull goes to a blank dome and the beard reads
as a lump glued to the jaw (see intro_profile.pivot_treatment's note, which is
why that beat ships as a back-lit silhouette).  The clones are the moment the
player has to read WHO is coming at them, five times in a row, at speed.  So the
head stays the approved front head - big, bald, orange beard, two red slits -
and the whole direction is carried by the body: a side-on torso pitched forward,
one arm punched out to the right and the other trailing, the rear leg driving
back, the gi tails and the juzu whipping behind him.

Every frame is authored as a joint dictionary rather than lerped, so the strike
can hold its fist position while the body catches up to it.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, erode,
                 poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, band, gi_fade,
                 bayer)
import parts as P
import combat_lib as CL
import combat_head as CH
from combat_lib import cyl, joint, limb, foot_at, hem_cut, tail, rot_pts
from render import cylm, sphm, seg, dot

FLOOR = 95


# ---------------------------------------------------------------- poses
# head = (dx, dy) applied to the approved head masks
# chest / pelvis = torso capsule ends, with radii
# near = the striking arm (drawn last, closest to camera)
# far  = the trailing arm
# lead = the forward leg, rear = the driving leg
# foot angles: 0 = toes pointing right

# Two things carry this pose, and both were found the hard way.
#
# The trailing arm is thrown back and UP, not down alongside the ribs.  Down,
# it lands inside the torso and the whole figure silhouettes as one barrel;
# up, it opens a wedge of air between arm, head and chest.
#
# The rear leg trails BACKWARD, nearly level with the hips, instead of being
# planted out to the side.  Splayed, both legs plus the trousers fused into one
# trapezoid across the bottom of the frame and the pose read as a squat.  Trailed,
# the whole area under him is empty, only the lead foot touches the floor, and
# the silhouette becomes an arrow pointing where he is going.

# Frame 0 is an APPROACH, not a wind-up.  A crouching anticipation pose put a
# standing squat at the head of a sheet that is otherwise pure travel, and the
# clones have no time for anticipation anyway - they are already moving when
# they enter the frame.  So this is simply an earlier moment on the same arc:
# arm cocked by the ribs, rear leg just off the floor.
COIL = dict(
    head=(5, 6), face=('glare', 1, 0),
    chest=(50.0, 57.0, 12.6), pelvis=(39.0, 71.0, 10.0),
    near=((54.0, 58.0), (47.0, 63.0), (42.0, 67.0), (39.0, 69.0)),
    far=((46.0, 59.0), (37.0, 52.0), (29.0, 47.0), (25.4, 44.4)),
    lead=((44.0, 69.0), (54.0, 79.0), (59.0, 91.0), 4.0),
    rear=((36.0, 72.0), (25.0, 76.0), (15.0, 79.0), 162.0),
    tails=(174.0, 18.0), sway=-3.0, streak=(9, 18), k=0,
)

DRIVE = dict(
    head=(8, 4), face=('glare', 1, 0),
    chest=(53.0, 55.0, 12.4), pelvis=(40.0, 70.0, 9.8),
    near=((57.0, 56.0), (66.0, 59.0), (73.0, 61.0), (76.0, 62.0)),
    far=((49.0, 57.0), (39.0, 50.0), (31.0, 44.0), (27.4, 41.4)),
    lead=((44.0, 68.0), (54.0, 78.0), (59.0, 90.0), 6.0),
    rear=((36.0, 71.0), (24.0, 73.0), (13.0, 74.0), 180.0),
    tails=(178.0, 25.0), sway=-5.0, streak=(14, 26), k=1,
)

STRIKE = dict(
    head=(11, 1), face=('glare', 2, 0),
    chest=(56.0, 54.0, 12.0), pelvis=(40.0, 69.0, 9.5),
    near=((60.0, 54.0), (73.0, 58.0), (82.0, 61.0), (86.0, 62.4)),
    far=((52.0, 56.0), (42.0, 48.0), (34.0, 42.0), (30.4, 39.4)),
    lead=((44.0, 68.0), (52.0, 79.0), (58.0, 90.0), 6.0),
    rear=((36.0, 70.0), (24.0, 67.0), (14.0, 66.0), 186.0),
    tails=(184.0, 29.0), sway=-6.0, streak=(18, 32), k=2,
)

FOLLOW = dict(
    head=(12, 1), face=('glare', 2, 0),
    chest=(58.0, 54.0, 11.8), pelvis=(44.0, 69.0, 9.5),
    near=((62.0, 54.0), (74.0, 58.0), (82.0, 61.0), (86.0, 62.4)),
    far=((54.0, 57.0), (45.0, 52.0), (37.0, 50.0), (33.4, 49.4)),
    lead=((48.0, 68.0), (56.0, 79.0), (62.0, 90.0), 4.0),
    rear=((40.0, 70.0), (29.0, 74.0), (19.0, 79.0), 152.0),
    tails=(176.0, 24.0), sway=-4.0, streak=(12, 24), k=3,
)

RUSH = [COIL, DRIVE, STRIKE, FOLLOW]

# where the punch bites - the pixel the impact effect should sit on
IMPACT = [(36, 70), (80, 62), (91, 63), (93, 63)]


# ---------------------------------------------------------------- masks

def torso_m(p):
    a = (p['chest'][0], p['chest'][1])
    b = (p['pelvis'][0], p['pelvis'][1])
    return cyl(a, b, p['chest'][2], p['pelvis'][2])


def _axis(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return dx / L, dy / L, -dy / L, dx / L, L


def fist_m(wr, fi, r):
    """A fist, not a ball: a knuckle mass stretched along the punch with a
    thumb lump riding on top of it.  A plain circle on the end of a cylinder
    read as a rolling pin."""
    ux, uy, nx, ny, _ = _axis(wr, fi)
    ang = math.degrees(math.atan2(uy, ux))
    knuck = ell(fi[0], fi[1], r + 1.1, r + 0.1, ang)
    thumb = ell(fi[0] - ux * 2.0 - nx * 2.6, fi[1] - uy * 2.0 - ny * 2.6,
                r * 0.66, r * 0.58, ang)
    return union(knuck, thumb)


def arm_m(A, r=(7.0, 5.9, 5.2)):
    sh, el, wr, fi = A
    up = cyl(sh, el, r[0], r[1])
    fo = cyl(el, wr, r[1], r[2])
    fist = fist_m(wr, fi, r[2])
    return up, fo, fist, union(joint(el, r[1]), union(union(up, fo), fist))


def wrap_m(A, r=(7.0, 5.9, 5.2)):
    """Cream binding on the wrist and the fist only.

    Starting the wrap halfway up the forearm turned the whole arm into one
    cream tube - it read as a plaster cast rather than a bound hand, and it
    hid the forearm muscle that sells a punch.  The approved sheet binds the
    last third and no more."""
    sh, el, wr, fi = A
    mid = (el[0] + (wr[0] - el[0]) * 0.70, el[1] + (wr[1] - el[1]) * 0.70)
    _, fo, fist, _ = arm_m(A, r)
    return union(inter(cyl(mid, fi, r[2] + 1.0), fo), fist)


def leg_m(L, r=(9.4, 8.2, 5.7, 5.2), fs=(13.0, 4.6, 3.4)):
    hip, knee, ank, ang = L
    th = cyl(hip, knee, r[0], r[1])
    sh = cyl(knee, ank, r[2], r[3])
    ft = foot_at(ank, ang, fs[0], fs[1], fs[2])
    return th, sh, ft, union(union(union(th, sh), joint(knee, r[1] - 1.4)), ft)


REAR_R = (7.6, 6.8, 4.8, 4.2)
REAR_F = (9.4, 3.0, 2.0)


def pants_leg(L, r, t_end=0.30):
    """One baggy trouser leg: the thigh plus the top of the shin, torn off
    square across the limb rather than along a screen row.  Kept tight - at
    +2px all round both legs and the hips fused into one navy diaper."""
    hip, knee, ank, _ = L
    m = union(cyl(hip, knee, r[0] + 1.2, r[1] + 1.4),
              cyl(knee, ank, r[2] + 1.8, r[3] + 1.0))
    return sub(m, CL.cut_beyond(knee, ank, t_end, amp=2.2, step=3.0))


def pants_m(p):
    cx, cy, cr = p['pelvis']
    ax, ay, _ = p['chest']
    hips = cyl((cx + (ax - cx) * 0.26, cy + (ay - cy) * 0.26),
               (cx - (ax - cx) * 0.16, cy - (ay - cy) * 0.16), cr + 1.2, cr + 0.6)
    return union(union(hips, pants_leg(p['lead'], (9.4, 8.2, 5.7, 5.2))),
                 pants_leg(p['rear'], REAR_R, 0.50))


def belt_ang(p):
    """A belt square across a torso pitched 45 degrees is itself at 45 degrees,
    which is geometrically right and reads completely wrong - it becomes a
    bandolier across his chest.  A real belt rides the hips and stays close to
    level however far the ribcage leans over it, so the perpendicular is pulled
    most of the way back toward horizontal."""
    cx, cy, _ = p['pelvis']
    ax, ay, _ = p['chest']
    a = math.degrees(math.atan2(cy - ay, cx - ax)) + 90.0
    a = (a + 180.0) % 360.0 - 180.0
    if a > 90.0:
        a -= 180.0
    elif a < -90.0:
        a += 180.0
    return a * 0.42


def belt_m(p):
    """Rope belt sitting across the hips.  Kept narrow and clipped to the body
    - at full width it read as a sash."""
    cx, cy, cr = p['pelvis']
    return poly(rot_pts([(cx - cr - 3.0, cy - 2.4), (cx + cr + 3.0, cy - 2.4),
                         (cx + cr + 3.0, cy + 2.6), (cx - cr - 3.0, cy + 2.6)],
                        cx, cy, belt_ang(p)))


def cap_m(p):
    """The torn-off sleeve stumps: only the crown of each deltoid, ending in a
    ragged tear a little way down the upper arm."""
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    near = union(ell(sx - 1.2, sy - 1.0, 10.4, 8.4),
                 ell(sx - 3.6, sy - 3.8, 8.6, 6.0))
    far = union(ell(fx + 1.0, fy - 1.0, 9.4, 7.6),
                ell(fx + 3.0, fy - 3.4, 7.8, 5.4))
    near = sub(near, CL.cut_beyond(p['near'][0], p['near'][1], 0.44, amp=2.0,
                                   step=2.6))
    far = sub(far, CL.cut_beyond(p['far'][0], p['far'][1], 0.42, amp=1.8,
                                 step=2.6))
    return union(near, far)


def _torso_frame(p):
    """(centre, unit down the body, unit out of the chest front, radius)"""
    cx, cy, cr = p['chest']
    px_, py_, _ = p['pelvis']
    dx, dy = px_ - cx, py_ - cy
    L = math.hypot(dx, dy) or 1.0
    return (cx, cy), (dx / L, dy / L), (-dy / L, dx / L), cr, L


def _proj(p):
    """signed distance out of the chest front, per pixel."""
    (cx, cy), _, (nx, ny), _, _ = _torso_frame(p)
    return [[(x + 0.5 - cx) * nx + (y + 0.5 - cy) * ny for x in range(W)]
            for y in range(H)]


def jacket_m(p, tor):
    """The gi seen from the side: a closed panel down his back, the open front
    edge as a narrow lapel, and a torn sleeve cap on each deltoid - with bare
    chest and ab grid showing in the strip between them.

    Both earlier attempts failed at this join.  Cutting a half plane through
    the torso centre stripped the gi off him completely; wrapping the whole
    grown torso put him in a t-shirt and buried the anatomy.  A back panel plus
    a lapel is what intro_profile does, and it is what reads."""
    (cx, cy), _, _, cr, L = _torso_frame(p)
    px_, py_, _ = p['pelvis']
    pr = _proj(p)
    shell = grow(tor, 1)
    back, lapel = empty(), empty()
    for y in range(H):
        for x in range(W):
            if not shell[y][x]:
                continue
            d = pr[y][x]
            if d < -1.0:
                back[y][x] = True
            elif d > cr - 4.2:
                lapel[y][x] = True
    j = union(union(back, lapel), cap_m(p))
    return sub(j, CL.cut_beyond((cx, cy), (px_, py_), 1.10, amp=2.6, step=2.8))


def tails_m(p):
    """Torn gi tails whipping out behind him - the cheapest speed in the set.

    Rooted on the trailing edge of the hips rather than the pelvis centre, so
    they leave the silhouette into open air instead of piling more bulk onto a
    body that is already the widest thing in the frame."""
    (cx, cy), (ux, uy), (nx, ny), cr, _ = _torso_frame(p)
    px_, py_, pr = p['pelvis']
    ang, ln = p['tails']
    # step back off the hip, away from the chest front
    rx, ry = px_ - nx * pr * 0.55, py_ - ny * pr * 0.55
    m = empty()
    for i, (ox, oy, da, f, w) in enumerate((
            (0.0, -5.0, -16.0, 1.00, 6.6), (-1.0, 0.0, 4.0, 0.84, 5.8),
            (1.0, 4.0, 22.0, 0.66, 4.6))):
        m = union(m, tail((rx + ox, ry + oy), ang + da, ln * f, w, 1.4,
                          curl=0.18 * (1 if i % 2 else -1)))
    return m


def beads_m(p):
    """the juzu thrown back over his shoulder by the acceleration."""
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    sway = p['sway']
    pts = []
    for i in range(9):
        t = i / 8.0
        x = fx - 3.0 + (sx - fx + 5.0) * t + sway * math.sin(math.pi * t) * 1.6
        y = fy - 6.0 + math.sin(math.pi * t) * 6.4 + sway * 0.5
        pts.append((x, y))
    m = empty()
    for cx, cy in pts:
        m = union(m, ell(cx, cy, 2.4, 2.4))
    return m, pts


def body_mask(p):
    tor = torso_m(p)
    _, _, _, na = arm_m(p['near'])
    _, _, _, fa = arm_m(p['far'], (6.4, 5.4, 4.7))
    _, _, _, ll = leg_m(p['lead'])
    _, _, _, rl = leg_m(p['rear'], REAR_R, REAR_F)
    hd, er, bd = CH.head_masks(*p['head'])
    return union(union(union(union(tor, na), union(fa, ll)),
                       union(union(rl, hd), union(er, bd))),
                 union(union(jacket_m(p, tor), pants_m(p)), tails_m(p)))


# ---------------------------------------------------------------- draw

def draw(p):
    cv = Canvas()
    hdx, hdy = p['head']
    tor = torso_m(p)

    # ---- far side first, two ramp steps down so it sits behind him
    fth, fsh, fft, fall = leg_m(p['rear'], REAR_R, REAR_F)
    low = union(fsh, fft)
    cv.part(low, 'skin', ('dist', 5.0), TH_HARD, bias=2)
    cv.outline(low)
    _toes(cv, p['rear'], REAR_F[0], REAR_F[1])

    fup, ffo, ffi, fa = arm_m(p['far'], (6.4, 5.4, 4.7))
    fwr = wrap_m(p['far'], (6.4, 5.4, 4.7))
    cv.part(sub(fa, fwr), 'skin', cylm(p['far'][0], p['far'][2], 7.6), TH_HARD,
            bias=1)
    cv.part(inter(fa, fwr), 'rope', ('dist', 5.0), TH_HARD2, bias=1)
    cv.outline(fa)
    _arm_detail(cv, p['far'], ffi, lit='t', dark='W', knuck='i', band='l')

    # ---- lead leg and the trousers over both thighs
    lth, lsh, lft, lall = leg_m(p['lead'])
    cv.part(lft, 'skin', ('dist', 4.2), TH_HARD, bias=0)
    cv.part(sub(lsh, lft), 'skin', cylm(p['lead'][1], p['lead'][2], 6.2),
            TH_HARD, bias=0)
    cv.outline(union(lft, lsh))
    _toes(cv, p['lead'])

    trs = pants_m(p)
    cv.part(trs, 'gi', ('dist', 9.6), TH_HARD2, bias=0)
    cv.recolor(inter(trs, lth), 'gi', cylm(p['lead'][0], p['lead'][1], 11.2),
               TH_HARD2, bias=0)
    cv.recolor(inter(trs, fth), 'gi', cylm(p['rear'][0], p['rear'][1], 9.4),
               TH_HARD2, bias=1)
    cv.outline(trs)
    # the navy-to-violet fall-off is anchored to the POSE, not to fixed rows:
    # a kneeling Carter lives entirely below row 60, and a fixed range turned
    # his whole gi violet the moment he went down.
    py = p['pelvis'][1]
    gi_fade(cv, trs, py + 2.0, py + 16.0)
    _fold(cv, p['lead'][0], p['lead'][1], 'a', 2.0)
    _fold(cv, p['rear'][0], p['rear'][1], 'e', -2.0)

    # ---- the gi tails, behind the body
    if p.get('tails'):
        tl = sub(tails_m(p), grow(union(tor, union(lall, fall)), 1))
        cv.part(tl, 'gi', ('dist', 4.6), TH_HARD2, bias=1)
        cv.outline(tl)
        gi_fade(cv, tl, p['chest'][1] + 2.0, p['pelvis'][1] + 10.0)

    # ---- torso
    cv.part(tor, 'skin', _across(p, 16.0), TH_HARD, bias=-1)
    cv.outline(tor)
    _anatomy(cv, p, tor)

    # ---- juzu swinging behind the shoulders
    if p.get('beads', True):
        bm, bpts = beads_m(p)
        cord = [(int(round(x)), int(round(y))) for x, y in bpts]
        seg(cv, cord, 'k', mirror_too=False, over_only=False)
        for cx, cy in bpts:
            cv.part(ell(cx, cy, 2.4, 2.4), 'bead',
                    sphm(cx - 0.7, cy - 0.8, 3.0, 3.0), TH_HARD, bias=0)
            dot(cv, int(cx - 0.8), int(cy - 0.9), 'G')

    # ---- deltoids, then the gi caps over them
    nup, nfo, nfi, na = arm_m(p['near'])
    sx, sy = p['near'][0]
    dl = union(ell(sx - 1.0, sy + 0.6, 9.4, 8.4), ell(sx - 3.0, sy - 3.4, 7.6, 5.6))
    cv.part(dl, 'skin', sphm(sx - 2.0, sy - 1.0, 12.0, 11.0), TH_HARD, bias=0)
    cv.outline(dl)

    jk = jacket_back_m(p, tor) if p.get('back') else jacket_m(p, tor)
    cv.part(jk, 'gi', ('dist', 7.4), TH_HARD2, bias=0)
    cv.recolor(inter(jk, dl), 'gi', sphm(sx - 2.0, sy - 3.0, 13.0, 11.0),
               TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, p['chest'][1] + 6.0, p['pelvis'][1] + 8.0)
    _gi_light(cv, p, jk)
    if p.get('back'):
        # centre the emblem on the part of the back that the striking arm does
        # NOT cover, or it lands under the shoulder and reads as a red smudge
        _, _, _, na_pre = arm_m(p['near'])
        panel = sub(jk, grow(na_pre, 1))
        sg = inter(mark_m(p, panel), jk)
        cv.part(sg, 'ember', ('dist', 3.2), TH_HARD2, bias=1)
        cv.outline(sg, PALC['9'])
        # a little bloom so it burns rather than sits there as a decal
        for y in range(H):
            for x in range(W):
                if sg[y][x]:
                    continue
                if any(0 <= y + dy < H and 0 <= x + dx < W and sg[y + dy][x + dx]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    c = cv.px[y][x]
                    if c is not None and c != BLACK:
                        cv.px[y][x] = CL.mixc(c, PALC['Y'], 0.45)

    blt = inter(belt_m(p), grow(union(tor, trs), 1))
    cv.part(blt, 'belt', _across(p, 3.6, at='pelvis'), TH_HARD2, bias=0)
    cv.outline(blt)
    _belt_twist(cv, p)

    # ---- head, then the striking arm over it.  The sleeve stump stays on top
    # of the arm, exactly as the profile rig does it - cutting the cap by the
    # arm instead leaves him bare shouldered.
    if p.get('back'):
        CH.draw_back_head(cv, hdx, hdy)
    else:
        CH.draw_head(cv, hdx, hdy, p['face'][0], p['face'][1], p['face'][2],
                     lean=p.get('lean', 0.0), shade=p.get('shade', 0),
                     bloom=p.get('bloom', 0.0))

    na = sub(na, erode(cap_m(p), 1))
    nwr = inter(wrap_m(p['near']), na)
    cv.part(sub(na, nwr), 'skin', cylm(p['near'][0], p['near'][2], 8.6),
            TH_HARD, bias=0)
    cv.part(nwr, 'rope', ('dist', 5.6), TH_HARD2, bias=0)
    cv.recolor(inter(na, nfi), 'rope',
               sphm(p['near'][3][0] - 1.4, p['near'][3][1] - 1.4, 6.2, 6.0),
               TH_HARD2, bias=0)
    cv.outline(na)
    _arm_detail(cv, p['near'], nfi)
    return cv


# ---------------------------------------------------------------- detail

def _across(p, r, at='chest'):
    """a cylinder model lying ACROSS the limb axis, so the body rounds the
    short way instead of down its own length."""
    cx, cy, _ = p[at]
    ax, ay, _ = p['chest' if at == 'pelvis' else 'pelvis']
    dx, dy = cx - ax, cy - ay
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    return cylm((cx - nx * 30, cy - ny * 30), (cx + nx * 30, cy + ny * 30), r)


def _gi_light(cv, p, jk):
    """rim light along the top of the shoulder cap and a crease down the back
    panel, so the navy is not one flat field."""
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    cx, cy, cr = p['chest']
    px_, py_, _ = p['pelvis']
    dx, dy = px_ - cx, py_ - cy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -dy / L, dx / L
    seg(cv, [(int(sx - 8), int(sy - 6)), (int(sx - 1), int(sy - 8)),
             (int(sx + 6), int(sy - 5))], 'a', mirror_too=False)
    seg(cv, [(int(fx - 7), int(fy - 5)), (int(fx + 2), int(fy - 7))], 'b',
        mirror_too=False)
    pts = []
    for t in (0.10, 0.45, 0.85):
        pts.append((int(round(cx + ux * L * t - nx * 6.0)),
                    int(round(cy + uy * L * t - ny * 6.0))))
    seg(cv, pts, 'b', mirror_too=False)
    pts = [(int(round(cx + ux * L * t - nx * 9.0)),
            int(round(cy + uy * L * t - ny * 9.0))) for t in (0.14, 0.5, 0.88)]
    seg(cv, pts, 'a', mirror_too=False)


def _fold(cv, a, b, ch, off):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = []
    for t in (0.18, 0.55, 0.88):
        pts.append((int(round(a[0] + dx * t + nx * off)),
                    int(round(a[1] + dy * t + ny * off))))
    seg(cv, pts, ch, mirror_too=False)


def _toes(cv, L, ln=13.0, hi=4.6):
    """Toe splits, an instep highlight and a sole shadow, all in the foot's own
    frame so a foot pointing backwards gets the same treatment as a planted one.
    Without these a rotated foot is just a slab and the leg ends in a stump."""
    ank, ang = L[2], L[3]
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def at(t, s):
        return (int(round(ank[0] + ca * t - sa * s)),
                int(round(ank[1] + sa * t + ca * s)))
    for t in (ln * 0.54, ln * 0.72, ln * 0.88):
        seg(cv, [at(t, hi * 0.42), at(t, hi * 0.96)], 'w', mirror_too=False)
    seg(cv, [at(-1.0, -hi * 0.42), at(ln * 0.66, -hi * 0.50)], 's',
        mirror_too=False)
    seg(cv, [at(-2.0, hi * 0.98), at(ln * 0.40, hi * 1.02)], 'W',
        mirror_too=False)


def _anatomy(cv, p, tor):
    """pec, ab grid and oblique grooves laid along the pitched torso axis."""
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    dx, dy = px_ - cx, py_ - cy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L            # down the body
    nx, ny = -dy / L, dx / L           # out the chest front

    def at(t, s):
        return (int(round(cx + ux * L * t + nx * s)),
                int(round(cy + uy * L * t + ny * s)))

    # pec: lit on top, hard shadow underneath
    seg(cv, [at(0.02, 2.0), at(0.14, 7.0), at(0.30, 8.6)], 's', mirror_too=False)
    seg(cv, [at(0.06, 1.0), at(0.18, 6.2), at(0.32, 7.4)], 't', mirror_too=False)
    seg(cv, [at(0.34, 1.0), at(0.40, 6.0), at(0.46, 8.0)], 'W', mirror_too=False)
    seg(cv, [at(0.37, 0.6), at(0.43, 5.6), at(0.49, 7.6)], 'w', mirror_too=False)
    # ab grid down the centre line, blocks lit on their upper edge
    for t in (0.50, 0.62, 0.74):
        seg(cv, [at(t, -1.0), at(t, 6.4)], 'w', mirror_too=False)
        seg(cv, [at(t + 0.035, -0.6), at(t + 0.035, 6.0)], 's', mirror_too=False)
    seg(cv, [at(0.46, 2.6), at(0.80, 2.2)], 'w', mirror_too=False)
    # the back edge rolls into shadow
    seg(cv, [at(0.10, -8.0), at(0.45, -9.0), at(0.80, -8.0)], 'W',
        mirror_too=False)
    seg(cv, [at(0.12, -6.4), at(0.46, -7.4), at(0.80, -6.4)], 'w',
        mirror_too=False)
    # obliques
    seg(cv, [at(0.62, 7.4), at(0.78, 5.4)], 'v', mirror_too=False)


def _belt_twist(cv, p):
    cx, cy, cr = p['pelvis']
    ang = math.radians(belt_ang(p))
    ca, sa = math.cos(ang), math.sin(ang)
    for s in (-7.0, -2.0, 3.0, 8.0):
        x0 = int(round(cx + ca * s - sa * 3.0))
        y0 = int(round(cy + sa * s + ca * 3.0))
        x1 = int(round(cx + ca * (s - 2.6) + sa * 3.0))
        y1 = int(round(cy + sa * (s - 2.6) - ca * 3.0))
        seg(cv, [(x0, y0), (x1, y1)], 'r', mirror_too=False)
    seg(cv, [(int(round(cx - ca * cr)), int(round(cy - sa * cr - 2))),
             (int(round(cx + ca * cr)), int(round(cy + sa * cr - 2)))], 'n',
        mirror_too=False)


def _arm_detail(cv, A, fist, lit='s', dark='W', knuck='g', band='j'):
    sh, el, wr, fi = A
    ux, uy, nx, ny, L = _axis(sh, wr)

    def at(t, s):
        return (int(round(sh[0] + ux * L * t + nx * s)),
                int(round(sh[1] + uy * L * t + ny * s)))
    # triceps lit along the top, hard shadow underneath
    seg(cv, [at(0.12, -4.4), at(0.45, -3.8), at(0.74, -3.2)], lit, mirror_too=False)
    seg(cv, [at(0.16, -3.0), at(0.48, -2.6)], 't', mirror_too=False)
    seg(cv, [at(0.14, 4.2), at(0.46, 3.8), at(0.76, 3.2)], dark, mirror_too=False)
    seg(cv, [at(0.18, 3.0), at(0.50, 2.8)], 'w', mirror_too=False)
    # wrap bindings across the forearm
    for t in (0.68, 0.81):
        seg(cv, [at(t, -4.2), at(t, 4.2)], band, mirror_too=False)
    # the fist: knuckle highlights along the leading face, a crease behind them
    fx, fy, gx, gy, _ = _axis(wr, fi)
    for s in (-2.6, 0.2, 2.8):
        dot(cv, int(round(fi[0] + fx * 3.4 + gx * s)),
            int(round(fi[1] + fy * 3.4 + gy * s)), knuck)
        dot(cv, int(round(fi[0] + fx * 1.6 + gx * s)),
            int(round(fi[1] + fy * 1.6 + gy * s)), band)
    seg(cv, [(int(round(fi[0] - fx * 1.0 - gx * 4.0)),
              int(round(fi[1] - fy * 1.0 - gy * 4.0))),
             (int(round(fi[0] + fx * 3.6 - gx * 3.4)),
              int(round(fi[1] + fy * 3.6 - gy * 3.4)))], 'l', mirror_too=False)


# ---------------------------------------------------------------- frames

# Aura roots for the dash: everything streams BACKWARD off him, so the strands
# are rooted on his leading surfaces and blown out to screen-left.  The standing
# sheet's vertical crown would read as hair standing up on a body moving this
# fast, which is exactly wrong.
def dash_specs(p, k, level=1.0):
    (cx, cy), _, _, _, _ = _torso_frame(p)
    hdx, hdy = p['head']
    roots = [
        (38.0 + hdx, 16.0 + hdy, 168.0, 34.0, 9.8),   # off the crown
        (33.0 + hdx, 28.0 + hdy, 176.0, 30.0, 8.6),   # temple
        (36.0 + hdx, 40.0 + hdy, 184.0, 26.0, 7.6),   # jaw
        (cx - 10.0, cy - 2.0, 178.0, 32.0, 10.4),     # shoulder
        (cx - 12.0, cy + 10.0, 186.0, 28.0, 8.8),     # ribs
        (p['pelvis'][0] - 8.0, p['pelvis'][1] + 2.0, 192.0, 24.0, 7.6),
    ]
    out = []
    for i, (rx, ry, ang, ln, w0) in enumerate(roots):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        px_, py_ = -sa, ca
        L = ln * level
        ph = k * math.pi / 2 + i * 1.19
        pts = []
        for f in (0.0, 0.34, 0.70, 1.0):
            off = math.sin(f * math.pi * 1.1) * (2.4 + 2.0 * math.sin(ph)) * \
                (1 if i % 2 else -1)
            pts.append((rx + ca * L * f + px_ * off,
                        ry + sa * L * f + py_ * off - 1.4 * f * f))
        out.append((pts, w0 * level, 1.0))
    return out


def dash_sparks(p, k):
    (cx, cy), _, _, _, _ = _torso_frame(p)
    pts = []
    for i in range(6):
        ph = k * 0.8 + i * 1.7
        x = cx - 18.0 - i * 5.0 + math.sin(ph) * 3.0
        y = cy - 8.0 + i * 5.0 + math.cos(ph * 0.8) * 4.0
        if 1.0 < x < W - 1 and 1.0 < y < H - 1:
            pts.append((x + 0.5, y + 0.5))
    return pts


def frame(i):
    p = RUSH[i]
    body = draw(p)
    bm = body.mask_of()
    k = p['k']
    lv = (0.80, 1.00, 1.00, 0.88)[i]
    cv = CL_compose(body, dash_specs(p, k, lv), dash_sparks(p, k), bm, k)
    # wind lines trailing the way he came from
    rows = [18 + p['head'][1], 30 + p['head'][1], 44, 54, 62, 70, 80, 90]
    CL.streaks(cv, bm, rows, back=-1, ln=p['streak'], seed=k)
    # the leading edge catches the light he is driving into
    _lead_edge(cv, bm, 0.45 + 0.25 * lv)
    if i >= 2:
        # no impact ring is drawn here - the FX pass owns that, and one drawn
        # on the sprite clipped against the frame edge.  Just let the fist
        # throw a little light back onto him.
        fx, fy = p['near'][3]
        CL.point_light(cv, bm, fx, fy, 0.30, reach=22.0)
    return cv


def CL_compose(body, specs, sparks, bm, k):
    import intro_lib as IL
    cv = IL.compose(body, specs, sparks, haze_in=5, haze_out=0, off=k)
    IL.soften(cv, grow(bm, 1), near=13, far=38, seed=k)
    return cv


def _lead_edge(cv, bm, amt):
    """A warm rim down the screen-right edge of every row: he is moving into
    the light of his own aura, and it is the cheapest way to stop a fast sprite
    reading as a flat cut-out."""
    for y in range(H):
        xs = [x for x in range(W) if bm[y][x]]
        if not xs:
            continue
        hi = max(xs)
        c = cv.px[y][hi]
        if c is None:
            continue
        cv.px[y][hi] = CL.mixc(c, PALC['X'], amt) if c != BLACK else c
        if hi - 1 >= 0 and cv.px[y][hi - 1] not in (None, BLACK):
            cv.px[y][hi - 1] = CL.mixc(cv.px[y][hi - 1], PALC['y'], amt * 0.55)


# ---------------------------------------------------------------- back view

def jacket_back_m(p, tor):
    """Seen from behind the gi is closed: one navy field across the back, with
    the torn armholes and the same ragged hem."""
    (cx, cy), _, _, cr, L = _torso_frame(p)
    px_, py_, _ = p['pelvis']
    j = union(grow(tor, 1), cap_m(p))
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    j = sub(j, union(ell(sx - 1.0, sy + 2.0, 5.6, 7.0),
                     ell(fx + 1.0, fy + 2.0, 5.2, 6.6)))
    return sub(j, CL.cut_beyond((cx, cy), (px_, py_), 1.10, amp=2.6, step=2.8))


def mark_m(p, panel=None):
    """The approved trident emblem fitted onto a pitched, foreshortened back.

    The emblem is authored for the full 96-wide standing back view.  Dropped on
    a torso that is only two dozen pixels across it was clipped down to a red
    sliver, so it is scaled to the panel it has to live on first - about three
    quarters of the torso width and half its length - and only then moved into
    place."""
    import intro_sigil
    (cx, cy), (ux, uy), (nx, ny), cr, L = _torso_frame(p)
    sg = intro_sigil.sigil()
    bb = CL.mask_bbox(sg)
    if bb is None:
        return sg
    x0, y0, x1, y1 = bb
    sw, sh = max(1, x1 - x0), max(1, y1 - y0)
    scx, scy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    if panel is not None:
        pb = CL.mask_bbox(panel)
    else:
        pb = None
    if pb:
        px0, py0, px1, py1 = pb
        pw, ph = max(6, px1 - px0), max(8, py1 - py0)
        tx, ty = (px0 + px1) * 0.5, py0 + ph * 0.46
        sx = min(1.0, (pw * 0.80) / sw)
        sy = min(1.0, (ph * 0.62) / sh)
    else:
        tx = cx + ux * L * 0.46
        ty = cy + uy * L * 0.46
        sx = min(1.0, (cr * 1.50) / sw)
        sy = min(1.0, (L * 0.62) / sh)
    sg = CL.scale_mask(sg, sx, sy, scx, scy)
    return CL.shift_mask(sg, int(round(tx - scx)), int(round(ty - scy)))
