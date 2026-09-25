"""matt_doll.png: "AH I NEED MY HONG STRESS TOY", 8 frames.

    0  reach    his left hand (screen-right) goes behind his back; wide frantic eyes, yelling
    1  pull     Hong yanked out, arms flung up by the whip of it, a swoosh behind; a manic grin
    2  hold     Hong held up at arm's length; Matt's head turned to him, a fixed crazed grin
    3-5 scream  Hong pulled in beside his face and shaken; Matt leans in and screams at him, head
                turned three-quarters, mouth wide, crest bristling. Three shake positions with Hong's
                limbs flailing, looping.
    6  stow     Hong going back behind his back, one last peek past his hip; Matt calmer, eyes shut
    7  exhale   a long breath out, shoulders dropped, crest settling

Hong stands in Matt's raised fist, held by the legs (mi_hong.held); the doll is stamped over the
head and the fist over the doll, so Hong is always in front and always gripped. Effects (the
swoosh, the breath) carry no keyline.
"""
import math

import mi_arms as A
import mi_base as B
import mi_faces as G
import mi_fig as F
import mi_hands as H
import mi_hong as HG
import mi_poses as PZ

NAME = 'matt_doll'
FIST = H.FIST_UP_R


def doll_arm(pose, elbow, wrist, dc=(71, 57), s0=(72, 59), body=(0, 0)):
    """The screen-right arm raised with Hong standing in its fist. Returns (arm, doll part, the
    hand's centre in frame coordinates)."""
    arm = A.bent(1, dc, s0, elbow, wrist, hand=FIST, hand_layer='top')
    ax, ay = A.attach(arm)
    rows, (ac, ar) = FIST
    tl = (int(round(ax)) - ac + body[0], int(round(ay)) - ar + body[1])
    doll = HG.held(pose, tl)
    hand = (tl[0] + 6, tl[1] + 5)
    return arm, doll, hand


def swoosh(cx, cy):
    """Two speed arcs sweeping out from behind his hip: the yank."""
    pts = {}
    for r, key in ((12, 'X'), (9, 'x')):
        for t in range(0, 70, 4):
            a = math.radians(95 - t)
            x = int(round(cx + r * math.cos(a) * 1.4))
            y = int(round(cy + r * math.sin(a) * 0.9))
            pts[(x, y)] = key
    return pts


def reach():
    arm = A.bent(1, (71, 57), (72, 59), (77, 64), (61, 69), hand=None, fore_layer='back')
    arms = [A.hang(0, upper_rot=14, fore_rot=16), arm]
    face = G.with_jaw(G.face(G.BR_WORRY, G.EY_WIDE), G.YELL_ROWS)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), head=(1, 0), spikes=PZ.SP_TENSE)


def pull():
    arm, doll, hand = doll_arm('FLAIL_A', (84, 73), (86, 65))
    sw = swoosh(70, 66)
    face = G.face(G.BR_HIGH, G.EY_WIDE, G.M_GRIN_TEETH)
    f = F.Fig(arms=[A.hang(0, upper_rot=6, fore_rot=8), arm], face=(face, G.X0, G.Y0),
              parts=[(sw, False, 'mid'), (doll, False, 'front')], spikes=PZ.SP_TENSE)
    f.fx = set(sw)
    f.anchors['doll_hand'] = hand
    return f


def hold():
    arm, doll, hand = doll_arm('STAND', (84, 52), (86, 43), dc=(71, 56), s0=(72, 57))
    face = G.face34(G.BR34_HIGH, G.EY34_WIDE, G.M34_GRIN_TEETH)
    f = F.Fig(arms=[A.hang(0, upper_rot=4, fore_rot=6), arm], face=(face, G.X0, G.Y0),
              parts=[(doll, False, 'front')], spikes=PZ.SP_TENSE, head=(1, 0))
    f.anchors['doll_hand'] = hand
    return f


SHAKE = [
    # (arm offset, doll pose, head offset, left-fist tremble, crest quiver)
    ((0, -1), 'FLAIL_A', (3, 1), 1, 2),
    ((2, 1), 'FLAIL_B', (3, 2), -1, -2),
    ((-1, 1), 'STAND', (2, 1), 0, 1),
]


def scream(k):
    (ox, oy), pose, head, trem, q = SHAKE[k]
    body = (1, 0)
    arm, doll, hand = doll_arm(pose, (82 + ox, 72 + oy), (80 + ox, 63 + oy), body=body)
    face = G.with_jaw(G.face34(G.BR34_ANGRY, G.EY34_ANGRY), G.YELL34_ROWS)
    spikes = [(a + (q if j % 2 else -q) * (1 if a else 0), r0, r1, w0, w1, b)
              for j, (a, r0, r1, w0, w1, b) in enumerate(PZ.SP_BRISTLE)]
    f = F.Fig(arms=[A.hang(0, upper_rot=14, fore_rot=10, dx=trem), arm], face=(face, G.X0, G.Y0),
              parts=[(doll, False, 'front')], spikes=spikes, head=head, body=body)
    f.anchors['doll_hand'] = hand
    return f


def stow():
    """Hong going back behind his back: the arm bent behind him as in the reach, Hong's head and
    tee still showing past his hip on the way in."""
    arm = A.bent(1, (71, 57), (72, 59), (74, 65), (62, 71), hand=None, fore_layer='back')
    doll = HG.held('STAND', (62, 76))       # behind his hip and trouser leg, in front of the forearm
    face = G.face(G.BR_RELAX, G.EY_SMUG, G.M_SETTLE)
    f = F.Fig(arms=[A.hang(0, upper_rot=2, fore_rot=2), arm], face=(face, G.X0, G.Y0),
              parts=[(doll, False, 'back2')], spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_DROOP, 0.3))
    f.anchors['doll_hand'] = (68, 81)
    return f


def exhale():
    """A long breath out: shoulders dropped a pixel, head sunk with them, eyes shut, "hoo"."""
    breath = B.amap(G.BREATH, 61, 45)
    face = G.face(G.BR_RELAX, G.EY_SMUG, G.M_HOO)
    f = F.Fig(arms=PZ.hang_pair(shoulder_dy=1), face=(face, G.X0, G.Y0), head=(0, 1),
              parts=[(breath, False, 'top')], spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_DROOP, 0.6))
    f.fx = set(breath)
    return f


def figs():
    return [reach(), pull(), hold(), scream(0), scream(1), scream(2), stow(), exhale()]


def frames():
    return [F.px_of(f) for f in figs()]
