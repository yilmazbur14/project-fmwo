"""portrait_demon: the A2 mask for the dialogue balloon (his last line), 64x64 like every portrait in
the cast. A close-up at about 1.5x the sprite: the same design with room for more of it (a derived
close-up carries more detail than the sprite, never less). The same palette, keyline, obsidian
ramp and rim lights as the sprite; its black ratio and colour count are checked against the same
crop of the hover sprite's frame 0 (jg_export --check prints both).

Composition: the crown of flame-horns fanning up out of his hair and breaking the top edge (the
tallest sweeping right, his quiff); the mask filling the middle, its heavy brow plate slanting
down in anger over burning almond eyes, cheek plates, a fanged furnace grin, his patchy beard
as glowing cracks along the jaw; a gorget and collar spikes under the chin; pauldron spikes in the
bottom corners; the core's crown of light at the bottom edge.
Mirror axis between columns 31 and 32 (x' = 63 - x); the right side is re-lit, not copied.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402
import jg_lord as L  # noqa: E402
from jg_lord_pal import PAL_A2  # noqa: E402

S = 64
AXP = 63             # mirror: x' = 63 - x
OBS_KEYS = L.OBS_KEYS


def mirp(part):
    return {(AXP - x, y): k for (x, y), k in part.items()}


def mpp(p):
    return (AXP - p[0], p[1])


def obsidian(mask, radius=None, cuts=(0.24, 0.44, 0.64, 0.86)):
    return L.obsidian(mask, radius=radius, cuts=cuts)


def both(C, part, radius=None, outline=True):
    C.stamp(part, outline=outline)
    m = mirp(part)
    if all(k in OBS_KEYS for k in m.values()):
        m = obsidian(set(m), radius=radius)
    C.stamp(m, outline=outline)


def spike(base, deg, length, width, bend=0.0, radius=2.0):
    return obsidian(L.spike_mask(base, math.radians(deg), length, width, bend), radius=radius)


# the mask's outline, left half, brow line to chin (mirrored to close it)
MASK_L = [(31.5, 21), (22, 21.5), (14, 23), (9.5, 27), (8, 31), (8.5, 36), (10, 41), (12, 45.5),
          (15, 49), (19, 52), (25, 53.5), (31.5, 54)]
# his hair: a swept mass above the mask, higher at the front right (the quiff's side)
HAIR = [(8.5, 29), (8, 23), (10, 17), (15, 12.5), (22, 10), (30, 9), (38, 8.5), (46, 10), (51.5, 14),
        (55, 19), (55.5, 25), (55, 29), (48, 23.5), (40, 21.5), (31.5, 21), (23, 21.5), (15, 23.5)]


def horns():
    """(back row, front row). Each horn: obsidian root heating to a gold tip; the quiff (the
    tallest, sweeping right) breaks the top edge."""
    specs_back = [((12, 19), [(7, 15), (4, 11), (2, 7)], 2.6),
                  ((18, 14), [(15, 10), (13, 6), (13, 2)], 2.9),
                  ((51, 19), [(56, 15), (59, 11), (61, 7)], 2.6),
                  ((45, 14), [(48, 10), (50, 6), (50, 2)], 2.9)]
    specs_front = [((25, 12), [(24, 8), (23, 4), (24, 1)], 3.1),
                   ((36, 11), [(37, 7), (40, 3), (45, 1), (51, 1)], 3.7)]     # the quiff, sweeping right
    back = [L.flame_horn(b, c, r) for (b, c, r) in specs_back]
    front = [L.flame_horn(b, c, r) for (b, c, r) in specs_front]
    return back, front


def build():
    C = B.Canvas(S, S)

    # 1. pauldrons in the bottom corners and their spikes
    pa = L.top_edge(obsidian(B.poly([(-2, 51), (7, 47), (17, 50), (21, 58), (17, 64), (-2, 64)]), radius=6), '5')
    C.stamp(pa)
    C.stamp(L.top_edge(obsidian(set(mirp(pa)), radius=6), '4'))
    for base, ang, ln, wd in (((6, 48), -120, 11, 2.8), ((1, 55), -160, 7, 2.2)):
        both(C, spike(base, ang, ln, wd, bend=-1.2))

    # 2. the top of the chest
    pec = L.top_edge(obsidian(B.poly([(18, 57), (31.5, 58.5), (31.5, 64), (16, 64)]), radius=6), '5')
    C.stamp(pec)
    C.stamp(L.top_edge(obsidian(set(mirp(pec)), radius=6), '4'))

    # 3. gorget and collar spikes
    C.stamp(L.obs_tube([(31.5, 49), (31.5, 58)], [6.0, 6.8]))
    both(C, spike((22, 56), -112, 8, 2.0, bend=-0.8))

    # 4. back horns, then his hair (obsidian, clumped, embers where the grease shone)
    back, front = horns()
    for h in back:
        C.stamp(h)
    hair = obsidian(B.poly(HAIR), radius=5, cuts=(0.30, 0.50, 0.70, 0.90))
    for pts in ([(12, 24), (14, 18), (19, 13)], [(19, 22), (22, 16), (27, 11)], [(27, 21), (31, 15), (36, 10)],
                [(36, 21), (41, 16), (46, 12)], [(44, 22), (49, 18), (52, 15)]):
        for q in B.polyline([(int(round(x)), int(round(y))) for x, y in pts]):
            if q in hair:
                hair[q] = '1'
    for q, k in (((16, 19), 'r'), ((24, 15), 'O'), ((33, 13), 'r'), ((42, 15), 'O'), ((49, 20), 'r')):
        if q in hair:
            hair[q] = k
    C.stamp(hair)

    # 5. the mask
    mask_pts = MASK_L + [mpp(p) for p in reversed(MASK_L[:-1])]
    mask = B.poly(mask_pts)
    C.stamp(obsidian(mask, radius=9, cuts=(0.20, 0.40, 0.62, 0.86)))

    def put(x, y, k, mirror_key=None, both_sides=True):
        if (x, y) in C.px:
            C.px[(x, y)] = k
        if both_sides and (AXP - x, y) in C.px:
            C.px[(AXP - x, y)] = mirror_key or k

    # forehead: a V ridge down to the brow (his widow's peak)
    for i, y in enumerate(range(22, 29)):
        put(31 - i // 3, y, 'k', both_sides=True)
    # the brow plate: steep V, lit top edge, black shelf beneath
    for x in range(9, 32):
        t = (x - 9) / 22.0
        y0 = int(round(26 + t * 6.5))
        put(x, y0 - 1, '5' if x < 29 else '4', mirror_key='4')
        put(x, y0, '4', mirror_key='3')
        put(x, y0 + 1, 'k')
        put(x, y0 + 2, 'k')
    # the eyes: angry almonds deep in black sockets, following the brow down to the nose
    sock = B.poly([(11, 30), (17, 31), (24, 34), (29, 37), (26, 39.5), (18, 37.5), (12, 34)])
    for (x, y) in sock:
        put(x, y, 'k')
    eye = B.poly([(13, 32), (18, 32.5), (24, 35), (27, 37), (19, 36.5), (14, 34)])
    for (x, y) in eye:
        edge = any(q not in eye for q in B.neighbours4((x, y)))
        hot = 18 <= x <= 22 and 34 <= y <= 35
        put(x, y, 'w' if (hot and not edge) else ('O' if edge else 'Y'))
    # cheek plates: a ridge from the temple to under the eye, hollow beneath
    for q in B.polyline([(9, 38), (13, 39), (18, 40), (23, 41)]):
        put(q[0], q[1], '5', mirror_key='4')
        put(q[0], q[1] + 1, 'k')
    # nose ridge and nostrils
    for y in range(35, 43):
        put(30, y, '5', both_sides=False)
        put(31, y, '4', both_sides=False)
        put(32, y, '2', both_sides=False)
    for q in ((28, 43), (29, 43)):
        put(q[0], q[1], 'k')
    # the grin: a wide furnace slit, fangs down from the top lip and up from the bottom
    grin = B.poly([(14, 44), (31.5, 45), (31.5, 50), (16, 48.5)])
    for (x, y) in grin:
        c = abs(x - 31.5)
        top = (x, y - 1) not in grin
        bot = (x, y + 1) not in grin
        if top or bot or x <= 15:
            k = 'k'
        else:
            k = 'Y' if c < 4 else 'O' if c < 8 else 'r' if c < 12 else 'R'
        put(x, y, k)
    for fx in (18, 22, 26, 30):
        put(fx, 46, '5', mirror_key='4')
        put(fx, 47, '4', mirror_key='3')
        put(fx - 1, 46, '4', mirror_key='3')
    for fx in (20, 24, 28):
        put(fx, 48, '4', mirror_key='3')
    # his patchy beard as glowing cracks: moustache halves that never meet, the jaw line broken at
    # the corner, chin patches, the fuller chin
    beard = [[(18, 43), (22, 42.5), (27, 43)],
             [(9, 37), (10.5, 42)], [(12.5, 46), (15.5, 50), (19.5, 52)],
             [(21, 51), (25, 52)], [(28, 51), (29, 53)]]
    for path in beard:
        for q in B.polyline([(int(round(x)), int(round(y))) for x, y in path]):
            if C.px.get(q) in OBS_KEYS:
                put(q[0], q[1], 'T' if (q[0] + q[1]) % 3 else 'R')
    for q in ((31, 52), (32, 52), (31, 53), (32, 53)):
        if C.px.get(q) in OBS_KEYS:
            C.px[q] = 'T' if q[1] < 53 else 'R'
    # ear fins sweeping back
    both(C, spike((8.5, 33), 196, 7, 2.0, bend=1.2, radius=1.8))

    # 6. the front horns: the left one and the quiff
    for h in front:
        C.stamp(h)

    # 7. the core's crown of light at the bottom edge, cracks climbing out of it
    for q, k in (((31, 63), 'w'), ((32, 63), 'w'), ((31, 62), 'Y'), ((32, 62), 'Y'), ((31, 61), 'O'),
                 ((32, 61), 'O'), ((31, 60), 'R'), ((32, 60), 'R'), ((29, 63), 'P'), ((34, 63), 'P'),
                 ((30, 62), 'O'), ((33, 62), 'O'), ((28, 63), 'Q'), ((35, 63), 'Q')):
        C.px[q] = k
    L.GLOW[0] = 1.0
    for pts in ([(28, 62), (24, 60), (20, 59)], [(29, 61), (27, 58)]):
        for path in (pts, [mpp(q) for q in pts]):
            L.draw_crack(C, path, 0.8, 0.2)

    px = L.rim_light(C.px, warm_below=48)
    px = {p: ('k' if k == '1' else k) for p, k in px.items()}
    px = L.fill_pinholes(px)
    return {p: k for p, k in px.items() if 0 <= p[0] < S and 0 <= p[1] < S}


def image():
    return B.image(build(), S, S, PAL_A2)


if __name__ == '__main__':
    out = sys.argv[1]
    im = image()
    print(B.stats(im))
    B.up(im, 8, bg=(60, 60, 72, 255)).save(os.path.join(out, 'portrait_demon_8x.png'))
