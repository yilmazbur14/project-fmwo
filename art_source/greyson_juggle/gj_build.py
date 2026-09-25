"""Greyson's juggle sheet and his mat shadow: the gated exporter.

  python -B gj_build.py                       render, check and report.  WRITES NOTHING.
  python -B gj_build.py --preview DIR         also writes the 4x strip and the shadow preview into DIR
                                              (only DIR; a DIR anywhere under Assets is refused).
  python -B gj_build.py --ship [--replace]    writes greyson_juggle.png + .aseprite and
                                              greyson_leap_shadow.png + .aseprite into
                                              Assets/Characters/Greyson, and nothing else.

SAFETY (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Without --ship this script has no path into Assets at all. A --preview folder that resolves
    anywhere under Assets is refused, compared by os.path.realpath (8.3 short names are on for this
    drive, and abspath alone can be fooled).
  - --ship writes only the four files named above. It never touches greyson_redesign.* (the design
    of record), greyson_fight_approval.*, portrait.* or any other artist's sheet.
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder, its .aseprite re-exported by Aseprite and compared with the
    PNG pixel for pixel (art_source/imgdiff.pixel_diff: alpha everywhere, colour wherever a pixel
    shows), then moved into place and compared again where it landed.
  - --ship refuses unless the identity proof (four approved frames re-built through the juggle rig at
    angle 0, with and without its short cut, equal to the approved rig's own), the determinism check
    (two renders, and a child process with another string-hash seed) and the lint all pass.

Output: 12 frames of 192x144 in one horizontal strip, feet on (96, 143).
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gj_rig as R        # noqa: E402  (imports the approved rig read-only, proving it on import)
import gj_poses as P      # noqa: E402
import gj_shadow as S     # noqa: E402
import gj_lint as LINT    # noqa: E402
from imgdiff import pixel_diff   # noqa: E402
from PIL import Image     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.realpath(os.path.join(ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(os.path.join(ROOT, 'Assets', 'Characters', 'Greyson'))
SHEET = 'greyson_juggle'
SHADOW = 'greyson_leap_shadow'
WRITES = (SHEET, SHADOW)
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
CHECK = [(60, 60, 60, 255), (48, 48, 48, 255)]


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def render():
    return [fn().image() for _, fn, _ in P.FRAMES]


def strip(frames):
    im = Image.new('RGBA', (R.W * len(frames), R.H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f, (i * R.W, 0))
    return im


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.putdata([p for row in rows for p in row])
    return im


def upscale(im, f, cell=None):
    w, h = im.size
    big = im.resize((w * f, h * f), Image.NEAREST)
    bg = Image.new('RGBA', big.size)
    bp = bg.load()
    for y in range(big.size[1]):
        for x in range(big.size[0]):
            bp[x, y] = CHECK[((x // f) + (y // f)) % 2]
    bg.alpha_composite(big)
    if cell:
        bp = bg.load()
        for i in range(1, w // cell):
            for y in range(bg.size[1]):
                bp[i * cell * f, y] = (170, 40, 170, 255)
    return bg


def measure(frames):
    spans = [(i,) + f.getbbox() for i, f in enumerate(frames)]
    tops = [(s[2], s[0]) for s in spans[:7]]          # every frame that can show lifted: 0-6
    cx = cy = n = 0
    for f in frames[2:7]:                              # the tumble loop: his figure, not the air
        for (x, y) in LINT.figure(f):
            cx += x
            cy += y
            n += 1
    ground = [(i, max(y for (x, y) in LINT.figure(frames[i]))) for i in (0, 7, 8, 9, 10, 11)]
    return {'top_row': min(tops), 'tumble_centre': (round(cx / float(n)), round(cy / float(n))),
            'ground_rows': ground, 'spans': spans}


def aseprite_roundtrip(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(png))
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', tmp], check=True, capture_output=True)
    return pixel_diff(Image.open(png), Image.open(tmp))


def ship(images, replace):
    """Write the sheets into Assets/Characters/Greyson (and only there)."""
    for name in images:
        assert name in WRITES, name
        for ext in ('.png', '.aseprite'):
            dst = os.path.join(SHIP_DIR, name + ext)
            if os.path.exists(dst) and not replace:
                print('REFUSING: %s exists (pass --replace to overwrite it)' % dst)
                return 1
    bad = 0
    for name, im in images.items():
        work = tempfile.mkdtemp()
        png = os.path.join(work, name + '.png')
        ase = os.path.join(work, name + '.aseprite')
        im.save(png)
        d = aseprite_roundtrip(png, ase)
        if d:
            print('REFUSING %s: its .aseprite does not round-trip in the temp folder: %s' % (name, d))
            return 1
        for src in (png, ase):
            dst = os.path.join(SHIP_DIR, os.path.basename(src))
            assert _under(dst, SHIP_DIR) and os.path.basename(dst).split('.')[0] in WRITES
            shutil.move(src, dst)
        d = aseprite_roundtrip(os.path.join(SHIP_DIR, name + '.png'),
                               os.path.join(SHIP_DIR, name + '.aseprite'))
        print('shipped %-22s round trip where it landed: %s'
              % (name, d or 'identical (alpha and colour, every pixel)'))
        bad += d is not None
    return 1 if bad else 0


def main(argv):
    do_ship = '--ship' in argv
    replace = '--replace' in argv
    preview = argv[argv.index('--preview') + 1] if '--preview' in argv else None
    if preview and _under(preview, ASSETS):
        print('REFUSING: the preview folder %s is under Assets' % preview)
        return 1

    ident = R.check_identity()
    bad_ident = [(n, d) for n, d in ident if d]
    print('identity: %d approved frames re-built through the juggle rig at angle 0 (%s): %s'
          % (len(ident), ', '.join(n for n, _ in ident),
             'all identical to the approved rig' if not bad_ident else bad_ident))

    frames = render()
    again = render()
    same = all(a.tobytes() == b.tobytes() for a, b in zip(frames, again))
    mine = hashlib.sha1(strip(frames).tobytes()).hexdigest()
    env = dict(os.environ, PYTHONHASHSEED='4242', PYTHONDONTWRITEBYTECODE='1')
    child = subprocess.run([sys.executable, '-B', '-c',
                            'import sys, hashlib; sys.dont_write_bytecode = True; '
                            'sys.path.insert(0, %r); import gj_build as b; '
                            'print(hashlib.sha1(b.strip(b.render()).tobytes()).hexdigest())'
                            % HERE], capture_output=True, text=True, env=env, cwd=HERE)
    lines = child.stdout.strip().splitlines()
    other = lines[-1] if lines else child.stderr.strip()[-200:]
    deterministic = same and other == mine
    print('determinism: two renders %s; a child process with another hash seed %s'
          % ('identical' if same else 'DIFFER',
             'matches' if other == mine else 'DIFFERS (%s)' % other))

    print()
    fatal = LINT.main()
    print()

    sheet = strip(frames)
    rows, sizes = S.sheet()
    shadow_im = to_image(rows)
    m = measure(frames)
    print('%s: %d frames of %dx%d in one strip (%dx%d), hframes %d, vframes 1'
          % (SHEET, len(frames), R.W, R.H, sheet.width, sheet.height, len(frames)))
    print('feet texel      (%d, %d)   ground frames 0, 7, 9-11 (8 is the bounce, up off the mat); '
          'lowest figure rows %s' % (R.FEET[0], R.FEET[1],
                                     ', '.join('f%d:%d' % r for r in m['ground_rows'])))
    print('offset          (0, %d)   his main sheet hangs at (0, -56) with the feet on row 111; '
          'this keeps the feet on the same floor line' % -(R.FEET[1] + 1 - R.H // 2))
    print('tumble_centre   (%d, %d)   centroid of his figure on the loop 2-6 (he turns about '
          '(96, %d))' % (m['tumble_centre'] + (P.SPIN_Y,)))
    print('top_row         %d        (frame %d; the highest row drawn on any frame that can show '
          'lifted, 0-6)' % m['top_row'])
    print('drawn extents   ' + ', '.join('f%d:%d,%d-%d,%d' % (s[0], s[1], s[2], s[3] - 1, s[4] - 1)
                                         for s in m['spans']))
    print('timings         ' + ', '.join('%d %s %.2f' % (i, n, t)
                                         for i, (n, _, t) in enumerate(P.FRAMES)))
    print('clips           ' + ', '.join('%s %d-%d%s' % (k, a, b, ' loop' if lp else '')
                                         for k, (a, b, lp) in P.TAGS.items()))
    print('%s: %d frames of %dx%d, ellipses %s, ink #000000'
          % (SHADOW, S.FRAMES, S.W, S.H, ' '.join('%dx%d' % s for s in sizes)))

    if preview:
        os.makedirs(preview, exist_ok=True)
        upscale(sheet, 4, R.W).save(os.path.join(preview, SHEET + '_4x.png'))
        upscale(shadow_im, 6, S.W).save(os.path.join(preview, SHADOW + '_6x.png'))
        print('\npreviews written to', preview)

    ok = not bad_ident and deterministic and not fatal
    if not do_ship:
        print('\n(no --ship: nothing written to Assets)')
        return 0 if ok else 1
    if not ok:
        print('\nREFUSING TO SHIP: the identity proof, the determinism check or the lint failed')
        return 1
    return ship({SHEET: sheet, SHADOW: shadow_im}, replace)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
