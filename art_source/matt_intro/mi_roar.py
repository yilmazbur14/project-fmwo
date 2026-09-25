"""matt_roar.png: the arena-shaking roar that ends the intro, 4 frames:

    0      brace     he drags in a breath: shoulders jammed up, head back, eyes squeezed shut, a
                     small dark "o" of a mouth, fists pulled in, the crest drawn tight
    1-3    roar      the approved roar pose (frame 1 is the approved frame without its rings),
                     looping with a slight vibration: the body shakes a pixel side to side, the
                     head and fists tremble, the crest quivers and the jaw pulses a row deeper

No sound rings are baked in: the rings are a separate effect in the game. The red eyes and the
flared crest are the approved ones.
"""
import mi_base as B
import mi_faces as G
import mi_fig as F
import mi_poses as PZ

NAME = 'matt_roar'
ROAR_FACE = (G.ROAR, G.X0, G.Y0)
SP_TIGHT = [(0, 8, 26, 6.2, 1.9, 0.0), (-25, 8, 25, 6.2, 1.9, 1.0), (-56, 9, 25, 7.0, 2.2, 1.5)]


def quiver(sp, d):
    """The roar crest with each pair's angle nudged d degrees (alternating) and length nudged."""
    out = []
    for j, (a, r0, r1, w0, w1, bend) in enumerate(sp):
        s = 1 if j % 2 else -1
        out.append((a + s * d if a else a, r0, r1 + (1 if d > 0 and j == 2 else 0), w0, w1, bend))
    return out


def brace():
    arms = PZ.hang_pair(upper_rot=-6, fore_rot=-8, shoulder_dy=-3)
    face = G.face(G.BR_ANGRY, G.EY_SQUEEZE, G.M_INHALE)
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), spikes=SP_TIGHT, head=(0, -1), neck=True,
                 body=(0, -1))


def roar(k):
    """k = 0 is the approved roar exactly (minus rings); 1 and 2 are the vibration."""
    if k == 0:
        return F.Fig(roar=True, collar=False, face=ROAR_FACE)
    if k == 1:
        return F.Fig(roar=True, collar=False, face=(G.ROAR_DEEP, G.X0, G.Y0),
                     body=(1, 0), head=(1, 0),
                     arms=[_roar_arm(0, 1, 1), _roar_arm(1, 1, 1)],
                     spikes=quiver(PZ.SP_ROAR, 2))
    return F.Fig(roar=True, collar=False, face=ROAR_FACE,
                 body=(-1, 0), head=(-1, 1),
                 arms=[_roar_arm(0, -1, 0), _roar_arm(1, -1, 0)],
                 spikes=quiver(PZ.SP_ROAR, -2))


def _roar_arm(side, dx, dy):
    import mi_arms as A
    return A.hang(side, upper_rot=30, fore_rot=6, shoulder_dy=-3, dx=dx - 0, dy=dy)


def figs():
    return [brace(), roar(0), roar(1), roar(2)]


def frames():
    return [F.px_of(f) for f in figs()]
