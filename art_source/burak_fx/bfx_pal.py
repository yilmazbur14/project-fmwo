"""Palette and grid helpers for Captain Burak's effects (Assets/Characters/BurakBoss/FX/).

Every colour is measured from his approved sheet, Assets/Characters/BurakBoss/burak_boss.png:
  gold         the trim and the approved shot's baked flash: #FFF3B0 #F5D94E #E0AB35 #B07D22 #7A5216
  smoke white  the approved shot's baked smoke and his shirt: #FFFCF4 #E8E1D3 #C3B9A9
  iron, steel  the cutlass, the tricorn and the approved baked ball: #DCE3EE #A6AFC1 #6D7589 #4E4F66
               #444A5C #353547 #23232F #15151D
  crimson      the coat: #D95763 #D8434F #B02436 #AC3232 #7E162B #6E1F22 #4A0C1B
  wood         the flintlock's walnut stock and the warm browns of his ramp: #E2A874 #D79864 #BE8254
               #AC714F #A88068 #7C5438 #5C3B28 #503729 #36251E #2A1D19 #281810
Effects carry no keyline; the darkest tone of a ramp does the edge work. Hard edges, no dither; partial
alpha only in fixed steps.

A frame is a list of equal-length rows, one key per texel, '.' for clear. A frame may carry its own extra
keys (Frame, below).
"""
from PIL import Image


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


PAL = {
    # gold, hot to dark
    'Q': hx('FFF3B0'), 'Y': hx('F5D94E'), 'G': hx('E0AB35'), 'g': hx('B07D22'), 'h': hx('7A5216'),
    # smoke whites
    'W': hx('FFFCF4'), 'w': hx('E8E1D3'), 'c': hx('C3B9A9'),
    # iron and steel, light to dark
    'S': hx('DCE3EE'), 's': hx('A6AFC1'), 'i': hx('6D7589'), 'I': hx('4E4F66'), 'j': hx('444A5C'),
    'k': hx('353547'), 'K': hx('23232F'), 'x': hx('15151D'),
    # crimson, light to dark
    '1': hx('D95763'), '2': hx('D8434F'), '3': hx('B02436'), '4': hx('AC3232'), '5': hx('7E162B'),
    '6': hx('6E1F22'), '7': hx('4A0C1B'),
    # wood, light to dark
    'e': hx('E2A874'), 'E': hx('D79864'), 'f': hx('BE8254'), 'F': hx('AC714F'), 'd': hx('A88068'),
    'D': hx('7C5438'), 'n': hx('5C3B28'), 'N': hx('503729'), 'o': hx('36251E'), 'O': hx('2A1D19'),
    'p': hx('281810'),
}


class Frame(list):
    """A frame (a list of rows) that carries its own extra palette keys."""
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


def transpose(frame):
    h, w = len(frame), len(frame[0])
    out = [''.join(frame[y][x] for y in range(h)) for x in range(w)]
    return Frame(out, frame.palette) if isinstance(frame, Frame) else out


def flip_h(frame):
    out = [r[::-1] for r in frame]
    return Frame(out, frame.palette) if isinstance(frame, Frame) else out


def flip_v(frame):
    out = list(frame[::-1])
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
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'texels': len(px), 'colours': len(set(px)), 'alphas': sorted(set(c[3] for c in px)),
            'black%': round(100.0 * black / max(1, len(px)), 2)}
