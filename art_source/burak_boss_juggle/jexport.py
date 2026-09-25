"""Write Captain Burak's juggle sheet and his mat shadow, each with an .aseprite beside it, and
round-trip both .aseprite files through Aseprite against the PNGs pixel for pixel (imgdiff).

    burak_boss_juggle.png          12 frames of 192x144 in a strip (Mason's order)
    burak_boss_leap_shadow.png     3 frames of 64x16: solid black ellipses, low / mid / high

A bare run writes nothing:

    python jexport.py <out_dir>     write all four files into <out_dir> (a scratch folder, for checking)
    python jexport.py --ship        write them into Assets/Characters/BurakBoss/

--ship is the only way this script touches Assets/, and it only ever writes those four file names.
A bare run of an art export script once overwrote live art in this project; this one refuses to guess.

It also prints the numbers the coder wires with: frame size and hframes, the feet texel, the tumble
centre, top_row, the clips and their timings, and the per-frame numbers.
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))              # art_source, for imgdiff
import jkit as J  # noqa: E402
import jposes  # noqa: E402
import jshadow  # noqa: E402
import kit  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSET_DIR = os.path.join(ROOT, 'Assets', 'Characters', 'BurakBoss')
SHEET = 'burak_boss_juggle'
SHADOW = 'burak_boss_leap_shadow'
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


def frames_with_owners():
    out = []
    for name, fn, hold in jposes.FRAMES:
        holder = {}
        orig = J.finish

        def capture(cv):
            holder['own'] = dict(cv.own)
            return orig(cv)
        J.finish = capture
        try:
            px = fn()
        finally:
            J.finish = orig
        out.append((name, px, holder['own'], hold))
    return out


def sheet():
    fr = frames_with_owners()
    im = Image.new('RGBA', (J.FW * len(fr), J.FH), (0, 0, 0, 0))
    for i, (name, px, own, hold) in enumerate(fr):
        im.paste(kit.image(px, J.FW, J.FH), (i * J.FW, 0))
    return im, fr


def shadow_sheet():
    return kit.image(jshadow.sheet_px(), jshadow.W * jshadow.FRAMES, jshadow.H)


def report(im, fr):
    lines = ['juggle sheet: %d frames of %dx%d (hframes %d), %dx%d'
             % (len(fr), J.FW, J.FH, len(fr), im.width, im.height)]
    lines.append('feet texel (ground frames 0, 7-11): %s' % (J.FEET,))
    lines.append('tumble_centre (his middle in every air frame, the rotation pivot): %s' % (J.TUMBLE_AT,))
    air_top, him_top = [], []
    for i in jposes.AIR:
        name, px, own, hold = fr[i]
        air_top.append(min(y for (x, y) in px))
        him_top.append(min(y for (x, y), o in own.items() if (x, y) in px and o not in ('fx', 'prop')))
    lines.append('top_row (highest drawn row in any air frame): %d   (his own body: %d)' % (min(air_top), min(him_top)))
    # the centroid of his drawn body in the air frames, for comparison with the pivot
    cx = cy = n = 0
    for i in jposes.AIR[1:]:
        name, px, own, hold = fr[i]
        for (x, y), o in own.items():
            if (x, y) in px and o not in ('fx', 'prop'):
                cx += x
                cy += y
                n += 1
    lines.append('   measured centroid of his body over tumble frames 2-6: (%.1f, %.1f)' % (cx / n, cy / n))
    for tag, (a, b, loop) in jposes.TAGS.items():
        holds = [jposes.FRAMES[i][2] for i in range(a, b + 1)]
        lines.append('clip %-7s frames %d-%d %s holds %s  (%.2fs)'
                     % (tag, a, b, 'loop' if loop else 'once', ' '.join('%.2f' % h for h in holds), sum(holds)))
    for i, (name, px, own, hold) in enumerate(fr):
        f = kit.image(px, J.FW, J.FH)
        st = kit.stats(f)
        semi = sum(1 for c in kit.pixels_of(f) if 0 < c[3] < 255)
        ys = [y for (x, y) in px]
        xs = [x for (x, y) in px]
        lines.append('frame %2d %-15s opaque %5d, colours %2d, black %.1f%%, semi-alpha %d, box x %d-%d y %d-%d'
                     % (i, name, st['opaque'], st['colours'], 100 * st['black'], semi, min(xs), max(xs), min(ys), max(ys)))
    st = kit.stats(im)
    lines.append('sheet: opaque %d, colours %d, black %.1f%%' % (st['opaque'], st['colours'], 100 * st['black']))
    return lines


def write_pair(im, out_dir, name):
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d1 = pixel_diff(im, Image.open(png))
    d2 = pixel_diff(im, Image.open(back))
    print('wrote %s %s\nwrote %s' % (png, im.size, ase))
    print('   png on disk vs build: %s; aseprite round trip vs build: %s' % (d1 or 'identical', d2 or 'identical'))
    return not (d1 or d2)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    assets = os.path.normcase(os.path.join(ROOT, 'Assets'))
    out_dir = ASSET_DIR if argv[0] == '--ship' else os.path.abspath(argv[0])
    if argv[0] != '--ship' and os.path.normcase(out_dir).startswith(assets):
        print('refusing to write into Assets/ without --ship')
        return 2
    os.makedirs(out_dir, exist_ok=True)
    im, fr = sheet()
    ok = write_pair(im, out_dir, SHEET)
    ok = write_pair(shadow_sheet(), out_dir, SHADOW) and ok
    for line in report(im, fr):
        print(line)
    sh = shadow_sheet()
    for i in range(jshadow.FRAMES):
        bb = sh.crop((i * jshadow.W, 0, (i + 1) * jshadow.W, jshadow.H)).getbbox()
        print('shadow frame %d: ellipse %dx%d' % (i, bb[2] - bb[0], bb[3] - bb[1]))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
