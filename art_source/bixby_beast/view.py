"""Preview helpers: zoomed PNGs on a neutral background, crops, side-by-side sheets."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale, blank, paste

BG = (96, 112, 104, 255)
PREV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prev')
os.makedirs(PREV, exist_ok=True)


def zoom_png(src, s, out, region=None, bg=BG):
    w, h, px = read_png(src)
    if region:
        x0, y0, rw, rh = region
        px = crop(px, x0, y0, rw, rh)
        w, h = rw, rh
    write_png(os.path.join(PREV, out), w * s, h * s, scale(px, s, bg))


def zoom_canvas(cv, s, out, region=None, bg=BG):
    px = cv.rgba()
    w, h = cv.w, cv.h
    if region:
        x0, y0, rw, rh = region
        px = crop(px, x0, y0, rw, rh)
        w, h = rw, rh
    write_png(os.path.join(PREV, out), w * s, h * s, scale(px, s, bg))


if __name__ == '__main__':
    src, s, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    region = tuple(int(v) for v in sys.argv[4:8]) if len(sys.argv) >= 8 else None
    zoom_png(src, s, out, region)
