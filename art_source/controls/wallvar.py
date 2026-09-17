import bg
from bg import *

def wall_variant(c, v):
    BH, BW = 14, 28
    for y in range(WALL_Y0, FLOOR_Y):
        row = (y - WALL_Y0) // BH
        off = (BW // 2) if row % 2 else 0
        for x in range(W):
            mh = (y - WALL_Y0) % BH == BH - 1
            mv = (x + off) % BW == BW - 1
            mortar = mh or mv
            lv = light_level(x, y)          # ~1 at fixture, <0 far away
            top_shadow = (y - WALL_Y0) / 40.0  # 0 at ceiling -> 1 at y=46
            if v == 1:
                # uniform plum, mortar fades inside the light, soft ceiling shadow
                col = P0
                if mortar:
                    col = P0 if (lv > 0.45 or (lv > 0.25 and dith(x, y, (lv - 0.25) / 0.2))) else N0
                if top_shadow < 1 and not dith(x, y, top_shadow) and lv < 0.6:
                    col = N0 if not mortar else K
            elif v == 2:
                # plum; lit core gets 1px brown top edge on blocks; mortar fades in light
                col = P0
                top_edge = (y - WALL_Y0) % BH == 0
                if mortar:
                    col = P0 if lv > 0.5 else N0
                elif top_edge and lv > 0.55:
                    col = BR
                if lv < 0.0 and dith(x, y, min(1, -lv * 1.5)):
                    col = N0 if not mortar else K
            elif v == 3:
                # darker overall: navy-dominant falloff, plum only under lights
                if lv > 0.3 or (lv > 0.0 and dith(x, y, lv / 0.3)):
                    col = N0 if mortar else P0
                else:
                    col = K if mortar else N0
            c.set(x, y, col)
    for x in range(W):
        c.set(x, FLOOR_Y - 1, K)

tiles = []
for v in (1, 2, 3):
    c = Canvas(W, H)
    draw_wall(c)
    wall_variant(c, v)
    draw_floor(c); draw_lockers(c); draw_bench(c)
    for fx in FIXTURES: draw_fixture(c, fx)
    tiles.append(c)
# stack crops: x 0..160 and x 480..640, y 0..280 for each variant, at 2x
cw, ch = 320, 280
S = 2
out = []
for Y in range(ch * S * 3 + 8):
    out.append([(255, 255, 255, 255)] * (cw * S))
for k, c in enumerate(tiles):
    rgba = c.to_rgba()
    for y in range(ch):
        for x in range(cw):
            sx = x if x < 160 else x + 320
            p = rgba[y][sx]
            for dy in range(S):
                for dx in range(S):
                    out[k * (ch * S + 4) + y * S + dy][x * S + dx] = p
write_png(os.path.join(OUT, 'wall_variants.png'), cw * S, ch * S * 3 + 8, out)
print('ok')
