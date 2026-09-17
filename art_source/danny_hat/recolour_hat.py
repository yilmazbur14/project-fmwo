"""Recolour Danny's beanie from white/grey to light blue/blue in every file that shows it.

The hat is isolated by ENCLOSURE, not by colour: inside a window around the hat, everything reachable from the
window border without crossing black ink is "outside" (background, floor, his face).  What is left, sealed
inside the hat's black outline, is the hat - including ink-separated ribbing segments in the hand-drawn art and
shadow pixels that happen to share the floor's grey.  Identical colours anywhere else (the paper, the ARENA
banners, the concrete) are therefore never touched.

Shading structure is preserved; each old tone maps to the same rung of a DB32 blue ramp:

    ffffff (white)       -> cbdbfc  ice / light blue
    cbdbfc (light rim)   -> 639bff  sky
    9badb7 (grey stripe) -> 5b6ee1  blurple (the UI blurple the menu and mascot use)
    847e87 (grey shadow) -> 3f3f74  indigo
    696a6a (deepest)     -> 222034  navy

Run:  python recolour_hat.py [--write]
Without --write it only reports what it would change.
"""
import os
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(SRC, '..', 'le_src')))
from pngio import read_png, write_png

DANNY = os.environ.get('DANNY_DIR', 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Danny')
BLACK = '000000'

MAP = {
    'ffffff': 'cbdbfc',
    'cbdbfc': '639bff',
    '9badb7': '5b6ee1',
    '847e87': '3f3f74',
    '696a6a': '222034',
}

# window around the hat: its border must lie in background / face, never inside the hat
FILES = [
    dict(name='danny.png', box=(20, 0, 124, 24)),            # two 64x64 frames, both hats
    dict(name='portrait.png', box=(8, 2, 56, 32)),
    dict(name='DannyDialogue.png', box=(26, 0, 52, 14)),
    dict(name='DannyIntro_pixel.png', box=(256, 30, 368, 96)),
    dict(name='DannyIntro.png', box=(850, 85, 1100, 245)),
]


def key(p):
    return '%02x%02x%02x' % tuple(p[:3])


def hex2rgba(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def enclosed(px, box):
    """pixels inside box that are sealed off from the box border by black ink"""
    x0, y0, x1, y1 = box
    outside = set()
    stack = []
    for x in range(x0, x1):
        stack += [(x, y0), (x, y1 - 1)]
    for y in range(y0, y1):
        stack += [(x0, y), (x1 - 1, y)]
    while stack:
        x, y = stack.pop()
        if (x, y) in outside or not (x0 <= x < x1 and y0 <= y < y1):
            continue
        p = px[y][x]
        if p[3] and key(p) == BLACK:
            continue
        outside.add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((x + dx, y + dy))
    inside = set()
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = px[y][x]
            if (x, y) not in outside and p[3] and key(p) != BLACK:
                inside.add((x, y))
    return inside


def run(write=False):
    total = 0
    for spec in FILES:
        path = os.path.join(DANNY, spec['name'])
        W, H, px = read_png(path)
        mask = enclosed(px, spec['box'])
        hist = {}
        for (x, y) in mask:
            k = key(px[y][x])
            hist[k] = hist.get(k, 0) + 1
        hat = {p for p in mask if key(px[p[1]][p[0]]) in MAP}
        xs = [p[0] for p in hat]
        ys = [p[1] for p in hat]
        elsewhere = {}
        for y in range(H):
            for x in range(W):
                p = px[y][x]
                if p[3] and key(p) in MAP and (x, y) not in hat:
                    elsewhere[key(p)] = elsewhere.get(key(p), 0) + 1
        print('%-22s %4dx%-4d hat px=%-5d bbox x %d..%d y %d..%d' % (spec['name'], W, H, len(hat), min(xs), max(xs), min(ys), max(ys)))
        print('   sealed inside the hat outline:', ', '.join('%s=%d' % kv for kv in sorted(hist.items(), key=lambda kv: -kv[1])))
        print('   same colours elsewhere (left alone):', ', '.join('%s=%d' % kv for kv in sorted(elsewhere.items(), key=lambda kv: -kv[1])) or 'none')
        if not write:
            continue
        out = [[tuple(p) for p in row] for row in px]
        for (x, y) in hat:
            out[y][x] = hex2rgba(MAP[key(px[y][x])])
        write_png(path, W, H, out)
        total += len(hat)
        print('   wrote %s (%d pixels recoloured)' % (spec['name'], len(hat)))
    if write:
        print('total recoloured:', total)


if __name__ == '__main__':
    run('--write' in sys.argv)
