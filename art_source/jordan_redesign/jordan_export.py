"""Write Jordan's redesign approval sprite: jordan_redesign.png (2 frames of 96x96 side by side, feet on
row 95, body centred on x = 48: 0 idle, 1 the fist-pump), the .aseprite beside it, and a round-trip
check that the .aseprite re-exports to exactly the same pixels (art_source/imgdiff.pixel_diff).

A bare run never touches Assets/:

    python jordan_export.py <scratch_dir>     # write both files there, for checking
    python jordan_export.py --ship            # write Assets/Characters/Jordan/jordan_redesign.{png,aseprite}

It only ever writes those two file names.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import jordan  # noqa: E402
import kit  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASSET_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Jordan'))
NAME = 'jordan_redesign'
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


def sheet():
    f0, f1 = jordan.frames()
    out = Image.new('RGBA', (192, 96), (0, 0, 0, 0))
    out.alpha_composite(f0, (0, 0))
    out.alpha_composite(f1, (96, 0))
    return out, f0, f1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = ASSET_DIR if argv[0] == '--ship' else os.path.abspath(argv[0])
    os.makedirs(out_dir, exist_ok=True)
    im, f0, f1 = sheet()
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    print('wrote', png, im.size)
    print('wrote', ase)
    print('round trip (.aseprite -> png vs png):', d or 'identical')
    for i, f in enumerate((f0, f1)):
        st = kit.stats(f)
        rows = [y for y in range(96) for x in range(96) if f.getpixel((x, y))[3]]
        print('frame %d: opaque %d, colours %d, black %.1f%%, rows %d..%d'
              % (i, st['opaque'], st['colours'], 100 * st['black'], min(rows), max(rows)))
    st = kit.stats(im)
    print('sheet: opaque %d, colours %d, black %.1f%%' % (st['opaque'], st['colours'], 100 * st['black']))
    return 1 if d else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
