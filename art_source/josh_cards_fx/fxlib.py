"""Shared toolkit for Josh's card props and effects.

Pure python (no PIL).  Alpha is always 0 or 255.  The palette is Josh's own deck palette
(lifted from art_source/josh_cards/jlib.py so the props match the boss sprite exactly) plus
the DB32 brass ramp used by Assets/UI for the HUD status icons.

A "canvas" here is a list of rows of single-char palette keys, '.' = transparent.
"""
import math, os, subprocess, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, blank, paste

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
OUT = PROJ + 'Assets/Characters/Josh/Cards/'


def work_dir():
    import tempfile
    d = (os.environ.get('JFX_WORK')
         or os.path.join(tempfile.gettempdir(), 'josh_cards_fx_work')).replace(os.sep, '/')
    os.makedirs(d, exist_ok=True)
    return d


WORK = work_dir()


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# --------------------------------------------------------------------------- palette
# Josh's deck colours are verbatim from art_source/josh_cards/jlib.py.
PAL = {
    '#': hx('000000'),
    # card stock / cream  (Josh's duster + card faces)
    'n': hx('fbf7ee'), 'N': hx('ede4d6'), 'u': hx('c7bbab'), 'U': hx('948779'),
    'i': hx('6b6157'), 'I': hx('3e3830'),
    # reds (cap crown, gloves, pips)
    'L': hx('48141c'), 'q': hx('6e1e22'), 'Q': hx('ac3232'), 'R': hx('d95763'), 'E': hx('ef8a90'),
    # gold card magic
    'Y': hx('fff7a0'), 'F': hx('fbf236'), 'D': hx('f2c457'), 'A': hx('c48a2c'),
    'K': hx('8a5a1c'), 'S': hx('f58a38'), 'l': hx('5a4a3a'),
    # blacks / neutrals
    'x': hx('111117'), 'X': hx('22222b'), 'v': hx('383845'), 'V': hx('5a5a6a'), 'z': hx('8d8da0'),
    'w': hx('ffffff'),
    # --- new for the phase-2 special cards -------------------------------
    # sickly drain green
    'j': hx('1e2c18'), 'J': hx('2c4020'), 'g': hx('4b692f'), 'G': hx('7a9b33'),
    'h': hx('a8c94a'), 'H': hx('d6ec8e'),
    # clean "safe" green
    'c': hx('37946e'), 'C': hx('6abe30'), 'e': hx('99e550'),
    # inverse purple
    'm': hx('2a1338'), 'M': hx('4a1f5e'), 'p': hx('76428a'), 'P': hx('a862c0'),
    'o': hx('d79bba'), 'O': hx('f0c4e8'),
    # --- DB32 brass, verbatim from Assets/UI -----------------------------
    'b': hx('524b24'), 'B': hx('8a6f30'), 't': hx('d9a066'), 'T': hx('fbf236'),
    'd': hx('222034'), 'f': hx('3f3f74'), 'k': hx('eec39a'),
    # arena mat (previews only, never shipped inside a sprite)
    '1': hx('719850'), '2': hx('88b463'),
}
TRANSPARENT = (0, 0, 0, 0)

GOLD = ['K', 'A', 'D', 'F', 'Y', 'w']            # dark -> light
CREAM = ['I', 'i', 'U', 'u', 'N', 'n']           # dark -> light
RED = ['L', 'q', 'Q', 'R', 'E']
DRAIN = ['j', 'J', 'g', 'G', 'h', 'H']
PURPLE = ['m', 'M', 'p', 'P', 'o', 'O']


# --------------------------------------------------------------------------- canvas
class Cv(object):
    def __init__(self, w, h, fill='.'):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def copy(self):
        o = Cv(self.w, self.h)
        o.p = [r[:] for r in self.p]
        return o

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x, y):
        return self.p[y][x] if self.inb(x, y) else '.'

    def set(self, x, y, ch):
        if self.inb(x, y) and ch is not None:
            self.p[y][x] = ch

    def blit(self, src, ox, oy):
        for y in range(src.h):
            for x in range(src.w):
                if src.p[y][x] != '.':
                    self.set(ox + x, oy + y, src.p[y][x])

    def colours(self):
        return {c for r in self.p for c in r if c != '.'}

    def rgba(self):
        return [[PAL[c] if c != '.' else TRANSPARENT for c in r] for r in self.p]

    def save(self, path):
        write_png(path, self.w, self.h, self.rgba())

    def bbox(self):
        xs = [x for y in range(self.h) for x in range(self.w) if self.p[y][x] != '.']
        ys = [y for y in range(self.h) for x in range(self.w) if self.p[y][x] != '.']
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)


def sheet(frames, cols=None):
    """Horizontal strip (or grid when cols is given) of equal-size canvases."""
    fw, fh = frames[0].w, frames[0].h
    cols = cols or len(frames)
    rows = (len(frames) + cols - 1) // cols
    s = Cv(fw * cols, fh * rows)
    for i, f in enumerate(frames):
        assert (f.w, f.h) == (fw, fh), 'frame %d is %dx%d, expected %dx%d' % (i, f.w, f.h, fw, fh)
        s.blit(f, (i % cols) * fw, (i // cols) * fh)
    return s


# --------------------------------------------------------------------------- outline
def outline(c, col='#', diag=True):
    """1px pure-black outline around every opaque island, drawn outside the art."""
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diag:
        nb += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    add = []
    for y in range(c.h):
        for x in range(c.w):
            if c.p[y][x] != '.':
                continue
            for dx, dy in nb:
                if c.get(x + dx, y + dy) not in ('.', col):
                    add.append((x, y))
                    break
    for x, y in add:
        c.p[y][x] = col
    return c


def inner_outline(c, col='#', diag=True):
    """Outline drawn INSIDE the silhouette - keeps the sprite's footprint exactly."""
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diag:
        nb += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    add = []
    for y in range(c.h):
        for x in range(c.w):
            if c.p[y][x] == '.':
                continue
            for dx, dy in nb:
                nx, ny = x + dx, y + dy
                if not c.inb(nx, ny) or c.p[ny][nx] == '.':
                    add.append((x, y))
                    break
    for x, y in add:
        c.p[y][x] = col
    return c


# --------------------------------------------------------------------------- shapes
def fill_poly(c, pts, ch):
    """Even-odd scanline fill of a closed polygon (list of float (x, y))."""
    if not pts:
        return c
    ys = [p[1] for p in pts]
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    n = len(pts)
    for y in range(max(0, y0), min(c.h, y1 + 1)):
        sy = y + 0.5
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= sy < by) or (by <= sy < ay):
                xs.append(ax + (sy - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(math.ceil(xs[i] - 0.5)), int(math.floor(xs[i + 1] - 0.5)) + 1):
                c.set(x, y, ch)
    return c


def disc(c, cx, cy, r, ch):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                c.set(x, y, ch)
    return c


def ring(c, cx, cy, r, thick, ch, over=None):
    for y in range(int(cy - r - thick) - 1, int(cy + r + thick) + 2):
        for x in range(int(cx - r - thick) - 1, int(cx + r + thick) + 2):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r - thick <= d <= r:
                if over is None or c.get(x, y) in over:
                    c.set(x, y, ch)
    return c


def line(c, x0, y0, x1, y1, ch):
    n = max(abs(x1 - x0), abs(y1 - y0))
    if n == 0:
        c.set(int(x0), int(y0), ch)
        return c
    for i in range(int(n) + 1):
        t = i / float(n)
        c.set(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), ch)
    return c


def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c.set(x, y, ch)
    return c


# --------------------------------------------------------------------------- pips
SPADE = [
    '.......#.......',
    '......###......',
    '.....#####.....',
    '....#######....',
    '...#########...',
    '..###########..',
    '.#############.',
    '###############',
    '###############',
    '###############',
    '.#############.',
    '..####.#.####..',
    '.......#.......',
    '......###......',
    '.....#####.....',
    '....#######....',
    '.....#####.....',
]
SPADE_S = [
    '..#..',
    '.###.',
    '#####',
    '#####',
    '#.#.#',
    '..#..',
    '.###.',
]
SPADE_T = [
    '.#.',
    '###',
    '###',
    '.#.',
]


def stamp(c, art, x0, y0, ch, on='1#'):
    for j, row in enumerate(art):
        for i, s in enumerate(row):
            if s in on:
                c.set(x0 + i, y0 + j, ch)
    return c


def scaled_art(art, sx, sy=None):
    sy = sy or sx
    out = []
    for row in art:
        r = ''.join(ch * sx for ch in row)
        for _ in range(sy):
            out.append(r)
    return out


# --------------------------------------------------------------------------- noise
def hashf(x, y, seed=0):
    """Deterministic 0..1 value noise - no RNG, so every rebuild is byte-identical."""
    h = (x * 374761393 + y * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def ramp_pick(ramp, t):
    i = int(t * len(ramp))
    return ramp[max(0, min(len(ramp) - 1, i))]


# --------------------------------------------------------------------------- aseprite
LUA = r'''
local specPath = app.params["spec"]
local lines = {}
for line in io.lines(specPath) do
  if #line > 0 then table.insert(lines, line) end
end
local function split(s, sep)
  local out = {}
  for piece in string.gmatch(s, "([^" .. sep .. "]+)") do table.insert(out, piece) end
  return out
end
local head = split(lines[1], "|")
local outPath, W, H = head[1], tonumber(head[2]), tonumber(head[3])
local layerNames = split(lines[2], ",")
local spr = Sprite(W, H, ColorMode.RGB)
local layers = {}
layers[1] = spr.layers[1]
layers[1].name = layerNames[1]
for i = 2, #layerNames do
  local l = spr:newLayer()
  l.name = layerNames[i]
  layers[i] = l
end
local frameLines, tagLines = {}, {}
for i = 3, #lines do
  if string.sub(lines[i], 1, 4) == "TAG|" then table.insert(tagLines, lines[i])
  else table.insert(frameLines, lines[i]) end
end
for f, fl in ipairs(frameLines) do
  local parts = split(fl, "|")
  local frame
  if f == 1 then frame = spr.frames[1] else frame = spr:newEmptyFrame() end
  frame.duration = tonumber(parts[1]) / 1000.0
  for li = 1, #layerNames do
    local p = parts[li + 1]
    if p and p ~= "-" then
      spr:newCel(layers[li], frame, Image{ fromFile = p }, Point(0, 0))
    end
  end
end
for _, tl in ipairs(tagLines) do
  local parts = split(tl, "|")
  local tag = spr:newTag(tonumber(parts[3]), tonumber(parts[4]))
  tag.name = parts[2]
end
spr:saveAs(outPath)
spr:close()
'''


def build_ase(out_path, frames, durations, tags=(), layer='art'):
    """One layer, N frames, per-frame durations (ms) and optional (name, from, to) tags.

    Frames are written as individual PNGs and imported by an Aseprite batch script - importing
    each frame as its own cel is the only reliable way to get a real multi-frame .aseprite.
    """
    key = os.path.splitext(os.path.basename(out_path))[0]
    tmp = WORK + '/ase_' + key
    os.makedirs(tmp, exist_ok=True)
    lines = ['%s|%d|%d' % (out_path, frames[0].w, frames[0].h), layer]
    for i, (c, d) in enumerate(zip(frames, durations)):
        if not c.colours():
            lines.append('%d|-' % d)
            continue
        fp = '%s/f%02d.png' % (tmp, i)
        c.save(fp)
        lines.append('%d|%s' % (d, fp))
    for name, a, b in tags:
        # Aseprite's newTag() is 1-BASED; passing our 0-based indices straight through silently
        # shifts every tag down a frame and swallows the last one.
        lines.append('TAG|%s|%d|%d' % (name, a + 1, b + 1))
    spec = tmp + '/spec.txt'
    open(spec, 'w').write('\n'.join(lines) + '\n')
    r = subprocess.run([ASEPRITE, '-b', '--script-param', 'spec=' + spec, '--script', lua_path()],
                       capture_output=True, text=True)
    if not os.path.exists(out_path):
        raise SystemExit('aseprite failed for %s\n%s\n%s' % (out_path, r.stdout, r.stderr))
    return out_path


def lua_path():
    p = WORK + '/make_ase.lua'
    open(p, 'w').write(LUA)
    return p


def check_png(path, allowed=None):
    """Alpha must be 0/255 and every colour must come from our palette."""
    w, h, px = read_png(path)
    alphas = {p[3] for row in px for p in row}
    assert alphas <= {0, 255}, ('partial alpha in ' + path, sorted(alphas))
    used = {'%02x%02x%02x' % p[:3] for row in px for p in row if p[3] == 255}
    ok = {'%02x%02x%02x' % PAL[k][:3] for k in (allowed or PAL)}
    assert used <= ok, (path, sorted(used - ok))
    return w, h


def save_zoom(c_or_path, dst, f, bg=(58, 62, 52, 255), checker=True):
    if isinstance(c_or_path, str):
        w, h, px = read_png(c_or_path)
    else:
        w, h, px = c_or_path.w, c_or_path.h, c_or_path.rgba()
    o = [[bg] * (w * f) for _ in range(h * f)]
    for y in range(h * f):
        for x in range(w * f):
            p = px[y // f][x // f]
            if p[3] == 0:
                if checker:
                    o[y][x] = (74, 78, 66, 255) if ((x // f) // 8 + (y // f) // 8) % 2 else bg
                else:
                    o[y][x] = bg
            else:
                o[y][x] = (p[0], p[1], p[2], 255)
    write_png(dst, w * f, h * f, o)
    return dst
