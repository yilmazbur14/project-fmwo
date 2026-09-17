"""The locked INVITE card at the top of the tower. Returns a transparent Canvas."""
from lib import *

MASCOT = [
    "..BBB.....BBB..",
    ".BBBBBBBBBBBBB.",
    "BBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBB",
    "BBBB..BBB..BBBB",
    "BBBB..BBB..BBBB",
    "BBBB..BBB..BBBB",
    "BBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBB",
    ".BBBBBBBBBBBBB.",
    "..BBBB...BBBB..",
]

# bold 5x7 letters for the card title
F57 = {
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    'N': ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    'V': ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
}

PADLOCK = [
    "....KKKKKKK....",
    "...KwwwwwggK...",
    "..KwgKKKKKggK..",
    "..KwK.....KgK..",
    "..KwK.....KgK..",
    "..KwK.....KgK..",
    "KKKKKKKKKKKKKKK",
    "KyyyyyyyyyyyyoK",
    "KytttttttttttoK",
    "KyttttKKKttttoK",
    "KytttKKKKKtttoK",
    "KyttttKKKttttoK",
    "KytttttKttttt oK".replace(' ', ''),
    "KytttttKtttttoK",
    "KtoooooooooooOK",
    ".KKKKKKKKKKKKK.",
]
PAD_MAP = {'K': K, 'w': WH2, 'g': G4, 'y': YL, 't': TN, 'o': GO, 'O': OL}


def card():
    CW, CH = 76, 48
    c = Canvas(CW, CH)
    x0, y0, x1, y1 = 3, 4, 72, 44          # card rectangle (inclusive)
    # body
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            corner = (x in (x0, x1) and y in (y0, y1))
            if corner:
                continue
            e = min(x - x0, x1 - x, y - y0, y1 - y)
            if e == 0:
                col = K
            elif e == 1:
                col = YL if (x - x0 == 1 or y - y0 == 1) and not (x1 - x == 1 or y1 - y == 1) else GO
            elif e == 2:
                col = TN
            elif e == 3:
                col = K
            else:
                col = N0
                if y - y0 == 4:
                    col = IN
            c.set(x, y, col)
    # re-round corners of the brass rim
    for (cx, cy, dx, dy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        c.set(cx + dx, cy + dy, K)
    # round server icon: white disc, the chat mascot in blurple (same icon as the logo's O)
    icx, icy, R = x0 + 15, y0 + 13, 10.6
    for yy in range(icy - 12, icy + 13):
        for xx in range(icx - 12, icx + 13):
            d = ((xx - icx) ** 2 + (yy - icy) ** 2) ** 0.5
            if d <= R:
                a = (xx - icx) + (yy - icy)
                col = K if d > R - 1.0 else WH
                if col == WH and d > R - 2.6:
                    col = WH if a < -4 else G5 if a > 5 else WH2
                c.set(xx, yy, col)
    mx, my = icx - 7, icy - 5
    for j, row in enumerate(MASCOT):
        for i, ch in enumerate(row):
            if ch == 'B':
                col = RB
                if j == 0 or (j <= 2 and i <= 1):
                    col = SB
                if j >= 9 or (j >= 7 and i >= 13):
                    col = IN
                c.set(mx + i, my + j, col)
    # title
    tx, ty = x0 + 30, y0 + 7
    for ch in 'INVITE':
        g = F57[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == '#':
                    c.set(tx + i, ty + j + 1, K)
                    c.set(tx + i, ty + j, WH if j < 3 else WH2)
        tx += 6
    # online line: green status dot + grey text bars
    sx, sy = x0 + 30, y0 + 18
    c.grid(sx, sy, [".GG.", "GLGG", "GGGG", ".GG."], {'G': GR, 'L': LG})
    c.hline(sx + 6, sx + 21, sy + 1, G4)
    c.hline(sx + 6, sx + 15, sy + 3, G3)
    c.hline(sx + 24, sx + 32, sy + 1, G3)
    # JOIN button (locked)
    bx0, by0, bx1, by1 = x0 + 6, y0 + 27, x1 - 6, y0 + 36
    for y in range(by0, by1 + 1):
        for x in range(bx0, bx1 + 1):
            if (x in (bx0, bx1)) and (y in (by0, by1)):
                continue
            e = min(x - bx0, bx1 - x, y - by0, by1 - y)
            col = K if e == 0 else (LG if y == by0 + 1 else OG if y == by1 - 1 else GR)
            c.set(x, y, col)
    # chain across the button, padlock in the middle
    cy = by0 + 5
    for x in range(0, CW):
        k = x % 6
        if k in (0, 1, 2, 3):
            if k in (0, 3):
                c.set(x, cy - 1, K); c.set(x, cy + 1, K); c.set(x, cy, G5)
            else:
                c.set(x, cy - 2, K); c.set(x, cy - 1, WH2); c.set(x, cy, K); c.set(x, cy + 1, G4); c.set(x, cy + 2, K)
        else:
            c.set(x, cy - 1, K); c.set(x, cy, G5 if k == 4 else G4); c.set(x, cy + 1, K)
    px, py = CW // 2 - 7, cy - 6
    c.grid(px, py, PADLOCK, PAD_MAP, skip='.')
    # notification badge
    bdx, bdy = x1 - 5, y0 - 4
    badge = ["..KKKKK..", ".KppppdK.", "KppWWpddK", "KppdWpddK", "KpppWpddK", "KpppWpddK", "KdpWWWddK",
             ".KdddddK.", "..KKKKK.."]
    c.grid(bdx, bdy, badge, {'K': K, 'p': PK, 'd': RD, 'W': WH}, skip='.')
    return c


if __name__ == '__main__':
    cc = card()
    p = cc.save('out/invite.png')
    crop_zoom(p, 'out/invite_10x.png', 0, 0, cc.w, cc.h, 10)
    print('ok')
