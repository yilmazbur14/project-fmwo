"""matt_yell_tell.png and matt_mystic_cast.png: the two shout wind-ups.

matt_yell_tell: 2 frames at 0.20 s. Out of the recover crouch he snaps upright and drags in a huge
breath, cheeks full, fists at his sides, no hands at the mouth; the roar sheet's f1-3 is the yell.
    0  snap up       upright with a jolt, brows flying up, eyes wide, cheeks already full
    1  full inhale   shoulders jammed up, chest out, brows slammed down, crest spreading for the roar
matt_mystic_cast: 4 frames, 0.225 0.225 0.075 0.075. A sharp "HA!" with the head thrust forward.
    0  wind-up       head back, fists pulled in, lips pressed, breathing in through the nose
    1  wind-up       the breath held, shoulders up, cheeks filling, crest drawn in tight
    2  HA!           head thrust forward and down, mouth wide: the bolt leaves the mouth texel
    3  follow-through  head coming back, crest settling
"""
import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
import mf_faces as FF

SP_TIGHT = [(0, 8, 26, 6.2, 1.9, 0.0), (-25, 8, 25, 6.2, 1.9, 1.0), (-56, 9, 25, 7.0, 2.2, 1.5)]


def yell_tell_figs():
    return [
        F.Fig(arms=PZ.hang_pair(upper_rot=8, fore_rot=6, shoulder_dy=-2), body=(0, -1), head=(0, -1),
              face=(FF.puffed(G.BR_HIGH, G.EY_WIDE), G.X0, G.Y0), spikes=PZ.SP_PERK, neck=True),
        F.Fig(arms=PZ.hang_pair(upper_rot=14, fore_rot=8, shoulder_dy=-3), body=(0, -1), head=(0, -1),
              face=(FF.puffed(G.BR_ANGRY, G.EY_WIDE), G.X0, G.Y0), spikes=PZ.SP_TENSE, neck=True),
    ]


def mystic_cast_figs():
    return [
        F.Fig(arms=PZ.hang_pair(upper_rot=-4, fore_rot=-10, shoulder_dy=-1), head=(0, -1), neck=True,
              face=(G.face(G.BR_ANGRY, G.EY_ANGRY, FF.M_PRESS), G.X0, G.Y0), spikes=SP_TIGHT),
        F.Fig(arms=PZ.hang_pair(upper_rot=-6, fore_rot=-12, shoulder_dy=-2), head=(0, -1), neck=True,
              face=(FF.puffed(G.BR_ANGRY, G.EY_ANGRY), G.X0, G.Y0),
              spikes=PZ.lerp_spikes(SP_TIGHT, PZ.SP_IDLE, -0.2)),
        F.Fig(arms=PZ.hang_pair(upper_rot=20, fore_rot=14, shoulder_dy=-1), body=(0, 1), head=(0, 2),
              face=(G.with_jaw(G.face(G.BR_ANGRY, G.EY_WIDE), G.YELL_ROWS), G.X0, G.Y0), spikes=PZ.SP_ROAR),
        F.Fig(arms=PZ.hang_pair(upper_rot=12, fore_rot=8), head=(0, 1),
              face=(G.face(G.BR_ANGRY, G.EY_ANGRY, FF.M_HA), G.X0, G.Y0),
              spikes=PZ.lerp_spikes(PZ.SP_ROAR, PZ.SP_IDLE, 0.5)),
    ]


class YellTell:
    NAME = 'matt_yell_tell'

    @staticmethod
    def figs():
        return yell_tell_figs()


class MysticCast:
    NAME = 'matt_mystic_cast'

    @staticmethod
    def figs():
        return mystic_cast_figs()
