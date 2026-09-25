"""The bodies of the turning frames: which drawn pose, head and eyes each beat wears.

INTRO (intro_frames.TURN)                       VICTORY (combat_victory.TURN)
  f9   phi 40   the back, squeezed as shipped      f0  phi 180  the approved standing body
                 (so the 天 lands where it did),     f1  phi 126  three-quarter front, turned to
                 his head turning left (back_40)                  screen RIGHT, the look-back's
  f10  phi 90   the back-lit pivot (unchanged)                    face on it (~the same angle)
  f11  phi 132  three-quarter front, turned to     f2  phi 90   the back-lit pivot
                 screen LEFT, the eyes kindling    f3  phi 0    the back view
  f12  phi 162  nearly front: the fists swinging
                 in, the face a pixel round, the
                 eyes nearly lit
  f13  phi 180  front, the arms folding (low X)
  f15           the arms dropping out of the fold
"""
import rig
from rig import fx, K, sq
from lib import Canvas, amap
import front
import backview
import fold
import turn34
import turnheads as TH
import lookback


def _headless_front(arms='idle'):
    import arms as AR
    import jacket as JK
    import chest as CH
    cv = front.lower_body(Canvas())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    front.belt(cv)
    cv.stamp(AR.fist_l(), outline=False)
    cv.stamp(AR.fist_r(), outline=False)
    return cv.px


def _stamp(px, parts):
    cv = Canvas()
    cv.px = dict(px)
    for p in parts:
        cv.stamp(p, outline=False)
    return cv.px


def _shift(part, dx, dy=0):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def _back_40(st):
    """phi 40, exactly the shipped pipeline on the polished back - bloom, rim light and the mark at
    this beat's levels, then hsq_canvas and the shift - so every pixel of the 天 is where it was.
    Only then is the squeezed back head lifted out (found with a probe sent through the same squeeze)
    and the turning head put in its place."""
    s = sq(st['phi'])
    dx = int(round(4.0 * (1.0 - s)))
    m = st['mark']
    full = backview.body().px
    px = fx.burn(full, m, bloom=m * 0.8, host=backview.host(), rim=m * 0.8, reach=32.0)
    px = fx.squeeze(px, s, keep_head=True, dx=dx)
    head = set(backview.head_back()) | set(backview.earring_back())
    probe = {q: ('M' if q in head else 'c') for q in full}
    probe = fx.squeeze(probe, s, keep_head=True, dx=dx, reoutline=False)
    for q, k in probe.items():
        if k == 'M':
            px.pop(q, None)
    cross = _shift(backview.earring_back(), dx - 2)     # the far ear's cross, hanging under the jaw
    px = _stamp(px, [cross])
    return _stamp(px, [_shift(TH.back_40(), dx)])


def intro_body(i):
    st = K.turn[i]
    phi = st['phi']
    s = sq(phi)
    if i == 0:
        return _back_40(st)
    if i == 1:
        px = fx.burn(backview.body().px, 0.80, bloom=0.70, host=backview.host())
        return fx.pivot(fx.squeeze(px, s))
    kindle = max(0.0, min(1.0, (phi - 110.0) / 70.0))
    if i == 2:
        body = turn34.front34(_headless_front(), 180.0 - phi, -1)
        return _stamp(body, [TH.eyes(TH.left_48(), kindle)])
    if i == 3:
        body = fold.body(fold.diag(st["arm"]), head=False).px
        return _stamp(body, [TH.eyes(TH.near_front(1), kindle), TH.earring_front()])
    return fold.body(fold.low_x(st['arm']), crossed_torso=True).px


def arms_dropping():
    return fold.body(fold.diag(K.settle_arm[1])).px


def look_body(k):
    return lookback.body(k).px


def victory_front(i):
    phi = K.vic_turn[i]['phi']
    if phi >= 179.0:
        return front.idle().px
    body = turn34.front34(_headless_front(), 180.0 - phi, 1)
    return _stamp(body, [amap(lookback.LOOK, 30, 24), lookback.earring(lookback.EARRING_X[3])])
