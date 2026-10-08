"""The rune circle: a separate layer that hangs behind him in the void and turns slowly. Cold cyan
light against his hot reds (the reference's key contrast). Effect art: no keyline, no semi-alpha.

Every element repeats every 60 degrees (a hexagram, 24 rune slots cycling 4 glyphs, 48 dots, 12
ticks with a major every 60), so turning it through 60 degrees is a seamless loop. Each frame is
drawn fresh at its angle (never a rotated bitmap), so the 1px lines stay clean instead of
stair-stepping. The runes are original marks built from radial and tangential strokes, so they
turn with the circle. Square, centred on its own pivot: (95.5, 95.5) is the circle's centre.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402

RUNE_PAL = {
    'd': B.hx('17385A'),     # dim
    'e': B.hx('2B6C99'),     # mid
    'f': B.hx('66C6EC'),     # bright
    'g': B.hx('D2F6FF'),     # hot
}

SIZE = 192
FRAMES = 36                  # one 60-degree loop, 1.67 degrees a frame
FRAME_TIME = 0.10            # seconds a frame: 60 degrees in 3.6 s, a full turn in 21.6 s

# glyphs in polar strokes: ((r0, a0), (r1, a1)) with r in texels from the band's middle radius
# and a in degrees from the slot's angle.
GLYPHS = [
    [((-4, 0), (4, 0)), ((0, -2.2), (0, 2.2))],                                   # a cross-barred stave
    [((-4, 0), (1, 0)), ((1, -2.0), (4, 0)), ((4, 0), (1, 2.0))],                 # an arrow
    [((-3, -2.0), (3, 0)), ((3, 0), (-3, 2.0)), ((-4, 0), (-4, 0))],              # a chevron and a dot
    [((-4, -1.6), (4, -1.6)), ((-4, 1.6), (4, 1.6)), ((0, -1.6), (0, 1.6))],      # twin staves, a rung
]


C0 = (SIZE - 1) / 2.0        # 95.5: the circle's centre falls between texels


def _snap(v, c=C0):
    """Round to a texel symmetrically about the centre (half-way cases round away from it), so the
    circle is exactly symmetric in its square instead of drifting half a texel."""
    return int(math.floor(v + 0.5)) if v >= c else int(math.ceil(v - 0.5))


def _pt(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def _line(out, p0, p1, key):
    for q in B.line(_snap(p0[0]), _snap(p0[1]), _snap(p1[0]), _snap(p1[1])):
        out[q] = key


def _dot(out, p, key):
    out[(_snap(p[0]), _snap(p[1]))] = key


def _ring(out, cx, cy, r, key):
    n = int(2 * math.pi * r * 1.6)
    for i in range(n):
        a = 2 * math.pi * i / n
        _dot(out, (cx + r * math.cos(a), cy + r * math.sin(a)), key)


def circle(angle=0.0, size=SIZE):
    """The circle turned `angle` degrees clockwise (screen), as {pixel: key}."""
    cx = cy = (size - 1) / 2.0
    out = {}
    R = size / 2.0 - 2
    _ring(out, cx, cy, R, 'g')
    _ring(out, cx, cy, R - 2, 'e')
    _ring(out, cx, cy, R - 13, 'f')
    # 48 dots on the inner edge of the band
    for i in range(48):
        _dot(out, _pt(cx, cy, R - 15, angle + i * 7.5), 'd')
    # the rune band: 24 slots, 4 glyphs repeating
    rb = R - 7.5
    for i in range(24):
        base = angle + i * 15.0 - 90.0
        for (r0, a0), (r1, a1) in GLYPHS[i % 4]:
            p0 = _pt(cx, cy, rb + r0, base + a0)
            p1 = _pt(cx, cy, rb + r1, base + a1)
            _line(out, p0, p1, 'f')
        # a hot fleck at each glyph's heart
        _dot(out, _pt(cx, cy, rb, base), 'g')
    # hexagram with a small ring at each point
    rh = R - 18
    pts = [_pt(cx, cy, rh, angle - 90 + 60 * i) for i in range(6)]
    for tri in ((0, 2, 4), (1, 3, 5)):
        for a_, b_ in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            _line(out, pts[a_], pts[b_], 'e')
    for (x, y) in pts:
        _ring(out, x, y, 4, 'f')
        _dot(out, (x, y), 'g')
    # the middle ring and its 12 ticks (a long one every 60 degrees)
    rm = R * 0.42
    _ring(out, cx, cy, rm, 'f')
    for i in range(12):
        long_ = i % 2 == 0
        r0, r1 = (rm - 5, rm + 5) if long_ else (rm - 2, rm + 2)
        _line(out, _pt(cx, cy, r0, angle + i * 30 - 90), _pt(cx, cy, r1, angle + i * 30 - 90), 'g' if long_ else 'e')
    _ring(out, cx, cy, R * 0.2, 'e')
    for i in range(24):
        _dot(out, _pt(cx, cy, R * 0.2 - 3, angle + i * 15), 'd')
    return {q: k for q, k in out.items() if 0 <= q[0] < size and 0 <= q[1] < size}


def frame_image(i, size=SIZE):
    return B.image(circle(60.0 * i / FRAMES, size), size, size, RUNE_PAL)


def image(size=SIZE):
    """Frame 0 on its own (the approval-pass still)."""
    return frame_image(0, size)


def strip(size=SIZE):
    from PIL import Image
    im = Image.new('RGBA', (size * FRAMES, size), (0, 0, 0, 0))
    for i in range(FRAMES):
        im.alpha_composite(frame_image(i, size), (i * size, 0))
    return im


if __name__ == '__main__':
    out = sys.argv[1]
    im = image()
    B.up(im, 3, bg=(8, 6, 16, 255)).save(os.path.join(out, 'runes_3x.png'))
    print(B.stats(im))
    # seamless check: a 60-degree turn lands back on frame 0
    from imgdiff import pixel_diff  # noqa: E402
    print('60-degree turn equals frame 0:', pixel_diff(B.image(circle(60.0), SIZE, SIZE, RUNE_PAL), im) or 'identical')
