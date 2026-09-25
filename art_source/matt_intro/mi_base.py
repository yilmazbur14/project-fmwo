"""Matt's intro art (walk-in, talk poses, the Hong doll, the arena roar, the portrait): shared base.

Imports the approved rig (art_source/matt) READ-ONLY and builds on it. Nothing in this folder edits
the rig, and bytecode writing is switched off so importing it leaves no __pycache__ behind in the
rig's folder (or in josh_redesign, whose lib.py the rig uses as its toolkit).

Every module in this folder is named mi_*, so none can shadow (or be shadowed by) the rig's pal /
shapes / shading / face / details / matt / preview / export, or josh_redesign's lib. The imports
below are checked against the folders they must come from.

Coordinates are the rig's own: 96x96 frames, column 48 the anchor and mirror axis (x' = 96 - x),
feet on row 95, light from the upper left.

Nothing in this module writes into Assets/. write_sheet() writes only to the folder it is given.
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'matt')
JOSH = os.path.join(ART, 'josh_redesign')
ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Matt')
APPROVED_PNG = os.path.join(ASSETS, 'matt.png')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.environ.get(
    'MATT_INTRO_SCRATCH',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\matt_intro')

for _p in (ART, RIG):
    if _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, ART)
sys.path.insert(0, RIG)          # the rig first, so its module names win

import pal            # noqa: E402  Matt's palette (installs itself into lib)
import lib            # noqa: E402  josh_redesign/lib.py, via pal's own path setup
import shapes         # noqa: E402
import shading as sh  # noqa: E402
import details        # noqa: E402
import face as rig_face  # noqa: E402
import matt           # noqa: E402  the rig's parts and the two approved frames
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == \
        os.path.normcase(os.path.abspath(folder))


for _m, _d in ((pal, RIG), (shapes, RIG), (sh, RIG), (details, RIG), (rig_face, RIG), (matt, RIG),
               (lib, JOSH)):
    if not _same_dir(_m, _d):
        raise ImportError('%s was imported from %s, expected %s: a module-name clash'
                          % (_m.__name__, _m.__file__, _d))

from lib import Canvas, amap, ellipse, fill, line, poly  # noqa: E402,F401
from shapes import capsule, sym, mir_set  # noqa: E402,F401

W = H = 96
AX = 96                      # mirror: x' = 96 - x
PAL = pal.PAL
DARKER, LIGHTER = pal.DARKER, pal.LIGHTER
ALLOWED = set(PAL)           # the approved palette, 41 keys; nothing else may appear
assert len(ALLOWED) == 41, len(ALLOWED)


# ---------------------------------------------------------------------------------------- parts

def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rows_of(rows):
    return [r.replace(' ', '') for r in rows]


def check_map(rows, width, name):
    """Every row the same width once the ruling spaces are gone."""
    bad = []
    for i, r in enumerate(rows_of(rows)):
        if len(r) != width:
            bad.append('%s row %d: width %d, not %d' % (name, i, len(r), width))
    return bad


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def keyline_gaps(part):
    """Keyline any transparent spot a coloured pixel touches (4-neighbours), in place."""
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


def clip(px):
    return {(x, y): k for (x, y), k in px.items() if 0 <= x < W and 0 <= y < H}


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PAL[k])
    return im


# ---------------------------------------------------------------------------------------- approved

def approved_sheet():
    return Image.open(APPROVED_PNG).convert('RGBA')


def approved_frame_px(i):
    """Approved frame i (0 idle, 1 roar) as keys, straight from the rig, checked pixel for pixel
    against the shipped PNG."""
    px = dict(matt.build(bool(i)).px)
    d = pixel_diff(image(px), approved_sheet().crop((96 * i, 0, 96 * i + 96, 96)))
    if d:
        raise SystemExit('rig no longer reproduces approved frame %d: %s' % (i, d))
    return px


# ---------------------------------------------------------------------------------------- measuring

def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(im):
    data = flat(im.convert('RGBA'))
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def audit(px, fx=()):
    """Problems a frame must not ship with:
      gaps   body-colour pixels touching transparency (a hole in the keyline)
      lone   pixels with no neighbour at all (stray specks)
      holes  transparent pixels boxed in on four sides (the floor showing through a pinhole)
      keys   palette keys outside the approved 41
    `fx` lists pixels that are effects (sweat, steam, motion ticks), which float free by design."""
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


# ---------------------------------------------------------------------------------------- sheets

def strip(frames, w=W, h=H):
    out = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f if isinstance(f, Image.Image) else image(f, w, h), (w * i, 0))
    return out


def write_sheet(name, im, out_dir):
    """Write <out_dir>/<name>.png in one go (built in a temp folder, then os.replace), save the
    .aseprite beside it the same way, and check the .aseprite re-exports to exactly the PNG's pixels
    (imgdiff.pixel_diff: alpha everywhere and colour wherever a pixel shows). Returns the paths and
    the round-trip result of the files where they landed (None = identical). out_dir is required:
    there is no default, on purpose."""
    if not out_dir:
        raise SystemExit('write_sheet needs an explicit output folder')
    tmp = tempfile.mkdtemp(prefix='matt_intro_')
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
