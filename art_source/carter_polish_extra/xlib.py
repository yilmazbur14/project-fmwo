"""Shared helpers for Carter's derived art and Messatsu sheets (art_source/carter_polish_extra).

Everything here reads the APPROVED polish (art_source/carter_polish, imported read-only - nothing is
ever written into that folder, and no bytecode either) and writes only to the scratchpad unless a
builder is run with --ship.

    keys_of(png, box)        -> {(x, y): key} of a shipped PNG, every colour mapped back to lib.PAL
    image(px, w, h)          -> RGBA image of a key dict
    resample15(px, sx0, sy0, n) -> the 1.5x close-up the Josh portrait introduced (no blends)
    measure(im)              -> {'opaque', 'colours', 'black'}
    ship(im, dest_stem)      -> PNG + .aseprite into Assets, only after the Aseprite round trip is
                                pixel-identical (imgdiff.pixel_diff), each file written in one copy
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
POLISH = os.path.join(ROOT, 'art_source', 'carter_polish')
for p in (POLISH, os.path.join(ROOT, 'art_source'), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image                                                   # noqa: E402
import lib                                                              # noqa: E402  (the polish lib)
from imgdiff import pixel_diff                                          # noqa: E402

CARTER = os.path.join(ROOT, 'Assets', 'Characters', 'Carter')
POLISH_PNG = os.path.join(CARTER, 'carter_polish.png')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.environ.get('CARTER_EXTRA_OUT', os.path.join(
    os.environ.get('TEMP', tempfile.gettempdir()), 'claude',
    'C--Users-theyi-OneDrive-Documents-new-game-project', 'a7fc2846-afef-472d-979b-e17143793a0f',
    'scratchpad', 'carter_polish', 'extra'))
BG = (46, 49, 58, 255)

RGB2KEY = {v[:3]: k for k, v in lib.PAL.items()}


def keys_of(png, box=None):
    """A shipped PNG as a key dict. Refuses any colour that is not in lib.PAL, so nothing derived
    from it can silently pick up an off-palette pixel."""
    im = Image.open(png).convert('RGBA')
    if box:
        im = im.crop(box)
    px = {}
    bad = set()
    for y in range(im.height):
        for x in range(im.width):
            c = im.getpixel((x, y))
            if c[3] == 0:
                continue
            k = RGB2KEY.get(c[:3])
            if k is None:
                bad.add(c)
                continue
            px[(x, y)] = k
    if bad:
        raise ValueError('%s: %d colours outside lib.PAL, e.g. %s' % (png, len(bad), sorted(bad)[:4]))
    return px


def image(px, w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), lib.PAL[k])
    return im


def measure(im):
    st = lib.stats(im)
    return {'opaque': st['opaque'], 'colours': st['colours'], 'black': st['black'], 'alphas': st['alphas']}


def fmt(m):
    return 'opaque %5d   colours %3d   pure black %5.1f%%' % (m['opaque'], m['colours'], 100 * m['black'])


def upscale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


# ------------------------------------------------------------------ the 1.5x close-up

def omap(u):
    """Source offset -> output offset: pairs (2k, 2k+1) land on 3k and 3k+2, 3k+1 is between."""
    return 3 * (u // 2) + 2 * (u % 2)


def _pick(a, b, aa, bb):
    """The between pixel of a and b (aa, bb: the pixels beyond each). Never a blend."""
    if a == b:
        return a
    if a is None or b is None:
        o = b if a is None else a
        return None if o == 'k' else o          # a silhouette keyline stays one pixel wide
    if a == 'k':
        return b                                 # so does an interior one
    if b == 'k':
        return a
    a_thin, b_thin = aa != a, bb != b
    if a_thin and not b_thin:
        return b                                 # a one-pixel feature stays one pixel
    if b_thin and not a_thin:
        return a
    return a


def resample15(px, sx0, sy0, n):
    """Every source pixel lands on exactly one output pixel and each pair gets one 'between' pixel
    copying one of its two neighbours (never a blend), so keylines stay one pixel wide and diagonal
    keylines stay joined. The same scheme as art_source/josh_redesign/portrait.py."""
    def g(x, y):
        return px.get((sx0 + x, sy0 + y))

    def axis(o):
        q, r = divmod(o, 3)
        return [2 * q] if r == 0 else ([2 * q + 1] if r == 2 else [2 * q, 2 * q + 1])

    out = {}
    size = omap(n - 1) + 1
    for oy in range(size):
        ys = axis(oy)
        for ox in range(size):
            xs = axis(ox)
            if len(xs) == 1 and len(ys) == 1:
                v = g(xs[0], ys[0])
            elif len(ys) == 1:
                y = ys[0]
                v = _pick(g(xs[0], y), g(xs[1], y), g(xs[0] - 1, y), g(xs[1] + 1, y))
            elif len(xs) == 1:
                x = xs[0]
                v = _pick(g(x, ys[0]), g(x, ys[1]), g(x, ys[0] - 1), g(x, ys[1] + 1))
            else:
                tl, tr, bl, br = g(xs[0], ys[0]), g(xs[1], ys[0]), g(xs[0], ys[1]), g(xs[1], ys[1])
                if (tl == br == 'k' and 'k' not in (tr, bl)) or (tr == bl == 'k' and 'k' not in (tl, br)):
                    v = 'k'                      # a diagonal keyline stays joined
                else:
                    top = _pick(tl, tr, g(xs[0] - 1, ys[0]), g(xs[1] + 1, ys[0]))
                    bot = _pick(bl, br, g(xs[0] - 1, ys[1]), g(xs[1] + 1, ys[1]))
                    v = _pick(top, bot, top, bot)
            if v is not None:
                out[(ox, oy)] = v
    # two diagonal source keyline pixels whose images land two apart get the one bridge pixel
    for y in range(n):
        for x in range(n):
            if g(x, y) != 'k':
                continue
            for dx in (1, -1):
                qx, qy = x + dx, y + 1
                if not (0 <= qx < n and qy < n) or g(qx, qy) != 'k' or 'k' in (g(qx, y), g(x, qy)):
                    continue
                P, Q = (omap(x), omap(y)), (omap(qx), omap(qy))
                if abs(P[0] - Q[0]) <= 1 and abs(P[1] - Q[1]) <= 1:
                    continue
                cands = [(bx, by) for bx in range(min(P[0], Q[0]), max(P[0], Q[0]) + 1)
                         for by in range(min(P[1], Q[1]), max(P[1], Q[1]) + 1)
                         if (bx, by) not in (P, Q) and max(abs(bx - P[0]), abs(by - P[1])) <= 1
                         and max(abs(bx - Q[0]), abs(by - Q[1])) <= 1]
                if not any(out.get(c) == 'k' for c in cands):
                    out[cands[0]] = 'k'
    return out


def to_out(pt, sx0, sy0):
    """A source pixel coordinate -> the output's, for anything placed by geometry after the scale."""
    return (1.5 * (pt[0] - sx0) + 0.25, 1.5 * (pt[1] - sy0) + 0.25)


# ------------------------------------------------------------------ Aseprite and shipping

def aseprite_roundtrip(png, ase):
    """Write ase from png with Aseprite, export it back, and compare pixel for pixel."""
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    return pixel_diff(Image.open(png), Image.open(back))


def stage(im, name):
    """Save im and its .aseprite into the scratch 'ship' folder and prove the round trip."""
    d = os.path.join(SCRATCH, 'ship')
    os.makedirs(d, exist_ok=True)
    png = os.path.join(d, name + '.png')
    ase = os.path.join(d, name + '.aseprite')
    im.save(png)
    return png, ase, aseprite_roundtrip(png, ase)


def ship(im, dest_dir, name):
    """Only after a pixel-identical round trip: copy the PNG and the .aseprite into Assets, one
    write each, and check the bytes that landed."""
    png, ase, d = stage(im, name)
    if d:
        raise RuntimeError('%s: aseprite round trip differs: %s' % (name, d))
    out = []
    for src, ext in ((png, '.png'), (ase, '.aseprite')):
        dst = os.path.join(dest_dir, name + ext)
        shutil.copyfile(src, dst)
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        out.append(dst)
    # and the shipped PNG really is what was built
    back = pixel_diff(im, Image.open(out[0]))
    if back:
        raise RuntimeError('%s: shipped PNG differs from the build: %s' % (name, back))
    return out
