"""jordan_climb: 6 frames, once (0.10 each). His leap back onto the kaiju's head (the intro's leap from
the mat, and every remount). The kaiju is on his left while he faces right, so the leap is a showy
BACKFLIP: a tuck reads the same whichever way the code carries him, and he lands astride facing right.

  0  crouch on his soles (soles row 95): knees bent deep, arms swung back, the box swung low, gritting
  1  launch: legs snapped straight, toes pointed, arms thrown up, the box hoisted, yelling
  2  tuck: curled into a ball (knees to chest, the box held out), a quarter turn back (exact turn)
  3  tuck: upside down at the top of the flip, grinning (he is enjoying this) (exact turn)
  4  scramble: landed astride the head, pitched forward, the near hand slapped down gripping the skull,
     the dangling leg still swinging, hair whipped
  5  settle: sat up into the seat, the hand back on his hip, the box up, a grin. Then ride_idle.

SOLES on f0 (the start), SEAT on f4-f5 (the end), PIVOT = his body's centre on every frame (the flip
turns about it), for the arc. Air frames f2-f3 are turned with the juggle's RotSprite turner.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_mat as M     # noqa: E402
import jr_rider as RR  # noqa: E402
import jr_rot as ROT   # noqa: E402
import jr_sheet as S   # noqa: E402

NAME = 'jordan_climb'
TIMES = [0.10] * 6
LOOP = False
KIND = 'mat'
OFFSET = (-1, 0)
NOTE = ('Start: SOLES (f0) on the take-off spot; end: SEAT (f4, f5) on the kaiju RIDER_SEAT (kneel/bow/idle '
        'seat). PIVOT = body centre for the arc. Faces right throughout (a backflip), so it works for a leap '
        'either way; never flip it.')
V, JB, J = F.V, F.JB, F.J


def crouch_legs(drop, knees_out=1):
    """v2's thin jeans in a deep crouch: `drop` rows taken out of the thighs and shins (the hips sink,
    the soles stay), the bony knees pushed forward (to the right) as they bend."""
    out = {}
    for (x, y), k in V.legs().items():
        if y in drop:
            continue
        out[(x, y + sum(1 for r in drop if r > y))] = k
    res = {}
    for (x, y), k in out.items():
        dx = 0
        if 74 <= y <= 88:
            w = 1.0 - abs(y - 81) / 8.0
            dx = int(round(knees_out * 2 * w))
        res[(x + dx, y)] = k
    return res


def f0():
    """Crouch: hips down 6, leaning in, arms swung back, the box hanging low from the far hand."""
    dy = 10
    fig = F.Fig()
    fig.stamp(M.leg((52.5, 77.5), (63.0, 80.5), (56.0, 88.5), lit_side=False, hem=(56.0, 88.0)))
    fig.stamp(M.shoe('far', (54, 89)), outline=False)
    fig.stamp(M.hips(1, dy))
    ux, uy = 4, dy
    # the far arm hanging back with the box (v2's fist-pump carry: LOW_HAND over the box's top edge)
    fig.stamp_all(M.arm_to('far', ux, uy, (62.5, 71.0), bend=-1))
    M.torso(fig, ux, uy, frame=1, lean=F.HEAD_AT[0] + 2)
    hd = F.head('grit', dx=F.HEAD_AT[0] + ux + 2, dy=F.HEAD_AT[1] + uy + 1, tilt=6)
    fig.stamp(hd, outline=False, name='head')
    fig.stamp(M.shoe('near', (40, 89)), outline=False)
    fig.stamp(M.leg((46.5, 78.0), (57.5, 81.5), (42.0, 88.5), hem=(42.5, 88.0)))
    fig.stamp_all(M.arm_to('near', ux, uy, (34.5, 72.5), bend=1))
    fig.stamp(F.map_at(F.HAND_HANG, 32, 72), outline=False)
    box = F.open_box(1, 46)
    fig.stamp(box, outline=False, name='box')
    fig.stamp(F.amap(V.LOW_HAND, 59, 71), outline=False)
    return fig, {'SOLES': (49, 95), 'PIVOT': (51, 66)}, 'crouch on his soles'


def f1():
    """Launch: legs straight, toes pointed down, arms flung up, the box hoisted."""
    lift = 6
    fig = F.Fig()
    legs = C.shift(V.legs(), 0, -lift)
    fig.stamp(legs)
    fig.stamp(M.shoe('far', (54, 89 - lift), deg=28), outline=False)
    fig.stamp(M.shoe('near', (40, 89 - lift), deg=28), outline=False)
    ux, uy = 0, -lift - 1
    fig.stamp_all(M.arm_to('far', ux, uy, (66.5, 30.0), bend=-1))
    M.torso(fig, ux, uy, frame=1)
    hd = F.head('shout', dx=F.HEAD_AT[0] + ux - 1, dy=F.HEAD_AT[1] + uy, tilt=-6)
    fig.stamp(hd, outline=False, name='head')
    fig.stamp_all(M.arm_to('near', ux, uy, (36.0, 27.0), bend=-1))
    fig.stamp(F.map_at(F.FIST_UP_FULL, 32, 18), outline=False)
    bdx, bdy = 2, -20
    fig.stamp(F.open_box(bdx, bdy), outline=False, name='box')
    fig.stamp(F.far_hand_box(bdx, bdy), outline=False)
    return fig, {'PIVOT': (50, 56)}, 'launch'


TUCK_C = (52.0, 58.0)


def tuck_fig(face):
    """Curled up: knees to his chest, shins folded under, the near arm wrapped round his shins, the
    box held out on the far arm."""
    fig = F.Fig()
    fig.stamp(M.leg((52.0, 67.5), (61.0, 58.5), (57.0, 67.0), lit_side=False, hem=(57.0, 66.5)))
    fig.stamp(M.shoe('far', (57, 68)), outline=False)
    ux, uy = 2, 3
    fig.stamp_all(M.arm_to('far', ux, uy, (69.0, 44.0), bend=-1))
    fig.stamp(M.hips(0, -1))
    M.torso(fig, ux, uy, frame=1, lean=F.HEAD_AT[0] + 3)
    hd = F.head(face, hair='whip_a', dx=F.HEAD_AT[0] + ux + 2, dy=F.HEAD_AT[1] + uy + 2, tilt=10)
    fig.stamp(hd, outline=False, name='head')
    fig.stamp(M.shoe('near', (51, 70)), outline=False)
    fig.stamp(M.leg((47.0, 68.0), (58.0, 60.5), (51.0, 69.0), hem=(51.5, 68.5)))
    fig.stamp_all(M.arm_to('near', ux, uy, (57.5, 66.0), bend=1))
    fig.stamp(F.map_at(F.FIST_SIDE, 56, 63), outline=False)
    bdx, bdy = 5, -6
    fig.stamp(F.open_box(bdx, bdy), outline=False, name='box')
    fig.stamp(F.far_hand_box(bdx, bdy), outline=False)
    return fig


def tucked(deg, face, place):
    fig = tuck_fig(face)
    xs = [x for (x, y) in fig.px]
    ys = [y for (x, y) in fig.px]
    c = (round(sum(xs) / len(xs)), round(sum(ys) / len(ys)))      # its centroid, a whole corner: exact quarters
    px = ROT.turn(fig.px, deg, c, place)
    hp = ROT.turn(dict(fig.pts['head']), deg, c, place)
    out = F.Fig()
    out.cv.px.update(px)
    out.pts['head'] = {q: px[q] for q in hp if q in px} or hp
    return out


def f2():
    fig = tucked(-90, 'grit', (52, 48))
    return fig, {'PIVOT': (52, 48)}, 'tuck, a quarter turn back'


def f3():
    fig = tucked(-180, 'grin', (52, 48))
    return fig, {'PIVOT': (52, 48)}, 'tuck, upside down'


def f4():
    """Scramble: landed astride, pitched forward, the near hand slapped down gripping the skull."""
    up = (3, 3)
    sh = (F.NEAR_ROOT[0] + up[0], F.NEAR_ROOT[1] + up[1])
    wrist = (55.0, 66.0)
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, 1)
    near = F.near_arm(sh, el, wrist) + [(F.map_at(F.FIST_HANG, 52, 66), False)]
    bdx, bdy = up[0] + 2, up[1] - 8
    import jr_s_ride_throw as RT
    far = RT.far_box_arm(up, bdx, bdy)
    head = F.head('grit', hair='whip_b', dx=F.HEAD_AT[0] + up[0] + 1, dy=F.HEAD_AT[1] + up[1] + 1, tilt=6)
    fig = RR.rider(up=up, head=head, far=far, near=near, box=F.open_box(bdx, bdy), far_hand=F.far_hand_box(bdx, bdy),
                   shin=(4, -3))
    return fig, {'SEAT': F.SEAT_PT, 'PIVOT': (50, 58)}, 'scramble: landed astride, gripping'


def f5():
    """Settle: sat up into the seat, a grin, the shin swinging back under him."""
    up = (1, 1)
    head = F.head('grin', dx=F.HEAD_AT[0] + up[0], dy=F.HEAD_AT[1] + up[1])
    fig = RR.rider(up=up, head=head, shin=(2, -1))
    return fig, {'SEAT': F.SEAT_PT, 'PIVOT': (50, 58)}, 'settled in the seat'


def frames():
    out = []
    for i, b in enumerate((f0, f1, f2, f3, f4, f5)):
        fig, a, note = b()
        a = dict(a)
        a['CROWN'] = S.crown(fig.px, fig.pts['head'])
        fr = S.to_frame(fig, OFFSET, a, on_mat=(i == 0), note=note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
