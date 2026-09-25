"""The approved front poses, without their aura, so the turn frames can wear their own.

    idle()     -> the body of carter_polish frame 0 (standing, arms hanging)
    crossed()  -> the body of carter_polish frame 1 (arms crossed, the signature)
    check()    -> both, with the approved aura put back, must equal frame0.build() / frame1.build()
                  pixel for pixel - the proof that these are the approved bodies and nothing else

The stamping is frame0.py / frame1.py's own, line for line, stopping before the aura.
"""
from lib import Canvas, grow
import head as HD
import chest as CH
import arms as AR
import jacket as JK
import lower as LO
import aura as AU
import cross as CR
import frame0
import frame1


def lower_body(cv):
    cv.stamp(LO.shins())
    for f in LO.feet():
        cv.stamp(f, outline=False)
    cv.stamp(LO.trousers())
    return cv


def belt(cv):
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(LO.knot(), outline=False)
    cv.stamp(LO.tails(), outline=False)
    return cv


def head(cv):
    cv.stamp(HD.head(), outline=False)
    cv.stamp(HD.earring(), outline=False)
    return cv


def idle():
    cv = lower_body(Canvas())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    belt(cv)
    cv.stamp(AR.fist_l(), outline=False)
    cv.stamp(AR.fist_r(), outline=False)
    return head(cv)


def crossed():
    cv = lower_body(Canvas())
    for j in JK.jacket():
        cv.stamp(j)
    cv.stamp(CH.chest(), outline=False)
    for b in CH.beads():
        cv.stamp(b, outline=False)
    belt(cv)
    parts = CR.arms()
    for part, outline in parts:
        cv.stamp(part, outline=outline)
    for part, _ in parts[4:]:
        low = {}
        for (x, y) in part:
            low[x] = max(low.get(x, y), y)
        for x, y in low.items():
            q = (x, y + 2)
            if cv.px.get((x, y + 1)) == 'k' and cv.px.get(q) in tuple('nopqr'):
                cv.px[q] = 'k'
    import lib
    lib.patch(cv.px, frame1.KNUCKLES)
    return head(cv)


def with_idle_aura(cv):
    body = set(cv.px)
    cv.stamp(AU.flames(AU.IDLE, grow(body, 1), AU.IDLE_ORDER), outline=False, under=True)
    cv.stamp(AU.embers(AU.IDLE_EMBERS), outline=False, under=True)
    return cv


def with_flare_aura(cv):
    body = set(cv.px)
    cv.stamp(AU.flames(AU.FLARE, grow(body, 1), AU.FLARE_ORDER), outline=False, under=True)
    cv.stamp(AU.embers(AU.FLARE_EMBERS), outline=False, under=True)
    return cv


def check():
    """None if the bodies here are the approved ones, else what differs."""
    errs = []
    a = with_idle_aura(idle())
    b = frame0.build()
    if a.px != b.px:
        errs.append('idle body + approved aura != frame0.build() (%d px differ)'
                    % len(set(a.px.items()) ^ set(b.px.items())))
    c = with_flare_aura(crossed())
    d = frame1.build()
    if c.px != d.px:
        errs.append('crossed body + approved aura != frame1.build() (%d px differ)'
                    % len(set(c.px.items()) ^ set(d.px.items())))
    return errs or None
