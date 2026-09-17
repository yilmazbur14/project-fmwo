import sys
from lib import *
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters"
def load(path, frame=0):
    w, h, px = read_png(path)
    return crop(w, h, px, frame * 64, 0, 64, 64)[2]
def main(new_path, out_path, s=3):
    imgs = [load('old/liam_old.png'), load(new_path), load(P + '/Mason/mason.png')]
    gap = 8
    Wt = 64 * 3 + gap * 4
    Ht = 64 + gap * 2
    bg = (58, 64, 84, 255)
    canvas = [[bg] * Wt for _ in range(Ht)]
    for i, im in enumerate(imgs):
        ox = gap + i * (64 + gap)
        for y in range(64):
            for x in range(64):
                p = im[y][x]
                if p[3] == 255:
                    canvas[gap + y][ox + x] = p
    w2, h2, big = scale(Wt, Ht, canvas, s)
    write_png(out_path, w2, h2, big)
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3)
