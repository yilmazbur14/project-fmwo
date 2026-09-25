"""Palette and grid helpers for beast Bixby's Inferno effects.

Every colour here is measured from approved or shipped Bixby art. None is invented:
  fire ramp      the approved redesign's throat fire (bixby_beast_redesign.png frame 2, rows 61-85),
                 ramp #2C0610 #9A2A10 #E0561A #FF8C2E #FFC45A #FFF2B0, plus the redesign's fur reds
                 r/t (#570C18, #B42424) where the flame needs a step the throat ramp lacks
  white-hot      #FFFFFF, the core of the old fire art (bixby_fire_trail.png, bixby_beast_firebreath.png)
  char / smoke   bixby_fire_scorch.png's four charcoals (#121016 #26222C #3A3542 #5C5868), which the
                 redesign's saddle ramp a/b/c/d matches within a few points
  air            the redesign's bone ramp (#74606E #B09A8E #E3D2BC #FFF6E6), for the inhale's streaks
  violet rim     the redesign's Hades rim (#7A5AAE #A98AE6)
  keyline        #000000, the redesign's and Mason's target's

A frame is a list of equal-length strings, one character per texel: a palette key, or '.' for clear.
"""
from PIL import Image


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


PAL = {
    'k': hx('000000'),
    # fire, hot to dark
    'W': hx('FFFFFF'),
    'Y': hx('FFF2B0'),
    'P': hx('FFC45A'),
    'p': hx('FF8C2E'),
    'N': hx('E0561A'),
    't': hx('B42424'),
    'n': hx('9A2A10'),
    'r': hx('570C18'),
    'q': hx('2C0610'),
    # char and smoke (the scorch's charcoals)
    'a': hx('121016'),
    'b': hx('26222C'),
    'c': hx('3A3542'),
    'd': hx('5C5868'),
    # violet rim
    'e': hx('7A5AAE'),
    'f': hx('A98AE6'),
    # air (bone)
    'z': hx('74606E'),
    'y': hx('B09A8E'),
    'x': hx('E3D2BC'),
    'w': hx('FFF6E6'),
}

# The fire ramp as a list, dark to hot, for anything that quantises a heat value.
FIRE = ['q', 'r', 'n', 'N', 'p', 'P', 'Y', 'W']


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def rows(grid):
    return [''.join(r) for r in grid]


def to_image(frame):
    """A frame (list of strings or list of lists) as an RGBA image."""
    h, w = len(frame), len(frame[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(frame):
        for x, k in enumerate(row):
            if k != '.':
                px[x, y] = PAL[k]
    return im


def sheet(frames_by_row):
    """Rows of frames (each a list of strings, all one size) as one sheet image."""
    fh, fw = len(frames_by_row[0][0]), len(frames_by_row[0][0][0])
    cols = max(len(r) for r in frames_by_row)
    im = Image.new('RGBA', (fw * cols, fh * len(frames_by_row)), (0, 0, 0, 0))
    for j, row in enumerate(frames_by_row):
        for i, fr in enumerate(row):
            assert len(fr) == fh and all(len(s) == fw for s in fr), 'frame %d,%d is not %dx%d' % (i, j, fw, fh)
            im.alpha_composite(to_image(fr), (i * fw, j * fh))
    return im


def stats(im):
    """Opaque texels, distinct colours, pure-black share and semi-alpha count of an image."""
    im = im.convert('RGBA')
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)),
            'black%': round(100.0 * black / max(1, len(px)), 2),
            'semi': sum(1 for c in px if c[3] < 255)}


def keys_used(frames):
    used = set()
    for fr in frames:
        for r in fr:
            used.update(r)
    used.discard('.')
    return used
