"""Rebuild the shipped crowd reaction sheets from scratch and compare them with Assets/Environment.
Writes nothing into the project (a temp folder only).

    python verify_shipped.py        (run it twice: two independent processes agreeing is the check)

Per sheet, all three must hold:
  pixels  the fresh generator output has exactly the pixels of the PNG on disk (imgdiff.pixel_diff)
  source  the .aseprite built from it is byte-identical to the .aseprite on disk
  export  exporting that .aseprite gives a PNG byte-identical to the PNG on disk
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from PIL import Image  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

import build_ship as B  # noqa: E402


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    tmp = tempfile.mkdtemp(prefix="crowd_verify_")
    bad = 0
    try:
        for gen, name, fh in B.SHEETS:
            subprocess.run([sys.executable, os.path.join(HERE, gen), "--out", tmp], check=True,
                           stdout=subprocess.DEVNULL)
            gen_png = os.path.join(tmp, name + ".png")
            src = os.path.join(tmp, name + ".fresh.aseprite")
            png = os.path.join(tmp, name + ".fresh.png")
            B.aseprite("--script-param", f"strip={gen_png}", "--script-param", "fw=640",
                       "--script-param", f"fh={fh}",
                       "--script-param", "durations=" + ",".join(map(str, B.DURATIONS)),
                       "--script-param", "tags=" + ",".join(f"{t}:{a + 1}-{b + 1}" for t, a, b in B.TAGS),
                       "--script-param", f"out={src}", "--script", B.LUA)
            B.aseprite(src, "--sheet", png, "--sheet-type", "horizontal")
            disk_png = os.path.join(B.ENV, name + ".png")
            disk_src = os.path.join(B.ENV, name + ".aseprite")
            checks = {
                "pixels": pixel_diff(Image.open(gen_png), Image.open(disk_png)) is None,
                "source": sha(src) == sha(disk_src),
                "export": sha(png) == sha(disk_png),
            }
            print(f"{name:22s} " + "  ".join(f"{k} {'match' if v else 'DIFFERS'}" for k, v in checks.items())
                  + f"   disk png {sha(disk_png)[:16]}  aseprite {sha(disk_src)[:16]}")
            bad += sum(not v for v in checks.values())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL MATCH" if bad == 0 else f"{bad} CHECK(S) FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
