import sys, os, math
from pngio import *

C = {
    '.': (0, 0, 0, 0),
    'O': (66, 10, 20, 255),
    'D': (130, 25, 25, 255),
    'R': (172, 50, 50, 255),
    'P': (212, 150, 156, 255),
    'L': (248, 212, 216, 255),
    'W': (255, 255, 255, 255),
}
BW, BH = 16, 23
BASE = "ODRRRPPPLLWWWLLPPPRRRDO"
STREAKS = [
    (1, 3, 2, 'R'), (3, 9, 4, 'P'), (4, 1, 2, 'P'), (6, 5, 5, 'L'), (7, 13, 2, 'L'),
    (9, 0, 4, 'W'), (9, 10, 2, 'W'), (13, 6, 5, 'W'), (15, 12, 3, 'L'), (16, 2, 4, 'L'),
    (18, 8, 2, 'P'), (19, 13, 4, 'P'), (21, 11, 2, 'R'),
]

def beam_frame(mirror_shift):
    rows = [[C[BASE[y]] for _ in range(BW)] for y in range(BH)]
    for row, x0, n, col in STREAKS:
        if mirror_shift:
            row, x0 = BH - 1 - row, x0 + 8
        for i in range(n):
            rows[row][(x0 + i) % BW] = C[col]
    return rows

FS = 35
def flare_frame(b):
    c = FS // 2
    rings = [(4.6, 'W'), (7.6, 'L'), (10.1, 'P'), (11.6, 'R'), (12.6, 'D'), (13.6, 'O')] if b else \
            [(3.6, 'W'), (6.6, 'L'), (9.6, 'P'), (11.6, 'R'), (12.6, 'D'), (13.6, 'O')]
    rows = [[C['.'] for _ in range(FS)] for _ in range(FS)]
    for y in range(FS):
        for x in range(FS):
            d = math.hypot(x - c, y - c)
            for r, col in rings:
                if d <= r:
                    rows[y][x] = C[col]
                    break
    ray = [(14, 'L'), (15, 'P'), (16, 'R')]
    if not b:
        for k, col in ray:
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                rows[c + dy][c + dx] = C[col]
    else:
        for k, col in ((10, 'L'), (11, 'P'), (12, 'R')):
            for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                rows[c + sy * k][c + sx * k] = C[col]
        for dx, dy in ((14, 0), (-14, 0), (0, 14), (0, -14)):
            rows[c + dy][c + dx] = C['P']
    return rows

AIM = [
    "OOOOOOOO....",
    "RRRRRRPL....",
    "RPPPPLWW....",
    "RRRRRRPL....",
    "OOOOOOOO....",
]

def build(out_dir):
    beam = beam_frame(False) + beam_frame(True)
    write_png(os.path.join(out_dir, "computah_laser_beam.png"), BW, BH * 2, beam)
    fa, fb = flare_frame(False), flare_frame(True)
    write_png(os.path.join(out_dir, "computah_laser_fx.png"), FS * 2, FS, [fa[y] + fb[y] for y in range(FS)])
    aim = [[C[ch] for ch in line] for line in AIM]
    write_png(os.path.join(out_dir, "computah_laser_aim.png"), 12, 5, aim)
    return beam, fa, fb, aim

if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    build(sys.argv[1])
