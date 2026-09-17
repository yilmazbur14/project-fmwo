SEG_CODE = r'''def seg_frame(t):
    """One flame-dome of the travelling shockwave. Rounded, fully outlined, so a chain of
    them overlapping at any spacing reads as one scalloped rolling crest."""
    cv = Canvas(SW, SH)
    tipdx = [0, 1, 0, -1][t]
    tiph = [0, -1, -2, -1][t]
    cxm = 11.5
    def ytop(x):
        u = (x + 0.5 - cxm) / 11.0
        # dome with a flame tip that sways a pixel side to side
        ut = (x + 0.5 - cxm - tipdx) / 11.0
        return 9.0 + 10.0 * u * u - (2.5 + (-tiph)) * max(0.0, 1 - abs(ut) * 4.0)
    def ybot(x):
        u = (x + 0.5 - cxm) / 11.0
        return 19.5 + 2.5 * math.sqrt(max(0.0, 1 - u * u))
    m = empty_mask(SW, SH)
    for x in range(SW):
        for y in range(SH):
            if ytop(x) <= y + 0.5 <= ybot(x):
                m[y][x] = True
    # emissive colouring: white-hot at the foot, cooling to red at the rim
    for y in range(SH):
        for x in range(SW):
            if not m[y][x]:
                continue
            dx = (x + 0.5 - cxm) / 11.5
            dy = (y + 0.5 - 18.5) / (10.0 if y + 0.5 < 18.5 else 3.5)
            e = math.sqrt(dx * dx + dy * dy)
            fl = 0.06 * [0, 1, 0, -1][t] * math.cos(3 * x)
            e += fl
            c = 'W' if e < 0.42 else ('P' if e < 0.62 else ('r' if e < 0.82 else 'R'))
            cv.put(x, y, PALC[c])
    for y in range(SH):
        for x in range(SW):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < SW and 0 <= yy < SH) or not m[yy][xx]:
                        cv.put(x, y, BLACK)
                        break
    # darker lower rim so it sits on the floor
    for x in range(SW):
        yb = None
        for y in range(SH - 1, -1, -1):
            if m[y][x]:
                yb = y
                break
        if yb is not None and yb - 1 >= 0 and cv.get(x, yb - 1) not in (None, BLACK):
            cv.put(x, yb - 1, PALC['X'] if abs(x + 0.5 - cxm) > 5 else PALC['R'])
    # hot streaks rising through the flame
    streak = [(9, 13, 17), (12, 15, 18), (10, 14, 17), (13, 16, 18)][t]
    cv.put(streak[0], streak[1], PALC['W'], only_empty=False)
    cv.put(streak[0], streak[1] + 1, PALC['W'])
    # rubble tossed over the crest + a chunk rolling at the foot
    hop = [4, 1, 0, 2]
    ra = SEG_ROCK if t % 2 == 0 else flipv(fliph(SEG_ROCK))
    cv.stamp(ra, 3 + (t % 2), hop[t])
    rb = SEG_PEBBLE if t % 2 else fliph(SEG_PEBBLE)
    cv.stamp(rb, 17, hop[(t + 2) % 4] + 1)
    foot = [(1, 18), (2, 17), (1, 18), (2, 18)][t]
    cv.stamp(SEG_ROCK, foot[0], foot[1])
    foot2 = [(19, 18), (19, 18), (18, 17), (19, 18)][t]
    cv.stamp(fliph(SEG_ROCK), foot2[0], foot2[1])
    SP = {0: [(11, 2, 'W'), (20, 8, 'r'), (7, 4, 'P')], 1: [(13, 1, 'W'), (21, 6, 'P'), (8, 7, 'r')],
          2: [(10, 1, 'P'), (20, 4, 'W'), (2, 9, 'r')], 3: [(14, 3, 'r'), (18, 1, 'W'), (1, 10, 'W')]}
    for x, y, c in SP[t]:
        cv.put(x, y, PALC[c], only_empty=True)
    return cv

'''
src=open('pound.py').read()
a=src.index("def seg_frame(t):"); b=src.index("# ------------------------------------------------------------------ output")
open('pound.py','w').write(src[:a]+SEG_CODE+src[b:])
