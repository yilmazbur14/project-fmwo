"""Zoom reference sprites for study and dump their palettes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale
from collections import Counter

C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs")
BG = (96, 112, 104, 255)

def info(name):
    w, h, px = read_png(C + name)
    cnt = Counter(p for row in px for p in row if p[3] > 0)
    alphas = sorted(set(p[3] for row in px for p in row))
    print(name, w, h, len(cnt), "colors; alphas:", alphas)
    return w, h, px, cnt

def zoom(name, s, out, region=None, bg=BG):
    w, h, px, cnt = info(name)
    if region:
        x0, y0, rw, rh = region
        px = crop(px, x0, y0, rw, rh)
        w, h = rw, rh
    write_png(os.path.join(OUT, out), w * s, h * s, scale(px, s, bg))

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "bixby":
        zoom("Bixby/bixby.png", 10, "bixby_10x.png")
        w, h, px, cnt = info("Bixby/bixby.png")
        for c, n in cnt.most_common(60):
            print("  #%02x%02x%02x %d" % (c[0], c[1], c[2], n))
    elif which == "liam":
        zoom("Liam/liam.png", 10, "liam_10x.png")
        zoom("Liam/portrait.png", 8, "liam_portrait_8x.png")
        zoom("Liam/liam_glasses_push.png", 4, "liam_glasses_push_4x.png")
    elif which == "mason":
        zoom("Mason/mason.png", 10, "mason_10x.png")
        zoom("Mason/mason_sheet.png", 3, "mason_sheet_3x.png")
    elif which == "mech":
        zoom("GreysonMech/greyson_mech.png", 6, "mech_6x.png")
        w, h, px, cnt = info("GreysonMech/greyson_mech.png")
        for c, n in cnt.most_common(60):
            print("  #%02x%02x%02x %d" % (c[0], c[1], c[2], n))
    elif which == "eric":
        zoom("Eric/eric_redesign_v2.png", 4, "eric_v2_4x.png")
        w, h, px, cnt = info("Eric/eric_redesign_v2.png")
        for c, n in cnt.most_common(60):
            print("  #%02x%02x%02x %d" % (c[0], c[1], c[2], n))
    elif which == "player":
        zoom("MainPlayer/player_4dir_sheet.png", 6, "player_6x.png")
    elif which == "generic":
        name, s, out = sys.argv[2], int(sys.argv[3]), sys.argv[4]
        region = tuple(int(v) for v in sys.argv[5:9]) if len(sys.argv) > 8 else None
        zoom(name, s, out, region)
