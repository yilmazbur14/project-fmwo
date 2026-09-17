"""The newcomer (player) from behind: hand-authored left half, mirrored, plus the headband knot/tails."""
from lib import *
LEFT = [
    "...........K.KKK",  # 0
    "..........KNKnnN",  # 1
    ".........KNnnNNN",  # 2
    ".........KNnNNNN",  # 3
    ".........KNNNNNN",  # 4
    ".........Kpppppp",  # 5
    ".........KrrrrrR",  # 6
    "........KTKNNNNN",  # 7
    "........KbKNNNNN",  # 8
    ".........KNNNNNN",  # 9
    "..........KNNNNN",  # 10
    "...........KdbTT",  # 11
    "........KSSSTTbT",  # 12
    ".....KSSTTTTTTTT",  # 13
    "...KSSTTTTTTTTTb",  # 14
    "..KSTTTbTTTTTTTb",  # 15
    ".KSTTTbbTTTTTTTb",  # 16
    ".KSTTTbTTbTTTTTb",  # 17
    ".KTTTbdTTTbTTTTb",  # 18
    ".KSTTbK.KdTTbTTb",  # 19
    ".KSTTbK.KdTTTbTb",  # 20
    ".KSTTbK.KdTTTTTb",  # 21
    ".KSTbK...KdTTTTb",  # 22
    "..KTbK...KdTTbTb",  # 23
    "..KSbK....KdTbTb",  # 24
    "..KSTbK...KdTbTb",  # 25
    "..KSTbK...KdTbTb",  # 26
    "..KTTbK...KdbbTb",  # 27
    "...KTbK..KKKKKKK",  # 28
    "..KBBuuK.KBBBBBB",  # 29
    "..KBuuiK.KBuuuui",  # 30
    "..KiiiiK.KBuuuui",  # 31
    "..KuuuiK.KBuuuui",  # 32
    "...KKKK..KBuuuui",  # 33
    ".........KBuuuii",  # 34
    ".........KBuuuiK",  # 35
    ".........KBuuiK.",  # 36
    ".........KKKKKK.",  # 37
    "..........KddbK.",  # 38
    "..........KTTbK.",  # 39
    "..........KSTbK.",  # 40
    "..........KSbK..",  # 41
    "..........KTbK..",  # 42
    ".........KSTTbK.",  # 43
    ".........KSTTbK.",  # 44
    ".........KTTbbK.",  # 45
    "..........KTbbK.",  # 46
    "..........KTbK..",  # 47
    "..........KbdK..",  # 48
    "..........KddK..",  # 49
    ".........KgsssK.",  # 50
    "........KggsssK.",  # 51
    "........KKKKKKK.",  # 52
]
W, H = 32, len(LEFT)
CMAP = {'K': K, 'N': N0, 'n': IN, 'p': PK, 'r': RD, 'R': BR, 'S': SK, 'T': TN, 'b': BR2, 'd': BR,
        'B': SB, 'u': RB, 'i': IN, 's': N0, 'g': G2}

def rows():
    for i, r in enumerate(LEFT):
        assert len(r) == 16, (i, len(r))
    g = [list(r + r[::-1]) for r in LEFT]
    # knot at the back of the head
    for x, y, ch in [(15, 5, 'p'), (16, 5, 'p'), (14, 6, 'R'), (15, 6, 'r'), (16, 6, 'r'), (17, 6, 'R'),
                     (15, 7, 'r'), (16, 7, 'r'), (15, 8, 'R'), (16, 8, 'r')]:
        g[y][x] = ch
    # tails fluttering out to the right
    tails = [(17, 7, 'r'), (18, 7, 'r'), (19, 7, 'R'), (17, 8, 'r'), (18, 8, 'r'), (19, 8, 'r'), (20, 8, 'r'),
             (21, 8, 'R'), (22, 8, 'r'), (23, 8, 'r'), (24, 9, 'r'), (25, 9, 'r'), (26, 9, 'R'),
             (19, 9, 'R'), (20, 9, 'r'), (21, 9, 'r'), (22, 10, 'r'), (23, 10, 'r'), (24, 11, 'R'), (25, 11, 'r')]
    ts = set()
    for x, y, ch in tails:
        g[y][x] = ch
        ts.add((x, y))
    for x, y, _ in tails:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and g[ny][nx] == '.':
                g[ny][nx] = 'K'
    return [''.join(r) for r in g]

if __name__ == '__main__':
    rr = rows()
    print('\n'.join(rr))
    c = Canvas(W, H)
    c.grid(0, 0, rr, CMAP, skip='.')
    p = c.save('out/player2.png')
    crop_zoom(p, 'out/player2_10x.png', 0, 0, W, H, 10)
