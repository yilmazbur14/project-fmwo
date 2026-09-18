"""Previews for Carter's combat set: a GIF per animation at the shipped
timings, a 6x contact sheet of every frame, and two 1920x1080 arena mockups
with the player in them for scale.

    python previews_combat.py <scratch_dir> [<arena_frame.png>]

The arena plate comes from Godot's movie writer:
  Godot.exe --path <project> --write-movie <out>.png --fixed-fps 30 \
            --quit-after 3 res://Scenes/Core/ArenaScene.tscn
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, blank, paste, crop
from gifio import write_gif
from build_combat import SHEETS, TIMINGS

A = r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters"
OUT = os.path.join(A, 'Carter')
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else '.'
ARENA = sys.argv[2] if len(sys.argv) > 2 else None
W = H = 96

BG = (30, 26, 36, 255)
GRID = (48, 42, 56, 255)
FLOORC = (104, 78, 130, 255)
INK = (232, 228, 238, 255)
HOT = (255, 90, 70, 255)
COOL = (120, 210, 255, 255)

# boss sprites live at scale 3, the player at scale 2 (MainPlayer.tscn)
BOSS_SCALE = 3
PLAYER_SCALE = 2


def frames_of(path, fw=W, fh=H):
    w, h, px = read_png(path)
    n = w // fw
    return [crop(px, i * fw, 0, fw, fh) for i in range(n)]


def flat(f, bg=BG):
    return [[(p if p[3] else bg) for p in row] for row in f]


# ---------------------------------------------------------------- GIFs

def gifs():
    for name, _, _ in SHEETS:
        fs = frames_of(os.path.join(OUT, name))
        ms = TIMINGS[name]
        assert len(ms) == len(fs), (name, len(ms), len(fs))
        sc = 4
        write_gif(os.path.join(SCRATCH, name.replace('.png', '.gif')),
                  [scale(flat(f), sc) for f in fs],
                  [max(2, round(m / 10.0)) for m in ms])
        print('%-28s %dx%d  %d frames  %dms total'
              % (name.replace('.png', '.gif'), W * sc, H * sc, len(fs), sum(ms)))


# ---------------------------------------------------------------- contact

def contact(sc=6):
    sets = [(n.replace('carter_', '').replace('.png', ''),
             frames_of(os.path.join(OUT, n))) for n, _, _ in SHEETS]
    cols = max(len(f) for _, f in sets)
    pad, lab = 4, 12
    cw, ch = (W + pad) * sc, (H + pad + lab) * sc
    canvas = blank(cols * cw, len(sets) * ch, BG)
    for r, (name, fs) in enumerate(sets):
        for c, f in enumerate(fs):
            tile = [[(p if p[3] else
                      (GRID if (x // 8 + y // 8) % 2 == 0 else BG))
                     for x, p in enumerate(row)] for y, row in enumerate(f)]
            for x in range(W):
                tile[95][x] = FLOORC
            paste(canvas, scale(tile, sc), c * cw, r * ch + lab * sc)
        # a bar the width of the row's frames marks where each set starts
        for x in range(cw * len(fs)):
            for y in range(sc, sc * 4):
                canvas[r * ch + y][x] = (78, 62, 96, 255)
    write_png(os.path.join(SCRATCH, 'carter_combat_contact_6x.png'),
              cols * cw, len(sets) * ch, canvas)
    print('carter_combat_contact_6x.png  %dx%d' % (cols * cw, len(sets) * ch))


# ---------------------------------------------------------------- arena

def player_frame(idx=10):
    w, h, px = read_png(A + '/MainPlayer/player_4dir_sheet.png')
    fw = w // 10
    fh = h // 4
    return crop(px, (idx % 10) * fw, (idx // 10) * fh, fw, fh)


def find_player(plate):
    """The arena scene already draws the player at his real in-game scale, so
    finding him gives both the floor line and an honest ruler.  The search
    window is deliberately tight - opened up it caught the ropes and the HUD
    and put the floor 100px too low, with Carter standing in the health bar."""
    h, w = len(plate), len(plate[0])
    xs, ys = [], []
    for y in range(int(h * 0.55), int(h * 0.89)):
        for x in range(int(w * 0.42), int(w * 0.58)):
            r, g, b = plate[y][x][:3]
            if not (100 < g < 200 and r < g - 20 and b < g - 20):
                xs.append(x)
                ys.append(y)
    if not xs:
        return w // 2, int(h * 0.85), 50
    return (min(xs) + max(xs)) // 2, max(ys), max(ys) - min(ys) + 1


def tick(img, x, y, col, r=9):
    h, w = len(img), len(img[0])
    for d in range(-r, r + 1):
        for px, py in ((x + d, y), (x, y + d)):
            if 0 <= px < w and 0 <= py < h and abs(d) > 2:
                img[py][px] = col


def stand(img, f, sc, cx, floor):
    """paste a 96x96 frame so row 95 lands on `floor` and x=47.5 on cx."""
    paste(img, scale(f, sc), int(cx - 48 * sc), int(floor - 95 * sc))


def arena(plate_path):
    w, h, plate = read_png(plate_path)
    pcx, pfloor, pht = find_player(plate)
    print('arena plate %dx%d, player centre x=%d, feet y=%d, %dpx tall'
          % (w, h, pcx, pfloor, pht))
    ply = player_frame()
    ph = len(ply)

    # ---- mockup 1: the punish window, player closing in
    img = [row[:] for row in plate]
    spent = frames_of(os.path.join(OUT, 'carter_spent.png'))
    bx = pcx + 330
    stand(img, spent[0], BOSS_SCALE, bx, pfloor)
    # the badge / light anchor: 18px of screen above the top of THIS pose,
    # which for the kneel is a long way below where the idle's would be
    top = pfloor - (95 - 24) * BOSS_SCALE
    tick(img, bx, top - 26, COOL)
    write_png(os.path.join(SCRATCH, 'arena_spent_1920.png'), w, h, img)
    print('arena_spent_1920.png  %dx%d' % (w, h))

    # ---- mockup 2: one clone crossing, four frames along its path
    img = [row[:] for row in plate]
    rush = frames_of(os.path.join(OUT, 'carter_rush.png'))
    step = 230
    x0 = pcx - 560
    for i, f in enumerate(rush):
        stand(img, f, BOSS_SCALE, x0 + i * step, pfloor)
    # where the strike bites on the last two frames, and the light anchor
    import combat_rush as CR
    for i in (2, 3):
        ix, iy = CR.IMPACT[i]
        cx = x0 + i * step + (ix - 47.5) * BOSS_SCALE
        cy = pfloor - (95 - iy) * BOSS_SCALE
        tick(img, int(cx), int(cy), HOT, 11)
    tick(img, x0 + 2 * step, pfloor - (95 - 10) * BOSS_SCALE - 26, COOL)
    write_png(os.path.join(SCRATCH, 'arena_rush_1920.png'), w, h, img)
    print('arena_rush_1920.png   %dx%d' % (w, h))

    # ---- mockup 3: the victory pose at the moment the mark ignites
    import combat_victory as CVI
    img = [row[:] for row in plate]
    vic = frames_of(os.path.join(OUT, 'carter_victory.png'))
    stand(img, vic[CVI.IGNITE_FRAME], BOSS_SCALE, pcx + 300, pfloor)
    tick(img, pcx + 300, pfloor - (95 - 20) * BOSS_SCALE - 26, COOL)
    write_png(os.path.join(SCRATCH, 'arena_victory_1920.png'), w, h, img)
    print('arena_victory_1920.png %dx%d  (ignition frame %d)'
          % (w, h, CVI.IGNITE_FRAME))


if __name__ == '__main__':
    gifs()
    contact()
    if ARENA and os.path.exists(ARENA):
        arena(ARENA)
    else:
        print('no arena plate given - skipping the 1920x1080 mockups')
