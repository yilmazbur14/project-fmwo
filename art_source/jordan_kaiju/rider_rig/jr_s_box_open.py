"""jordan_box_open: 6 frames, once (0.10). The intro: standing at his spot with the chase-edition box, he
cracks it open and pulls out the toy kaiju, and holds it up.

  0  his live idle frame 0, pixel for pixel (the intro starts on jordan_idle)
  1  the near hand reaches up across his collar to the box's window panel, eyes on it
  2  the panel flipped open on its hinge: the toy sits in the tray (drawn in his greys, see below),
     a glint pops off it; his hand back on his hip, a pleased grin
  3  the near hand dips into the tray
  4  he lifts the toy out on his palm past his face (the tray now the empty hollow of the approved
     rider's box). The TOY is the code's kaiju_toy sprite: this frame leaves a clean palm and gives
     TOY = where its FEET pivot goes
  5  holds it up high on the fist-pump arm, shouting (TOY anchor); the open box still up in the far hand

NEW / invented: the toy-in-the-tray (f2-f3) is the open box's kaiju-shaped hollow filled with his
charcoal/grey/ivory keys (2, 3, 9: the nearest to the kaiju's charcoal-teal hide and ivory plates in his
40 colours); the PALM_UP hand; the window panel taking the plumber print with it as it opens.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_mat as M     # noqa: E402
import jr_sheet as S   # noqa: E402
import janim_idle as JI  # noqa: E402

NAME = 'jordan_box_open'
TIMES = [0.10] * 6
LOOP = False
KIND = 'mat'
OFFSET = (-1, 0)
NOTE = ('Standing (SOLES row 95 at his intro spot). f0 == live jordan_idle f0. TOY (f4, f5) = where kaiju_toy '
        'FEET (its pivot (12, 27)) goes; its tray hollow is ~9x10 texels, so the toy reads best at ~0.4-0.5 scale.')
V, JB, J = F.V, F.JB, F.J


def toy_in_tray(box):
    """The open box with its kaiju-shaped hollow filled: the toy sitting in the tray, keylined against
    the tray's blue plastic, lit along its back, one gold eye."""
    out = dict(box)
    y0 = min(y for (x, y) in box)
    hollow = {q for q, k in box.items() if k == 'n' and 9 <= q[1] - y0 <= 16}
    for (x, y) in hollow:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in hollow and out.get(q) in ('D', 'B'):
                out[q] = 'k'
    for (x, y) in hollow:
        lit = (x - 1, y) not in hollow or (x, y - 1) not in hollow
        out[(x, y)] = '9' if lit else '3'
    top = min(y for (x, y) in hollow)
    ex = max(x for (x, y) in hollow if y == top + 1)
    out[(ex, top + 1)] = 'O'                               # the chase edition's amber eye
    return out


def standing(fig, near, head, box, far_hand=True, shirt=1, far=None):
    fig.stamp(V.legs())
    for s in V.shoes():
        fig.stamp(s, outline=False)
    fig.stamp_all(far if far is not None else V.far_arm_box())
    fig.stamp(V.neck(F.HEAD_AT[0]))
    fig.stamp(V.shirt(shirt))
    JB.dandruff(fig.px)
    fig.stamp(head, outline=False, name='head')
    fig.stamp_all(near)
    fig.stamp(box, outline=False, name='box')
    if far_hand:
        fig.stamp(F.far_hand_box(0, 0), outline=False)


def reach_up(wrist, hand_rows, hand_at, twist=(3, -2)):
    sh = (F.NEAR_ROOT[0] + twist[0], F.NEAR_ROOT[1] + twist[1])
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, 1)
    return F.near_arm(sh, el, wrist) + [(F.map_at(hand_rows, *hand_at), False)]


def raised_palm():
    """v2's fist-pump arm (jv2_body.raised_arm: its limb, its fitted cuff, the wristband) with an open
    palm turned up in place of the fist."""
    arm = V.limb([((40.8, 47.5), (35.4, 34.6), 1.6, 1.5), ((35.4, 34.6), (31.4, 22.5), 1.5, 1.3)],
                 knobs=((35.4, 34.8, 1.9),))
    sl = V.raised_sleeve(arm)
    through = {q: k for q, k in arm.items() if q[1] in (41, 42)}
    band = F.map_at(F.BAND, 28, 22)
    palm = F.map_at(F.PALM_UP, 27, 16)
    return [(arm, True), (sl, True), (through, False), (band, False), (palm, False)]


def f0():
    cv, fx = JI.build(dip=0, box_deg=0, head='idle')
    fig = F.Fig()
    fig.cv.px.update(cv.px)
    fig.pts['head'] = F.head('idle', dx=F.HEAD_AT[0], dy=F.HEAD_AT[1])
    return fig, {}, 'his idle f0'


def f1():
    fig = F.Fig()
    near = reach_up((62.5, 41.0), F.REACH, (62, 38))
    standing(fig, near, F.head('admire', dx=F.HEAD_AT[0] + 1, dy=F.HEAD_AT[1], tilt=4), J.box_part(2, 2))
    return fig, {}, 'reaching for the panel'


def f2():
    fig = F.Fig()
    standing(fig, V.near_arm_hip(), F.head('grin', dx=F.HEAD_AT[0], dy=F.HEAD_AT[1]), toy_in_tray(F.open_box(0, 0)),
             shirt=0)
    fig.fxput(M.sparkle(84, 31), under=True)
    fig.fxput(M.sparkle(73, 24, big=False), under=True)
    return fig, {}, 'panel open, the toy in the tray'


def f3():
    fig = F.Fig()
    near = reach_up((64.5, 41.5), F.REACH, (64, 38))
    standing(fig, near, F.head('admire', dx=F.HEAD_AT[0] + 1, dy=F.HEAD_AT[1] + 1, tilt=5), toy_in_tray(F.open_box(0, 0)))
    return fig, {}, 'hand into the tray'


def f4():
    fig = F.Fig()
    sh = F.NEAR_ROOT
    wrist = (37.0, 35.5)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, -1)
    near = F.near_arm(sh, el, wrist) + [(F.map_at(F.BAND, 34, 35), False), (F.map_at(F.PALM_UP, 33, 29), False)]
    standing(fig, near, F.head('grin', dx=F.HEAD_AT[0] - 1, dy=F.HEAD_AT[1], tilt=-3), F.open_box(0, 0))
    return fig, {'TOY': (37, 29)}, 'the toy lifted out on his palm'


def f5():
    fig = F.Fig()
    standing(fig, raised_palm(), F.head('shout', dx=JB.V2F.HEAD_AT[1][0], dy=JB.V2F.HEAD_AT[1][1]),
             F.open_box(0, 0))
    return fig, {'TOY': (31, 16)}, 'holding the toy up high'


def frames():
    out = []
    for i, b in enumerate((f0, f1, f2, f3, f4, f5)):
        fig, a, note = b()
        a = dict(a)
        a['SOLES'] = (49, 95)
        a['CROWN'] = S.crown(fig.px, fig.pts['head'])
        fr = S.to_frame(fig, OFFSET, a, on_mat=True, note=note)
        if i:
            S.fill_holes(fr.px)
        out.append(fr)
    return out


def check_f0():
    fr = frames()[0]
    return C.pixel_diff(C.render(fr.px), C.live_sheet('jordan_idle').crop((0, 0, 96, 96)))


if __name__ == '__main__':
    print('f0 vs live jordan_idle f0:', check_f0() or 'IDENTICAL')
