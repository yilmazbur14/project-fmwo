from pngio import read_png, write_png, scale
FLOOR = (136, 180, 99, 255); GAP = (96, 128, 70, 255)
A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
for name, fw in (('eric_thrown_sword', 96), ('eric_sword_planted', 64), ('eric_leap_shadow', 48),
                 ('eric_quake_impact', 160), ('eric_quake_segment', 32)):
    w, h, px = read_png(A + name + '.png')
    n = w // fw
    W = w + 2 * (n - 1)
    out = [[FLOOR] * W for _ in range(h)]
    for i in range(n):
        ox = i * (fw + 2)
        for y in range(h):
            for x in range(fw):
                p = px[y][i * fw + x]
                if p[3]: out[y][ox + x] = p
            if i < n - 1:
                out[y][ox + fw] = GAP; out[y][ox + fw + 1] = GAP
    z = scale(out, 3)
    write_png('strip3x_' + name + '.png', len(z[0]), len(z), z)
    print(name, n, 'frames')
