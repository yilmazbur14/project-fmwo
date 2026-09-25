"""Write matt.png (2 frames of 96x96 in a strip: idle, then roar) and matt.aseprite, then
round-trip the .aseprite through Aseprite and compare it with the PNG pixel for pixel.

    python export.py <out_dir> <scratch_dir>

Both directories are required on purpose. There is no default: a bare run of an art export
script once overwrote live Assets in this project, so this one refuses to guess.
The shipped files live in Assets/Characters/Matt/.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))           # art_source, for imgdiff
import matt  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'


def sheet():
    f0, f1 = matt.frames()
    out = Image.new('RGBA', (192, 96), (0, 0, 0, 0))
    out.paste(f0, (0, 0))
    out.paste(f1, (96, 0))
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    out_dir, scratch = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(scratch, exist_ok=True)
    im = sheet()
    png = os.path.join(out_dir, 'matt.png')
    ase = os.path.join(out_dir, 'matt.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = os.path.join(scratch, 'matt_roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    on_disk = pixel_diff(im, Image.open(png))
    round_trip = pixel_diff(im, Image.open(back))
    print('wrote', png)
    print('wrote', ase)
    print('png on disk vs build:', on_disk or 'identical')
    print('aseprite round trip vs build:', round_trip or 'identical')
    if on_disk or round_trip:
        sys.exit(1)


if __name__ == '__main__':
    main()
