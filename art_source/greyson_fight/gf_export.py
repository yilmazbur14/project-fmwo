"""Write Greyson's fight APPROVAL sheet, greyson_fight_approval.png (5 frames of 112x112 in a
horizontal strip, frame 0 leftmost), with greyson_fight_approval.aseprite beside it. Unwired: no
scene or script refers to it. A bare run writes nothing:

    python -B gf_export.py                        # prints this, writes nothing
    python -B gf_export.py <scratch_dir>          # writes both files there, for checking
    python -B gf_export.py --ship [--replace]     # writes them into Assets/Characters/Greyson/

Frames (the coordinator's brief, 2026-09-24):
    f0 idle     the fight idle: the barbell on his shoulder, the cannon on his left arm
    f1 pose_a   the three-quarter back twist (ref images/25.png)
    f2 pose_b   the front double biceps (ref 26.png), on the approved f1
    f3 pose_c   the rear V (ref 27.png)
    f4 spirit   the spirit-bomb raise: the cannon arm alone, straight up
Feet at (56, 111) in every frame.

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/. A scratch folder
    that resolves anywhere under Assets is refused, compared by os.path.realpath (8.3 short
    names are on for this drive, and abspath alone can be fooled).
  - It only ever writes greyson_fight_approval.png and .aseprite. It never touches
    greyson_redesign.* (the approved design of record) or portrait.png.
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder and moved into place in one step.
  - gf_base proves on import that the approved rig still draws the approved sprite exactly.

Checked before anything is written, per frame:
  - 112x112, the strip horizontal
  - his feet: the lowest drawn row is 111; nothing drawn on the frame's other three edges
  - every colour is in the fight palette (the approved 29 keys plus the cannon's two bore
    darks), the keyline is pure #000000, no semi-alpha
  - no keyline gaps, stray pixels or pinholes, no keys off the palette (gf_base.audit)
  - the share of black within 15-29% (the cast's band; back views carry no face, so they sit a
    couple of points under the front ones, as Matt's accepted back sheets do)
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
sys.path.insert(0, HERE)
import gf_base as B  # noqa: E402  (proves the approved rig on import)
import gf_fig  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

K = B.K
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(B.ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(os.path.join(B.ROOT, 'Assets', 'Characters', 'Greyson'))
NAME = 'greyson_fight_approval'
FRAMES = ('idle', 'pose_a', 'pose_b', 'pose_c', 'spirit')
FW = FH = 112
FEET_ROW = 111
BLACK_RANGE = (0.15, 0.29)


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def build():
    """-> (strip image, per-frame rows for the report, problems)."""
    frames, rows, problems = [], [], []
    pal_rgba = set(K.PAL.values())
    for i, name in enumerate(FRAMES):
        cv = gf_fig.build(name)
        px = cv.px
        im = B.image(px)
        tag = 'f%d %s' % (i, name)
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
        a = B.audit(px)
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:4] for k, v in a.items() if v}))
        x0, y0, x1, y1 = K.bbox(px)
        if y1 != FEET_ROW:
            problems.append('%s: lowest drawn row %d, not %d' % (tag, y1, FEET_ROW))
        if x0 < 1 or x1 > FW - 2 or y0 < 1:
            problems.append('%s: drawn on the frame edge (cols %d..%d, top row %d)' % (tag, x0, x1, y0))
        feet = [x for (x, y) in px if y == FEET_ROW]
        mid = (min(feet) + max(feet)) / 2.0 if feet else None
        if mid is None or abs(mid - 56) > 1.0:
            problems.append('%s: the feet are not centred on column 56 (%s)' % (tag, mid))
        if not BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]:
            problems.append('%s: black %.1f%% outside %.0f-%.0f%%' % (
                tag, 100 * st['black'], 100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        frames.append(im)
        rows.append((tag, st, len(cols), (x0, y0, x1, y1)))
    strip = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (FW * i, 0))
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
    tmp = tempfile.mkdtemp(prefix='greyson_fight_')
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
    print('%s  %dx%d, %d frames of %dx%d, feet at (56, %d)' % (
        os.path.basename(png), strip.width, strip.height, len(rows), FW, FH, FEET_ROW))
    for tag, st, ncol, bb in rows:
        print('   %-10s opaque %4d  colours %2d  black %.1f%%  rows %d..%d  cols %d..%d' % (
            tag, st['opaque'], ncol, 100 * st['black'], bb[1], bb[3], bb[0], bb[2]))
    print('   sheet: colours %d, black %.1f%%, semi-alpha %d' % (
        sheet['colours'], 100 * sheet['black'], sheet['semi']))
    print('   .aseprite round trip:', landed or 'identical')
    print('wrote', png)
    print('wrote', ase)
    return 1 if landed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
