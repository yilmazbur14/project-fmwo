"""Draw kaiju frames from the posable rig (kjr): the whole body, the body with its head taken off (the
breath stance's neck stump), the head layer alone, and the spines overlay.

render_body() follows kj_frames2.build() step for step, so the rest pose IS the approved kaiju.
Every render returns (px, fx, info) in frame coordinates (FW x FH, the sprite's pivot at FEET).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
import kjr as R  # noqa: E402

FX_KEYS = set('XKJI8WQPqOY')
LOD_BELOW = 0.42                     # below this share of the fight size, draw the simplified kaiju


def shaded(rig, rest, spec, bias=0.0, seed=None, rim=True, bounce=0.25, **kw):
    part, info = S.shade(R.prims(rig, spec), 'hide', bias=bias, bounce=bounce, **kw)
    if seed is not None:
        R.bumps(rig, rest, spec, part, seed=seed)
        R.scales(rig, rest, spec, part, seed=seed)
    if rim:
        S.rim_light(part)
    return part, info


def render_body(pose=None, sc=R.BASE_SC, head=True, glow=None, flash=False, jaw=0.0, mouth_glow=False,
                halo=False, spark_pts=(), feet=R.FEET, size=(R.FW, R.FH), floor=True, star_sole=False,
                lod=None, sx=1.0, eye='normal'):
    """The kaiju. head=False leaves the neck stump (the breath stance's body, the head drawn as its own
    layer). glow {group: 0..1} lights plates; flash lights every lit plate white-hot."""
    pose = pose or {}
    glow = glow or {}
    rig = R.Rig(pose, sc, feet, sx=sx)
    rig.eye = eye
    rest = R.Rig({}, sc, feet)
    cv = R.KCanvas(*size)
    if lod is None:
        lod = sc < LOD_BELOW * R.BASE_SC
    cv.lod = lod
    sole = rig.floor() if floor else None
    tail_floor = rig.Ti('root', (0, 184.0))[1] if floor else None
    s_front = R.RIDGE_S[R.TAIL_FRONT_END]
    lit_parts, fx = [], set()
    rows = {row: R.plates(rig, glow, row, flash=flash) for row in ('far', 'main')}
    groups = {}

    def plate_pass(front):
        for row in ('far', 'main'):
            for (part, g, s_) in rows[row]:
                if (s_ < s_front) == front:
                    cv.stamp(part, cast=0 if row == 'far' else 1, floor=tail_floor, keep_line=True)
                    groups.setdefault(g, []).append(part)
                    if glow.get(g):
                        lit_parts.append(part)

    def stamp(spec, cast=2, fl='sole', owner=None, **kw):
        part, _ = shaded(rig, rest, spec, **kw)
        cv.stamp(part, cast=cast, floor=sole if fl == 'sole' else fl, owner=owner)
        return part

    plate_pass(front=False)
    stamp(R.TAIL_BACK, seed=3, owner='tail_back')
    stamp(R.FAR_LEG, bias=-0.14, seed=5, bounce=0.2, owner='far_leg')
    ff = stamp(R.FAR_FOOT, bias=-0.12, bounce=0.2, owner='far_foot')
    for toe in R.FAR_TOES:
        stamp(toe, bias=-0.08, cast=1)
    if not lod:
        cv.stamp(R.claws(rig, R.FFOOT_TIPS, 3), cast=0, floor=sole)
    if star_sole:
        _star_sole(rig, cv, ff)
    stamp(R.F_UPPER, bias=-0.14)
    stamp(R.F_FORE, bias=-0.1, cast=1)
    for f in R.F_FINGERS:
        stamp(f, bias=-0.05, cast=1)
    if not lod:
        cv.stamp(R.claws(rig, R.F_TIPS, 3), cast=0, floor=sole)
    for spec, seed in ((R.BELLY, 11), (R.CHEST, 12)):
        torso, tinfo = shaded(rig, rest, spec, bias=-0.04, seed=seed, bounce=0.3)
        R.belly(rig, torso, tinfo, seams=not lod)
        cv.stamp(torso, floor=sole, owner='belly' if spec is R.BELLY else 'chest')
    nl, _ = shaded(rig, rest, R.NEAR_LEG, bias=-0.02, seed=13, bounce=0.3)
    R.seam(rig, 'n_thigh', nl, [(64, 129), (70, 124), (78, 121), (86, 122), (93, 126)])
    cv.stamp(nl, floor=sole, owner='near_leg')
    stamp(R.NEAR_FOOT, bounce=0.2, owner='near_foot')
    for toe in R.NEAR_TOES:
        stamp(toe, bias=0.04, cast=1)
    if not lod:
        cv.stamp(R.claws(rig, R.NFOOT_TIPS, 3), cast=0, floor=sole)
    plate_pass(front=True)
    tf, _ = shaded(rig, rest, R.TAIL_FRONT, seed=4)
    R.seam(rig, 't3', tf, [(47, 163), (53, 165), (60, 167.5), (64, 172)])
    cv.stamp(tf, floor=tail_floor, owner='tail_front')
    mouth_at = None
    if head:
        jaw_px = R.jaw_part(rig, rest)
        cv.stamp(jaw_px, floor=sole)
        hd = R.head_part(rig, rest)
        cv.stamp(hd, floor=sole, owner='head')
        fx |= R.mouth(rig, rest, cv, jaw, glow=mouth_glow, jaw_px=jaw_px, head_px=hd)
        mouth_at = rig.Ti('head', R.MOUTH_PT)
    up, _ = shaded(rig, rest, R.N_UPPER, bias=0.02, bounce=0.2)
    R.seam(rig, 'n_upper', up, [(80, 99), (86, 102), (95, 100)])
    cv.stamp(up, floor=sole, owner='n_upper')
    stamp(R.N_FORE, bias=0.02, cast=1, bounce=0.2, owner='n_fore')
    stamp(R.N_PALM, bias=0.04, cast=1)
    for f in R.N_FINGERS:
        stamp(f, bias=0.08, cast=1)
    if not lod:
        cv.stamp(R.claws(rig, R.N_TIPS, 3.5), cast=0, floor=sole)
    skip = () if head else ('head',)
    R.gloss(rig, cv.px, skip, owner=cv.owner)
    R.lines_k(rig, cv.px, R.KNEE_CREASES, skip, any_key=True, owner=cv.owner, owners=R.CREASE_OWNER)
    R.lines_k(rig, cv.px, R.FOLDS, skip, owner=cv.owner, owners=R.FOLD_OWNER)
    star_mark(rig, cv)
    if halo:
        fx |= R.glow_halo(cv, lit_parts)
    if spark_pts:
        fx |= R.sparks(rig, cv, spark_pts)
    if not rig.rest:
        R.remove_islands(cv.px, keep=fx, min_size=14 if not lod else 3)
        R.seal(cv.px, fx)
    fx |= R.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in FX_KEYS}
    info = anchors(rig, cv.px, groups, head)
    return cv.px, fx, info


def star_mark(rig, cv):
    if rig.sc < 0.6 * R.BASE_SC:
        return
    b, p = R.STAR_AT
    ax, ay = rig.Ti(b, p)
    for r, row in enumerate(R.STAR):
        for c, ch in enumerate(row):
            q = (ax + c - 3, ay + r - 3)
            if ch != '.' and cv.px.get(q) not in (None, 'k') and cv.owner.get(q) == 'far_foot':
                cv.px[q] = ch


def _star_sole(rig, cv, foot_px):
    """The stomping foot lifted, its sole toward us: a pale sole pad with the chase-edition star
    sticker on it, laid over the foot's underside."""
    pts = [(113, 167.5), (139, 167.5), (141, 170.2), (126, 172.2), (112, 170.4)]
    pad = K.poly(rig.TP('f_foot', pts))
    for q in pad:
        if q in foot_px and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = '5'
    edge = [q for q in pad if q in foot_px and any(n not in pad for n in ((q[0], q[1] - 1), (q[0] - 1, q[1])))]
    for q in edge:
        if cv.px.get(q) not in (None, 'k'):
            cv.px[q] = '6'
    cx, cy = rig.Ti('f_foot', (126, 169.8))
    for r, row in enumerate(R.STAR):
        for c, ch in enumerate(row):
            q = (cx + c - 3, cy + r - 3)
            if ch != '.' and cv.px.get(q) not in (None, 'k'):
                cv.px[q] = ch


def anchors(rig, px, groups, head=True):
    """The per-frame anchors, frame texels."""
    ox, oy = rig.ox, rig.oy
    out = {
        'FEET': [int(round(ox)), int(round(oy))],
        'RIDER_SEAT': list(rig.Ti('head', R.SEAT)),
        'NECK': list(rig.Ti('head', R.BONES['head'][1])),
        'MOUTH': list(rig.Ti('head', R.MOUTH_PT)) if head else None,
        'FOOT_IMPACT': list(rig.Ti('f_foot', R.SOLE_F)),
        'FOOT_NEAR': list(rig.Ti('n_foot', R.SOLE_N)),
        'HIP': list(rig.Ti('pelvis', R.BONES['pelvis'][1])),
        'TAIL_ROOT': list(rig.Ti('t1', R.BONES['t1'][1])),
        'HEAD_TOP': list(rig.Ti('head', R.CROWN_PT)) if head else None,
    }
    if px:
        xs = [x for (x, y) in px]
        ys = [y for (x, y) in px]
        top = min(ys)
        out['CROWN'] = [min(x for (x, y) in px if y == top), top]
        out['BODY_DRAWN'] = [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]
    rects = []
    for g in range(R.N_GROUPS):
        pix = set()
        for part in groups.get(g, []):
            pix |= {q for q in part if px.get(q) == part[q]}
        if pix:
            xs = [x for (x, y) in pix]
            ys = [y for (x, y) in pix]
            rects.append([min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1])
        else:
            rects.append(None)
    out['SPINE_ROWS'] = rects
    return out


#THE HEAD LAYER

HEAD_FW, HEAD_FH = 176, 176
HEAD_PIVOT = (64, 88)              # NECK in the head frame


def render_head(aim=0.0, jaw=0.0, glow=True, flare=False, sc=R.BASE_SC):
    """The head layer for the breath: skull, jaw and the neck swivel collar round NECK, turned `aim`
    degrees (0 = the approved head; + is down), jaw opened `jaw` degrees, the throat glowing."""
    pv = R.BONES['head'][1]
    # place the rig so NECK lands on HEAD_PIVOT
    feet = (HEAD_PIVOT[0] - sc * (pv[0] - R.DX0), HEAD_PIVOT[1] - sc * (pv[1] - R.DY0))
    pose = {'head': (aim, 0.0, 0.0), 'jaw': (jaw, 0.0, 0.0)}
    rig = R.Rig(pose, sc, feet)
    rest = R.Rig({}, sc, feet)
    cv = R.KCanvas(HEAD_FW, HEAD_FH)
    cv.stamp(R.collar_part(rig), cast=0)
    jaw_px = R.jaw_part(rig, rest)
    cv.stamp(jaw_px)
    hd = R.head_part(rig, rest)
    cv.stamp(hd)
    fx = R.mouth(rig, rest, cv, jaw, glow=glow, jaw_px=jaw_px, head_px=hd)
    R.gloss(rig, cv.px, skip_bones=tuple(b for b in R.BONES if b != 'head'))
    origin = _mouth_origin(rig, jaw)
    if flare:
        fx |= R.flare(rig, cv, origin)
    fx |= R.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in FX_KEYS}
    seat = rig.Ti('head', R.SEAT)
    return cv.px, fx, {'NECK': list(HEAD_PIVOT), 'MOUTH': list(origin), 'SEAT_ON_HEAD': list(seat),
                       'AIM': aim}


def _mouth_origin(rig, jaw):
    """The beam's origin: just past the open mouth's front, midway between the jaws."""
    up = rig.T('head', (167.5, 81.8))
    lo = rig.T('jaw', (163.5, 84.5))
    mx, my = (up[0] + lo[0]) / 2.0, (up[1] + lo[1]) / 2.0
    d = rig.turn('head', (1.0, 0.0))
    return (int(round(mx + d[0] * 2.0)), int(round(my + d[1] * 2.0)))
