src = open('bg.py', encoding='utf-8').read()

# ---- banner: drop the fold lines (flat reads cleaner), keep finials
a = src.index('    # soft fabric folds in the lower part')
b = src.index('    # inner trim lines', a)
src = src[:a] + src[b:]

# ---- chalkboard: rewrite the chalk content
a = src.index('    # faint chalk dust smears')
b = src.index('    # tray', a)
chalk = '''    # faint chalk dust (old erased marks), kept away from the play
    for k in range(16):
        if dith(7 + k, 80, 0.45):
            c.set(7 + k, 80, G2)
        if dith(7 + k, 81, 0.25):
            c.set(7 + k, 81, G2)
    ch = G4
    # two X's (defenders) and an O (target)
    for (cx, cy) in [(10, 44), (31, 46)]:
        for k in range(-2, 3):
            c.set(cx + k, cy + k, ch)
            c.set(cx + k, cy - k, ch)
    O = [".XXX.", "X...X", "X...X", "X...X", ".XXX."]
    stamp(c, 27, 68, O, G5)
    # evenly dashed curve from the first X around to the O
    p0, p1, p2 = (10.0, 49.0), (10.0, 71.0), (23.0, 70.0)
    pts = []
    for k in range(0, 400):
        t = k / 399.0
        px = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        py = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        q = (int(round(px)), int(round(py)))
        if not pts or pts[-1] != q:
            pts.append(q)
    for k, (px, py) in enumerate(pts):
        if k % 5 < 3:
            c.set(px, py, ch)
    # arrow head pointing at the O
    for (hx, hy) in [(23, 70), (22, 69), (21, 68), (22, 71), (21, 72)]:
        c.set(hx, hy, ch)
'''
src = src[:a] + chalk + src[b:]
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
