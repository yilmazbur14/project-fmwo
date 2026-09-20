"""Every boss bust, built by the crop-scale-rim method. One table, one builder.

Each entry names the source frame, the crop taken around that character's own
centreline, the integer scale that makes them fill a 116x120 bust, and where to
paste it. Pairs list two layers, back one first.

Scale is chosen per character from their source size, not fixed: Eric, Greyson,
Computah, Mason, Josh, Carter and Liam crop at 2x; Danny and Bixby have large
sheets and crop at 1x; Jordan is a narrow 28px figure and crops at 3x.

Burak is NOT here - his sprite's figure is 15x25, which would need 5x, and 5x
blocks are not art. He is the one deliberate redraw, and the brief to raise him
above his 7-colour sheet is an art-direction decision, not a fallback.
"""
import sys, os, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import bustkit as K

# key: (source, frame box, crop, scale, paste-at) | pairs: list of layers
TABLE = {
    "eric":     [("Eric/eric_sheet_v2.png", (57, 40, 164, 192), (41, 75, 99, 135), 2, (0, 0))],
    # Computah behind at the same 2x, Greyson in front and lower - depth comes
    # from the overlap, not from shrinking one of them.
    "greyson":  [("Computah/computah_idle.png", (0, 0, 64, 64), (8, 0, 48, 60), 2, (52, 0)),
                 ("Greyson/greyson_idle.png", (0, 0, 64, 96), (10, 0, 58, 52), 2, (0, 16))],
    "mason":    [("Mason/mason.png", None, (0, 0, 58, 60), 2, (0, 0))],
    "josh":     [("Josh/josh_idle.png", (0, 0, 64, 80), (0, 2, 54, 62), 2, (4, 0))],
    "danny":    [("Danny/Sumo/danny_sumo_idle.png", (0, 0, 176, 144), (27, 0, 143, 120), 1, (0, 0))],
    "carter":   [("Carter/carter_akuma.png", (0, 0, 96, 96), (1, 0, 59, 60), 2, (0, 0))],
    # The beast IS the fight by the time you get here, so it takes the frame and
    # Liam rides small at the bottom-left. Both at 1x, so the pixel size matches.
    "liam":     [("Bixby/bixby_beast.png", (0, 0, 192, 160), (44, 0, 160, 120), 1, (0, 0)),
                 ("Liam/liam.png", None, (14, 0, 44, 46), 1, (2, 72))],
    "jordan":   [("Jordan/jordan.png", None, (0, 0, 28, 40), 3, (16, 0))],
}

# Tones deliberately added past what the sheet holds, where a source is too thin
# to carry a bust. Same decision as Burak's: match the character exactly, raise
# the density.
EXTRA = {
    "computah": ["#E8F4FF", "#7A8CA4"],
    "jordan": ["#F6E2C4", "#C0A078"],
}


def auto_groups(cols, keyline):
    """Cluster a sheet's palette into materials by hue so rim_all can light each
    one with its own tones. Sixteen buckets keeps skin and orange hair apart,
    which a coarser split does not."""
    out = {}
    for c in cols:
        if c == keyline:
            continue
        r, g, b = K._rgb(c)
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        if l < 0.10:
            continue
        key = "grey" if s < 0.14 else int(h * 16)
        out.setdefault(key, []).append(c)
    return [v for v in out.values() if len(v) >= 2]


def make(key, detail=None):
    layers = TABLE[key]
    im = Image.new("RGBA", (K.W, K.H), (0, 0, 0, 0))
    pal, srcs = set(), []
    for path, box, crop, scale, at in layers:
        src = K.frame(path, box)
        srcs.append(src)
        pal |= set(K.palette_of(src))
        K.place(im, src, crop, scale, at)
    keyline = K.keyline_of(srcs[-1])
    K.rim_all(im, auto_groups(sorted(pal), keyline))
    if detail:
        detail(im)
    return K.lock(im, sorted(pal | set(EXTRA.get(key, []))))


def source_for(key):
    """The frame a bust is measured against - the front layer of a pair."""
    path, box = TABLE[key][-1][0], TABLE[key][-1][1]
    return K.frame(path, box)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for k in TABLE:
        b = make(k)
        K.measure(k, b, source_for(k))
        b.save(os.path.join(out, "bust_%s.png" % k))
