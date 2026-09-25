"""A posable build of the approved beast, made only from the redesign rig's stable parts (imported
read-only). build(HOVER) reproduces frame.build('up', 0) pixel for pixel; see regress().

Pose fields (see HOVER for the defaults):
  wings, wings_left     wing pose dicts (right authored; the left is the mirror of wings_left or wings)
  wing_glow             1 = ember rims burning, 0 = cold (the membrane's torn edges unlit)
  tails_wave            Liam's headband tails
  tail                  (path, tip offset (dx, dy)) for the saddle-black tail and its white tip
  hind, hind_left       joints (absolute) for the hind legs; planted_hind puts the paws flat
  torso                 (dx, dy) for mantle, belly and chest
  front, front_left     joints (absolute) for the front legs; planted_front puts the paws flat
  neck, neck_left       (base, top) of the side necks
  side, side_left       kwargs for side_head() (right head; the left is mirrored)
  mid                   kwargs for mid_head()
"""
import copy
import math

import common as C  # noqa: F401  (sets sys.path for the redesign rig)
from pal import BCanvas, amap, fill, mir, poly
from shapes import capsule, chain, edge, poly_line, recolor
import body
import frame
import heads
import midmaps
import sidemaps
import wings
import faces

#WINGS (wings.py, driven by a pose dict instead of a pose name)

WING_UP = dict(copy.deepcopy(wings.POSES['up']), claw='up')
WING_DOWN = dict(copy.deepcopy(wings.POSES['down']), claw='down')


def wing_moved(P, dx=0, dy=0, sx=1.0, sy=1.0, about=None):
    """A wing pose moved, and scaled about a point (the shoulder by default): sx = sy = 0.3 is a wing
    only just tearing out of the back."""
    ax, ay = about or P['shoulder']

    def m(p):
        return (ax + (p[0] - ax) * sx + dx, ay + (p[1] - ay) * sy + dy)
    Q = dict(P)
    for k in ('shoulder', 'elbow', 'wrist', 'thumb'):
        Q[k] = m(P[k])
    for k in ('tips', 'burn', 'knuckles'):
        Q[k] = [m(p) for p in P[k]]
    for k in ('tears', 'holes'):
        Q[k] = [[m(p) for p in run] for run in P[k]]
    return Q


def wing_membrane(P, glow=1):
    pts = [P['shoulder'], P['elbow'], P['wrist']]
    for tip, tear in zip(P['tips'], P['tears']):
        pts.append(tip)
        pts.extend(tear)
    m = poly(pts)
    for h in P['holes']:
        m -= poly(h)
    part = fill(m, 'B')
    for tip in P['tips']:
        for q in poly_line([P['wrist'], tip]):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in part:
                        part[r] = 'A'
    upper = poly([P['shoulder'], P['elbow'], P['wrist'], P['tips'][0]] + P['tears'][0] + [P['tips'][1]])
    recolor(part, upper, 'C', only='B')
    arm_side = set()
    for q in poly_line([P['shoulder'], P['elbow'], P['wrist'], P['tips'][0]]):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                arm_side.add((q[0] + dx, q[1] + dy))
    bodyset = set(part)
    rimset = set()
    for (x, y) in bodyset:
        if (x, y) in arm_side:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in bodyset:
                rimset.add((x, y))
                break
    if glow <= 0:
        # cold: the torn edges go out; a scorched line stays where the rim burned
        for p in rimset:
            part[p] = 'q'
        return part
    for p in rimset:
        part[p] = 'u'
    for (bx, by) in P['burn']:
        for (x, y) in list(rimset):
            d = abs(x - bx) + abs(y - by)
            if d <= 1:
                part[(x, y)] = 'P'
            elif d <= 3:
                part[(x, y)] = 'v'
    if glow < 1:
        # dying: only the deepest points of the tears still smoulder
        for p in rimset:
            part[p] = {'u': 'r', 'v': 's', 'P': 'u'}[part[p]]
    return part


def _rp(p):
    return (int(round(p[0])), int(round(p[1])))


def wing_bones(P):
    arm = capsule(P['shoulder'], P['elbow'], 3.4, 2.8) | capsule(P['elbow'], P['wrist'], 2.8, 2.2)
    fingers = set()
    for tip in P['tips']:
        fingers |= capsule(P['wrist'], tip, 1.5, 0.6)
    for (kx, ky) in P['knuckles']:
        fingers |= capsule((kx, ky), (kx, ky), 1.8, 1.8)
    b = fill(arm | fingers, 'c')
    recolor(b, edge(b, 0, -1, 1), 'd')
    recolor(b, edge(b, -1, 0, 1), 'e')
    recolor(b, edge(b, 0, 1, 1), 'b')
    for (kx, ky) in P['knuckles']:
        q = _rp((kx, ky - 1))
        if q in b:
            b[q] = 'f'
    wx, wy = P['wrist']
    knuckle = fill(capsule((wx - 2, wy), (wx + 2, wy), 2.6, 2.6), 'd')
    recolor(knuckle, edge(knuckle, 0, -1, 1), 'e')
    knuckle[_rp((wx - 1, wy - 2))] = 'f'
    return b, knuckle


def wing_claws(P):
    wx, wy = P['wrist']
    tx, ty = P['thumb']
    out = [wings.claw((wx - 3, wy - 1), (wx + 1, wy - 2), (tx, ty))]
    fx, fy = P['tips'][0]
    if P.get('claw', 'up') == 'up':
        out.append(wings.claw((fx - 4, fy + 1), (fx - 2, fy + 3), (fx + 2, fy - 1)))
    else:
        out.append(wings.claw((fx - 2, fy - 3), (fx, fy - 4), (fx, fy + 3)))
    return out


def wing_parts(P, glow=1):
    b, kn = wing_bones(P)
    return [wing_membrane(P, glow), b, kn] + wing_claws(P)


#LEGS (body.py's front and hind legs, every joint a parameter; details ride their joint)

FRONT = dict(shoulder=(119, 100), sh_end=(124, 110), arm_top=(123, 108), elbow=(128, 119),
             fore_top=(127, 121), wrist=(124, 137), paw=(123, 143))
HIND = dict(hip=(136, 110), hock=(152, 128), ankle=(152, 139), paw=(153, 144))
_F_TUFT = [(130, 112), (137, 117), (133, 118), (138, 123), (131, 124), (128, 126)]
_F_CUTS = [[(130, 115), (134, 120)], [(127, 113), (128, 118)]]
_F_GROOVE = [(128, 124), (126, 133)]
_SH_CUT = [(116, 104), (122, 113)]
_H_TUFT = [(146, 110), (158, 115), (152, 118), (159, 122), (152, 124)]
_H_CUTS = [[(149, 115), (154, 121)], [(141, 118), (146, 124)]]


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _carry(pts, o0, a0, o1, a1):
    da = a1 - a0
    c, s = math.cos(da), math.sin(da)
    out = []
    for (x, y) in pts:
        rx, ry = x - o0[0], y - o0[1]
        if abs(da) > 1e-9:
            rx, ry = rx * c - ry * s, rx * s + ry * c
        out.append((o1[0] + rx, o1[1] + ry))
    return out


def front_leg(J=None):
    F = dict(FRONT)
    F.update(J or {})
    shoulder = fill(capsule(F['shoulder'], F['sh_end'], 10, 9), 'c')
    body.black_shade(shoulder)
    cut = _carry(_SH_CUT, FRONT['shoulder'], _ang(FRONT['shoulder'], FRONT['sh_end']),
                 F['shoulder'], _ang(F['shoulder'], F['sh_end']))
    for q in poly_line(cut):
        if q in shoulder and shoulder[q] == 'c':
            shoulder[q] = 'b'
    upper = fill(capsule(F['arm_top'], F['elbow'], 8, 7), 't')
    a0, a1 = _ang(FRONT['arm_top'], FRONT['elbow']), _ang(F['arm_top'], F['elbow'])
    upper.update({p: 't' for p in poly(_carry(_F_TUFT, FRONT['elbow'], a0, F['elbow'], a1))})
    recolor(upper, edge(upper, 0, -1, 1), 'u')
    recolor(upper, edge(upper, 1, 0, 1), 's')
    recolor(upper, edge(upper, 0, 1, 2), 's')
    recolor(upper, edge(upper, 0, 1, 1), 'r')
    for seg in _F_CUTS:
        for q in poly_line(_carry(seg, FRONT['elbow'], a0, F['elbow'], a1)):
            if q in upper:
                upper[q] = 'k'
    fore = fill(capsule(F['fore_top'], F['wrist'], 6.4, 5.4), 'x')
    recolor(fore, edge(fore, -1, 0, 2), 'w', only='x')
    recolor(fore, edge(fore, 1, 0, 3), 'y')
    recolor(fore, edge(fore, 1, 0, 1), 'z')
    g = _carry(_F_GROOVE, FRONT['fore_top'], _ang(FRONT['fore_top'], FRONT['wrist']),
               F['fore_top'], _ang(F['fore_top'], F['wrist']))
    for q in poly_line(g):
        if q in fore and fore[q] == 'x':
            fore[q] = 'y'
    return [shoulder, upper, fore]


def hind_leg(J=None):
    H = dict(HIND)
    H.update(J or {})
    thigh = fill(capsule(H['hip'], H['hock'], 10, 6.5), 't')
    a0, a1 = _ang(HIND['hip'], HIND['hock']), _ang(H['hip'], H['hock'])
    thigh.update({p: 't' for p in poly(_carry(_H_TUFT, HIND['hock'], a0, H['hock'], a1))})
    recolor(thigh, edge(thigh, 0, -1, 1), 'u')
    recolor(thigh, edge(thigh, 1, 0, 1), 's')
    recolor(thigh, edge(thigh, 0, 1, 2), 's')
    recolor(thigh, edge(thigh, 0, 1, 1), 'r')
    for seg in _H_CUTS:
        for q in poly_line(_carry(seg, HIND['hock'], a0, H['hock'], a1)):
            if q in thigh:
                thigh[q] = 'k'
    shin = fill(capsule(H['hock'], H['ankle'], 5, 4.6), 'x')
    recolor(shin, edge(shin, -1, 0, 1), 'w', only='x')
    recolor(shin, edge(shin, 1, 0, 2), 'y')
    recolor(shin, edge(shin, 1, 0, 1), 'z')
    return [thigh, shin]


# Planted paws: the hanging maps with the claws cut down to stubs on the ground row.
FRONT_PAW_PLANTED = body.FRONT_PAW[:11] + [".kdk. kdck. kdck. kdk."]
HIND_PAW_PLANTED = body.HIND_PAW[:9] + [".kdk. kdk.k dk.kd k."]
FRONT_PAW_OFF = (body.FRONT_PAW_XY[0] - FRONT['paw'][0], body.FRONT_PAW_XY[1] - FRONT['paw'][1])
HIND_PAW_OFF = (body.HIND_PAW_XY[0] - HIND['paw'][0], body.HIND_PAW_XY[1] - HIND['paw'][1])


def paw(front=True, centre=None, planted=False):
    if front:
        rows = FRONT_PAW_PLANTED if planted else body.FRONT_PAW
        c, off = centre or FRONT['paw'], FRONT_PAW_OFF
    else:
        rows = HIND_PAW_PLANTED if planted else body.HIND_PAW
        c, off = centre or HIND['paw'], HIND_PAW_OFF
    return amap(rows, int(round(c[0] + off[0])), int(round(c[1] + off[1])))


def planted_centre(front, ground_y, x=None):
    """The paw centre that puts a planted paw's claw-stub row on ground_y."""
    rows = FRONT_PAW_PLANTED if front else HIND_PAW_PLANTED
    off = FRONT_PAW_OFF if front else HIND_PAW_OFF
    base = FRONT['paw'] if front else HIND['paw']
    return (base[0] if x is None else x, ground_y - (len(rows) - 1) - off[1])


#TORSO, NECKS, TAIL

def torso(dx=0, dy=0):
    parts = [body.mantle(dy), body.belly(dy), body.chest(dy)]
    return [C.shift(p, dx, 0) for p in parts] if dx else parts


def side_neck(base=(118, 98), top=(142, 82)):
    n = fill(capsule(base, top, 10, 10), 'c')
    body.black_shade(n)
    return n


TAIL_UP = body.TAIL_PATHS['up']
TAIL_TIP_PTS = [(6, 118), (5, 110), (8, 102), (10, 106), (12, 95), (15, 103), (19, 94), (18, 106),
                (16, 116), (12, 121)]


def tail(path):
    t = fill(chain(path, 4.2, 2.8), 'c')
    recolor(t, edge(t, 0, -1, 1), 'd')
    recolor(t, edge(t, 0, 1, 1), 'b')
    recolor(t, edge(t, -1, 0, 1), 'e')
    return t


def tail_tip(dx=0, dy=0, pts=None):
    t = fill(poly([(x + dx, y + dy) for (x, y) in (pts or TAIL_TIP_PTS)]), 'x')
    recolor(t, edge(t, -1, 0, 1), 'w')
    recolor(t, edge(t, 1, 0, 1), 'y')
    recolor(t, edge(t, 0, 1, 1), 'y')
    return t


#HEADS

MID_DY0 = int(round(frame.MID['cy'] - heads.HY))                     # 3: the maps' row offset at rest
SIDE_MDX0 = int(round(frame.SIDE['cx'] - frame.SIDE_REF[0]))          # 0
SIDE_MDY0 = int(round(frame.SIDE['cy'] - frame.SIDE_REF[1]))          # -4


def mid_head(cv, dx=0, dy=0, mouth='snarl', eyes='open', low_dx=0, low_dy=0, brows=True, ears=1, eye_glow=1,
             tongue_dx=0, tongue_dy=0, xf_extra=None):
    """The middle head, with Liam's headband. mouth: 'snarl' (approved), 'inhale' (jaw dropped, fire in the
    throat), 'gape' (jaw dropped, dark throat). eyes: 'open', or a faces.MID_EYES name. ears: 1 burning,
    0 cold (tips out)."""
    xf = frame.xf(frame.MID, 0, dx, dy)
    low = frame.xf(frame.MID, 0, dx + low_dx, dy + low_dy) if (low_dx or low_dy) else None
    procedural = mouth == 'snarl' and eyes == 'open'
    tmp = BCanvas()
    heads.build(tmp, xf, with_headband=True, features=procedural, low=low, brows=brows)
    faces.cool_ears(tmp.px, xf, ears)
    cv.px.update(tmp.px)
    off = MID_DY0 + dy
    if mouth == 'snarl':
        cv.stamp(midmaps.mouth_part(dx, off), outline=False)
        cv.stamp(C.shift(midmaps.tongue_part(0, off), dx + tongue_dx, tongue_dy), outline=False)
    elif mouth in ('inhale', 'gape'):
        mdy = off + 3
        if mouth == 'inhale':
            cv.stamp(midmaps.inhale_glow(dx, mdy), outline=False)
        else:
            cv.stamp(faces.dark_maw(dx, mdy), outline=False)
        for p in midmaps.inhale_mouth(dx, mdy):
            cv.stamp(p, outline=False)
        cv.stamp(C.shift(midmaps.inhale_tongue(0, mdy), dx + tongue_dx, tongue_dy), outline=False)
    if eyes == 'open':
        for e in midmaps.eye_parts(dx, off):
            cv.stamp(faces.glow_eye(e, eye_glow), outline=False)
    else:
        for e in faces.mid_eyes(eyes, dx, off):
            cv.stamp(faces.glow_eye(e, eye_glow), outline=False)
    return xf


def side_head(dx=0, dy=0, mouth='snarl', eyes='open', low_dx=0, low_dy=0, ears=1, eye_glow=1):
    """The RIGHT side head on its own canvas (mirror it for the left). mouth 'snarl' or 'roar' (jaw
    dropped 4)."""
    side = BCanvas()
    xf = frame.xf(frame.SIDE, 0, dx, dy)
    low = frame.xf(frame.SIDE, 0, dx + low_dx, dy + low_dy)
    heads.build(side, xf, tongue_flip=True, features=False, low=low)
    faces.cool_ears(side.px, xf, ears)
    mdx, mdy = SIDE_MDX0 + dx, SIDE_MDY0 + dy
    roar = mouth == 'roar'
    rows = sidemaps.ROAR if roar else sidemaps.MOUTH
    side.stamp(amap(rows, sidemaps.MOUTH_XY[0] + mdx, sidemaps.MOUTH_XY[1] + mdy), outline=False)
    tdy = sidemaps.ROAR_TONGUE_DY if roar else 0
    side.stamp(amap(sidemaps.TONGUE, sidemaps.TONGUE_XY[0] + mdx, sidemaps.TONGUE_XY[1] + mdy + tdy),
               outline=False)
    if eyes == 'open':
        for rows, (x0, y0) in ((sidemaps.FAR_EYE, sidemaps.FAR_EYE_XY), (sidemaps.NEAR_EYE, sidemaps.NEAR_EYE_XY)):
            side.stamp(faces.glow_eye(amap(rows, x0 + mdx, y0 + mdy), eye_glow), outline=False)
    else:
        for e in faces.side_eyes(eyes, mdx, mdy):
            side.stamp(faces.glow_eye(e, eye_glow), outline=False)
    return side


#THE WHOLE BEAST

HOVER = dict(
    wings=WING_UP, wings_left=None, wing_glow=1, wing_glow_left=None,
    tails_wave=0,
    tail=(TAIL_UP, (0, 0)),
    hind=None, hind_left=None, planted_hind=False,
    torso=(0, 0),
    front=None, front_left=None, planted_front=False,
    neck=((118, 98), (142, 82)), neck_left=None,
    side=dict(), side_left=None,
    mid=dict(),
    hide=(),
)


def make(base=None, **kw):
    P = copy.deepcopy(base or HOVER)
    for k, v in kw.items():
        P[k] = v
    return P


def _paw_centre(J, base):
    return (J or {}).get('paw', base['paw'])


def build(P):
    hide = set(P.get('hide', ()))
    cv = BCanvas()
    if 'wings' not in hide:
        wl = P['wings_left'] or P['wings']
        gl = P['wing_glow_left'] if P.get('wing_glow_left') is not None else P['wing_glow']
        for p in wing_parts(wl, gl):
            cv.stamp(mir(p))
        for p in wing_parts(P['wings'], P['wing_glow']):
            cv.stamp(p)
    mid_kw = P.get('mid', {})
    mid_xf = frame.xf(frame.MID, 0, mid_kw.get('dx', 0), mid_kw.get('dy', 0))
    if 'tails' not in hide:
        for t in heads.headband_tails(mid_xf, wave=P.get('tails_wave', 0)):
            cv.stamp(t)
    if 'tail' not in hide:
        path, (tdx, tdy) = P['tail']
        cv.stamp(tail(path))
        cv.stamp(tail_tip(tdx, tdy, P.get('tail_tip_pts')))
    # hind legs, then their paws
    hr = hind_leg(P['hind'])
    hl = hind_leg(P['hind_left']) if P['hind_left'] is not None else hr
    for a, b in zip(hl, hr):
        if P['hind_left'] is None:
            cv.stamp(dict(list(b.items()) + list(mir(a).items())))
        else:
            cv.stamp(mir(a))
            cv.stamp(b)
    pr = paw(False, _paw_centre(P['hind'], HIND), P['planted_hind'])
    pl = paw(False, _paw_centre(P['hind_left'], HIND), P['planted_hind']) if P['hind_left'] is not None else pr
    cv.stamp(mir(pl), outline=False)
    cv.stamp(pr, outline=False)
    if 'torso' not in hide:
        for p in torso(*P['torso']):
            cv.stamp(p)
    fr = front_leg(P['front'])
    fl = front_leg(P['front_left']) if P['front_left'] is not None else fr
    for a, b in zip(fl, fr):
        if P['front_left'] is None:
            cv.stamp(dict(list(b.items()) + list(mir(a).items())))
        else:
            cv.stamp(mir(a))
            cv.stamp(b)
    pr = paw(True, _paw_centre(P['front'], FRONT), P['planted_front'])
    pl = paw(True, _paw_centre(P['front_left'], FRONT), P['planted_front']) if P['front_left'] is not None else pr
    cv.stamp(mir(pl), outline=False)
    cv.stamp(pr, outline=False)
    nb, nt = P['neck']
    nr = side_neck(nb, nt)
    nl = side_neck(*P['neck_left']) if P.get('neck_left') else nr
    if P.get('neck_left'):
        cv.stamp(mir(nl))
        cv.stamp(nr)
    else:
        cv.stamp(dict(list(nr.items()) + list(mir(nl).items())))
    if 'side' not in hide:
        right = side_head(**P.get('side', {}))
        left = side_head(**P['side_left']) if P.get('side_left') is not None else right
        cv.px.update(mir(left.px))
        cv.px.update(right.px)
    if 'mid' not in hide:
        mid_head(cv, **mid_kw)
    # paws brought round in front of everything (lying down, the chin rests between them)
    for (x, y) in P.get('paws_front', ()):
        c = planted_centre(True, 151 if y is None else y, x)
        cv.stamp(paw(True, c, True), outline=False)
    return cv


def regress():
    from imgdiff import pixel_diff
    a = build(HOVER).image()
    b = frame.build('up', 0).image()
    d = pixel_diff(a, b)
    print('pose.build(HOVER):', d or 'pixel-identical to frame.build("up", 0)')
    return d is None


if __name__ == '__main__':
    import sys
    sys.exit(0 if regress() else 1)
