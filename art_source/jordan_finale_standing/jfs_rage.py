"""jordan_rage.png: 2 frames, the furious talk pair ("What an idiot..." / "This is my world, my
server..."). The finale plays it looped while a rage line types (0 shut, 1 open) and holds frame 0
between lines (rage_shut).

He stands planted in the fitted tee, shaking with fury: both stick arms rigid and held off his sides,
fists clenched white-knuckled (the near one in his pink wristband), shoulders up, head thrust forward
on the thin neck. The finale's glare face (brows crushed, teeth clenched; open, shouting), the ear
burning red, Matt's anger mark popped on the back of his greasy hair and steam off his head, as the
seated glare has them. The shake is in the pair: everything above the knees jolts a pixel between the
two frames, and tremble ticks flicker at the fists (no keyline: effects).

  0  shut: seething, teeth clenched
  1  open: shouting, jolted a pixel forward and up
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402
import jfs_faces as FA  # noqa: E402
import jfs_parts as P  # noqa: E402

V = B.V
NAME = 'jordan_rage'
TIMES = [0.12, 0.12]
LOOP = True

HEAD_AT = (4, 3)            # v2's idle slump (3, 2), thrust a pixel further forward and sunk a pixel
                            # lower between his hunched shoulders

# tremble ticks round a fist: short strokes, white and pale grey (effects)
TICKS_A = {(-2, 1): 'W', (-2, 2): '9', (8, 0): 'W', (8, 1): '9', (-1, 7): '9', (7, 7): 'W'}
TICKS_B = {(-2, 3): 'W', (-2, 4): '9', (8, 3): 'W', (8, 4): '9', (0, 8): 'W', (6, 8): '9'}


def build(face, jolt):
    """jolt: (dx, dy) of everything above the knees (the shake)."""
    dx, dy = jolt
    cv = B.Canvas(96, 96)
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    far, far_fist = P.far_arm_tense(dx, dy)
    B.stamp_all(cv, far)
    hx, hy = HEAD_AT[0] + dx, HEAD_AT[1] + dy
    cv.stamp(B.shift(V.neck(HEAD_AT[0]), dx, dy))
    cv.stamp(B.shift(V.shirt(1), dx, dy))
    B.AB.dandruff(cv.px, dx, dy)
    hd = FA.head(face, hx, hy)
    cv.stamp(hd, outline=False)
    near, near_fist = P.near_arm_tense(dx, dy)
    B.stamp_all(cv, near)
    fx = set()
    FA.anger(cv, hd, fx, flip_steam=(face != 'glare_shut'))
    ticks = TICKS_A if face == 'glare_shut' else TICKS_B
    for (fxo, fyo) in (near_fist, far_fist):
        for (tx, ty), k in ticks.items():
            q = (fxo + tx, fyo + ty)
            if q not in cv.px:
                cv.px[q] = k
                fx.add(q)
    return cv, fx


def builders():
    return [lambda: build('glare_shut', (0, 0)),
            lambda: build('glare_open', (1, -1))]


def frames():
    """[(px, fx)] in frame coordinates."""
    out = []
    for b in builders():
        cv, fx = b()
        out.append((B.fill_holes(B.finish(cv)), {(x + B.ANCHOR_SHIFT, y) for (x, y) in fx}))
    return out
