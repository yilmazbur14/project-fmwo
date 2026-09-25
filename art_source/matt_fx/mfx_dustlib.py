"""Shared dust: puffs lit from the top left, in the dust ramp measured from the shipped Josh card plume."""
import math

RANK = {'.': 0, '5': 1, '4': 2, '3': 3, '2': 4, '1': 5}


def puff(g, cx, cy, r, fade=0):
    """A round puff: #FBF7EE where it's lit (upper left), #EDE4D6 body, #C7BBAB shade (lower right), a
    #948779 underside rim so it holds up on the mat. fade shifts it all a step darker as it thins."""
    H, W = len(g), len(g[0])
    ramp = ['1', '2', '3', '4', '5']
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if not (0 <= x < W and 0 <= y < H):
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            light = (-dx - dy) / max(1.0, r)                  # +1 toward the upper left
            if d > r - 1.0 and dy > r * 0.2:
                i = 3                                         # the underside rim
            elif light > 0.55:
                i = 0
            elif light > -0.35:
                i = 1
            else:
                i = 2
            k = ramp[min(4, i + fade)]
            if g[y][x] == '.' or RANK[k] > RANK[g[y][x]] or (i == 3 and g[y][x] in '45'):
                g[y][x] = k
