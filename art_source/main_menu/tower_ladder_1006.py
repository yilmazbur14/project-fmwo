"""Rebuilds the main menu's tower (main_menu_bg.png and main_menu_bg_fx.png) with the members on the 2026-10-06 ladder,
off art_source/main_menu's own rig, writing ONLY under this scratch folder. Every write the rig could make is routed
through a guard that refuses any path outside SCRATCH.

  python tower_rig.py check     the rig, unchanged, against the shipped PNGs (must be identical)
  python tower_rig.py build     the new placement: PNGs, layers and before/after previews into SCRATCH/tower
"""
import os, sys

SCRATCH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.realpath("C:/Users/theyi/OneDrive/Documents/new-game-project")
RIG = os.path.join(PROJ, "art_source", "main_menu")
SHIPPED_BG = os.path.join(PROJ, "Assets", "UI", "Screens", "main_menu_bg.png")
SHIPPED_FX = os.path.join(PROJ, "Assets", "UI", "Screens", "main_menu_bg_fx.png")
OUT = os.path.join(SCRATCH, "tower")

sys.path.insert(0, RIG)
import pngio
import lib


def _guarded(real):
    def write(path, *a, **k):
        p = os.path.realpath(path)
        if not p.startswith(SCRATCH + os.sep):
            raise SystemExit("REFUSED write outside scratch: %s" % p)
        return real(path, *a, **k)
    return write


pngio.write_png = _guarded(pngio.write_png)
lib.write_png = _guarded(lib.write_png)

import bg
import fx
from PIL import Image

# The 2026-10-06 ladder, bottom to top. Each mask keeps its own anchor column (where its feet centre). Neighbouring
# tiers still never share a column, the rule PLACE was built on: the duo tier (Liam & Bixby, now 7) leaves the carpet to
# the tiers either side (Computah 6, Carter 8, both on it), Matt (9) steps off it between Carter and Jordan, and Josh (3)
# steps off it between Mason and Eric. Everyone keeps the side and the offset he had where that rule allows.
NEW_PLACE = [
    ('burak', 1, bg.CX - 40, 14),
    ('mason', 2, bg.CX + 44, 14),
    ('josh', 3, bg.CX - 44, 14),
    ('eric', 4, bg.CX, 23),
    ('danny', 5, bg.CX - 44, 15),
    ('computah', 6, bg.CX, 13),
    ('liam', 7, bg.CX - 38, 14),
    ('bixby', 7, bg.CX + 38, 14),
    ('carter', 8, bg.CX, 12),
    ('matt', 9, bg.CX + 38, 13),
    ('jordan', 10, bg.CX, 10),
]


def canvas_image(c):
    im = Image.new("RGBA", (c.w, c.h))
    im.putdata([tuple(px) for px in _rgba_pixels(c)])
    return im


def _rgba_pixels(c):
    flat = c.to_rgba()
    if isinstance(flat, (bytes, bytearray)):
        return [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]
    out = []
    for row in flat:
        if isinstance(row, (bytes, bytearray)):
            out.extend(tuple(row[i:i + 4]) for i in range(0, len(row), 4))
        elif row and isinstance(row[0], (list, tuple)):
            out.extend(tuple(p) for p in row)
        else:
            out.extend(tuple(row[i:i + 4]) for i in range(0, len(row), 4))
    return out


def build_all():
    comp, parts = bg.build()
    comp2, frames = fx.build()
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    return comp, parts, strip, frames


def same(a, b):
    a, b = a.convert("RGBA"), b.convert("RGBA")
    if a.size != b.size:
        return False, "size %s vs %s" % (a.size, b.size)
    pa, pb = a.load(), b.load()
    diff = 0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            if pa[x, y] != pb[x, y] and not (pa[x, y][3] == 0 and pb[x, y][3] == 0):
                diff += 1
    return diff == 0, "%d pixels differ" % diff


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "build":
        bg.PLACE[:] = NEW_PLACE
    comp, parts, strip, frames = build_all()
    bg_im, fx_im = canvas_image(comp), canvas_image(strip)
    if mode == "check":
        print("bg vs shipped:", same(bg_im, Image.open(SHIPPED_BG)))
        print("fx vs shipped:", same(fx_im, Image.open(SHIPPED_FX)))
        return
    os.makedirs(os.path.join(OUT, "layers"), exist_ok=True)
    bg_im.save(os.path.join(OUT, "main_menu_bg.png"))
    fx_im.save(os.path.join(OUT, "main_menu_bg_fx.png"))
    for i, (name, lc) in enumerate(parts):
        canvas_image(lc).save(os.path.join(OUT, "layers", "%d_%s.png" % (i, name)))
    # fx overlay pixels that land on a member: the corner-post lanterns flicker over whatever is there, so a member
    # standing in front of one would be painted over on that frame.
    members = dict(parts)["members"]
    hits = 0
    for f in frames:
        for y in range(bg.H):
            for x in range(bg.W):
                if f.p[y][x] is not None and members.p[y][x] is not None:
                    hits += 1
    print("fx overlay pixels over a member, all frames:", hits)
    before = Image.open(SHIPPED_BG).convert("RGBA")
    after = bg_im
    W, H = before.size
    pair = Image.new("RGBA", (W * 2 + 8, H), (255, 255, 255, 255))
    pair.paste(before, (0, 0))
    pair.paste(after, (W + 8, 0))
    pair.resize((pair.width * 2, pair.height * 2), Image.NEAREST).save(os.path.join(OUT, "before_after_2x.png"))
    x0, w = bg.CX - 132, 264
    crop = lambda im: im.crop((x0, 0, x0 + w, 330))
    zoom = Image.new("RGBA", (w * 2 + 4, 330), (255, 255, 255, 255))
    zoom.paste(crop(before), (0, 0))
    zoom.paste(crop(after), (w + 4, 0))
    zoom.resize((zoom.width * 3, zoom.height * 3), Image.NEAREST).save(os.path.join(OUT, "before_after_tower_3x.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
