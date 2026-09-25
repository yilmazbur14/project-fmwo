"""Bixby's juggle: the twelve frames, in Mason's order.

  0-1   HIT     0 the uppercut lands under his chest: the three heads snap back yelping, eyes squeezed
                shut, wings flung up, paws leaving the mat. 1 popped up and tipping over, heads still
                thrown back, legs dangling, streaks under him.
  2-6   TUMBLE  2 the hang: the body keeps tipping but all three heads snap round to stare at the camera,
                eyes blown wide (the take). 3-6 one full clockwise turn, a quarter a frame, wings flapping
                every which way, legs kicking, every mouth yelping.
  7-9   CRASH   flat on his back: 7 the thud, squashed into the mat with dust blasted out along it;
                8 the bounce, everything flung; 9 the settle, heads flopping over.
  10-11 DOWN    KO'd belly-up: legs in the air, wings spread flat on the mat, the three heads lolled
                over with swirl eyes and tongues out; 11 is 10 with the chest risen on a breath.

Every body is the approved rig's (jrig: rig.build's stamp order, relit for its turn) placed into the
256x256 juggle frame by jcompose: exact quarter turns for the spin and the lying frames, RotSprite for
the tipping body of 1-2 (whose heads stay upright and exact).
"""
import numpy as np

import jcommon as C
import jcompose as JC
import jfx
import rig_faces2 as F2
import rig_stance as ST
import rig_wings as RW
from rig import HOVER_UP, pose

TC = C.TUMBLE_CENTRE
FX_ = C.FEET[0]
GY = C.FEET[1]


def P_base(**kw):
    P = pose(HOVER_UP)
    P['mid'] = {}
    P['side'] = {}
    for k, v in kw.items():
        P[k] = v
    return P


def legs(P, fr=None, fl=None, hr=None, hl=None, sh=(119, 100), hip=(136, 110), bend=(1, 1, 1, 1), dy=0):
    """Hanging legs by paw centre (right-side coordinates; the left ones are given in right-side space and
    mirrored by the rig). dy moves the whole leg (shoulder, hip and paw) with a breathing torso."""
    sh = (sh[0], sh[1] + dy)
    hip = (hip[0], hip[1] + dy)
    if fr:
        P['front'] = ST.front_joints(sh, (fr[0], fr[1] + dy), bend=bend[0], planted=False)
    if fl:
        P['front_left'] = ST.front_joints(sh, (fl[0], fl[1] + dy), bend=bend[1], planted=False)
    if hr:
        P['hind'] = ST.hind_joints(hip, (hr[0], hr[1] + dy), bend=bend[2])
    if hl:
        P['hind_left'] = ST.hind_joints(hip, (hl[0], hl[1] + dy), bend=bend[3])
    return P


def fit(layers, bottom=None, left=None):
    """Shift every layer so the figure's lowest texel is on row `bottom` (and/or its centre on x `left`)."""
    a = JC.compose(layers)
    ys = np.nonzero(a.any(axis=1))[0]
    sy = 0 if bottom is None else bottom - int(ys.max())
    for L in layers:
        L.dest = (L.dest[0], L.dest[1] + sy)
    return layers


LAST_FIGURE = None          # the last frame's figure alone, before its effects (for the lint)
LAST_BODY = None            # ... and its body layer alone, which is what relight.py lights


def finish(layers, back=(), front=()):
    """Compose: effects behind him (only on empty texels), him, effects over him."""
    global LAST_FIGURE, LAST_BODY
    fr = JC.compose(layers)
    LAST_FIGURE = fr.copy()
    LAST_BODY = JC.compose([L for L in layers if L.name in ('wings', 'body')])
    if back:
        fr = jfx.over_where_empty(fr, jfx.to_arr(back))
    if front:
        fr = jfx.over(fr, jfx.to_arr(front))
    return fr


UPRIGHT = {'mid': 0, 'left': 0, 'right': 0}

# ------------------------------------------------------------------------------------------ HIT ---


def hit_contact():
    P = P_base(wings=RW.FLARE, tails_wave=1,
               mid=dict(dy=-9, eyes='shut', mouth='yelp', low_dy=5),
               side=dict(dx=4, dy=-10, eyes='shut', mouth='roar', low_dy=3),
               neck=((118, 98), (146, 72)),
               tail_path=[(66, 126), (50, 134), (36, 132), (26, 122), (22, 108), (24, 96)],
               tail_tip=(24, 98))
    legs(P, fr=(125, 146), fl=(121, 146), hr=(155, 147), hl=(152, 147))
    d = JC.ground_dest(0, -5)
    lay = JC.figure(P, 0, dest=d)
    bx, by = JC.place(0, C.LOCAL_PIVOT, d, (96, 136))
    bx, by = int(bx), int(by) + 3
    front = [jfx.impact(bx, by, r=18, rays=14, ray_len=(24, 40)),
             jfx.sweat(40, 34, -1), jfx.sweat(212, 30), jfx.sweat(150, 14), jfx.sweat(96, 20, -1)]
    back = [jfx.burst_lines(bx, by, n=10, r0=44, r1=62, phase=0.15),
            jfx.dust(FX_ - 44, 3, -1), jfx.dust(FX_ + 44, 3, 1),
            jfx.dust(FX_ - 74, 2, -1), jfx.dust(FX_ + 74, 2, 1),
            jfx.dust(FX_ - 98, 1, -1), jfx.dust(FX_ + 98, 1, 1),
            jfx.pebbles([(FX_ - 20, GY - 8, 2), (FX_ + 22, GY - 11, 1), (FX_ - 90, GY - 16, 1),
                         (FX_ + 88, GY - 19, 2), (FX_ - 60, GY - 26, 1), (FX_ + 58, GY - 30, 1)])]
    return finish(lay, back, front)


def hit_lift():
    P = P_base(wings=RW.UP, tails_wave=0,
               mid=dict(dy=-10, eyes='shut', mouth='yelp', low_dy=5),
               side=dict(dx=5, dy=-12, eyes='shut', mouth='roar', low_dy=3),
               neck=((118, 98), (147, 70)),
               tail_path=[(66, 128), (50, 142), (34, 150), (20, 150), (12, 142), (10, 132)],
               tail_tip=(12, 134))
    legs(P, fr=(127, 152), fl=(123, 152), hr=(158, 153), hl=(154, 153))
    lay = JC.figure(P, 20, loll=UPRIGHT)
    back = [jfx.streaks([(88, 210, 238), (104, 216, 250), (122, 212, 244), (140, 218, 250), (158, 208, 236),
                         (74, 204, 226), (172, 200, 224)])]
    front = [jfx.sweat(46, 40, -1), jfx.sweat(206, 30), jfx.sweat(100, 22)]
    return finish(lay, back, front)


# --------------------------------------------------------------------------------------- TUMBLE ---


def hang():
    P = P_base(wings=RW.moved(RW.DOWN, dy=-2), wings_left=RW.MID, tails_wave=1,
               mid=dict(eyes='wide', mouth='yelp', low_dy=5),
               side=dict(eyes='wide', mouth='roar', low_dy=3, dx=2, dy=-2),
               neck=((118, 98), (144, 80)),
               tail_path=[(66, 128), (54, 142), (46, 156), (44, 168), (48, 178), (56, 184)],
               tail_tip=(56, 184))
    legs(P, fr=(146, 128), fl=(96, 130), hr=(165, 138), hl=(112, 142), bend=(1, -1, 1, -1))
    lay = JC.figure(P, 45, loll=UPRIGHT)
    front = [jfx.sweat(58, 36, -1), jfx.sweat(196, 44), jfx.sweat(112, 32)]
    return finish(lay, (), front)


# theta, right wing, left wing, legs (front r, front l, hind r, hind l), mid, side, side_left, tail
SPIN = [
    (90, RW.FLARE, RW.DOWN, ((140, 128), (116, 148), (166, 134), (150, 150)),
     dict(eyes='shut', mouth='yelp', low_dy=5), dict(eyes='wide', mouth='roar', low_dy=3, dx=3, dy=2),
     dict(eyes='shut', mouth='roar', low_dy=3, dx=1, dy=-5),
     [(66, 126), (48, 136), (30, 134), (18, 124), (14, 110), (18, 98)]),
    (180, RW.DOWN, RW.FLARE, ((118, 150), (138, 130), (150, 150), (168, 132)),
     dict(eyes='wide', mouth='yelp', low_dy=5), dict(eyes='shut', mouth='roar', low_dy=3, dx=1, dy=-4),
     dict(eyes='wide', mouth='roar', low_dy=3, dx=3, dy=2),
     [(66, 128), (50, 144), (34, 152), (20, 150), (12, 140), (10, 128)]),
    (270, RW.UP, RW.MID, ((136, 146), (124, 134), (162, 146), (158, 134)),
     dict(eyes='shut', mouth='yelp', low_dy=5), dict(eyes='shut', mouth='roar', low_dy=3, dx=2, dy=1),
     dict(eyes='wide', mouth='roar', low_dy=3, dx=2, dy=-3),
     [(66, 126), (46, 128), (28, 122), (16, 110), (14, 96), (20, 86)]),
    (360, RW.MID_UP, RW.UP, ((124, 136), (134, 148), (160, 136), (164, 150)),
     dict(eyes='wide', mouth='yelp', low_dy=5), dict(eyes='wide', mouth='roar', low_dy=3, dx=2, dy=-3),
     dict(eyes='shut', mouth='roar', low_dy=3, dx=2, dy=1),
     [(66, 128), (52, 146), (40, 158), (28, 162), (18, 158), (12, 150)]),
]


def spin(i):
    th, wr, wl, (fr, fl, hr, hl), mid, side, side_l, tail = SPIN[i]
    P = P_base(wings=wr, wings_left=wl, tails_wave=i % 2, mid=dict(mid), side=dict(side),
               side_left=dict(side_l), tail_path=tail, tail_tip=tail[-1],
               neck=((118, 98), (142 + side['dx'], 82 + side['dy'])),
               neck_left=((118, 98), (142 + side_l['dx'], 82 + side_l['dy'])))
    legs(P, fr=fr, fl=fl, hr=hr, hl=hl)
    lay = JC.figure(P, th)
    a0 = th - 90
    back = [jfx.arc(TC[0], TC[1], 116, 110, a0 - 158, a0 - 104),
            jfx.arc(TC[0], TC[1], 112, 106, a0 + 22, a0 + 76),
            jfx.arc(TC[0], TC[1], 100, 96, a0 - 60, a0 - 30)]
    return finish(lay, back)


# ---------------------------------------------------------------------------------------- CRASH ---

LIE = 180


def belly_up(eyes='dizzy', mouths=('yelp', 'roar'), tongue=True, breath=0, side=(6, -16), side_l=(2, -10),
             wings=RW.MID, wings_left=None, leg_paws=None, tail=None):
    mm, ms = mouths
    P = P_base(wings=wings, wings_left=wings_left, tails_wave=1,
               mid=dict(eyes=eyes, mouth=mm, low_dy=5 if mm != 'snarl' else 0),
               side=dict(eyes=eyes, mouth=ms, low_dy=3 if ms == 'roar' else 0, dx=side[0], dy=side[1]),
               torso=(0, breath),
               neck=((118, 98 + breath), (142 + side[0], 82 + side[1])),
               tail_path=tail or [(66, 126), (52, 138), (40, 150), (36, 164), (40, 176), (48, 184)],
               tail_tip=(tail or [(48, 184)])[-1])
    P['side_left'] = dict(P['side'], dx=side_l[0], dy=side_l[1])
    P['neck_left'] = ((118, 98 + breath), (142 + side_l[0], 82 + side_l[1]))
    if tongue:
        P['mid']['tongue'] = F2.mid_tongue_long
        P['side']['tongue'] = F2.side_tongue_long(ms == 'roar')
        P['side_left']['tongue'] = F2.side_tongue_long(ms == 'roar')
    lp = leg_paws or dict(fr=(140, 142), fl=(132, 146), hr=(168, 140), hl=(160, 146))
    legs(P, dy=breath, **lp)
    return P


def crash_impact():
    """The thud: slammed flat on his back, squashed into the mat, every eye bulging (squeezed-shut eyes
    vanish on an upside-down head at this scale), legs and wings flung wide. Dust blasts out along the mat both ways in a wave, more is thrown up, light fans where
    his heads hit, the mat cracks, grit flies, and fall streaks hang above him."""
    P = belly_up('wide', tongue=False, side=(10, -12), side_l=(8, -8), wings=RW.moved(RW.MID, dy=-4),
                 leg_paws=dict(fr=(152, 132), fl=(148, 136), hr=(178, 128), hl=(174, 136)),
                 tail=[(66, 126), (50, 130), (34, 128), (20, 122), (10, 114), (4, 106)])
    lay = fit(JC.figure(P, LIE, dest=(FX_, 100), post=(1.12, 0.8)), bottom=GY)
    top = int(JC.np_top(JC.compose(lay)))
    wave = []
    for dx, size, lift in ((58, 3, 0), (80, 3, 0), (102, 3, 0), (117, 2, 0),
                           (48, 2, 9), (70, 2, 10), (92, 2, 8), (110, 1, 6),
                           (86, 2, 24), (64, 1, 34), (106, 1, 30)):
        for sgn in (-1, 1):
            wave.append(jfx.dust_at(FX_ + sgn * dx, GY - lift, size, sgn))
    front = wave + [
        jfx.flash(FX_ - 52, w=22, h=14), jfx.flash(FX_ + 52, w=22, h=14), jfx.flash(FX_, w=30, h=10),
        jfx.star(FX_ - 30, GY - 44, 4), jfx.star(FX_ + 34, GY - 40, 4), jfx.star(FX_ + 2, GY - 70, 3),
        jfx.pebbles([(30, GY - 44, 2), (224, GY - 40, 2), (54, GY - 62, 1), (200, GY - 66, 1),
                     (14, GY - 22, 1), (240, GY - 18, 1), (40, GY - 80, 2), (214, GY - 84, 2)])]
    back = [jfx.cracks(FX_ - 36, 26), jfx.cracks(FX_ + 36, 26),
            jfx.streaks([(x, top - L - 6, top - 6) for x, L in ((80, 22), (100, 30), (128, 16),
                                                                  (156, 28), (176, 20))])]
    return finish(lay, back, front)


def crash_bounce():
    """The bounce: everything flung up off the mat, heads flopping, the dust wave rolling on and rising,
    grit in the air."""
    P = belly_up('dizzy', tongue=True, side=(10, -20), side_l=(8, -16), wings=RW.moved(RW.MID, dy=-10),
                 leg_paws=dict(fr=(146, 152), fl=(128, 154), hr=(174, 150), hl=(156, 156)),
                 tail=[(66, 126), (52, 134), (40, 142), (26, 146), (14, 144), (6, 138)])
    lay = fit(JC.figure(P, LIE, dest=(FX_, 100), post=(0.96, 1.05),
                        loll={'left': 160, 'right': 205, 'mid': 180}), bottom=GY - 14)
    front = []
    for dx, size, lift in ((94, 3, 6), (111, 2, 2), (76, 2, 22), (102, 2, 30), (58, 1, 40), (116, 1, 18)):
        for sgn in (-1, 1):
            front.append(jfx.dust_at(FX_ + sgn * dx, GY - lift, size, sgn))
    front.append(jfx.pebbles([(36, GY - 96, 2), (218, GY - 100, 2), (62, GY - 114, 1), (192, GY - 118, 1),
                              (20, GY - 60, 1), (236, GY - 56, 1)]))
    return finish(lay, (), front)


def crash_settle():
    """Back on the mat, the heads flopping over; the dust thins out at the edges and the grit lands."""
    P = belly_up('dizzy', tongue=True, side=(10, -18), side_l=(8, -14), wings=RW.moved(RW.MID, dy=-6),
                 tail=KO_TAIL)
    lay = fit(JC.figure(P, LIE, dest=(FX_, 100), post=(1.04, 0.94),
                        loll={'left': 150, 'right': 215, 'mid': 180}), bottom=GY)
    front = [jfx.dust_at(FX_ - 116, GY, 2, -1), jfx.dust_at(FX_ + 116, GY, 2, 1),
             jfx.dust_at(FX_ - 104, GY - 16, 1, -1), jfx.dust_at(FX_ + 106, GY - 18, 1, 1),
             jfx.pebbles([(40, GY - 2, 2), (214, GY - 3, 2), (26, GY - 1, 1), (230, GY - 2, 1),
                          (60, GY - 30, 1), (196, GY - 34, 1)])]
    return finish(lay, (), front)


# ----------------------------------------------------------------------------------------- DOWN ---

KO_LOLL = {'left': 145, 'right': 220, 'mid': 180}
# the tail flopped out along the mat beside him (drawn turned: this runs off to his right on screen)
KO_TAIL = [(66, 126), (52, 130), (38, 128), (24, 122), (12, 114), (4, 104)]


KO_LEGS = dict(fr=(140, 142), fl=(132, 146), hr=(168, 140), hl=(160, 146))


def down(breath=0, twitch=False):
    """KO'd belly-up. The in-breath lifts his chest and legs 2 texels, and one hind leg twitches."""
    lp = dict(KO_LEGS)
    if twitch:
        lp['hl'] = (150, 140)          # the leg jerks in at the knee
    P = belly_up('dizzy', tongue=True, breath=breath, side=(10, -18), side_l=(8, -14),
                 wings=RW.moved(RW.MID, dy=-6), tail=KO_TAIL, leg_paws=lp)
    lay = fit(JC.figure(P, LIE, dest=(FX_, 100), loll=KO_LOLL), bottom=GY)
    return finish(lay)


FRAMES = [
    ('hit_contact', hit_contact, 0.06),
    ('hit_lift', hit_lift, 0.08),
    ('hang', hang, 0.14),
    ('spin_a', lambda: spin(0), 0.08),
    ('spin_b', lambda: spin(1), 0.08),
    ('spin_c', lambda: spin(2), 0.08),
    ('spin_d', lambda: spin(3), 0.08),
    ('crash_impact', crash_impact, 0.07),
    ('crash_bounce', crash_bounce, 0.09),
    ('crash_settle', crash_settle, 0.14),
    ('down', lambda: down(0), 0.4),
    ('down_breathe', lambda: down(2, twitch=True), 0.4),
]
