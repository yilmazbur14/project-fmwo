"""Greyson's one-armed spirit bomb, drawn to the user's Genki Dama references (scratchpad/greyson_fight/
spirit_bomb_ref_1-3.png): a SOFT, bright sphere whose white core fills most of it and fades smoothly to pale
blue, a thin SATURATED cyan-blue rim hatched with fine short spikes that drip downward along its bottom edge,
a glow haze spreading beyond the rim; round soft orbs with halos drifting up into it; blue light over the whole
scene and on him. Raised on his one cannon arm, straight up. Four sheets:
  greyson_bomb         20 frames of 432x432 in a grid of 5 columns x 4 rows (hframes 5, vframes 4). f0-15: the
                       sphere GROWING off the cannon's muzzle, radius 8 to 172 texels (344 across at full size, 4x
                       his height), played across the 2.5 s gather (0.15 s each, or spread to fit); f16-19: the full
                       sphere SHIMMERING, looped at 0.08 s (the spikes flicker, the haze breathes). PIVOT: the
                       cannon's muzzle (216, 398): the sphere's foot, which stays on the muzzle as it grows.
  greyson_bomb_orb     4 rows (small, medium, large, extra large) x 4 frames of 48x48 (hframes 4, vframes 4),
                       looped at 0.1 s:
                       a mote of the crowd's energy, a white ball in a pale-blue skin in a four-step halo, the halo
                       breathing. The code sends them up from the crowd all round the arena into the sphere, in
                       mixed sizes. PIVOT: the centre (24, 24).
  greyson_bomb_light   1 frame of 640x360: blue light over the whole scene, a screen-space layer at scale 3 drawn
                       over the arena and the fighters (him included), under the sphere, the orbs and the HUD:
                       pale round the sphere, deep blue out at the corners, in ten alpha steps. Authored for the
                       proposed cast spot (his feet at (960, 800) px, the sphere's centre at (1041, -52) px). Fade
                       it in (modulate alpha 0 to 1) with the sphere's growth. PIVOT: top-left (0, 0).
  greyson_bomb_screen  10 frames of 640x360, once: the full-screen explosion, a screen-space layer at scale 3,
                       top-left pivot. White flashes on f0, f3 and f6 only, 0.4 s apart (2.5 a second: under the
                       3-a-second photosensitivity limit); between them blue-cyan blast rings over a blue wash;
                       then the wash fades. Frame times: 0.10, 0.15, 0.15, 0.10, 0.15, 0.15, 0.10, 0.25, 0.35,
                       0.35 s (1.85 s). Draw the player's disintegration OVER this layer so it is seen through it.
No keyline, no dither; the soft parts are stepped: the body's white-to-blue fade in up to nine colour steps, the
haze in eight alpha steps, the orbs' halos in four, the light in ten.
"""
import math
import random

import gfx_pal as pal

BW, BH = 432, 432
MX, MY = 216.0, 398.0
GAP = 8                      # texels between the muzzle and the sphere's foot at full size (the drips hang into it)
N_GROW = 16
RADII = [int(round(8 + (172 - 8) * i / (N_GROW - 1.0))) for i in range(N_GROW)]
R_FULL = RADII[-1]
SW, SH = 640, 360

# the body, white to the rim: the pale ramp (up to nine steps, fewer on a small sphere) and the saturated rim
RAMP = ['F3FAFF', 'E6F5FF', 'D8F0FF', 'C9EAFF', 'B9E3FF', 'A6DBFF', '90D2FF', '78C8FF', '5EBDFF']
RAMP_KEYS = '123456789'
WHITE_Q = 0.70               # white out to 70% of the radius
RIM_KEYS = {'H': pal.hx('40C8FF'), 'I': pal.hx('2A94F4')}
# the haze beyond the rim: (texels out at full size, colour, alpha), eight steps
HAZE = [(3, '8FE4FF', 200), (7, '6FDCFF', 168), (11, '5FD0FF', 136), (16, '4FC0FF', 108), (21, '40B0FF', 84),
        (26, '3A9CF5', 62), (31, '2A8CF0', 42), (36, '2A7CE0', 24)]
HAZE_KEYS = '!#$%&*+='
TIP_KEYS = {'<': pal.hx('40C8FF', 160), '>': pal.hx('40C8FF', 96)}

LOCAL = {}
LOCAL.update({k: pal.hx(c) for k, c in zip(RAMP_KEYS, RAMP)})
LOCAL.update(RIM_KEYS)
LOCAL.update({k: pal.hx(c, a) for k, (_, c, a) in zip(HAZE_KEYS, HAZE)})
LOCAL.update(TIP_KEYS)


def body_bands(R):
    """[(outer radius in texels, key)] from the white core out to the rim, for a sphere of radius R."""
    t_i = max(1.0, 0.02 * R)
    t_h = max(1.0, 0.025 * R)
    r_ramp_out = R - t_i - t_h
    r_white = WHITE_Q * R
    width = max(0.0, r_ramp_out - r_white)
    n = max(1, min(9, int(round(width / 3.0))))
    idx = [4] if n == 1 else [int(round(j * 8.0 / (n - 1))) for j in range(n)]
    bands = [(r_white, 'W')]
    for j, i in enumerate(idx):
        bands.append((r_white + width * (j + 1) / n, RAMP_KEYS[i]))
    bands.append((R - t_i, 'H'))
    bands.append((R, 'I'))
    return bands


def line(g, x0, y0, x1, y1, keyfn):
    """A 1-texel line from (x0, y0) to (x1, y1); keyfn(t) gives the key at fraction t along it (None skips)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / float(n)
        x, y = int(math.floor(x0 + (x1 - x0) * t)), int(math.floor(y0 + (y1 - y0) * t))
        k = keyfn(t)
        if k and 0 <= x < len(g[0]) and 0 <= y < len(g):
            g[y][x] = k


def sphere(g, R, seed, breathe=0.0):
    """The sphere of radius R standing on the muzzle."""
    gap = max(3.0, GAP * R / float(R_FULL))
    cx, cy = MX, MY - gap - R
    rnd = random.Random(seed)
    k_halo = max(0.35, R / float(R_FULL))
    bands = body_bands(R)
    haze = [(lim * k_halo + breathe, k) for (lim, _, _), k in zip(HAZE, HAZE_KEYS)]
    reach = int(R + haze[-1][0] + 2)
    for y in range(max(0, int(cy) - reach), min(BH, int(cy) + reach + 1)):
        for x in range(max(0, int(cx) - reach), min(BW, int(cx) + reach + 1)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= R:
                for (lim, k) in bands:
                    if d <= lim:
                        g[y][x] = k
                        break
            else:
                for (lim, k) in haze:
                    if d - R <= lim:
                        g[y][x] = k
                        break
    # fine short spikes all round the rim: a stroke in from the rim over the pale body (the hatching), and one out
    # into the haze; along the bottom the outer strokes turn downward and lengthen into drips
    if R >= 16:
        s = R / float(R_FULL)
        n = int(2 * math.pi * R / 3.0)
        for i in range(n):
            a = 2 * math.pi * (i + rnd.uniform(-0.3, 0.3)) / n
            ca, sa = math.cos(a), math.sin(a)
            px, py = cx + ca * (R - 0.5), cy + sa * (R - 0.5)
            if rnd.random() < 0.65:
                l_in = rnd.uniform(2.0, 7.0) * math.sqrt(s)
                line(g, px - ca * l_in, py - sa * l_in, px, py, lambda t: 'H')
            w = min(1.0, max(0.0, (sa - 0.15) / 0.6))
            dx, dy = ca * (1 - w), sa + w
            dl = math.hypot(dx, dy)
            dx, dy = dx / dl, dy / dl
            l_out = rnd.uniform(1.5, 4.0) + s * rnd.uniform(0.0, 3.0)
            if sa > 0:
                l_out += (sa ** 1.5) * rnd.uniform(2.0, 10.0) * s
            line(g, px, py, px + dx * l_out, py + dy * l_out,
                 lambda t: 'I' if t < 0.55 else ('<' if t < 0.8 else '>'))
    # the feed from the cannon's muzzle up into the sphere's foot: a white spine in a cyan glow, flaring as it
    # meets the sphere
    y_top = int(cy + R - 2)
    for y in range(y_top, int(MY) + 1):
        t = (MY - y) / max(1.0, MY - y_top)
        hw = 1.3 + 1.9 * t * t
        for x in range(int(MX - 2 * hw) - 1, int(MX + 2 * hw) + 2):
            dd = abs(x + 0.5 - MX) / hw
            if not (0 <= y < BH and 0 <= x < BW) or dd > 1.9:
                continue
            k = 'W' if dd < 0.45 else ('C' if dd < 0.8 else ('A' if dd < 1.15 else ('!' if dd < 1.5 else '$')))
            if g[y][x] in '.$%&*+=' or k in 'WCA':
                g[y][x] = k


def bomb_frame(f):
    g = pal.blank(BW, BH)
    if f < N_GROW:
        sphere(g, RADII[f], seed=f)
    else:
        sphere(g, R_FULL, seed=40 + f, breathe=[0.0, 2.0, 4.0, 2.0][f - N_GROW])
    return pal.Frame(pal.rows(g), LOCAL)


# the orbs: (white radius, pale-skin radii, halo radius) in texels
ORBS = [(1.2, (2.0,), 5.0), (2.2, (3.0, 3.6), 8.5), (3.6, (4.8, 5.8), 13.2), (5.6, (7.4, 8.8), 20.0)]
OW = 48
ORB_HALO = [('(', 'A8EAFF', 200), (')', '78DCFF', 144), ('[', '4FC4FF', 92), (']', '3AA4F8', 48)]
ORB_LOCAL = {k: pal.hx(c, a) for (k, c, a) in ORB_HALO}
ORB_BREATHE = [1.0, 1.06, 1.1, 1.04]


def orb_frame(size, f):
    g = pal.blank(OW, OW)
    cx = cy = OW / 2.0
    rw, skins, halo = ORBS[size]
    rc = skins[-1]
    halo = rc + (halo - rc) * ORB_BREATHE[f]
    skin_keys = ['C', 'c'][:len(skins)]
    for y in range(OW):
        for x in range(OW):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= rw:
                g[y][x] = 'W'
                continue
            for r, k in zip(skins, skin_keys):
                if d <= r:
                    g[y][x] = k
                    break
            else:
                for j, (k, _, _) in enumerate(ORB_HALO):
                    if d <= rc + (halo - rc) * (j + 1) / len(ORB_HALO):
                        g[y][x] = k
                        break
    return pal.Frame(pal.rows(g), ORB_LOCAL)


# the proposed staging: the cast spot (his feet) and the muzzle's offset from his feet in the body artist's spirit
# frame (greyson_fight_approval f4: feet (56, 111), muzzle (83, 7)), all at scale 3
CAST_FEET = (960, 800)
MUZZLE_OFF = (27, -104)
SPHERE_CENTRE = (CAST_FEET[0] / 3.0 + MUZZLE_OFF[0], CAST_FEET[1] / 3.0 + MUZZLE_OFF[1] - GAP - R_FULL)
# the light, out from the sphere's edge: (texels beyond the edge, colour, alpha), ten steps
LIGHT_BANDS = [(24, '8FD0FF', 120), (64, '7CC2FF', 128), (104, '6AB2F8', 134), (144, '5AA0EE', 140),
               (184, '4C8CE0', 146), (224, '4078D0', 152), (264, '3666BC', 158), (304, '2E56A6', 164),
               (344, '284A90', 172), (9999, '223F78', 184)]
LIGHT_KEYS = 'jlotxzDdgh'


def light_frame():
    g = pal.blank(SW, SH)
    local = {k: pal.hx(c, a) for k, (_, c, a) in zip(LIGHT_KEYS, LIGHT_BANDS)}
    cx, cy = SPHERE_CENTRE
    for y in range(SH):
        for x in range(SW):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.15) - R_FULL
            for k, (lim, _, _) in zip(LIGHT_KEYS, LIGHT_BANDS):
                if d <= lim:
                    g[y][x] = k
                    break
    return pal.Frame(pal.rows(g), local)


SCREEN_TIMES = [0.10, 0.15, 0.15, 0.10, 0.15, 0.15, 0.10, 0.25, 0.35, 0.35]
FLASH = {0: 232, 3: 216, 6: 200}
WASH = {1: 160, 2: 176, 4: 176, 5: 192, 7: 176, 8: 112, 9: 56}


def screen_frame(f):
    g = pal.blank(SW, SH)
    cx, cy = SW / 2.0, SH / 2.0
    local = {}
    if f in FLASH:
        a = FLASH[f]
        local = {'5': pal.hx('FFFFFF', a), '6': pal.hx('E6F7FF', a)}
        for y in range(SH):
            for x in range(SW):
                d = math.hypot((x + 0.5 - cx) / 320, (y + 0.5 - cy) / 180)
                g[y][x] = '5' if d < 0.7 else '6'
        return pal.Frame(pal.rows(g), local)
    a = WASH[f]
    local = {'7': pal.hx('2E5FB0', a), '8': pal.hx('1E3566', a), '9': pal.hx('5FE1FF', min(255, a + 48)),
             '0': pal.hx('E6F7FF', min(255, a + 64))}
    for y in range(SH):
        for x in range(SW):
            d = math.hypot((x + 0.5 - cx) / 320, (y + 0.5 - cy) / 180)
            g[y][x] = '7' if d < 0.75 else '8'
    # energy rings racing out from the blast, and rays, while it is still hot
    if f <= 7:
        age = {1: 0, 2: 1, 4: 2, 5: 3, 7: 4}[f]
        for n in range(3):
            r = 40 + age * 70 + n * 55
            count = int(2 * math.pi * r * 1.2)
            for i in range(count):
                t = 2 * math.pi * i / count
                x = int(cx + r * math.cos(t))
                y = int(cy + r * 0.62 * math.sin(t))
                for w in range(3 - n):
                    if 0 <= x < SW and 0 <= y + w < SH:
                        g[y + w][x] = '0' if n == 0 else '9'
        rnd = random.Random(f)
        for i in range(18):
            t = rnd.uniform(0, 2 * math.pi)
            r0 = rnd.uniform(30, 120)
            for s in range(rnd.randint(30, 90)):
                x = int(cx + (r0 + s) * math.cos(t))
                y = int(cy + (r0 + s) * 0.62 * math.sin(t))
                if 0 <= x < SW and 0 <= y < SH:
                    g[y][x] = '9'
    return pal.Frame(pal.rows(g), local)


def bomb_frames():
    return [bomb_frame(f) for f in range(N_GROW + 4)]


def bomb_rows():
    fr = bomb_frames()
    return [fr[i:i + 5] for i in range(0, len(fr), 5)]


def orb_frames():
    """Row by row: small, medium, large, extra large; 4 frames each."""
    return [orb_frame(sz, f) for sz in range(4) for f in range(4)]


def orb_rows():
    return [[orb_frame(sz, f) for f in range(4)] for sz in range(4)]


def light_frames():
    return [light_frame()]


def screen_frames():
    return [screen_frame(f) for f in range(10)]


SHEETS = {'greyson_bomb': (bomb_frames, (BW, BH)), 'greyson_bomb_orb': (orb_frames, (OW, OW)),
          'greyson_bomb_light': (light_frames, (SW, SH)), 'greyson_bomb_screen': (screen_frames, (SW, SH))}
ROWS = {'greyson_bomb': bomb_rows, 'greyson_bomb_orb': orb_rows}
