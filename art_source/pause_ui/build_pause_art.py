"""Builds Assets/UI/Pause: the in-fight pause screen's final art, 1x + _3x, each with a .aseprite.

  python art_source/pause_ui/build_pause_art.py            write the set and verify it
  python art_source/pause_ui/build_pause_art.py --check    build twice, diff against what shipped,
                                                           verify the .aseprite round-trips; writes
                                                           nothing
  PAUSE_DEST=<dir>                                         stage somewhere else than Assets/UI/Pause

What is verified on every run, before a byte is written:
  * every opaque pixel is DB32 and alpha is only 0 or 255
  * the four 9-slices pass ui_kit.kitlib.check_nine_slice at margin 8 - edges constant along their
    axis, flat centre, bleed-safe innermost ring - so Godot can stretch them to any row or panel
  * the frames are left/right and top/bottom symmetric in silhouette and keyline
  * black ratio and colour count are reported against the shipped kit
  * two independent builds are byte-identical, and the _3x is exactly nearest-neighbour 3x of 1x
  * each .aseprite exports back to a PNG identical to the one beside it

Nothing here touches project.godot, any .tscn or any .gd. USE_FINAL_PAUSE_ART stays false until a
coder flips it.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "art_source", "ui_kit"))

from PIL import Image  # noqa: E402
from kitlib import DB32_SET, grid_to_pix, check_db32, check_nine_slice  # noqa: E402
import pause_art  # noqa: E402
import pause_title  # noqa: E402

PROJ = os.path.join(ROOT, "")
DEST = os.environ.get("PAUSE_DEST", os.path.join(ROOT, "Assets", "UI", "Pause"))
# What the shipped kit measures, for the report. (colours, black % of opaque pixels)
KIT_BENCHMARK = {
    "ui_button": (12, 29.8),
    "ui_dialogue_frame": (11, 25.7),
    "ui_card_frame": (11, 33.3),
}
SCALE = 3

ASEPRITE_CANDIDATES = [
    "C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe",
    "C:/Program Files/Aseprite/Aseprite.exe",
]

# One layer named "art", and a grid matching the 9-slice margin so the slice lines are visible when
# the file is opened for a revision.
ASEPRITE_LUA = r'''
local dir = app.params["dir"]
for spec in string.gmatch(app.params["names"], "[^,]+") do
  local n, m = string.match(spec, "([^:]+):(%d+)")
  local spr = app.open(dir .. "/" .. n .. ".png")
  if spr == nil then
    print("FAILED to open " .. n)
  else
    spr.layers[1].name = "art"
    local mm = tonumber(m)
    if mm > 0 then spr.gridBounds = Rectangle(mm, mm, spr.width - mm * 2, spr.height - mm * 2) end
    spr:saveAs(dir .. "/" .. n .. ".aseprite")
    print(string.format("saved %s.aseprite %dx%d", n, spr.width, spr.height))
    spr:close()
  end
end
'''


# ---------------------------------------------------------------- pixels


def scale_nn(pix, s):
    return [[pix[y // s][x // s] for x in range(len(pix[0]) * s)] for y in range(len(pix) * s)]


def img_to_pix(im):
    w, h = im.size
    d = im.load()
    return [[d[x, y] for x in range(w)] for y in range(h)]


def pix_to_img(pix):
    im = Image.new("RGBA", (len(pix[0]), len(pix)))
    d = im.load()
    for y, row in enumerate(pix):
        for x, p in enumerate(row):
            d[x, y] = p
    return im


def stats(pix):
    flat = [p for row in pix for p in row]
    opaque = [p for p in flat if p[3] == 255]
    colours = {"%02x%02x%02x" % p[:3] for p in opaque}
    black = sum(1 for p in opaque if p[:3] == (0, 0, 0))
    return len(colours), (100.0 * black / len(opaque) if opaque else 0.0), len(opaque), len(flat)


def build_all():
    """{name: (pix, margin_or_None)} at 1x. Deterministic: no clock, no randomness, no dict order
    dependence."""
    out = {}
    for name, (rows, margin, pal) in sorted(pause_art.build().items()):
        _, _, pix = grid_to_pix(rows, pal)
        out[name] = (pix, margin)
    out["pause_title"] = (img_to_pix(pause_title.build()), None)
    return out


# ---------------------------------------------------------------- checks


def verify(built):
    problems = []
    for name, (pix, margin) in sorted(built.items()):
        w, h = len(pix[0]), len(pix)
        alphas = {p[3] for row in pix for p in row}
        if not alphas <= {0, 255}:
            problems.append("%s: alpha is not binary (%s)" % (name, sorted(alphas)))
        bad = check_db32(w, h, pix, name)
        if bad:
            problems.append("%s: off-DB32 %s" % (name, sorted(bad)))
        if margin:
            for p in check_nine_slice(w, h, pix, margin):
                problems.append("%s: %s" % (name, p))
            key = [[(p[:3] == (0, 0, 0), p[3] == 0) for p in row] for row in pix]
            if key != [list(reversed(r)) for r in key]:
                problems.append("%s: keyline is not left/right symmetric" % name)
            if key != list(reversed(key)):
                problems.append("%s: keyline is not top/bottom symmetric" % name)
    return problems


def report(built):
    print("%-22s %9s %6s %8s   kit: ui_button 12/29.8%%  dialogue 11/25.7%%  card 11/33.3%%"
          % ("asset", "size", "cols", "black"))
    for name, (pix, margin) in sorted(built.items()):
        cols, blk, _, _ = stats(pix)
        print("%-22s %4dx%-4d %6d %7.1f%%  %s"
              % (name, len(pix[0]), len(pix), cols, blk,
                 "9-slice margin %d (%d at 3x)" % (margin, margin * SCALE) if margin else "drawn whole"))


# ---------------------------------------------------------------- aseprite


def aseprite_exe():
    import json
    cfg = os.path.expanduser("~/.config/pixel-mcp/config.json")
    if os.path.exists(cfg):
        try:
            with open(cfg, encoding="utf-8") as f:
                p = json.load(f).get("aseprite_path")
            if p and os.path.exists(p):
                return p
        except Exception:
            pass
    for p in ASEPRITE_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def write_aseprite(dest, specs):
    """specs: [(name, margin)] - margin 0 for a drawn-whole image."""
    exe = aseprite_exe()
    if not exe:
        print("  ! Aseprite not found: .aseprite files NOT written")
        return False
    lua = os.path.join(tempfile.gettempdir(), "pause_ui_to_aseprite.lua")
    with open(lua, "w", encoding="utf-8") as f:
        f.write(ASEPRITE_LUA)
    arg = ",".join("%s:%d" % (n, m) for n, m in specs)
    r = subprocess.run([exe, "-b", "--script-param", "dir=" + dest.replace("\\", "/"),
                        "--script-param", "names=" + arg, "--script", lua],
                       capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if out:
        print("\n".join("  " + ln for ln in out.splitlines()))
    if r.returncode != 0:
        print("  ! aseprite failed:", (r.stderr or "").strip())
        return False
    return True


def check_roundtrip(dest, names):
    """Every .aseprite must export back to the PNG beside it, pixel for pixel."""
    exe = aseprite_exe()
    if not exe:
        return ["Aseprite not found: round-trip unverified"]
    problems = []
    with tempfile.TemporaryDirectory() as td:
        for n in names:
            ase = os.path.join(dest, n + ".aseprite")
            png = os.path.join(dest, n + ".png")
            if not os.path.exists(ase):
                problems.append("%s.aseprite missing" % n)
                continue
            back = os.path.join(td, n + "_back.png")
            r = subprocess.run([exe, "-b", ase, "--save-as", back], capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(back):
                problems.append("%s: aseprite could not re-export (%s)" % (n, (r.stderr or "").strip()))
                continue
            a = Image.open(png).convert("RGBA")
            b = Image.open(back).convert("RGBA")
            if a.size != b.size:
                problems.append("%s: round-trip size %s vs %s" % (n, a.size, b.size))
            elif img_to_pix(a) != img_to_pix(b):
                problems.append("%s: round-trip pixels differ" % n)
    return problems


# ---------------------------------------------------------------- disk


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def files_for(built):
    """[(name, pix, margin)] for every PNG the set ships, 1x then _3x."""
    out = []
    for name, (pix, margin) in sorted(built.items()):
        out.append((name, pix, margin or 0))
        out.append((name + "_%dx" % SCALE, scale_nn(pix, SCALE), (margin or 0) * SCALE))
    return out


def write_set(dest, built):
    os.makedirs(dest, exist_ok=True)
    for name, pix, _ in files_for(built):
        pix_to_img(pix).save(os.path.join(dest, name + ".png"))
    return [(n, m) for n, _, m in files_for(built)]


def main():
    check = "--check" in sys.argv
    built = build_all()

    problems = verify(built)
    again = build_all()
    if {k: v[0] for k, v in again.items()} != {k: v[0] for k, v in built.items()}:
        problems.append("build is not deterministic: two runs differ")

    report(built)
    if problems:
        print("\nFAILED:")
        for p in problems:
            print("  -", p)
        return 1

    names = [n for n, _, _ in files_for(built)]
    if check:
        # Rebuild into a scratch folder and diff every byte against what is on disk.
        with tempfile.TemporaryDirectory() as td:
            write_set(td, built)
            missing, diff = [], []
            for n in names:
                live = os.path.join(DEST, n + ".png")
                if not os.path.exists(live):
                    missing.append(n + ".png")
                elif sha(live) != sha(os.path.join(td, n + ".png")):
                    diff.append(n + ".png")
            rt = check_roundtrip(DEST, names) if not missing else ["not checked: PNGs missing"]
        print("\n--check against %s" % DEST)
        print("  %d png(s) expected, %d missing, %d differing" % (len(names), len(missing), len(diff)))
        for n in missing + diff:
            print("   !", n)
        for p in rt:
            print("   !", p)
        ok = not missing and not diff and not rt
        print("  " + ("CLEAN: shipped art matches a fresh build and every .aseprite round-trips"
                      if ok else "DIRTY"))
        return 0 if ok else 1

    specs = write_set(DEST, built)
    print("\nwrote %d png(s) to %s" % (len(specs), DEST))
    ok = write_aseprite(DEST, specs)
    if ok:
        for p in check_roundtrip(DEST, names):
            print("   !", p)
            ok = False
    # A second build straight to a scratch folder proves the writer is deterministic too.
    with tempfile.TemporaryDirectory() as td:
        write_set(td, built)
        for n in names:
            if sha(os.path.join(DEST, n + ".png")) != sha(os.path.join(td, n + ".png")):
                print("   ! %s.png is not reproducible" % n)
                ok = False
    print("build ok" if ok else "build finished WITH PROBLEMS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
