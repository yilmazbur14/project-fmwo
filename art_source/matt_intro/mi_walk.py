"""matt_walk.png: the friendly walk-in, 6 frames looping. He walks toward camera and a little to
screen-right, head turned three-quarters that way, waving with his near (screen-left) hand the whole
way: the open hand rocks out, up, in and back across the cycle while the other arm swings.
The game mirrors the strip (flip_h) for the other direction.

The cycle, two steps:
    0  contact     screen-left foot planted forward, the other back on its toe   body low
    1  lift        the back foot comes up                                        body rising
    2  pass        the lifted foot passes under him                              body high
    3  contact     screen-right foot planted forward                             body low
    4  lift
    5  pass
Bounce: the body bobs 3 px and the head sinks one more on each contact (squash), the crest flops
down on the landings and springs up at the top.
"""
import mi_base as B
import mi_arms as A
import mi_faces as G
import mi_fig as F
import mi_hands as H
import mi_legs as L
import mi_poses as PZ

NAME = 'matt_walk'

BODY = [2, 1, 0, 2, 1, 0]            # torso bob, down from rest (the crest already tops out at row 1)
HEAD_REL = [1, 0, 0, 1, 0, 0]        # extra head drop on contact: the squash
FLOP = [1.0, 0.5, 0.0, 1.0, 0.5, 0.0]
# feet: (dx, dy, knee lean) for the screen-left and screen-right foot
FEET = [
    ((0, 0, 0.0), (1, -1, 0.0)),     # 0 contact: right foot back, heel up
    ((0, 0, 0.0), (1, -4, 0.8)),     # 1 lift
    ((0, 0, 0.0), (1, -3, 0.4)),     # 2 pass
    ((0, -1, 0.0), (1, 0, 0.0)),     # 3 contact: left foot back, heel up
    ((0, -4, -0.8), (1, 0, 0.0)),    # 4 lift
    ((0, -3, -0.4), (1, 0, 0.0)),    # 5 pass
]
BACK = [1, 1, 1, 0, 0, 0]            # which leg is drawn first (further from camera)
WAVE = [-1, 0, 1, 1, 0, -1]          # the waving hand: out, up, in, in, up, out
SWING = [1, 0.5, -0.5, -1, -0.5, 0.5]  # the other arm: + forward (toward camera)


def wave_arm(tilt):
    wrist = {-1: (10, 39), 0: (13, 38), 1: (16, 39)}[tilt]
    hand = H.shear(H.OPEN_UP_L, 0.25 * tilt)
    return A.bent(0, (25, 56), (24, 57), (14, 49), wrist, hand=hand)


def swing_arm(s):
    return A.hang(1, upper_rot=-6 * s + 2, fore_rot=-10 * s, dy=int(round(s * 0.6)))


def fig(i):
    body = BODY[i]
    head = body + HEAD_REL[i]
    (lx, ly, ll), (rx, ry, rl) = FEET[i]
    legs = (lambda f, i=i, body=body: L.walk_legs(body, FEET[i][0], FEET[i][1], back=BACK[i]))
    face = G.face34(G.BR34_RELAX, G.EY34_SOFT, G.M34_SMILE_OPEN)
    spikes = PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_DROOP, FLOP[i])
    return F.Fig(arms=[wave_arm(WAVE[i]), swing_arm(SWING[i])], legs=legs, body=(0, body),
                 head=(0, head), face=(face, G.X0, G.Y0), spikes=spikes)


def figs():
    return [fig(i) for i in range(6)]


def frames():
    return [F.px_of(f) for f in figs()]
