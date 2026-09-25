"""Computah's cannon arm, worn by Greyson as a gauntlet over his LEFT forearm.

After the tear-off Greyson jams his forearm into the torn shoulder socket, the way Mega Man wears
his buster: the socket end sits at his elbow, the barrel runs down his forearm, and the muzzle is
where his fist would be. His upper arm stays flesh, so he can still flex the biceps under it.

The shape and colours are Computah's approved cannon (Assets/Characters/Computah/, and the torn
arm in art_source/computah_redesign/computah_arm.png): a rounded socket collar ringed with bolt
nubs, a narrower barrel with a lit stripe along it, a flared muzzle ring, and the dark slate bore
(#1A212C / #3C4757, Computah's own). Its purples are Greyson's trunk ramp (A-E), which is
Computah's paint. Its keyline is pure black: on Greyson it sits inside his keyline, not
Computah's #0C111A. The torn socket's sparking cable is left out; his forearm plugs the socket.

Generated along any axis, so every pose gets the same upper-left light instead of a rotated
picture carrying its old shading with it. The muzzle's face is an ellipse tilted toward the viewer
(`face` 0 = seen edge-on, 1 = straight down the barrel), so the bore's dark disc, the cannon's
signature, still shows when it points up or out.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
K = B.K

PURPLE = 'ABCDE'
CUTS = (0.80, 0.52, 0.20, -0.12)


def _profile(a, L, r_col, r_bar, r_muz, c1, m1):
    """Half-thickness at distance a along the axis. Computah's arm starts from a ball (his torn
    shoulder, the socket in its far side), then the barrel, swelling slightly, then the flared
    muzzle ring. The ball is centred c1 - 0.2 r_col along the axis and cut flat at the socket
    (a = 0), where Greyson's forearm goes in."""
    if a < 0:
        return None
    ac = c1 - 0.2 * r_col
    if a <= c1:
        d = a - ac
        rr = r_col * r_col - d * d
        return max(r_bar, math.sqrt(rr)) if rr > 0 else r_bar
    if a < m1:
        mid = (c1 + m1) / 2.0
        return r_bar + 0.5 * (1 - abs(a - mid) / ((m1 - c1) / 2.0))
    if a <= L:
        if a > L - 1.0:
            return r_muz - 0.3
        return r_muz
    return None


def cannon(p0, p1, r_col=8.0, r_bar=6.3, r_muz=7.6, c1=None, m1=None, face=0.45, bolts=4,
           stripe=True):
    """The cannon from the socket end p0 (at his elbow) to the muzzle end p1.
    Returns {pixel: key} with its own black separations; stamp it WITH an outline."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    c1 = 0.36 * L if c1 is None else c1
    m1 = L - 0.20 * L if m1 is None else m1
    rmax = max(r_col, r_bar, r_muz) + 2
    xs = range(int(min(x0, x1) - rmax - 2), int(max(x0, x1) + rmax + 3))
    ys = range(int(min(y0, y1) - rmax - 2), int(max(y0, y1) + rmax + 3))
    geo = {}
    for y in ys:
        for x in xs:
            dx, dy = x - x0, y - y0
            a = dx * ux + dy * uy
            s = dx * nx + dy * ny
            r = _profile(a, L, r_col, r_bar, r_muz, c1, m1)
            if r is None or abs(s) > r:
                continue
            geo[(x, y)] = (a, s, r)
    part = {}
    for (x, y), (a, s, r) in geo.items():
        q = max(-0.97, min(0.97, s / r))
        z = math.sqrt(1.0 - q * q)
        part[(x, y)] = K.tone(K.lambert((q * nx, q * ny, z)), PURPLE, CUTS)
    # the barrel's lit stripe, on the side nearest the light
    if stripe:
        lit = 1 if (nx * K.LIGHT3[0] + ny * K.LIGHT3[1]) > 0 else -1
        for (x, y), (a, s, r) in geo.items():
            if c1 + 1.5 < a < m1 - 1.5 and 0.28 <= lit * s / r <= 0.66:
                part[(x, y)] = 'A'
    # black separations: collar | barrel | muzzle ring
    for (x, y), (a, s, r) in geo.items():
        if abs(a - c1) < 0.5 or abs(a - m1) < 0.5:
            part[(x, y)] = 'k'
    # the muzzle's face: a tilted ellipse at the end, rim in purple, the bore dark inside it
    if face > 0:
        fr = r_muz + 0.2
        fb = max(1.0, fr * face)
        for y in ys:
            for x in xs:
                dx, dy = x - x1, y - y1
                a = dx * ux + dy * uy
                s = dx * nx + dy * ny
                e = (s / fr) ** 2 + (a / fb) ** 2
                if e > 1.0:
                    continue
                ei = (s / (fr - 1.7)) ** 2 + (a / max(0.6, fb - 1.2)) ** 2
                if ei <= 1.0:
                    # the bore: deep, with its lit lower lip
                    part[(x, y)] = 'Z' if (a < -0.2 * fb and ei > 0.45) else 'z'
                else:
                    q = max(-0.97, min(0.97, s / fr))
                    lit_rim = -a / fb
                    part[(x, y)] = K.tone(K.lambert((q * nx - ux * lit_rim, q * ny - uy * lit_rim,
                                                     0.6)), PURPLE, CUTS)
    K.despeckle(part, keys=PURPLE)       # clean the shading first; the bolts are single on purpose
    # bolt nubs round the socket's lip (Computah's torn socket is ringed with them): each a lit
    # knob with its shadow on the far side from the light
    for i in range(bolts):
        frac = (i + 0.5) / bolts
        ss = (-r_col + 2.0) + frac * (2 * r_col - 4.0)
        cx, cy = int(round(x0 + ux * 1.6 + nx * ss)), int(round(y0 + uy * 1.6 + ny * ss))
        if (cx, cy) in part and part[(cx, cy)] != 'k':
            part[(cx, cy)] = 'A'
            sh = (cx + (1 if K.LIGHT3[0] < 0 else -1), cy + (1 if K.LIGHT3[1] < 0 else -1))
            if sh in part and part[sh] not in ('k', 'A'):
                part[sh] = 'E'
    return part
