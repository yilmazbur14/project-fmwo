"""Previews only - never writes into the project.

  python previews.py <out_dir>

Produces a GIF per animated piece, two 1920x1080 arena mockups built on a real Godot render of
ArenaScene, and a 6x close-up sheet of the special faces and the HUD badges.
"""
import math, os, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
from gifio import write_gif
import giant, bomb, projectile, specials, status, glider, bursts

MAT = (113, 152, 79)               # the arena mat's own green
HUD = (26, 24, 38)

# where the 3x cards sit on the 1920x1080 arena render
X0, Y0 = 99, 118
CARD_W3, CARD_H3 = giant.CW * 3, giant.CH * 3


def rgb(c, bg):
    """Canvas -> flat RGB rows over a solid background (GIF has no alpha here)."""
    out = []
    for row in c.rgba():
        out.append([(p[0], p[1], p[2]) if p[3] else bg for p in row])
    return out


def up(rows, f):
    h, w = len(rows), len(rows[0])
    return [[rows[y // f][x // f] for x in range(w * f)] for y in range(h * f)]


def gif(path, frames, delays, bg=MAT, scale=3):
    write_gif(path, [up(rgb(c, bg), scale) for c in frames], delays)
    print('  ', os.path.basename(path))


# --------------------------------------------------------------------------- arena mockups
def arena_base(src):
    w, h, px = read_png(src)
    return w, h, [[tuple(p[:3]) for p in row] for row in px]


def paste3(dst, c, ox, oy, scale=3):
    """Blit a canvas at an integer scale onto an RGB mockup."""
    H, W = len(dst), len(dst[0])
    pal = c.rgba()
    for y in range(c.h):
        for x in range(c.w):
            p = pal[y][x]
            if not p[3]:
                continue
            for j in range(scale):
                for i in range(scale):
                    X, Y = ox + x * scale + i, oy + y * scale + j
                    if 0 <= X < W and 0 <= Y < H:
                        dst[Y][X] = (p[0], p[1], p[2])


def erase_arena_player(m):
    """ArenaScene renders its own player at centre-bottom; wipe it so the mockup shows exactly
    one figure, placed where the fight actually puts them."""
    for y in range(876, 922):
        for x in range(940, 978):
            m[y][x] = MAT


def player_frame(row=0, col=0):
    src = PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png'
    w, h, px = read_png(src)
    c = Cv(32, 32)
    c.rgba_override = [[px[row * 32 + y][col * 32 + x] for x in range(32)] for y in range(32)]
    return c.rgba_override


def paste_rgba(dst, grid, ox, oy, scale):
    H, W = len(dst), len(dst[0])
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            p = grid[y][x]
            if len(p) < 4 or not p[3]:
                continue
            for j in range(scale):
                for i in range(scale):
                    X, Y = ox + x * scale + i, oy + y * scale + j
                    if 0 <= X < W and 0 <= Y < H:
                        dst[Y][X] = (p[0], p[1], p[2])


def mockup_thirds(base, out):
    """Three giant cards over the thirds: left and right already down, the centre one mid-fall
    with its shadow warning on the floor underneath."""
    w, h, px = base
    m = [row[:] for row in px]
    erase_arena_player(m)
    card, shadow = giant.build(), giant.build_shadow()
    paste3(m, card, X0, Y0)
    paste3(m, card, X0 + CARD_W3 * 2, Y0)
    paste3(m, shadow, X0 + CARD_W3, Y0)                       # the warning footprint
    paste3(m, card, X0 + CARD_W3, Y0 - 430)                   # the same card, still falling
    # the player has taken cover on the left card, which has already landed
    paste_rgba(m, player_frame(0, 0), X0 + 250, Y0 + 620, 2)
    write_png(out, w, h, [[(p[0], p[1], p[2], 255) for p in row] for row in m])
    print('  ', os.path.basename(out))


def mockup_monte(base, out):
    """Phase 2: three face-down cards over the thirds, the middle one flipping up under the
    player, and bomb cards falling in."""
    w, h, px = base
    m = [row[:] for row in px]
    erase_arena_player(m)
    cells = specials.cells()
    back, safe = cells[3], cells[0]
    # the monte cards are the 48x64 specials, shown at 6x (288x384) - one per third
    SC = 6
    cw, ch = specials.CW * SC, specials.CH * SC
    cy = Y0 + CARD_H3 - ch - 70
    for i, face in enumerate((back, safe, back)):
        cx = X0 + i * CARD_W3 + (CARD_W3 - cw) // 2
        paste3(m, face, cx, cy, SC)
    # the reveal burst on the middle card
    paste3(m, cells[12], X0 + CARD_W3 + (CARD_W3 - cw) // 2, cy, SC)
    # bomb cards falling in and one ticking on the mat
    bf = bomb.build()
    for (bx, by, fi) in ((X0 + 180, Y0 + 90, 1), (X0 + CARD_W3 * 2 + 300, Y0 + 40, 2),
                         (X0 + 420, Y0 + 430, 0), (X0 + CARD_W3 * 2 + 120, Y0 + 520, 6)):
        paste3(m, bf[fi], bx, by, 3)
    paste_rgba(m, player_frame(0, 0), X0 + CARD_W3 + 253, cy + 296, 2)
    write_png(out, w, h, [[(p[0], p[1], p[2], 255) for p in row] for row in m])
    print('  ', os.path.basename(out))


def ride_cells(pad=110):
    """Josh's ACTUAL josh_glide.png frames composited onto the glider at the shipping anchor,
    so the fit can be checked rather than taken on trust.  Returns RGBA grids."""
    src = PROJ + 'Assets/Characters/Josh/josh_glide.png'
    jw, jh, jpx = read_png(src)
    gl = glider.build()
    ax, ay = glider.JOSH_ANCHOR
    out = []
    for i in range(jw // 80):
        cell = [[(0, 0, 0, 0)] * pad for _ in range(pad)]
        g = gl[i % len(gl)].rgba()
        for y in range(glider.GH):
            for x in range(glider.GW):
                p = g[y][x]
                if p[3] and 0 <= ay + y < pad and 0 <= ax + x < pad:
                    cell[ay + y][ax + x] = p
        for y in range(80):                      # Josh draws OVER the glider
            for x in range(80):
                p = jpx[y][i * 80 + x]
                if p[3]:
                    cell[y][x] = p
        out.append(cell)
    return out


def ride_gif(path, bg=MAT, scale=3):
    cells = ride_cells()
    frames = []
    for cell in cells:
        frames.append(up([[(p[0], p[1], p[2]) if p[3] else bg for p in row] for row in cell], scale))
    write_gif(path, frames, [11] * len(frames))
    print('  ', os.path.basename(path))


def ride_sheet(out, scale=4):
    cells = ride_cells()
    n, pad = len(cells), len(cells[0])
    W = pad * n
    px = [[(0, 0, 0, 0)] * W for _ in range(pad)]
    for i, cell in enumerate(cells):
        for y in range(pad):
            for x in range(pad):
                px[y][i * pad + x] = cell[y][x]
    tmp = WORK + '/ride_raw.png'
    write_png(tmp, W, pad, px)
    save_zoom(tmp, out, scale, bg=(113, 152, 79, 255), checker=False)
    print('  ', os.path.basename(out))


def shadow_strip(out, scale=6):
    """The four shadow heights on the mat, with Josh's grounded footprint width marked."""
    sh = glider.build_shadow()
    band = sheet(sh)
    save_zoom(band, out, scale, bg=(113, 152, 79, 255), checker=False)
    print('  ', os.path.basename(out))


def closeup(out):
    """6x sheet: the three special faces, the back, and the two HUD badges in both states."""
    sc = specials.cells()
    st = status.cells()
    pad = 4
    row1 = sheet([sc[0], sc[1], sc[2], sc[3]])
    band = Cv(row1.w, row1.h + pad + 26)
    band.blit(row1, 0, 0)
    for i, ic in enumerate(st):
        band.blit(ic, 8 + i * 30, row1.h + pad)
    save_zoom(band, out, 6, checker=False, bg=(34, 32, 46, 255))
    print('  ', os.path.basename(out))


# --------------------------------------------------------------------------- main
def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    o = lambda n: os.path.join(outdir, n).replace(os.sep, '/')
    print('gifs')
    gif(o('card_giant_impact.gif'), giant.build_impact(), [5, 5, 6, 7, 9], scale=2)
    bf = bomb.build()
    gif(o('card_bomb.gif'), bf, [d // 10 for d in bomb.DURATIONS], scale=4)
    gif(o('card_bomb_tick_loop.gif'), bf[5:8], [15, 15, 15], scale=4)
    gif(o('card_projectile.gif'), projectile.build(), [6, 6, 6, 6], scale=5)
    sc = specials.cells()
    gif(o('card_shuffle.gif'), sc[5:9], [6, 6, 6, 6], scale=3)
    gif(o('card_reveal.gif'), [sc[3]] + sc[10:15], [30, 5, 5, 6, 7, 9], scale=3)
    stc = status.cells()
    gif(o('status_stamina_drain.gif'), stc[0:2], [40, 22], bg=HUD, scale=6)
    gif(o('status_inverse.gif'), stc[2:4], [40, 22], bg=HUD, scale=6)
    gif(o('josh_glider.gif'), glider.build(), [11, 11, 11], scale=5)
    gif(o('card_shatter.gif'), bursts.build_shatter(), [4, 5, 6, 7, 8], bg=HUD, scale=5)
    gif(o('card_burst.gif'), bursts.build_burst(), [9, 7, 7, 7, 8, 9], scale=4)
    gif(o('card_burst_rain.gif'), bursts.build_rain(), [8, 8, 8, 9, 10, 12], scale=4)

    print('glider fit')
    ride_gif(o('josh_glider_ride.gif'))
    ride_sheet(o('josh_glider_ride_sheet.png'))
    shadow_strip(o('josh_shadow_heights.png'))

    print('mockups')
    src = os.environ.get('JFX_ARENA')
    if src and os.path.exists(src):
        base = arena_base(src)
        mockup_thirds(base, o('mockup_giant_thirds.png'))
        mockup_monte(base, o('mockup_phase2_monte.png'))
    else:
        print('   (set JFX_ARENA to a Godot ArenaScene render to build the mockups)')

    print('closeups')
    closeup(o('closeup_specials_and_icons.png'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
