"""Liam's Avatar-State AURA: two layers on a 128x128 cell, frame for frame with liam_puppet_avatar.
  back  : the rune-blue glow hugging his silhouette, the far half of the orbit, the motes behind him
  front : the near half of the orbit and the motes in front of him
The cell's centre texel (64, 64) sits on his float pivot, body texel (48, 56): the body frame's top-left
is aura texel (16, 8). Glow and wind carry no keyline (house FX rule); the four element motes do (they
are objects - a flame, a drop, a stone, a gust - and must read against the wheel's colours)."""
import math
from ge_common import *
import elements_pal as E

AW = AH = 128
OX, OY = 16, 8                     # body frame (0,0) in aura texels
PIVOT_BODY = (48, 56)
PIVOT = (64, 64)

MOTES = {
    'fire': (E.FIRE, [
        "...#.....",
        "..#y#....",
        "..#oy#...",
        ".#oyy#.#.",
        ".#ryco##y#",
        "#rocWco#.",
        "#rycWyo#.",
        "#royyor#.",
        ".#rooe#..",
        "..####...",
    ]),
    'water': (E.WATER, [
        "....#....",
        "...#L#...",
        "...#BL#..",
        "..#bBL#..",
        ".#bBBWL#.",
        "#ebBBLWl#",
        "#ebBBBLl#",
        "#debBBBL#",
        ".#debbB#.",
        "..#####..",
    ]),
    'earth': (E.EARTH, [
        "....##...",
        "...#gG#..",
        ".###gG###",
        "#ijjGjjJ#",
        "#ijjjjJn#",
        "#jijjJJn#",
        "#jjjJJnd#",
        ".#JJJnnd#",
        "..#nndd#.",
        "...####..",
    ]),
    'air': (E.AIR, [
        "#########",
        "#pWWWWWs#",
        ".#sppts#.",
        ".#WWWWs#.",
        "..#ppt#..",
        "..#WWs#..",
        "...#t#...",
        "...#s#...",
        "....#....",
        ".........",
    ]),
}
ORDER = ('water', 'earth', 'fire', 'air')        # round the orbit, the wheel's own order


def mote(name):
    pal, rows = MOTES[name]
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                a[y, x] = E.K
            elif ch != '.':
                a[y, x] = pal[ch]
    return a


def blit(dst, src, cx, cy):
    h, w = src.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    for y in range(h):
        for x in range(w):
            if src[y, x, 3] and 0 <= y0 + y < dst.shape[0] and 0 <= x0 + x < dst.shape[1]:
                dst[y0 + y, x0 + x] = src[y, x]


def dilate(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def build(body_frames):
    """body_frames: the two treated 96x96 RGBA frames. Returns (back frames, front frames)."""
    backs, fronts = [], []
    for f, body in enumerate(body_frames):
        sil = np.zeros((AH, AW), bool)
        sil[OY:OY + 96, OX:OX + 96] = body[:, :, 3] > 0
        back = np.zeros((AH, AW, 4), np.uint8)
        front = np.zeros((AH, AW, 4), np.uint8)
        # 1. the glow round his silhouette: G1 against him, G2 outside it, a dithered G2 fringe (more on the surge)
        d1 = dilate(sil, 1) & ~sil
        d2 = dilate(sil, 2) & ~dilate(sil, 1)
        d3 = dilate(sil, 3) & ~dilate(sil, 2)
        yy, xx = np.mgrid[0:AH, 0:AW]
        back[d1] = G1
        back[d2] = G2
        fringe = d3 & (((xx + yy) % 2 == 0) if f == 1 else ((xx + yy) % 4 == 0))
        back[fringe] = G2
        # 3. the orbit: a ring of wind round his waist, far half behind him, near half in front, broken in dashes
        rx, ry = (50, 13) if f == 0 else (54, 15)
        cy = PIVOT[1] + (6 if f == 0 else 2)
        tilt = -0.10
        phase = 0.0 if f == 0 else 0.6
        for band in range(2):                       # a 2-texel band: outer and inner rows
            for i in range(900):
                t = 2 * math.pi * i / 900
                gap = math.sin(t * 3 + phase * 2) < -0.82          # three short gaps: a ribbon of wind, not a hoop
                if gap:
                    continue
                ex, ey = (rx - band) * math.cos(t), (ry - band * 0.5) * math.sin(t)
                x = int(math.floor(PIVOT[0] + ex * math.cos(tilt) - ey * math.sin(tilt) + 0.5))
                y = int(math.floor(cy + ex * math.sin(tilt) + ey * math.cos(tilt) + 0.5))
                if not (0 <= x < AW and 0 <= y < AH):
                    continue
                near = math.sin(t) > 0
                glint = math.sin(t * 5 + phase * 4) > 0.8
                if near:
                    front[y, x] = E.AIR['W'] if (glint or band == 1) else E.AIR['s']
                elif not sil[y, x]:
                    back[y, x] = E.AIR['p'] if glint else (E.AIR['s'] if band == 1 else E.AIR['v'])
        # 4. the four element motes round the orbit (the near ones in front of him)
        th0 = math.radians(25 if f == 0 else 55)
        for i, name in enumerate(ORDER):
            t = th0 + i * math.pi / 2
            ex, ey = (rx + 2) * math.cos(t), (ry + 2) * math.sin(t)
            x = PIVOT[0] + ex * math.cos(tilt) - ey * math.sin(tilt)
            y = cy + ex * math.sin(tilt) + ey * math.cos(tilt) - 2
            blit(front if math.sin(t) > 0 else back, mote(name), x, y)
        backs.append(back)
        fronts.append(front)
    return backs, fronts


def composite(body, back, front):
    """The three layers as the game would stack them: back, body, front (aura cell)."""
    out = Image.new('RGBA', (AW, AH), (0, 0, 0, 0))
    out.alpha_composite(Image.fromarray(back, 'RGBA'))
    b = Image.new('RGBA', (AW, AH), (0, 0, 0, 0))
    b.paste(Image.fromarray(body, 'RGBA'), (OX, OY))
    out.alpha_composite(b)
    out.alpha_composite(Image.fromarray(front, 'RGBA'))
    return out


if __name__ == '__main__':
    import liam_puppet as LP
    frames, infos, av = LP.build()
    backs, fronts = build(frames)
    comps = [composite(frames[f], backs[f], fronts[f]) for f in range(2)]
    sheet = Image.new('RGBA', (AW * 2, AH), (0, 0, 0, 0))
    for f, c in enumerate(comps):
        sheet.alpha_composite(c, (f * AW, 0))
    up(sheet, 5, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'liam_aura_comp_5x.png'))
    up(sheet, 2, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'liam_aura_comp_2x.png'))
    print('ok')
