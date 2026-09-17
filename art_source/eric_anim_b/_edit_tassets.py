p = 'turn.py'
s = open(p).read()
s += '''


def tasset_wrap_samples(V, layer, R=26.0, Rz=18.0, step=0.34, wrap=78.0):
    """tassets hang on the hip ring: front-view |X| 0..25 wraps from the front (t=90) toward the side
    (t = 90 +- wrap) so that turned views see a real plate over the thigh."""
    smp = Samples()
    ys = [y for y in range(N) for x in range(N) if layer[y][x] is not None]
    xs = [x for y in range(N) for x in range(N) if layer[y][x] is not None]
    if not ys:
        return smp
    y = min(ys)
    while y <= max(ys) + 1:
        x = min(xs)
        while x <= max(xs) + 1:
            ix, iy = int(math.floor(x)), int(math.floor(y))
            if 0 <= ix < N and 0 <= iy < N and layer[iy][ix] is not None:
                Xf = x - 48
                t = math.radians(90.0 - wrap * max(-1.0, min(1.0, Xf / 25.0)))
                X, Z = R * math.cos(t), Rz * math.sin(t)
                n = norm((math.cos(t) / R, 0.12, math.sin(t) / Rz))
                Yl = y - KAPPA * 9.0
                px, py, d = V.proj(X, Yl, Z)
                smp.add(px, py, d, V.nproj(n), (x, y))
            x += step
        y += step
    return smp
'''
open(p, 'w').write(s)

p = 'views.py'
s = open(p).read()
old = "        smp = T.plate_from_layer(V, part, R=HIP_R, Rz=HIP_RZ)"
assert old in s
s = s.replace(old, "        smp = T.tasset_wrap_samples(V, part)")
open(p, 'w').write(s)

p = 'whirl.py'
s = open(p).read()
s = s.replace("HANDS_R, SH_R = 25.0, 22.0", "HANDS_R, SH_R = 27.0, 22.0")
s = s.replace("return BA.solve_elbow(sh, h, 18.0, 17.0, bend)", "return BA.solve_elbow(sh, h, 16.0, 15.5, bend)")
open(p, 'w').write(s)
print('ok')
