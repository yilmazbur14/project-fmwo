"""jordan_butt_land: 6 frames, once (0.06, 0.08, 0.10, 0.12, 0.14, hold). Killed while mounted: the kaiju
shrinks out from under him and he is bucked off, lands on his butt, and ends exactly where his defeat
ends, so the walk-out's getup matches.

  0  bucked: thrown up off the seat, limbs everywhere, the box flung out of his hand, the quiff knocked
     flat, a pained yelp
  1  dropping butt-first, legs up, arms up, the box tumbling away
  2  THUMP on his butt: dust, eyes screwed shut, the box coming down upside down beside him
  3  jordan_defeat f3, pixel for pixel: the bump bounces him up onto his knees, head dropping, the box
     landed on its side
  4  jordan_defeat f4, pixel for pixel (sunk back on his heels, reaching for the box)
  5  jordan_defeat f5, pixel for pixel (held; the walk-out's getup starts from here)

The box: his OPEN rider box while it flies (f0-f2); from f3 it is the defeat's box on its side (closed,
the plumber in its window), because f3-f5 are the defeat's own frames.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_mat as M     # noqa: E402
import jr_rot as ROT   # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_daze as D  # noqa: E402
import jr_s_topple as T  # noqa: E402
import janim_defeat as JD  # noqa: E402

NAME = 'jordan_butt_land'
TIMES = [0.06, 0.08, 0.10, 0.12, 0.14, 1.0]
LOOP = False
HOLD_FRAME = 5
KIND = 'mat'
OFFSET = (-1, 0)
NOTE = ('Ends pixel-identical to jordan_defeat f5 (f3, f4 == defeat f3, f4). PIVOT (hips) on f0-f1 for the arc from the '
        'seat; SOLES on f2-f5 = the defeat landing spot. Hold f5 (times[5] is nominal).')
V, JB = F.V, F.JB


def flying_box(deg, at):
    """The open box tumbling free: turned with the juggle's RotSprite turner."""
    box = F.open_box(0, 0)
    c = (72, 37)
    return ROT.turn(box, deg, c, at)


def f0():
    fig = T.flail_fig('pain', 'flopped', near_wr=(32.0, 33.0), near_hand=(F.HAND_OPEN_BACK, (26, 27)),
                      far_wr=(70.0, 40.0), box_d=None,
                      near_leg=((47.0, 68.0), (57.5, 64.0), (65.0, 70.0)),
                      far_leg=((52.0, 67.5), (61.5, 62.0), (70.0, 64.0)), near_bend=-1)
    out = T.turned(fig, -14, (50, 66))
    out.stamp(flying_box(35, (78, 18)), outline=False, name='box')
    return out, {'PIVOT': (50, 66)}, 'bucked off, the box flung away'


def f1():
    fig = T.flail_fig('yelp', 'flopped', near_wr=(30.0, 38.0), near_hand=(F.HAND_OPEN_BACK, (24, 33)),
                      far_wr=(68.0, 35.0), box_d=None,
                      near_leg=((47.0, 68.0), (58.5, 64.0), (68.5, 61.5)),
                      far_leg=((52.0, 67.5), (62.5, 61.5), (71.5, 58.5)), near_bend=-1)
    out = T.turned(fig, -16, (50, 70))
    out.stamp(flying_box(110, (83, 25)), outline=False, name='box')
    return out, {'PIVOT': (50, 70)}, 'dropping butt-first, the box tumbling'


def f2():
    fig = F.Fig()
    head = F.head('pain', dx=F.HEAD_AT[0] + D.UP[0] - 2, dy=F.HEAD_AT[1] + D.UP[1] + 1, tilt=-6)
    D.sit_body(fig, head=head, box=False)
    fig.stamp(flying_box(170, (81, 70)), outline=False, name='box')
    for (x, y, r) in ((23, 94, 2), (30, 92, 1), (36, 94, 1)):
        fig.fxput(M.dust(x, y, r), under=True)
    return fig, {'SOLES': (49, 95)}, 'THUMP: on his butt, the box coming down'


def f3():
    return defeat_frame(3), {'SOLES': (49, 95)}, 'jordan_defeat f3: bounced up onto his knees'


def defeat_frame(i):
    """jordan_defeat frame i, pixel for pixel (from the rig copy; checked against the live sheet)."""
    px, fx, info = JD.frames_info()[i]
    fig = F.Fig()
    fig.cv.px.update({(x + 1, y): k for (x, y), k in px.items()})      # back to build coordinates
    fig.fx = {(x + 1, y) for (x, y) in fx}
    fig.pts['head'] = {(x + 1, y): k for (x, y), k in info['head'].items()}
    fig.pts['box'] = {(x + 1, y): k for (x, y), k in info['box'].items()}
    return fig


def f4():
    return defeat_frame(4), {'SOLES': (49, 95)}, 'jordan_defeat f4'


def f5():
    return defeat_frame(5), {'SOLES': (49, 95)}, 'jordan_defeat f5 (held)'


def frames():
    out = []
    for i, b in enumerate((f0, f1, f2, f3, f4, f5)):
        fig, a, note = b()
        a = dict(a)
        a['CROWN'] = S.crown(fig.px, fig.pts['head'])
        fr = S.to_frame(fig, OFFSET, a, on_mat=(i >= 2), note=note)
        if i < 3:
            S.fill_holes(fr.px)
        out.append(fr)
    return out


def check_tail():
    fr = frames()
    live = C.live_sheet('jordan_defeat')
    return {i: C.pixel_diff(C.render(fr[i].px), live.crop((96 * i, 0, 96 * i + 96, 96))) for i in (3, 4, 5)}


if __name__ == '__main__':
    for i, d in check_tail().items():
        print('f%d vs live jordan_defeat f%d:' % (i, i), d or 'IDENTICAL')
