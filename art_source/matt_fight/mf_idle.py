"""matt_idle.png and matt_spent.png.

matt_idle: 4 frames at 0.16 s, looping. f0 is matt.png f0, pixel for pixel. A slow breath: the
shoulders lift and the crest sways one way, then the head settles a texel on the out-breath and the
crest sways back. (The crest already tops out on row 1, so the breath rides the shoulders, not the
head.)
    0  rest (approved)   1  in: shoulders up, crest leans left   2  out: head settles   3  crest leans right
matt_spent: 4 frames at 0.15 s, looping. Standing upright with one hand up, palm out: "hold on".
Winded but on his feet, so it must not read as the open, punishable crouch (matt_recover).
    0  "haa" open   1  shut, shoulders up   2  "haa" open, hand waggles   3  shut
"""
import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
import mf_faces as FF


def idle_figs():
    return [
        F.Fig(),
        F.Fig(arms=PZ.hang_pair(shoulder_dy=-1), tilt=-1.5),
        F.Fig(head=(0, 1), spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_DROOP, 0.15)),
        F.Fig(tilt=1.5),
    ]


def hold_on_arm(wag=0, dy=0):
    """His right hand (screen-left) up at his shoulder, palm out: the hand of "hold on"."""
    return A.bent(0, (25, 56 + dy), (24, 57 + dy), (16, 62 + dy), (15 + wag, 52 + dy), hand=H.OPEN_UP_L)


SWEAT = [
    "..k..",
    ".kAk.",
    "kWABk",
    "kABCk",
    ".kkk.",
]


def spent_figs():
    sweat = [(M.part(SWEAT, 59, 28), False, 'front')]
    out = []
    for i, (mouth, sh, wag) in enumerate(((FF.M_HAA, 0, 0), (FF.M_HAA_SHUT, -1, 0),
                                          (FF.M_HAA, 0, 1), (FF.M_HAA_SHUT, -1, 0))):
        arms = [hold_on_arm(wag, sh), A.hang(1, upper_rot=4, fore_rot=4, shoulder_dy=sh)]
        face = G.face(G.BR_WORRY, G.EY_SMUG, mouth)
        out.append(F.Fig(arms=arms, face=(face, G.X0, G.Y0), parts=list(sweat),
                         spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_DROOP, 0.35)))
    return out


class Idle:
    NAME = 'matt_idle'

    @staticmethod
    def figs():
        return idle_figs()


class Spent:
    NAME = 'matt_spent'

    @staticmethod
    def figs():
        return spent_figs()
