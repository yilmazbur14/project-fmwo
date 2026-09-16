"""In-context legibility mock: real arena floor colour, real Mason (3x) and player (2x)
sprites, plus FX strips at their in-game 3x scale. Positions are sprite CENTRES (Godot
Sprite2D default centred=true)."""
import sys
import fxpng

ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/'
FLOOR = (136, 180, 99)


def frame_of(px, fw, fh, i):
    return [row[i * fw:(i + 1) * fw] for row in px[:fh]]


def blit(canvas, cw, ch, spr, sw, sh, k, cx, cy):
    x0 = cx - (sw * k) // 2
    y0 = cy - (sh * k) // 2
    for y in range(sh * k):
        for x in range(sw * k):
            p = spr[y // k][x // k]
            if p[3] == 0:
                continue
            X, Y = x0 + x, y0 + y
            if 0 <= X < cw and 0 <= Y < ch:
                a = p[3] / 255.0
                q = canvas[Y][X]
                canvas[Y][X] = tuple(int(round(p[i] * a + q[i] * (1 - a))) for i in range(3)) + (255,)


def new_canvas(w, h):
    return [[FLOOR + (255,) for _ in range(w)] for _ in range(h)]


if __name__ == '__main__':
    bomb_path = sys.argv[1]
    out = sys.argv[2]
    cw, ch = 640, 300
    cv = new_canvas(cw, ch)
    _, _, mason = fxpng.read_png(ASSETS + 'Characters/Mason/mason.png')
    _, _, player = fxpng.read_png(ASSETS + 'Characters/MainPlayer/MainC Top Down.png')
    _, _, bombs = fxpng.read_png(bomb_path)
    # trail of bombs left behind Mason as he waddles right
    for i, bx in enumerate((60, 170, 280, 390)):
        blit(cv, cw, ch, frame_of(bombs, 32, 32, i % 2), 32, 32, 3, bx, 200)
    blit(cv, cw, ch, mason, 64, 64, 3, 530, 170)
    blit(cv, cw, ch, player, 32, 32, 2, 230, 90)
    fxpng.write_png(out, cw, ch, cv)
