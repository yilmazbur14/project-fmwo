"""Greyson's fight FX palette and the grid helpers every gfx_ module draws with.

Measured from his approved sprite (Assets/Characters/Greyson/greyson_redesign.png: 28 colours, pure black
keyline, 17.8% black) and from Computah's (whose purple cannon arm he now wears), except where noted:
  cannon violets (Computah's paint, Greyson's trunks)   V #C892F2  v #A063DC  U #7C3BB4  u #592687  X #391555
  Computah's darkest navy                               Z #0C111A
  whites and chalk (Computah's)                         W #FFFFFF  w #F2F8FF  E #CEDCEA  e #A6B8CC  f #8091A8
  steel and iron (Greyson's boot greys, Computah's)     S #D5D9EC  s #9DA1C0  F #5E6C82  i #3F3F52  k #2A2A38
                                                        K #1A212C
  golds (Greyson's hair)                                Y #FFF1B4  y #F7D06A  G #E5A548  O #C27434
  reds (his forehead vein)                              r #D95763  R #9E3A48
Not measured from him:
  the crowd's energy, for the spirit bomb and his hype cells (the Genki Dama brief: a white-hot core fading
  to pale blue, a saturated cyan rim):                  C #E6F7FF  c #B4DCFF  A #5FE1FF  a #2FA8E0
                                                        B #639BFF  b #2E5FB0  N #1E3566
  (#B4DCFF, #639BFF and #1E3566 are his eyes' blues)
  the mat's own greens, for cracks in the canvas (derived from the arena's #7EA85B #88B463 #759C54, as Danny's):
                                                        n #A2C882  m #5E8243  q #3A5227  Q #24341A
The cannon's violet is his power (eruptions, teleport); the crowd's cyan is what fuels the cannon (hype
cells, spirit bomb). Violet sits exactly opposite the mat's green (hue 272 against 92). FX draw no keyline:
the darkest tone of each ramp does the edge work. No dither; alpha is stepped.
"""
from PIL import Image


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


PAL = {
    'V': hx('C892F2'), 'v': hx('A063DC'), 'U': hx('7C3BB4'), 'u': hx('592687'), 'X': hx('391555'), 'Z': hx('0C111A'),
    'W': hx('FFFFFF'), 'w': hx('F2F8FF'), 'E': hx('CEDCEA'), 'e': hx('A6B8CC'), 'f': hx('8091A8'),
    'S': hx('D5D9EC'), 's': hx('9DA1C0'), 'F': hx('5E6C82'), 'i': hx('3F3F52'), 'k': hx('2A2A38'), 'K': hx('1A212C'),
    'Y': hx('FFF1B4'), 'y': hx('F7D06A'), 'G': hx('E5A548'), 'O': hx('C27434'),
    'r': hx('D95763'), 'R': hx('9E3A48'),
    'C': hx('E6F7FF'), 'c': hx('B4DCFF'), 'A': hx('5FE1FF'), 'a': hx('2FA8E0'), 'B': hx('639BFF'), 'b': hx('2E5FB0'),
    'N': hx('1E3566'),
    'n': hx('A2C882'), 'm': hx('5E8243'), 'q': hx('3A5227'), 'Q': hx('24341A'),
}


class Frame(list):
    """A frame (a list of rows) that carries its own extra palette keys (e.g. stepped-alpha variants)."""
    def __init__(self, rows, palette):
        super().__init__(rows)
        self.palette = palette


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def rows(grid):
    return [''.join(r) for r in grid]


def put(grid, x, y, k):
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = k


def flip_h(frame):
    out = [r[::-1] for r in frame]
    return Frame(out, frame.palette) if isinstance(frame, Frame) else out


def to_image(frame, palette=None):
    h, w = len(frame), len(frame[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    pal = dict(PAL)
    pal.update(palette or getattr(frame, 'palette', None) or {})
    for y, row in enumerate(frame):
        for x, k in enumerate(row):
            if k != '.':
                px[x, y] = pal[k]
    return im


def alpha_keys(keys, level, prefix_pool):
    """Frame-local stepped-alpha versions of `keys` at `level`, named from `prefix_pool` (unused chars).
    Returns (mapping key -> local key, local palette)."""
    m, local = {}, {}
    for k, nk in zip(keys, prefix_pool):
        c = PAL[k]
        m[k] = nk
        local[nk] = (c[0], c[1], c[2], level)
    return m, local


def sheet(frames_by_row):
    fh, fw = len(frames_by_row[0][0]), len(frames_by_row[0][0][0])
    cols = max(len(r) for r in frames_by_row)
    im = Image.new('RGBA', (fw * cols, fh * len(frames_by_row)), (0, 0, 0, 0))
    for j, row in enumerate(frames_by_row):
        for i, fr in enumerate(row):
            assert len(fr) == fh and all(len(s) == fw for s in fr), 'frame %d,%d is not %dx%d' % (i, j, fw, fh)
            im.paste(to_image(fr), (i * fw, j * fh))
    return im


def strip(frames):
    return sheet([frames])


def pixels(im):
    im = im.convert('RGBA')
    flat = getattr(im, 'get_flattened_data', None)
    return list(flat() if flat else im.getdata())


def stats(im):
    px = [c for c in pixels(im) if c[3] > 0]
    return {'texels': len(px), 'colours': len(set(px)), 'alphas': sorted(set(c[3] for c in px))}
