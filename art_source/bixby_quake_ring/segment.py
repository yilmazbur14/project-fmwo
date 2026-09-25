"""Shades a quake-ring row's ground (ground.py) into palette keys, and lays the moving crest on it."""
import numpy as np

import ground as G

# light for the chunk tops: from the upper left, a little from the camera's side
LIGHT = np.array([-0.55, 0.35, 0.76])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def chunk_normal(gr, cid):
    side = -1 if cid < 100 else 1
    j = cid if cid < 100 else cid - 100
    z0, gd, gt = gr.planes[side][j]
    gx = gt * gr.u[0] + gd * side * gr.n[0]
    gy = gt * gr.u[1] + gd * side * gr.n[1]
    nrm = np.array([-gx, -gy, 1.0])
    return nrm / np.linalg.norm(nrm)


def shade(gr, hit, cw_, ch_, frame=0):
    """Palette keys for a marched ground (hit = Ground.march output)."""
    grid = [['.'] * cw_ for _ in range(ch_)]
    cidg = np.full((ch_, cw_), -2)
    t_hit = gr.T[hit["it"], hit["iv"]]
    heat_map = gr.heat(t_hit, frame)          # the magma's, pulsing
    still_map = gr.heat(t_hit)                 # the lit faces', holding still
    for r in range(ch_):
        for c in range(cw_):
            m = hit['mat'][r, c]
            it, iv = hit['it'][r, c], hit['iv'][r, c]
            if m == G.UNOWNED and gr.UNDER[it, iv] == G.CHUNK and not hit['wall'][r, c]:
                cidg[r, c] = gr.CID[it, iv]              # a neighbour draws it, but it is still that chunk
            if m in (G.CLEAR, G.UNOWNED):
                continue
            d = gr.D[it, iv]
            cw = gr.CW[it, iv]
            z = hit['z'][r, c]
            near_crack = d - cw
            hot = heat_map[r, c]
            if m == G.MAGMA:
                heat = (1.0 - d / cw) * 0.4 + hot * 0.8 - 0.25
                k = 'W' if heat > 0.8 else 'Y' if heat > 0.6 else 'P' if heat > 0.45 else 'p' if heat > 0.32 else 'N' if heat > 0.18 else 'n'
            elif hit['wall'][r, c]:
                if near_crack < 1.0:
                    above = (z - G.MAGMA_Z) / (0.3 + still_map[r, c])
                    k = 'N' if above < 0.5 else 'n' if above < 1.1 else 'r' if above < 1.8 else '1'
                elif near_crack < 3.0:
                    k = 'r'
                else:
                    k = '1'
            elif m == G.EARTH:
                k = 'n' if near_crack < 2.0 else 'r' if near_crack < 4.5 else '0'
            else:
                cid = gr.CID[it, iv]
                cidg[r, c] = cid
                lam = float(chunk_normal(gr, cid) @ LIGHT)
                k = '4' if lam > 0.86 else '3' if lam > 0.7 else '2' if lam > 0.5 else '1'
                if near_crack < 1.0:
                    k = 'N' if z > 0.3 else 'n'
                elif near_crack < 2.0 and z > 1.5:
                    k = 'n' if k in '12' else k
            grid[r][c] = k
    # Lone texels sticking off the band's ragged edge go. Isolation is judged on the continuous ring (ground
    # drawn here or by a neighbour counts as ground), so every segment makes the same call and none opens a gap.
    solid = hit['mat'] != G.CLEAR
    for r in range(1, ch_ - 1):
        for c in range(1, cw_ - 1):
            if grid[r][c] == '.':
                continue
            n = int(solid[r - 1, c]) + int(solid[r + 1, c]) + int(solid[r, c - 1]) + int(solid[r, c + 1])
            if n <= 1:
                grid[r][c] = '.'
    # a chunk's top edge catches the light: one step up the ramp where the texel above isn't the same chunk
    up = {'1': '2', '2': '3', '3': '4', '4': '4'}
    for r in range(1, ch_):
        for c in range(cw_):
            if grid[r][c] != '.' and cidg[r, c] >= 0 and cidg[r - 1, c] != cidg[r, c] and grid[r][c] in up:
                grid[r][c] = up[grid[r][c]]
    return grid, cidg
