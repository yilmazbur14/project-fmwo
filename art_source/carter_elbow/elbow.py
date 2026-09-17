import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from puppet import *
import heads

FAR = -0.32


class Axis:
    """body axis frame: s along body (neck->hips), t across (neg = back/up side, pos = chest side)"""
    def __init__(self, nx, ny, ang_deg):
        a = math.radians(ang_deg)
        self.N = (nx, ny)
        self.u = (math.cos(a), -math.sin(a))
        self.n = (math.sin(a), math.cos(a))

    def __call__(self, s, t):
        return (self.N[0] + s * self.u[0] + t * self.n[0], self.N[1] + s * self.u[1] + t * self.n[1])

    def pts(self, st):
        return [self(s, t) for s, t in st]


TORSO_ST = [(-2, -4.5), (1, -8), (5, -10), (10, -10.5), (15, -9.5), (19, -8), (23, -7), (27, -8.3),
            (31, -8), (34, -3.5), (33.5, 2.5), (28, 6.5), (23, 7), (19, 7), (15, 8.2), (12, 10.2), (7, 10.8),
            (2, 9), (-2, 5.5), (-3, 0)]
TRUNKS_ST = [(22.0, -7.3), (27, -8.7), (31.3, -8.3), (34.4, -3.5), (33.9, 2.7), (28, 6.9), (22.0, 7.2)]


def bounds_check(g, name):
    H, W = len(g), len(g[0])
    for y in range(H):
        for x in (0, W - 1):
            if g[y][x] != '.':
                print('WARN', name, 'touches left/right edge at', x, y)
    for x in range(W):
        for y in (0, H - 1):
            if g[y][x] != '.':
                print('WARN', name, 'touches top/bottom edge at', x, y)


def dive(var=0):
    ax = Axis(19, 40, 38)
    P = []
    # far leg (behind) - trails higher
    if var == 0:
        fhip, fknee, fank, ftoe = ax(29, -3.5), ax(37, -5), ax(41, -6), ax(45, -6.5)
    else:
        fhip, fknee, fank, ftoe = ax(29, -3.5), ax(36.5, -6.5), ax(40, -8.5), ax(43.5, -10)
    P += [cap(*fhip, *fknee, 4.0, 3.6, group='farleg', bias=FAR),
          cap(*fknee, *fank, 3.6, 3.0, group='farleg', bias=FAR),
          cap(*fank, *ftoe, 3.8, 3.6, mat='boot', group='farleg')]
    # far arm raised (behind)
    fsh = ax(6, -8)
    fel = (15, 22) if var == 0 else (17, 21)
    ffi = (10, 15) if var == 0 else (13, 12)
    P += [cap(*fsh, *fel, 4.2, 3.3, group='fararm', bias=FAR),
          cap(*fel, *ffi, 3.3, 2.8, group='fararm', bias=FAR),
          ell(ffi[0], ffi[1], 3.4, 3.2, 0, group='fararm', bias=FAR)]
    # near thigh (under trunks)
    if var == 0:
        nhip, nknee, nank, ntoe = ax(30, 2.5), ax(37.5, 3), ax(41.5, 3.5), ax(45.5, 4)
    else:
        nhip, nknee, nank, ntoe = ax(30, 2.5), ax(37.5, 2.5), ax(41.5, 1), ax(45, -0.5)
    P += [cap(*nhip, *nknee, 4.2, 3.8, group='nearleg')]
    # torso + trunks
    P += [poly(ax.pts(TORSO_ST), rad=6.0, group='body'),
          poly(ax.pts(TRUNKS_ST), rad=4.5, mat='trunks', group='body', sep=None)]
    P += [cap(*nknee, *nank, 3.8, 3.2, group='nearleg'),
          cap(*nank, *ntoe, 4.0, 3.7, mat='boot', group='nearleg')]
    # near arm: forearm + fist tucked BEHIND upper arm so the upper arm is one clean spike
    nsh = ax(4, 5.5)
    nel = (25, 57)
    nfi = (32, 47)
    P += [cap(*nel, *nfi, 2.6, 2.8, group='nearFore', bias=-0.12),
          ell(nfi[0], nfi[1], 3.4, 3.2, 0, group='nearFore', bias=-0.12),
          ell(*ax(3, 5), 5.2, 4.5, -38, group='nearArm'),
          cap(*nsh, *nel, 4.2, 2.6, group='nearArm')]
    g, lab = render(P)
    hc = ax(-6.5, -5.5)
    stamp(g, int(round(hc[0])) - 9, int(round(hc[1])) - 8, heads.TQ_LEFT)
    bounds_check(g, 'dive%d' % var)
    return g


def impact():
    ax = Axis(20, 47, 5)
    sq = [(s * 1.04, t * 0.86) for s, t in TORSO_ST]
    sqt = [(s * 1.04, t * 0.86) for s, t in TRUNKS_ST]
    P = []
    # far leg whipped up (behind)
    fhip, fknee, fank, ftoe = ax(30, -3), ax(37, -7), ax(39, -14), ax(40, -18)
    P += [cap(*fhip, *fknee, 4.0, 3.6, group='farleg', bias=FAR),
          cap(*fknee, *fank, 3.6, 3.0, group='farleg', bias=FAR),
          cap(*fank, *ftoe, 3.8, 3.6, mat='boot', group='farleg')]
    # far arm flung up behind the back
    fsh = ax(7, -6)
    fel, ffi = (22, 30), (17, 24)
    P += [cap(*fsh, *fel, 4.2, 3.3, group='fararm', bias=FAR),
          cap(*fel, *ffi, 3.3, 2.8, group='fararm', bias=FAR),
          ell(ffi[0], ffi[1], 3.4, 3.2, 0, group='fararm', bias=FAR)]
    nhip, nknee, nank, ntoe = ax(31, 2), ax(39, -1), ax(43, -7), ax(45, -11)
    P += [cap(*nhip, *nknee, 4.2, 3.8, group='nearleg')]
    P += [poly(ax.pts(sq), rad=6.0, group='body'),
          poly(ax.pts(sqt), rad=4.5, mat='trunks', group='body', sep=None)]
    P += [cap(*nknee, *nank, 3.8, 3.2, group='nearleg'),
          cap(*nank, *ntoe, 4.0, 3.7, mat='boot', group='nearleg')]
    nsh = ax(5, 5)
    nel = (26, 60)
    nfi = (34, 55)
    P += [cap(*nel, *nfi, 2.6, 2.8, group='nearFore', bias=-0.12),
          ell(nfi[0], nfi[1], 3.4, 3.2, 0, group='nearFore', bias=-0.12),
          ell(*ax(4, 4.5), 5.6, 4.6, -5, group='nearArm'),
          cap(*nsh, *nel, 4.4, 2.8, group='nearArm')]
    g, lab = render(P)
    hc = ax(-6.5, -1)
    stamp(g, int(round(hc[0])) - 9, int(round(hc[1])) - 8, heads.TQ_LEFT_OUCH)
    bounds_check(g, 'impact')
    return g


def mirror_pts(pts):
    return pts + [(63 - x, y) for x, y in reversed(pts)]


def crouch():
    """front view launch crouch: wide squat, arms swung down/back, fists by the boots."""
    P = []
    torso = mirror_pts([(27, 31), (22, 33), (19, 35), (18, 39), (21, 43), (23, 46), (22, 52)])
    trunks = mirror_pts([(22.4, 45.5), (21.4, 53)])
    # legs (behind torso)
    for sgn in (-1, 1):
        cx = 31.5
        def X(dx):
            return cx + sgn * dx
        P += [cap(X(6), 50, X(15), 53, 4.4, 4.0, group='leg%d' % sgn),
              cap(X(15), 53, X(14), 58, 4.0, 3.4, group='leg%d' % sgn),
              poly([(X(10), 56.5), (X(19.5), 56.5), (X(19.5), 62.5), (X(10), 62.5)], rad=2.0, mat='boot', group='leg%d' % sgn)]
    P += [poly(torso, rad=6.0, group='body'),
          poly(trunks, rad=4.0, mat='trunks', group='body', sep=None)]
    for sgn in (-1, 1):
        cx = 31.5
        def X(dx):
            return cx + sgn * dx
        P += [ell(X(13), 37, 5.0, 4.8, 0, group='arm%d' % sgn),
              cap(X(13.5), 38, X(20), 47, 4.0, 3.2, group='arm%d' % sgn),
              cap(X(20), 47, X(24), 55, 3.2, 2.8, group='arm%d' % sgn),
              ell(X(25), 57, 3.4, 3.2, 0, group='arm%d' % sgn)]
    g, lab = render(P)
    stamp(g, 23, 16, heads.FRONT)
    bounds_check(g, 'crouch')
    return g


def rise():
    """front view airborne rising: image-left arm punching up, other arm pulled down, legs trailing."""
    P = []
    torso = mirror_pts([(27, 23), (22, 25), (19, 27), (18, 31), (21, 35), (23, 38), (23, 49)])
    trunks = mirror_pts([(23.4, 42), (22.8, 49.5)])
    # legs behind: image-left straight down pointed, image-right knee bent (boot tucked higher)
    P += [cap(27, 48, 26, 54, 4.2, 3.6, group='legL'),
          cap(26, 54, 25, 57, 3.6, 3.2, group='legL'),
          poly([(21, 55.5), (29.5, 55.5), (28.5, 62.5), (22, 62.5)], rad=2.0, mat='boot', group='legL'),
          cap(36, 48, 39, 53, 4.2, 3.6, group='legR', bias=-0.1),
          cap(39, 53, 40, 55, 3.6, 3.2, group='legR', bias=-0.1),
          poly([(35.5, 52.5), (44, 52.5), (43, 59.5), (36.5, 59.5)], rad=2.0, mat='boot', group='legR')]
    P += [poly(torso, rad=6.0, group='body'),
          poly(trunks, rad=4.0, mat='trunks', group='body', sep=None)]
    # image-left arm up
    P += [ell(18.5, 29, 5.0, 4.8, 0, group='armL'),
          cap(18, 28, 12, 18, 4.0, 3.2, group='armL'),
          cap(12, 18, 9, 9, 3.2, 2.8, group='armL'),
          ell(8.5, 6.5, 3.5, 3.4, 0, group='armL')]
    # image-right arm down, fist by hip
    P += [ell(44.5, 29, 5.0, 4.8, 0, group='armR'),
          cap(45, 30, 49, 39, 4.0, 3.2, group='armR'),
          cap(49, 39, 48, 47, 3.2, 2.8, group='armR'),
          ell(47.5, 49, 3.4, 3.2, 0, group='armR')]
    g, lab = render(P)
    stamp(g, 23, 7, heads.FRONT)
    bounds_check(g, 'rise')
    return g


def impact2(var=0):
    """hips up, chest slammed, legs whipped high, far arm slapping mat ahead"""
    ax = Axis(21, 45, 14)
    sq = [(s * 1.0, t * 0.95) for s, t in TORSO_ST]
    sqt = [(s * 1.0, t * 0.95) for s, t in TRUNKS_ST]
    P = []
    fhip, fknee, fank, ftoe = ax(29, -3), ax(34, -10), ax(34.5, -17), ax(34.5, -21)
    P += [cap(*fhip, *fknee, 4.0, 3.6, group='farleg', bias=FAR),
          cap(*fknee, *fank, 3.6, 3.0, group='farleg', bias=FAR),
          cap(*fank, *ftoe, 3.8, 3.6, mat='boot', group='farleg')]
    if var == 0:   # far arm slaps mat ahead of head
        fsh, fel, ffi = ax(5, -4), (12, 51), (6, 58)
    else:          # far arm flung back over the body
        fsh, fel, ffi = ax(7, -7), (30, 31), (38, 27)
    P += [cap(*fsh, *fel, 4.2, 3.3, group='fararm', bias=FAR),
          cap(*fel, *ffi, 3.3, 2.8, group='fararm', bias=FAR),
          ell(ffi[0], ffi[1], 3.4, 3.2, 0, group='fararm', bias=FAR)]
    nhip, nknee, nank, ntoe = ax(30, 2), ax(38, -2), ax(40, -9), ax(40.5, -14)
    P += [cap(*nhip, *nknee, 4.2, 3.8, group='nearleg')]
    P += [poly(ax.pts(sq), rad=6.0, group='body'),
          poly(ax.pts(sqt), rad=4.5, mat='trunks', group='body', sep=None)]
    P += [cap(*nknee, *nank, 3.8, 3.2, group='nearleg'),
          cap(*nank, *ntoe, 4.0, 3.7, mat='boot', group='nearleg')]
    nsh = ax(4, 5.5)
    nel = (27, 59)
    P += [ell(*ax(3.5, 4.5), 6.0, 4.6, -14, group='nearArm'),
          cap(*nsh, *nel, 4.6, 2.5, group='nearArm')]
    g, lab = render(P)
    hc = ax(-6.5, -0.5)
    stamp(g, int(round(hc[0])) - 9, int(round(hc[1])) - 8, heads.TQ_LEFT_OUCH)
    bounds_check(g, 'impact2_%d' % var)
    return g


def pushoff():
    """3/4-left sprinter push-off: crouched, near hand pushing the ground, far arm swung back."""
    ax = Axis(21, 31, -40)
    P = []
    # far leg: knee forward, boot planted behind
    P += [cap(*ax(29, -3), 39, 44, 4.0, 3.6, group='farleg', bias=FAR),
          cap(39, 44, 46, 56, 3.6, 3.0, group='farleg', bias=FAR),
          poly([(42, 55), (50, 55), (51, 61.5), (41, 61.5)], rad=2.0, mat='boot', group='farleg')]
    # far arm swung back / up behind
    P += [cap(*ax(6, -8), 38, 27, 4.2, 3.3, group='fararm', bias=FAR),
          cap(38, 27, 46, 30, 3.3, 2.8, group='fararm', bias=FAR),
          ell(48, 31, 3.4, 3.2, 0, group='fararm', bias=FAR)]
    # near thigh folded up under chest
    P += [cap(*ax(30, 2), 28, 46, 4.3, 3.9, group='nearleg')]
    P += [poly(ax.pts(TORSO_ST), rad=6.0, group='body'),
          poly(ax.pts(TRUNKS_ST), rad=4.5, mat='trunks', group='body', sep=None)]
    P += [cap(28, 46, 30, 56, 3.9, 3.3, group='nearleg'),
          poly([(22, 55), (33, 55), (33.5, 61.5), (21, 61.5)], rad=2.0, mat='boot', group='nearleg')]
    # near arm straight down pushing the ground ahead
    P += [ell(*ax(3, 5), 5.2, 4.5, 40, group='nearArm'),
          cap(*ax(4, 5.5), 15, 47, 4.2, 3.2, group='nearArm'),
          cap(15, 47, 12, 55, 3.2, 2.9, group='nearArm'),
          ell(11, 58, 3.6, 3.0, 0, group='nearArm')]
    g, lab = render(P)
    hc = ax(-6.5, -5)
    stamp(g, int(round(hc[0])) - 9, int(round(hc[1])) - 8, heads.TQ_LEFT)
    bounds_check(g, 'pushoff')
    return g


def takeoff():
    """3/4-left rising: body near vertical, far fist punching straight up, near arm back, knees tucked."""
    ax = Axis(25, 29, -76)
    P = []
    # far arm straight up (behind head)
    P += [cap(*ax(5, -7), 33, 13, 4.2, 3.3, group='fararm', bias=FAR),
          cap(33, 13, 33, 6, 3.3, 3.0, group='fararm', bias=FAR),
          ell(33, 4.5, 3.5, 3.3, 0, group='fararm', bias=FAR)]
    # far leg tucked back
    P += [cap(*ax(29, -3), 40, 55, 4.0, 3.6, group='farleg', bias=FAR),
          cap(40, 55, 47, 50, 3.6, 3.0, group='farleg', bias=FAR),
          cap(47, 50, 52, 47, 3.8, 3.6, mat='boot', group='farleg')]
    P += [cap(*ax(30, 2), 33, 58, 4.3, 3.9, group='nearleg')]
    P += [poly(ax.pts(TORSO_ST), rad=6.0, group='body'),
          poly(ax.pts(TRUNKS_ST), rad=4.5, mat='trunks', group='body', sep=None)]
    P += [cap(33, 58, 42, 58, 3.9, 3.3, group='nearleg'),
          cap(42, 58, 48, 56, 4.0, 3.7, mat='boot', group='nearleg')]
    # near arm swept down/back along body
    P += [ell(*ax(3, 5), 5.2, 4.5, 76, group='nearArm'),
          cap(*ax(4, 5.5), 15, 38, 4.2, 3.2, group='nearArm'),
          cap(15, 38, 18, 46, 3.2, 2.9, group='nearArm'),
          ell(19, 48, 3.5, 3.3, 0, group='nearArm')]
    g, lab = render(P)
    hc = ax(-6, -3)
    stamp(g, int(round(hc[0])) - 9, int(round(hc[1])) - 8, heads.TQ_LEFT)
    bounds_check(g, 'takeoff')
    return g


def front_torso(neck, shoulder_top, armpit, trunks_top, trunks_bot):
    """Carter's idle torso outline (arms excluded), re-timed vertically. returns (torso_poly, trunks_poly)"""
    n, st, ap, tt, tb = neck, shoulder_top, armpit, trunks_top, trunks_bot
    left = [(28, n), (24, n + 1), (21, n + 2.5), (18.5, st - 1), (17, st + 0.5), (16.5, st + 3),
            (22.5, ap), (23.5, ap + 3), (24, tt - 1), (23, tt), (22.5, tb)]
    trunks_left = [(22.8, tt), (22.3, tb)]
    return mirror_pts(left), mirror_pts(trunks_left)


def squat(style='A'):
    P = []
    torso, trunks = front_torso(33, 36, 41, 47, 53.5)
    for sgn, grp in ((-1, 'legL'), (1, 'legR')):
        X = lambda dx: 31.5 + sgn * dx
        P += [cap(X(5.5), 51, X(16), 53, 4.6, 4.2, group=grp),
              cap(X(16), 53, X(15.5), 58, 4.2, 3.6, group=grp),
              poly([(X(10.5), 56.5), (X(20.5), 56.5), (X(20.5), 62.5), (X(10.5), 62.5)], rad=2.0, mat='boot', group=grp)]
    if style == 'A':
        for sgn, grp in ((-1, 'armL'), (1, 'armR')):
            X = lambda dx: 31.5 + sgn * dx
            P += [cap(X(19.5), 48, X(15), 53, 3.2, 2.9, group=grp + 'f', bias=-0.1),
                  ell(X(14.5), 54, 3.4, 3.2, 0, group=grp + 'f', bias=-0.1)]
    P += [poly(torso, rad=6.0, group='body'),
          poly(trunks, rad=4.0, mat='trunks', group='body', sep=None)]
    for sgn, grp in ((-1, 'armL'), (1, 'armR')):
        X = lambda dx: 31.5 + sgn * dx
        if style == 'A':   # arms swung down/back, fists behind knees
            P += [ell(X(13), 39.5, 5.2, 4.8, 0, group=grp),
                  cap(X(13.5), 40, X(19.5), 48, 4.2, 3.3, group=grp)]
        else:              # fists planted on the mat between the feet
            P += [ell(X(13), 39.5, 5.2, 4.8, 0, group=grp),
                  cap(X(13.5), 40, X(12), 49, 4.2, 3.3, group=grp),
                  cap(X(12), 49, X(6), 56, 3.3, 2.9, group=grp + 'f'),
                  ell(X(5.5), 59, 3.6, 3.2, 0, group=grp + 'f')]
    g, lab = render(P)
    stamp(g, 23, 17, heads.FRONT)
    bounds_check(g, 'squat' + style)
    return g


def superman():
    P = []
    torso, trunks = front_torso(25, 30, 36, 46, 53.5)
    # legs behind torso
    P += [cap(27, 52, 26.5, 56, 4.4, 3.9, group='legL'),
          poly([(21.5, 55.5), (30.5, 55.5), (29.5, 62.5), (22.5, 62.5)], rad=2.0, mat='boot', group='legL'),
          cap(36, 52, 38, 54, 4.4, 3.9, group='legR', bias=-0.1),
          poly([(34, 53.5), (43, 53.5), (42, 60), (35, 60)], rad=2.0, mat='boot', group='legR')]
    P += [poly(torso, rad=6.0, group='body'),
          poly(trunks, rad=4.0, mat='trunks', group='body', sep=None)]
    # image-left arm straight up
    P += [ell(18.5, 32, 5.2, 4.8, 0, group='armL'),
          cap(18, 31, 16, 19, 4.2, 3.4, group='armL'),
          cap(16, 19, 16, 10, 3.4, 3.0, group='armL'),
          ell(16, 6.5, 3.6, 3.4, 0, group='armL')]
    # image-right arm: flexed, fist clenched at hip
    P += [ell(44.5, 32, 5.2, 4.8, 0, group='armR'),
          cap(45, 32, 50.5, 41, 4.2, 3.4, group='armR'),
          cap(50.5, 41, 46.5, 48, 3.4, 3.0, group='armRf'),
          ell(45.5, 49.5, 3.6, 3.4, 0, group='armRf')]
    g, lab = render(P)
    stamp(g, 23, 9, heads.FRONT)
    bounds_check(g, 'superman')
    return g


def final_frames():
    return [dive(0), dive(1), impact2(0), squat('A'), superman()]


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'freeze':
    fr = final_frames()
    for i, g in enumerate(fr[:3]):
        with open(os.path.join(HERE, 'frame%d_base.txt' % i), 'w') as f:
            f.write(grid_to_text(g))
    write_strip(os.path.join(HERE, 'base_strip.png'), fr)
    print('frozen')
    sys.exit(0)

if __name__ == '__main__':
    frames = [dive(0), dive(1), impact(), crouch(), rise()] if len(sys.argv) < 2 else [impact2(0), squat('A'), squat('B'), superman(), rise()]
    write_strip(os.path.join(HERE, 'wip_elbow.png'), frames)
    for n, g in enumerate(frames):
        with open(os.path.join(HERE, 'wip_%s.txt' % n), 'w') as f:
            f.write(grid_to_text(g))
    print('ok')
