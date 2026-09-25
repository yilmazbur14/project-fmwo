"""Write Greyson's POSE sheets, each a horizontal strip of 112x112 frames (frame 0 leftmost) with
its .aseprite beside it. Unwired: no scene or script refers to them yet. A bare run writes nothing:

    python -B gp_export.py                        # prints this, writes nothing
    python -B gp_export.py <scratch_dir>          # writes all ten files there, for checking
    python -B gp_export.py --ship [--replace]     # writes them into Assets/Characters/Greyson/

The sheets (the coordinator's brief, 2026-09-24; the plan's pose clock is a 0.3 s strike, then a
1.2 s hold, in the order A, B, C, A, B, C):
    greyson_pose_a    3  strike | hold (the approved f1) | hold, breathing flex
    greyson_pose_b    3  strike | hold (the approved f2) | hold, breathing flex
    greyson_pose_c    3  strike | hold (the approved f3) | hold, breathing flex
    greyson_pose_hit  2  knocked out of the pose | annoyed (holds to the pose's end)
    greyson_spirit    4  arm up (the approved f4) | hold | grin | THROW
Feet at (56, 111) in every frame. Drawn facing as the approved frames; the code decides any flip.

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/. A scratch folder
    anywhere under Assets is refused, compared by os.path.realpath (8.3 short names are on).
  - It only ever writes the five names above (.png and .aseprite). It never touches another
    artist's sheets or the approved files (greyson_redesign.*, greyson_fight_approval.*).
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder and moved into place in one step.
  - gp_base proves on import that both rigs still draw their approved frames exactly, and the
    hold frames here are checked pixel-identical to the approved fight frames before writing.

Checked before anything is written, per frame:
  - 112x112; the lowest drawn row is 111; the feet centred on column 56; nothing on the frame's
    other edges
  - every colour in the fight palette, the keyline pure #000000, no semi-alpha
  - no keyline gaps, strays, pinholes or keys off the palette (the rig's audit)
  - black within 15-19% (the approved frames run 15.9-18.1%; back views sit lowest)
Afterwards each .aseprite is re-exported by Aseprite and compared with its PNG pixel for pixel,
in the temp folder and again where it landed (art_source/imgdiff.pixel_diff).
Prints every frame's anchors: feet, crown and muzzle (the cannon's muzzle centre).
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_base as G  # noqa: E402  (proves both rigs on import)
import gp_fig as P  # noqa: E402
from PIL import Image  # noqa: E402

K = G.K
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(G.B.ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(G.SHIP_DIR)
NAMES = ('greyson_pose_a', 'greyson_pose_b', 'greyson_pose_c', 'greyson_pose_hit', 'greyson_spirit')
TIMING = {
    'greyson_pose_a': 'f0 0.3 strike; then f1/f2 alternate through the 1.2 s hold (0.4 s each: f1 f2 f1)',
    'greyson_pose_b': 'as pose_a',
    'greyson_pose_c': 'as pose_a',
    'greyson_pose_hit': 'f0 0.12; f1 held until that pose\'s clock ends',
    'greyson_spirit': 'f0 0-0.5 s; f1 through the gather (0.5-3.0); f2 3.0-3.5; f3 from 3.5 (launch)',
}
# the frames that must stay exactly the approved fight frames
APPROVED_HOLDS = {('greyson_pose_a', 1): 'pose_a', ('greyson_pose_b', 1): 'pose_b',
                  ('greyson_pose_c', 1): 'pose_c', ('greyson_spirit', 0): 'spirit'}
FW = FH = 112
FEET_ROW = 111
BLACK_RANGE = (0.15, 0.19)


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def build(name):
    """-> (strip image, per-frame rows, problems)"""
    frames, rows, problems = [], [], []
    pal_rgba = set(K.PAL.values())
    for i, (label, cv, anc) in enumerate(P.build_sheet(name)):
        px = cv.px
        im = cv.image()
        tag = '%s f%d %s' % (name, i, label)
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
        a = G.audit(px)
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
        key = APPROVED_HOLDS.get((name, i))
        if key:
            d = G.pixel_diff(im, G.approved_frame(key))
            if d:
                problems.append('%s: no longer the approved %s frame: %s' % (tag, key, d))
        frames.append(im)
        rows.append((i, label, st, len(cols), (x0, y0, x1, y1), anc))
    strip = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (FW * i, 0))
    return strip, rows, problems


def _aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(name, strip, out_dir, replace):
    """Both files built in a temp folder, the .aseprite proven there, moved into out_dir, proven
    again where they landed. Returns (png, ase, landed round-trip result)."""
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    tmp = tempfile.mkdtemp(prefix='greyson_poses_')
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
    built, problems = [], []
    for name in NAMES:
        strip, rows, probs = build(name)
        built.append((name, strip, rows))
        problems += probs
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    if not replace:
        existing = [os.path.join(out_dir, n + ext) for n in NAMES for ext in ('.png', '.aseprite')
                    if os.path.exists(os.path.join(out_dir, n + ext))]
        if existing:
            print('NOT WRITTEN: these exist; pass --replace to overwrite them:')
            for p in existing:
                print('  ' + p)
            return 1
    status = 0
    for name, strip, rows in built:
        png, ase, landed = write(name, strip, out_dir, replace)
        sheet = K.stats(strip)
        print('%s  %dx%d, %d frames of %dx%d, feet at (56, %d)' % (
            os.path.basename(png), strip.width, strip.height, len(rows), FW, FH, FEET_ROW))
        print('   timing: %s' % TIMING[name])
        for (i, label, st, ncol, bb, anc) in rows:
            print('   f%d %-10s black %.1f%%  colours %2d  cols %3d..%3d rows %3d..%3d  feet %s  crown %s  muzzle %s' % (
                i, label, 100 * st['black'], ncol, bb[0], bb[2], bb[1], bb[3], anc['feet'], anc['crown'],
                anc['muzzle']))
        print('   sheet: colours %d, black %.1f%%, semi-alpha %d' % (
            sheet['colours'], 100 * sheet['black'], sheet['semi']))
        print('   .aseprite round trip:', landed or 'identical')
        status |= 1 if landed else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
