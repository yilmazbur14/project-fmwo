"""Previews: 6x close-up vs the approved redesign, and a 1920x1080 arena mockup."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, blank, paste, crop

A = r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters"
W = H = 96

# ---------------------------------------------------------------- close-up
_, _, sheet = read_png('sheet.png')
_, _, old = read_png(A + "/Carter/carter_redesign.png")
oldf = crop(old, 0, 0, 64, 64)

BG = (24, 24, 32, 255)
LINE = (58, 58, 74, 255)
pad, gap = 10, 12
cols = [('NEW  carter_akuma f0', crop(sheet, 0, 0, W, H)),
        ('f1  signature pose', crop(sheet, W, 0, W, H)),
        ('f2  back / mark', crop(sheet, 2 * W, 0, W, H))]
cw = W * 3
total_w = pad * 2 + cw * 3 + gap * 2 + gap + 64 * 3
canvas = blank(total_w, pad * 2 + H * 3, BG)
x = pad
for _, im in cols:
    paste(canvas, scale(im, 3), x, pad)
    x += cw + gap
# approved sprite at the same 3x, feet aligned to the same baseline
paste(canvas, scale(oldf, 3), x, pad + (H - 64) * 3)
write_png('preview_closeup.png', total_w * 2, (pad * 2 + H * 3) * 2,
          scale(canvas, 2, BG))
print('preview_closeup.png', total_w * 2, (pad * 2 + H * 3) * 2)

# 6x close-up of just frame 0 next to the approved sprite
c2w = pad * 2 + W * 6 + gap + 64 * 6
c2 = blank(c2w, pad * 2 + H * 6, BG)
paste(c2, scale(crop(sheet, 0, 0, W, H), 6), pad, pad)
paste(c2, scale(oldf, 6), pad + W * 6 + gap, pad + (H - 64) * 6)
write_png('preview_vs_approved_x6.png', c2w, pad * 2 + H * 6, c2)
print('preview_vs_approved_x6.png', c2w, pad * 2 + H * 6)

# ---------------------------------------------------------------- arena mockup
aw, ah, arena = read_png('arena/frame00000002.png')
# find the already-rendered player so the mockup sits on the real floor line
pw, ph, psheet = read_png(A + "/MainPlayer/player_4dir_sheet.png")
xs, ys = [], []
for y in range(ah):
    for x in range(aw):
        r, g, b, a = arena[y][x]
        # the player's skin/denim against the flat green ring
        if a and not (100 < r < 135 and 140 < g < 175 and 60 < b < 100):
            if 600 < y < 960 and 700 < x < 1250:
                xs.append(x)
                ys.append(y)
floor = max(ys) if ys else 900
print('detected player feet row:', floor)

mock = [row[:] for row in arena]
player = crop(psheet, 0, 64, 32, 32)          # facing the camera-ish
oldf64 = crop(old, 0, 0, 64, 64)

# line them all up on the real floor row: player, approved Carter, new f0, new f1
paste(mock, scale(player, 2), 470, floor - 32 * 2 + 2)
paste(mock, scale(oldf64, 3), 560, floor - 64 * 3 + 2)
paste(mock, scale(crop(sheet, 0, 0, W, H), 3), 800, floor - H * 3 + 3)
paste(mock, scale(crop(sheet, W, 0, W, H), 3), 1130, floor - H * 3 + 3)
paste(mock, scale(crop(sheet, 2 * W, 0, W, H), 3), 1460, floor - H * 3 + 3)

write_png('preview_arena.png', aw, ah, mock)
print('preview_arena.png', aw, ah)
small = [[mock[y][x] for x in range(0, aw, 2)] for y in range(0, ah, 2)]
write_png('preview_arena_half.png', len(small[0]), len(small), small)
