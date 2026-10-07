"""The shout, one syllable a mash bar, as chunky slanted action lettering: a hot fill (white over the beam's ramp),
the ramp's deep tone as an inner rim, a black outline and a drop shadow. Screen-space art (a UI layer)."""
import numpy as np
from PIL import Image
from common import *
from energy import RAMPS, rgba

GLYPHS = {
    "S": [".######", "#######", "##.....", "######.", ".######", ".....##", ".....##", "#######", "######."],
    "H": ["##...##", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##", "##...##"],
    "I": ["######", "######", "..##..", "..##..", "..##..", "..##..", "..##..", "######", "######"],
    "N": ["##...##", "###..##", "###..##", "####.##", "##.####", "##..###", "##..###", "##...##", "##...##"],
    "K": ["##...##", "##..##.", "##.##..", "####...", "###....", "####...", "##.##..", "##..##.", "##...##"],
    "U": ["##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "##...##", "#######", ".#####."],
    "A": ["..###..", ".#####.", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##"],
    "D": ["######.", "#######", "##...##", "##...##", "##...##", "##...##", "##...##", "#######", "######."],
    "O": [".#####.", "#######", "##...##", "##...##", "##...##", "##...##", "##...##", "#######", ".#####."],
    "E": ["#######", "#######", "##.....", "##.....", "######.", "######.", "##.....", "#######", "#######"],
    "!": ["##", "##", "##", "##", "##", "##", "..", "##", "##"],
    ".": ["..", "..", "..", "..", "..", "..", "..", "##", "##"],
}
WORDS = ["SHIN", "KU", "HA", "DO", "KEN!!!!"]
CELL_W, CELL_H = 96, 16


def word_mask(word, slant=True):
    gh = 9
    width = sum(len(GLYPHS[c][0]) + 2 for c in word) - 2
    shear = (gh - 1) // 3 if slant else 0
    m = np.zeros((gh, width + shear), bool)
    x = 0
    for c in word:
        g = GLYPHS[c]
        for y, row in enumerate(g):
            off = (gh - 1 - y) // 3 if slant else 0
            for i, ch in enumerate(row):
                if ch == "#":
                    m[y, x + i + off] = True
        x += len(g[0]) + 2
    return m


def render(word, take, faded=False):
    m = word_mask(word)
    h, w = m.shape
    pad = 3
    big = np.zeros((h + pad * 2, w + pad * 2), bool)
    big[pad:pad + h, pad:pad + w] = m

    def grow(a):
        g = a.copy()
        g[1:, :] |= a[:-1, :]; g[:-1, :] |= a[1:, :]; g[:, 1:] |= a[:, :-1]; g[:, :-1] |= a[:, 1:]
        return g

    outline = grow(big)
    shadow = np.zeros_like(outline)
    shadow[1:, 1:] = outline[:-1, :-1]
    out = np.zeros(big.shape + (4,), np.uint8)
    ramp = [c for _, c in RAMPS[take]]
    out[shadow & ~outline] = rgba(ramp[6]) if not faded else rgba("3b3346")
    out[outline] = rgba("000000")
    # fill: white top rows, the ramp's light then mid towards the bottom; the inner rim in the deep tone
    inner_rim = big & ~(np.roll(big, 1, 0) & np.roll(big, -1, 0) & np.roll(big, 1, 1) & np.roll(big, -1, 1))
    for y in range(big.shape[0]):
        k = (y - pad) / 8.0
        col = ramp[0] if k < 0.3 else (ramp[1] if k < 0.55 else (ramp[2] if k < 0.8 else ramp[3]))
        if faded:
            col = "9badb7" if k < 0.5 else "847e87"
        out[y][big[y]] = rgba(col)
    return Image.fromarray(out, "RGBA")


def sheet(take):
    """One cell a syllable, 96x16, left-aligned at x 0 and baseline-aligned: SHIN, KU, HA, DO, KEN!!!!, and a
    deflated 'KEN...' for the fail."""
    words = [render(wd, take) for wd in WORDS] + [render("KEN...", take, faded=True)]
    cells = []
    for im in words:
        c = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        c.alpha_composite(im, (0, 0))
        cells.append(c)
    return strip(cells)


if __name__ == "__main__":
    for take in "ab":
        zoomed(sheet(take), 4, (20, 14, 34, 255)).save(WORK + "/shout_%s.png" % take)
