"""Assemble Josh's two frames: 0 = standing idle with a fan of cards, 1 = signature card throw."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
import head, body
import cards as CD


def fan(c, pivot, angles, radius=11.0, w=6, h=12, pip_on_front=True, front_red=True):
    """Cards fanned about a fist pivot, back to front. Only the front card shows a pip - on a real
    fan you just see the edges of the ones behind, and pips on them turn to noise at this size."""
    px, py = pivot
    n = len(angles)
    for i, a in enumerate(angles):
        r = math.radians(a)
        cx = px + radius * math.sin(r)
        cy = py - radius * math.cos(r)
        front = (i == n - 1)
        CD.draw_card(c, cx, cy, w, h, a,
                     pip=(CD.DIAMOND3 if (front and pip_on_front) else None),
                     pip_col='Q' if front_red else '#')
    # grip: a few glove pixels back over the card bases so the fist reads as holding them
    for (dx, dy) in ((-1, 1), (0, 1), (1, 1), (-1, 2), (0, 2), (1, 2), (0, 0)):
        if c[py + dy][px + dx] not in '.':
            put(c, px + dx, py + dy, 'Q' if (dx + dy) % 2 == 0 else 'q')


def spinner(c, cx, cy, ang, w=5, h=9, glow_amp=0.0):
    """A card tumbling in orbit, with a thin gold heat-rim."""
    if glow_amp:
        CD.card_glow(c, cx, cy, w, h, ang, amp=glow_amp, reach=2.0)
    CD.draw_card(c, cx, cy, w, h, ang, pip=CD.DIAMOND3, pip_col='Q')


def frame0(shades_up=True):
    c = blank()
    body.build_body(c, body.POSE0)
    head.build(c, shades_up=shades_up)
    # fan of three in his right hand (our left), held low and cocky
    fan(c, (25, 67), [-78, -52, -26], radius=11.0)
    CD.glow(c, [(15, 64, 0.32), (17, 60, 0.30), (20, 57, 0.26)], 8.0)
    # one card idling in orbit past his shoulder
    spinner(c, 66, 45, 26, glow_amp=0.42)
    CD.spark(c, 61, 36, 2)
    CD.spark(c, 70, 57, 1)
    return c


def frame1(shades_up=True):
    """Signature: one blazing card held forward between two fingers, a fan in the other hand,
    cards spinning around him."""
    c = blank()
    body.build_body(c, body.POSE1)
    head.build(c, shades_up=shades_up)
    # five-card spread held high in his left hand (our right)
    fan(c, (62, 44), [-8, 16, 40, 64], radius=9.5)
    CD.glow(c, [(61, 33, 0.30), (65, 35, 0.28), (70, 39, 0.26)], 8.0)
    # the blazing card, held forward between two fingers of his right hand (our left)
    CD.card_glow(c, 13, 35, 8, 14, -22, amp=1.0, reach=7.0)
    CD.rays(c, 13, 35, [-90, -50, -14, 22, 60, 118, 160, 200], [6, 6, 8, 6, 7, 5, 5, 4], gap=7)
    CD.draw_card(c, 13, 35, 8, 14, -22, face='w', shade='Y', dark='F',
                 pip=CD.SPADE5, pip_col='#', outline='#')
    for (gx, gy) in ((17, 42), (16, 40), (18, 40)):   # gold spill onto the gripping fingers
        if c[gy][gx] != '.':
            put(c, gx, gy, 'D')
    # the card is the light source: warm rim down his near side
    CD.rim_light(c, 'IiUuNn' + 'gfdsa1' + 'LqQRE' + 'xXvVz', (13, 35), reach=46.0, xmax=42)
    # cards spinning around him
    spinner(c, 16, 62, -38, glow_amp=0.46)
    spinner(c, 65, 67, 52, glow_amp=0.42)
    for (sx, sy, sz) in ((22, 20, 2), (4, 47, 2), (47, 14, 1), (74, 55, 1), (28, 70, 1), (57, 24, 1)):
        CD.spark(c, sx, sy, sz)
    return c


if __name__ == '__main__':
    OUT = sys.argv[1]
    for i, fn in enumerate((frame0, frame1)):
        c = fn()
        save_png(c, OUT + '/f%d.png' % i)
        preview(c, OUT + '/f%d_8x.png' % i, s=8)
    print('ok')
