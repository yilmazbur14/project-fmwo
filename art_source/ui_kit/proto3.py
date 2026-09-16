"""Prototype pass 3: the whole kit in brass, viewed zoomed and in screen mocks."""
from kitlib import *
from framegen import *
import os, sys

P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
OUT = "proto3/"
os.makedirs(OUT, exist_ok=True)

TUBE_TOP = list("K1234K") + ['p']
TUBE_BOT = ['q'] + list("K2345K")

BOLT_PLATE9 = [
    "KKKKKKKKK",
    "K1111112K",
    "K1333334K",
    "K13ab334K",
    "K13bcd34K",
    "K133dd34K",
    "K1333334K",
    "K2444445K",
    "KKKKKKKKK",
]
BOLT_PLATE7 = [
    "KKKKKKK",
    "K11112K",
    "K1ab34K",
    "K1bcd4K",
    "K13dd4K",
    "K24445K",
    "KKKKKKK",
]

BRASS = {'K': '000000', '1': 'fbf236', '2': 'eec39a', '3': 'd9a066', '4': '8a6f30', '5': '524b24',
         'a': 'ffffff', 'b': 'fbf236', 'c': '8f563b', 'd': '45283c'}

assets = {}

# ---- dialogue frame 32x32, margin 10
g = stamp(inner_round(chamfer(frame_grid(32, TUBE_TOP, TUBE_BOT)), 32, 5), 32, BOLT_PLATE9)
assets['dialogue'] = (to_rows(g), 10, dict(BRASS, P='222034', p='000000', q='3f3f74'))

# ---- card frame 24x24, margin 8
g = stamp(inner_round(chamfer(frame_grid(24, TUBE_TOP, TUBE_BOT)), 24, 5), 24, BOLT_PLATE7)
assets['card'] = (to_rows(g), 8, dict(BRASS, P='222034', p='000000', q='3f3f74'))

# ---- portrait frame 24x24, margin 8 (inset backdrop)
g = stamp(inner_round(chamfer(frame_grid(24, TUBE_TOP, TUBE_BOT)), 24, 5), 24, BOLT_PLATE7)
assets['portrait'] = (to_rows(g), 8, dict(BRASS, P='3f3f74', p='222034', q='3f3f74'))

# ---- buttons 24x24, margin 8 (hand-written: raised crimson plate + lip)
def button_rows(state):
    n = 24
    if state in ('normal', 'hover'):
        top = list("KH") + ['F']
        bot = list("FSLLK")          # inner->outer: face, face shadow, lip, lip, K
        left = list("KH") + ['F']
        right = list("FSK")
    else:  # pressed: face sunk 1px, bevel inverted
        top = list("KLs") + ['F']    # K, dark gap, shadow line, face
        bot = list("FHLK")           # face, highlight line, lip(1), K
        left = list("Ks") + ['F']
        right = list("FHK")
    g = chamfer(frame_grid(n, top, bot, left, right, fill='F'))
    return to_rows(g)

RED = {'K': '000000'}
assets['button'] = (button_rows('normal'), 8, dict(RED, H='d95763', F='ac3232', S='663931', L='45283c'))
assets['button_hover'] = (button_rows('hover'), 8, dict(RED, H='eec39a', F='d95763', S='ac3232', L='45283c'))
assets['button_pressed'] = (button_rows('pressed'), 8, dict(RED, H='d95763', F='ac3232', s='663931', L='45283c'))

# ---- continue arrow: 2 frames of 8x8
ARROW = [
    "KKKKKKKK",
    "K111112K",
    "K133334K",
    ".K1334K.",
    "..K34K..",
    "...KK...",
]
f0 = ARROW + ["........"] * 2
f1 = ["........"] + ARROW + ["........"]
arrow_rows = [a + b for a, b in zip(f0, f1)]
assets['next'] = (arrow_rows, None, BRASS)

pix = {}
for name, (rows, m, pal) in assets.items():
    w, h, px = grid_to_pix(rows, pal)
    pix[name] = (w, h, px)
    if m:
        probs = check_nine_slice(w, h, px, m)
        print(f"{name:15s} {w}x{h} m={m} 9-slice:", "OK" if not probs else probs[:4])
    else:
        print(f"{name:15s} {w}x{h}")
    write_png(OUT + f"{name}_1x.png", w, h, px)
    with open(OUT + f"{name}.txt", "w") as f:
        f.write("\n".join(rows))

# ---- zoom sheet of all assets at 8x
S = 8
order = ['dialogue', 'card', 'portrait', 'button', 'button_hover', 'button_pressed', 'next']
x = 16
tiles = []
for name in order:
    w, h, px = pix[name]
    _, _, z = upscale(w, h, px, S, bg=(132, 126, 135, 255))
    tiles.append((x, z, w * S, h * S))
    x += w * S + 16
sheet = solid(x, 32 * S + 32, (132, 126, 135, 255))
for (tx, z, zw, zh) in tiles:
    blit(sheet, z, tx, 16)
write_png(OUT + "sheet_8x.png", x, 32 * S + 32, sheet)
print("sheet written")
