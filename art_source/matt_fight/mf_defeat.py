"""matt_defeat.png: 6 frames, 0.13 0.11 0.11 0.13 0.18 hold. Kept simple on purpose: the user has to
confirm this pose.

    0  silent roar   the roar pose, mouth wide, but white panicked eyes and nothing comes out
    1  throat        both fists clutching his throat, eyes squeezed, gasping
    2  buckle        knees going, head drooping, fists still at his throat
    3  sit           down on his heels with a bump, arms flung out
    4  Hong          Hong out and held against his chest
    5  hug (hold)    hugging Hong, eyes shut with tears welling, a wobbling pout

"Sitting down" is drawn as sitting back on his heels: from the front his knees make two humps on
the floor and his feet go behind him, which keeps his own trousers and trainers out of a pose they
were never drawn for.
"""
import mf_base as M
from mf_base import B, A, G, F, H, L, PZ, HG
from mi_base import sh
import mf_faces as FF

# the roar's own face with the red eyes swapped for white, tiny-pupilled panic
ROAR_PANIC = G.patched(G.ROAR, [(35, 39, 'WWWWW'), (36, 39, 'kWhWk'), (35, 55, 'WWWWW'), (36, 54, 'kWhWk')])


def knees(f):
    """Kneeling: two rounded knee humps on the floor, charcoal, shaded as the rig shades the legs."""
    out = []
    for side, cx in ((0, 38.5), (1, 57.5)):
        pts = B.ellipse(cx, 90.5, 9.2, 6.2)
        part = {p: 'L' for p in pts if p[1] <= 94}
        sh.ellipsoid(part, cx, 89.5, 9.5, 6.5, 'NMLK', (0.84, 0.62, 0.2))
        out.append((part, True))
    return out


def throat_arms(dy=0):
    """Both fists up under his chin, gripping his throat."""
    return [A.bent(0, (25, 57 + dy), (24, 60 + dy), (20, 67 + dy), (35, 60 + dy), hand=H.FIST_UP_L,
                   fore_layer='front'),
            A.bent(1, (71, 57 + dy), (72, 60 + dy), (76, 67 + dy), (61, 60 + dy), hand=H.FIST_UP_R,
                   fore_layer='front')]


def defeat_figs():
    sit = 10
    hong = HG.held('STAND', (42, 78))
    # arm points are body-relative: the builder carries them down with the body, so no `sit` here
    hug_arms = [A.bent(0, (25, 57), (24, 60), (22, 68), (35, 68), hand=H.FIST_L,
                       hand_layer='top', fore_layer='top'),
                A.bent(1, (71, 57), (72, 60), (74, 68), (61, 68), hand=H.FIST_R,
                       hand_layer='top', fore_layer='top')]
    hold_arms = [A.bent(0, (25, 57), (24, 60), (20, 68), (31, 69), hand=H.FIST_UP_L, hand_layer='top'),
                 A.bent(1, (71, 57), (72, 60), (76, 68), (65, 69), hand=H.FIST_UP_R, hand_layer='top')]
    return [
        F.Fig(roar=True, collar=False, face=(ROAR_PANIC, G.X0, G.Y0)),
        F.Fig(arms=throat_arms(), head=(0, 0),
              face=(G.face(G.BR_WORRY, G.EY_SQUEEZE, FF.M_O), G.X0, G.Y0),
              spikes=PZ.lerp_spikes(PZ.SP_ROAR, PZ.SP_DROOP, 0.5)),
        F.Fig(arms=throat_arms(dy=2),
              legs=lambda f: L.walk_legs(4, (-2, 0, -1.4), (2, 0, 1.4), screen=True),
              body=(0, 4), head=(0, 6), face=(G.face(G.BR_WORRY, G.EY_SQUEEZE, FF.M_O), G.X0, G.Y0),
              spikes=PZ.SP_DROOP),
        F.Fig(arms=PZ.hang_pair(upper_rot=40, fore_rot=30, shoulder_dy=1), legs=knees,
              body=(0, sit), head=(0, sit + 1), hem=True,
              face=(G.face(G.BR_WORRY, G.EY_SQUEEZE, FF.M_O), G.X0, G.Y0), spikes=PZ.SP_DROOP),
        F.Fig(arms=hold_arms, legs=knees, body=(0, sit), head=(0, sit),
              face=(G.face(G.BR_WORRY, G.EY_ROUND, FF.M_POUT), G.X0, G.Y0),
              parts=[(hong, False, 'front')], spikes=PZ.SP_DROOP),
        F.Fig(arms=hug_arms, legs=knees, body=(0, sit), head=(0, sit + 1),
              face=(G.face(G.BR_WORRY, FF.EY_TEARY, FF.M_POUT), G.X0, G.Y0),
              parts=[(hong, False, 'front')], spikes=PZ.lerp_spikes(PZ.SP_DROOP, PZ.SP_DROOP, 0)),
    ]


class Defeat:
    NAME = 'matt_defeat'

    @staticmethod
    def figs():
        return defeat_figs()
