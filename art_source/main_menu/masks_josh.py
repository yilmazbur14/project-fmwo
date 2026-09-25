"""Josh's tower silhouette: the raw derivation his masks_clean.txt entry was hand-cleaned from.

The source is the approved 2026-09-23 redesign, Assets/Characters/Josh/josh_cards.png frame 0
(80x80, feet on row 79), sampled the way masks2.py / masks3.py did it: 4x4 supersamples per tower
pixel, a pixel is solid at 34% coverage, bottom-anchored so the ground line is exact.

SCALE 2.3. That is his previous entry's scale, recovered by fitting rather than guessed: sampling
the pre-redesign josh_idle.png frame 0 at 2.0-2.6 and scoring each against the old cleaned mask,
2.3 won (IoU 0.88; the next best, 2.4, scored 0.83). The redesign comes out 25x33 at that scale.

What the hand-clean did to this raw output (the same kind of pass the old entry got):
  - hat: flat 6-wide crown top, the card tucked on the near side kept as a pale 'o' tip,
    the band as a 'y' row the width of the crown, a 19-wide brim tapering by one pixel
    underneath
  - head squared to 10 wide; the popped collar steps one pixel out on each side at the jaw,
    with an 'R' inside each edge for its crimson face (on the edge itself it would sit against
    the red carpet and vanish)
  - the fan: the one-pixel gap between it and his coat (x27 in the sprite) opened down its full
    height, and pale 'o' card faces with the ace's red heart
  - the akimbo elbow kept as a one-pixel bulge; a one-pixel gap between the boots

    python masks_josh.py        # prints the raw mask
"""
from pngio import read_png

SRC = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Josh/josh_cards.png"
FRAME_W = 80
FACTOR = 2.3
THRESHOLD = 0.34
SS = 4


def raw_mask(frame=0):
    w, h, px = read_png(SRC)
    alpha = [[px[y][frame * FRAME_W + x][3] for x in range(FRAME_W)] for y in range(h)]
    xs = [x for y in range(h) for x in range(FRAME_W) if alpha[y][x]]
    ys = [y for y in range(h) for x in range(FRAME_W) if alpha[y][x]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    tw, th = int(round((x1 - x0) / FACTOR)), int(round((y1 - y0) / FACTOR))
    rows = []
    for ty in range(th):
        r = ''
        for tx in range(tw):
            hit = 0
            for sy in range(SS):
                for sx in range(SS):
                    X = int(x0 + (tx + (sx + 0.5) / SS) * FACTOR)
                    Y = int(y1 - (th - ty) * FACTOR + ((sy + 0.5) / SS) * FACTOR)
                    if 0 <= X < FRAME_W and 0 <= Y < h and alpha[Y][X]:
                        hit += 1
            r += '#' if hit / (SS * SS) >= THRESHOLD else '.'
        rows.append(r)
    return rows


if __name__ == '__main__':
    m = raw_mask()
    print('josh raw, %dx%d at %.1f' % (len(m[0]), len(m), FACTOR))
    print('\n'.join(m))
