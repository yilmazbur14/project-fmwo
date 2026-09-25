"""Round-trip check: every .aseprite in this folder must re-export byte-identical to
the .png beside it.  Uses art_source/imgdiff.py - a bare getbbox() would compare only
the silhouettes and pass two images that differ in every colour."""
import glob
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from imgdiff import pixel_diff                                    # noqa: E402
from PIL import Image                                             # noqa: E402

ASEPRITE = os.environ.get(
    "ASEPRITE",
    r"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe")


# The armless set ships from armless_build.py straight into Assets as well, so its
# live .aseprite files are checked here too, not just the working copies.
LIVE = os.path.realpath(os.path.join(HERE, "..", "..", "Assets", "Characters",
                                     "Computah"))
LIVE_SHEETS = ("computah_armless", "computah_wrench", "computah_arm_prop")


def _roundtrip(ase, tmp):
    png = ase[:-len(".aseprite")] + ".png"
    out = os.path.join(tmp, os.path.basename(png))
    subprocess.run([ASEPRITE, "-b", ase, "--save-as", out], check=True,
                   capture_output=True)
    return pixel_diff(Image.open(png), Image.open(out))


def main():
    tmp = tempfile.mkdtemp()
    bad = 0
    for ase in sorted(glob.glob(os.path.join(HERE, "*.aseprite"))):
        d = _roundtrip(ase, tmp)
        print("%-34s %s" % (os.path.basename(ase), d or "identical"))
        bad += d is not None
    live_tmp = tempfile.mkdtemp()
    for name in LIVE_SHEETS:
        ase = os.path.join(LIVE, name + ".aseprite")
        if not os.path.exists(ase):
            print("%-34s NOT SHIPPED YET" % ("Assets: " + name + ".aseprite"))
            bad += 1
            continue
        d = _roundtrip(ase, live_tmp)
        print("%-34s %s" % ("Assets: " + name + ".aseprite", d or "identical"))
        bad += d is not None
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
