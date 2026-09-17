"""Write Josh's animation strips into Assets/Characters/Josh/.

Every sheet is a horizontal strip of 80x80 frames (hframes = N, vframes = 1, frame 0 leftmost).
Run:  python export_anims.py [dest_dir]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from jlib import W, H, PAL, to_rgba
from pngio import write_png, read_png
import anims

ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Josh/'
NAMES = {v[:3]: k for k, v in PAL.items()}


def strip(canvases):
    n = len(canvases)
    sheet = [[(0, 0, 0, 0)] * (W * n) for _ in range(H)]
    for i, c in enumerate(canvases):
        g = to_rgba(c)
        for y in range(H):
            for x in range(W):
                sheet[y][i * W + x] = g[y][x]
    return sheet, W * n, H


def audit(path):
    w, h, px = read_png(path)
    alphas = sorted({p[3] for row in px for p in row})
    cols = Counter('#%02X%02X%02X' % p[:3] for row in px for p in row if p[3])
    stray = [k for k in cols if tuple(int(k[i:i + 2], 16) for i in (1, 3, 5)) not in NAMES]
    solid = [(x % W, y) for y in range(h) for x in range(w) if px[y][x][3]]
    bottom = max(y for (x, y) in solid)
    ok = (alphas == [0, 255]) and not stray
    return ok, w, h, len(cols), bottom, stray, alphas


def base_sheet():
    """josh_cards.png - the base 2-frame sprite the menu and the victory ladder crop a portrait
    from.  Rebuilt on the lean build so the portrait matches the fight sheets.
    Frame 0 = the idle, frame 1 = his signature card presentation."""
    return [anims.idle(0), anims.show_card(2)]


if __name__ == '__main__':
    out = (sys.argv[1] if len(sys.argv) > 1 else ASSET).rstrip('/\\') + '/'
    for name in anims.ANIMS:
        sheet, w, h = strip(anims.sheet(name))
        p = out + name + '.png'
        write_png(p, w, h, sheet)
        ok, w, h, nc, bottom, stray, alphas = audit(p)
        print('%-18s %3dx%-3d  %2d frames  %2d colours  lowest row %2d  %s'
              % (name + '.png', w, h, w // W, nc, bottom, 'OK' if ok else 'CHECK %s %s' % (alphas, stray)))
    sheet, w, h = strip(base_sheet())
    p = out + 'josh_cards.png'
    write_png(p, w, h, sheet)
    ok, w, h, nc, bottom, stray, alphas = audit(p)
    print('%-18s %3dx%-3d  %2d frames  %2d colours  lowest row %2d  %s'
          % ('josh_cards.png', w, h, w // W, nc, bottom, 'OK' if ok else 'CHECK %s %s' % (alphas, stray)))
