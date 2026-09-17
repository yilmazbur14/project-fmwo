"""Shared helpers for the Jordan funko figures: text-grid sprites, compositing, previews.

Paths (override with environment variables):
  FUNKO_PROJECT  Godot project root (auto-detected by walking up to project.godot)
  FUNKO_WORK     work dir for wip renders, per-frame PNGs and the arena render (default: <tmp>/jordan_funkos_work)
  FUNKO_PREVIEW  where previews/GIFs/mockups are written (default: <FUNKO_WORK>/previews/)
"""
import os
import tempfile
from pngio import read_png, write_png

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_project():
    d = HERE
    for _ in range(8):
        if os.path.exists(os.path.join(d, 'project.godot')):
            return d.replace(os.sep, '/') + '/'
        d = os.path.dirname(d)
    return 'C:/Users/theyi/OneDrive/Documents/new-game-project/'


def _dir(v):
    v = v.replace(os.sep, '/')
    return v if v.endswith('/') else v + '/'


PROJ = _dir(os.environ.get('FUNKO_PROJECT') or _find_project())
OUT_ASSETS = PROJ + 'Assets/Characters/Jordan/Funkos/'
WORK = _dir(os.environ.get('FUNKO_WORK') or os.path.join(tempfile.gettempdir(), 'jordan_funkos_work'))
SCRATCH = WORK
WIP = WORK + 'wip/'
PREVIEW = _dir(os.environ.get('FUNKO_PREVIEW') or WORK + 'previews/')
ARENA_FRAME = WORK + 'arena/frame00000002.png'
os.makedirs(WIP, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)

T = (0, 0, 0, 0)


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def grid(text, pal, w=None, h=None):
    """Parse a text grid (one char per pixel) with a char->hex palette. '.' and ' ' are transparent."""
    lines = [ln for ln in text.strip('\n').split('\n')]
    # strip common leading indentation marker '|' if used
    lines = [ln.split('|', 1)[1] if '|' in ln else ln for ln in lines]
    H = h or len(lines)
    W = w or max(len(ln) for ln in lines)
    out = [[T] * W for _ in range(H)]
    for y, ln in enumerate(lines[:H]):
        for x, ch in enumerate(ln[:W]):
            if ch in '. ':
                continue
            if ch not in pal:
                raise KeyError('char %r at (%d,%d) not in palette' % (ch, x, y))
            out[y][x] = hx(pal[ch]) if isinstance(pal[ch], str) else pal[ch]
    return out


def blank(w, h):
    return [[T] * w for _ in range(h)]


def size(px):
    return len(px[0]), len(px)


def paste(dst, src, ox, oy):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        yy = oy + y
        if not (0 <= yy < H):
            continue
        for x, p in enumerate(row):
            xx = ox + x
            if 0 <= xx < W and p[3] > 0:
                dst[yy][xx] = p
    return dst


def copy(px):
    return [list(r) for r in px]


def flip_h(px):
    return [list(reversed(r)) for r in px]


def rot90cw(px):
    h, w = len(px), len(px[0])
    return [[px[h - 1 - c][r] for c in range(h)] for r in range(w)]


def rot90ccw(px):
    h, w = len(px), len(px[0])
    return [[px[c][w - 1 - r] for c in range(h)] for r in range(w)]


def rot180(px):
    return [list(reversed(r)) for r in reversed(px)]


def recolor(px, mapping):
    """mapping: {rgba_tuple: rgba_tuple}"""
    return [[mapping.get(p, p) for p in r] for r in px]


def bbox(px):
    xs, ys = [], []
    for y, r in enumerate(px):
        for x, p in enumerate(r):
            if p[3] > 0:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def zoom(px, s, bg='checker', grid_lines=False):
    H, W = len(px), len(px[0])
    out = []
    for y in range(H):
        row = []
        for x in range(W):
            p = px[y][x]
            if p[3] == 0:
                if bg == 'checker':
                    c = 196 if ((x // 1 + y // 1) % 2 == 0) else 176
                    q = (c, c, c, 255)
                elif bg is None:
                    q = T
                else:
                    q = bg
            else:
                q = p
            cell = [q] * s
            if grid_lines and s >= 6:
                d = (max(0, q[0] - 22), max(0, q[1] - 22), max(0, q[2] - 22), 255)
                cell = [d] + [q] * (s - 1)
            row.extend(cell)
        for sy in range(s):
            if grid_lines and s >= 6 and sy == 0:
                out.append([(max(0, c[0] - 22), max(0, c[1] - 22), max(0, c[2] - 22), 255) for c in row])
            else:
                out.append(list(row))
    return out


ARENA_GREEN = (136, 180, 99, 255)


def save(px, path):
    w, h = size(px)
    write_png(path, w, h, px)


def hstack(frames, gap=0, bg=T):
    H = max(len(f) for f in frames)
    W = sum(len(f[0]) for f in frames) + gap * (len(frames) - 1)
    out = [[bg] * W for _ in range(H)]
    x = 0
    for f in frames:
        for yy, r in enumerate(f):
            for xx, p in enumerate(r):
                if p[3] > 0:
                    out[yy][x + xx] = p
        x += len(f[0]) + gap
    return out


def vstack(frames, gap=0, bg=T):
    W = max(len(f[0]) for f in frames)
    H = sum(len(f) for f in frames) + gap * (len(frames) - 1)
    out = [[bg] * W for _ in range(H)]
    y = 0
    for f in frames:
        for yy, r in enumerate(f):
            for xx, p in enumerate(r):
                if p[3] > 0:
                    out[y + yy][xx] = p
        y += len(f)
    return out


def fill_bg(px, bg):
    return [[p if p[3] > 0 else bg for p in r] for r in px]


def audit(px, name=''):
    """alpha only 0/255 check and colour count"""
    alphas = set(p[3] for r in px for p in r)
    cols = set(p[:3] for r in px for p in r if p[3] > 0)
    bad = alphas - {0, 255}
    print('%s: %d colours, alphas=%s %s' % (name, len(cols), sorted(alphas), 'BAD ALPHA' if bad else 'ok'))
    return not bad


def blit_scaled(dst, src, ox, oy, s):
    """paste src scaled by s with top-left at (ox, oy)"""
    H, W = len(src), len(src[0])
    DH, DW = len(dst), len(dst[0])
    for y in range(H):
        for x in range(W):
            p = src[y][x]
            if p[3] == 0:
                continue
            for yy in range(s):
                Y = oy + y * s + yy
                if not (0 <= Y < DH):
                    continue
                row = dst[Y]
                for xx in range(s):
                    X = ox + x * s + xx
                    if 0 <= X < DW:
                        row[X] = p


def player_frame(row=3, col=0):
    pw, ph, psheet = read_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')
    return [r[col * 32:(col + 1) * 32] for r in psheet[row * 32:(row + 1) * 32]]


def arena_check(frames24, out_name, zoomf=4):
    """Composite 24x24 figure frames at 3x beside the player (2x) on the arena floor."""
    w, h, arena = read_png(ARENA_FRAME)
    arena = [list(r) for r in arena]
    n = len(frames24)
    width = 120 + n * 80
    x0 = 840
    y0 = 640
    # player at 2x: frame 32x32 -> feet at row 28 -> place feet at y=730
    blit_scaled(arena, player_frame(3, 0), x0 + 20, 730 - 29 * 2, 2)
    for i, f in enumerate(frames24):
        # figure feet baseline row 20 -> place at y=730
        blit_scaled(arena, f, x0 + 100 + i * 80, 730 - 21 * 3, 3)
    crop = [r[x0:x0 + width] for r in arena[y0:y0 + 110]]
    save(crop, WIP + out_name + '_1x.png')
    save(zoom(crop, zoomf, None), WIP + out_name + '_%dx.png' % zoomf)


BLACK = (0, 0, 0, 255)


def lint_outline(px, name='', allow=()):
    """Report coloured (non-black) pixels that touch transparency 4-way (holes in the outline)."""
    H, W = len(px), len(px[0])
    bad = []
    for y in range(H):
        for x in range(W):
            p = px[y][x]
            if p[3] == 0 or p[:3] == (0, 0, 0) or p in allow:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if not (0 <= X < W and 0 <= Y < H) or px[Y][X][3] == 0:
                    bad.append((x, y))
                    break
    if bad:
        print('LINT %s: %d exposed pixels: %s' % (name, len(bad), bad[:20]))
    return bad


def gif_preview(frames, path, scale=8, delay_cs=8, bg=ARENA_GREEN, loops=1):
    """Write an animated GIF of frames (list of px) upscaled on a solid background."""
    from gifio import write_gif
    fr = [fill_bg(zoom(f, scale, None), bg) for f in frames] * loops
    return write_gif(path, fr, [delay_cs] * len(fr) if isinstance(delay_cs, int) else list(delay_cs) * loops)


def close_outline(px, skip=()):
    """Add black outline to transparent pixels 4-adjacent to coloured (non-black) pixels.
    skip: colours (rgba) that should not generate outline (e.g. fx)."""
    H, W = len(px), len(px[0])
    add = []
    for y in range(H):
        for x in range(W):
            if px[y][x][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H:
                    q = px[Y][X]
                    if q[3] and q[:3] != (0, 0, 0) and q not in skip:
                        add.append((x, y))
                        break
    for x, y in add:
        px[y][x] = BLACK
    return len(add)
