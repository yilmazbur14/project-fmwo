"""One Matt, built upright in his own LOCAL frame for a body that will be turned `theta` clockwise.

This is mi_fig.build (art_source/matt_intro) stamp for stamp, with four differences:

  1. The canvas has no edge. The rig's is 96x96 and silently drops anything past it; a tumbling
     man throws his arms and feet past his own frame.
  2. Every stamped pixel remembers which part put it there (`owner`), so the hand-drawn parts can be
     re-lit and the lint can measure him part by part.
  3. The light is turned -theta while he is built. Every surface the rig shades from a normal (the
     sweatshirt, sleeves, deltoids, trousers, socks, trainers, hem, cuffs, and the crest through
     mj_hair) is then lit from the FRAME's upper left once the body is turned: the rig's own volumes,
     with only the light moved, never a light refitted to the rotated bounding box.
  4. The hand-drawn parts carry their light baked in (the face, fists and hands, the collar, the
     combed strands, the speaker ports). The ports are round, so they are drawn pre-turned by
     -theta (to the nearest quarter) and come out exactly as drawn. The rest are re-lit by a delta:
     each pixel keeps its own tone and is shifted by how much brighter or darker the turned light
     makes a smooth volume at that spot (a head, a fist, a collar ring). The offset field is smooth,
     so the drawing's detail (nostrils, creases, knuckles) survives and only the light moves.

At theta 0 no pixel is touched by 3 or 4, and build() reproduces the approved frames pixel for
pixel (checked in _selftest against matt.png and the shipped hit and recover sheets).
"""
import math

import mj_base as J
from mj_base import A, B, F, details, matt, moved, rig_face, sh
import mj_hair

N4 = J.N4


class JFig(F.Fig):
    """mi_fig.Fig for the juggle frame. The only change is the headroom cap: the rig caps the
    centre spike so its tip stays on the 96x96 frame's row 1; the juggle frame has room above him,
    and the hit's flared crest needs it. cap=True restores the rig's behaviour exactly."""

    def __init__(self, **kw):
        self.cap = False
        super().__init__(**kw)

    def pose(self):
        if self.cap:
            return super().pose()
        P = matt.Pose(self.roar)
        if self.spikes is not None:
            P.spikes = list(self.spikes)
        if self.stance is not None:
            P.stance = self.stance
        return P


class Canvas:
    """lib.Canvas without edges, remembering each pixel's part."""

    def __init__(self):
        self.px = {}
        self.owner = {}

    def stamp(self, part, outline=True, owner='?'):
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if q not in body:
                        self.px[q] = 'k'
                        self.owner[q] = owner
        for q, k in part.items():
            self.px[q] = k
            self.owner[q] = owner


# ------------------------------------------------------------------------------ labelling
SKIN = set('123456')
LAVK = set('ABCDEF')
YELK = set('abcde')
CONE = set('KLMN')


def label_arm_part(part, outline, side):
    ks = set(part.values()) - {'k'}
    if ks & SKIN:
        return 'hand%d' % side
    if ks & CONE and ks & YELK:
        return 'port%d' % side
    if outline and ks <= YELK:
        return 'cuff%d' % side
    return 'sleeve%d' % side


# ------------------------------------------------------------------------------ the ports
def _quarter(rows, q):
    """A map's rows turned q quarter turns clockwise (exact)."""
    rs = [r.replace(' ', '') for r in rows]
    for _ in range(q % 4):
        h, w = len(rs), len(rs[0])
        rs = [''.join(rs[h - 1 - r][c] for r in range(h)) for c in range(w)]
    return rs


def port_part(centre, lit_side, theta):
    """A speaker port centred on `centre` (local), pre-turned so the turned body shows it exactly as
    drawn. lit_side: True for the port nearer the key light (PORT_L's rim), False for PORT_R's."""
    rows = details.PORT_L if lit_side else details.PORT_R
    q = int(round(theta / 90.0)) % 4
    rs = _quarter(rows, -q)
    h, w = len(rs), len(rs[0])
    x0 = int(round(centre[0] - (w - 1) / 2.0))
    y0 = int(round(centre[1] - (h - 1) / 2.0))
    return B.amap(rs, x0, y0)


def _map_centre(part):
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)


# ------------------------------------------------------------------------------ the delta relight
def _normal(x, y, cx, cy, rx, ry):
    nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 > 1.0:
        s = math.sqrt(d2)
        return nx / s, ny / s, 0.0
    return nx, ny, math.sqrt(1.0 - d2)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


RAMPS = {'skin': '123456', 'yel': 'abcde', 'hair': 'ljih', 'lav': 'ABCDEF', 'char': 'NMLK'}


def relight(cv, owners, model, baked, target, ramp, step, only=None, keep_extremes=True):
    """Shift the tone of every pixel owned by one of `owners` that is on `ramp` by how much a
    smooth volume `model` = (cx, cy, rx, ry) brightens or darkens under `target` against the light
    it was drawn under (`baked`). step: the lit difference worth one tone. The darkest tone of the
    ramp is only reached by pixels that were already on it (keep_extremes)."""
    cx, cy, rx, ry = model
    top = len(ramp) - 1
    changed = 0
    for q, o in cv.owner.items():
        if o not in owners:
            continue
        k = cv.px.get(q)
        if k not in ramp or (only is not None and q not in only):
            continue
        n = _normal(q[0], q[1], cx, cy, rx, ry)
        d = _dot(n, target) - _dot(n, baked)
        shift = int(round(d / step))
        if not shift:
            continue
        i = ramp.index(k)
        hi = top if (i == top or not keep_extremes) else top - 1
        j = max(0, min(hi, i - shift))
        if j != i:
            cv.px[q] = ramp[j]
            changed += 1
    return changed


def relight_keep_counts(cv, owners, model, baked, target, ramp, step, form):
    """The delta relight, with the drawing's own tone COUNTS kept.

    The approved faces and hands are drawn in the house way: a thin highlight on the lit rim, a
    broad shadow on the far one. Moving the light as physics would simply swaps those widths, so a
    face turned upside down comes out with a broad highlight and a thin shadow: brighter than any
    face on his sheets (the lint caught it: 22-24% highlight against an approved 6-15%). So each
    pixel is ranked by its drawn tone shifted by the turned light (the delta relight's own score),
    and the `form` tones are handed back out in the numbers the drawing had: the light moves, the
    style stays. Tones outside `form` (the nostrils, the ear canals, the knuckle creases, which are
    drawing rather than light) are left exactly as drawn."""
    cx, cy, rx, ry = model
    pts = []
    for q, o in cv.owner.items():
        if o not in owners:
            continue
        k = cv.px.get(q)
        if k not in form:
            continue
        n = _normal(q[0], q[1], cx, cy, rx, ry)
        d = _dot(n, target) - _dot(n, baked)
        t = ramp.index(k)
        pts.append((t - d / step, t, q))
    if not pts:
        return 0
    counts = [sum(1 for p in pts if ramp[p[1]] == k) for k in form]
    pts.sort()
    changed = 0
    i = 0
    for k, n in zip(form, counts):
        for (_, t, q) in pts[i:i + n]:
            if cv.px[q] != k:
                cv.px[q] = k
                changed += 1
        i += n
    return changed


def part_model(cv, owner, pad=1.0):
    """A sphere-ish volume fitted round one part's own pixels: its box, slightly padded."""
    pts = [q for q, o in cv.owner.items() if o == owner]
    if not pts:
        return None
    xs = [x for (x, y) in pts]
    ys = [y for (x, y) in pts]
    cx, cy = (min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0
    rx = (max(xs) - min(xs) + 1) / 2.0 + pad
    ry = (max(ys) - min(ys) + 1) / 2.0 + pad
    return (cx, cy, rx, ry)


# The head's volume for the face relight, at the head's rest position: the face map spans x 31-65
# and rows 29-52; the skull's middle sits between the eyes.
HEAD_MODEL = (48.5, 40.5, 24.0, 21.0)
COLLAR_MODEL = (48.5, 53.0, 15.0, 6.0)
# The dome's own flat model (matt.hair): lit = u*L.x + v*L.y with u = (x-48)/15, v = (y-22)/7, and a
# tone change every ~1.1 of lit.
DOME = (48, 22, 15.0, 7.0)
FACE_STEP = 0.85
HAND_STEP = 0.62
COLLAR_STEP = 0.62


def relight_comb(cv, theta, dx, dy):
    """The rig's combed strands sit on the dome, so they follow the dome's own flat light."""
    l0 = J.DOME_LIGHT
    l1 = J.rot2(J.DOME_LIGHT, -theta)
    ramp = RAMPS['hair']
    for q, o in cv.owner.items():
        if o != 'comb':
            continue
        k = cv.px.get(q)
        if k not in ramp:
            continue
        u = (q[0] - dx - DOME[0]) / DOME[2]
        v = (q[1] - dy - DOME[1]) / DOME[3]
        d = (u * l1[0] + v * l1[1]) - (u * l0[0] + v * l0[1])
        shift = int(round(d / 1.1))
        if shift:
            i = ramp.index(k)
            cv.px[q] = ramp[max(0, min(len(ramp) - 1, i - shift))]


# ------------------------------------------------------------------------------ the build
def build(f, theta=0.0, trail=0.0, relit=True, hands_baked=None):
    """Matt from a mi_fig.Fig spec, in LOCAL coordinates, for a body that will be turned theta
    clockwise. Returns the Canvas (px and owner).

    hands_baked: {side: degrees} for hand maps that were themselves drawn turned (a quarter-turned
    OPEN_UP for a hand pointing sideways): their baked light is the rig's turned by that much."""
    P = f.pose()
    cv = Canvas()
    bx, by = f.body
    hx, hy = f.head
    target = J.local_light3(theta)
    saved = sh.LIGHT3
    sh.LIGHT3 = target
    q = int(round(theta / 90.0)) % 4
    try:
        # the port nearer the key light keeps PORT_L's rim: which one that is depends on the turn
        port_centres = {}

        def port_lit(side):
            c = port_centres.get(side)
            o = port_centres.get(1 - side)
            if c is None or o is None:
                return side == 0
            lx, ly = J.rot2((c[0] - o[0], c[1] - o[1]), theta)
            return lx * J.LIGHT3[0] + ly * J.LIGHT3[1] > 0

        arm_parts = []
        for side, arm in enumerate(f.arms or []):
            ps = []
            for part, ol, layer in A.parts(arm):
                lab = label_arm_part(part, ol, arm.side)
                ps.append((part, ol, layer, lab))
                if lab.startswith('port'):
                    port_centres[arm.side] = _map_centre(moved(part, bx, by))
            arm_parts.append(ps)

        def stamp_layer(name):
            for part, ol, layer in f.parts:
                if layer == name:
                    cv.stamp(part, outline=ol, owner='extra')
            for ps in arm_parts:
                for part, ol, layer, lab in ps:
                    if layer != name:
                        continue
                    part = moved(part, bx, by)
                    if lab.startswith('port') and theta:
                        side = int(lab[-1])
                        part = port_part(_map_centre(part), port_lit(side), theta)
                    cv.stamp(part, outline=ol, owner=lab)

        stamp_layer('back')
        stamp_layer('back2')
        # legs
        if f.legs is None:
            cv.stamp(matt.trousers(P), owner='legs')
            for ft in matt.feet(P):
                cv.stamp(ft, outline=False, owner='feet')
        else:
            for part, ol in f.legs(f):
                ks = set(part.values())
                cv.stamp(part, outline=ol, owner='legs' if ks <= set('NMLKk') else 'feet')
        # torso
        shirt = f.torso_fn() if f.torso_fn else matt.sweatshirt(P)
        if f.torso_hook:
            f.torso_hook(shirt)
        cv.stamp(moved(shirt, bx, by), owner='shirt')
        if f.hem:
            cv.stamp(moved(f.hem_fn() if f.hem_fn else matt.hem_band(P), bx, by), owner='hem')
        if f.collar:
            cv.stamp(moved(f.collar_fn() if f.collar_fn else details.collar(), bx, by),
                     outline=False, owner='collar')
        # arms
        if f.arms is None:
            for side in (0, 1):
                for part, outline in matt.arm_parts(P, side):
                    lab = 'cuff%d' % side if set(part.values()) <= YELK else 'sleeve%d' % side
                    cv.stamp(moved(part, bx, by), outline=outline, owner=lab)
            (pdx, pdy), (fdx, fdy) = matt.arm_offsets(P)
            pl, pr = details.ports()
            pl, pr = moved(pl, pdx + bx, pdy + by), moved(pr, -pdx + bx, pdy + by)
            if theta:
                port_centres[0], port_centres[1] = _map_centre(pl), _map_centre(pr)
                pl = port_part(port_centres[0], port_lit(0), theta)
                pr = port_part(port_centres[1], port_lit(1), theta)
            cv.stamp(pl, outline=False, owner='port0')
            cv.stamp(pr, outline=False, owner='port1')
            fl, fr = details.fists()
            cv.stamp(moved(fl, fdx + bx, fdy + by), outline=False, owner='hand0')
            cv.stamp(moved(fr, -fdx + bx, fdy + by), outline=False, owner='hand1')
        stamp_layer('mid')
        if f.neck:
            n = {}
            for y in range(47, 54):
                for x in range(42, 55):
                    n[(x + bx, y + by)] = '4' if y < 50 else '3'
            for y in range(47, 54):
                n[(41 + bx, y + by)] = 'k'
                n[(55 + bx, y + by)] = 'k'
            cv.stamp(n, outline=False, owner='neck')
        # head
        hdy = hy + P.head_dy
        cv.stamp(moved(mj_hair.hair(P.spikes, f.tilt, theta, trail), hx, hdy), owner='hair')
        if f.comb:
            for (x, y, k) in matt.STRANDS:
                qq = (x + hx, y + hdy)
                if cv.px.get(qq) in ('i', 'j', 'h', 'l'):
                    cv.px[qq] = k
                    cv.owner[qq] = 'comb'
        if f.face is None:
            rows, x0, y0 = rig_face.IDLE, rig_face.X0, rig_face.IDLE_Y0
        else:
            rows, x0, y0 = f.face
        cv.stamp(moved(B.amap(rows, x0, y0), hx, hdy), outline=False, owner='face')
        if f.face_hook:
            f.face_hook(cv.px)
        stamp_layer('front')
        stamp_layer('top')
    finally:
        sh.LIGHT3 = saved

    if relit and theta % 360:
        base = J.LIGHT3
        hm = (HEAD_MODEL[0] + hx, HEAD_MODEL[1] + hdy, HEAD_MODEL[2], HEAD_MODEL[3])
        relight_keep_counts(cv, {'face'}, hm, base, target, RAMPS['skin'], FACE_STEP, '1234')
        cm = (COLLAR_MODEL[0] + bx, COLLAR_MODEL[1] + by, COLLAR_MODEL[2], COLLAR_MODEL[3])
        relight(cv, {'collar'}, cm, base, target, RAMPS['yel'], COLLAR_STEP)
        for side in (0, 1):
            lab = 'hand%d' % side
            m = part_model(cv, lab)
            if m is None:
                continue
            baked = base
            if hands_baked and side in hands_baked:
                bl = J.rot2(base[:2], hands_baked[side])
                baked = (bl[0], bl[1], base[2])
            relight_keep_counts(cv, {lab}, m, baked, target, RAMPS['skin'], HAND_STEP, '1234')
        relight_comb(cv, theta, hx, hdy)
    return cv


def close_pinholes(px, fx=()):
    """mi_fig.close_pinholes: a transparent pixel boxed in on four sides becomes keyline."""
    if not px:
        return px
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in px:
                continue
            if all(q in px and q not in fx for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                px[(x, y)] = 'k'
    return px


def px_of(f, theta=0.0, **kw):
    cv = build(f, theta, **kw)
    return close_pinholes(cv.px, f.fx), cv.owner


# ------------------------------------------------------------------------------ self-test
def _selftest():
    ok = True
    idle, _ = px_of(F.Fig())
    ref = {p: k for p, k in F.px_of(F.Fig()).items()}
    d = B.pixel_diff(B.image(idle), B.approved_sheet().crop((0, 0, 96, 96)))
    print('build(Fig()) vs approved matt.png f0:', d or 'identical')
    ok &= d is None
    # the shipped fight sheets, frame for frame: the arms here are bent arms and the legs custom
    for cls, png in ((J.MR.Hit, 'matt_hit.png'), (J.MR.Recover, 'matt_recover.png')):
        from PIL import Image
        import os
        sheet = Image.open(os.path.join(J.ASSETS, png)).convert('RGBA')
        for i, f in enumerate(cls.figs()):
            mine, _ = px_of(f)
            mine = {p: k for p, k in mine.items() if 0 <= p[0] < 96 and 0 <= p[1] < 96}
            d = B.pixel_diff(B.image(mine), sheet.crop((96 * i, 0, 96 * i + 96, 96)))
            print('build(%s f%d) vs shipped %s:' % (cls.NAME, i, png), d or 'identical')
            ok &= d is None
    return ok


if __name__ == '__main__':
    _selftest()
