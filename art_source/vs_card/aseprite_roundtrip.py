"""Saves a .aseprite beside every card PNG and proves the round-trip is lossless.

  python aseprite_roundtrip.py <dir>

For each PNG: import it into Aseprite, save the .aseprite, export that back to a
temporary PNG, and compare pixel-for-pixel with the original. Any mismatch is
reported and the file is left alone rather than shipped.
"""
import sys, os, subprocess, tempfile, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from imgdiff import pixel_diff

ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"


def run(args):
    r = subprocess.run([ASE, "-b"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("aseprite failed: %s\n%s" % (args, r.stderr or r.stdout))
    return r


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def roundtrip(png):
    ase = os.path.splitext(png)[0] + ".aseprite"
    run([png, "--save-as", ase])
    with tempfile.TemporaryDirectory() as td:
        back = os.path.join(td, "back.png")
        run([ase, "--save-as", back])
        a = Image.open(png).convert("RGBA")
        b = Image.open(back).convert("RGBA")
        if a.size != b.size:
            return ase, "SIZE %s vs %s" % (a.size, b.size)
        why = pixel_diff(a, b)
        return ase, ("OK" if why is None else "DIFF " + why)


if __name__ == "__main__":
    d = sys.argv[1]
    pngs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    bad = 0
    for f in pngs:
        p = os.path.join(d, f)
        ase, status = roundtrip(p)
        if status != "OK":
            bad += 1
        print("%-28s -> %-28s %-12s png=%s ase=%s" %
              (f, os.path.basename(ase), status, sha(p), sha(ase)))
    print("\n%d file(s), %d mismatch(es)" % (len(pngs), bad))
