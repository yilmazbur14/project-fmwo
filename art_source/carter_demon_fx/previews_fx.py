"""Previews for the RAGING DEMON effects - GIFs, the red/yellow comparison and
its greyscale proof, and two 1920x1080 arena mockups of the sequence moment.

    python previews_fx.py <output_dir>

The mockups composite for real - normal alpha for the darkness, additive for the
spotlight and the impacts - because the whole question about the stage pieces is
whether their strengths are right once they are actually layered, and a preview
that just pastes opaque pixels answers nothing.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, '..', 'carter_akuma'))
os.chdir(_HERE)

from pngio import read_png, write_png, blank, paste, crop, scale
from gifio import write_gif

PROJ = os.path.abspath(os.path.join('..', '..'))
DEMON = os.path.join(PROJ, 'Assets', 'Characters', 'Carter', 'Demon')
CHARS = os.path.join(PROJ, 'Assets', 'Characters')

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
ARENA = os.path.join(OUT, 'arena', 'frame00000002.png')


def d(name):
    return os.path.join(DEMON, name)


# ------------------------------------------------------------- compositing

def over(dst, src, ox, oy):
    """normal alpha blend"""
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = oy + y
        if not (0 <= yy < H):
            continue
        for x, p in enumerate(row):
            a = p[3]
            if not a:
                continue
            xx = ox + x
            if not (0 <= xx < W):
                continue
            b = dst[yy][xx]
            k = a / 255.0
            dst[yy][xx] = (int(p[0] * k + b[0] * (1 - k)),
                           int(p[1] * k + b[1] * (1 - k)),
                           int(p[2] * k + b[2] * (1 - k)), 255)


def add(dst, src, ox, oy):
    """additive blend, the way a CanvasItem with blend_mode = add does it"""
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = oy + y
        if not (0 <= yy < H):
            continue
        for x, p in enumerate(row):
            a = p[3]
            if not a:
                continue
            xx = ox + x
            if not (0 <= xx < W):
                continue
            b = dst[yy][xx]
            k = a / 255.0
            dst[yy][xx] = (min(255, int(b[0] + p[0] * k)),
                           min(255, int(b[1] + p[1] * k)),
                           min(255, int(b[2] + p[2] * k)), 255)


def grey(px):
    out = []
    for row in px:
        r = []
        for p in row:
            g = int(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2])
            r.append((g, g, g, p[3]))
        out.append(r)
    return out


def frames_of(path, fw):
    w, h, px = read_png(path)
    return [crop(px, i * fw, 0, fw, h) for i in range(w // fw)]


# -------------------------------------------------------------------- gifs

def gif(name, path, fw, z, delays, bg=(18, 18, 22, 255)):
    fr = frames_of(path, fw)
    out = []
    for f in fr:
        cv = blank(len(f[0]) * z, len(f) * z, bg)
        over(cv, scale(f, z), 0, 0)
        out.append(cv)
    n = os.path.join(OUT, name)
    write_gif(n, out, delays if isinstance(delays, list)
              else [delays] * len(out))
    print('  ', name, len(out), 'frames')


def gifs():
    # the light plays as two separate 4-frame clips, so show them one after
    # the other with a beat between
    gif('demon_light.gif', d('demon_light.png'), 24, 8,
        [5, 4, 30, 8, 5, 4, 30, 14])
    gif('demon_clone.gif', d('demon_clone.png'), 48, 5,
        [5, 5, 5, 5, 4, 4, 4, 4, 5, 5, 5, 12])
    gif('demon_clone_ghost.gif', d('demon_clone_ghost.png'), 96, 4, 4)
    gif('demon_strike.gif', d('demon_strike.png'), 96, 3, [4, 3, 3, 3, 3, 6])
    gif('demon_parry_break.gif', d('demon_parry_break.png'), 96, 3,
        [4, 4, 3, 3, 3, 7])
    gif('demon_finish.gif', d('demon_finish.png'), 224, 2, [4, 4, 6, 5, 8])


# ---------------------------------------------- one clone, start to finish

CLONE_X = [30, 32, 34, 37,            # appear: it barely drifts while it forms
           52, 86, 120, 152,          # rush: it crosses
           172, 180, 186, 190]        # dissipate: the residue coasts to a stop
CLONE_DELAY = [6, 6, 6, 6, 4, 4, 4, 4, 5, 5, 6, 16]


def clone_pass_gif():
    """the whole life of one clone: gathers out of the dark, crosses, scatters"""
    cw, ch, Z = 232, 58, 3
    _, _, cl = read_png(d('demon_clone.png'))
    _, _, gh = read_png(d('demon_clone_ghost.png'))
    out = []
    for i in range(12):
        cv = blank(cw * Z, ch * Z, (23, 23, 24, 255))
        x, y = CLONE_X[i], 6
        if 3 <= i <= 8:                          # the smear only while moving
            g = crop(gh, min(3, max(0, i - 4)) * 96, 0, 96, 48)
            over(cv, scale(g, Z), (x - 24) * Z, y * Z)
        over(cv, scale(crop(cl, i * 48, 0, 48, 48), Z), x * Z, y * Z)
        out.append(cv)
    write_gif(os.path.join(OUT, 'demon_clone_pass.gif'), out, CLONE_DELAY)
    print('   demon_clone_pass.gif 12 frames')


# ------------------------------------------------- red vs yellow comparison

def comparison():
    fr = frames_of(d('demon_light.png'), 24)
    Z, pad, gap = 6, 16, 10
    lab = 0
    cw, ch = 24 * Z, 24 * Z
    W = pad * 2 + cw * 4 + gap * 3
    H = pad * 2 + (ch + gap) * 2 + lab
    BG = (20, 20, 26, 255)

    def block(src):
        cv = blank(W, H, BG)
        for i in range(4):
            over(cv, scale(src[i], Z), pad + i * (cw + gap), pad)
            over(cv, scale(src[4 + i], Z), pad + i * (cw + gap), pad + ch + gap)
        return cv

    colour = block(fr)
    write_png(os.path.join(OUT, 'light_compare_x6.png'), W, H, colour)
    write_png(os.path.join(OUT, 'light_compare_x6_greyscale.png'), W, H,
              grey(colour))

    # and the two hold frames alone, side by side, colour over greyscale -
    # this is the pair the player actually has to tell apart
    HZ = 10
    hw = 24 * HZ
    W2 = pad * 2 + hw * 2 + gap
    H2 = pad * 2 + hw * 2 + gap
    big = blank(W2, H2, BG)
    over(big, scale(fr[2], HZ), pad, pad)
    over(big, scale(fr[6], HZ), pad + hw + gap, pad)
    g = grey(big)
    for y in range(pad + hw + gap, H2 - pad):
        for x in range(W2):
            big[y][x] = g[y - hw - gap][x]
    write_png(os.path.join(OUT, 'light_hold_x10_colour_vs_grey.png'),
              W2, H2, big)
    print('   light_compare_x6.png / _greyscale.png / hold_x10')


# ---------------------------------------------------------- arena mockups

FLOOR = (136, 180, 99, 255)
PLAYER_HOME = (959, 900)
CENTRE = (960, 540)             # the middle of the ring: Panel 100..1820 / 100..980


def arena_mockup(light_frame, name):
    aw, ah, arena = read_png(ARENA)
    mock = [list(r) for r in arena]

    # the player is standing at the bottom in the render; the sequence yanks
    # them to the middle, so paint the old position out with the floor colour
    for y in range(PLAYER_HOME[1] - 48, PLAYER_HOME[1] + 48):
        for x in range(PLAYER_HOME[0] - 44, PLAYER_HOME[0] + 44):
            mock[y][x] = FLOOR

    # ---- 1. darkness, over the floor and the crowd
    _, _, dk = read_png(d('demon_darkness.png'))
    over(mock, scale(dk, 3), 0, 0)

    # ---- 2. the floor pool, under the fighters.  The POOL file, not the
    # combined one - the cone goes on separately at step 6 and laying the whole
    # spotlight down here would draw the shaft twice.
    _, _, sp = read_png(d('demon_spotlight_pool.png'))
    spx, spy = CENTRE[0] - 80 * 3, CENTRE[1] + 32 - 186 * 3
    add(mock, scale(sp, 3), spx, spy)

    # ---- 3. the player, lit, at the centre
    _, _, psheet = read_png(os.path.join(CHARS, 'MainPlayer',
                                         'player_4dir_sheet.png'))
    player = crop(psheet, 0, 64, 32, 32)          # facing down-ish
    over(mock, scale(player, 2), CENTRE[0] - 32, CENTRE[1] - 32)

    # ---- 4. a clone mid-rush, coming in from the left.  48x48 at 3x = 144px,
    #         about half Carter and twice the player.
    _, _, cl = read_png(d('demon_clone.png'))
    clone = crop(cl, 5 * 48, 0, 48, 48)           # mid-rush
    _, _, gh = read_png(d('demon_clone_ghost.png'))
    ghost1 = crop(gh, 96, 0, 96, 48)              # age 1
    cx = CENTRE[0] - 290                          # frame left edge
    cy = CENTRE[1] + 32 - 48 * 3                  # feet on the player's line
    over(mock, scale(ghost1, 3), cx - 24 * 3, cy)   # ghost frame is 48 wider
    over(mock, scale(clone, 3), cx, cy)

    # ---- 5. the light over its head, sat on the clone's own bounding box
    xs = [x for y in range(48) for x in range(48) if clone[y][x][3] > 0]
    ys = [y for y in range(48) for x in range(48) if clone[y][x][3] > 0]
    hx = cx + (min(xs) + max(xs)) // 2 * 3
    hy = cy + min(ys) * 3
    _, _, li = read_png(d('demon_light.png'))
    lg = crop(li, light_frame * 24, 0, 24, 24)
    over(mock, scale(lg, 3), hx - 36, hy - 84)

    # ---- 6. the cone, in the air in FRONT of the fighters
    _, _, cone = read_png(d('demon_spotlight_cone.png'))
    add(mock, scale(cone, 3), spx, spy)

    # ---- 7. the HUD lives on a CanvasLayer above all of this
    for y in range(962, ah):
        for x in range(aw):
            p = arena[y][x]
            if p[:3] == (0, 0, 0):
                continue
            greyish = abs(p[0] - p[1]) < 12 and abs(p[1] - p[2]) < 12
            greenish = p[1] > p[0] + 20 and p[1] > p[2] + 20
            if y >= 1012 or not (greyish or greenish):
                mock[y][x] = p

    write_png(os.path.join(OUT, name), aw, ah, mock)
    half = [[mock[y][x] for x in range(0, aw, 2)] for y in range(0, ah, 2)]
    write_png(os.path.join(OUT, name.replace('.png', '_half.png')),
              len(half[0]), len(half), half)
    print('  ', name)


if __name__ == '__main__':
    print('gifs')
    gifs()
    clone_pass_gif()
    print('comparison')
    comparison()
    print('arena mockups')
    arena_mockup(2, 'mockup_red.png')
    arena_mockup(6, 'mockup_yellow.png')
