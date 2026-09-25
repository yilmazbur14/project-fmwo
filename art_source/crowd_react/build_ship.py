"""Build, verify and - with --ship - install the crowd reaction sheets with their .aseprite sources.

    python build_ship.py --stage <scratch dir>              build and verify only
    python build_ship.py --stage <scratch dir> --ship       ...then install into Assets/Environment

Ships two NEW files (crowd_v2.png is never touched):
  crowd_v3.png              4480x40,  7 frames of 640x40   the top band
  arena_ringside_crowd.png  4480x360, 7 frames of 640x360  the ringside overlay
each with its .aseprite beside it, in crowd_v2.aseprite's layout: one layer "Flattened", frame
durations 350/350/350/150/150/200/200 ms, tags idle 1-3, cheer 4-5, boo 6-7.

Per sheet, every one of these must hold or nothing is installed:
  1. the generator runs twice, in two separate processes, and the two PNGs are byte-identical
  2. Aseprite builds the .aseprite from it (crowd_sheet.lua); the shipped PNG is Aseprite's own
     horizontal-sheet export of that .aseprite, so the source reproduces it exactly:
       - its pixels equal the generator's (imgdiff.pixel_diff - never a bare getbbox)
       - a second export is byte-identical to the first
       - the frames, durations and tags read back from the .aseprite are the ones above
  3. crowd_v3's frames 0-4 equal crowd_v2.png pixel for pixel (neutral and cheer don't move);
     the ringside overlay's own self-check (its idle frame equals arena_ringside.png's crowd)
     runs inside ringside_react.py and fails the build if it doesn't hold
--ship refuses to overwrite an existing file unless --replace is given, and checks every copy.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from PIL import Image  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASEPRITE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
LUA = os.path.join(HERE, "crowd_sheet.lua")
ENV = os.path.realpath(os.path.join(HERE, "..", "..", "Assets", "Environment"))
DURATIONS = [350, 350, 350, 150, 150, 200, 200]
TAGS = [("idle", 0, 2), ("cheer", 3, 4), ("boo", 5, 6)]      # 0-based, as Aseprite's JSON reports
SHEETS = [
    # (generator, output name, frame height)
    ("crowd_react.py", "crowd_v3", 40),
    ("ringside_react.py", "arena_ringside_crowd", 360),
]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"failed: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def aseprite(*args):
    return run([ASEPRITE, "-b", *args])


def check(ok, label):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    return ok


def build(stage, gen, name, fh):
    print(name)
    ok = True
    runs = [os.path.join(stage, "run1"), os.path.join(stage, "run2")]
    for d in runs:
        out = run([sys.executable, os.path.join(HERE, gen), "--out", d])
        if "self-check" in out or "idle vs" in out:
            print("   ", out.strip().splitlines()[0])
    pngs = [os.path.join(d, name + ".png") for d in runs]
    ok &= check(sha(pngs[0]) == sha(pngs[1]), f"two generator processes byte-identical  {sha(pngs[0])[:16]}")

    final = os.path.join(stage, "final")
    os.makedirs(final, exist_ok=True)
    src = os.path.join(final, name + ".aseprite")
    png = os.path.join(final, name + ".png")
    again = os.path.join(final, name + ".export2.png")
    aseprite("--script-param", f"strip={pngs[0]}", "--script-param", "fw=640",
             "--script-param", f"fh={fh}", "--script-param", "durations=" + ",".join(map(str, DURATIONS)),
             "--script-param", "tags=" + ",".join(f"{t}:{a + 1}-{b + 1}" for t, a, b in TAGS),
             "--script-param", f"out={src}", "--script", LUA)
    aseprite(src, "--sheet", png, "--sheet-type", "horizontal")
    aseprite(src, "--sheet", again, "--sheet-type", "horizontal")

    gen_im, out_im = Image.open(pngs[0]), Image.open(png)
    ok &= check(out_im.size == (640 * len(DURATIONS), fh), f"sheet is {out_im.size[0]}x{out_im.size[1]}")
    d = pixel_diff(gen_im, out_im)
    ok &= check(d is None, "the .aseprite keeps every pixel of the generator's sheet" + ("" if d is None else f": {d}"))
    ok &= check(sha(png) == sha(again), f"a second export of the .aseprite is byte-identical  {sha(png)[:16]}")

    meta = os.path.join(stage, name + ".json")
    aseprite("--list-tags", "--list-layers", src, "--data", meta, "--format", "json-array",
             "--sheet", os.path.join(stage, name + ".meta.png"), "--sheet-type", "horizontal")
    with open(meta, encoding="utf-8") as f:
        m = json.load(f)
    durs = [fr["duration"] for fr in m["frames"]]
    tags = [(t["name"], t["from"], t["to"]) for t in m["meta"].get("frameTags", [])]
    layers = [layer["name"] for layer in m["meta"].get("layers", [])]
    ok &= check(durs == DURATIONS, f"frame durations {durs}")
    ok &= check(tags == TAGS, f"tags {tags}")
    ok &= check(layers == ["Flattened"], f"layers {layers}")

    if name == "crowd_v3":
        v2 = Image.open(os.path.join(ENV, "crowd_v2.png"))
        d = pixel_diff(out_im.crop((0, 0, 640 * 5, 40)), v2)
        ok &= check(d is None, "frames 0-4 equal crowd_v2.png (neutral and cheer unchanged)" + ("" if d is None else f": {d}"))
    os.remove(again)
    return ok, [png, src]


def ship(files, replace):
    for path in files:
        dst = os.path.join(ENV, os.path.basename(path))
        if os.path.realpath(os.path.dirname(dst)) != ENV:
            raise SystemExit(f"refusing: {dst} is not in Assets/Environment")
        if os.path.basename(dst).startswith("crowd_v2"):
            raise SystemExit("refusing to touch crowd_v2")
        if os.path.exists(dst) and not replace:
            raise SystemExit(f"{dst} exists - pass --replace to overwrite it")
        shutil.copyfile(path, dst)
        same = sha(dst) == sha(path)
        print(f"  installed {dst}  {sha(dst)[:16]}  {'verified' if same else 'COPY MISMATCH'}")
        if not same:
            raise SystemExit("install copy mismatch")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, help="scratch folder for both builds and the checks")
    ap.add_argument("--ship", action="store_true", help="install into Assets/Environment if every check passes")
    ap.add_argument("--replace", action="store_true", help="allow overwriting files already shipped")
    args = ap.parse_args()
    if os.path.realpath(args.stage).startswith(os.path.realpath(os.path.join(HERE, "..", "..", "Assets"))):
        raise SystemExit("the stage folder must not be inside Assets")
    for d in ("run1", "run2", "final"):
        shutil.rmtree(os.path.join(args.stage, d), ignore_errors=True)
    all_ok, files = True, []
    for gen, name, fh in SHEETS:
        ok, out = build(args.stage, gen, name, fh)
        all_ok &= ok
        files += out
    if not all_ok:
        raise SystemExit("checks failed - nothing installed")
    print("all checks passed")
    if args.ship:
        ship(files, args.replace)


if __name__ == "__main__":
    main()
