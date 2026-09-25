"""Write Greyson's eight attack sheets (his APPROVED fight look), each PNG with its .aseprite beside it,
after checking every frame. A bare run writes nothing:

    python -B gan_export.py                        # prints this, writes nothing
    python -B gan_export.py <scratch_dir>          # writes all sixteen files there, for checking
    python -B gan_export.py --ship [--replace]     # writes them into Assets/Characters/Greyson/

It only ever writes these names (.png and .aseprite), horizontal strips of 112x112 frames, frame 0
leftmost, feet at (56, 111), facing screen-right (the code flips him):

    greyson_idle (4)   greyson_throw (4)   greyson_teleport (3)   greyson_slam (5)
    greyson_hit (2)    greyson_broken (4)  greyson_defeat (5)     greyson_victory (4)

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/ (which must exist).
    A scratch folder that resolves anywhere under Assets is refused, by os.path.realpath (8.3 short
    names are on for this drive, and abspath alone can be fooled).
  - An existing file is never overwritten without --replace; every target is checked before
    anything is written, so a refusal leaves everything as it was.
  - Every sheet is built and checked before the first file is written; one problem writes nothing.
  - Each file is built in a temp folder and moved into place in one step (os.replace).
  - Importing gan_base proves the approved design rig and the approved fight rig still draw their
    shipped sheets exactly.

Checked, per frame:
  - 112x112, the strip horizontal
  - the lowest drawn row is 111 and the soles (or the knees, kneeling) are centred on column 56;
    nothing drawn on the frame's other three edges
  - every colour is in the fight palette (the approved keys plus the cannon's two bore darks), the
    keyline pure #000000, no semi-alpha
  - no keyline gaps, stray pixels or pinholes, no keys off the palette (gf_base.audit; the speed
    lines and grit are FX pixels, free of keyline by design, and are exempt)
  - the share of black within 15-21% (the brief's target is about 17-18%; frames over 18.5% are
    flagged in the report with the reason)
  - idle f0 IS approval f0, and victory is built on a rebuild of approval f2 that is proved equal
    to it with its own face
Afterwards each .aseprite is re-exported by Aseprite and compared with its PNG pixel for pixel
(art_source/imgdiff.pixel_diff: alpha everywhere, colour wherever a pixel shows), in the temp
folder and again where it landed.
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402  (proves both approved rigs on import)
import gan_idle  # noqa: E402
import gan_throw  # noqa: E402
import gan_teleport  # noqa: E402
import gan_slam  # noqa: E402
import gan_hit  # noqa: E402
import gan_broken  # noqa: E402
import gan_defeat  # noqa: E402
import gan_victory  # noqa: E402
from PIL import Image  # noqa: E402

K = B.K
MODULES = [gan_idle, gan_throw, gan_teleport, gan_slam, gan_hit, gan_broken, gan_defeat, gan_victory]
NAMES = ('greyson_idle', 'greyson_throw', 'greyson_teleport', 'greyson_slam', 'greyson_hit',
         'greyson_broken', 'greyson_defeat', 'greyson_victory')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(B.ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(B.ASSETS)
FW = FH = 112
FEET_ROW = 111
BLACK_RANGE = (0.15, 0.21)
BLACK_FLAG = 0.185

assert tuple(m.NAME for m in MODULES) == NAMES


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root + os.sep)


def check(mod, pal):
    """-> (strip image, per-frame report rows, problems)."""
    frames, rows, problems = [], [], []
    for i, (px, fx) in enumerate(mod.frames()):
        im = B.image(px)
        tag = '%s f%d' % (mod.NAME, i)
        if im.size != (FW, FH):
            problems.append('%s: frame is %s' % (tag, im.size))
        st = K.stats(im)
        cols = {c for c in K.flat(im) if c[3]}
        if cols - pal:
            problems.append('%s: colours off the palette: %s' % (tag, sorted(cols - pal)[:4]))
        if any(c[:3] == (0, 0, 0) and c != (0, 0, 0, 255) for c in cols):
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        a = B.audit(px, fx)
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:4] for k, v in a.items() if v}))
        x0, y0, x1, y1 = K.bbox(px)
        if y1 != FEET_ROW:
            problems.append('%s: lowest drawn row %d, not %d' % (tag, y1, FEET_ROW))
        if x0 < 1 or x1 > FW - 2 or y0 < 1:
            problems.append('%s: drawn on the frame edge (cols %d..%d, top row %d)' % (tag, x0, x1, y0))
        stance = [x for (x, y) in px if y == FEET_ROW and 30 <= x <= 82]
        mid = (min(stance) + max(stance)) / 2.0 if stance else None
        if mid is None or abs(mid - 56) > 1.5:
            problems.append('%s: the feet are not centred on column 56 (%s)' % (tag, mid))
        if not BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]:
            problems.append('%s: black %.1f%% outside %.0f-%.0f%%' % (
                tag, 100 * st['black'], 100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        frames.append(im)
        rows.append((i, st, len(cols), (x0, y0, x1, y1), len(fx)))
    strip = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (FW * i, 0))
    if len(mod.TIMES) != len(frames):
        problems.append('%s: %d times for %d frames' % (mod.NAME, len(mod.TIMES), len(frames)))
    approval = B.approval_sheet()
    for i, ref in getattr(mod, 'APPROVED', {}).items():
        d = B.pixel_diff(strip.crop((FW * i, 0, FW * i + FW, FH)),
                         approval.crop((FW * ref, 0, FW * ref + FW, FH)))
        if d:
            problems.append('%s f%d is not approval f%d: %s' % (mod.NAME, i, ref, d))
    return strip, rows, problems


def _aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(name, strip, out_dir, tmp):
    """Both files built in `tmp` and the .aseprite proved there, then moved into out_dir in one step
    each and proved again where they landed. -> (png, ase, round-trip result or None)."""
    t_png = os.path.join(tmp, name + '.png')
    t_ase = os.path.join(tmp, name + '.aseprite')
    strip.save(t_png)
    d = B.pixel_diff(strip, Image.open(t_png))
    if d:
        raise SystemExit('%s: the PNG on disk differs from the build: %s' % (name, d))
    _aseprite(t_png, t_ase)
    back = os.path.join(tmp, name + '_roundtrip.png')
    _aseprite(t_ase, back)
    d = B.pixel_diff(Image.open(t_png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    os.replace(t_png, png)
    os.replace(t_ase, ase)
    back2 = os.path.join(tmp, name + '_landed.png')
    _aseprite(ase, back2)
    landed = B.pixel_diff(Image.open(png), Image.open(back2)) or B.pixel_diff(strip, Image.open(png))
    return png, ase, landed


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    replace = '--replace' in argv
    args = [a for a in argv if a != '--replace']
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
    targets = [os.path.join(out_dir, n + ext) for n in NAMES for ext in ('.png', '.aseprite')]
    existing = [t for t in targets if os.path.exists(t)]
    if existing and not replace:
        raise SystemExit('NOT WRITTEN: these exist; pass --replace to overwrite them:\n  ' +
                         '\n  '.join(existing))
    pal = set(K.PAL.values())
    built, problems = [], []
    for mod in MODULES:
        strip, rows, pr = check(mod, pal)
        built.append((mod, strip, rows))
        problems += pr
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    status = 0
    tmp = tempfile.mkdtemp(prefix='greyson_anims_')
    try:
        for mod, strip, rows in built:
            png, ase, landed = write(mod.NAME, strip, out_dir, tmp)
            sheet = K.stats(strip)
            print('%s  %dx%d, %d frames of %dx%d, feet at (56, %d), times %s%s' % (
                os.path.basename(png), strip.width, strip.height, len(rows), FW, FH, FEET_ROW,
                mod.TIMES, ', loops' if mod.LOOP else ', once'))
            for i, st, ncol, bb, nfx in rows:
                flag = '  <- over %.1f%%' % (100 * BLACK_FLAG) if st['black'] > BLACK_FLAG else ''
                print('   f%d  opaque %4d  colours %2d  black %.1f%%  rows %d..%d  cols %d..%d%s%s' % (
                    i, st['opaque'], ncol, 100 * st['black'], bb[1], bb[3], bb[0], bb[2],
                    '  fx %d' % nfx if nfx else '', flag))
            print('   sheet: colours %d, black %.1f%%, semi-alpha %d; .aseprite round trip: %s' % (
                sheet['colours'], 100 * sheet['black'], sheet['semi'], landed or 'identical'))
            status |= 1 if landed else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
