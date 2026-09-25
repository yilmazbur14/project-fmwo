"""The crest with its light turned: the rig's own hair builder (matt.hair, by way of mi_hair.hair's
per-spike tilt), copied line for line with the two light directions it hard-codes made parameters.

A body that is about to be turned theta clockwise is built with its light turned -theta, so once
it is turned every spike and the dome are lit from the frame's upper left, as the cast is. At
theta 0 this is pixel for pixel the rig's hair (checked in _selftest).

`bend` per spike is the rig's own parameter; `trail` adds the same sideways bow to all five in the
same rotational sense, so a spinning crest drags behind the spin.
"""
import mj_base as J
from mj_base import matt
from shapes import tuft_frames
from lib import poly


def spike_specs(spikes, tilt=0.0, trail=0.0):
    """(base, tip, w0, w1, bend) for the five spikes, back to front, as matt.spike_specs() lays
    them out, each turned by `tilt` degrees. `trail` bows every spike the same rotational way
    (positive: the tips lag a clockwise spin)."""
    out = []
    centre, inner, outer = spikes
    for (ang, r0, r1, w0, w1, bend) in (outer, inner):
        for sgn in (1, -1):
            base, tip = matt.radial(48, 30, ang * sgn + tilt, r0, r1)
            out.append((base, tip, w0, w1, bend * sgn + trail))
    ang, r0, r1, w0, w1, bend = centre
    base, tip = matt.radial(48, 30, ang + tilt, r0, r1)
    out.append((base, tip, w0, w1, bend + trail))
    return out


def hair(spikes, tilt=0.0, theta=0.0, trail=0.0):
    """The dome and the five spikes as one part, lit for a body that will be turned theta."""
    sl = J.rot2(J.SPIKE_LIGHT, -theta)
    dl = J.rot2(J.DOME_LIGHT, -theta)
    dome = poly(matt.DOME)
    tufts = [tuft_frames(base, tip, w0, w1, bend)
             for (base, tip, w0, w1, bend) in spike_specs(spikes, tilt, trail)]
    part = {}
    for (x, y) in dome:
        u = (x - 48) / 15.0
        v = (y - 22) / 7.0
        lit = u * dl[0] + v * dl[1]
        part[(x, y)] = 'j' if lit > 0.55 else ('h' if lit < -0.55 else 'i')
    owner = {}
    for idx, (px, fr) in enumerate(tufts):
        for p in px:
            t, s, nx, ny = fr[p]
            t = min(1.0, t)
            lit = s * (nx * sl[0] + ny * sl[1])
            if t >= 0.64 - 0.06 * lit and p not in dome:
                k = 'c'
                if lit > 0.15:
                    k = 'b'
                if lit > 0.45 and t < 0.93:
                    k = 'a'
                if lit < -0.3:
                    k = 'd'
                if lit < -0.75:
                    k = 'e'
            else:
                k = 'i'
                if lit > 0.2:
                    k = 'j'
                if lit > 0.5 and 0.3 < t < 0.62:
                    k = 'l'
                if lit < -0.35:
                    k = 'h'
            part[p] = k
            owner[p] = idx
    for idx, (px, fr) in enumerate(tufts):
        for p in px:
            if owner.get(p) != idx:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in owner and owner[q] < idx and q not in dome:
                    part[p] = 'k' if fr[p][0] > 0.42 else 'h'
                    break
    return part


def _selftest():
    ok = True
    for roar in (False, True):
        P = matt.Pose(roar)
        a = matt.hair(P)
        b = hair(P.spikes)
        print('hair(theta 0) vs matt.hair, roar=%s:' % roar, 'identical' if a == b else 'DIFFERENT')
        ok &= a == b
    return ok


if __name__ == '__main__':
    _selftest()
