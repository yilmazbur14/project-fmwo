"""charge_up: back view built on the mirrored approved charge silhouette, re-shaded as a back."""
from approved import *
import paint_charge as pc
import frames_charge as fc


def mask_of(grid):
    return {(x, y) for y in range(64) for x in range(64) if grid[y][x] != '.'}


def mir(s):
    return {(63 - x, y) for x, y in s}


def back_view(alt=False, bob=0):
    lay = lambda L: mask_of(pc.paint([L], with_speed=False)[0])
    head_all = mask_of(HEAD_TUCK)
    taper = {11: (23, 40), 12: (22, 41), 13: (22, 41), 22: (22, 41), 23: (22, 41), 24: (22, 41), 25: (23, 40),
             26: (24, 39), 27: (25, 38), 28: (27, 36)}
    skull = {(x, y) for x, y in head_all if y <= 28 and 21 <= x <= 42
             and (y not in taper or taper[y][0] <= x <= taper[y][1])}
    earL = span_pixels({18: (18, 21), 19: (16, 21), 20: (16, 21), 21: (16, 21), 22: (16, 21), 23: (16, 21),
                        24: (17, 21), 25: (18, 22)})
    ears = earL | {(63 - x, y) for x, y in earL}
    beard = {(x, y) for x, y in head_all if y >= 27 and 22 <= x <= 41}
    trunk = lay(pc.L_TORSO) | beard | lay(pc.L_FOREARM) | lay(pc.L_FIST)
    trunk = {(x, y) for x, y in trunk if x >= 11 or y < 40}          # drop the elbow tip poking left
    trunk |= span_pixels({y: (22, 41) for y in range(27, 45)})
    if not alt:
        legs = [('pushleg', 1, 'skin', lay(pc.L_LEG_BACK)), ('pushboot', 0, 'boot', lay(pc.L_BOOT_BACK)),
                ('kneeleg', 3, 'skin', lay(pc.L_LEG_FRONT)), ('kneeboot', 2, 'boot', lay(pc.L_BOOT_FRONT))]
    else:  # swapped legs = f6 legs
        legF = span_pixels({48: (31, 43), 49: (30, 44), 50: (30, 45), 51: (30, 45), 52: (30, 45), 53: (31, 45), 54: (32, 44), 55: (33, 43)})
        bootF = span_pixels({54: (31, 45), 55: (31, 45), 56: (30, 45), 57: (30, 45), 58: (30, 45), 59: (31, 44), 60: (32, 43)})
        legB = span_pixels({49: (18, 30), 50: (17, 29), 51: (17, 28), 52: (17, 28), 53: (17, 27), 54: (17, 27), 55: (17, 26)})
        bootB = span_pixels({55: (16, 27), 56: (16, 27), 57: (16, 27), 58: (16, 27), 59: (15, 27), 60: (15, 27), 61: (14, 28), 62: (14, 28), 63: (14, 28)})
        legs = [('pushleg', 1, 'skin', legB), ('pushboot', 0, 'boot', bootB), ('kneeleg', 3, 'skin', legF), ('kneeboot', 2, 'boot', bootF)]
    up = lambda s: {(x, y + bob) for x, y in s}
    P = [Part(n, z, m, mir(s)) for n, z, m, s in legs]
    P += [Part('speedo', 4, 'blue', mir(lay(pc.L_SPEEDO))),
          Part('trunk', 5, 'skin', up(mir(trunk))),
          Part('arm', 6, 'skin', up(mir(lay(pc.L_ARM_TRAIL)))),
          Part('delt', 7, 'skin', up(mir(lay(pc.L_DELT_LEAD)))),
          Part('ears', 8, 'skin', up(mir(ears))),
          Part('skull', 9, 'skin', up(mir(skull)))]
    g, lab = shade(P, term_x=41)
    B = bob
    # dome + gloss unchanged by the flip (light stays upper-left)
    for (x, y) in skull:
        if y <= 19 and HEAD_TUCK[y][x] not in ('.', '#') and lab[y + B][x] == 'skull' and g[y + B][x] != '#':
            g[y + B][x] = HEAD_TUCK[y][x]
    rows = {20: (22, "Hssssssssssssssmmmmd"), 21: (22, "Hssssssssssssssmmmmd"), 22: (22, "Hsssssssssssssmmmmmd"),
            23: (22, "ssssssssssssssmmmmdd"), 24: (22, "msssssssssssssmmmddd"), 25: (22, "mmssssssssssssmmmddd"),
            26: (22, "ddmmmsssssssmmmmdddD"), 27: (22, "dddmmmmmmmmmmmmddDDD"), 28: (22, "DDDDdddddddddddDDDDD")}
    for y, (x0, s) in rows.items():
        for i, c in enumerate(s):
            if lab[y + B][x0 + i] == 'skull' and g[y + B][x0 + i] != '#':
                g[y + B][x0 + i] = c
    for x, y in [(x, y) for y in range(64) for x in range(64) if lab[y][x] == 'ears' and g[y][x] != '#']:
        g[y][x] = ('H' if x <= 17 else 's') if x < 31 else ('d' if x <= 45 else 'm')
    # 1px cast shadow on shoulders/traps just outside each ear so the ears separate from the body behind
    for y in range(12, 30):
        for x in range(1, 63):
            if lab[y][x] in ('delt', 'arm', 'trunk') and g[y][x] not in ('#',):
                if any(lab[y + dy][x + dx] == 'ears' for dx, dy in ((1, 0), (-1, 0), (0, -1), (1, -1), (-1, -1))):
                    g[y][x] = 'D'
    # beard tips peeking past the jaw on both sides
    segs(g, {29 + B: [(22, "#oO#"), (38, "#rR#")], 30 + B: [(23, "#r#"), (38, "#R#")], 31 + B: [(24, "#"), (39, "#")]})
    # earring: his right ear = screen right from behind
    segs(g, {27 + B: [(43, "#c#")], 28 + B: [(42, "#CcC#")], 29 + B: [(43, "#C#")], 30 + B: [(44, "#")]})
    # back anatomy: spine groove, blades, lat creases
    tr = ('trunk',)
    line(g, lab, [(31, y + B) for y in range(31, 46)], 'm', tr)
    line(g, lab, [(32, y + B) for y in range(31, 46)], 'D', tr)
    line(g, lab, [(x, y + B) for x in range(24, 30) for y in (32, 33)], 'H', tr)
    line(g, lab, [(x, 36 + B) for x in range(24, 30)] + [(x, 36 + B) for x in range(35, 41)], 'd', tr)
    line(g, lab, [(x, y + B) for x in range(35, 40) for y in (32, 33)], 's', tr)
    line(g, lab, [(x, 40 + B) for x in (25, 26, 37, 38)], 'm', tr)
    repaint_speedo(g, lab)
    # push-off boot shows its SOLE (heel up); knee-leg boot shows its heel counter
    for part, sole in (('pushboot', True), ('kneeboot', False)):
        px = [(x, y) for y in range(64) for x in range(64) if lab[y][x] == part and g[y][x] != '#']
        if not px:
            continue
        top = min(y for x, y in px)
        for x, y in px:
            r = y - top
            if sole:
                g[y][x] = 'g' if r == 0 else ('q' if r in (1, 2) else ('K' if r == 3 else ('q' if r % 2 == 0 else 'k')))
            else:
                g[y][x] = 'q' if r == 0 else 'k'
    for y in range(23, 30):          # neck in shadow between skull base and ears
        for x in range(19, 45):
            if g[y][x] == '.':
                g[y][x] = 'D'
    # speed lines trailing BELOW him
    base = blank()
    off = 4 if alt else 0
    for x, a, b in [(5, 42, 58), (10, 50, 63), (54, 46, 60), (59, 34, 50), (62, 22, 40), (2, 26, 42), (51, 58, 63)]:
        a, b = a + off, min(63, b + off)
        n = b - a + 1
        if n < 3:
            continue
        for i, y in enumerate(range(a, b + 1)):
            t = i / (n - 1)
            base[y][x] = 'f' if t < 0.45 else ('F' if t < 0.75 else 'L')
    return paste(base, g)


def f7():
    return back_view(False, 0)


def f8():
    return back_view(True, 1)
