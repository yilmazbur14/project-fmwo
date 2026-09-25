"""burak_ball.png: Burak's shot, a small cast-iron ball with a spark trail (Attacks 1 and 2). 20 frames of
32x32, one strip:
  frames 0-3     heading 0 degrees (flying right)
  frames 4-7     heading 22.5
  frames 8-11    heading 45
  frames 12-15   heading 67.5
  frames 16-19   heading 90 (flying down)
4 flicker frames per heading at 0.05 s, looping. Godot angles (y down); the code picks the nearest 22.5
degree heading to its true flight and flips for the other quadrants (flip_h for leftward, flip_v for
upward). The ball is round, so snapping only the trail's angle costs nothing where it matters.
THE PIVOT IS THE FRAME CENTRE (16, 16): the ball's centre, for every heading and flip (no offset).

The ball: 7 texels across, iron from Burak's sheet (#DCE3EE glint top left through #4E4F66 and #23232F to a
#15151D rim), dark against the mat. The trail: hot powder sparks streaming off its back (#FFF3B0, #F5D94E,
#E0AB35 cooling to #B07D22) with a couple of loose sparks and a smoke speck, streaming back frame to frame.
"""
import math

import bfx_pal as pal

W = H = 32
C = 16.0
FRAME_SIZE = (32, 32)
NOTE = '20 frames: 0/22.5/45/67.5/90 deg x 4 (0.05 s loop); pivot = frame centre (16,16), the ball'
HEADINGS = (0.0, 22.5, 45.0, 67.5, 90.0)
R = 3.6


def ball(g):
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - C, y + 0.5 - C
            d = math.hypot(dx, dy)
            if d > R:
                continue
            hl = math.hypot(dx + 1.3, dy + 1.3)
            if d > R - 0.9:
                k = 'x' if dx + dy > -1.0 else 'k'
            elif hl < 0.8:
                k = 'S'
            elif hl < 1.7:
                k = 's'
            elif hl < 2.8:
                k = 'I'
            elif dx + dy > 1.5:
                k = 'K'
            else:
                k = 'k'
            g[y][x] = k


def trail(g, theta, f):
    t = math.radians(theta)
    d = (math.cos(t), math.sin(t))
    n = (-d[1], d[0])
    # the main stream: a tapering line of sparks behind the ball, the hot end nearest it
    pts = []
    s = R - 0.5
    while s < 15.5:
        wob = 0.55 * math.sin(s * 1.3 + f * 1.6) * min(1.0, (s - R) / 4.0)
        x = C - d[0] * s + n[0] * wob
        y = C - d[1] * s + n[1] * wob
        pts.append((s, int(math.floor(x)), int(math.floor(y))))
        s += 0.25
    seen = set()
    for (s, x, y) in pts:
        if (x, y) in seen or not (0 <= x < W and 0 <= y < H) or g[y][x] != '.':
            continue
        # break the stream into sparks that stream back a little each frame
        if s > 7 and int(s * 1.1 + f * 1.4) % 3 == 0:
            continue
        seen.add((x, y))
        g[y][x] = 'Q' if s < 5.5 else ('Y' if s < 8.5 else ('G' if s < 12 else 'g'))
    # a second, thinner stream to one side near the ball: the trail is 2 wide where it's hottest
    for s in (4.2, 5.0, 5.8):
        side = 0.9 if f % 2 == 0 else -0.9
        x = int(math.floor(C - d[0] * s + n[0] * side))
        y = int(math.floor(C - d[1] * s + n[1] * side))
        if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
            g[y][x] = 'Y'
    # loose sparks and a smoke speck, drifting back
    for (s0, off, k) in ((9.0, 2.4, 'Y'), (13.0, -2.2, 'G'), (16.5, 1.0, 'c')):
        s = s0 + 1.2 * f
        if s > 17.5:
            s -= 7.0
        x = int(math.floor(C - d[0] * s + n[0] * off))
        y = int(math.floor(C - d[1] * s + n[1] * off))
        if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
            g[y][x] = k


def frame(theta, f):
    g = pal.blank(W, H)
    ball(g)
    trail(g, theta, f)
    return pal.rows(g)


def frames():
    by = {t: [frame(t, f) for f in range(4)] for t in (0.0, 22.5, 45.0)}
    by[67.5] = [pal.transpose(fr) for fr in by[22.5]]
    by[90.0] = [pal.transpose(fr) for fr in by[0.0]]
    out = []
    for t in HEADINGS:
        out.extend(by[t])
    return out
