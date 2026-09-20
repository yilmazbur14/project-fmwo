"""Rebuild the shipped arena textures from scratch and compare them, byte for byte, with the files in
Assets/Environment. Writes nothing into the project.

    pyE.cmd verify_shipped.py        (run it twice: two independent processes agreeing is the check)

Why this exists: this machine's P-cores corrupt computation, and the dangerous case is a run that
finishes and writes a subtly wrong pixel (see art_source/carter_akuma/verify_shipped.py, the model
for this). gen_arena.py is fully deterministic and so is Aseprite's export, so a fresh build that
matches the disk proves the files are what the code means them to be. Run it under the E-core
wrapper; the generator and Aseprite run as child processes and inherit the pinning.

Per texture, all three must hold:
  pixels  the fresh generator output has exactly the pixels of the PNG on disk
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

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.abspath(os.path.join(HERE, "..", "..", "Assets", "Environment"))
ASEPRITE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
NAMES = ("arena_mat", "arena_ringside")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def pixels(path):
    im = Image.open(path)
    return im.size, im.convert("RGBA").tobytes()


def aseprite(*args):
    r = subprocess.run([ASEPRITE, "-b", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"aseprite failed on {args}:\n{r.stdout}\n{r.stderr}")


def main():
    tmp = tempfile.mkdtemp(prefix="arena_verify_")
    bad = 0
    try:
        subprocess.run([sys.executable, os.path.join(HERE, "gen_arena.py"), "--final", "--out", tmp],
                       check=True, stdout=subprocess.DEVNULL)
        for name in NAMES:
            gen = os.path.join(tmp, name + ".png")
            src = os.path.join(tmp, name + ".aseprite")
            png = os.path.join(tmp, name + ".export.png")
            aseprite(gen, "--save-as", src)
            aseprite(src, "--save-as", png)
            disk_png = os.path.join(ENV, name + ".png")
            disk_src = os.path.join(ENV, name + ".aseprite")
            checks = {
                "pixels": pixels(gen) == pixels(disk_png),
                "source": sha(src) == sha(disk_src),
                "export": sha(png) == sha(disk_png),
            }
            print(f"{name:16s} " + "  ".join(f"{k} {'match' if v else 'DIFFERS'}" for k, v in checks.items())
                  + f"   disk png {sha(disk_png)[:16]}  aseprite {sha(disk_src)[:16]}")
            bad += sum(not v for v in checks.values())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL MATCH" if bad == 0 else f"{bad} CHECK(S) FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
