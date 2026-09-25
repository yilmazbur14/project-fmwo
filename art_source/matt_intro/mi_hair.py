"""The crest with a tilt: the rig's own hair builder (matt.hair, copied here line for line, the rig is
never edited) with every spike turned about the crown by the same angle, so a head tilt tilts the
whole crest. The rig builds each side pair of spikes from one mirrored angle, which cannot express a
tilt; here each of the five gets its own. At tilt 0 this is pixel for pixel the rig's hair
(checked in _selftest).
"""
import mi_base as B
from mi_base import matt, poly
from shapes import tuft_frames


def spike_specs(spikes, tilt=0.0):
    """(base, tip, w0, w1, bend) for the five spikes, back to front, as matt.spike_specs() lays
    them out, each turned by `tilt` degrees (negative leans the crest toward screen-left)."""
    out = []
    centre, inner, outer = spikes
    for (ang, r0, r1, w0, w1, bend) in (outer, inner):
        for sgn in (1, -1):
            base, tip = matt.radial(48, 30, ang * sgn + tilt, r0, r1)
            out.append((base, tip, w0, w1, bend * sgn))
    ang, r0, r1, w0, w1, bend = centre
    base, tip = matt.radial(48, 30, ang + tilt, r0, r1)
    out.append((base, tip, w0, w1, bend))
    return out


def hair(spikes, tilt=0.0):
    dome = poly(matt.DOME)
    tufts = [tuft_frames(base, tip, w0, w1, bend) for (base, tip, w0, w1, bend) in spike_specs(spikes, tilt)]
    part = {}
    for (x, y) in dome:
        u = (x - 48) / 15.0
        v = (y - 22) / 7.0
        lit = -(u * 0.75 + v * 0.65)
        part[(x, y)] = 'j' if lit > 0.55 else ('h' if lit < -0.55 else 'i')
    owner = {}
    for idx, (px, fr) in enumerate(tufts):
        for p in px:
            t, s, nx, ny = fr[p]
            t = min(1.0, t)
            lit = s * (nx * matt.LIGHT[0] + ny * matt.LIGHT[1])
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
    for roar in (False, True):
        P = matt.Pose(roar)
        a = matt.hair(P)
        b = hair(P.spikes, 0.0)
        print('hair(tilt 0) vs matt.hair, roar=%s:' % roar, 'identical' if a == b else 'DIFFERENT')


if __name__ == '__main__':
    _selftest()
