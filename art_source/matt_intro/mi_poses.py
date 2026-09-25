"""Reusable pieces of Matt's intro poses: crest variants and arm poses.

Crest spikes are the rig's own spec, (angle, r_base, r_tip, w0, w1, bend) for the centre, inner and
outer pairs, angles in degrees from straight up (negative leans out to screen-left; the rig mirrors
the pair). Arms are mi_arms specs in frame coordinates. Left-arm points mirror to the right arm by
x' = 96 - x, but each arm is still built and lit on its own, so the light stays upper left.
"""
import mi_arms as A
import mi_hands as H

# ------------------------------------------------------------------ crests
SP_IDLE = [(0, 8, 27, 6.2, 1.9, 0.0), (-31, 8, 26, 6.2, 1.9, 1.5), (-66, 9, 27, 7.0, 2.2, 2.5)]
SP_ROAR = [(0, 8, 28, 6.4, 2.0, 0.0), (-37, 8, 30, 6.4, 2.0, 0.5), (-80, 9, 30, 7.2, 2.4, 1.0)]
# perked up: a touch taller and more upright (pleased with himself)
SP_PERK = [(0, 8, 28, 6.2, 1.9, 0.0), (-29, 8, 27, 6.2, 1.9, 1.0), (-62, 9, 28, 7.0, 2.2, 2.0)]
# wilting: shorter, the outer pair bowed down (nervous, sheepish)
SP_DROOP = [(0, 8, 26, 6.0, 1.9, 1.0), (-35, 8, 25, 6.0, 1.9, 3.0), (-73, 9, 26, 6.8, 2.1, 4.5)]
# bristling: longer than the roar's and dead straight (ENOUGH)
SP_BRISTLE = [(0, 8, 29, 6.4, 2.0, 0.0), (-39, 8, 31, 6.4, 2.0, 0.0), (-83, 9, 31, 7.2, 2.4, 0.3)]
# halfway to the roar's flare (irritated, shouting)
SP_TENSE = [(0, 8, 28, 6.3, 1.95, 0.0), (-34, 8, 28, 6.3, 1.95, 1.0), (-73, 9, 28, 7.1, 2.3, 1.8)]


def lerp_spikes(a, b, t):
    return [tuple(x + (y - x) * t for x, y in zip(p, q)) for p, q in zip(a, b)]


# ------------------------------------------------------------------ arms
def mx(p):
    return (96 - p[0], p[1])


def pair(dc, s0, elbow, wrist, hand_l, hand_r, **kw):
    """Both arms from the left arm's points; the right arm is the mirror, built and lit on its own."""
    left = A.bent(0, dc, s0, elbow, wrist, hand=hand_l, **kw)
    right = A.bent(1, mx(dc), mx(s0), mx(elbow), mx(wrist), hand=hand_r, **kw)
    return [left, right]


def one(side, dc, s0, elbow, wrist, hand, **kw):
    """One arm given in LEFT-arm coordinates; side 1 mirrors the points."""
    if side:
        dc, s0, elbow, wrist = mx(dc), mx(s0), mx(elbow), mx(wrist)
    return A.bent(side, dc, s0, elbow, wrist, hand=hand, **kw)


def hang_pair(**kw):
    return [A.hang(0, **kw), A.hang(1, **kw)]


# the idle's own geometry, for reference: deltoid (25, 57), s0 (24, 60), elbow (17.5, 65.5),
# wrist (18.5, 70); the fist hangs from 3 px below the wrist
IDLE_ARM = ((25, 57), (24, 60), (17.5, 65.5), (18.5, 70))
