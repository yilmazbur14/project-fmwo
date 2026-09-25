"""Write Greyson's BRAWL sheets (the Punch-Out final phase), each a horizontal strip with its
.aseprite beside it. SHARED: it ships this folder's sheets (gb_sheets.py, the punching half) and any
other sheet module handed to it (the other half: dazed, uppercut, recover, ko, toss, the barbell
prop). A bare run writes nothing:

    python -B gb_export.py                                    # prints this, writes nothing
    python -B gb_export.py <scratch_dir> [options]            # writes there, for checking
    python -B gb_export.py --ship [--replace] [options]       # writes into Assets/Characters/Greyson/

options:
    --sheets <file.py>[,<file.py>...]   sheet modules to add (by path); gb_sheets.py is always in
    --no-default                        leave gb_sheets.py out (ship only the given modules)
    --only <name>[,<name>...]           write only these sheets (all are still checked)

A sheet module defines:
    SHEETS = {name: [(label, builder, kwargs), ...]}   frame 0 first; builder(**kwargs) returns
                                                       (canvas with .px and .image(), anchors dict)
  and may define, per sheet name:
    FRAME_SIZE = {name: (w, h)}          default 112x112
    FEET       = {name: (x, y) or None}  default (56, 111): the lowest row and the feet's centre;
                                         None for a prop (no feet check)
    BLACK      = {name: (lo, hi) or None}  default 15-21.5% (the approved brawl frames run
                                         18.4-19.9%); None skips it (a prop)
    APPROVED   = {(name, frame): path}   frames that must stay pixel-identical to an approved PNG

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/. A scratch folder
    anywhere under Assets is refused (compared by os.path.realpath; 8.3 short names are on).
  - Only names matching greyson_brawl_* or greyson_barbell_prop are accepted, and a name defined
    by two modules is refused. It never touches another sheet in the folder.
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder and moved into place in one step.
  - The approved design and fight rigs are proven on import (via art_source/greyson_poses).

Checked before anything is written, per frame: the frame size; the feet (lowest row, centred);
nothing on the frame's other edges; every colour in his approved fight palette; a pure #000000
keyline; no semi-alpha; the rig's audit (no keyline gaps, strays, pinholes or stray keys); black in
range; the approved frames unchanged. Afterwards each .aseprite is re-exported by Aseprite and
compared with its PNG pixel for pixel, in the temp folder and again where it landed.

Prints every frame's anchors as its builder reports them (crown, chin, fist, gauntlet, muzzle,
contact, ...).
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_base as B  # noqa: E402  (proves both rigs on import)
from PIL import Image  # noqa: E402

K, G = B.K, B.G
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(G.B.ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(B.SHIP_DIR)
NAME_OK = re.compile(r'^greyson_(brawl_[a-z0-9_]+|barbell_prop)$')
DEFAULT_SIZE = (112, 112)
DEFAULT_FEET = (56, 111)
DEFAULT_BLACK = (0.15, 0.215)
APPROVED_DIR = os.path.join(HERE, 'approved')
# this folder's approved frames (the user's approval pass, 2026-09-24)
OWN_APPROVED = {('greyson_brawl_guard', 0): os.path.join(APPROVED_DIR, 'greyson_brawl_guard_f0.png'),
                ('greyson_brawl_hook_l', 1): os.path.join(APPROVED_DIR, 'greyson_brawl_hook_l_strike.png')}


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def load_module(path):
    path = os.path.realpath(path)
    name = 'gbx_' + re.sub(r'\W', '_', os.path.splitext(os.path.basename(path))[0])
    folder = os.path.dirname(path)
    if folder not in sys.path:
        sys.path.insert(1, folder)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not isinstance(getattr(mod, 'SHEETS', None), dict):
        raise SystemExit('%s defines no SHEETS dict' % path)
    return mod


def collect(mods):
    """-> {name: (module, frames spec)}; refuses bad or duplicate names."""
    out = {}
    for mod in mods:
        for name, spec in mod.SHEETS.items():
            if not NAME_OK.match(name):
                raise SystemExit('refusing sheet name %r (from %s): only greyson_brawl_* or '
                                 'greyson_barbell_prop' % (name, mod.__file__))
            if name in out:
                raise SystemExit('sheet %r is defined twice (%s and %s)' % (
                    name, out[name][0].__file__, mod.__file__))
            out[name] = (mod, spec)
    return out


def build(name, mod, spec):
    """-> (strip, rows, problems)"""
    fw, fh = getattr(mod, 'FRAME_SIZE', {}).get(name, DEFAULT_SIZE)
    feet = getattr(mod, 'FEET', {}).get(name, DEFAULT_FEET)
    black = getattr(mod, 'BLACK', {}).get(name, DEFAULT_BLACK)
    approved = dict(OWN_APPROVED)
    approved.update(getattr(mod, 'APPROVED', {}))
    pal = set(K.PAL.values())
    frames, rows, problems = [], [], []
    for i, (label, fn, kw) in enumerate(spec):
        cv, anc = fn(**kw)
        px = cv.px
        im = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
        for (x, y), k in px.items():
            if 0 <= x < fw and 0 <= y < fh:
                im.putpixel((x, y), K.PAL[k])
        tag = '%s f%d %s' % (name, i, label)
        if any(not (0 <= x < fw and 0 <= y < fh) for (x, y) in px):
            problems.append('%s: drawn outside its %dx%d frame' % (tag, fw, fh))
        st = K.stats(im)
        cols = {c for c in K.flat(im) if c[3]}
        if cols - pal:
            problems.append('%s: colours off the palette: %s' % (tag, sorted(cols - pal)[:4]))
        if any(c[:3] == (0, 0, 0) and c != (0, 0, 0, 255) for c in cols):
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        a = G.audit(px)
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:4] for k, v in a.items() if v}))
        x0, y0, x1, y1 = K.bbox(px)
        if feet is not None:
            if y1 != feet[1]:
                problems.append('%s: lowest drawn row %d, not %d' % (tag, y1, feet[1]))
            row = [x for (x, y) in px if y == feet[1]]
            mid = (min(row) + max(row)) / 2.0 if row else None
            if mid is None or abs(mid - feet[0]) > 1.0:
                problems.append('%s: the feet are not centred on column %d (%s)' % (tag, feet[0], mid))
            if x0 < 1 or x1 > fw - 2 or y0 < 1:
                problems.append('%s: drawn on the frame edge (cols %d..%d, top row %d)' % (tag, x0, x1, y0))
        if black is not None and not black[0] <= st['black'] <= black[1]:
            problems.append('%s: black %.1f%% outside %.1f-%.1f%%' % (
                tag, 100 * st['black'], 100 * black[0], 100 * black[1]))
        ref = approved.get((name, i))
        if ref:
            d = G.pixel_diff(im, Image.open(ref).convert('RGBA'))
            if d:
                problems.append('%s: no longer the approved frame %s: %s' % (tag, os.path.basename(ref), d))
        frames.append(im)
        rows.append((i, label, st, len(cols), (x0, y0, x1, y1), anc))
    strip = Image.new('RGBA', (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (fw * i, 0))
    return strip, rows, problems


def _aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(name, strip, out_dir):
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    tmp = tempfile.mkdtemp(prefix='greyson_brawl_')
    try:
        t_png = os.path.join(tmp, name + '.png')
        t_ase = os.path.join(tmp, name + '.aseprite')
        strip.save(t_png)
        _aseprite(t_png, t_ase)
        back = os.path.join(tmp, 'roundtrip.png')
        _aseprite(t_ase, back)
        d = G.pixel_diff(Image.open(t_png), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        d = G.pixel_diff(strip, Image.open(t_png))
        if d:
            raise SystemExit('%s: the PNG on disk differs from the build: %s' % (name, d))
        os.makedirs(out_dir, exist_ok=True)
        os.replace(t_png, png)
        os.replace(t_ase, ase)
        back2 = os.path.join(tmp, 'roundtrip_landed.png')
        _aseprite(ase, back2)
        landed = G.pixel_diff(Image.open(png), Image.open(back2)) or G.pixel_diff(strip, Image.open(png))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return png, ase, landed


def _opt(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args):
            raise SystemExit('%s needs a value' % flag)
        val = args[i + 1]
        del args[i:i + 2]
        return [v for v in val.split(',') if v]
    return None


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    args = list(argv)
    replace = '--replace' in args
    no_default = '--no-default' in args
    args = [a for a in args if a not in ('--replace', '--no-default')]
    extra = _opt(args, '--sheets') or []
    only = _opt(args, '--only')
    if args == ['--ship']:
        out_dir = SHIP_DIR
        if not os.path.isdir(out_dir):
            raise SystemExit('%s is missing; refusing to create a character folder' % out_dir)
    elif len(args) == 1 and not args[0].startswith('--'):
        out_dir = os.path.realpath(args[0])
        if _under(out_dir, ASSETS):
            raise SystemExit('refusing %s: it is under Assets. Only --ship writes there.' % out_dir)
    else:
        print(__doc__)
        return 2
    mods = [] if no_default else [load_module(os.path.join(HERE, 'gb_sheets.py'))]
    mods += [load_module(p) for p in extra]
    sheets = collect(mods)
    if only:
        unknown = [n for n in only if n not in sheets]
        if unknown:
            raise SystemExit('--only names no sheet: %s' % unknown)
    built, problems = [], []
    for name, (mod, spec) in sheets.items():
        strip, rows, probs = build(name, mod, spec)
        built.append((name, strip, rows))
        problems += probs
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    todo = [b for b in built if not only or b[0] in only]
    if not replace:
        existing = [os.path.join(out_dir, n + ext) for n, _, _ in todo for ext in ('.png', '.aseprite')
                    if os.path.exists(os.path.join(out_dir, n + ext))]
        if existing:
            print('NOT WRITTEN: these exist; pass --replace to overwrite them:')
            for p in existing:
                print('  ' + p)
            return 1
    status = 0
    for name, strip, rows in todo:
        png, ase, landed = write(name, strip, out_dir)
        sheet = K.stats(strip)
        fw = strip.width // len(rows)
        print('%s  %dx%d, %d frames of %dx%d' % (os.path.basename(png), strip.width, strip.height,
                                                 len(rows), fw, strip.height))
        for (i, label, st, ncol, bb, anc) in rows:
            print('   f%d %-10s black %.1f%%  colours %2d  cols %3d..%3d rows %3d..%3d  %s' % (
                i, label, 100 * st['black'], ncol, bb[0], bb[2], bb[1], bb[3],
                '  '.join('%s %s' % kv for kv in anc.items())))
        print('   sheet: colours %d, black %.1f%%, semi-alpha %d' % (
            sheet['colours'], 100 * sheet['black'], sheet['semi']))
        print('   .aseprite round trip:', landed or 'identical')
        status |= 1 if landed else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
