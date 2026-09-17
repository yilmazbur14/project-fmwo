p = 'turn.py'
s = open(p).read()
s = s.replace("ZF, ZB = 0.93, 0.80", "ZF, ZB = 0.82, 0.72")
old = "def ellipsoid_samples(V, cx, cy, cz, rx, ry, rz, roll=0.0, step=0.35, tex=True, front_only_tex=True, kappa=None):"
new = "def ellipsoid_samples(V, cx, cy, cz, rx, ry, rz, roll=0.0, step=0.35, tex=True, front_only_tex=True, kappa=None,\n                      rim_axis=None):"
assert old in s
s = s.replace(old, new)
old2 = """            t = (48 + X, Y + kk * Z) if (tex and (Z - cz) > 0) else None
            smp.add(x, ys, d, V.nproj(n), t)"""
new2 = """            t = (48 + X, Y + kk * Z) if (tex and (Z - cz) > 0) else None
            tone = 0
            if rim_axis is not None:
                ux, uy, uz = ex / rx, ey / ry, ez / rz
                cth = ux * rim_axis[0] + uy * rim_axis[1] + uz * rim_axis[2]
                if cth > 0 and uy > 0.12:
                    sth = math.sqrt(max(0.0, 1 - cth * cth))
                    if 0.70 <= sth < 0.80:
                        tone = 1
                    elif 0.80 <= sth < 0.92:
                        tone = -1
            smp.add(x, ys, d, V.nproj(n), t, tone)"""
assert old2 in s
s = s.replace(old2, new2)
open(p, 'w').write(s)
print('ok')
