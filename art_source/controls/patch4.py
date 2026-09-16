src = open('bg.py', encoding='utf-8').read()

# ---- banner polish: finials on the rod, soft folds below the lettering
old = '''    # inner trim lines
    c.hline(bx0 + 3, bx1 - 3, top + 3, IN)'''
new = '''    # finials on the rod ends
    for fx in (bx0 - 6, bx1 + 5):
        c.rect(fx, ry - 2, fx + 1, ry + 3, K)
        c.set(fx, ry - 1, G4)
        c.set(fx, ry, G3)
    # soft fabric folds in the lower part (kept clear of the lettering)
    for fx, ystart in ((bx0 + 13, top + 36), (bx1 - 14, top + 38)):
        for y in range(ystart, tail):
            frac = abs(fx - mid) / (mid - bx0)
            ybot = int(round(notch + (tail - notch) * frac))
            if y >= ybot - 1:
                break
            if c.get(fx, y) == N0:
                c.set(fx, y, IN if y > ystart + 1 or dith(fx, y, 0.5) else N0)
            if c.get(fx + 1, y) == N0:
                c.set(fx + 1, y, K if y > ystart + 3 else N0)
    # inner trim lines
    c.hline(bx0 + 3, bx1 - 3, top + 3, IN)'''
assert old in src
src = src.replace(old, new)

# ---- chalkboard: pull clear of the card edge
old_cb = "    x0, x1, y0, y1 = 2, 45, 34, 90"
assert old_cb in src
src = src.replace(old_cb, "    x0, x1, y0, y1 = 1, 42, 34, 90")
src = src.replace("    for (cx, cy) in [(11, 44), (33, 46)]:", "    for (cx, cy) in [(10, 44), (31, 46)]:")
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
