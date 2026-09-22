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


def main():
    tmp = tempfile.mkdtemp()
    bad = 0
    for ase in sorted(glob.glob(os.path.join(HERE, "*.aseprite"))):
        png = ase[:-len(".aseprite")] + ".png"
        out = os.path.join(tmp, os.path.basename(png))
        subprocess.run([ASEPRITE, "-b", ase, "--save-as", out], check=True,
                       capture_output=True)
        d = pixel_diff(Image.open(png), Image.open(out))
        print("%-34s %s" % (os.path.basename(ase), d or "identical"))
        bad += d is not None
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
