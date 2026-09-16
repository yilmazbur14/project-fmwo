"""Prototype pass 1: dialogue frame shape + colour variants, stretched over the
real intro background so the choice is made in context."""
from kitlib import *

P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
OUT = "proto1/"
import os
os.makedirs(OUT, exist_ok=True)

# Roles: K outline, 1 rim highlight (top/left outer), 2 rim lit inner wall
# (bottom/right), 3 rim base, 4 rim shadow inner wall (top/left), 5 rim deep
# shadow (bottom/right outer), P panel, p panel recess shadow (top/left),
# q panel recess light (bottom/right)
DLG = []
DLG.append("..KKKKKKKK" + "KKKKKKKKKKKK" + "KKKKKKKK..")   # y0
DLG.append(".K11111111" + "111111111111" + "11111111K.")   # y1
DLG.append("K133333333" + "333333333333" + "333333335K")   # y2
DLG.append("K133333333" + "333333333333" + "333333335K")   # y3
DLG.append("K133444444" + "444444444444" + "444443335K")   # y4
DLG.append("K13344KKKK" + "KKKKKKKKKKKK" + "KKKK32335K")   # y5
DLG.append("K1334KKppp" + "pppppppppppp" + "pppKK2335K")   # y6
for _ in range(7, 25):
    DLG.append("K1334KpPPP" + "PPPPPPPPPPPP" + "PPPqK2335K")
DLG.append("K1334KKqqq" + "qqqqqqqqqqqq" + "qqqKK2335K")   # y25
DLG.append("K13343KKKK" + "KKKKKKKKKKKK" + "KKKK22335K")   # y26
DLG.append("K133322222" + "222222222222" + "222222335K")   # y27
DLG.append("K133333333" + "333333333333" + "333333335K")   # y28
DLG.append("K133333333" + "333333333333" + "333333335K")   # y29
DLG.append(".K55555555" + "555555555555" + "55555555K.")   # y30
DLG.append("..KKKKKKKK" + "KKKKKKKKKKKK" + "KKKKKKKK..")   # y31
assert len(DLG) == 32

VARIANTS = {
    'steel_navy': dict(K='000000', **{'1': 'cbdbfc', '2': 'cbdbfc', '3': '9badb7', '4': '847e87', '5': '595652'},
                       P='222034', p='000000', q='3f3f74'),
    'gold_navy': dict(K='000000', **{'1': 'ffffff', '2': 'fbf236', '3': 'fbf236', '4': 'df7126', '5': '8f563b'},
                      P='222034', p='000000', q='3f3f74'),
    'bronze_navy': dict(K='000000', **{'1': 'eec39a', '2': 'eec39a', '3': 'd9a066', '4': '8f563b', '5': '663931'},
                        P='222034', p='000000', q='3f3f74'),
    'crimson_navy': dict(K='000000', **{'1': 'd95763', '2': 'd95763', '3': 'ac3232', '4': '663931', '5': '45283c'},
                         P='222034', p='000000', q='3f3f74'),
    'steel_plum': dict(K='000000', **{'1': 'cbdbfc', '2': 'cbdbfc', '3': '9badb7', '4': '847e87', '5': '595652'},
                       P='45283c', p='222034', q='76428a'),
    'gold_plum': dict(K='000000', **{'1': 'ffffff', '2': 'fbf236', '3': 'fbf236', '4': 'df7126', '5': '8f563b'},
                      P='45283c', p='222034', q='76428a'),
}

bw, bh, bg = read_png(P + "Assets/Characters/Danny/DannyIntro.png")
pw, ph, portrait = read_png(P + "Assets/Characters/Danny/portrait.png")
_, _, portrait3 = scale_nn(pw, ph, portrait, 3)

for name, pal in VARIANTS.items():
    w, h, pix = grid_to_pix(DLG, pal)
    probs = check_nine_slice(w, h, pix, 10)
    print(name, "9-slice problems:", probs if probs else "none", "| non-DB32:", check_db32(w, h, pix) or "none")
    write_png(OUT + f"dlg_{name}_1x.png", w, h, pix)
    W3, H3, pix3 = scale_nn(w, h, pix, 3)
    # stretched mock at real size, composited on the intro's bottom strip
    box = nine_slice(W3, H3, pix3, 30, 1860, 234)
    strip = crop([list(r) for r in bg], 0, 1080 - 300, 1920, 300)
    blit(strip, box, 30, 300 - 234 - 15)
    blit(strip, portrait3, 30 + 30 + 6, 300 - 234 - 15 + 21)
    write_png(OUT + f"mock_{name}.png", 1920, 300, strip)
print("done")
