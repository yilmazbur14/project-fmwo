"""rig34.draw, carried into the juggle frame.

    draw(p, T, head=None) -> lib.Canvas (192x144)

`p` is a rig34 pose dictionary in HIS OWN 96x96 space (the format in rig34's docstring), `T` the
kjrig.Tf that puts him in the frame.  Everything is drawn in the order rig34.draw draws it, by the
same functions where they already light by the screen (limb, fist), and by exact equivalents here
where rig34 bakes body-relative light or gravity (foot, trousers, jacket, caps, belt, beads, the chest
detail, the 天).  check_identity() renders the approved sheets' own poses through this at angle 0 and
compares them with rig34.draw, pixel for pixel.

`head` overrides the head: dict(part=, turn=, shift=, back=, earring=) -- see kjrig and poses.py.
"""
import math

import kjrig as K
from kjrig import L, RG, FC, HD

LIGHT2 = RG.LIGHT                       # (-0.6, -0.8): the rig's screen light for its bands
NECK_PIVOT = (47.5, 49.0)               # where a head tips: under the beard, on the neck


def _unit(dx, dy):
    Ln = math.hypot(dx, dy) or 1.0
    return dx / Ln, dy / Ln, Ln


def fpt(T, p):
    return T.fwd(p[0], p[1])


def body_px(T, X, Y):
    """The pixel of his own space under a frame pixel's centre, as integer coordinates."""
    u, v = T.inv(X + 0.5, Y + 0.5)
    return (int(math.floor(u)), int(math.floor(v)))


def frame_of(T, pixels):
    """Every frame pixel whose centre maps back into a set of his own pixels (nearest sampling;
    exact under a whole-pixel quarter turn)."""
    if not pixels:
        return {}
    if T.whole():
        out = {}
        for (x, y) in pixels:
            X, Y = T.fwd(x + 0.5, y + 0.5)
            out[(int(math.floor(X)), int(math.floor(Y)))] = (x, y)
        return out
    xs = [q[0] for q in pixels]
    ys = [q[1] for q in pixels]
    corners = [T.fwd(a, b) for a in (min(xs), max(xs) + 1) for b in (min(ys), max(ys) + 1)]
    out = {}
    for Y in range(int(math.floor(min(c[1] for c in corners))) - 1,
                   int(math.ceil(max(c[1] for c in corners))) + 2):
        for X in range(int(math.floor(min(c[0] for c in corners))) - 1,
                       int(math.ceil(max(c[0] for c in corners))) + 2):
            q = body_px(T, X, Y)
            if q in pixels:
                out[(X, Y)] = q
    return out


def carry(T, part):
    """A {(x, y): key} part of his own space, in the frame."""
    return {Q: part[q] for Q, q in frame_of(T, set(part)).items()}


# ------------------------------------------------------------------ feet and hands
def foot(T, ank_b, deg_b, ln=11.0, hi=4.6, bias=0, floor=None):
    """rig34.foot, turned.  The foot's shape and its top/sole are his own (the 'up' out of the
    instep is chosen in his own space, as rig34 chooses it); the top is lit when it faces the screen
    light and the sole is lit when IT does -- the same test rig34 makes, asked on screen."""
    a = math.radians(deg_b)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny
    # into the frame
    ank = fpt(T, ank_b)
    ux, uy = T.turn(ux, uy)
    nx, ny = T.turn(nx, ny)
    if floor is not None and ank[1] > floor - 9 and abs(uy) < 0.35:
        hi = max(2.6, min(hi, floor - 1 - ank[1] + 0.5))
    local = [(-2.6, -hi), (-2.6, -hi * 0.25), (-1.2, 0.0), (1.5, 0.0), (ln * 0.72, -hi * 0.46),
             (ln * 0.97, -hi * 0.58), (ln, -hi * 0.86), (ln * 0.94, -hi - 0.3), (-2.0, -hi - 0.3)]
    pts = [(ank[0] + ux * t + nx * s, ank[1] + uy * t + ny * s) for t, s in local]
    m = L.poly(pts)
    if floor is not None:
        m = {q for q in m if q[1] <= floor - 1}
    lit_top = nx * LIGHT2[0] + ny * LIGHT2[1] >= 0
    part = {}
    for q in m:
        t = (q[0] - ank[0]) * ux + (q[1] - ank[1]) * uy
        s = (q[0] - ank[0]) * nx + (q[1] - ank[1]) * ny
        f = (s + hi) / hi
        if not lit_top:
            f = 1.0 - f
        i = 1 if f > 0.66 else (2 if f > 0.34 else (3 if f > 0.08 else 4))
        if t < -1.0:
            i = min(4, i + 1)
        part[q] = 'stuvw'[min(4, i + bias)]
    for tt in (ln * 0.60, ln * 0.78):
        for ss in (-hi + 0.4, -hi + 1.4):
            q = (int(round(ank[0] + ux * tt + nx * ss)), int(round(ank[1] + uy * tt + ny * ss)))
            if q in part:
                part[q] = 'k'
    return part


def flat_hand(T, wr_b, direction=-1, bias=0, floor=95):
    """rig34.flat_hand in his own space (it is only ever flat on the floor), carried."""
    x0, y0 = int(round(wr_b[0])), int(round(wr_b[1]))
    part = {}
    for dy in range(-2, 2):
        for dx in range(-2, 3):
            part[(x0 + dx, y0 + dy)] = 'hhijl'[min(4, max(0, dx * direction + 2 + bias))] \
                if dy < 1 else 'j'
    for dx in range(0, 8):
        x = x0 + direction * (dx + 2)
        for yy in range(y0 + 1, floor):
            part[(x, yy)] = 'u' if yy == y0 + 1 else ('v' if yy < floor - 1 else 'w')
    for dx in (4, 6):
        x = x0 + direction * (dx + 2)
        part[(x, floor - 2)] = 'k'
        part[(x, floor - 1)] = 'k'
    return carry(T, part)


# ------------------------------------------------------------------ clothes
def trousers(T, p):
    """rig34.trousers: the legs and the seat drawn in the frame (their bands light by the screen),
    the torn hems cut along each shin, and the navy->violet fade asked in HIS space -- it is the
    cloth's own dye toward the hems, not light."""
    out = {}
    py = p['pelvis'][1]
    sc = T.scale
    for key, bias, r in (('rear', 1, (7.2, 6.4, 4.8)), ('lead', 0, (8.0, 7.0, 5.2))):
        hip, knee, ank, _ = p[key]
        bx, by, BL = _unit(ank[0] - knee[0], ank[1] - knee[1])
        cut = (knee[0] + bx * BL * 0.32, knee[1] + by * BL * 0.32)
        H_, K_, C_ = fpt(T, hip), fpt(T, knee), fpt(T, cut)
        segs = [(H_, K_, r[0] * sc, r[1] * sc), (K_, C_, r[1] * sc, r[2] * sc)]
        part = RG.limb(segs, bias=bias, tones='abcdef', hi=False)
        ux, uy = T.turn(bx, by)
        nx, ny = -uy, ux
        for q in list(part):
            t = (q[0] - C_[0]) * ux + (q[1] - C_[1]) * uy
            s = (q[0] - C_[0]) * nx + (q[1] - C_[1]) * ny
            tooth = 1.6 * abs(math.sin(s * 0.95))
            if t > -0.5 + tooth:
                del part[q]
        out[key] = part
    cx, cy, cr = p['pelvis']
    ax, ay, _ = p['chest']
    top = (ax + (cx - ax) * (RG.BELT_T - 0.06), ay + (cy - ay) * (RG.BELT_T - 0.06))
    out['seat'] = RG.limb([(fpt(T, top), fpt(T, (cx, cy + 1.5)), (cr + 1.4) * sc,
                            (cr + 1.2) * sc)], tones='abcdef', hi=False)
    NAVY, VIOLET = 'abcdef', 'ABCDEF'
    for part in out.values():
        for (X, Y), k in list(part.items()):
            x, y = body_px(T, X, Y)
            if k in NAVY and (y >= py + 9 or (y == py + 8 and (x + y) % 2 == 0)):
                part[(X, Y)] = VIOLET[NAVY.index(k)]
    return out


def jacket_body(p, back=False):
    """rig34.jacket's SHAPE in his own space: {pixel: (t, s, r, lapel?)} -- the lapels and the open
    front are the cloth's cut and stay his.  Its light is decided in the frame (jacket())."""
    (cx, cy), (ux, uy), (nx, ny), Ln = RG.torso_frame(p)
    cr = p['chest'][2]
    pr = p['pelvis'][2]
    shell = L.grow(L.capsule((cx, cy), p['pelvis'][:2], cr, pr), 1)
    out = {}
    for (x, y) in shell:
        t = ((x - cx) * ux + (y - cy) * uy) / Ln
        s = (x - cx) * nx + (y - cy) * ny
        r = cr + (pr - cr) * max(0.0, min(1.0, t))
        if t > RG.BELT_T + 0.04:
            continue
        lo, hi = RG.V_OPEN(t, r)
        if not back and lo < s < hi:
            continue
        lapel = (not back and (lo - 2.2 <= s <= lo or hi <= s <= hi + 2.2) and t < RG.V_CLOSE)
        out[(x, y)] = (t, s, r, lapel)
    return out


def _facing(v_rest, T):
    """How much more (or less) a body axis faces the screen light once T has turned it, relative to
    how it faced it at rest: (turned . L) / (rest . L).  1 at angle 0; -1 when turned to face away."""
    Lx, Ly = LIGHT2
    Ln = math.hypot(Lx, Ly)
    rest = (v_rest[0] * Lx + v_rest[1] * Ly) / Ln
    vx, vy = T.turn(*v_rest)
    now = (vx * Lx + vy * Ly) / Ln
    # 1 + (now - rest) / D: exactly now / rest when the axis faced the light at rest, and still well
    # behaved when it was nearly edge-on to it (a pitched rush torso) -- and exactly 1 at angle 0,
    # where now == rest bit for bit.
    D = rest if abs(rest) >= 0.35 else (0.35 if rest >= 0 else -0.35)
    return max(-1.5, min(1.5, 1.0 + (now - rest) / D))


def jacket(T, p, back=False):
    """rig34.jacket, turned.  rig34 shades the gi as a CYLINDER round the torso:
        lvl = -s/(r+1)*0.65 - t*0.35
    a strong term ACROSS the torso (s, toward its chest-front axis n) and a mild one ALONG it (t,
    toward its belt axis u) -- in its upright pose, lighter toward the upper left.  Turning him turns
    n and u, so each term is scaled by how its axis now faces the screen light compared with how it
    faced it at rest (_facing): the cylinder keeps its own shape of shading and only the light's side
    of it moves.  At angle 0 both scales are exactly 1: rig34's own number, pixel for pixel."""
    shape = jacket_body(p, back)
    (cx, cy), (ux, uy), (nx, ny), Ln = RG.torso_frame(p)
    a_s = _facing((nx, ny), T)
    a_t = _facing((ux, uy), T)
    part = {}
    for Q, q in frame_of(T, set(shape)).items():
        t, s, r, lapel = shape[q]
        lvl = -s / (r + 1.0) * 0.65 * a_s - t * 0.35 * a_t
        k = 'b' if lvl > 0.30 else ('c' if lvl > -0.12 else ('d' if lvl > -0.45 else 'e'))
        if lapel:
            k = 'b' if t < RG.V_CLOSE * 0.6 else 'c'
        part[Q] = k
    return part, shape


def caps(T, p, footprint=None):
    """rig34.caps: the torn cap's shape asked in his space, its light on screen.  If `footprint` is
    a set, the caps' own pixels (his space) are added to it."""
    out = []
    for key, bias in (('far', 1), ('near', 0)):
        sh, el = p[key][0], p[key][1]
        ux, uy, _ = _unit(el[0] - sh[0], el[1] - sh[1])
        m = L.ellipse(sh[0] - ux * 1.5, sh[1] - uy * 1.5 - 1.0, 7.2, 6.2)
        keep = set()
        for q in m:
            t = (q[0] - sh[0]) * ux + (q[1] - sh[1]) * uy
            s = (q[0] - sh[0]) * (-uy) + (q[1] - sh[1]) * ux
            if t > 1.8 + 1.8 * abs(math.sin(s * 1.05)):
                continue
            keep.add(q)
        if footprint is not None:
            footprint |= keep
        SH = fpt(T, sh)
        part = {}
        for Q in frame_of(T, keep):
            lit = (Q[0] - SH[0]) * LIGHT2[0] + (Q[1] - SH[1]) * LIGHT2[1]
            i = 1 if lit > 3.0 else (2 if lit > -1.0 else 3)
            part[Q] = 'abcde'[min(4, i + bias)]
        out.append(part)
    return out


def belt(T, p):
    """rig34.belt: the rope's lie is his (levelled against his lean, as rig34 does it); the knot's
    light is on screen."""
    cx, cy, cr = p['pelvis']
    ax, ay, _ = p['chest']
    a = math.degrees(math.atan2(cy - ay, cx - ax)) + 90.0
    a = (a + 180.0) % 360.0 - 180.0
    if a > 90.0:
        a -= 180.0
    elif a < -90.0:
        a += 180.0
    ang = math.radians(a * 0.42)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    cyl = cy - 3.0
    half = cr + 2.2
    rope = {}
    for y in range(int(cyl - 8), int(cyl + 8)):
        for x in range(int(cx - half - 3), int(cx + half + 4)):
            t = (x - cx) * ux + (y - cyl) * uy
            s = (x - cx) * nx + (y - cyl) * ny
            if abs(t) <= half and -1.5 <= s <= 1.5:
                row = int(round(s + 1.5))
                rope[(x, y)] = ('nnop', 'nopq', 'opqr', 'opqr')[min(3, row)][(x + y) % 4]
    kx, ky = cx + ux * (half - 1.0), cyl + uy * (half - 1.0)
    knot = L.ellipse(kx, ky, 2.6, 2.4)
    part = {}
    KX, KY = fpt(T, (kx, ky))
    for Q, q in frame_of(T, set(rope) | knot).items():
        if q in knot:
            # rig34 lights the knot toward the upper left of its centre; asked on screen
            dd = (Q[0] - KX) + (Q[1] - KY)
            part[Q] = 'n' if dd < -1 else ('o' if dd < 1 else 'q')
        else:
            part[Q] = rope[q]
    return part


def beads(T, p):
    """rig34.beads, positioned in his space and stamped upright in the frame -- round beads."""
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    sway = p.get('sway', 0.0)
    out = []
    n = 6
    for i in range(n):
        t = i / (n - 1.0)
        x = fx - 2.0 + (sx - fx + 4.0) * t + sway * math.sin(math.pi * t) * 1.2
        y = fy - 5.0 + math.sin(math.pi * t) * 6.0 + sway * 0.4
        bx, by = int(round(x)) - 1, int(round(y)) - 1          # rig34's own rounding, in his space
        X, Y = T.fwd(bx + 0.5, by + 0.5)
        out.append((int(math.floor(X)), int(math.floor(Y))))
    return out


def chest_detail(cv, T, p):
    """rig34._chest_detail: the pec shadow and the ab rungs, laid in his space and carried."""
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    ux, uy, Ln = _unit(px_ - cx, py_ - cy)
    nx, ny = -uy, ux
    if nx < 0:
        nx, ny = -nx, -ny

    def at(t, s):
        return (int(round(cx + ux * Ln * t + nx * s)), int(round(cy + uy * Ln * t + ny * s)))
    skin = set('stuvw')
    for pts, key in (([at(0.30, -1.0), at(0.34, 2.5), at(0.30, 5.5)], 'w'),
                     ([at(0.52, 0.0), at(0.52, 4.0)], 'v'),
                     ([at(0.70, 0.0), at(0.70, 4.0)], 'v'),
                     ([at(0.35, 1.0), at(0.95, 1.5)], 'v')):
        for q in L.polyline(pts):
            X, Y = T.fwd(q[0] + 0.5, q[1] + 0.5)
            Q = (int(math.floor(X)), int(math.floor(Y)))
            if cv.px.get(Q) in skin:
                cv.px[Q] = key


def mark(cv, T, p, shape, clear=None):
    """The 天 on his back: fitted by the mark artist's own rig in HIS space (mark.ten_fitted, exactly
    as rig34._mark does it), carried into the frame, and its one dark edge repainted by the rule that
    rig drew it with -- the edge pixels facing down or right ON SCREEN (intro_sigil.paint_rest)."""
    import mark as MK
    sh, el, wr, fi = p['near']
    arm = L.capsule(sh, el, 5.4, 4.8) | L.capsule(el, wr, 4.8, 4.2)
    jk = set(shape)
    panel = jk - L.grow(arm, 1)
    if clear:
        # the juggle's back views: the caps and the back of his head are drawn after the mark, so
        # fitting it where they will not land keeps the whole 天 in view rather than fragments
        panel -= L.grow(clear, 1)
    ten = MK.ten_fitted(panel, jk)
    if T.angle == 0 and T.whole():
        cv.stamp(carry(T, ten), outline=False)
        return
    moved = carry(T, ten)
    m = set(moved)
    part = {}
    for (X, Y) in m:
        part[(X, Y)] = 'Y' if ((X, Y + 1) not in m or (X + 1, Y) not in m) else 'y'
    cv.stamp(part, outline=False)


# ------------------------------------------------------------------ the head
def head_parts(p, T, override=None):
    """The head, neck and earring, turned and re-lit.  Returns (neck, head, earring, fresh):
    fresh=True when the head was resampled and needs a keyline stamped round it."""
    hdx, hdy = p['head']
    eye, jaw = p.get('face', (0, 0))
    o = override or {}
    back = p.get('back', False)
    tilt = o.get('turn', 0.0)
    if back:
        part = FC.back_head_part(0, 0)
    else:
        part = o.get('part') or FC.head_part(eye, jaw, 0, 0)
    Th = T.sub(NECK_PIVOT, tilt, shift=(hdx, hdy))
    total = T.angle + tilt
    lit = K.relight(part, total)
    head, fresh = K.turned(lit, Th)
    neck = {}
    if not back:
        nk = FC.neck_part(0, 0, rows=5)
        nk = K.relight(nk, total, sph=K.NECK_SPHERE)
        neck, _ = K.turned(nk, Th)
    # the cross hangs from the lobe of his right ear on its link -- whatever way he is turned, it
    # hangs DOWN the screen (it is a pendant); on the back view the ear is on screen right
    lobe = (33.5, 43.5) if not back else (95 - 33.5 + 1.0, 43.5)
    LX, LY = Th.fwd(*lobe)
    ear = {}
    for (x, y), k in L.amap(HD.EARRING, 31, 43).items():
        xx = x if not back else 95 - x
        ear[(int(math.floor(LX)) + (xx - (33 if not back else 62)),
             int(math.floor(LY)) + (y - 43))] = k
    return neck, head, ear, fresh


# ------------------------------------------------------------------ the figure
def draw(p, T, head=None, floor=None):
    """rig34.draw in the frame.  floor: the frame row his soles may not pass (None in the air)."""
    cv = K.canvas()
    back = p.get('back', False)
    sc = T.scale

    hip, knee, ank, deg = p['rear']
    cv.stamp(RG.limb([(fpt(T, knee), fpt(T, ank), 4.2 * sc, 3.6 * sc)], bias=1))
    cv.stamp(foot(T, ank, deg, ln=9.5, hi=4.0, bias=1, floor=floor))

    sh, el, wr, fi = p['far']
    cv.stamp(RG.limb([(fpt(T, sh), fpt(T, el), 5.0 * sc, 4.4 * sc),
                      (fpt(T, el), fpt(T, wr), 4.4 * sc, 3.8 * sc)], bias=1))
    if p.get('far_hand') == 'flat':
        cv.stamp(flat_hand(T, wr, -1, bias=1))
    else:
        cv.stamp(RG.fist(fpt(T, wr), fpt(T, fi), 3.8 * sc, bias=1))

    hip, knee, ank, deg = p['lead']
    cv.stamp(RG.limb([(fpt(T, knee), fpt(T, ank), 4.8 * sc, 4.2 * sc)]))
    cv.stamp(foot(T, ank, deg, floor=floor))

    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    cv.stamp(RG.limb([(fpt(T, (cx, cy)), fpt(T, (px_, py_)), cr * sc, pr * sc)], tones='stuvw'))
    if not back:
        chest_detail(cv, T, p)
    tr = trousers(T, p)
    for k in ('rear', 'seat', 'lead'):
        cv.stamp(tr[k])
    jk, shape = jacket(T, p, back)
    cv.stamp(jk)
    neck, hd, ear, fresh = head_parts(p, T, head)
    cap_parts = None
    if back:
        clear = None
        if p.get('mark_clear'):
            clear = set()
            cap_parts = caps(T, p, footprint=clear)
            for (X, Y) in hd:
                clear.add(body_px(T, X, Y))
        mark(cv, T, p, shape, clear=clear)
    elif p.get('beads', True):
        for (bx, by) in beads(T, p):
            cv.stamp(L.amap(RG.BEAD, bx, by), outline=False)
    cv.stamp(belt(T, p))

    sh, el, wr, fi = p['near']
    cv.stamp(RG.limb([(fpt(T, sh), fpt(T, el), 5.4 * sc, 4.8 * sc),
                      (fpt(T, el), fpt(T, wr), 4.8 * sc, 4.2 * sc)]))
    if p.get('near_hand') == 'flat':
        cv.stamp(flat_hand(T, wr, 1))
    else:
        cv.stamp(RG.fist(fpt(T, wr), fpt(T, fi), 4.3 * sc))
    for c in (cap_parts if cap_parts is not None else caps(T, p)):
        cv.stamp(c)

    if neck:
        cv.stamp(neck, outline=False)
    cv.stamp(hd, outline=fresh)
    cv.stamp(ear, outline=False)
    return cv


# ------------------------------------------------------------------ the proof
def check_identity(offset=(0, 0)):
    """Every approved three-quarter pose (rush, pass, spent, defeat), drawn by draw() at angle 0,
    against rig34.draw's own frame.  Returns [(name, diff or None)].

    At offset (0, 0) the transform is an exact identity in floating point, so this proves the LOGIC
    of every recomputed part.  (At a non-zero offset a handful of pixels that sit exactly on one of
    rig34's thresholds -- a cap's `lit > 3.0`, a hem tooth's `t > -0.5 + tooth` -- can round the
    other way, because (56 + 48) - (53.8 + 48) is not bit-for-bit 56 - 53.8.  That is arithmetic,
    not a different drawing.)"""
    import poses34 as PZ
    from PIL import Image
    from imgdiff import pixel_diff
    ox, oy = offset
    out = []
    named = ([('rush %d' % i, q) for i, q in enumerate(PZ.RUSH)]
             + [('pass %d' % i, q) for i, q in enumerate(PZ.PASS)]
             + [('spent', PZ.SPENT)]
             + [('defeat %d' % i, q) for i, q in enumerate(PZ.DEFEAT) if q])
    for name, q in named:
        want = RG.draw(q).image()
        T = K.Tf(0.0, pivot=(0.0, 0.0), dest=(float(ox), float(oy)))
        got = draw(q, T, floor=95 + oy).image().crop((ox, oy, ox + 96, oy + 96))
        out.append((name, pixel_diff(want, got)))
    return out
