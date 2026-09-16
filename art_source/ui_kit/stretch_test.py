"""9-slice stretch test on the shipped _3x files (read from Assets/UI)."""
import os, subprocess
from kitlib import *

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
UI = PROJ + "Assets/UI/"
OUT = "final/"


def load3(name):
    return read_png(UI + name + "_3x.png")


def godot_nine_patch(w, h, px, m, W, H):
    """Mirror of Godot 4's canvas shader map_ninepatch_axis (stretch mode),
    sampled at fragment centres with nearest filtering."""
    def axis(pixel, draw, tex, mb, me):
        if pixel < mb:
            return pixel
        if pixel >= draw - me:
            return tex - (draw - pixel)
        ratio = (pixel - mb) / (draw - mb - me)
        return mb + ratio * (tex - mb - me)
    xs = [min(w - 1, int(axis(X + 0.5, W, w, m, m))) for X in range(W)]
    ys = [min(h - 1, int(axis(Y + 0.5, H, h, m, m))) for Y in range(H)]
    return [[px[ys[Y]][xs[X]] for X in range(W)] for Y in range(H)]


def verify(name, m, W, H):
    w, h, px = load3(name)
    a = nine_slice(w, h, px, m, W, H)
    b = godot_nine_patch(w, h, px, m, W, H)
    assert a == b, f"{name}: my 9-slice and the Godot-shader model disagree at {W}x{H}"
    # corners exact
    for (cx, cy, dx, dy) in [(0, 0, 0, 0), (w - m, 0, W - m, 0), (0, h - m, 0, H - m), (w - m, h - m, W - m, H - m)]:
        for y in range(m):
            for x in range(m):
                assert a[dy + y][dx + x] == px[cy + y][cx + x], f"{name}: corner distorted"
    # stretched edges uniform along their length, centre flat
    for y in list(range(m)) + list(range(H - m, H)):
        assert len(set(a[y][m:W - m])) == 1, f"{name}: top/bottom edge row {y} not uniform"
    for x in list(range(m)) + list(range(W - m, W)):
        assert len(set(a[y][x] for y in range(m, H - m))) == 1, f"{name}: side edge col {x} not uniform"
    assert len({a[y][x] for y in range(m, H - m) for x in range(m, W - m)}) == 1, f"{name}: centre not flat"
    return a


sizes = {
    'ui_dialogue_frame': [(1860, 234), (1860, 180), (640, 234), (96, 96), (97, 131)],
    'ui_card_frame': [(480, 760), (300, 200), (72, 72), (73, 500)],
    'ui_portrait_frame': [(240, 240), (176, 176), (72, 72)],
    'ui_button': [(410, 110), (200, 72), (72, 72)],
    'ui_button_hover': [(410, 110), (72, 72)],
    'ui_button_pressed': [(410, 110), (72, 72)],
}
margins = {'ui_dialogue_frame': 30}
for name, lst in sizes.items():
    m = margins.get(name, 24)
    for (W, H) in lst:
        verify(name, m, W, H)
    print(f"{name}: stretched cleanly at", ", ".join(f"{W}x{H}" for W, H in lst))

GREY = (132, 126, 135, 255)
checker = lambda W, H: [[(200, 200, 200, 255) if ((x // 24 + y // 24) % 2 == 0) else (170, 170, 170, 255)
                         for x in range(W)] for y in range(H)]

# ---- sheet 1: the dialogue box at 1860x234 on a checker, with portrait frame, portrait, arrow
W, H = 1920, 300
s1 = checker(W, H)
box = verify('ui_dialogue_frame', 30, 1860, 234)
blit(s1, box, 30, 33)
pf = verify('ui_portrait_frame', 24, 176, 176)
blit(s1, pf, 30 + 30, 33 + 29)
pw, ph, por = read_png(PROJ + "Assets/Characters/Danny/portrait.png")
_, _, por2 = scale_nn(pw, ph, por, 2)
blit(s1, por2, 30 + 30 + 24, 33 + 29 + 24)
aw, ah, apx = read_png(UI + "ui_dialogue_next.png")
_, _, a3 = scale_nn(aw, ah, apx, 3)
blit(s1, crop(a3, 0, 0, 24, 24), 30 + 1860 - 30 - 30, 33 + 234 - 30 - 30)
write_png(OUT + "test_dialogue_1860x234.png", W, H, s1)

# ---- sheet 2: three cards 480x760 + three button states 410x110
W, H = 1920, 1080
s2 = checker(W, H)
card = verify('ui_card_frame', 24, 480, 760)
for i in range(3):
    blit(s2, card, 60 + i * 520, 40)
keys = ["Assets/UI/ArrowKeys.png", "Assets/UI/qKey.png", "Assets/UI/wKey.png"]
for i, k in enumerate(keys):
    kw, kh, kp = read_png(PROJ + k)
    _, _, k3 = scale_nn(kw, kh, kp, 3)
    blit(s2, k3, 60 + i * 520 + (480 - 192) // 2, 40 + 420)
for j, st in enumerate(['ui_button', 'ui_button_hover', 'ui_button_pressed']):
    blit(s2, verify(st, 24, 410, 110), 60 + j * 450, 870)
write_png(OUT + "test_cards_buttons.png", W, H, s2)

# text overlays (the game's pixel font, white)
specs = {
    "test_dialogue_1860x234": "270|68|40|ffffff|Danny;;270|128|40|ffffff|Welcome to the arena, kid. Before you step in that ring,;;270|178|40|ffffff|you better learn the controls. White text, pixel font, on the navy panel.",
    "test_cards_buttons": ";;".join([
        "96|110|56|ffffff|Classic arrow", "96|180|56|ffffff|key movement",
        "680|130|80|ffffff|Attack", "1220|130|80|ffffff|Dash",
        "108|897|56|ffffff|I'm ready!", "558|897|56|ffffff|I'm ready!", "1008|900|56|ffffff|I'm ready!",
    ]),
}
wd = os.path.abspath(OUT)
for fname, spec in specs.items():
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "text.ps1",
                        "-In", os.path.join(wd, fname + ".png"), "-Out", os.path.join(wd, fname + "_t.png"),
                        "-Spec", spec], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[:200])
print("stretch tests ok")
