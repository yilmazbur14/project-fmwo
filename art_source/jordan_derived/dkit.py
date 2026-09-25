"""Shared kit for the art derived from Jordan's approved 2026-09-23 redesign: paths, his rig (imported,
never edited), the 1.5x resample, measuring, and preview helpers.

Named dkit, not lib or kit, on purpose: Jordan's rig imports art_source/josh_redesign/lib.py as `lib`
and its own kit.py as `kit`, and a module of the same name here would shadow them.

Nothing in this module writes into Assets/. Previews go to the session scratchpad (PREVIEWS).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ART = os.path.join(ROOT, 'art_source')
RIG = os.path.join(ART, 'jordan_redesign')
ASSETS = os.path.join(ROOT, 'Assets')
SPRITE = os.path.join(ASSETS, 'Characters', 'Jordan', 'jordan_redesign.png')
PREVIEWS = os.environ.get(
    'JORDAN_DERIVED_PREVIEWS',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\jordan_derived')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

for _p in (RIG, ART):
    if _p not in sys.path:
        sys.path.append(_p)
import kit                                                        # noqa: E402  (Jordan's rig)
from PIL import Image, ImageDraw                                  # noqa: E402

PAL = kit.PAL


# ---------------------------------------------------------------------------------------- 1.5x
# The same scaling Josh's portrait used (art_source/josh_redesign/portrait.py), parametrised on the
# window: every source pixel lands on exactly one output pixel, and each pair of them gets one
# 'between' pixel that copies one of its two neighbours - never a blend - chosen so a keyline stays
# one pixel wide and a diagonal keyline stays joined.
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


def resample(px, sx0, sy0, n):
    """The n x n source window at (sx0, sy0) of key map px, scaled 1.5x (n = 43 gives 64)."""
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


# ---------------------------------------------------------------------------------------- images
def image(px, w, h, pal=None):
    """Render keys. `pal` defaults to the approved rig's kit.PAL; the v2 art passes jv2_base.PAL,
    whose skin keys are the pallor tones."""
    pal = pal or PAL
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), pal[k])
    return im


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(im):
    px = [c for c in flat(im.convert('RGBA')) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': black / max(1, len(px)),
            'alphas': sorted({c[3] for c in flat(im.convert('RGBA'))})}


BG = (46, 49, 58, 255)
DARK = (10, 10, 12, 255)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im.convert('RGBA'))
    return out


def up(im, s, bg=BG):
    base = on_bg(im, bg) if bg else im.convert('RGBA')
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def gridded(im, s, major=5, bg=BG):
    """Upscaled with a pixel grid (every pixel faint, every `major` stronger), for placing edits."""
    big = up(im, s, bg)
    d = ImageDraw.Draw(big, 'RGBA')
    for gx in range(0, big.width, s):
        d.line([(gx, 0), (gx, big.height)], fill=(255, 80, 200, 90) if (gx // s) % major == 0 else (255, 255, 255, 26))
    for gy in range(0, big.height, s):
        d.line([(0, gy), (big.width, gy)], fill=(255, 80, 200, 90) if (gy // s) % major == 0 else (255, 255, 255, 26))
    return big


def ruled(im, s, major=5, bg=BG, x0=0, y0=0):
    """gridded() with the x and y coordinates of every `major`th pixel written in a margin."""
    big = gridded(im, s, major, bg)
    m = 22
    out = Image.new('RGBA', (big.width + m, big.height + m), DARK)
    out.paste(big, (m, m))
    d = ImageDraw.Draw(out)
    for i in range(0, im.width, major):
        d.text((m + i * s + 1, 5), str(x0 + i), fill=(255, 140, 220, 255))
    for j in range(0, im.height, major):
        d.text((1, m + j * s + 1), str(y0 + j), fill=(255, 140, 220, 255))
    return out


def label(im, text, pad=18, col=(220, 220, 228, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=col)
    return out


def row(ims, gap=10, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def col(ims, gap=10, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def preview(im, name):
    os.makedirs(PREVIEWS, exist_ok=True)
    p = os.path.join(PREVIEWS, name)
    im.save(p)
    return p


def dump(px, x0, y0, x1, y1):
    """Rows of keys for a region (inclusive), ruled in fives, labelled with their y."""
    lines = ['      ' + ' '.join('%-5d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        r = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(r[i:i + 5] for i in range(0, len(r), 5)))
    return '\n'.join(lines)


def patch(px, edits):
    """Overwrite horizontal spans: edits are (y, x0, keys). In keys, '.' erases, '_' keeps, spaces
    are ignored so spans can be ruled in fives."""
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            if ch == '.':
                px.pop((x, y), None)
            elif ch != '_':
                px[(x, y)] = ch
            x += 1
