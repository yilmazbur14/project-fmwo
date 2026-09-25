"""Write Captain Burak's approval sprite, burak_boss.png (2 frames of 96x96 in a strip, feet on row 95,
column 48 the anchor: 0 idle, 1 the shot), and burak_boss.aseprite beside it, then round-trip the
.aseprite through Aseprite and compare it with the PNG pixel for pixel (art_source/imgdiff.py).

A bare run writes nothing:

    python export.py <out_dir>          write both files into <out_dir> (a scratch folder, for checking)
    python export.py --ship             write Assets/Characters/BurakBoss/burak_boss.{png,aseprite}

--ship is the only way this script touches Assets/, and it only ever writes those two file names.
A bare run of an art export script once overwrote live art in this project; this one refuses to guess.
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))                # art_source, for imgdiff
import burak  # noqa: E402
import kit  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASSET_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'BurakBoss'))
NAME = 'burak_boss'
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


def sheet():
    f0, f1 = burak.frames()
    out = Image.new('RGBA', (192, 96), (0, 0, 0, 0))
    out.paste(f0, (0, 0))
    out.paste(f1, (96, 0))
    return out, f0, f1


def audit(im, name):
    """Per-frame numbers: opaque px, colours, black share, semi-alpha, the content box, the feet row
    and the body's centre column."""
    lines = []
    for i in range(im.width // 96):
        f = im.crop((i * 96, 0, i * 96 + 96, 96))
        px = kit.pixels_of(f)
        semi = sum(1 for c in px if 0 < c[3] < 255)
        st = kit.stats(f)
        bb = f.getbbox()
        feet = [x for x in range(96) if f.getpixel((x, 94))[3]]
        lines.append('%s frame %d: opaque %d, colours %d, black %.1f%%, semi-alpha %d, box x %d-%d y %d-%d, '
                     'feet row 94 spans x %d-%d (centre %.1f)'
                     % (name, i, st['opaque'], st['colours'], 100 * st['black'], semi, bb[0], bb[2] - 1,
                        bb[1], bb[3] - 1, min(feet), max(feet), (min(feet) + max(feet)) / 2.0))
    st = kit.stats(im)
    lines.append('%s sheet: opaque %d, colours %d, black %.1f%%' % (name, st['opaque'], st['colours'], 100 * st['black']))
    return lines


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = ASSET_DIR if argv[0] == '--ship' else os.path.abspath(argv[0])
    if argv[0] != '--ship' and os.path.normcase(out_dir).startswith(os.path.normcase(
            os.path.normpath(os.path.join(HERE, '..', '..', 'Assets')))):
        print('refusing to write into Assets/ without --ship')
        return 2
    os.makedirs(out_dir, exist_ok=True)
    im, f0, f1 = sheet()
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    on_disk = pixel_diff(im, Image.open(png))
    round_trip = pixel_diff(im, Image.open(back))
    print('wrote', png, im.size)
    print('wrote', ase)
    print('png on disk vs build:', on_disk or 'identical')
    print('aseprite round trip vs build:', round_trip or 'identical')
    for line in audit(im, NAME):
        print(line)
    return 1 if (on_disk or round_trip) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
