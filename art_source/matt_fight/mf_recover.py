"""matt_recover.png and matt_hit.png: the punish window.

matt_recover: 4 frames at 0.18 s, looping. Hands on knees, bent over, wheezing with his tongue out:
the punish silhouette, low and wide. Bent over, his head drops in front of his chest, the belly and
the hem band tuck out of sight, the thighs show under the chest, and each fist rests on a knee.
    0  wheeze        tongue out
    1  gasp in       shoulders and head heave up a texel, mouth wide, tongue in
    2  wheeze        tongue out further
    3  sag           shoulders and head sink a texel, crest drooping, a bead of sweat
matt_hit: 2 frames, 0.07 then 0.12, from the recover stance.
    0  impact        head snapped back and aside, eyes squeezed, an "OOF", fists jolted off the knees
    1  recoil        settling back toward the knees, a pained grimace
"""
import mf_base as M
from mf_base import B, A, G, F, H, L, PZ

# ------------------------------------------------------------------ faces
EY_SHUT = [(36, 38, 'kkkkkk'), (37, 39, 'kkkk'), (36, 53, 'kkkkkk'), (37, 54, 'kkkk')]
# panting with the tongue hanging over the lower lip
M_PANT = [(45, 42, 'kkkkkkkkkkkkk'), (46, 42, 'kWWWWWWWWWWXk'), (47, 43, 'kmnnqqqnnmk'),
          (48, 44, 'kkqrrrqkk'), (49, 45, 'kqrRrqk'), (50, 45, 'kqrrrqk'), (51, 46, 'kqrqk'), (52, 47, 'kkk')]
M_PANT_LOW = [(45, 42, 'kkkkkkkkkkkkk'), (46, 42, 'kWWWWWWWWWWXk'), (47, 43, 'kmnnqqqnnmk'),
              (48, 44, 'kkqrrrqkk'), (49, 45, 'kqrRrqk'), (50, 45, 'kqrrrqk'), (51, 45, 'kqrrrqk'),
              (52, 46, 'kqrqk'), (53, 47, 'kkk')]
# gasping in: the mouth wide, the tongue back inside
M_GASP = [(44, 42, 'kkkkkkkkkkkkk'), (45, 42, 'kWWWWWWWWWWXk'), (46, 42, 'kmmnnnnnnnmmk'),
          (47, 42, 'kmnqrrrrrqnmk'), (48, 43, 'kkqrRRrqkkk'), (49, 45, 'kkkkkkk')]
# the hit: a round "OOF", then a pained grimace
M_OOF = [(44, 46, 'kkkkk'), (45, 45, 'kmnnnmk'), (46, 44, 'kmnmmmnmk'), (47, 44, 'kmnqrqnmk'),
         (48, 45, 'knqrqnk'), (49, 46, 'kkkkk')]


def tuck(bottom):
    """Bent over: everything of the sweatshirt below `bottom` (build coordinates) is out of sight."""
    def hook(part):
        for (x, y) in list(part):
            if y > bottom:
                del part[(x, y)]
    return hook


# ------------------------------------------------------------------ the stance
STANCE, HIP = 3, 3


def legs(f):
    return L.walk_legs(HIP, (-STANCE, 0, -1.2), (STANCE, 0, 1.2), screen=True)


def knee_arms(dy=0, lift=0, spread=0):
    """Both arms straight down onto the knees; lift raises the fists off them, spread pushes them
    out."""
    el, wl = (27 - spread, 65 + dy - lift), (31 - spread, 72 + dy - lift)
    return [A.bent(0, (25, 57 + dy), (24, 60 + dy), el, wl, hand=H.FIST_L),
            A.bent(1, (71, 57 + dy), (72, 60 + dy), (96 - el[0], el[1]), (96 - wl[0], wl[1]), hand=H.FIST_R)]


def fig(body, head, face, arms=None, spikes=PZ.SP_DROOP, parts=(), head_dx=0):
    return F.Fig(arms=arms if arms is not None else knee_arms(), legs=legs, body=(0, body),
                 head=(head_dx, head), face=(face, G.X0, G.Y0), spikes=spikes, hem=False,
                 torso_hook=tuck(66), parts=list(parts))


SWEAT_SMALL = [
    "..k..",
    ".kAk.",
    "kWABk",
    "kABCk",
    ".kkk.",
]


def recover_figs():
    sweat = [(M.part(SWEAT_SMALL, 59, 36), False, 'front')]
    droop = PZ.lerp_spikes(PZ.SP_DROOP, PZ.SP_IDLE, 0.0)
    return [
        fig(4, 11, G.face(G.BR_WORRY, EY_SHUT, M_PANT)),
        fig(3, 10, G.face(G.BR_WORRY, EY_SHUT, M_GASP), arms=knee_arms(dy=-1),
            spikes=PZ.lerp_spikes(PZ.SP_DROOP, PZ.SP_IDLE, 0.4)),
        fig(4, 11, G.face(G.BR_WORRY, EY_SHUT, M_PANT_LOW)),
        fig(5, 12, G.face(G.BR_WORRY, EY_SHUT, M_PANT), arms=knee_arms(dy=1), spikes=droop, parts=sweat),
    ]


def hit_figs():
    return [
        fig(3, 8, G.face(G.BR_WORRY, G.EY_SQUEEZE, M_OOF), arms=knee_arms(dy=-1, lift=3, spread=2),
            spikes=PZ.SP_TENSE, head_dx=-2),
        fig(4, 10, G.face(G.BR_WORRY, G.EY_SQUEEZE, G.M_GRIT), arms=knee_arms(lift=1, spread=1),
            spikes=PZ.lerp_spikes(PZ.SP_TENSE, PZ.SP_DROOP, 0.5), head_dx=-1),
    ]


class Recover:
    NAME = 'matt_recover'

    @staticmethod
    def figs():
        return recover_figs()


class Hit:
    NAME = 'matt_hit'

    @staticmethod
    def figs():
        return hit_figs()
