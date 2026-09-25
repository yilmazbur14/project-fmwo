"""Palette and grid helpers for Matt's attack effects (Assets/Characters/Matt/FX/).

Where every colour comes from (none is invented):
  Mystic cyan    the plan's art contract (matt_plan.md 4.3): #FFFFFF #D2FAFF #6EF0FF #22C3E8 #0E7FB0,
                 and #0A4E78 for the far wisps only
  Trueshot gold  the same contract: leading edge #FFFFF0 / #FFF3A8, body #FFCB3C -> #F2A51E, fading to
                 #C87414 toward the inner curve in 3 alpha steps
  Matt lavender  measured from the approved matt.png: the shirt ramp #332F68 #4F4D96 #6D6FBC #8E91DA
                 #B3B6F2 #DCDEFF, and frame 1's baked sound rings #F2F3FF (core) #C4C9FA (flanks)
                 #4F4D96 (edge)
  Matt yellow    measured from matt.png's hair tips, collar and belt: #6A4618 #AC7C26 #E2B13C #F8DB66
                 #FFF6BE

Effects carry no keyline. Edges are hard, there is no dither, and the only partial alpha is a few fixed
steps (the keys below whose alpha is under 255), never a soft gradient.

A frame is a list of equal-length rows, one key per texel, '.' for clear.
"""
from PIL import Image


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


PAL = {
    # ground shadow: solid black, as the project's other shadows (bixby_beast_shadow*.png); the code
    # supplies the translucency with modulate
    'k': hx('000000'),
    # Mystic Shot cyan, hot to cool
    'W': hx('FFFFFF'),
    'D': hx('D2FAFF'),
    'C': hx('6EF0FF'),
    'B': hx('22C3E8'),
    'R': hx('0E7FB0'),
    'F': hx('0A4E78'),          # far wisps only
    # Trueshot gold, hot to cool
    'H': hx('FFFFF0'),
    'Y': hx('FFF3A8'),
    'G': hx('FFCB3C'),
    'O': hx('F2A51E'),
    'A': hx('C87414'),
    'a': hx('C87414', 176),     # the inner-curve fade: 3 alpha steps of #C87414
    'b': hx('C87414', 112),
    'c': hx('C87414', 56),
    # Matt's lavender (shirt ramp) and ring colours
    'l': hx('332F68'),
    'm': hx('4F4D96'),
    'n': hx('6D6FBC'),
    'o': hx('8E91DA'),
    'p': hx('B3B6F2'),
    'q': hx('DCDEFF'),
    'r': hx('C4C9FA'),
    's': hx('F2F3FF'),
    # Matt's yellow (hair tips, collar, belt)
    't': hx('6A4618'),
    'u': hx('AC7C26'),
    'v': hx('E2B13C'),
    'w': hx('F8DB66'),
    'x': hx('FFF6BE'),
    # Glass Row (matt_plan_glass.md 6.3): the glass ramp (with 'W' #FFFFFF at its top), and the shards'
    # floor shadow
    'E': hx('E6FBFF'),
    'I': hx('B8ECF5'),
    'J': hx('7FC9DB'),
    'K': hx('4D8FA6'),
    'S': hx('1B1638'),
    # dust, measured from the shipped card_giant_impact.png plume (Josh), light to dark
    '1': hx('FBF7EE'),
    '2': hx('EDE4D6'),
    '3': hx('C7BBAB'),
    '4': hx('948779'),
    '5': hx('6B6157'),
}


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def rows(grid):
    return [''.join(r) for r in grid]


def put(grid, x, y, k):
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = k


def transpose(frame):
    """Swap x and y. A heading of t degrees (Godot angles, y down) becomes 90 - t."""
    h, w = len(frame), len(frame[0])
    return [''.join(frame[y][x] for y in range(h)) for x in range(w)]


def flip_h(frame):
    return [r[::-1] for r in frame]


def flip_v(frame):
    return list(frame[::-1])


def to_image(frame, palette=None):
    """A frame as RGBA. A frame may carry its own palette (a dict of extra keys), used before PAL."""
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


class Frame(list):
    """A frame (a list of rows) that carries its own extra palette keys."""
    def __init__(self, rows, palette):
        super().__init__(rows)
        self.palette = palette


def sheet(frames_by_row):
    """Rows of frames (each a list of strings, all one size) as one sheet image, frame 0 top left."""
    fh, fw = len(frames_by_row[0][0]), len(frames_by_row[0][0][0])
    cols = max(len(r) for r in frames_by_row)
    im = Image.new('RGBA', (fw * cols, fh * len(frames_by_row)), (0, 0, 0, 0))
    for j, row in enumerate(frames_by_row):
        for i, fr in enumerate(row):
            assert len(fr) == fh and all(len(s) == fw for s in fr), 'frame %d,%d is not %dx%d' % (i, j, fw, fh)
            im.paste(to_image(fr), (i * fw, j * fh))
    return im


def strip(frames):
    """One horizontal strip (hframes = len(frames), vframes = 1)."""
    return sheet([frames])


def pixels(im):
    im = im.convert('RGBA')
    flat = getattr(im, 'get_flattened_data', None)
    return list(flat() if flat else im.getdata())


def stats(im):
    """Opaque texels, distinct colours (RGBA), alpha levels and pure-black share of an image."""
    px = [c for c in pixels(im) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'texels': len(px), 'colours': len(set(px)), 'alphas': sorted(set(c[3] for c in px)),
            'black%': round(100.0 * black / max(1, len(px)), 2)}


def keys_used(frames):
    used = set()
    for fr in frames:
        for r in fr:
            used.update(r)
    used.discard('.')
    return used
