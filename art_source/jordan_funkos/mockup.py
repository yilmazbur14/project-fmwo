"""1920x1080 arena mockup: Jordan (3x) mid-summon with spawn pops, figures (3x) chasing the player (2x),
one flashing its fuse, one tumbling after a punch, one explosion. Built on a Godot movie-writer render of
Scenes/Core/ArenaScene.tscn (player node painted out and re-placed)."""
from build import figure_frames
from pop import pop_frames
from explosion import explosion_frames
from figures import FIGURES
import os
from lib import *

FLOOR = (136, 180, 99, 255)


def arena_base():
    if not os.path.exists(ARENA_FRAME):
        raise SystemExit('missing %s - render it first (see build.py docstring)' % ARENA_FRAME)
    w, h, px = read_png(ARENA_FRAME)
    px = [list(r) for r in px]
    for y in range(870, 932):
        for x in range(940, 980):
            px[y][x] = FLOOR
    return px


def sprite_at(dst, img, cx, cy, s, flip=False, anchor=None):
    """place img scaled by s so that texture point anchor (ax, ay) lands on screen (cx, cy)."""
    if flip:
        img = flip_h(img)
    w, h = size(img)
    ax, ay = anchor if anchor else (w / 2.0, h / 2.0)
    if flip and anchor:
        ax = w - ax
    ox = int(round(cx - ax * s))
    oy = int(round(cy - ay * s))
    blit_scaled(dst, img, ox, oy, s)


def load_jordan():
    w, h, px = read_png(PROJ + 'Assets/Characters/Jordan/jordan.png')
    return px


def build_scene(t=None):
    """returns list of (sort_y, draw_fn)."""
    figs = {f.name: figure_frames(f) for f in FIGURES}
    pop = pop_frames()
    exp = explosion_frames()
    jordan = load_jordan()
    player_punch = player_frame(2, 8)
    items = []
    # Jordan at 3x, feet at y=400
    items.append((400, lambda d: sprite_at(d, jordan, 960, 400, 3, anchor=(32, 64))))
    # spawn pops around Jordan (pop anchor = (16,17) on the figure body centre)
    items.append((452, lambda d: sprite_at(d, pop[1], 812, 440, 3, anchor=(16, 17))))
    items.append((452, lambda d: sprite_at(d, pop[2], 1118, 446, 3, anchor=(16, 17))))
    items.append((500, lambda d: sprite_at(d, pop[0], 915, 492, 3, anchor=(16, 17))))
    items.append((466, lambda d: sprite_at(d, figs['mascot'][1], 1118, 467, 3, flip=True, anchor=(12, 21))))
    # player punching left, feet at (1080, 790)
    items.append((790, lambda d: sprite_at(d, player_punch, 1080, 790, 2, anchor=(16, 29))))
    # chasers converging on the player (feet anchor (12,21))
    items.append((690, lambda d: sprite_at(d, figs['plumber'][0], 880, 690, 3, anchor=(12, 21))))
    items.append((676, lambda d: sprite_at(d, figs['hedgehog'][1], 1235, 676, 3, flip=True, anchor=(12, 21))))
    items.append((818, lambda d: sprite_at(d, figs['hedgehog'][2], 1330, 818, 3, flip=True, anchor=(12, 21))))
    items.append((880, lambda d: sprite_at(d, figs['plumber'][3], 930, 880, 3, anchor=(12, 21))))
    # one flashing its fuse right next to the player
    items.append((866, lambda d: sprite_at(d, figs['mascot'][5], 1180, 866, 3, flip=True, anchor=(12, 21))))
    # one tumbling away after the punch (body-centre anchor (12,14))
    items.append((770, lambda d: sprite_at(d, figs['gamer'][6], 968, 750, 3, anchor=(12, 14))))
    # explosion where another one blew up
    items.append((835, lambda d: sprite_at(d, exp[2], 660, 835, 3, anchor=(32, 32))))
    return items


def render():
    dst = arena_base()
    for _, fn in sorted(build_scene(), key=lambda it: it[0]):
        fn(dst)
    return dst


if __name__ == '__main__':
    img = render()
    save(img, PREVIEW + 'jordan_funkos_arena_mockup.png')
    crop = [r[480:1440] for r in img[196:916]]
    save(zoom(crop, 2, None), PREVIEW + 'jordan_funkos_arena_mockup_zoom2x.png')
    print('ok')
