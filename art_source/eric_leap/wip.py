"""WIP composer: builds a frame grid from reference parts, then writes it as editable text."""
import sys
from lib import *
R = [to_chars(f) for f in ref_frames()]
F21, F11, F27 = R[21], R[11], R[27]

def base_wait():
    g = blank()
    # lower body from idle 21: torso sides, belly, loincloth, legs (exclude right arm x>=70 and left raised arm)
    copy_region(g, F21, 47, 95, 70, 113)
    copy_region(g, F21, 44, 113, 80, 122)
    # head from frame 11 moved up 2 (clean, no sword)
    copy_region(g, F11, 54, 79, 67, 88, 0, -2)
    # beard/neck/chest rows 86-94 from 21, x>=56
    copy_region(g, F21, 56, 86, 70, 95)
    # right arm from 21 (x66..76 rows 89..112) - only arm pixels
    copy_region(g, F21, 66, 89, 78, 113, keep=lambda x, y, c: x >= 70 or (y <= 95 and x >= 67) or (y <= 93 and x >= 66))
    # left arm: mirror right arm about x=60, shifted -1
    for y in range(89, 113):
        for x in range(66, 78):
            c = F21[y][x]
            if c in '.~':
                continue
            if not (x >= 70 or (y <= 95 and x >= 67) or (y <= 93 and x >= 66)):
                continue
            X = 120 - x - 1
            if g[y][X] == '.':
                g[y][X] = c
    # left pauldron/chest mirror of rows 86-94 x61..69
    for y in range(86, 95):
        for x in range(61, 70):
            c = F21[y][x]
            if c in '.~':
                continue
            X = 120 - x
            g[y][X] = c
    return g

if __name__ == '__main__':
    g = base_wait()
    save_txt('base_wait.txt', g, 36, 70, 88, 124)
    print(open('base_wait.txt').read())
