"""Josh's hands (his own fight): shared toolkit. Palette, the guard, cards, stamping, images.

Built on Josh's approved rig (art_source/josh_redesign, imported read-only): the same palette keys,
the same pure-black keyline Canvas, the same RotSprite rotation. Nothing here writes anything; the
writer (jh_build.py) installs `install_guard()` first, which refuses any write outside this folder,
the scratchpad and the temp folder, and any process but Aseprite.
"""
import math
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
REDESIGN = os.path.join(ART, 'josh_redesign')
for p in (REDESIGN, ART):
    if p not in sys.path:
        sys.path.insert(0, p)

import lib as JL            # noqa: E402  Josh's own palette, Canvas, shapes (read-only)
import josh3                # noqa: E402
import ground_kit as gk     # noqa: E402
import rig                  # noqa: E402
from PIL import Image       # noqa: E402

SCRATCH = os.environ.get('JH_SCRATCH', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\josh_hands'))
APPROVAL = os.path.join(HERE, 'approval')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

# ------------------------------------------------------------------ palette
# Josh's measured palette (josh_redesign/lib.PAL, 38 colours, keyline pure black) is the whole body
# palette here: the hands and the portals add no body colour of their own.
PAL = dict(JL.PAL)
# The additive glow layers only (drawn with blend ADD; opaque dark values that add light).
GLOW = {
    'q': (22, 12, 3, 255),      # faint gold haze
    'u': (46, 26, 6, 255),      # gold glow
    'U': (86, 52, 12, 255),     # hot gold glow
    'Q': (132, 92, 28, 255),    # flare
    'e': (40, 6, 12, 255),      # wine haze
    'E': (74, 14, 24, 255),     # crimson glow
}
TAKES = {
    'A': "Gilded deck: cream card faces with gold borders, wine vortex, gold glow",
    'B': "Wine deck: his cards' wine backs with a gold lattice, the same wine vortex, crimson glow",
}


def hexs(key, pal=None):
    c = (pal or PAL)[key]
    return '#%02X%02X%02X' % c[:3]


# ------------------------------------------------------------------ the guard

def install_guard(extra_roots=()):
    import subprocess
    roots = [HERE, tempfile.gettempdir(), SCRATCH] + list(extra_roots)
    roots = [os.path.normcase(os.path.realpath(r)) for r in roots]
    ase = os.path.normcase(os.path.realpath(ASEPRITE))
    assets = os.path.normcase(os.path.realpath(os.path.join(ROOT, 'Assets')))

    def inside(p):
        rp = os.path.normcase(os.path.realpath(os.fspath(p)))
        if rp == assets or rp.startswith(assets + os.sep):
            return False
        return any(rp == r or rp.startswith(r + os.sep) for r in roots)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not inside(path):
                raise PermissionError('guard: josh_hands writes only into %s, the scratchpad or temp, not %s'
                                      % (HERE, path))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'shutil.copyfile', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not inside(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            argv = args[1]
            line = argv if isinstance(argv, str) else subprocess.list2cmdline([os.fspath(a) for a in argv])
            first = line[1:line.index('"', 1)] if line.startswith('"') else line.split(' ')[0]
            if os.path.normcase(os.path.realpath(first)) != ase:
                raise PermissionError('guard: josh_hands launches only Aseprite, not %s' % first)
            if assets in os.path.normcase(os.path.realpath(line)) or 'assets' + os.sep in os.path.normcase(line):
                raise PermissionError('guard: an Aseprite argument under Assets')

    sys.addaudithook(hook)


# ------------------------------------------------------------------ images

def to_image(px, w, h, pal=None, ox=0, oy=0):
    pal = pal or PAL
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    put = im.putpixel
    for (x, y), k in px.items():
        x2, y2 = x + ox, y + oy
        if 0 <= x2 < w and 0 <= y2 < h:
            put((x2, y2), pal[k])
    return im


def strip(images):
    w, h = images[0].size
    out = Image.new('RGBA', (w * len(images), h), (0, 0, 0, 0))
    for i, im in enumerate(images):
        out.alpha_composite(im, (w * i, 0))
    return out


def upscale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def add_glow(base, glow, xy=(0, 0)):
    """Composite an additive glow image onto an opaque RGBA base (in place semantics: returns new)."""
    import numpy as np
    b = np.array(base).astype(np.int32)
    g = np.zeros_like(b)
    gl = np.array(glow).astype(np.int32)
    x, y = xy
    h, w = gl.shape[:2]
    H, W = b.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return base
    sub = gl[y0 - y:y1 - y, x0 - x:x1 - x]
    mask = (sub[..., 3:4] > 0)
    g[y0:y1, x0:x1, :3] = sub[..., :3] * mask
    b[..., :3] = np.clip(b[..., :3] + g[..., :3], 0, 255)
    return Image.fromarray(b.astype('uint8'), 'RGBA').copy()


# ------------------------------------------------------------------ stamping

def keyline(part):
    """part plus its own 1px 4-neighbour keyline, as one part."""
    out = {}
    body = set(part)
    for (x, y) in body:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body:
                out[q] = 'k'
    out.update(part)
    return out


def stamp(px, part, outline=True):
    if outline:
        body = set(part)
        for (x, y) in body:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body:
                    px[q] = 'k'
    px.update(part)
    return px


def mv(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rot_pt(p, deg, pivot):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))
