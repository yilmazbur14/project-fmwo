p = 'whirl.py'
s = open(p).read()

# ghost blade helper + edge-aware sword drawing
helper = '''

def a_limit(S, margin=5):
    """largest blade coordinate a whose centre-line and edges stay inside the frame"""
    best = 91.0
    a = 0.0
    while a <= 91.0:
        for b in (-10.5, 0.0, 10.5):
            x, y = S.P(a, b)
            if not (margin <= x <= 127 - margin and 1 <= y <= 126):
                return a - 1.0
        a += 1.0
    return best


def draw_sword_whirl(fr, S):
    c = cv(fr)
    lim = a_limit(S)
    if lim >= 90.5:
        S.draw(c)
        return None
    cut = max(18.0, lim - 22.0)
    S.draw_blade(c, a_max=cut)
    S.draw_grip(c); S.draw_pommel(c); S.draw_guard(c)
    # ghost: the rest of the blade smeared into pale speed streaks, tapering toward the frame edge
    span = max(1.0, lim + 6 - cut)
    for y in range(128):
        for x in range(128):
            a, b = S.ab(x, y)
            if a < cut - 0.8 or a > lim + 6:
                continue
            f = (a - cut) / span
            hw = 10.5 * (1.0 - 0.55 * f)
            if abs(b) > hw:
                continue
            q = b * S.dark / hw           # -1 lit edge .. +1 dark edge
            if f > 0.55 and (int(a) // 3) % 2 == 1 and abs(q) < 0.6:
                continue
            if q < -0.55:
                col = 'W'
            elif q < 0.25:
                col = 'A'
            elif q < 0.7:
                col = 'B'
            else:
                col = 'C' if f < 0.3 else 'B'
            if f > 0.8 and abs(q) > 0.3:
                continue
            fr.px[y][x] = PALC[col]
    return cut
'''
s = s.replace("\n\ndef whirl_frame(i, debug=False):", helper + "\n\ndef whirl_frame(i, debug=False):")

old = """    # ---------------------------------------------------------------- in front
    if not sword_behind:
        S.draw(cv(fr))
    if not back_mode:
        for sh, el, near in arms:
            if near:
                draw_arm(sh, el, fore_only=True)
        fist(fr, hands, vertical=abs(U[1]) > abs(U[0]))
    for args in ARCS:
        smear(fr, theta, *args, 'front')
    return fr"""
new = """    # ---------------------------------------------------------------- in front
    for args in ARCS:
        smear(fr, theta, *args, 'front')
    if not sword_behind:
        draw_sword_whirl(fr, S)
    if not back_mode:
        for sh, el, near in arms:
            if near:
                draw_arm(sh, el, fore_only=True)
        fist(fr, hands, vertical=abs(U[1]) > abs(U[0]))
    return fr"""
assert old in s
s = s.replace(old, new)
s = s.replace("""    if sword_behind:
        S.draw(cv(fr))""", """    if sword_behind:
        draw_sword_whirl(fr, S)""")
s = s.replace("ARCS = [(95, 118, 0.5, 16), (70, 84, 0.5, 9), (45, 56, 0.5, 4)]",
              "ARCS = [(100, 112, 0.5, 11), (75, 80, 0.5, 7), (50, 52, 0.5, 3)]")
open(p, 'w').write(s)
print('ok')
