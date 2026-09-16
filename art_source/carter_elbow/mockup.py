"""Game-scale (3x) mock-up of the full elbow-drop attack on the arena floor colour.
Sprites are 'centered' like Godot Sprite2D: node position = texture centre."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png

S = 3
FLOOR = (136, 180, 99)
car_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'carter_elbowdrop_wip.png')
tgt_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'elbow_target_wip.png')
imp_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'elbow_impact_wip.png')
out_path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, 'mockup_3x.png')
ELBOW = (26.5, 61.0)   # elbow ground-contact point inside carter frame 2


def frames(path, fw):
    w, h, p = read_png(path)
    return [[row[i * fw:(i + 1) * fw] for row in p] for i in range(w // fw)], fw, h


CAR, CW, CH = frames(car_path, 64)
TGT, TW, TH = frames(tgt_path, 48)
IMP, IW, IH = frames(imp_path, 64)

PW, PH = 250, 330
panels = [
    # (label, [(sprite_frames, idx, dx, dy)] offsets are screen px relative to landing point P)
    ('warn f0', [(TGT, 0, 0, 0), (CAR, 0, 0, -250)]),
    ('warn f1', [(TGT, 1, 0, 0), (CAR, 1, 0, -170)]),
    ('warn f0', [(TGT, 0, 0, 0), (CAR, 0, 0, -115)]),
    ('hit+fx0', [(CAR, 2, 0, 0), (IMP, 0, 0, 0)]),
    ('hit+fx1', [(CAR, 2, 0, 0), (IMP, 1, 0, 0)]),
    ('push+fx2', [(CAR, 3, 0, 0), (IMP, 2, 0, 0)]),
    ('rise+fx3', [(CAR, 4, 0, -40), (IMP, 3, 0, 0)]),
]
W = PW * len(panels)
img = [[FLOOR + (255,)] * W for _ in range(PH)]
P = (PW // 2, 235)
car_off = ((32 - ELBOW[0]) * S, (32 - ELBOW[1]) * S)   # carter node offset so elbow tip lands on P


def blit(ox, fr, cx, cy):
    fh, fw = len(fr), len(fr[0])
    left = int(round(cx - fw * S / 2))
    top = int(round(cy - fh * S / 2))
    for y in range(fh * S):
        Y = top + y
        if not (0 <= Y < PH):
            continue
        for x in range(fw * S):
            X = left + x
            if not (0 <= X < PW):
                continue
            r, g, b, a = fr[y // S][x // S]
            if a == 0:
                continue
            br, bg, bb, _ = img[Y][ox + X]
            k = a / 255.0
            img[Y][ox + X] = (int(r * k + br * (1 - k)), int(g * k + bg * (1 - k)), int(b * k + bb * (1 - k)), 255)


for i, (label, layers) in enumerate(panels):
    ox = i * PW
    for fr_list, idx, dx, dy in layers:
        fr = fr_list[idx]
        if fr_list is CAR:
            blit(ox, fr, P[0] + car_off[0] + dx, P[1] + car_off[1] + dy)
        else:
            blit(ox, fr, P[0] + dx, P[1] + dy)
    for y in range(PH):
        img[y][ox] = (60, 80, 40, 255)
write_png(out_path, W, PH, img)
print('wrote', out_path, W, PH)
