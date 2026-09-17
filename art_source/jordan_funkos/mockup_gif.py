"""Animated chase-scene GIF (4 s @ 15 fps): Jordan's pops spawn figures that sprint at the player,
one is punched away and blows up at a safe distance, one fuses and blows near its target.
Region x 560..1400, y 190..880 of the 1920x1080 arena (840x690) shown at 2x -> 1680x1380."""
import math
from build import figure_frames
from figures import FIGURES
from pop import pop_frames
from explosion import explosion_frames
from mockup import arena_base, load_jordan
from gifio import write_gif
from lib import *

FPS = 15
N = 60
RX0, RY0, RW, RH = 560, 190, 840, 690
Z = 2

FIGS = {f.name: figure_frames(f) for f in FIGURES}
POP = pop_frames()
EXP = explosion_frames()
JORDAN = load_jordan()
PUNCH = [player_frame(2, c) for c in (5, 6, 7, 8)]
IDLE = player_frame(2, 0)
BASE = arena_base()
REGION = [r[RX0:RX0 + RW] for r in BASE[RY0:RY0 + RH]]

PLAYER = (1080, 790)  # feet


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) ** 2


def draw(dst, img, sx, sy, s, anchor, flip=False):
    if flip:
        img = flip_h(img)
        anchor = (len(img[0]) - anchor[0], anchor[1])
    blit_scaled(dst, img, int(round(sx - anchor[0] * s)) - RX0, int(round(sy - anchor[1] * s)) - RY0, s)


def runner(name, spawn_t, start, end, run_time, fuse_t=None, boom_t=None, punched_t=None, punch_to=None,
           punch_boom_t=None):
    """returns function(t) -> list of (sorty, drawfn)"""
    fr = FIGS[name]

    def at(t):
        out = []
        if t < spawn_t:
            return out
        # spawn pop plays for 4 frames from spawn_t
        pf = int((t - spawn_t) * FPS)
        if pf < 4:
            out.append((start[1] - 1, lambda d, pf=pf: draw(d, POP[pf], start[0], start[1] - 21 + 14, 3, (16, 17))))
        if pf < 2:
            return out
        # explosion states
        if punched_t is not None and t >= punched_t:
            if punch_boom_t is not None and t >= punch_boom_t:
                ef = int((t - punch_boom_t) * FPS)
                if ef < 6:
                    out.append((punch_to[1] + 40, lambda d, ef=ef: draw(d, EXP[ef], punch_to[0], punch_to[1] - 7, 3,
                                                                        (32, 32))))
                return out
            # tumble along an arc away from the player
            k = min(1.0, (t - punched_t) / 0.55)
            e = ease_out(k)
            hit = pos_at(t=punched_t)
            x = lerp(hit[0], punch_to[0], e)
            y = lerp(hit[1], punch_to[1], e) - math.sin(k * math.pi) * 38
            fi = 6 + (int((t - punched_t) * FPS) % 2)
            if k >= 1.0:
                # landed: fuse flashing while it waits to blow
                fi = 4 + (int(t * FPS) % 2)
                out.append((y, lambda d, fi=fi, x=x, y=y: draw(d, fr[fi], x, y, 3, (12, 21))))
            else:
                out.append((y, lambda d, fi=fi, x=x, y=y: draw(d, fr[fi], x, y - 21 + 14, 3, (12, 14))))
            return out
        if boom_t is not None and t >= boom_t:
            ef = int((t - boom_t) * FPS)
            p = pos_at(boom_t)
            if ef < 6:
                out.append((p[1] + 40, lambda d, ef=ef, p=p: draw(d, EXP[ef], p[0], p[1] - 7, 3, (32, 32))))
            return out
        p = pos_at(t)
        flip = end[0] < start[0]
        if fuse_t is not None and t >= fuse_t:
            fi = 4 + (int(t * FPS * 1.5) % 2)
        else:
            fi = int(t * FPS) % 4
        out.append((p[1], lambda d, fi=fi, p=p, flip=flip: draw(d, fr[fi], p[0], p[1], 3, (12, 21), flip)))
        return out

    def pos_at(t):
        t0 = spawn_t + 2.0 / FPS
        stop_t = fuse_t if fuse_t is not None else (punched_t if punched_t is not None else 99)
        tt = min(t, stop_t)
        k = max(0.0, min(1.0, (tt - t0) / run_time))
        return (lerp(start[0], end[0], k), lerp(start[1], end[1], k))

    return at


ACTORS = [
    runner('gamer', 0.00, (1000, 470), (1052, 776), 1.15, punched_t=1.28, punch_to=(760, 700), punch_boom_t=2.30),
    runner('plumber', 0.10, (820, 455), (1010, 812), 2.3),
    runner('hedgehog', 0.25, (1120, 460), (1150, 760), 2.2),
    runner('mascot', 0.45, (900, 505), (975, 850), 1.6, fuse_t=2.05, boom_t=2.75),
    runner('hedgehog', 0.70, (1300, 540), (1165, 820), 2.0),
]


def player_items(t):
    # punch at 1.08..1.35
    if 1.08 <= t < 1.36:
        idx = min(3, int((t - 1.08) * FPS))
        img = PUNCH[idx]
    else:
        img = IDLE
    return [(PLAYER[1], lambda d, img=img: draw(d, img, PLAYER[0], PLAYER[1], 2, (16, 29)))]


def render(t):
    dst = [list(r) for r in REGION]
    items = [(400, lambda d: draw(d, JORDAN, 960, 400, 3, (32, 64)))]
    for a in ACTORS:
        items += a(t)
    items += player_items(t)
    for _, fn in sorted(items, key=lambda it: it[0]):
        fn(dst)
    return dst


if __name__ == '__main__':
    import time
    t0 = time.time()
    frames = []
    for i in range(N):
        frames.append(zoom(render(i / FPS), Z, None))
    print('rendered', time.time() - t0)
    save(frames[5], WIP + 'gif_frame05.png')
    save(frames[36], WIP + 'gif_frame36.png')
    n = write_gif(PREVIEW + 'jordan_funkos_chase_scene.gif', frames, [7] * N)
    print('gif bytes', n, time.time() - t0)
