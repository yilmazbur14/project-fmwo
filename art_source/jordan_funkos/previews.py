"""Review previews: 6x design sheet, contract strips, GIFs."""
from build import figure_frames
from figures import FIGURES
from rig import STAND
from pop import pop_frames
from explosion import explosion_frames
from font import draw_text
from gifio import write_gif
from lib import *

BG = (34, 32, 52, 255)
FLOOR = (136, 180, 99, 255)
WHITE = (255, 255, 255, 255)
GREY = (170, 170, 190, 255)
LABELS = {'plumber': 'PLUMBER HERO', 'hedgehog': 'SPEEDY HEDGEHOG', 'mascot': 'SERVER MASCOT',
          'gamer': 'HOODED GAMER'}


def canvas(w, h, c=BG):
    return [[c] * w for _ in range(h)]


def cell(img, s, bg=FLOOR):
    return fill_bg(zoom(img, s, None), bg)


def design_sheet():
    S = 6
    cw = 24 * S
    pad = 24
    W = pad + 4 * (cw + pad)
    Hh = 60 + 2 * (cw + 40) + 150
    c = canvas(W, Hh)
    draw_text(c, 'JORDAN FUNKO MINIONS - DESIGN PASS (6X)', pad, 16, WHITE, 3)
    for i, fig in enumerate(FIGURES):
        x = pad + i * (cw + pad)
        draw_text(c, LABELS[fig.name], x, 50, WHITE, 2)
        stand = fig.frame(STAND)
        close_outline(stand)
        fr = figure_frames(fig)
        blit_scaled(c, cell(stand, 1), x, 66, S)
        draw_text(c, 'REFERENCE POSE', x, 66 + cw + 6, GREY, 2)
        blit_scaled(c, cell(fr[0], 1), x, 66 + cw + 26, S)
        draw_text(c, 'CHASE FRAME 0', x, 66 + 2 * cw + 32, GREY, 2)
    # game-scale strip: player 2x + figures 3x on floor
    y0 = 66 + 2 * cw + 58
    strip_h = 110
    for yy in range(y0, y0 + strip_h):
        for xx in range(pad, W - pad):
            c[yy][xx] = FLOOR
    draw_text(c, 'GAME SCALE: PLAYER 2X, FIGURES 3X', pad + 6, y0 + 6, BG, 2)
    feet = y0 + strip_h - 12
    blit_scaled(c, player_frame(3, 0), pad + 30, feet - 29 * 2, 2)
    for i, fig in enumerate(FIGURES):
        fr = figure_frames(fig)
        blit_scaled(c, fr[1], pad + 130 + i * 120, feet - 21 * 3, 3)
        blit_scaled(c, fr[0], pad + 130 + i * 120 + 60, feet - 21 * 3, 3) if False else None
    save(c, PREVIEW + 'jordan_funkos_design_sheet_6x.png')


def contract_sheet():
    S = 6
    pad = 20
    sheets = [(fig.name, figure_frames(fig), 24) for fig in FIGURES]
    rows_h = sum(24 * S + 48 for _ in sheets) + (32 * S + 48) + (64 * 4 + 48)
    W = pad * 2 + 8 * (24 * S + 6)
    W = max(W, pad * 2 + 6 * (64 * 4 + 6))
    c = canvas(W, rows_h + 60)
    draw_text(c, 'SHEET CONTRACT (FRAME INDEX UNDER EACH CELL)', pad, 14, WHITE, 3)
    y = 50
    groups = ['CHASE', 'CHASE', 'CHASE', 'CHASE', 'FUSE', 'FUSE', 'PUNCHED', 'PUNCHED']
    for name, fr, fs in sheets:
        draw_text(c, 'FUNKO_%s.PNG  8 X 24X24' % name.upper(), pad, y, WHITE, 2)
        for i, f in enumerate(fr):
            x = pad + i * (24 * S + 6)
            blit_scaled(c, cell(f, 1), x, y + 14, S)
            draw_text(c, '%d %s' % (i, groups[i]), x + 2, y + 16 + 24 * S, GREY, 2)
        y += 24 * S + 48
    pop = pop_frames()
    draw_text(c, 'FUNKO_SPAWN_POP.PNG  4 X 32X32', pad, y, WHITE, 2)
    for i, f in enumerate(pop):
        x = pad + i * (32 * S + 6)
        blit_scaled(c, cell(f, 1), x, y + 14, S)
        draw_text(c, '%d' % i, x + 2, y + 16 + 32 * S, GREY, 2)
    y += 32 * S + 48
    exp = explosion_frames()
    draw_text(c, 'FUNKO_EXPLOSION.PNG  6 X 64X64 (SHOWN 4X)', pad, y, WHITE, 2)
    for i, f in enumerate(exp):
        x = pad + i * (64 * 4 + 6)
        blit_scaled(c, cell(f, 1), x, y + 14, 4)
        draw_text(c, '%d' % i, x + 2, y + 16 + 64 * 4, GREY, 2)
    save(c, PREVIEW + 'jordan_funkos_sheet_contract.png')


def gif(frames, path, scale, delays, hold_blank=0):
    fr = [fill_bg(zoom(f, scale, None), FLOOR) for f in frames]
    d = list(delays)
    if hold_blank:
        fr.append([[FLOOR] * len(fr[0][0]) for _ in fr[0]])
        d.append(hold_blank)
    write_gif(path, fr, d)


def gifs():
    for fig in FIGURES:
        fr = figure_frames(fig)
        n = 'funko_' + fig.name
        gif(fr[0:4], PREVIEW + n + '_chase.gif', 6, [7, 7, 7, 7])
        gif(fr[4:6], PREVIEW + n + '_fuse.gif', 6, [8, 8])
        gif(fr[6:8], PREVIEW + n + '_punched.gif', 6, [6, 6])
    gif(pop_frames(), PREVIEW + 'funko_spawn_pop.gif', 6, [5, 7, 8, 10], hold_blank=40)
    gif(explosion_frames(), PREVIEW + 'funko_explosion.gif', 4, [5, 6, 8, 9, 10, 12], hold_blank=40)
    # all four chase loops side by side
    allfr = [figure_frames(f) for f in FIGURES]
    frames = []
    for i in range(4):
        frames.append(hstack([fill_bg(zoom(a[i], 6, None), FLOOR) for a in allfr]))
    write_gif(PREVIEW + 'funko_all_chase.gif', frames, [7] * 4)


if __name__ == '__main__':
    design_sheet()
    contract_sheet()
    gifs()
    print('ok')
