"""Final build of the FMWO UI kit.
Writes 1x + 3x PNGs into Assets/UI (never overwriting a file this script did
not create), grid dumps + verification renders into ./final/."""
import os, json
from kitlib import *
import kit_assets

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
UI = PROJ + "Assets/UI/"
OUT = "final/"
os.makedirs(OUT, exist_ok=True)
MANIFEST = OUT + "created_files.json"
created = set(json.load(open(MANIFEST))) if os.path.exists(MANIFEST) else set()

EXPECT = {  # name: (w, h, margin)
    'ui_dialogue_frame': (32, 32, 10),
    'ui_portrait_frame': (24, 24, 8),
    'ui_card_frame': (24, 24, 8),
    'ui_button': (24, 24, 8),
    'ui_button_hover': (24, 24, 8),
    'ui_button_pressed': (24, 24, 8),
    'ui_dialogue_next': (16, 8, None),
}

A = kit_assets.build(plates_on_buttons=True, portrait_style='deep')
assert set(A) == set(EXPECT), set(A) ^ set(EXPECT)


def safe_write(path, w, h, px):
    if os.path.exists(path) and path not in created:
        raise SystemExit(f"REFUSING to overwrite pre-existing file {path}")
    write_png(path, w, h, px)
    created.add(path)


built = {}
for name, (rows, m, pal) in A.items():
    ew, eh, em = EXPECT[name]
    w, h, px = grid_to_pix(rows, pal)
    assert (w, h) == (ew, eh), (name, w, h)
    assert m == em, (name, m, em)
    bad = check_db32(w, h, px)
    assert not bad, (name, bad)
    alphas = {p[3] for r in px for p in r}
    assert alphas <= {0, 255}, (name, alphas)
    if m:
        probs = check_nine_slice(w, h, px, m)
        assert not probs, (name, probs)
    built[name] = (w, h, px, m)
    with open(OUT + name + ".txt", "w") as f:
        f.write("\n".join(rows) + "\n")

# arrow: frame 1 must be frame 0 moved down exactly 1px
w, h, px, _ = built['ui_dialogue_next']
f0 = [r[0:8] for r in px]
f1 = [r[8:16] for r in px]
assert all(p == TRANSPARENT for p in f0[7]), "frame0 needs an empty bottom row"
assert all(p == TRANSPARENT for p in f1[0]), "frame1 needs an empty top row"
assert f1[1:8] == f0[0:7], "frame1 is not frame0 shifted down 1px"

# symmetry of the outline + silhouette (role K and transparency) for frames.
# (colour symmetry is intentionally absent: the bevel is lit from upper-left)
for name, (rows, m, pal) in A.items():
    if not m:
        continue
    shape = [[(ch == 'K', ch == '.') for ch in r] for r in rows]
    assert shape == [list(reversed(r)) for r in shape], f"{name}: outline not L/R symmetric"
    assert shape == list(reversed(shape)), f"{name}: outline not T/B symmetric"

# write deliverables
for name, (w, h, px, m) in built.items():
    safe_write(UI + name + ".png", w, h, px)
    if m:
        W3, H3, px3 = scale_nn(w, h, px, 3)
        safe_write(UI + name + "_3x.png", W3, H3, px3)
json.dump(sorted(created), open(MANIFEST, "w"), indent=1)

# read back and verify the files on disk
for name, (w, h, px, m) in built.items():
    rw, rh, rpx = read_png(UI + name + ".png")
    assert (rw, rh, rpx) == (w, h, px), name
    if m:
        rw, rh, rpx = read_png(UI + name + "_3x.png")
        assert (rw, rh) == (w * 3, h * 3), name
        assert all(rpx[y][x] == px[y // 3][x // 3] for y in range(rh) for x in range(rw)), name
print("wrote + verified:", ", ".join(sorted(os.path.basename(p) for p in created)))

# ---- 8x zoom sheet of the 1x assets
S = 8
order = ['ui_dialogue_frame', 'ui_portrait_frame', 'ui_card_frame', 'ui_button', 'ui_button_hover',
         'ui_button_pressed', 'ui_dialogue_next']
x = 16
tiles = []
for name in order:
    w, h, px, m = built[name]
    _, _, z = upscale(w, h, px, S, bg='checker')
    tiles.append((x, z))
    x += w * S + 24
sheet = solid(x, 32 * S + 32, (60, 60, 70, 255))
for tx, z in tiles:
    blit(sheet, z, tx, 16)
write_png(OUT + "zoom_8x.png", x, 32 * S + 32, sheet)


# ---- luminance / contrast for white text
def lum(hx):
    c = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


for label, hx in [('dialogue/card panel', '222034'), ('portrait well', '3f3f74'),
                  ('button face', 'ac3232'), ('button hover face', 'd95763')]:
    print(f"white on #{hx} ({label}): contrast {1.05 / (lum(hx) + 0.05):.1f}:1")
print("build ok")
