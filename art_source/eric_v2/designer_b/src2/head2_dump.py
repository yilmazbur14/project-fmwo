import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'a_prop'))
sys.path.insert(1, HERE)
import rig2 as R
import headwarp as HW1
HS = 0.84
A = (48.0, 40.0)
A2 = (48.0, 96 + (40 - 96) * 0.8)

def HTinv(X, Y):
    return (A[0] + (X - A2[0]) / HS, A[1] + (Y - A2[1]) / HS)

def resample(lab):
    out = {}
    for Y in range(96):
        for X in range(96):
            sx, sy = HTinv(X + 0.5, Y + 0.5)
            k = (int(math.floor(sx)), int(math.floor(sy)))
            if k in lab:
                out[(X, Y)] = lab[k]
    return out

for yaw in (45, 90, 135, 180):
    reg, st = HW1.regions(yaw, 1)
    lab = resample(reg)
    xs = [x for x, y in lab]; ys = [y for x, y in lab]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    print('yaw', yaw, 'origin', x0, y0)
    for y in range(y0, y1 + 1):
        print('%2d %s' % (y, ''.join(lab.get((x, y), '.') for x in range(x0, x1 + 1))))
