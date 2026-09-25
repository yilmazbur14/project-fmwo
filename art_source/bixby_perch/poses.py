"""The perch set's poses, in sheet order, on 192x160 frames.

  0-1 perch_land   2-3 perch   4-6 volley   7-9 inhale   10 rear_back   11-12 perch_breath
  13 spent         14-15 release

Offsets are relative to the approved placements: middle head frame.MID (95.5, 43), side head frame.SIDE
(156, 70), front leg rig_body.FRONT. Wings are rig_wings-style poses.

Where the heads are: in the hang they lean out below the rope. For the volley, the rear back and the
breath the middle head rears up through the gate's doorway in the top rope (screen x 852..1067, frame
columns 60..131 with him on x 960), where there is no rope to cross it, so its maw can sit high: the
breath's cone has to start within 29 texels of the rope, or the strip under the rope is a safe pocket.
"""
import copy

from common import RW
import rig_fx as FX
from perch import fore
import fx
import throwback

# The wings on the rope: raised up and out over the crowd, the arm rising outside the hind leg so the
# leg stands clear against the mat, the membrane spread from the wrist out to the frame edge. Its
# claws top out at row 5: a wing may rise 2 rows at most (the headroom stops at row 3).
PERCH_WING = dict(
    shoulder=(134, 92), elbow=(158, 54), wrist=(168, 14), thumb=(162, 6),
    tips=[(188, 9), (190, 36), (189, 66), (181, 97)],
    tears=[[(185, 14), (188, 19), (182, 21), (186, 26), (180, 28), (186, 31)],
           [(186, 42), (189, 47), (182, 49), (186, 55), (180, 58), (186, 61)],
           [(185, 72), (186, 78), (180, 79), (182, 86), (176, 88), (180, 93)],
           [(175, 101), (170, 97), (167, 104), (161, 101), (157, 107), (151, 104), (145, 109),
            (139, 106)]],
    holes=[[(175, 17), (179, 19), (176, 23), (173, 21)], [(181, 38), (184, 40), (181, 44)],
           [(178, 64), (181, 66), (178, 70)]],
    burn=[(180, 28), (180, 58), (176, 88), (167, 104), (157, 107)],
    knuckles=[(177, 11), (179, 25), (179, 41), (174, 58)],
    claw='up')
SHOULDER = PERCH_WING['shoulder']


def wing(dx=0, dy=0, sx=1.0, sy=1.0):
    # drawn a touch narrower about the shoulder, so the tips keep the approved frames' 2px side margin
    return RW.moved(PERCH_WING, dx, dy, sx * 0.965, sy, about=SHOULDER)


WING = wing()
WING_HIGH = wing(0, -2)                 # braced and raised: the grab, the volley, the rear back, the blast
WING_DOWN = wing(0, 6, 1.0, 0.92)       # swept down as the body swings through
WING_DROOP = wing(-1, 9, 0.97, 0.88)    # spent

REST_MID, REST_SIDE = 37, 31            # the hang: the heads' offsets from their approved placements


def hind(dy=0, hock=(151, 55), hip=(131, 77)):
    """The right hind leg on the rope: the paw holds the rope and never moves; the rest rides the body."""
    return dict(paw=(146, 33), ankle=(146, 42), hock=(hock[0], hock[1] + dy), hip=(hip[0], hip[1] + dy))


def neck(body_dy, side_dy, side_dx=0):
    return ((118, 98 + body_dy), (142 + side_dx, 82 + side_dy))


def hang(dy=0, mid_dy=REST_MID, side_dy=REST_SIDE, side_dx=0, fore_dy=6, **kw):
    """The hang with the body `dy` px lower than the rest pose (heads, torso and forelegs ride it)."""
    P = dict(
        wings=WING, hide_band_tails=True, tail_path=None,
        hind=hind(dy), grip='hook',
        torso=(0, 8 + dy), front=fore(fore_dy + dy),
        neck=neck(8 + dy, side_dy + dy, side_dx),
        side=dict(dy=side_dy + dy, dx=side_dx), mid=dict(dy=mid_dy + dy),
    )
    P.update(kw)
    return P


#MOUTHS: where each maw's fire comes from, from the head placement.
def mid_mouth(mid):
    """The approved middle head's throat: the snarl's, or the dropped jaw's (inhale, yelp) glow."""
    off = 3 + mid.get('dy', 0) + mid.get('bob', 0)
    dx = mid.get('dx', 0)
    if mid.get('mouth', 'snarl') == 'snarl':
        return (96 + dx, 62 + off)
    return (96 + dx, 67 + off + 3)


def side_mouth(side, out=False):
    """The approved right side head's throat (the left mirrors). The roar drops the jaw and the throat
    with it. `out`: the head turned outward."""
    dx, dy = side.get('dx', 0), side.get('dy', 0) + side.get('bob', 0)
    x, y = 151 + dx, 88 + dy
    if side.get('mouth', 'snarl') == 'roar':
        y += 3
    if out:
        x = 191 - (x - 121)
    return (x, y)


def rigfx(f):
    """The redesign rig's effects take (cv, pose); perch.build calls fx(cv)."""
    return lambda cv: f(cv, None)


def mirror_pt(p):
    return (191 - p[0], p[1])


def arc(frm, to, bend, n=8):
    """Points on a curve from frm to to, bowed sideways by `bend` px (positive bows toward +x)."""
    (x0, y0), (x1, y1) = frm, to
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t + bend * 4 * t * (1 - t)
        y = y0 + (y1 - y0) * t
        pts.append((x, y))
    return pts


def suction_paths(mm, sm):
    """Streaks sweeping in from below and outside into each maw (inside the frame, below row 159)."""
    paths = []
    lm = mirror_pt(sm)
    for k in (-1, 1):
        paths.append(arc((mm[0] + k * 34, 158), (mm[0] + k * 3, mm[1] + 3), k * 6))
        paths.append(arc((mm[0] + k * 16, 159), (mm[0] + k * 2, mm[1] + 5), -k * 4))
    for (tx, ty), out in ((sm, 1), (lm, -1)):
        paths.append(arc((tx + out * 28, ty + 34), (tx + out * 2, ty + 3), out * 5))
        paths.append(arc((tx - out * 6, 159), (tx, ty + 5), out * 5))
    return [[(x, min(159, y)) for (x, y) in pth] for pth in paths]


def frames():
    """Poses 0..14 in sheet order, each with 'mouths' = (middle, left, right). Frame 15 is release_upright."""
    out = []

    # 0-1 PERCH_LAND: the grab (talons clamp, wings braced high, the body still swung up, forepaws
    # reaching), then the swing through (the body overshoots below the rest, wings swept down)
    f = hang(-5, mid_dy=35, side_dy=31, wings=WING_HIGH, fore_dy=4)
    f['hind'] = hind(-5, hock=(153, 53), hip=(134, 74))
    f['front'] = fore(-2, paw=(124, 139), wrist=(125, 133), elbow=(131, 116))
    out.append(f)
    f = hang(3, wings=WING_DOWN, fore_dy=5)
    f['hind'] = hind(3, hock=(149, 58), hip=(130, 79))
    out.append(f)

    # 2-3 PERCH: the hang, breathing
    out.append(hang(0))
    out.append(hang(1, wings=wing(0, 1)))

    # 4-6 VOLLEY: all three heads thrown back, maws gaping at the sky with the fire up in their throats;
    # the middle one reared up through the doorway. Each frame one head spits.
    mdraw, mmaw = throwback.mid(dy=-6, pitch=28, drop=10)
    sdraw, smaw = throwback.side(dx=0, dy=-6, pitch=16, drop=7)
    for i in range(3):
        f = hang(-4, mid_dy=0, side_dy=2, wings=WING_HIGH, fore_dy=4)
        f['torso'] = (0, 2)
        f['neck'] = neck(2, -4)
        f['hind'] = hind(-6, hock=(153, 53), hip=(134, 73))
        f['mid'] = dict(draw=mdraw)
        f['side'] = dict(draw=sdraw)
        spit = [mmaw, mirror_pt(smaw), smaw][i]
        f['fx'] = [fx.flash(spit[0], spit[1] - 4, 1.7 if i == 0 else 1.25, seed=i)]
        f['mouths'] = (mmaw, mirror_pt(smaw), smaw)
        out.append(f)

    # 7-9 INHALE: maws wide, chests swelling (least, most, between), air and embers dragged into the maws
    for i, (sw, ph) in enumerate(((0, 0.0), (2, 0.5), (1, 1.0))):
        f = hang(-sw, wings=wing(0, -min(2, sw)), fore_dy=6)
        f['mid'].update(mouth='inhale', low_dy=4 + sw)
        f['side'].update(mouth='roar', low_dy=3 + sw)
        f['front'] = fore(6 - sw, dx=sw)
        mm, sm = mid_mouth(f['mid']), side_mouth(f['side'])
        f['fx_paths'] = paths = suction_paths(mm, sm)
        f['fx'] = [fx.throat(mm[0], mm[1], 5.0), fx.throat(sm[0], sm[1], 3.5),
                   fx.throat(191 - sm[0], sm[1], 3.5), fx.wisps(paths, ph)]
        f['mouths'] = (mm, mirror_pt(sm), sm)
        out.append(f)

    # 10 REAR_BACK: reared up, the middle head through the doorway, jaws clamped on the fire, chests
    # puffed, wings braced high
    f = hang(0, mid_dy=0, side_dy=-2, side_dx=-2, wings=WING_HIGH, fore_dy=4)
    f['torso'] = (0, 0)
    f['neck'] = neck(0, -2, -2)
    f['hind'] = hind(-6, hock=(152, 54), hip=(133, 72))
    f['front'] = fore(0, dx=-3)
    mm, sm = mid_mouth(f['mid']), side_mouth(f['side'])
    f['fx'] = [fx.throat(mm[0], mm[1], 8.0, keys='kq'), fx.throat(sm[0], sm[1], 6.0, keys='kq'),
               fx.throat(191 - sm[0], sm[1], 6.0, keys='kq'),
               # embers spat at the lips
               fx.embers([(78, 70), (113, 70), (sm[0] - 9, sm[1] - 4), (191 - sm[0] + 9, sm[1] - 4)])]
    f['mouths'] = (mm, mirror_pt(sm), sm)
    out.append(f)

    # 11-12 PERCH_BREATH: the blast. The middle head stays up in the doorway, so its maw is as high as
    # the headroom allows; the side heads, turned out, just under the rope. The cone's apex is the top of
    # the middle maw; its 65-degree sides run out through the side maws. The middle jet pours straight
    # down, the side jets down and out along the sides, and the fan spreads from the apex.
    for i in range(2):
        f = hang(0, mid_dy=0, side_dy=-3, side_dx=10, side_out=True, wings=WING_HIGH, fore_dy=4)
        f['mid'].update(mouth='inhale', low_dy=4)
        f['side'].update(mouth='roar', low_dy=3)
        f['torso'] = (0, 0)
        f['neck'] = neck(0, -3, 0)
        f['hind'] = hind(-6, hock=(152, 56), hip=(132, 74))
        f['front'] = fore(2, dx=14, elbow=(142, 117), wrist=(147, 134), paw=(148, 141))
        mm = mid_mouth(f['mid'])
        sm = side_mouth(f['side'], out=True)
        apex = (96, mm[1] - 10)
        f['apex'] = apex
        f['fx'] = [fx.breath_cone(apex, [
            dict(mouth=(96, apex[1] + 2), angle=0, length=34, w0=6, w1=16, seed=i, open_end=True),
            dict(mouth=sm, angle=44, length=32 + 2 * i, w0=4.5, w1=12, seed=i + 3),
            dict(mouth=mirror_pt(sm), angle=-44, length=32 + 2 * i, w0=4.5, w1=12, seed=i + 5),
        ], 65, 50 + 3 * i, i * 2.3, shrink=0.12)]
        f['mouths'] = (mm, mirror_pt(sm), sm)
        out.append(f)

    # 13 SPENT: heads hanging, eyes heavy, tongues out, the fire guttering in the throats and smoke curling
    # up out of the corners of the maws, wings sagging
    f = hang(3, wings=WING_DROOP, fore_dy=5)
    f['mid'].update(mouth='yelp', eyes='tired', low_dy=3)
    f['side'].update(mouth='roar', eyes='tired', low_dy=2)
    f['hind'] = hind(3, hock=(149, 60), hip=(129, 80))
    mm, sm = mid_mouth(f['mid']), side_mouth(f['side'])
    lm = mirror_pt(sm)
    f['fx'] = [fx.throat(mm[0], mm[1], 7.0, keys='kq', dim=True),
               fx.throat(sm[0], sm[1], 4.0, keys='kq', dim=True), fx.throat(lm[0], lm[1], 4.0, keys='kq', dim=True),
               # sweat flicked off the heads, as the redesign's recover draws exhaustion
               rigfx(FX.sweat(72, 47, -1)), rigfx(FX.sweat(117, 45)), rigfx(FX.sweat(26, 74, -1)),
               rigfx(FX.sweat(164, 72))]
    f['mouths'] = (mm, lm, sm)
    out.append(f)

    # 14 RELEASE: the talons thrown open, the body swinging up toward upright, wings flaring
    f = hang(0, mid_dy=18, side_dy=15, wings=RW.moved(RW.FLARE, 0, 1), grip='open', fore_dy=2)
    f['torso'] = (0, 5)
    f['neck'] = neck(5, 15)
    f['hind'] = dict(paw=(148, 31), ankle=(150, 41), hock=(157, 58), hip=(137, 80), splay=1.0)
    # the tail and Liam's headband tails swing back into view as he lets go (land frame 0 has them)
    f['hide_band_tails'] = False
    f['band_wave'] = 1
    f['tail_path'] = [(66, 118), (50, 124), (34, 122), (22, 114), (14, 104), (12, 94)]
    f['tail_tip'] = (13, 96)
    out.append(f)

    for f in out:
        if 'mouths' not in f:
            if f['mid'].get('draw'):
                raise ValueError('a drawn head needs its mouths given')
            mm, sm = mid_mouth(f['mid']), side_mouth(f['side'], f.get('side_out', False))
            f['mouths'] = (mm, mirror_pt(sm), sm)
    return out


def release_upright():
    """15: upright, as land frame 0 (the redesign rig's land pose) at the hover's height, so it stays inside
    the 33-row headroom (land frame 0 itself rides 2 rows higher)."""
    import rig_poses
    P = copy.deepcopy(rig_poses.land()[0])
    P['bob'] = 0
    return P


# the approved hover's throats, which land frame 0 keeps
RELEASE_MOUTHS = ((96, 65), (40, 88), (151, 88))
