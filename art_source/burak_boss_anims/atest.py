"""python atest.py - the rig's regression test: the default Pose must BE the approved idle frame and
the shot Pose the approved shot frame without its baked-in effects, pixel for pixel (imgdiff)."""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import akit  # noqa: E402
import burak as B  # noqa: E402
import kit  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

APPROVED = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'BurakBoss', 'burak_boss.png'))


def main():
    sheet = Image.open(APPROVED).convert('RGBA')
    f0 = sheet.crop((0, 0, 96, 96))
    ok = True
    d = pixel_diff(akit.image(akit.idle0()), f0)
    print('idle Pose vs approved frame 0:', d or 'identical')
    ok = ok and not d
    shot_clean = kit.image(B.frame_px(1, fx=False))
    d = pixel_diff(kit.image(akit.render(akit.shot0(), pinholes=False)), shot_clean)
    print('shot Pose vs approved frame 1 without effects:', d or 'identical')
    ok = ok and not d
    fixed = akit.render(akit.shot0())
    raw = akit.render(akit.shot0(), pinholes=False)
    changed = sorted(q for q in set(fixed) | set(raw) if fixed.get(q) != raw.get(q))
    print('   the fight set closes its pinholes; on the shot frame that changes:', changed)
    ok = ok and changed == [(77, 57)]
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
