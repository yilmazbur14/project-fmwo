"""The three-quarter rig: one joint dictionary per frame, drawn in the polish style.

Used by the rush, the rush pass, the punish window and the defeat. The poses are the approved sheets'
own joints (art_source/carter_akuma/combat_rush.py and combat_poses.py), converted from that rig's
design space to pixels (x' = 47.5 + (x - 47.5) * 0.84, y' = 96 + (y - 96) * 0.84, radii * 0.84), so
every sheet keeps the timing, reach and silhouette the fight was tuned against. What is new is how
they are drawn:

  * every limb is ONE capsule per segment, keylined once, toned in bands across its width - lit on
    the side facing the upper left - so it reads as a cylinder, not a stack of outlined pieces;
  * fists are wrapped fists (cream wrap, a keyline where it stops at the knuckles, bare fingers);
  * feet have an instep, a sole and keylined toes, at any angle;
  * the head is the polished front head (faces.head_part) or the back head, never re-rasterised.

A pose (all pixel space, facing RIGHT):
    head    (dx, dy) offset of the front head          face   (eye level, jaw)
    chest   (x, y, r)          pelvis  (x, y, r)
    near    (shoulder, elbow, wrist, fist)  the arm nearer the camera, drawn last
    far     (shoulder, elbow, wrist, fist)  the other arm, drawn first, a step darker
    lead    (hip, knee, ankle, foot_deg)    the forward leg   (foot_deg 0 = toes right)
    rear    (hip, knee, ankle, foot_deg)    the other leg, a step darker
    back    True for the rush pass (his back to the camera: the back head, the jacket closed, the 天)
    beads   draw the juzu (default True)    tails  (deg, length) gi tails whipping behind, or None
    far_hand / near_hand   'fist' (default) or 'flat' (palm on the floor)

    draw(p) -> Canvas (no aura)
"""
import math
from lib import (Canvas, poly, ellipse, capsule, grow, erode, edge, rim, stroke, DARKER, LIGHTER,
                 mirror_set)
import faces as FC

LIGHT = (-0.6, -0.8)


def _unit(dx, dy):
    L = math.hypot(dx, dy) or 1.0
    return dx / L, dy / L, L


def band(mask, a, b, r, tones='stuvw', bias=0, hi=True):
    """Tone a limb segment by its offset across the axis a->b: the side facing the light is lit.
    tones: light..dark (5). bias steps darker (far limbs)."""
    ux, uy, L = _unit(b[0] - a[0], b[1] - a[1])
    nx, ny = -uy, ux
    if nx * LIGHT[0] + ny * LIGHT[1] < 0:
        nx, ny = -nx, -ny
    out = {}
    for (x, y) in mask:
        t = ((x - a[0]) * ux + (y - a[1]) * uy) / L
        s = ((x - a[0]) * nx + (y - a[1]) * ny) / r
        i = 1 if s > 0.45 else (2 if s > -0.25 else (3 if s > -0.7 else 4))
        if hi and s > 0.72 and 0.15 < t < 0.8:
            i = 0
        out[(x, y)] = tones[min(len(tones) - 1, i + bias)]
    return out


def limb(segs, bias=0, tones='stuvw', hi=True):
    """segs: [(a, b, r0, r1)]. Each pixel takes the band of its nearest segment."""
    parts = []
    mask = set()
    for a, b, r0, r1 in segs:
        m = capsule(a, b, r0, r1)
        parts.append((m, a, b, (r0 + r1) / 2.0))
        mask |= m
    out = {}
    for q in mask:
        best = None
        for m, a, b, r in parts:
            ux, uy, L = _unit(b[0] - a[0], b[1] - a[1])
            t = max(0.0, min(1.0, ((q[0] - a[0]) * ux + (q[1] - a[1]) * uy) / L))
            d = math.hypot(q[0] - a[0] - ux * L * t, q[1] - a[1] - uy * L * t)
            if best is None or d < best[0]:
                best = (d, m, a, b, r)
        _, m, a, b, r = best
        out[q] = band({q}, a, b, r, tones, bias, hi)[q]
    return out


# ------------------------------------------------------------------ fists and feet

def fist(wr, fi, r=4.4, bias=0):
    """A wrapped fist on the end of a forearm, knuckles toward `fi`: cream wrap over the wrist and
    the back of the hand, a keyline where the wrap stops at the knuckles, bare fingers in front."""
    ux, uy, L = _unit(fi[0] - wr[0], fi[1] - wr[1])
    nx, ny = -uy, ux
    cx, cy = fi[0] - ux * 0.5, fi[1] - uy * 0.5
    body = set()
    for y in range(int(cy - 8), int(cy + 9)):
        for x in range(int(cx - 8), int(cx + 9)):
            t = (x - cx) * ux + (y - cy) * uy
            s = (x - cx) * nx + (y - cy) * ny
            if (t / (r + 1.3)) ** 2 + (s / (r + 0.3)) ** 2 <= 1.0:
                body.add((x, y))
    wrap = capsule(wr, (cx, cy), r + 0.4, r + 0.6) | body
    part = {}
    ramp = 'ghijlm'
    for q in wrap:
        t = (q[0] - cx) * ux + (q[1] - cy) * uy
        s = (q[0] - cx) * nx + (q[1] - cy) * ny
        lit = (-(s if nx * LIGHT[0] + ny * LIGHT[1] > 0 else -s)) / (r + 0.5)
        i = 1 if lit < -0.35 else (2 if lit < 0.2 else (3 if lit < 0.6 else 4))
        part[q] = ramp[min(5, i + bias)]
    # the knuckles: the wrap stops a little behind the fist's front, the fingers are skin
    for q in list(part):
        t = (q[0] - cx) * ux + (q[1] - cy) * uy
        if t > r * 0.28:
            s = (q[0] - cx) * nx + (q[1] - cy) * ny
            part[q] = 'kuvw'[0] if abs(t - r * 0.28) < 0.75 else ('t' if s * (nx * LIGHT[0] + ny * LIGHT[1]) > 0 else 'u')
    # finger splits across the front
    for k in (-1.6, 1.6):
        for d in (0.4, 1.4):
            x = int(round(cx + ux * (r * 0.28 + d + 0.8) + nx * k))
            y = int(round(cy + uy * (r * 0.28 + d + 0.8) + ny * k))
            if (x, y) in part:
                part[(x, y)] = 'k'
    # a groove where the wrist band meets the hand wrap
    gx, gy = cx - ux * (r * 0.9), cy - uy * (r * 0.9)
    for s in range(-6, 7):
        q = (int(round(gx + nx * s * 0.5)), int(round(gy + ny * s * 0.5)))
        if q in part and part[q] in 'ghij':
            part[q] = 'l' if bias else 'j'
    return part


def flat_hand(wr, direction=-1, bias=0):
    """An open hand planted on the floor, fingers spread toward `direction` (-1 left, 1 right), the
    wrap round the wrist - it is what he leans on in the punish window."""
    x0, y0 = int(round(wr[0])), int(round(wr[1]))
    part = {}
    # the wrapped wrist
    for dy in range(-2, 2):
        for dx in range(-2, 3):
            part[(x0 + dx, y0 + dy)] = 'hhijl'[min(4, max(0, dx * direction + 2 + bias))] if dy < 1 else 'j'
    # the palm and fingers along the floor
    for dx in range(0, 8):
        x = x0 + direction * (dx + 2)
        for yy in range(y0 + 1, 95):
            part[(x, yy)] = 'u' if yy == y0 + 1 else ('v' if yy < 94 else 'w')
    for dx in (4, 6):
        x = x0 + direction * (dx + 2)
        part[(x, 93)] = 'k'
        part[(x, 94)] = 'k'
    return part


def foot(ank, deg, ln=11.0, hi=4.6, bias=0, floor=95):
    """A bare foot at any angle, hanging from the ankle: the ankle sits on top of the instep and the
    sole is `hi` below it, so a planted foot stands on the floor. Heel, instep, rounded toes; toe
    splits keylined."""
    a = math.radians(deg)
    ux, uy = math.cos(a), math.sin(a)
    # 'up' out of the top of the foot: the side that faces up the screen
    nx, ny = uy, -ux
    if ny > 0:
        nx, ny = -nx, -ny
    # a foot planted near the floor is as tall as the room it has, so its sole lands on the floor
    if ank[1] > floor - 9 and abs(uy) < 0.35:
        hi = max(2.6, min(hi, floor - 1 - ank[1] + 0.5))
    local = [(-2.6, -hi), (-2.6, -hi * 0.25), (-1.2, 0.0), (1.5, 0.0), (ln * 0.72, -hi * 0.46),
             (ln * 0.97, -hi * 0.58), (ln, -hi * 0.86), (ln * 0.94, -hi - 0.3), (-2.0, -hi - 0.3)]
    pts = [(ank[0] + ux * t + nx * s, ank[1] + uy * t + ny * s) for t, s in local]
    m = poly(pts)
    m = {q for q in m if q[1] <= floor - 1}
    part = {}
    for q in m:
        t = (q[0] - ank[0]) * ux + (q[1] - ank[1]) * uy
        s = (q[0] - ank[0]) * nx + (q[1] - ank[1]) * ny
        f = (s + hi) / hi
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


# ------------------------------------------------------------------ clothes

def trousers(p):
    """Both legs' gi trousers and the seat: thigh and the top of the shin, torn square across each
    leg; navy fading to violet toward the hems, anchored to the pose's hips."""
    out = {}
    py = p['pelvis'][1]
    for key, bias, r in (('rear', 1, (7.2, 6.4, 4.8)), ('lead', 0, (8.0, 7.0, 5.2))):
        hip, knee, ank, _ = p[key]
        ux, uy, L = _unit(ank[0] - knee[0], ank[1] - knee[1])
        cut = (knee[0] + ux * L * 0.32, knee[1] + uy * L * 0.32)
        segs = [(hip, knee, r[0], r[1]), (knee, cut, r[1], r[2])]
        part = limb(segs, bias=bias, tones='abcdef', hi=False)
        # torn hem: teeth across the leg at the cut
        nx, ny = -uy, ux
        for q in list(part):
            t = (q[0] - cut[0]) * ux + (q[1] - cut[1]) * uy
            s = (q[0] - cut[0]) * nx + (q[1] - cut[1]) * ny
            tooth = 1.6 * abs(math.sin(s * 0.95))
            if t > -0.5 + tooth:
                del part[q]
        out[key] = part
    # the seat
    cx, cy, cr = p['pelvis']
    ax, ay, _ = p['chest']
    top = (ax + (cx - ax) * (BELT_T - 0.06), ay + (cy - ay) * (BELT_T - 0.06))
    seat = limb([(top, (cx, cy + 1.5), cr + 1.4, cr + 1.2)], tones='abcdef', hi=False)
    out['seat'] = seat
    NAVY, VIOLET = 'abcdef', 'ABCDEF'
    for part in out.values():
        for (x, y), k in list(part.items()):
            if k in NAVY and (y >= py + 9 or (y == py + 8 and (x + y) % 2 == 0)):
                part[(x, y)] = VIOLET[NAVY.index(k)]
    return out


def torso_frame(p):
    """(chest centre, unit down the body, unit out of the chest front (toward screen right), length)"""
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    ux, uy, L = _unit(px_ - cx, py_ - cy)
    nx, ny = -uy, ux
    if nx < 0:
        nx, ny = -nx, -ny
    return (cx, cy), (ux, uy), (nx, ny), L


BELT_T = 0.86      # where the belt crosses the torso, as a fraction chest -> pelvis
V_CLOSE = 0.62     # how far down the torso the lapels meet


def V_OPEN(t, r):
    """the open front's edges (s from, s to) at t down the torso; empty below V_CLOSE"""
    if t <= 0.04 or t >= V_CLOSE:
        return (1.0, -1.0)
    f = (t - 0.04) / (V_CLOSE - 0.04)
    mid = 0.62 * r
    half = 0.48 * r * (1.0 - f)
    return (mid - half, mid + half)


def jacket(p, back=False):
    """The gi on a pitched torso, from the collar down to the belt. Front (the rush): closed over his
    back and side, with a window of bare chest on the side he faces - the window's edges are the two
    lapels, so the keyline stamped round the gi lands on them. Back (the rush pass): one closed field."""
    (cx, cy), (ux, uy), (nx, ny), L = torso_frame(p)
    cr = p['chest'][2]
    pr = p['pelvis'][2]
    shell = grow(capsule((cx, cy), p['pelvis'][:2], cr, pr), 1)
    part = {}
    for (x, y) in shell:
        t = ((x - cx) * ux + (y - cy) * uy) / L
        s = (x - cx) * nx + (y - cy) * ny
        r = cr + (pr - cr) * max(0.0, min(1.0, t))
        if t > BELT_T + 0.04:
            continue
        # the open front: a wedge of chest from the collar down to where the lapels close
        lo, hi = V_OPEN(t, r)
        if not back and lo < s < hi:
            continue
        lvl = -s / (r + 1.0) * 0.65 - t * 0.35
        k = 'b' if lvl > 0.30 else ('c' if lvl > -0.12 else ('d' if lvl > -0.45 else 'e'))
        if not back and (lo - 2.2 <= s <= lo or hi <= s <= hi + 2.2) and t < V_CLOSE:
            k = 'b' if t < V_CLOSE * 0.6 else 'c'     # the lapels, rolled toward the light
        part[(x, y)] = k
    return part


def caps(p):
    """Torn sleeve caps over both deltoids."""
    out = []
    for key, bias in (('far', 1), ('near', 0)):
        sh, el = p[key][0], p[key][1]
        ux, uy, L = _unit(el[0] - sh[0], el[1] - sh[1])
        m = ellipse(sh[0] - ux * 1.5, sh[1] - uy * 1.5 - 1.0, 7.2, 6.2)
        part = {}
        for q in m:
            t = (q[0] - sh[0]) * ux + (q[1] - sh[1]) * uy
            s = (q[0] - sh[0]) * (-uy) + (q[1] - sh[1]) * ux
            if t > 1.8 + 1.8 * abs(math.sin(s * 1.05)):
                continue
            lit = (q[0] - sh[0]) * LIGHT[0] + (q[1] - sh[1]) * LIGHT[1]
            i = 1 if lit > 3.0 else (2 if lit > -1.0 else 3)
            part[q] = 'abcde'[min(4, i + bias)]
        out.append(part)
    return out


def belt(p):
    """The rope round his hips, kept near level however far he leans, with the knot at the front."""
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
    part = {}
    for y in range(int(cyl - 8), int(cyl + 8)):
        for x in range(int(cx - half - 3), int(cx + half + 4)):
            t = (x - cx) * ux + (y - cyl) * uy
            s = (x - cx) * nx + (y - cyl) * ny
            if abs(t) <= half and -1.5 <= s <= 1.5:
                row = int(round(s + 1.5))
                part[(x, y)] = ('nnop', 'nopq', 'opqr', 'opqr')[min(3, row)][(x + y) % 4]
    # the knot on the front of the hips (the side he faces)
    kx, ky = cx + ux * (half - 1.0), cyl + uy * (half - 1.0)
    for q in ellipse(kx, ky, 2.6, 2.4):
        part[q] = 'n' if (q[0] - kx) + (q[1] - ky) < -1 else ('o' if (q[0] - kx) + (q[1] - ky) < 1 else 'q')
    return part


def beads(p):
    """The juzu across his chest, swinging with the lunge (sway)."""
    sx, sy = p['near'][0]
    fx, fy = p['far'][0]
    sway = p.get('sway', 0.0)
    out = []
    n = 6
    for i in range(n):
        t = i / (n - 1.0)
        x = fx - 2.0 + (sx - fx + 4.0) * t + sway * math.sin(math.pi * t) * 1.2
        y = fy - 5.0 + math.sin(math.pi * t) * 6.0 + sway * 0.4
        out.append((x, y))
    return out


BEAD = ["kkkk", "kGHk", "kHIk", "kkkk"]


# ------------------------------------------------------------------ the figure

def draw(p):
    cv = Canvas()
    back = p.get('back', False)

    # far leg: shin and foot, a step darker
    hip, knee, ank, deg = p['rear']
    cv.stamp(limb([(knee, ank, 4.2, 3.6)], bias=1))
    cv.stamp(foot(ank, deg, ln=9.5, hi=4.0, bias=1))

    # far arm, a step darker; its fist or its flat hand
    sh, el, wr, fi = p['far']
    cv.stamp(limb([(sh, el, 5.0, 4.4), (el, wr, 4.4, 3.8)], bias=1))
    if p.get('far_hand') == 'flat':
        cv.stamp(flat_hand(wr, -1, bias=1))
    else:
        cv.stamp(fist(wr, fi, 3.8, bias=1))

    # lead leg: shin and foot
    hip, knee, ank, deg = p['lead']
    cv.stamp(limb([(knee, ank, 4.8, 4.2)]))
    cv.stamp(foot(ank, deg))

    # the torso's skin, then the trousers over his hips and thighs, then the gi over his chest
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    cv.stamp(limb([((cx, cy), (px_, py_), cr, pr)], tones='stuvw'))
    if not back:
        _chest_detail(cv, p)
    tr = trousers(p)
    for k in ('rear', 'seat', 'lead'):
        cv.stamp(tr[k])
    jk = jacket(p, back)
    cv.stamp(jk)
    if back:
        _mark(cv, p, jk)
    elif p.get('beads', True):
        from lib import amap
        for bx, by in beads(p):
            cv.stamp(amap(BEAD, int(round(bx)) - 1, int(round(by)) - 1), outline=False)
    cv.stamp(belt(p))

    # the near arm, its cap over its shoulder
    sh, el, wr, fi = p['near']
    cv.stamp(limb([(sh, el, 5.4, 4.8), (el, wr, 4.8, 4.2)]))
    if p.get('near_hand') == 'flat':
        cv.stamp(flat_hand(wr, 1))
    else:
        cv.stamp(fist(wr, fi, 4.3))
    for c in caps(p):
        cv.stamp(c)

    # the head last: it sits between the shoulders, in front of the caps - hung low in the punish
    # window it would otherwise lose its beard behind them
    hdx, hdy = p['head']
    eye, jaw = p.get('face', (0, 0))
    if back:
        cv.stamp(FC.back_head_part(hdx, hdy), outline=False)
        cv.stamp(FC.back_earring_part(hdx, hdy), outline=False)
    else:
        cv.stamp(FC.neck_part(hdx, hdy, rows=5), outline=False)
        cv.stamp(FC.head_part(eye, jaw, hdx, hdy), outline=False)
        cv.stamp(FC.earring_part(hdx, hdy), outline=False)
    return cv


def _chest_detail(cv, p):
    """The strip of bare chest between the gi's back panel and the lapel: a pec shadow and the ab
    rungs, laid along the pitched torso."""
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    ux, uy, L = _unit(px_ - cx, py_ - cy)
    nx, ny = -uy, ux
    if nx < 0:
        nx, ny = -nx, -ny

    def at(t, s):
        return (int(round(cx + ux * L * t + nx * s)), int(round(cy + uy * L * t + ny * s)))
    skin = set('stuvw')
    for pts, key in (([at(0.30, -1.0), at(0.34, 2.5), at(0.30, 5.5)], 'w'),
                     ([at(0.52, 0.0), at(0.52, 4.0)], 'v'),
                     ([at(0.70, 0.0), at(0.70, 4.0)], 'v'),
                     ([at(0.35, 1.0), at(0.95, 1.5)], 'v')):
        from lib import polyline
        for q in polyline(pts):
            if cv.px.get(q) in skin:
                cv.px[q] = key


def _mark(cv, p, jk):
    """The 天 on his pitched back, fitted and painted by the mark artist's rig: what the near arm and
    its cap will cover is left out of the panel so it lands on the open back, and it shows as
    fragments once the arm is over it - the approved rush pass does the same."""
    import mark as MK
    sh, el, wr, fi = p['near']
    arm = capsule(sh, el, 5.4, 4.8) | capsule(el, wr, 4.8, 4.2)
    panel = set(jk) - grow(arm, 1)
    cv.stamp(MK.ten_fitted(panel, set(jk)), outline=False)
