"""Inspection helpers: upscale on a dark background, optionally with a pixel grid, optionally cropped."""
import sys

from PIL import Image

from pal import lib

SCRATCH = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
           'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_redesign/')
BG = (46, 49, 58, 255)


def zoom(im, s, box=None, bg=BG, grid=False, major=10):
    if box:
        im = im.crop(box)
    if grid:
        big = lib.grid(im, s, major=major)
    else:
        big = lib.upscale(lib.on_bg(im, bg), s)
    return big


def save(im, name, s=4, box=None, grid=False):
    zoom(im, s, box, grid=grid).save(SCRATCH + name)
    return SCRATCH + name


if __name__ == '__main__':
    src, name, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
    box = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
    save(Image.open(src).convert('RGBA'), name, s, box, grid='grid' in sys.argv)
