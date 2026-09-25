"""greyson_defeat.png: 5 frames of 112x112, played once, the last frame held; feet (56, 111).

  0  the last blow: jolted back off his heels, eyes squeezed shut, the barbell knocked up off his
     shoulder, the cannon flung out
  1  the barbell drops: the plate thuds onto the floor at his side (an arc behind it, grit where it
     lands), his knees giving way, the daze face
  2  down on both knees (the shins folded back out of sight under him), the arms hanging, the
     fist still on the bar, the cannon's muzzle on the floor
  3  slumping: the head sinks between the traps, the eyes shut, the jaw hanging ('ko')
  4  out: sunk a little further, the head lolled to one side; held

The kneel is the approved leg traced only as far as the kneecap (gr_fig.leg's outline and bumps,
the calves left out, the knee rounded off onto the floor), shaded exactly like the approved legs.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
import gan_faces as FC  # noqa: E402
from gr_muscle import Form, Layer  # noqa: E402

K = B.K
F = B.gf_fig
G = B.gr_fig
NAME = 'greyson_defeat'
TIMES = [0.1, 0.16, 0.14, 0.2, 0.4]
LOOP = False

PLATE_C = F.PLATE_C
BAR_GRIP = F.BAR_GRIP
FIST = (41.0, 55.0)
SOCKET, MUZZLE = F.mp((21.4, 70.0)), F.mp((13.8, 95.0))
FLOOR_PLATE = (13.5, 100.0)      # the plate come to rest on its rim at his right side

# ------------------------------------------------------------------------------------ the kneel

KNEEL_BUMPS = ('sweep', 'front', 'add', 'knee')
# gr_fig.leg's outline down to the knee, then the kneecap rounded off onto the floor
KNEEL_PTS = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (38.6, 95.2), (40.0, 97.2),
             (42.0, 98.4), (45.0, 99.0), (48.5, 98.8), (51.2, 98.0), (52.8, 96.6), (54.2, 94.2),
             (55.4, 91.4), (55.9, 89.5), (56.0, 80.0)]


def kneel_leg(side):
    """gr_fig.leg (copied, with its outline cut at the knee): the same bumps bar the two calf heads,
    the same form, the same cuts."""
    bumps = G.side_bumps([b for b in G.LEG_BUMPS if b.name in KNEEL_BUMPS], side)
    pix = K.poly(G.mps(KNEEL_PTS, side))
    c = G.mp((46.2, 90), side)
    form = Form(axis=[(c[0], 80), (c[0], 104)], r=9.5)
    lay = Layer(pix, form, bumps, floor=0.2, strength=1.0)
    return lay.shade_owned(cuts=G.CUTS)[0]


def kneel_legs(splay=0):
    """-> (stamp function, drop): both kneeling legs dropped so the kneecaps' keyline is row 111,
    the knees splayed `splay` px outward at the floor."""
    def stamp(cv):
        for side in (0, 1):
            lg = K.despeckle(kneel_leg(side))
            low = max(y for (_x, y) in lg)
            d = 110 - low
            out = {}
            for (x, y), k in lg.items():
                sx = int(round(splay * max(0.0, y - 84) / 16.0)) * (-1 if side == 0 else 1)
                out[(x + sx, y + d)] = k
            cv.stamp(out)
    return stamp


def kneel_drop():
    return 110 - max(y for (_x, y) in K.despeckle(kneel_leg(0)))


# ------------------------------------------------------------------------------------ frames

def blow():
    dx, dy = -3, 1
    cv = B.Canvas()
    B.front_base(cv, lat_flare=0.9, dx=dx, dy=dy, legs=B.squash_legs(drop=(92,), dx=dx))
    R = B.CARRY_REF
    grip_d = (0, -3)
    cv.stamp(B.arm((R.S[0] + dx, R.S[1] + dy), (R.E[0] + dx, R.E[1] + dy),
                   (R.Wr[0] + dx + grip_d[0], R.Wr[1] + dy + grip_d[1]), tri=R.tri, ref=R))
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, dx, dy))
    s = (SOCKET[0] + dx, SOCKET[1] + dy)
    m = (MUZZLE[0] + dx + 6, MUZZLE[1] + dy - 5)
    cv.stamp(B.rec('cannon', B.cannon(s, m, face=0.62)))
    B.rec('muzzle', m)
    cv.stamp(B.rec('head', FC.head('hurt', dx - 3, dy - 1)), outline=False)
    pc = (PLATE_C[0] + dx + 3, PLATE_C[1] + dy - 9)
    grip = (BAR_GRIP[0] + dx + grip_d[0], BAR_GRIP[1] + dy + grip_d[1])
    for p, ol in B.barbell(grip, pc):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (FIST[0] + dx + grip_d[0], FIST[1] + dy + grip_d[1]))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, FC.keep('hurt', dx - 3, dy - 1)), set()


GRIT = [(-9, 8), (-7, 5), (8, 7), (10, 4), (6, 10), (-5, 9)]


def drop():
    """The barbell thuds down; the knees go."""
    rows = (84, 88, 92, 96)
    dx, dy = -1, len(rows)
    cv = B.Canvas()
    B.front_base(cv, lat_flare=0.4, dx=dx, dy=dy, legs=B.squash_legs(drop=rows, spread=1, dx=dx))
    S = (28.0 + dx, 56.0 + dy)
    E = (23.0 + dx, 73.0 + dy)
    Wr = (25.5 + dx, 84.0 + dy)
    cv.stamp(B.arm(S, E, Wr, tri=(-1, 0), ref=B.IDLE_REF))
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, dx, dy))
    s = (90.6 + dx, 70.0 + dy)
    m = (96.0 + dx, 97.5)
    cv.stamp(B.rec('cannon', B.cannon(s, m, face=0.55)))
    B.rec('muzzle', m)
    cv.stamp(B.rec('head', FC.head('daze', dx - 1, dy)), outline=False)
    grip = (24.0 + dx, 92.0 + dy)
    pc = FLOOR_PLATE
    for p, ol in B.barbell(grip, pc, squash=0.6, ang=-70):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (25.0 + dx, 84.5 + dy))
    cv.stamp(B.rec('hand', fist), outline=False)
    # the arc the plate fell through, and grit kicked up where it hit
    fx = B.streaks([(11, 36), (6, 50), (4, 64), (5, 78)], 'X')
    fx.update(B.streaks([(15, 44), (11, 58), (10, 70)], 'W'))
    for (gx, gy) in GRIT:
        fx[(int(pc[0] + gx), int(pc[1] + gy))] = 'X' if (gx + gy) % 2 else 'x'
    fx = {q: k for q, k in fx.items() if q not in cv.px and 0 < q[0] < 111 and 0 < q[1] < 112}
    cv.px.update(fx)
    return B.finish(cv, FC.keep('daze', dx - 1, dy)), set(fx)


def kneel(face, head_dx, head_dy, lat, sink=0, splay=2):
    """On his knees. `sink` lowers the shoulders and arms (the slump); head_dy is the head's
    extra drop below the torso's."""
    D = kneel_drop()
    cv = B.Canvas()
    B.front_base(cv, lat_flare=lat, dy=D, legs=kneel_legs(splay))
    S = (28.0, 56.0 + D + sink)
    E = (22.5, 72.5 + D + sink)
    Wr = (25.5, 83.5 + D)
    cv.stamp(B.arm(S, E, Wr, tri=(-1, 0), ref=B.IDLE_REF))
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, 0, D + sink))
    s = (90.6, 70.0 + D + sink)
    m = (95.5, 106.0)
    cv.stamp(B.rec('cannon', B.cannon(s, m, face=0.5)))
    B.rec('muzzle', m)
    cv.stamp(B.rec('head', FC.head(face, head_dx, D + head_dy)), outline=False)
    grip = (23.0, 91.0 + D)
    pc = FLOOR_PLATE
    for p, ol in B.barbell(grip, pc, squash=0.6, ang=-70):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (24.0, 84.5 + D))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, FC.keep(face, head_dx, D + head_dy)), set()


def builders():
    return [blow,
            drop,
            lambda: kneel('daze', -1, 0, lat=0.3),
            lambda: kneel('ko', 0, 2, lat=0.1, sink=1),
            lambda: kneel('ko', -1, 3, lat=0.0, sink=1)]


def frames_info():
    return B.make_frames(builders())


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    print('kneel drop', kneel_drop())
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()},
              {k: len(v) for k, v in a.items()}, 'bbox', B.bbox(px))
