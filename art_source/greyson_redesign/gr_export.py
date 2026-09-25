"""Write Greyson's redesign approval sheet, greyson_redesign.png (2 frames of 112x112 in a
horizontal strip: f0 the idle ready stance, f1 the front double biceps), with
greyson_redesign.aseprite beside it. A bare run writes nothing:

    python -B gr_export.py                        # prints this, writes nothing
    python -B gr_export.py <scratch_dir>          # writes both files there, for checking
    python -B gr_export.py --ship [--replace]     # writes them into Assets/Characters/Greyson/

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/. A scratch folder
    that resolves anywhere under Assets is refused. Paths are compared by os.path.realpath,
    because 8.3 short names are on for this drive and abspath alone can be fooled.
  - It only ever writes greyson_redesign.png and greyson_redesign.aseprite. It never touches
    portrait.png or any other file.
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder and moved into place in one step.

Checked before anything is written, per frame:
  - 112x112, the strip horizontal, frame 0 leftmost
  - his feet: the lowest drawn row is 111, the frame's bottom row
  - height (top row to feet) within 80-86 texels
  - every colour is one of the rig's palette, the keyline is pure #000000, no semi-alpha
  - no keyline gaps, stray pixels or pinholes, no keys off the palette (gr_kit.audit)
  - the silhouette mirrors about column 56 (x' = 112 - x); only f1's sweat bead is exempt
  - the share of black within the cast's band (16-29%)
Afterwards the .aseprite is re-exported by Aseprite and compared with the PNG pixel for pixel
(art_source/imgdiff.pixel_diff: alpha everywhere, colour wherever a pixel shows).
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
sys.path.insert(0, HERE)
sys.path.insert(0, ART)                     # art_source, for imgdiff
import gr_kit as K  # noqa: E402
import gr_fig  # noqa: E402
import gr_face  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(os.path.join(ROOT, 'Assets', 'Characters', 'Greyson'))
NAME = 'greyson_redesign'
POSES = ('idle', 'flex')
FW = FH = 112
FEET_ROW = 111
HEIGHT_RANGE = (80, 86)
BLACK_RANGE = (0.16, 0.29)


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def build():
    """-> (strip image, per-frame rows for the report, problems)."""
    frames, rows, problems = [], [], []
    pal_rgba = {v for v in K.PAL.values()}
    for i, pose in enumerate(POSES):
        cv = gr_fig.build(pose)
        px = cv.px
        im = cv.image()
        tag = 'f%d %s' % (i, pose)
        if im.size != (FW, FH):
            problems.append('%s: frame is %s' % (tag, im.size))
        st = K.stats(im)
        cols = {c for c in K.flat(im) if c[3]}
        if cols - pal_rgba:
            problems.append('%s: colours off the palette: %s' % (tag, sorted(cols - pal_rgba)[:4]))
        if any(c[:3] == (0, 0, 0) and c != (0, 0, 0, 255) for c in cols):
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        a = K.audit(px)
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:4] for k, v in a.items() if v}))
        x0, y0, x1, y1 = K.bbox(px)
        if y1 != FEET_ROW:
            problems.append('%s: lowest drawn row %d, not %d' % (tag, y1, FEET_ROW))
        height = y1 - y0 + 1
        if not HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]:
            problems.append('%s: %d texels tall, outside %s' % (tag, height, HEIGHT_RANGE))
        effect = set(gr_face.EXTRAS.get(pose, {}))
        asym = [p for p in px if p not in effect and (K.AX - p[0], p[1]) not in px
                and (K.AX - p[0], p[1]) not in effect]
        if asym:
            problems.append('%s: silhouette off-mirror at %s' % (tag, sorted(asym)[:6]))
        if not BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]:
            problems.append('%s: black %.1f%% outside %.0f-%.0f%%' % (
                tag, 100 * st['black'], 100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        frames.append(im)
        rows.append((tag, st, len(cols), (x0, y0, x1, y1), height))
    strip = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (FW * i, 0))
    if strip.size != (FW * len(POSES), FH):
        problems.append('strip is %s' % (strip.size,))
    return strip, rows, problems


def _aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(strip, out_dir, replace):
    """Build both files in a temp folder, prove the .aseprite round-trips there, then move them
    into out_dir and prove it again where they landed. Returns (png, ase, round-trip result)."""
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    for p in (png, ase):
        if os.path.exists(p) and not replace:
            raise SystemExit('%s exists; pass --replace to overwrite it' % p)
    tmp = tempfile.mkdtemp(prefix='greyson_redesign_')
    try:
        t_png = os.path.join(tmp, NAME + '.png')
        t_ase = os.path.join(tmp, NAME + '.aseprite')
        strip.save(t_png)
        _aseprite(t_png, t_ase)
        back = os.path.join(tmp, 'roundtrip.png')
        _aseprite(t_ase, back)
        d = pixel_diff(Image.open(t_png), Image.open(back))
        if d:
            raise SystemExit('the .aseprite does not round-trip: %s' % d)
        d = pixel_diff(strip, Image.open(t_png))
        if d:
            raise SystemExit('the PNG on disk differs from the build: %s' % d)
        os.makedirs(out_dir, exist_ok=True)
        os.replace(t_png, png)
        os.replace(t_ase, ase)
        back2 = os.path.join(tmp, 'roundtrip_landed.png')
        _aseprite(ase, back2)
        landed = pixel_diff(Image.open(png), Image.open(back2)) or pixel_diff(strip, Image.open(png))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
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
    strip, rows, problems = build()
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    png, ase, landed = write(strip, out_dir, replace)
    sheet = K.stats(strip)
    print('%s  %dx%d, %d frames of %dx%d, feet on row %d, column 56 the anchor' % (
        os.path.basename(png), strip.width, strip.height, len(rows), FW, FH, FEET_ROW))
    for tag, st, ncol, bb, h in rows:
        print('   %-8s opaque %4d  colours %2d  black %.1f%%  rows %d..%d (%d tall, %d px at 3x)  '
              'cols %d..%d' % (tag, st['opaque'], ncol, 100 * st['black'], bb[1], bb[3], h, h * 3,
                                bb[0], bb[2]))
    print('   sheet: colours %d, black %.1f%%, semi-alpha %d' % (
        sheet['colours'], 100 * sheet['black'], sheet['semi']))
    print('   .aseprite round trip:', landed or 'identical')
    print('wrote', png)
    print('wrote', ase)
    return 1 if landed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
