"""victory_confetti: 4-frame looping confetti overlay, 640x360 per frame (horizontal strip).
Seamless without any code-side movement: pieces fall in periodic streams; each stream's spacing
P equals 4x its per-frame fall, so frame 4 == frame 0. Spin state and paper side depend only on
the piece's y, so the loop is exact. Transparent everywhere else (alpha 0/255 only).
python confetti.py outdir"""
import sys, math, random
from cv import *

W, H, F = 640, 360, 4
PAIRS = [(PINK, RED), (YEL, TAN), (LIME, GREEN), (SKY, BLURPLE), (ROSE, PURPLE), (CYAN, STEEL),
         (WHITE, GREY), (ORANGE, RUST)]


def shape(state, a, b):
    """list of (dx, dy, colour) for a spin state; a = lit side, b = shade."""
    if state == 0:
        return [(0, 0, a), (1, 0, a), (2, 0, a), (0, 1, b), (1, 1, b), (2, 1, b)]
    if state == 1:
        return [(0, 0, a), (1, 1, a), (1, 0, b), (2, 1, b)]
    if state == 2:
        return [(1, 0, b), (1, 1, b), (1, 2, b)]
    return [(2, 0, a), (1, 1, a), (1, 0, b), (0, 1, b)]


def build(seed=21, n_streams=34):
    random.seed(seed)
    streams = []
    for i in range(n_streams):
        dy = random.choice([7, 8, 9, 10])
        P = 4 * dy
        streams.append(dict(
            x0=random.randint(0, W - 1), dy=dy, P=P, phase=random.randint(0, P - 1),
            c1=random.choice(PAIRS), c2=random.choice(PAIRS),
            A=random.choice([0, 1, 2, 2, 3]), lam=random.choice([60, 90, 120]), phi=random.random() * 6.28,
            skip=random.randint(0, 5)))
    frames = []
    for f in range(F):
        cv = Canvas(W, H)
        for s in streams:
            for k in range(-4, H // s['P'] + 4):
                y = s['phase'] + k * s['P'] + f * s['dy']
                if y < -3 or y >= H:
                    continue                                 # clip, never wrap (keeps the loop exact)
                idx = (y - s['phase']) // s['P']
                if (idx + s['skip']) % 6 == 0:
                    continue                                 # gaps so streams don't read as dotted lines
                x = s['x0'] + int(round(s['A'] * math.sin(2 * math.pi * y / s['lam'] + s['phi'])))
                state = ((y - s['phase']) // s['dy']) % 4
                side = ((y - s['phase'] + 2 * s['dy']) // s['P']) % 2
                a, b = s['c1'] if side == 0 else s['c2']
                for (dx, dy2, c) in shape(state, a, b):
                    if 0 <= y + dy2 < H:
                        cv.set((x + dx) % W, y + dy2, c)
        frames.append(cv)
    return frames


def strip(frames):
    out = Canvas(W * len(frames), H)
    for i, fr in enumerate(frames):
        out.blit(fr, i * W, 0)
    return out


if __name__ == '__main__':
    od = sys.argv[1].rstrip('/') + '/'
    fr = build()
    # loop check: rebuild a 5th frame and compare with frame 0
    import copy
    F5 = F + 1
    globals()['F'] = F5
    fr5 = build()
    same = fr5[4].p == fr[0].p
    print('loop seamless (frame4 == frame0):', same)
    strip(fr).save(od + 'victory_confetti.png')
    print('ok')
