"""Saves an editable .aseprite next to every exported sheet (Aseprite CLI, batch mode), then round-trips each back to
PNG in the work folder and checks it is pixel-identical."""
import subprocess, os, glob
import numpy as np
from PIL import Image
from common import APPROVAL, WORK

A = r"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe"
pngs = sorted(glob.glob(APPROVAL + "/player/*.png") + glob.glob(APPROVAL + "/take_a_blue/*.png") +
              glob.glob(APPROVAL + "/take_b_hype/*.png"))
bad = []
for p in pngs:
    out = p[:-4] + ".aseprite"
    subprocess.run([A, "-b", p, "--save-as", out], check=True, timeout=120, capture_output=True)
    rt = os.path.join(WORK, "rt_check.png")
    subprocess.run([A, "-b", out, "--save-as", rt], check=True, timeout=120, capture_output=True)
    a = np.asarray(Image.open(p).convert("RGBA")).astype(int)
    b = np.asarray(Image.open(rt).convert("RGBA")).astype(int)
    if a.shape != b.shape or (a[..., 3] > 0).sum() != (b[..., 3] > 0).sum() or np.abs(a - b)[a[..., 3] > 0].max(initial=0):
        bad.append(p)
print(len(pngs), "sheets saved as .aseprite; mismatches:", bad)
