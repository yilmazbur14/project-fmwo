"""jordan_ride_throw: 4 frames, once (0.20, 0.20, 0.10, 0.15). From the kaiju's head he digs a figure
out of the open box and hurls it down into the ring. HAND (the release texel) on f2.

  0  reach: he leans in and stretches the near arm up across his collar, the hand dipping into the
     open box's tray where it is held up beside his face; eyes on it
  1  wind-up: he rocks back, the near arm cocked behind his head, fist closed on the figure (a pink
     summon glint flickering round it: the figure in his fist is the code's sprite, not drawn), teeth
     gritted
  2  release: he lunges forward, the stick arm whipped out ahead of him under the box (which the far
     arm jerks up a few pixels for balance), the hand flung open, a speed streak along the swing,
     yelling. HAND = the open palm: the code's funko leaves from here
  3  settle: the arm dropping back toward his hip, a pleased grin, on the way back to the idle
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_rider as RR  # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_ride_idle as RI  # noqa: E402

NAME = 'jordan_ride_throw'
TIMES = [0.20, 0.20, 0.10, 0.15]
LOOP = False
KIND = 'ride'
OFFSET = RI.OFFSET
NOTE = 'HAND on f2 is where the thrown figure appears (the open palm). SEAT as jordan_ride_idle.'
V = F.V


def sparkles(pts):
    out = {}
    for (cx, cy, big) in pts:
        out[(cx, cy)] = 'W'
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out[(cx + dx, cy + dy)] = 'Q'
    return out


def streak(pts, key='W'):
    out = {}
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in C.line(x0, y0, x1, y1):
            out[q] = key
    return out


LAP = (-17, 32)                  # the open box set down in his lap (offset from its approved spot)


def far_box_arm(up, bdx, bdy):
    """v2's far arm re-posed to hold the box moved by (bdx, bdy) by its base: the wrist under v2's far hand."""
    fsh = (F.FAR_ROOT[0] + up[0], F.FAR_ROOT[1] + up[1])
    fwr = (64.4 + bdx, 49.8 + bdy)
    fel = F.ik(fsh, fwr, 9.52, 6.99, -1)
    return F.far_arm(fsh, fel, fwr)


def lap_box(up, bdx=LAP[0], bdy=LAP[1]):
    """The box in his lap, the far hand hooked over its top edge on the right (v2's LOW_HAND)."""
    box = F.open_box(bdx, bdy)
    top = 27 + bdy
    hx, hy = 58 + bdx + 17, top - 2
    fsh = (F.FAR_ROOT[0] + up[0], F.FAR_ROOT[1] + up[1])
    fwr = (hx + 3.4, hy + 0.5)
    fel = F.ik(fsh, fwr, 9.52, 6.99, -1)
    far = F.far_arm(fsh, fel, fwr)
    hand = F.amap(F.V.LOW_HAND, hx, hy)
    return far, box, hand


def f0():
    up = (2, 0)
    sh = (F.NEAR_ROOT[0] + up[0] + 3, F.NEAR_ROOT[1] + up[1] - 2)   # the shoulder raised and twisted in
    wrist = (63.5, 41.0)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, 1)
    near = F.near_arm(sh, el, wrist) + [(F.map_at(F.REACH, 63, 38), False)]
    head = F.head('admire', dx=F.HEAD_AT[0] + up[0] - 1, dy=F.HEAD_AT[1] + up[1] + 1, tilt=4)
    fig = RR.rider(up=up, head=head, far=F.far_arm_box(0, 0), near=near, box=F.open_box(0, 0),
                   far_hand=F.far_hand_box(0, 0), near_over_box=True, shin=(0, 0))
    return fig, {}, 'reach up into the box'


def f1():
    up = (-2, 0)
    sh = (F.NEAR_ROOT[0] + up[0], F.NEAR_ROOT[1] + up[1])
    wrist = (30.5, 33.5)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, -1)
    fist = F.map_at(F.FIST_UP_FULL, 26, 24)
    band = F.map_at(F.BAND, 27, 32)
    near = F.near_arm(sh, el, wrist) + [(band, False), (fist, False)]
    head = F.head('grit', dx=F.HEAD_AT[0] + up[0], dy=F.HEAD_AT[1] + up[1], tilt=-5)
    fig = RR.rider(up=up, head=head, far=F.far_arm_box(*up), near=near, box=F.open_box(*up),
                   far_hand=F.far_hand_box(*up), shin=(-1, 0))
    fig.fxput(sparkles([(24, 23, True), (35, 22, False), (23, 30, False), (36, 27, True)]), under=True)
    return fig, {}, 'wind-up, fist cocked behind his head'


def f2():
    up = (3, 2)
    sh = (F.NEAR_ROOT[0] + up[0] + 3, F.NEAR_ROOT[1] + up[1])     # the near shoulder twisted forward
    wrist = (66.5, 54.0)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, 1)
    hand = F.map_at(F.PALM_FWD, 66, 50)
    band = F.map_at(['kkkk', 'kQPk', 'kPqk', 'kkkk'], 62, 52)
    near = F.near_arm(sh, el, wrist) + [(band, False), (hand, False)]
    head = F.head('shout', dx=F.HEAD_AT[0] + up[0], dy=F.HEAD_AT[1] + up[1], tilt=6)
    bdx, bdy = 3, -6                    # the far arm jerks the box up for balance
    fig = RR.rider(up=up, head=head, far=far_box_arm(up, bdx, bdy), near=near, box=F.open_box(bdx, bdy),
                   far_hand=F.far_hand_box(bdx, bdy), shin=(1, 0))
    fig.fxput(streak([(32, 33), (37, 41), (44, 47), (52, 50)], 'W') | streak([(30, 38), (35, 45), (41, 50)], 'Q'),
              under=True)
    return fig, {'HAND': (71, 53)}, 'release: HAND = the open palm'


def f3():
    up = (1, 1)
    sh = (F.NEAR_ROOT[0] + up[0], F.NEAR_ROOT[1] + up[1])
    wrist = (39.0, 62.5)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, -1)
    hand = F.map_at(F.HAND_HANG, 37, 62)
    near = F.near_arm(sh, el, wrist) + [(hand, False)]
    head = F.head('grin', dx=F.HEAD_AT[0] + up[0], dy=F.HEAD_AT[1] + up[1])
    fig = RR.rider(up=up, head=head, far=F.far_arm_box(*up), near=near, box=F.open_box(*up),
                   far_hand=F.far_hand_box(*up), shin=(0, 0))
    return fig, {}, 'settling back, grinning'


def frames():
    out = []
    for b in (f0, f1, f2, f3):
        fig, extra, note = b()
        fr = RI.to_frame(fig, extra, note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
