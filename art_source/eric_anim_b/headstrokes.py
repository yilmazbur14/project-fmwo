"""relative light/dark strokes over the head ('+' lighter, '-' darker, or palette char)"""
import headmap
HW, HH, X0, Y0 = headmap.HW, headmap.HH, headmap.X0, headmap.Y0
g = [['.'] * HW for _ in range(HH)]


def P(y, c, ch):
    g[y - Y0][c] = ch


def line(pts, ch):
    for (y0, c0), (y1, c1) in zip(pts, pts[1:]):
        n = max(abs(y1 - y0), abs(c1 - c0), 1)
        for i in range(n + 1):
            y = round(y0 + (y1 - y0) * i / n)
            c = round(c0 + (c1 - c0) * i / n)
            P(y, c, ch)


# ---- hair: three swept locks (y, c) with c = x - 30
# lock boundaries (darker)
line([(5, 13), (6, 15), (7, 17), (8, 19), (9, 21), (10, 23), (12, 25), (14, 27)], '-')
line([(9, 7), (10, 9), (11, 11), (12, 13), (13, 14)], '-')
line([(4, 22), (5, 24), (6, 26), (8, 28), (10, 29)], '-')
# lock highlights (lighter), running just above each boundary on the lit side
line([(5, 10), (5, 12)], '+'); line([(6, 12), (6, 13)], '+')
line([(7, 8), (7, 10)], '+'); line([(8, 11), (8, 12)], '+')
line([(10, 6), (10, 7)], '+'); line([(11, 8), (11, 9)], '+'); line([(12, 10), (12, 11)], '+')
line([(7, 20), (7, 21)], '+'); line([(8, 22), (8, 23)], '+'); line([(9, 24), (9, 24)], '+')
line([(4, 20), (4, 21)], '+'); line([(5, 22), (5, 22)], '+')
# sideburn depth
line([(15, 5), (19, 5)], '-'); line([(15, 30), (21, 30)], '-')
# ---- nose
for y in range(21, 26):
    P(y, 19, '-')
P(26, 16, '-'); P(26, 17, '-'); P(26, 18, '-'); P(26, 19, '-')
P(26, 15, 'v'); P(26, 20, 'w')
P(23, 17, '+'); P(24, 17, '+'); P(25, 17, '+')
P(25, 20, '-')
# ---- cheeks under eyes
P(24, 10, '-'); P(24, 25, '-')
# ---- moustache
line([(28, 14), (28, 16)], '+'); line([(29, 12), (29, 13)], '+'); P(30, 10, '+')
line([(30, 22), (31, 25)], '-'); line([(29, 21), (29, 22)], '-')
P(28, 19, '-'); P(29, 17, '-'); P(29, 18, '-')
# ---- beard strands (flow down, converge to tip)
line([(31, 4), (35, 5), (38, 6)], '+')
line([(34, 8), (38, 9), (42, 11)], '+')
line([(35, 13), (40, 14), (45, 15)], '+')
line([(29, 5), (30, 6)], '+')
line([(37, 3), (40, 5), (43, 7)], '-')
line([(39, 11), (43, 13), (46, 15)], '-')
line([(34, 17), (39, 17), (44, 17), (50, 17)], '-')
line([(35, 22), (40, 21), (45, 20)], '-')
line([(33, 27), (38, 26), (43, 24)], '-')
line([(30, 31), (35, 30), (39, 29)], '-')
line([(36, 19), (40, 19)], '+')
line([(33, 23), (36, 23)], '+')
STROKES = '\n'.join(''.join(r) for r in g)
