"""Write Eric's entrance sheet to Assets.

  python export.py            # frames 0-8, the walk-in and arrival
  python export.py --ase      # and round-trip the .aseprite

Partial on purpose: frames 0-8 ship now so the build stops showing him walking
in with his sword already drawn. Frames 9-15 (grip, heave, pull, raise, point)
append later and hframes goes to 16.

256x192 per frame, feet on row 191, body centred on column 128, horizontal
strip - hframes = N, vframes = 1, the project's convention.
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vs_card"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from imgdiff import pixel_diff
import walk as W
from pxlib import black_ratio

OUT = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric"
SHEET_NAME = "eric_entrance"
ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
SCRATCH = ("C:/Users/theyi/AppData/Local/Temp/claude/"
           "C--Users-theyi-OneDrive-Documents-new-game-project/"
           "a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/eric_entrance/_rt")


def sheet():
    frames = W.build()
    im = Image.new("RGBA", (W.FW * len(frames), W.FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.alpha_composite(f, (i * W.FW, 0))
    return im, len(frames)


def roundtrip(png):
    os.makedirs(SCRATCH, exist_ok=True)
    ase = os.path.splitext(png)[0] + ".aseprite"
    back = os.path.join(SCRATCH, "back.png")
    if os.path.exists(back):
        os.remove(back)
    r1 = subprocess.run([ASE, "-b", png, "--save-as", ase], capture_output=True, text=True)
    r2 = subprocess.run([ASE, "-b", ase, "--save-as", back], capture_output=True, text=True)
    if r1.returncode or r2.returncode or not os.path.exists(back):
        return ase, "aseprite failed rc=%s/%s" % (r1.returncode, r2.returncode)
    a, b = Image.open(png).convert("RGBA"), Image.open(back).convert("RGBA")
    why = pixel_diff(a, b)
    return ase, ("OK" if why is None else why)


if __name__ == "__main__":
    im, n = sheet()
    png = os.path.join(OUT, SHEET_NAME + ".png")
    im.save(png, optimize=False)
    k, o, pct = black_ratio(im)
    print("%s  %dx%d   hframes = %d, vframes = 1" % (SHEET_NAME + ".png", im.width, im.height, n))
    print("black %.1f%% of opaque px (his body-only benchmark is 24-26%%)" % pct)
    print("colours %d" % len({q[:3] for q in im.convert("RGBA").getdata() if q[3] > 128}))
    if "--ase" in sys.argv:
        ase, status = roundtrip(png)
        print("round-trip %s: %s" % (os.path.basename(ase), status))
