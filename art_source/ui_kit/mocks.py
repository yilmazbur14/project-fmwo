"""Render the kit + full-screen mock-ups (intro dialogue, controls screen).
usage: python mocks.py OUTDIR [variant options as key=value]"""
import sys, os, subprocess
from kitlib import *
import kit_assets

P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
OUT = sys.argv[1].rstrip('/') + '/'
opts = dict(a.split('=') for a in sys.argv[2:])
os.makedirs(OUT, exist_ok=True)

A = kit_assets.build(plates_on_buttons=opts.get('bplates', '1') == '1',
                     portrait_style=opts.get('portrait', 'deep'))
pix = {}
for name, (rows, m, pal) in A.items():
    w, h, px = grid_to_pix(rows, pal)
    pix[name] = (w, h, px, m)
    if m:
        probs = check_nine_slice(w, h, px, m)
        print(f"{name:20s} {w}x{h} m={m}:", "OK" if not probs else probs[:4])
    bad = check_db32(w, h, px)
    assert not bad, (name, bad)
    write_png(OUT + name + ".png", w, h, px)
    with open(OUT + name + ".txt", "w") as f:
        f.write("\n".join(rows))

# ---- zoom sheet
S = 8
order = ['ui_dialogue_frame', 'ui_card_frame', 'ui_portrait_frame', 'ui_button', 'ui_button_hover',
         'ui_button_pressed', 'ui_dialogue_next']
x = 16
tiles = []
for name in order:
    w, h, px, m = pix[name]
    _, _, z = upscale(w, h, px, S, bg=(132, 126, 135, 255))
    tiles.append((x, z))
    x += w * S + 16
sheet = solid(x, 32 * S + 32, (132, 126, 135, 255))
for tx, z in tiles:
    blit(sheet, z, tx, 16)
write_png(OUT + "sheet_8x.png", x, 32 * S + 32, sheet)


def x3(name):
    w, h, px, m = pix[name]
    return scale_nn(w, h, px, 3), (m or 0) * 3


def ns(name, W, H):
    (w3, h3, p3), m3 = x3(name)
    return nine_slice(w3, h3, p3, m3, W, H)


texts = []   # (file, spec)

# ---- intro mock: full 1920x1080
bw, bh, bg = read_png(P + "Assets/Characters/Danny/DannyIntro.png")
scr = [list(r) for r in bg]
BX, BY, BW, BH = 30, 1080 - 234 - 15, 1860, 234
blit(scr, ns('ui_dialogue_frame', BW, BH), BX, BY)
# portrait frame fills the box's content height (border 21px) -> 192x192, portrait at 2x inside
PF = 192
PFX, PFY = BX + 21, BY + 21
blit(scr, ns('ui_portrait_frame', PF, PF), PFX, PFY)
pw, ph, por = read_png(P + "Assets/Characters/Danny/portrait.png")
_, _, por2 = scale_nn(pw, ph, por, 2)
blit(scr, por2, PFX + (PF - 128) // 2, PFY + (PF - 128) // 2)
# continue arrow (frame 0), 3x, bottom-right of the box
aw, ah, apx, _ = pix['ui_dialogue_next']
_, _, a3 = scale_nn(aw, ah, apx, 3)
blit(scr, crop(a3, 0, 0, 24, 24), BX + BW - 21 - 24 - 12, BY + BH - 21 - 24 - 6)
write_png(OUT + "mock_intro.png", 1920, 1080, scr)
TX = PFX + PF + 30
texts.append(("mock_intro", f"{TX}|{BY + 34}|40|ffffff|Danny;;{TX}|{BY + 92}|40|ffffff|Welcome to the arena, kid. Before you step in that ring,;;{TX}|{BY + 142}|40|ffffff|you better learn the controls."))

# ---- controls mock: 1920x1080 over a stand-in background (intro art)
scr = [list(r) for r in bg]
CW, CH = 480, 760
keys = ["Assets/UI/ArrowKeys.png", "Assets/UI/qKey.png", "Assets/UI/wKey.png"]
labels = [("Classic arrow", "key movement"), ("Attack", ""), ("Dash", "")]
cx0 = 170
spec = []
for i in range(3):
    cx = cx0 + i * (CW + 40)
    cy = 60
    blit(scr, ns('ui_card_frame', CW, CH), cx, cy)
    kw, kh, kp = read_png(P + keys[i])
    _, _, k3 = scale_nn(kw, kh, kp, 4)
    blit(scr, k3, cx + (CW - 256) // 2, cy + 400)
    l1, l2 = labels[i]
    spec.append(f"{cx + 60}|{cy + 90}|60|ffffff|{l1}")
    if l2:
        spec.append(f"{cx + 60}|{cy + 170}|60|ffffff|{l2}")
# buttons: normal, hover, pressed side by side along the bottom
for j, st in enumerate(['ui_button', 'ui_button_hover', 'ui_button_pressed']):
    bx, by = 40 + j * 450, 1080 - 152
    blit(scr, ns(st, 410, 110), bx, by)
    dy = 3 if st == 'ui_button_pressed' else 0
    spec.append(f"{bx + 42}|{by + 22 + dy}|64|ffffff|I'm ready!")
write_png(OUT + "mock_controls.png", 1920, 1080, scr)
texts.append(("mock_controls", ";;".join(spec)))

wd = subprocess.check_output(["cygpath", "-w", os.path.abspath(OUT)]).decode().strip() if False else os.path.abspath(OUT)
for fname, spec in texts:
    src = os.path.join(wd, fname + ".png")
    dst = os.path.join(wd, fname + "_t.png")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "text.ps1",
                        "-In", src, "-Out", dst, "-Spec", spec], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[:300])
print("done")
