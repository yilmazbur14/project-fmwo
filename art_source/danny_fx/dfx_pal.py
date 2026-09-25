"""Danny's FX palette and the grid helpers every dfx_ module draws with.

Measured from his approved sumo sheets (Assets/Characters/Danny/Sumo/danny_sumo_*.png: 26 colours on a pure
black keyline, 16.4% black), except where noted:
  beanie / mawashi blues   W #FFFFFF  Q #F0F5FF  P #CBDBFC  L #97ABEF  M #7D90F0  B #5B6EE1  S #639BFF
                           N #3F3F74  V #222034  g #8595B8
  collar reds              r #D95763  R #AC3232  q #7A2430
  rope / chain golds       y #FFFBC4  Y #FBF236  G #F0B432  O #DF7126  h #8A4B1F
  skin and browns          e #FADCB8  E #EEC39A  f #D9A066  F #B67A4B  d #8F563B  D #663931  x #45283C
Not measured from him:
  the worms' own pinks     1 #FFD6D0  2 #F4A3A0  3 #DC7A80  4 #B55466  5 #7E3448, and the slime's mid dark
                           6 #58303F, set against the mat (hue 92, lightness 0.46-0.59): the worms sit about
                           100 degrees of hue off the green and well above it in value; their slime pool
                           (x 6 D, lightness 0.21-0.30) sits well below it, so a puddle is a dark stain with
                           bright wriggling on it
  the mat's own greens     n #A2C882  m #5E8243  k #3A5227  K #24341A, derived from the arena mat's measured
                           greens (#7EA85B #88B463 #759C54): a lifted torn edge catching the light, the dent's
                           shade, a crack, its depth
  heal greens              J #E4FFB8  j #99E550  i #37946E (#99E550 and #37946E are DB32's lime and teal,
                           like his palette): lime with a white heart and a dark teal edge, so a sparkle
                           still reads against the green mat
FX draw no keyline: the darkest tone of each ramp does the edge work. No dither; alpha is stepped.
"""
from PIL import Image


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


PAL = {
    'W': hx('FFFFFF'), 'Q': hx('F0F5FF'), 'P': hx('CBDBFC'), 'L': hx('97ABEF'), 'M': hx('7D90F0'),
    'B': hx('5B6EE1'), 'S': hx('639BFF'), 'N': hx('3F3F74'), 'V': hx('222034'), 'g': hx('8595B8'),
    'r': hx('D95763'), 'R': hx('AC3232'), 'q': hx('7A2430'),
    'y': hx('FFFBC4'), 'Y': hx('FBF236'), 'G': hx('F0B432'), 'O': hx('DF7126'), 'h': hx('8A4B1F'),
    'e': hx('FADCB8'), 'E': hx('EEC39A'), 'f': hx('D9A066'), 'F': hx('B67A4B'), 'd': hx('8F563B'),
    'D': hx('663931'), 'x': hx('45283C'),
    '1': hx('FFD6D0'), '2': hx('F4A3A0'), '3': hx('DC7A80'), '4': hx('B55466'), '5': hx('7E3448'),
    '6': hx('58303F'),
    'n': hx('A2C882'), 'm': hx('5E8243'), 'k': hx('3A5227'), 'K': hx('24341A'),
    'J': hx('E4FFB8'), 'j': hx('99E550'), 'i': hx('37946E'),
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
