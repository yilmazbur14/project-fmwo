"""Preview GIF: the card magic pulsing on the signature pose (4 frames, ping-pong).

Preview only - the shipped sprite is the static 2-frame strip. This just shows the coder/user
what the gold should do when the glow is animated later.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# josh_v2 goes at the END of sys.path so only its gif writer is picked up, not its 64x64 jlib
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'josh_v2'))
from jlib import W, H, blank, to_rgba, PAL
from gif import write_gif
import head, body
import cards as CD
import frames as FR

BG = (40, 38, 52, 255)


def pose(amp, ray_scale, spin_phase):
    c = blank()
    body.build_body(c, body.POSE1)
    head.build(c, shades_up=True)
    FR.fan(c, (62, 44), [-8, 16, 40, 64], radius=9.5)
    CD.glow(c, [(61, 33, 0.30), (65, 35, 0.28), (70, 39, 0.26)], 8.0)
    CD.card_glow(c, 13, 35, 8, 14, -22, amp=amp, reach=6.0 + 2.0 * amp)
    CD.rays(c, 13, 35, [-90, -50, -14, 22, 60, 118, 160, 200],
            [int(v * ray_scale) for v in (6, 6, 8, 6, 7, 5, 5, 4)], gap=7)
    CD.draw_card(c, 13, 35, 8, 14, -22, face='w', shade='Y', dark='F',
                 pip=CD.SPADE5, pip_col='#', outline='#')
    FR.spinner(c, 16, 62, -38 + spin_phase, glow_amp=0.46)
    FR.spinner(c, 65, 67, 52 + spin_phase, glow_amp=0.42)
    for (sx, sy, sz) in ((22, 20, 2), (4, 47, 2), (47, 14, 1), (74, 55, 1), (28, 70, 1), (57, 24, 1)):
        CD.spark(c, sx, sy, max(1, sz - (1 if amp < 0.9 else 0)))
    CD.rim_light(c, 'IiUuNn' + 'gfdsa1' + 'LqQRE' + 'xXvVz', (13, 35), reach=46.0, xmax=42)
    return c


def scaled(c, f=5):
    g = to_rgba(c)
    return [[(g[y // f][x // f][:3] if g[y // f][x // f][3] else BG[:3]) + (255,)
             for x in range(W * f)] for y in range(H * f)]


if __name__ == '__main__':
    OUT = sys.argv[1]
    steps = [(0.80, 0.7, 0), (1.00, 1.0, 14), (1.18, 1.25, 28), (1.00, 1.0, 42)]
    imgs = [scaled(pose(*s)) for s in steps]
    write_gif(os.path.join(OUT, 'card_glow.gif'), imgs, [110] * len(imgs))
    print('wrote card_glow.gif', W * 5, 'x', H * 5, len(imgs), 'frames')
