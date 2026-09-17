from pngio import *
from gen_art import *
beam, fx = build("preview")
FLOOR = (136, 180, 99, 255)
_, _, comp = read_png(r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Computah/computah.png")
W, H = 200, 70
canvas = [[FLOOR for _ in range(W)] for _ in range(H)]
def blit(src_px, sx, sy, sw, sh, dx, dy):
    for y in range(sh):
        for x in range(sw):
            p = src_px(sx + x, sy + y)
            if p[3] > 0 and 0 <= dy + y < H and 0 <= dx + x < W:
                canvas[dy + y][dx + x] = p
cx, cy = 100, 32
blit(lambda x, y: comp[y][x], 17*64, 0, 64, 64, cx - 32, cy - 32)
L = 60
for frame_off, side in ((0, 1), (0, -1)):
    ex = cx + (32 if side > 0 else -33)
    ey = cy - 4
    for i in range(L):
        for r in range(9):
            p = beam[r + frame_off][i % 8]
            x = ex + side * i if side > 0 else ex - 1 - i
            canvas[ey - 4 + r][x] = p
    f = fx[0]
    for y in range(11):
        for x in range(11):
            if f[y][x][3] > 0: canvas[ey - 5 + y][ex - 5 + x] = f[y][x]
    t = fx[2]
    tx = ex + side * L
    for y in range(11):
        for x in range(11):
            if t[y][x][3] > 0: canvas[ey - 5 + y][tx - 5 + x] = t[y][x]
# aim line sample row
for i in range(40):
    p = PAL[AIM[0][i % 6]]
    if p[3] > 0: canvas[62][10 + i] = p
w2, h2, up = upscale(W, H, canvas, 6)
write_png("mock_beam.png", w2, h2, up)
