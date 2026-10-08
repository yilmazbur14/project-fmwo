"""Jordan's fight animations: shared base.

The sheets are drawn in his approved v2 look (thin, frail, greasy: art_source/jordan_v2, approved
2026-09-24), which itself builds on the approved redesign rig (art_source/jordan_redesign). Both are
imported READ-ONLY: nothing here edits them, and bytecode writing is switched off so importing them
leaves no __pycache__ in their folders.

Every module in this folder is named janim_*, so none of them can shadow (or be shadowed by) the
redesign rig's kit / head / torso / jordan / previews, v2's jv2_*, or josh_redesign's lib / export.
The imports below are checked against the folders they must come from.

Coordinates: parts are placed in the rigs' BUILD coordinates, exactly as jv2_frames.build() does; a
finished frame is shifted by the rig's ANCHOR_SHIFT (-1 in x) so the body centres on column 48, with
the soles on row 95. Frames render through v2's palette (the same 40 keys; the skin is v2's pallor).
"""
import math
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'jordan_redesign')
V2 = os.path.join(ART, 'jordan_v2')
JOSH = os.path.join(ART, 'josh_redesign')
ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')
APPROVED_PNG = os.path.join(ASSETS, 'jordan_redesign_v2.png')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

for _p in (RIG, ART, V2):
    if _p not in sys.path:
        sys.path.append(_p)

import kit            # noqa: E402  the redesign rig's palette and renderer
import lib            # noqa: E402  josh_redesign/lib.py, via kit's own path setup
import jordan         # noqa: E402  the redesign rig: box, fist, pop cloud, star, sneakers, face rows
import head as rig_head    # noqa: E402
import torso as rig_torso  # noqa: E402
import jv2_base       # noqa: E402  v2: its palette (the pallor skin) and renderer
import jv2_body       # noqa: E402  v2: the thin body in the baggy tee
import jv2_head       # noqa: E402  v2: the greasy hair
import jv2_frames     # noqa: E402  v2: the two approved frames
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == os.path.normcase(os.path.abspath(folder))


for _m, _d in ((kit, RIG), (jordan, RIG), (rig_head, RIG), (rig_torso, RIG), (lib, JOSH),
               (jv2_base, V2), (jv2_body, V2), (jv2_head, V2), (jv2_frames, V2)):
    if not _same_dir(_m, _d):
        raise ImportError('%s was imported from %s, expected %s: a module-name clash' % (_m.__name__, _m.__file__, _d))

from kit import capsule  # noqa: E402,F401
from lib import (Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, stroke)  # noqa: E402,F401

PAL = jv2_base.PAL           # v2's palette: the approved 40 keys, the skin ramp turned to pallor
V2B = jv2_body               # short names for the v2 parts
V2H = jv2_head
V2F = jv2_frames

W = H = 96
ANCHOR_SHIFT = jordan.ANCHOR_SHIFT          # -1: build x -> frame x

# The approved sheet's 40 colours, as palette keys. Nothing else may appear in a frame.
ALLOWED = set('01239ABDGNOPQRSTVWYabcdefghijklmnopqsvwx')
assert len(ALLOWED) == 40
# Keys that are effects (glints, sparkles, speed lines), which float free of any keyline by design.
FX_KEYS = set('WQYPOq')


#PART HELPERS

def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rows_of(rows):
    return [r.replace(' ', '') for r in rows]


def rot(part, deg, pivot):
    """Rotate a part by `deg` degrees about `pivot` (x, y), positive = clockwise on screen.

    Three integer shears (x, then y, then x). Each pass moves whole rows or whole columns, so it is a
    bijection on the pixel grid: nothing is dropped or doubled, a closed keyline stays closed, and
    details survive as clean one-pixel steps instead of nearest-neighbour mush."""
    if not deg:
        return dict(part)
    th = math.radians(deg)
    a = -math.tan(th / 2.0)
    b = math.sin(th)
    px_, py_ = pivot

    def sx(p, amt):
        return {(x + int(math.floor(amt * (y - py_) + 0.5)), y): k for (x, y), k in p.items()}

    def sy(p, amt):
        return {(x, y + int(math.floor(amt * (x - px_) + 0.5))): k for (x, y), k in p.items()}

    # y grows downward on screen, so the textbook counter-clockwise shears turn things clockwise
    return sx(sy(sx(part, a), b), a)


def _scale2x(g):
    h, w = len(g), len(g[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = g[y][x]
            a = g[y - 1][x] if y > 0 else p
            b = g[y][x + 1] if x < w - 1 else p
            c = g[y][x - 1] if x > 0 else p
            d = g[y + 1][x] if y < h - 1 else p
            e0 = a if (c == a and c != d and a != b) else p
            e1 = b if (a == b and a != c and b != d) else p
            e2 = c if (d == c and d != b and c != a) else p
            e3 = d if (b == d and b != a and d != c) else p
            out[2 * y][2 * x], out[2 * y][2 * x + 1] = e0, e1
            out[2 * y + 1][2 * x], out[2 * y + 1][2 * x + 1] = e2, e3
    return out


def rotsprite(part, deg, pivot, pad=4):
    """RotSprite-style turn (Scale2x three times, nearest sample, back to 1x), clockwise positive.
    Only ever used to make a TEMPLATE for a hand-authored map: its output is dumped, redrawn by hand
    and the hand-drawn map is what ships."""
    x0, y0, x1, y1 = bbox(part)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    g = [[part.get((x, y)) for x in range(x0, x1 + 1)] for y in range(y0, y1 + 1)]
    for _ in range(3):
        g = _scale2x(g)
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    px_, py_ = pivot
    out = {}
    r = max(x1 - x0, y1 - y0) + 8
    for Y in range(int(py_) - r, int(py_) + r):
        for X in range(int(px_) - r, int(px_) + r):
            dx, dy = X + 0.5 - px_, Y + 0.5 - py_
            sx_, sy_ = c * dx + s * dy + px_, -s * dx + c * dy + py_
            gx, gy = int(math.floor((sx_ - x0) * 8)), int(math.floor((sy_ - y0) * 8))
            if 0 <= gy < len(g) and 0 <= gx < len(g[0]) and g[gy][gx] is not None:
                out[(X, Y)] = g[gy][gx]
    return out


def tilt2(part, deg, pivot, order='xy'):
    """A small turn (clockwise positive) as one row-shear and one column-shear, so every row and
    every column of the part stays intact and features step instead of smearing. A pixel that
    neither shear covers (where a row step meets a column step) is filled from the source at the
    inverse-turned spot. Only for templates and small tilts; check the result by eye."""
    th = math.radians(deg)
    t = math.tan(th)
    px_, py_ = pivot

    def r(v):
        return int(math.floor(v + 0.5))

    out = {}
    for (x, y), k in part.items():
        if order == 'xy':
            x1 = x + r(-t * (y + 0.5 - py_))
            y1 = y + r(t * (x1 + 0.5 - px_))
        else:
            y1 = y + r(t * (x + 0.5 - px_))
            x1 = x + r(-t * (y1 + 0.5 - py_))
        out[(x1, y1)] = k
    c, s = math.cos(th), math.sin(th)
    xs = [q[0] for q in out]
    ys = [q[1] for q in out]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in out:
                continue
            if sum(n in out for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))) >= 3:
                dx, dy = x + 0.5 - px_, y + 0.5 - py_
                sx_, sy_ = c * dx + s * dy + px_, -s * dx + c * dy + py_
                k = part.get((int(math.floor(sx_)), int(math.floor(sy_))))
                if k:
                    out[(x, y)] = k
    return out


def dandruff(px, dx=0, dy=0):
    """v2's dandruff flakes on his shoulders (jv2_body.DANDRUFF), moved with the tee by (dx, dy):
    only where they land on the tee's red, as v2 does."""
    for (x, y), k in V2B.DANDRUFF.items():
        q = (x + dx, y + dy)
        if px.get(q) in ('R', 'T', 'V', 'v'):
            px[q] = k


def close_gaps(part):
    """Keyline any transparent spot a coloured pixel of `part` touches (4-neighbours), in place."""
    add = set()
    for (x, y), k in part.items():
        if k == 'k':
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in part:
                add.add(q)
    for q in add:
        part[q] = 'k'
    return part


def stamp_all(cv, parts):
    """Stamp (part, outline) pairs in order."""
    for part, ol in parts:
        cv.stamp(part, outline=ol)


def finish(cv_or_px):
    """Build coordinates -> frame coordinates (the rig's anchor shift), clipped to the frame."""
    px = cv_or_px.px if hasattr(cv_or_px, 'px') else cv_or_px
    out = {}
    for (x, y), k in px.items():
        q = (x + ANCHOR_SHIFT, y)
        if 0 <= q[0] < W and 0 <= q[1] < H:
            out[q] = k
    return out


def to_image(px):
    return jv2_base.image(px, W, H)


#RECORDING (where things are, for the layout numbers)

_REC = [None]


def rec(name, value):
    """Frame builders hand named parts (dicts of build-coordinate pixels) or points to this while a
    measurement is recording; otherwise it does nothing."""
    if _REC[0] is not None:
        _REC[0][name] = value
    return value


def record(builder):
    """Run one frame builder; return (what it returned, the parts and points it recorded)."""
    _REC[0] = {}
    try:
        res = builder()
        got = _REC[0]
    finally:
        _REC[0] = None
    return res, got


#THE APPROVED FRAMES

def approved_sheet():
    return Image.open(APPROVED_PNG).convert('RGBA')


def approved_frame(i):
    """The approved v2 frame i (0 idle, 1 fist-pump) as frame-coordinate keys, straight from the v2
    rig, checked pixel-for-pixel against the shipped jordan_redesign_v2.png."""
    px = jv2_frames.frame_px(i)
    d = pixel_diff(to_image(px), approved_sheet().crop((96 * i, 0, 96 * i + 96, 96)))
    if d:
        raise SystemExit('rig no longer reproduces approved frame %d: %s' % (i, d))
    return px


def _to_frame(v):
    if isinstance(v, dict):
        return {(x + ANCHOR_SHIFT, y): k for (x, y), k in v.items()}
    if isinstance(v, set):
        return {(x + ANCHOR_SHIFT, y) for (x, y) in v}
    return (v[0] + ANCHOR_SHIFT, v[1])


def make_frames(builders, approved=None, post=None):
    """Build a sheet's frames. `builders` are zero-argument callables returning (Canvas, fx pixels)
    in build coordinates. `approved` maps a frame index to the rig frame it must be pixel for pixel:
    that builder has to reproduce the rig's frame exactly (so what it recorded belongs to the approved
    frame), and then the rig's own frame is what ships. `post` is applied to every other frame.
    Returns [(px, fx, info)] in frame coordinates, info being what the builder recorded."""
    out = []
    for i, b in enumerate(builders):
        (cv, fx), info = record(b)
        px = finish(cv)
        if approved and i in approved:
            ref = approved_frame(approved[i])
            d = pixel_diff(to_image(px), to_image(ref))
            if d:
                raise SystemExit('frame %d must be approved frame %d but differs: %s' % (i, approved[i], d))
            px = ref
        elif post:
            px = post(px)
        out.append((px, _to_frame(set(fx)), {k: _to_frame(v) for k, v in info.items()}))
    return out


#MEASURING

def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def audit(px, fx=()):
    """Problems a frame must not ship with:
      gaps   body-colour pixels touching transparency (a hole in the keyline)
      lone   pixels with no neighbour at all (stray specks)
      holes  transparent pixels boxed in on four sides (the floor showing through)
      keys   palette keys outside the approved 40
    `fx` lists pixels that are effects (sparkles, speed lines) and so float free by design."""
    fx = set(fx)
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if k != 'k' and any(q not in px for q in n4):
            gaps.append((x, y, k))
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            lone.append((x, y, k))
    x0, y0, x1, y1 = bbox(px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                holes.append((x, y))
    keys = sorted(set(px.values()) - ALLOWED)
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


#SHEETS AND SHIPPING

def strip(frames):
    out = Image.new('RGBA', (W * len(frames), H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f if isinstance(f, Image.Image) else to_image(f), (W * i, 0))
    return out


def write_sheet(name, im, out_dir):
    """Write <out_dir>/<name>.png in one go (built in a temp folder, then os.replace), save the
    .aseprite beside it the same way, and check the .aseprite re-exports to exactly the PNG's pixels
    (imgdiff.pixel_diff: alpha everywhere and colour wherever a pixel shows). Returns the paths and
    the round-trip result of the files where they landed (None = identical)."""
    tmp = tempfile.mkdtemp(prefix='janim_')
    tmp_png = os.path.join(tmp, name + '.png')
    tmp_ase = os.path.join(tmp, name + '.aseprite')
    im.save(tmp_png)
    subprocess.run([ASEPRITE, '-b', tmp_png, '--save-as', tmp_ase], check=True, capture_output=True)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([ASEPRITE, '-b', tmp_ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(tmp_png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    os.replace(tmp_png, png)
    os.replace(tmp_ase, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    return png, ase, pixel_diff(Image.open(png), Image.open(back2))
