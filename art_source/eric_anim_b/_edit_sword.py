p = 'sword.py'
s = open(p).read()
old = """                bs = b * self.sb * self.dark        # + toward the dark side, screen px
                hwd = self.blade_hw(a, self.dark) * self.sb
                hwl = self.blade_hw(a, -self.dark) * self.sb"""
new = """                bs = b * self.bscale * self.dark    # + toward the dark side, screen px
                hwd = self.blade_hw(a, self.dark) * self.bscale
                hwl = self.blade_hw(a, -self.dark) * self.bscale"""
assert old in s
s = s.replace(old, new)
old = """        if dark is None:
            dark = 1 if (self.p[0] + self.p[1]) >= 0 else -1
        self.dark = dark"""
new = """        if dark is None:
            dark = 1 if (self.p[0] + self.p[1]) >= 0 else -1
        self.dark = dark
        self.bscale = sb"""
assert old in s
s = s.replace(old, new)
s += '''

class AffineSword(Sword):
    """Sword with an arbitrary (oblique) screen projection: P = o + a*U + b*Pv.
    U = screen vector for one unit along the blade, Pv = screen vector for one unit across it."""

    def __init__(self, origin, U, Pv, dark=None):
        import math as _m
        self.o = origin
        self.U, self.Pv = U, Pv
        lu = _m.hypot(*U) or 1e-6
        self.u = (U[0] / lu, U[1] / lu)
        self.ang = _m.degrees(_m.atan2(U[1], U[0]))
        # perpendicular (screen) direction on the same side as Pv
        pp = (-self.u[1], self.u[0])
        if pp[0] * Pv[0] + pp[1] * Pv[1] < 0:
            pp = (-pp[0], -pp[1])
        self.p = pp
        self.sa = lu
        self.bscale = abs(Pv[0] * pp[0] + Pv[1] * pp[1])
        self.sb = self.bscale
        det = U[0] * Pv[1] - U[1] * Pv[0]
        self._inv = (Pv[1] / det, -Pv[0] / det, -U[1] / det, U[0] / det)
        if dark is None:
            dark = 1 if (pp[0] + pp[1]) >= 0 else -1
        self.dark = dark

    def P(self, a, b):
        return (self.o[0] + self.U[0] * a + self.Pv[0] * b, self.o[1] + self.U[1] * a + self.Pv[1] * b)

    def ab(self, x, y):
        dx, dy = x + 0.5 - self.o[0], y + 0.5 - self.o[1]
        i00, i01, i10, i11 = self._inv
        return (i00 * dx + i01 * dy, i10 * dx + i11 * dy)
'''
open(p, 'w').write(s)
print('ok')
