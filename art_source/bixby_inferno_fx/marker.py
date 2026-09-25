"""bixby_fireball_marker.png: where a falling fireball will land. 4 frames of 44x22 texels.

The oval fills the frame: it IS the landing's 132x66 px hit oval at 3x, centred on the spot (frame centre
(22, 11)). Mason's nugget-target contract (NuggetMeteorScript): frames 0 and 1 each hold a quarter of the
warning, then 2 and 3 flash at MARKER_FLASH_TIME (0.12 s).

Built the way nugget_target.png is: a black keyline, a fire rim lit from above (hotter on top, darker
underneath), and a shadowed interior, here in bixby_fire_scorch.png's charcoals so the marker already shows
the burn the ball will leave. A dark core and black keyline are what let it read over the flood's red
smoulder as well as over the green mat. The rim heats frame by frame; the inner shadow grows as the ball
nears; four ember ticks mark the aim.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from firelib import rings, put  # noqa: E402

W, H = 44, 22
CX, CY = 22.0, 11.0


def oval(rx, ry, cx=CX, cy=CY):
    return {(x, y) for y in range(H) for x in range(W)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0}


OUTER = oval(22.0, 11.0)

# Per frame: rim ring 1 (top half, bottom half), rim ring 2 (top, bottom), inner shadow size, centre, ticks.
FRAMES = [
    dict(r1=('N', 'n'), r2=('n', 'r'), shadow=0.46, core='r', tick='n'),
    dict(r1=('p', 'N'), r2=('N', 'n'), shadow=0.56, core='N', tick='N'),
    dict(r1=('Y', 'P'), r2=('P', 'p'), shadow=0.66, core='P', tick='P'),
    dict(r1=('P', 'N'), r2=('p', 'n'), shadow=0.66, core='p', tick='p'),
]


def frame(i):
    spec = FRAMES[i]
    g = [['.'] * W for _ in range(H)]
    depth = rings(OUTER)
    inner = oval(22.0 * spec['shadow'], 11.0 * spec['shadow'])
    inner_edge = {p for p, d in rings(inner).items() if d == 0}
    for (x, y), d in depth.items():
        top = y + 0.5 < CY
        if d == 0:
            k = 'k'
        elif d == 1:
            k = spec['r1'][0 if top else 1]
        elif d == 2:
            k = spec['r2'][0 if top else 1]
        elif (x, y) in inner_edge:
            k = 'c'
        elif (x, y) in inner:
            k = 'a' if i >= 1 else 'b'
        else:
            k = 'b' if i >= 1 else 'c'
        put(g, x, y, k)
    # the rim's sides are thin where the oval is steep; give the top a highlight run like the nugget's
    if i == 2:
        for x in range(15, 29):
            put(g, x, 1, 'W')
    # four ember ticks pointing in at the aim, and the centre
    tk = spec['tick']
    for (x, y) in ((21, 3), (22, 3), (21, 18), (22, 18), (5, 10), (5, 11), (38, 10), (38, 11)):
        put(g, x, y, tk)
    for (x, y) in ((21, 10), (22, 10), (21, 11), (22, 11)):
        put(g, x, y, spec['core'])
    return g


def frames():
    return [frame(i) for i in range(4)]
