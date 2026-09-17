"""Shared helpers for the defense / hype art (stamina, hype meter, popups, parry & guard-break FX).
Pure python (no PIL). DB32 only for UI/FX; the player's own 7 colours for player frames. Alpha 0/255."""
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import Canvas, from_png, strip, save_zoom, hex2rgb, DB32, DB32_HEX, PLAYER, PLAYER_SET
from pngio import read_png, write_png

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
GODOT = 'C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe'
HERE = os.path.dirname(os.path.abspath(__file__)).replace(os.sep, '/')
# scratch output never goes into the project: override with DH_WORK / DH_PREVIEWS
import tempfile
WORK = (os.environ.get('DH_WORK') or os.path.join(tempfile.gettempdir(), 'fmwo_defense_hype_work')).replace(os.sep, '/')
PREVIEWS = (os.environ.get('DH_PREVIEWS') or WORK + '/previews').replace(os.sep, '/')
os.makedirs(WORK, exist_ok=True)
os.makedirs(PREVIEWS, exist_ok=True)


def work(name):
    return WORK.rstrip('/') + '/' + name


# DB32, one letter each
C = {
    'K': '000000', 'n': '222034', 'p': '45283c', 'r': '663931', 'R': '8f563b', 'O': 'df7126',
    'T': 'd9a066', 'S': 'eec39a', 'Y': 'fbf236', 'l': '99e550', 'g': '6abe30', 'G': '37946e',
    'v': '4b692f', 'o': '524b24', 'q': '323c39', 'I': '3f3f74', 'u': '306082', 'B': '5b6ee1',
    'b': '639bff', 'C': '5fcde4', 'P': 'cbdbfc', 'W': 'ffffff', 's': '9badb7', 'h': '847e87',
    'j': '696a6a', 'k': '595652', 'V': '76428a', 'E': 'ac3232', 'e': 'd95763', 'm': 'd77bba',
    'x': '8f974a', 'D': '8a6f30',
}
assert set(C.values()) == DB32 and len(C) == 32

# the player's own colours (player_4dir_sheet.png), as used in that sheet's text dumps
PC = {'b': 'd79864', 'd': 'ac714f', 'c': '000000', 'e': 'ac3232', 'a': '2464bd', 'f': '162fbb', 'g': '3883c9'}
PC_INV = {v: k for k, v in PC.items()}


def grid(rows, pal=C, skip='.'):
    """list of equal-length strings -> Canvas"""
    w = max(len(r) for r in rows)
    c = Canvas(w, len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == skip or ch == ' ':
                continue
            if ch not in pal:
                raise KeyError('char %r not in palette (row %d col %d)' % (ch, y, x))
            c.p[y][x] = pal[ch]
    return c


def stamp(c, rows, x0, y0, pal=C, skip='.'):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == skip or ch == ' ':
                continue
            c.set(x0 + i, y0 + j, pal[ch])


def to_rows(c, pal=C):
    inv = {v: k for k, v in pal.items()}
    return [''.join(inv[v] if v else '.' for v in row) for row in c.p]


def crop(c, x0, y0, w, h):
    o = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            o.p[y][x] = c.get(x0 + x, y0 + y)
    return o


def cell(src, i, w, h, row=0):
    return crop(src, i * w, row * h, w, h)


def flip_h(c):
    o = Canvas(c.w, c.h)
    o.p = [list(reversed(r)) for r in c.p]
    return o


def scale3(c):
    o = Canvas(c.w * 3, c.h * 3)
    for y in range(o.h):
        for x in range(o.w):
            o.p[y][x] = c.p[y // 3][x // 3]
    return o


def recolor(c, mapping):
    o = c.copy()
    for y in range(c.h):
        for x in range(c.w):
            v = c.p[y][x]
            if v in mapping:
                o.p[y][x] = mapping[v]
    return o


def grid_sheet(frames_rows):
    """frames_rows: list of rows, each a list of equal-size canvases -> one sheet"""
    fw, fh = frames_rows[0][0].w, frames_rows[0][0].h
    cols = max(len(r) for r in frames_rows)
    s = Canvas(fw * cols, fh * len(frames_rows))
    for j, row in enumerate(frames_rows):
        for i, f in enumerate(row):
            assert (f.w, f.h) == (fw, fh)
            s.blit(f, i * fw, j * fh)
    return s


def nine_slice_problems(c, l, t, r, b):
    """left/right margin columns constant down the centre rows; top/bottom margin rows constant across the
    centre columns; centre one flat colour."""
    probs = []
    for y in list(range(t)) + list(range(c.h - b, c.h)):
        vals = {c.p[y][x] for x in range(l, c.w - r)}
        if len(vals) != 1:
            probs.append('row %d not uniform across the centre columns' % y)
    for x in list(range(l)) + list(range(c.w - r, c.w)):
        vals = {c.p[y][x] for y in range(t, c.h - b)}
        if len(vals) != 1:
            probs.append('col %d not uniform down the centre rows' % x)
    centre = {c.p[y][x] for y in range(t, c.h - b) for x in range(l, c.w - r)}
    if len(centre) != 1:
        probs.append('centre not flat: %s' % centre)
    return probs


def check_colours(c, allowed, name=''):
    bad = c.colours() - set(allowed)
    assert not bad, (name, bad)


def zoom_png(c, path, s, bg=(70, 70, 90), grid_wh=None):
    save_zoom(c, path, s, bg=bg, grid=grid_wh)


def bbox(c):
    xs = [x for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    ys = [y for y in range(c.h) for x in range(c.w) if c.p[y][x]]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)
