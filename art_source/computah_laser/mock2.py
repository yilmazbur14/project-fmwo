from pngio import *
from gen_art2 import *
beam, fa, fb, aim = build("preview2")
FLOOR = (136, 180, 99, 255)
_, _, comp = read_png(r"C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Computah/computah.png")
W, H = 320, 150
canvas = [[FLOOR for _ in range(W)] for _ in range(H)]
def put(x, y, p):
    if p[3] > 0 and 0 <= x < W and 0 <= y < H: canvas[y][x] = p
def sprite(src, sx, sw, sh, dx, dy):
    for y in range(sh):
        for x in range(sw):
            put(dx + x, dy + y, src[y][sx + x])
# top: firing with beams; bottom: telegraph with aim lines
for row, (frame, firing) in enumerate(((17, True), (16, False))):
    cx, cy = 160, 38 + row * 75
    sprite(comp, frame * 64, 64, 64, cx - 32, cy - 32)
    for side in (-1, 1):
        ex = cx - 33 if side < 0 else cx + 32
        ey = cy - 4
        if firing:
            for i in range(-6, 130):
                for r in range(23):
                    x = ex + i if side > 0 else ex - 1 - i
                    put(x, ey - 11 + r, beam[r][i % 16])
        else:
            for i in range(0, 130):
                for r in range(5):
                    x = ex + i if side > 0 else ex - 1 - i
                    put(x, ey - 2 + r, aim[r][i % 12])
        f = fa if firing else fb
        for y in range(35):
            for x in range(35):
                put(ex - 17 + x, ey - 17 + y, f[y][x])
w2, h2, up = upscale(W, H, canvas, 4)
write_png("mock_beam2.png", w2, h2, up)
