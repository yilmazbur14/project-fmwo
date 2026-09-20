"""A condensed gothic capital set for the boss nameplates, hand-drawn.

WHY A HAND-DRAWN FACE AT ALL
The plate's name slot is NAME_MAX_W = 66 native px.  plates.fit_size() picks the
largest Pixelify size whose ink fits that, PER LINE - so on a pair the two lines
bake at different sizes and '& COMPUTAH' comes out at exactly 66px, touching the
border with no margin.  That is the reported overflow: not a clipped glyph, a
cramped line and a size mismatch between the two lines of the same name.

A 5x9 condensed face fixes both at once by being narrow enough that every line
of every boss name fits at ONE fixed size with room left over.  Fixed-width
glyphs also mean the plate can be laid out without measuring.

LICENCE.  Nothing is imported here - these glyphs are drawn for this project, so
there is no third-party licence to carry.  Of the two fonts we ship,
PixelifySans.ttf has its OFL licence beside it in fonts/; I-pixel-u.ttf has no
licence file in the repo, which needs resolving before it is used in shipped
art, since the repo is public.
"""
GLYPH_W, GLYPH_H, GAP = 5, 9, 1
SPACE_W = 3

_G = {
    "A": ".###. #...# #...# #...# ##### #...# #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# #...# #...# ####.",
    "C": ".#### #.... #.... #.... #.... #.... #.... #.... .####",
    "D": "####. #...# #...# #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... #.... ####. #.... #.... #.... #####",
    "F": "##### #.... #.... #.... ####. #.... #.... #.... #....",
    "G": ".#### #.... #.... #.... #..## #...# #...# #...# .####",
    "H": "#...# #...# #...# #...# ##### #...# #...# #...# #...#",
    "I": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. #####",
    "J": "..### ...#. ...#. ...#. ...#. ...#. #..#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... ##... #.#.. #..#. #...# #...#",
    "L": "#.... #.... #.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## ##.## #.#.# #.#.# #...# #...# #...# #...#",
    "N": "#...# ##..# ##..# #.#.# #.#.# #..## #..## #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# #...# ####. #.... #.... #.... #....",
    "Q": ".###. #...# #...# #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# #...# ####. #.#.. #..#. #..#. #...#",
    "S": ".#### #.... #.... #.... .###. ....# ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# #...# .#.#. .#.#. ..#..",
    "W": "#...# #...# #...# #...# #.#.# #.#.# ##.## ##.## #...#",
    "X": "#...# #...# .#.#. .#.#. ..#.. .#.#. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. .#.#. ..#.. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. ..#.. .#... #.... #.... #####",
    "&": ".##.. #..#. #..#. .##.. .##.. #..#. #.##. #..#. .##.#",
    "'": "..#.. ..#.. ..#.. ..... ..... ..... ..... ..... .....",
    "-": "..... ..... ..... ..... ##### ..... ..... ..... .....",
    "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#.. ..#..",
}
GLYPHS = {k: v.split(" ") for k, v in _G.items()}


def width(text):
    w = 0
    for i, ch in enumerate(text):
        if i:
            w += GAP
        w += SPACE_W if ch == " " else GLYPH_W
    return w


def render(text, fill=(255, 255, 255, 255), ink=None):
    """Bake a line.  `ink` adds a 1px black keyline under the letterforms, which
    is what lets a pale name sit on the plate's dark panel without fringing."""
    from PIL import Image
    text = text.upper()
    w, h = width(text), GLYPH_H
    pad = 1 if ink else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    px = im.load()
    cells = []
    x = 0
    for i, ch in enumerate(text):
        if i:
            x += GAP
        if ch == " ":
            x += SPACE_W
            continue
        g = GLYPHS.get(ch)
        if g:
            for gy, row in enumerate(g):
                for gx, c in enumerate(row):
                    if c == "#":
                        cells.append((x + gx, gy))
        x += GLYPH_W
    if ink:
        for cx, cy in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx + pad, cy + dy + pad
                    if 0 <= nx < im.width and 0 <= ny < im.height:
                        px[nx, ny] = ink
    for cx, cy in cells:
        px[cx + pad, cy + pad] = fill
    return im


if __name__ == "__main__":
    for t in ("ERIC", "GREYSON", "& COMPUTAH", "MASON", "JOSH", "DANNY",
              "CARTER", "LIAM", "& BIXBY", "JORDAN", "COMPUTAH", "BIXBY"):
        print("%-14s %3dpx  %s" % (t, width(t), "fits 66" if width(t) <= 66 else "OVER"))
