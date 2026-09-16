import sys
from lib import *
from gif import write_gif
import frames as FR
def main(out='out/anim/preview_4x.gif', s=4):
    fr = FR.build_frames()
    bg = (58, 64, 84, 255)
    imgs, delays = [], []
    for name, dur, cv in fr:
        rgba = to_rgba(cv)
        rgba = [[p if p[3] == 255 else bg for p in row] for row in rgba]
        _, _, big = scale(64, 64, rgba, s)
        imgs.append(big)
        delays.append(dur)
    write_gif(out, imgs, delays)
    print('gif written', out, sum(delays), 'ms')
if __name__ == '__main__':
    main()
