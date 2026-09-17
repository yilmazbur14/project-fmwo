"""Build 96-space layers for a turned view (yaw 45/90/135/180, side +-1). yaw 0 returns the approved layers."""
import math
import lib
from lib import PALC, BLACK, TH_METAL, TH_SOFT, TH_CLOTH, hexc, RAMPS
import turn as T
from turn import View, render_part, Samples, norm, KAPPA

import rig as arig

RED = set(hexc(c) for c in RAMPS['red'])
CAPE_TH = [9.0, 0.95, 0.80, 0.55, 0.2]
HIP_R, HIP_RZ = 27.0, 16.0
PAUL_K = 0.12


def canvas():
    lib.W = lib.H = 96
    return lib.Canvas()


def approved(name):
    img = arig.layers()[name]
    return [[(p if p[3] else None) for p in row] for row in img]


def _interior(layer, x, y, r=1):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx, yy = x + dx, y + dy
            if not (0 <= xx < 96 and 0 <= yy < 96) or layer[yy][xx] is None:
                return False
    return True


# ------------------------------------------------------------------ decals
def cross_decal(cv, V):
    if V.yaw > 62:
        return
    w = T.interp(T.TORSO_W, 61.5)
    Z = T.ZF * w
    xc = 48 + V.side * Z * V.s
    Yl = 61.5 - KAPPA * Z
    yc = Yl + KAPPA * (Z * V.c)
    f = 0.62 if V.yaw else 1.0
    m = lib.empty()
    for y in range(96):
        for x in range(96):
            px, py = x + 0.5, y + 0.5
            vb = abs(px - xc) <= 3.0 * f + 0.01 and -7.5 <= py - yc <= 7.5
            hb = abs(px - xc) <= 10.0 * f + 0.01 and -4.5 <= py - yc <= 1.5
            if vb or hb:
                m[y][x] = True
    sx = 46.5 + V.side * 17 * V.s
    cv.part(m, 'red', ('sphere', sx, 53, 28.5, 25.5, 0.05), th=[0.95, 0.72, 0.42, -9, -9])


def roundel(cv, V, center3, axis, rdome):
    ax, ay, az = axis
    f = -ax * V.s + az * V.c
    if f < 0.3:
        return
    X = center3[0] + ax * rdome
    Y = center3[1]
    Z = center3[2] + az * rdome
    x, y, d = V.proj(X, Y, Z, PAUL_K)
    rx = 5.4 * max(0.45, f)
    disc = lib.ell(x, y, rx, 5.4)
    cv.part(disc, 'plate', ('sphere', x - 1, y - 1, rx + 0.6, 6), th=[0.99, 0.8, 0.45, 0.1, -9])
    cx, cy = int(math.floor(x)), int(math.floor(y))
    hw = max(1, int(round(3 * f)))
    for dy in range(-3, 3):
        for dx in (-1, 0):
            cv.set(cx + dx, cy + dy, 'X')
    for dx in range(-hw, hw):
        for dy in (-1, 0):
            cv.set(cx + dx, cy + dy, 'X')
    cv.set(cx - 1, cy - 3, 'x')
    cv.set(cx - hw, cy - 1, 'x')
    for px_, py_ in [(cx, cy + 2), (cx + hw - 1, cy), (cx, cy - 3), (cx, cy + 1)]:
        cv.set(px_, py_, 'y')


# ------------------------------------------------------------------ build
def build(yaw, side=1):
    V = View(yaw, side)
    L = {}
    if yaw == 0:
        for k, n in (('cape', 'cape'), ('legs', 'legs'), ('flap', 'flap'), ('tassets', 'tassets'), ('belt', 'belt'),
                     ('torso', 'torso'), ('buckle', 'buckle'), ('gorget', 'gorget'), ('paul_r', 'paulL'),
                     ('paul_l', 'paulR'), ('head', 'head')):
            L[k] = approved(n)
        return V, L
    tors = approved('torso')

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

    src = approved('buckle')
    cv = canvas()
    smp = T.plate_from_layer(V, src, R=HIP_R, Rz=20.0)
    for (x, y), (d, n, tex, tone) in smp.buf.items():
        if n[2] > 0.15:
            tx, ty = int(math.floor(tex[0])), int(math.floor(tex[1]))
            cv.px[y][x] = src[ty][tx]
    L['buckle'] = cv.px

    tas = approved('tassets')
    cv = canvas()
    for half in (0, 1):
        part = [[(p if ((x < 48) == (half == 0)) else None) for x, p in enumerate(row)] for row in tas]
        smp = T.tasset_wrap_samples(V, part)
        render_part(cv, smp, 'plate', TH_METAL, tex_layer=part,
                    tex_filter=lambda p, x, y, part=part: (p == BLACK and _interior(part, x, y, 1)) or p in (PALC['E'], PALC['W']))
    L['tassets'] = cv.px

    cv = canvas()
    smp = T.plate_from_layer(V, approved('flap'), flat_z=12.0)
    render_part(cv, smp, 'cape', TH_CLOTH)
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

    import legs as LG
    import headwarp as HWp
    L['legs'] = LG.legs_layer(yaw, side)
    cv = canvas()
    HWp.render(cv, yaw, side)
    L['head'] = cv.px
    return V, L


def order(yaw, side=1):
    """back-to-front layer order. 'paul_r' (his right, X<0) is the near shoulder for yaw in (0, 180)."""
    near, far = 'paul_r', 'paul_l'
    if yaw == 0:
        return ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', near, far, 'head']
    if yaw <= 60:
        return ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', far, near, 'head']
    if yaw <= 110:
        return ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'buckle', 'gorget', far, 'head', near]
    return ['flap', 'tassets', 'belt', 'torso', 'buckle', 'legs', 'gorget', 'cape', far, near, 'head']
