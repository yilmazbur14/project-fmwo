"""Render the poo pile as a real sphere-swept conical helix (orthographic, slightly
from above), shade by surface normal into a 4-tone ramp, auto-crease where the coil
passes in front of itself. Output = ASCII grids to freeze + hand-refine."""
import math
import sys
import fxpng

W = H = 32
PAL = {
    '.': None, 'K': '#000000',
    'a': '#3B1F1E',  # deep crease shadow
    'b': '#5C3326',  # shadow
    'c': '#7E4A2E',  # base
    'd': '#A0633A',  # light
    'e': '#C98A4E',  # highlight
    'f': '#EDC08A',  # wet glint
}


def render(swell=0.0, phi_deg=32, turns=2.55, R0=8.6, r0=4.6, rise=5.1, cx=15.5, base_sy=28.4,
           light=(-0.55, 0.70, 0.46), bands=(0.13, 0.30, 0.34), tip_flick=(1.6, 3.2)):
    phi = math.radians(phi_deg)
    L = light
    ln = math.sqrt(sum(v * v for v in L))
    L = tuple(v / ln for v in L)
    R0s = R0 + 0.55 * swell
    r0s = r0 + 0.25 * swell
    rises = rise + 0.25 * swell
    N = 900
    spheres = []
    for i in range(N + 1):
        u = i / N  # 0..1 along the coil
        t = u * turns
        th = math.pi / 2 + 2 * math.pi * t  # start at the back
        R = R0s * (1 - u) ** 0.85
        r = r0s * (1 - 0.72 * u)
        z = rises * t + (r0s - r)  # keep coil resting on the coil below
        X = R * math.cos(th)
        Y = R * math.sin(th)
        spheres.append((X, Y, z, r, u))
    # little upward flick at the end: the tip
    X, Y, z, r, u = spheres[-1]
    fx, fz = tip_flick
    for j in range(1, 40):
        v = j / 39
        spheres.append((X + fx * v * v, Y, z + fz * v, r * (1 - 0.75 * v), 1.0 + 0.2 * v))
    # project
    proj = []
    for (X, Y, Z, r, u) in spheres:
        su = Y * math.sin(phi) + Z * math.cos(phi)
        dep = Y * math.cos(phi) - Z * math.sin(phi)
        proj.append((X, su, dep, r, u))
    # screen offset: put the lowest ground point at base_sy
    min_su = min(su - r for (X, su, dep, r, u) in proj)
    zbuf = {}
    SS = 1  # one sample per pixel centre
    for (X, su, dep, r, u) in proj:
        for py in range(H):
            for px in range(W):
                sx = px + 0.5 - cx
                sy_up = (base_sy - (py + 0.5)) + min_su  # screen-up coordinate in world units
                dx, du = sx - X, sy_up - su
                q = r * r - dx * dx - du * du
                if q < 0:
                    continue
                s = math.sqrt(q)
                d = dep - s
                if (px, py) not in zbuf or d < zbuf[(px, py)][0]:
                    n = (dx / r, du / r, s / r)
                    zbuf[(px, py)] = (d, u, n)
    # flatten the bottom: nothing below the ground line
    ground_py = int(base_sy)
    for k in [k for k in zbuf if k[1] > ground_py]:
        del zbuf[k]
    # shading bands per coil so each loop gets a full ramp
    vals = {}
    for k, (d, u, n) in zbuf.items():
        lv = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
        vals[k] = lv
    s = sorted(vals.values())
    th = []
    acc = 0
    for f in bands:
        acc += f
        th.append(s[min(len(s) - 1, int(len(s) * (1 - acc)))])
    grid = [['.'] * W for _ in range(H)]
    for (px, py), lv in vals.items():
        grid[py][px] = 'e' if lv > th[0] else 'd' if lv > th[1] else 'c' if lv > th[2] else 'b'
    # creases: neighbour belongs to a coil segment far away along the tube and is in front
    for (px, py), (d, u, n) in zbuf.items():
        for dx, dy in ((0, -1), (1, 0), (-1, 0), (0, 1)):
            nb = zbuf.get((px + dx, py + dy))
            if nb is None:
                continue
            if abs(nb[1] - u) > 0.18 and nb[0] < d - 0.5:
                grid[py][px] = 'K'
                break
    # silhouette outline
    for (px, py) in zbuf:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (px + dx, py + dy) not in zbuf:
                grid[py][px] = 'K'
                break
    return grid


def to_px(grids, pal=PAL):
    out = [[(0, 0, 0, 0)] * (W * len(grids)) for _ in range(H)]
    for f, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                c = pal.get(g[y][x])
                if c:
                    out[y][f * W + x] = fxpng.hexc(c)
    return out


if __name__ == '__main__':
    variants = [
        dict(),
        dict(phi_deg=25),
        dict(phi_deg=38),
        dict(turns=2.3, rise=5.8),
    ]
    grids = []
    for v in variants:
        g = render(**v)
        grids.append(g)
        print(v)
        for row in g:
            print(''.join(row))
    px = to_px(grids)
    fxpng.write_png('coil_variants.png', W * len(grids), H, px)
    W8, H8, o = fxpng.view(W * len(grids), H, px, 8, grid=(32, 32))
    fxpng.write_png('coil_variants_8x.png', W8, H8, o)
