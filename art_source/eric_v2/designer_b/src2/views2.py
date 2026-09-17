"""v2 turned body views (96-space layers at body scale S about the feet anchor (48, 96)).
The v1 3D samplers are reused unchanged; positions are scaled at splat time, so outlines stay 1 px and the
ramps/lighting are recomputed at the new size."""
import math
import lib
from lib import PALC, BLACK, TH_METAL, TH_SOFT, TH_CLOTH, hexc, RAMPS
import turn as T
from turn import View, render_part, norm, KAPPA

S = 0.80
CAPE_TH = [9.0, 0.95, 0.80, 0.55, 0.2]
HIP_R = 27.0
PAUL_K = 0.12


def sc(x, y):
    return (48 + (x - 48) * S, 96 + (y - 96) * S)


_BaseSamples = T.Samples


class ScaledSamples(_BaseSamples):
    def add(self, x, y, d, n, tex=None, tone=0):
        X, Y = sc(x, y)
        _BaseSamples.add(self, X, Y, d, n, tex, tone)


def install():
    T.Samples = ScaledSamples


def canvas():
    lib.W = lib.H = 96
    return lib.Canvas()


_V1 = {}


def v1_layers():
    """unscaled approved front layers (source textures for re-projection)"""
    if not _V1:
        import parts as P
        lib.W = lib.H = 96

        def lay(fn):
            cv = lib.Canvas()
            fn(cv)
            return cv.px
        _V1['torso'] = lay(lambda cv: P.torso_details(cv, P.torso(cv)))
        _V1['tassets'] = lay(lambda cv: (P.tassets(cv), P.tasset_details(cv)))
        _V1['buckle'] = lay(P.belt_details)
        _V1['flap'] = lay(P.flap)
    return _V1


def _interior(layer, x, y, r=1):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx, yy = x + dx, y + dy
            if not (0 <= xx < 96 and 0 <= yy < 96) or layer[yy][xx] is None:
                return False
    return True


def cross_decal(cv, V):
    if V.yaw > 62:
        return
    w = T.interp(T.TORSO_W, 61.5)
    Z = T.ZF * w
    xc = 48 + V.side * Z * V.s
    yc = 61.5 - KAPPA * Z + KAPPA * (Z * V.c)
    xc, yc = sc(xc, yc)
    f = 0.62 if V.yaw else 1.0
    m = lib.empty()
    for y in range(96):
        for x in range(96):
            px, py = x + 0.5, y + 0.5
            vb = abs(px - xc) <= 3.0 * S * f + 0.35 and -6.2 <= py - yc <= 6.0
            hb = abs(px - xc) <= 8.0 * f + 0.2 and -3.8 <= py - yc <= 1.2
            if vb or hb:
                m[y][x] = True
    X, Y = sc(46.5 + V.side * 17 * V.s, 53)
    cv.part(m, 'red', ('sphere', X, Y, 28.5 * S, 25.5 * S, 0.05), th=[0.95, 0.72, 0.42, -9, -9])


def roundel(cv, V, center3, axis, rdome):
    ax, ay, az = axis
    f = -ax * V.s + az * V.c
    if f < 0.3:
        return
    X = center3[0] + ax * rdome
    Z = center3[2] + az * rdome
    x, y, d = V.proj(X, center3[1], Z, PAUL_K)
    x, y = sc(x, y)
    r = 4.4
    rx = r * max(0.5, f)
    disc = lib.ell(x, y, rx, r)
    cv.part(disc, 'plate', ('sphere', x - 1, y - 1, rx + 0.6, r + 0.6), th=[0.99, 0.8, 0.45, 0.1, -9])
    cx, cy = int(math.floor(x)), int(math.floor(y))
    hw = max(1, int(round(2 * f)))
    for dy in range(-2, 3):
        cv.set(cx, cy + dy, 'X')
    for dx in range(-hw, hw + 1):
        cv.set(cx + dx, cy, 'X')
    cv.set(cx, cy - 2, 'x')
    cv.set(cx + 1 if hw > 1 else cx, cy + 1, 'y')


def build(yaw, side=1):
    install()
    V = View(yaw, side)
    L = {}
    src = v1_layers()
    tors = src['torso']

    cv = canvas()
    render_part(cv, T.cape_samples(V), 'cape', CAPE_TH, back_bias=1)
    L['cape'] = cv.px

    cv = canvas()
    render_part(cv, T.torso_samples(V), 'plate', TH_METAL, tex_layer=tors,
                tex_filter=lambda p, x, y: p == BLACK and _interior(tors, x, y, 2) and not (37 <= x <= 58 and 53 <= y <= 70))
    cross_decal(cv, V)
    L['torso'] = cv.px

    cv = canvas()
    render_part(cv, T.ring_band_samples(V, 26.0, 20.0, 69.0, 78.6, 63.6, 70.4, tex=False), 'leath', TH_SOFT)
    L['belt'] = cv.px

    b = src['buckle']
    cv = canvas()
    smp = T.plate_from_layer(V, b, R=HIP_R, Rz=20.0)
    for (x, y), (d, n, tex, tone) in smp.buf.items():
        if n[2] > 0.15:
            tx, ty = int(math.floor(tex[0])), int(math.floor(tex[1]))
            cv.px[y][x] = b[ty][tx]
    L['buckle'] = cv.px

    tas = src['tassets']
    cv = canvas()
    for half in (0, 1):
        part = [[(p if ((x < 48) == (half == 0)) else None) for x, p in enumerate(row)] for row in tas]
        smp = T.tasset_wrap_samples(V, part)
        render_part(cv, smp, 'plate', TH_METAL, tex_layer=part,
                    tex_filter=lambda p, x, y, part=part: (p == BLACK and _interior(part, x, y, 1)) or p in (PALC['E'], PALC['W']))
    L['tassets'] = cv.px

    cv = canvas()
    render_part(cv, T.plate_from_layer(V, src['flap'], flat_z=12.0), 'cape', TH_CLOTH)
    L['flap'] = cv.px

    cv = canvas()
    render_part(cv, T.ellipsoid_samples(V, 0, 37.5, 0, 15.8, 7.0, 11.0, tex=False), 'plate', TH_METAL, bias=1)
    L['gorget'] = cv.px

    for key, sgn in (('paul_r', -1), ('paul_l', 1)):
        cv = canvas()
        axis = norm((sgn * 0.6, 0.0, 0.8))
        for cx, cy, rx, ry, rz, roll in ((28.7, 54, 11.3, 5.6, 10, 18), (27.2, 49.2, 13, 6.6, 11, 15),
                                          (24.5, 41.3, 13.6, 10.6, 12, 12)):
            smp = T.ellipsoid_samples(V, sgn * cx, cy, 0, rx, ry, rz, roll=-sgn * roll, kappa=PAUL_K, tex=False,
                                      rim_axis=axis if rx == 13.6 else None)
            render_part(cv, smp, 'plate', TH_METAL)
        rdome = 1.0 / math.sqrt((axis[0] / 13.6) ** 2 + (axis[2] / 12.0) ** 2)
        roundel(cv, V, (sgn * 24.5, 40.8, 0.0), axis, rdome)
        L[key] = cv.px

    import legs2
    import head2
    L['legs'] = legs2.legs_layer(yaw, side)
    cv = canvas()
    head2.render(cv, yaw, side)
    L['head'] = cv.px
    return V, L


def order(yaw, side=1):
    near, far = 'paul_r', 'paul_l'
    if yaw <= 60:
        return ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', far, near, 'head']
    if yaw <= 110:
        return ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', far, 'head', near]
    return ['flap', 'tassets', 'belt', 'torso', 'buckle', 'legs', 'gorget', 'cape', far, near, 'head']
