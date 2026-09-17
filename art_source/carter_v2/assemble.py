"""Assemble the 15-frame main sheet + 5-frame elbow sheet, write PNGs, strips, GIFs and checks."""
from approved import *
import frames_idle as fi, frames_tele as ft, frames_charge as fc, frames_up as fu, frames_more as fm, frames_elbow as fe
from gif import write_gif

R = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
OUT = os.path.join(HERE, 'sheet')
os.makedirs(OUT, exist_ok=True)

MAIN = [fi.f0(), fi.f1(), fi.f2(), ft.f3(), ft.f4(), fc.f5(), fc.f6(), fu.f7(), fu.f8(),
        fm.f9(), fm.f10(), fm.f11(), fm.f12(), fm.f13(), fm.f14()]
ELBOW = [fe.e0(), fe.e1(), fe.e2(), fe.e3(), fe.e4()]
assert len(MAIN) == 15 and len(ELBOW) == 5


def holes(g):
    return [(x, y) for y in range(1, 63) for x in range(1, 63)
            if g[y][x] == '.' and all(g[y + dy][x + dx] != '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]


def strip(frames):
    pix = [grid_to_pix(g) for g in frames]
    return [sum((p[y] for p in pix), []) for y in range(64)]


APPROVED_GAP = {(21, 20), (21, 21)}   # earring gap from the approved idle
for name, frames in (('main', MAIN), ('elbow', ELBOW)):
    for i, g in enumerate(frames):
        for (x, y) in holes(g):
            if not (name == 'main' and i <= 2 and (x, y) in APPROVED_GAP) and not (name == 'elbow' and i == 4 and (x, y) == (21, 20)):
                g[y][x] = '#'
        save_grid(os.path.join(OUT, '%s_%02d.txt' % (name, i)), g)
        h = holes(g)
        if h:
            print(name, i, 'enclosed transparent px:', h)

main_strip = strip(MAIN)
elbow_strip = strip(ELBOW)
write_png(R + 'CarterAndJosh/carter.png', 960, 64, main_strip)
write_png(R + 'Mason/carter_elbowdrop.png', 320, 64, elbow_strip)

LIGHT = (236, 236, 240, 255)
GREEN = (136, 179, 99, 255)
save(os.path.join(OUT, 'carter_sheet_3x.png'), zoom(main_strip, 3, LIGHT))
save(os.path.join(OUT, 'carter_elbowdrop_3x.png'), zoom(elbow_strip, 3, LIGHT))

# per-animation GIFs at the scene's real timings, 3x on the arena green
ANIMS = {
    'idle': ([0, 1, 2], [350, 350, 350]),
    'telegraph': ([3, 4], [200, 200]),
    'charge_down': ([5, 6], [120, 120]),
    'charge_up': ([7, 8], [120, 120]),
    'recover': ([9, 10, 11], [250, 250, 250]),
    'hit': ([0, 12, 0], [600, 200, 600]),          # shown between idle frames for context
    'defeated': ([13, 14], [350, 1600]),            # last frame holds in game
}
mp = [grid_to_pix(g) for g in MAIN]
for a, (idx, delays) in ANIMS.items():
    frames = [zoom(mp[i], 3, GREEN) for i in idx]
    if a == 'telegraph':
        write_gif(os.path.join(OUT, 'gif_telegraph_tinted.gif'), [zoom(tint(mp[i]), 3, GREEN) for i in idx], delays)
    write_gif(os.path.join(OUT, 'gif_%s.gif' % a), frames, delays)
ep = [grid_to_pix(g) for g in ELBOW]
seq = [0, 1, 0, 1, 0, 2, 3, 4]
dl = [80, 80, 80, 80, 30, 200, 120, 400]
write_gif(os.path.join(OUT, 'gif_elbowdrop.gif'), [zoom(ep[i], 3, GREEN) for i in seq], dl)

# checks
for path, w in ((R + 'CarterAndJosh/carter.png', 960), (R + 'Mason/carter_elbowdrop.png', 320)):
    ww, hh, p = read_png(path)
    print(path.split('/')[-1], ww, hh, 'alphas', sorted({px[3] for row in p for px in row}))
print('assembled')
