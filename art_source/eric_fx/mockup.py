"""3x in-context mockup on the arena floor colour. Sprites are sampled nearest-neighbour at output
resolution (like Godot with nearest filtering), so rotated shockwave segments look as they would in game."""
import math, sys
from pngio import read_png, write_png

FLOOR = (136, 180, 99, 255)
SC = 3
FX = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
SHEET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png'

def load(path):
    w, h, px = read_png(path)
    return px

def frame_of(px, fw, i):
    return [row[i * fw:(i + 1) * fw] for row in px]

def draw(out, tex, cx, cy, ax, ay, rot=0.0, alpha=1.0):
    """place texture so its anchor (ax, ay) (continuous texel coords) lands at native (cx, cy)"""
    th = len(tex); tw = len(tex[0])
    OW = len(out[0]); OH = len(out)
    c, s = math.cos(rot), math.sin(rot)
    R = math.hypot(max(ax, tw - ax), max(ay, th - ay)) + 1
    x0 = max(0, int((cx - R) * SC)); x1 = min(OW, int((cx + R) * SC) + 1)
    y0 = max(0, int((cy - R) * SC)); y1 = min(OH, int((cy + R) * SC) + 1)
    for oy in range(y0, y1):
        ny = (oy + 0.5) / SC - cy
        for ox in range(x0, x1):
            nx = (ox + 0.5) / SC - cx
            u = c * nx + s * ny + ax
            v = -s * nx + c * ny + ay
            iu = math.floor(u); iv = math.floor(v)
            if 0 <= iu < tw and 0 <= iv < th:
                p = tex[iv][iu]
                if p[3] > 0:
                    if alpha < 1.0:
                        q = out[oy][ox]
                        p = tuple(round(q[i] * (1 - alpha) + p[i] * alpha) for i in range(3)) + (255,)
                    out[oy][ox] = p

def main(outpath, sword_f=1, impact_f=2, seg_f=1, planted_f=1, ring_r=108, nseg=24):
    NW, NH = 540, 300
    out = [[FLOOR] * (NW * SC) for _ in range(NH * SC)]
    eric = load(SHEET)
    thrown = load(FX + 'eric_thrown_sword.png')
    planted = load(FX + 'eric_sword_planted.png')
    impact = load(FX + 'eric_quake_impact.png')
    seg = load(FX + 'eric_quake_segment.png')
    shadow = load(FX + 'eric_leap_shadow.png')
    rcx, rcy = 395, 158
    # shockwave ring: segment 'up' faces outward
    for i in range(nseg):
        a = 2 * math.pi * i / nseg
        x = rcx + ring_r * math.cos(a); y = rcy + ring_r * math.sin(a)
        draw(out, frame_of(seg, 32, seg_f), x, y, 16, 16, a + math.pi / 2)
    draw(out, frame_of(impact, 160, impact_f), rcx, rcy, 80.5, 66.5)
    draw(out, frame_of(planted, 64, planted_f), rcx, rcy, 32.5, 80.5)
    # Eric idle (frame 21) and the thrown sword mid-spin, with a medium leap shadow between them
    draw(out, frame_of(eric, 128, 21), 70, 170, 64, 64)
    draw(out, frame_of(shadow, 48, 1), 190, 205, 24, 8, alpha=0.35)   # code sets the shadow's transparency
    draw(out, frame_of(thrown, 96, sword_f), 190, 110, 48, 48)
    OW = NW * SC; OH = NH * SC
    write_png(outpath, OW, OH, out)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'mockup_3x.png')
