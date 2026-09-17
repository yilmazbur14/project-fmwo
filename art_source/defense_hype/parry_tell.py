"""Parry tells: a red alert badge that floats above a boss's head while a parryable attack winds up.
  parry_tell        : 6 frames of 32x24, pivot (16, 24). Red diamond with a white "!", pulsing.
  parry_tell_strong : 6 frames of 48x36, pivot (24, 36). Same badge bigger, inside a double broken ring
                      with spark ticks and a white-hot flash - the parry also staggers the boss.
  parry_glow        : 4 frames of 32x32, pivot (16, 16). Red aura drawn BEHIND a parryable projectile.
Frame 0 of each is the brightest, so spawning on frame 0 pops in without needing a fade.
A diamond (not a shield or a heart) so it can never be confused with the HUD hearts or a health bar.
DB32 only, alpha 0/255, 1 px black outline like the rest of the kit."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *

# body palettes: normal, bright (pulse peak), hot (spawn / strong flash)
PAL_NORMAL = {'H': 'e', 'B': 'E', 'S': 'r', 'G': 'W'}
PAL_BRIGHT = {'H': 'S', 'B': 'e', 'S': 'E', 'G': 'W'}
PAL_HOT = {'H': 'W', 'B': 'e', 'S': 'E', 'G': 'W'}


def bang(h):
    """white '!' glyph h rows tall (stem, gap, dot)"""
    stem = max(2, h - 3)
    return ['GGG'] * stem + ['...'] + ['GGG'] * 2


def badge(c, cx, cy, rx, ry, pal, glyph):
    inside = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if abs(x - cx) / rx + abs(y - cy) / ry <= 1.0:
                inside.add((x, y))
    for (x, y) in inside:
        up = (x, y - 1) not in inside or (x - 1, y) not in inside
        dn = (x, y + 1) not in inside or (x + 1, y) not in inside
        c.set(x, y, C[pal['H'] if up else (pal['S'] if dn else pal['B'])])
    for (x, y) in inside:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in inside and c.inb(*q):
                c.set(q[0], q[1], C['K'])
    if glyph:
        gh, gw = len(glyph), len(glyph[0])
        for j, row in enumerate(glyph):
            for i, ch in enumerate(row):
                if ch != '.':
                    c.set(int(round(cx - gw / 2.0)) + i, int(round(cy - gh / 2.0)) + j, C[pal[ch]])
    return inside


def halo(c, col):
    """1 px glow ring on empty pixels around everything drawn so far (0/255 alpha, so it is a hard ring)"""
    solid = {(x, y) for y in range(c.h) for x in range(c.w) if c.p[y][x]}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in solid and c.inb(*q) and c.get(*q) is None:
                c.set(q[0], q[1], C[col])


def ticks(c, cx, cy, r0, r1, angles, cols):
    for ang in angles:
        a = math.radians(ang)
        for k, t in enumerate(range(int(r0), int(r1) + 1)):
            c.set(int(round(cx + t * math.cos(a))), int(round(cy + t * math.sin(a))),
                  C[cols[min(len(cols) - 1, k)]])


def ring(c, cx, cy, r, col, gaps=()):
    for y in range(c.h):
        for x in range(c.w):
            d = math.hypot(x - cx, y - cy)
            if r - 0.5 <= d < r + 0.5:
                a = math.degrees(math.atan2(y - cy, x - cx)) % 360
                if any((a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1) for a0, a1 in gaps):
                    continue
                if c.get(x, y) is None:
                    c.set(x, y, C[col])


# ------------------------------------------------------------------ standard tell (32x24)
TW, TH = 32, 24
T_CX, T_CY, T_RX, T_RY = 16, 11, 7.5, 9.0
TELL_DURATIONS_MS = [90, 90, 110, 110, 90, 90]


def tell_frame(f):
    """0 pops (hot + halo + corner sparks), 1 bright, 2-3 rest (bobbed down 1 px), 4-5 swell back"""
    c = Canvas(TW, TH)
    pal = [PAL_HOT, PAL_BRIGHT, PAL_NORMAL, PAL_NORMAL, PAL_NORMAL, PAL_BRIGHT][f]
    bob = [0, 0, 1, 1, 1, 0][f]
    grow = [1, 0, 0, 0, 0, 1][f]                        # the badge swells 1 px on the peak frames
    badge(c, T_CX, T_CY + bob, T_RX + grow, T_RY + grow, pal, bang(9))
    if f in (0, 5):
        halo(c, 'e')
        ticks(c, T_CX, T_CY + bob, T_RX + 4, T_RX + 5 + (1 if f == 0 else 0), (-40, -140, 40, 140), ['e', 'S'])
    elif f in (1, 4):
        halo(c, 'E')
    return c


def parry_tell():
    return [tell_frame(f) for f in range(6)]


# ------------------------------------------------------------------ strong tell (48x36)
SW_, SH_ = 48, 36
S_CX, S_CY, S_RX, S_RY = 24, 17, 9.5, 11.5
STRONG_DURATIONS_MS = [70, 70, 80, 80, 70, 70]


def strong_frame(f):
    """bigger badge in a double broken ring, spark ticks, white-hot on frame 0; faster loop"""
    c = Canvas(SW_, SH_)
    pal = [PAL_HOT, PAL_HOT, PAL_BRIGHT, PAL_NORMAL, PAL_BRIGHT, PAL_HOT][f]
    bob = [0, 0, 1, 1, 1, 0][f]
    grow = [1, 1, 0, 0, 0, 1][f]
    badge(c, S_CX, S_CY + bob, S_RX + grow, S_RY + grow, pal, bang(13))
    hot0 = f in (0, 1, 5)
    if hot0:
        halo(c, 'e' if f == 0 else 'E')                 # glow hugs the badge only, before the rings go on
    rot = f * 24
    r_in = [14, 14, 13, 13, 14, 14][f]
    r_out = [17, 17, 16, 16, 17, 17][f]
    hot = hot0
    ring(c, S_CX, S_CY + bob, r_in, 'W' if f == 0 else ('S' if hot else 'e'),
         gaps=[((58 + rot) % 360, (122 + rot) % 360), ((238 + rot) % 360, (302 + rot) % 360)])
    ring(c, S_CX, S_CY + bob, r_out, 'e' if hot else 'E',
         gaps=[((148 + rot) % 360, (212 + rot) % 360), ((328 + rot) % 360, (32 + rot) % 360)])
    ln = [5, 4, 2, 2, 3, 4][f]
    ticks(c, S_CX, S_CY + bob, r_out + 2, r_out + 1 + ln, (-30, -150, 30, 150),
          ['W', 'e', 'E', 'r', 'r'] if hot else ['e', 'E', 'r', 'r', 'r'])
    ticks(c, S_CX, S_CY + bob, r_out + 2, r_out + int(ln / 2) + 1, (-70, -110, 70, 110),
          ['e', 'E', 'r'] if hot else ['E', 'r', 'r'])
    return c


def parry_tell_strong():
    return [strong_frame(f) for f in range(6)]


# ------------------------------------------------------------------ projectile aura (32x32)
GW, GH = 32, 32
G_C = 16
GLOW_DURATIONS_MS = [90, 90, 90, 90]


def glow_frame(f):
    """pulsing red aura for a parryable projectile: solid inner ring, dithered falloff, clear centre"""
    c = Canvas(GW, GH)
    r = [11.0, 12.0, 13.0, 12.0][f]
    for y in range(GH):
        for x in range(GW):
            d = math.hypot(x - G_C + 0.5, y - G_C + 0.5)
            if d > r:
                continue
            t = d / r
            if t < 0.45:
                continue
            if t < 0.62:
                col = 'E'
            elif t < 0.78:
                col = 'E' if (x + y) % 2 == 0 else 'e'
            elif t < 0.9:
                col = 'r' if (x + y) % 2 == 0 else None
            else:
                col = 'r' if (x % 2 == 0 and y % 2 == 0) else None
            if col:
                c.set(x, y, C[col])
    if f in (1, 2):
        ticks(c, G_C, G_C, r - 1, r, (-45, 45, 135, 225), ['e', 'S'])
    return c


def parry_glow():
    return [glow_frame(f) for f in range(4)]


def build():
    return {'parry_tell': parry_tell(), 'parry_tell_strong': parry_tell_strong(), 'parry_glow': parry_glow()}


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32, 'bbox f0', bbox(frames[0]))
        save_zoom(s, work('%s_8x.png' % name), 8, bg=(70, 70, 90), grid=(frames[0].w, frames[0].h))
        for bg, tag in (((255, 255, 255), 'white'), ((136, 180, 99), 'green'), ((32, 32, 40), 'dark')):
            save_zoom(s, work('%s_3x_%s.png' % (name, tag)), 3, bg=bg, grid=(frames[0].w, frames[0].h))
