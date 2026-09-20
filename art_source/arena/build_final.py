"""
Final arena textures - direction A, approved without changes - and their .aseprite sources.

Run it under the E-core wrapper (this machine's P-cores have corrupted pure-Python output without
crashing); the generator subprocesses inherit the affinity:

    pyE.cmd build_final.py --stage <scratch dir> [--approved <dir>] [--install <Assets/Environment>]

1. Generates both textures twice, in two separate processes, and refuses to go on unless the two
   runs are byte-identical.
2. Round-trips each through Aseprite in batch mode: generated PNG -> .aseprite -> PNG. The shipped
   PNG is Aseprite's own export of the .aseprite, so the source reproduces it exactly. Checked:
   every pixel survives, a second export of the .aseprite is byte-identical to the shipped PNG, and
   re-saving the shipped PNG as .aseprite and exporting that is byte-identical too.
3. --approved: also requires the pixels to equal the textures the design pass was approved on.
4. --install: copies each .png/.aseprite pair into that folder, only if every check passed.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASEPRITE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
TEXTURES = (
    # (shipped name, the design pass's name for the same art)
    ("arena_mat", "mat_a"),
    ("arena_ringside", "ringside_a"),
)


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


def check(ok, label):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--approved", help="dir holding the design pass's mat_a.png / ringside_a.png")
    ap.add_argument("--install", help="folder to copy the finished .png/.aseprite pairs into")
    args = ap.parse_args()

    runs = [os.path.join(args.stage, "run1"), os.path.join(args.stage, "run2")]
    for d in runs:
        shutil.rmtree(d, ignore_errors=True)
        subprocess.run([sys.executable, os.path.join(HERE, "gen_arena.py"), "--final", "--out", d],
                       check=True)

    final = os.path.join(args.stage, "final")
    shutil.rmtree(final, ignore_errors=True)
    os.makedirs(final)
    all_ok = True

    for name, design_name in TEXTURES:
        print(name)
        gen = [os.path.join(d, name + ".png") for d in runs]
        all_ok &= check(sha(gen[0]) == sha(gen[1]),
                        f"two generator processes byte-identical  {sha(gen[0])[:16]}")

        src = os.path.join(final, name + ".aseprite")
        png = os.path.join(final, name + ".png")
        again = os.path.join(final, name + ".export2.png")
        aseprite(gen[0], "--save-as", src)
        aseprite(src, "--save-as", png)
        aseprite(src, "--save-as", again)

        size, px = pixels(png)
        all_ok &= check(pixels(gen[0]) == (size, px), f"Aseprite kept every pixel  {size[0]}x{size[1]}")
        all_ok &= check(sha(png) == sha(again), f".aseprite re-export byte-identical  {sha(png)[:16]}")

        # the other direction: the shipped PNG itself survives PNG -> .aseprite -> PNG
        src2 = os.path.join(final, name + ".from_png.aseprite")
        back = os.path.join(final, name + ".from_png.png")
        aseprite(png, "--save-as", src2)
        aseprite(src2, "--save-as", back)
        all_ok &= check(sha(back) == sha(png), "shipped PNG -> .aseprite -> PNG byte-identical")

        if args.approved:
            ref = os.path.join(args.approved, design_name + ".png")
            all_ok &= check(pixels(ref) == (size, px), f"pixels equal the approved {design_name}.png")

        for p in (again, src2, back):
            os.remove(p)

    if not all_ok:
        raise SystemExit("checks failed - nothing installed")
    print("all checks passed")

    if args.install:
        os.makedirs(args.install, exist_ok=True)
        for name, _ in TEXTURES:
            for ext in (".png", ".aseprite"):
                dst = os.path.join(args.install, name + ext)
                shutil.copyfile(os.path.join(final, name + ext), dst)
                ok = sha(dst) == sha(os.path.join(final, name + ext))
                print(f"  installed {dst}  {sha(dst)[:16]}  {'verified' if ok else 'COPY MISMATCH'}")
                if not ok:
                    raise SystemExit("install copy mismatch")


if __name__ == "__main__":
    main()
