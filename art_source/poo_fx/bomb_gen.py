"""Poo bomb generator v2: 3D coil + specular glint + fuse + spark. Writes ASCII grids
(bomb_frames.txt) that get frozen and hand-refined."""
import math
import fxpng

W = H = 32
FLOOR = (136, 180, 99)

PAL = {
    '.': None, 'K': '#000000',
    'a': '#3B1F1E',  # deep shadow
    'b': '#5C3326',  # shadow
    'c': '#7E4A2E',  # base
    'd': '#A0633A',  # light
    'e': '#C98A4E',  # highlight
    'f': '#F0CC98',  # wet glint
    # fuse cord
    'g': '#F4EEDC',  # cord light
    'h': '#B5AA92',  # cord shadow
    'i': '#4A3A36',  # charred tip
    # spark
    'W': '#FFFFFF',
    'Y': '#FBF236',
    'O': '#DF7126',
    'R': '#AC3232',
}


def coil(swell=0.0, phi_deg=30, turns=3.2, R0=10.0, r0=4.0, rise=4.0, cx=15.5, base_sy=29.4,
         light=(-0.55, 0.85, 0.35), bands=(0.16, 0.30, 0.32), tip_flick=(2.0, 3.4),
         spec_k=18, spec_th=0.80, crease_du=0.18, end_taper=0.70, flick_taper=0.78, flick_pow=2.0):
    phi = math.radians(phi_deg)
    ln = math.sqrt(sum(v * v for v in light))
    L = tuple(v / ln for v in light)
    R0s, r0s, rises = R0 + 0.5 * swell, r0 + 0.22 * swell, rise + 0.22 * swell
    N = 1000
    sph = []
    for i in range(N + 1):
        u = i / N
        t = u * turns
        th = math.pi / 2 + 2 * math.pi * t
        R = R0s * (1 - u) ** 0.85
        r = r0s * (1 - end_taper * u)
        z = rises * t + (r0s - r)
        sph.append((R * math.cos(th), R * math.sin(th), z, r, u))
    X, Y, z, r, u = sph[-1]
    fx, fz = tip_flick
    for j in range(1, 50):
        v = j / 49
        sph.append((X + fx * v ** flick_pow, Y, z + fz * v, r * (1 - flick_taper * v), 1.0 + 0.2 * v))
    proj = [(X, Y * math.sin(phi) + Z * math.cos(phi), Y * math.cos(phi) - Z * math.sin(phi), r, u)
            for (X, Y, Z, r, u) in sph]
    min_su = min(su - r for (_, su, _, r, _) in proj)
    zb = {}
    for (X, su, dep, r, u) in proj:
        x0, x1 = int(cx + X - r - 1), int(cx + X + r + 2)
        for py in range(H):
            sy_up = (base_sy - (py + 0.5)) + min_su
            du = sy_up - su
            if abs(du) > r:
                continue
            for px in range(max(0, x0), min(W, x1)):
                dx = px + 0.5 - cx - X
                q = r * r - dx * dx - du * du
                if q < 0:
                    continue
                s = math.sqrt(q)
                d = dep - s
                if (px, py) not in zb or d < zb[(px, py)][0]:
                    zb[(px, py)] = (d, u, (dx / r, du / r, s / r))
    ground = int(base_sy)
    for k in [k for k in zb if k[1] > ground]:
        del zb[k]
    lum, spec = {}, {}
    for k, (d, u, n) in zb.items():
        nl = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
        lum[k] = nl
        rz = 2 * nl * n[2] - L[2]
        spec[k] = max(0.0, rz) ** spec_k
    s = sorted(lum.values())
    th, acc = [], 0
    for f in bands:
        acc += f
        th.append(s[min(len(s) - 1, int(len(s) * (1 - acc)))])
    g = [['.'] * W for _ in range(H)]
    for (px, py), v in lum.items():
        g[py][px] = 'e' if v > th[0] else 'd' if v > th[1] else 'c' if v > th[2] else 'b'
    smax = max(spec.values())
    for k, sv in spec.items():
        if sv > spec_th * smax:
            g[k[1]][k[0]] = 'f'
    for (px, py), (d, u, n) in zb.items():
        for dx, dy in ((0, -1), (1, 0), (-1, 0), (0, 1)):
            nb = zb.get((px + dx, py + dy))
            if nb is not None and abs(nb[1] - u) > crease_du and nb[0] < d - 0.5:
                g[py][px] = 'K'
                break
    for (px, py) in zb:
        if any((px + dx, py + dy) not in zb for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g[py][px] = 'K'
    return g, zb


def bbox(g):
    pts = [(x, y) for y in range(H) for x in range(W) if g[y][x] != '.']
    return (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))


def centred_coil(**kw):
    g, zb = coil(**kw)
    x0, x1, _, _ = bbox(g)
    mid = (x0 + x1 + 1) / 2.0
    kw = dict(kw)
    kw['cx'] = kw.get('cx', 15.5) + (16.0 - mid)
    return coil(**kw)


def to_px(grids, pal=PAL, fw=W, fh=H):
    out = [[(0, 0, 0, 0)] * (fw * len(grids)) for _ in range(fh)]
    for f, g in enumerate(grids):
        for y in range(fh):
            for x in range(fw):
                c = pal.get(g[y][x])
                if c:
                    out[y][f * fw + x] = fxpng.hexc(c)
    return out


def dump(grids, path):
    with open(path, 'w') as fh:
        for i, g in enumerate(grids):
            fh.write('# frame %d\n' % i)
            for row in g:
                fh.write(''.join(row) + '\n')


if __name__ == '__main__':
    import sys
    grids = []
    for sw in (0.0, 1.0):
        g, zb = centred_coil(swell=sw)
        print('swell', sw, 'bbox', bbox(g))
        grids.append(g)
    dump(grids, 'bomb_coil_frames.txt')
    px = to_px(grids)
    fxpng.write_png('bomb_coil.png', 64, 32, px)
    a, b, o = fxpng.view(64, 32, px, 8, grid=(32, 32))
    fxpng.write_png('bomb_coil_8x.png', a, b, o)
    a, b, o = fxpng.view(64, 32, px, 3, bg=FLOOR)
    fxpng.write_png('bomb_coil_3x_floor.png', a, b, o)
    for g in grids:
        for row in g:
            print(''.join(row))
        print()
