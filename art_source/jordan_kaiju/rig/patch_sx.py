"""Give the rig a horizontal scale `sx` about the feet (sx = -1 draws it turned to face left, |sx| < 1 the
squash of a turn in progress). The light stays upper left: every normal is worked out after the flip.
sx = 1 changes nothing (the rest frame stays the approved kaiju)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))


def sub(path, old, new, count=1):
    p = os.path.join(HERE, path)
    s = open(p).read()
    if old not in s:
        raise SystemExit('not found in %s: %r' % (path, old[:90]))
    s = s.replace(old, new, count)
    open(p, 'w').write(s)


sub('kjr.py', """    def __init__(self, pose=None, sc=BASE_SC, feet=FEET):
        self.pose = pose or {}
        self.sc = sc""", """    def __init__(self, pose=None, sc=BASE_SC, feet=FEET, sx=1.0):
        self.pose = pose or {}
        self.sc = sc
        self.sx = sx""")
sub('kjr.py', """        self.rest = not any(any(v) for v in self.pose.values()) and sc == BASE_SC""",
    """        self.rest = not any(any(v) for v in self.pose.values()) and sc == BASE_SC and sx == 1.0""")
sub('kjr.py', """    def T(self, b, p):
        x, y = self.W(b, p)
        return (self.ox + self.sc * (x - DX0), self.oy + self.sc * (y - DY0))""", """    def T(self, b, p):
        x, y = self.W(b, p)
        if self.sx != 1.0:
            return (self.ox + self.sc * self.sx * (x - DX0), self.oy + self.sc * (y - DY0))
        return (self.ox + self.sc * (x - DX0), self.oy + self.sc * (y - DY0))

    def fx_(self, x):
        \"\"\"A frame x laid out unflipped about the feet, flipped / squashed by sx.\"\"\"
        return self.ox + (x - self.ox) * self.sx if self.sx != 1.0 else x""")
sub('kjr.py', """    def E(self, b, cx, cy, rx, ry, z=0.0):
        p = self.T(b, (cx, cy))
        return Ell(p[0], p[1], self.R(rx), self.R(ry), z=self.R(z), ang=self.rot[b])

    def C(self, b, p0, p1, r0, r1, z=0.0):
        return Cap(self.T(b, p0), self.T(b, p1), self.R(r0), self.R(r1), z=self.R(z))""", """    def E(self, b, cx, cy, rx, ry, z=0.0):
        p = self.T(b, (cx, cy))
        if self.sx != 1.0:
            a = abs(self.sx)
            return Ell(p[0], p[1], self.R(rx) * a, self.R(ry), z=self.R(z),
                       ang=self.rot[b] * (1 if self.sx > 0 else -1))
        return Ell(p[0], p[1], self.R(rx), self.R(ry), z=self.R(z), ang=self.rot[b])

    def C(self, b, p0, p1, r0, r1, z=0.0):
        if self.sx != 1.0:
            k = 0.5 + 0.5 * abs(self.sx)
            return Cap(self.T(b, p0), self.T(b, p1), self.R(r0) * k, self.R(r1) * k, z=self.R(z))
        return Cap(self.T(b, p0), self.T(b, p1), self.R(r0), self.R(r1), z=self.R(z))""")
sub('kjr.py', """    def inv(self, q):
        \"\"\"Frame -> world design.\"\"\"
        return ((q[0] - self.ox) / self.sc + DX0, (q[1] - self.oy) / self.sc + DY0)""", """    def inv(self, q):
        \"\"\"Frame -> world design.\"\"\"
        return ((q[0] - self.ox) / (self.sc * self.sx) + DX0, (q[1] - self.oy) / self.sc + DY0)""")
sub('kjr.py', """        a = math.radians(self.rot[b])
        c, s = math.cos(a), math.sin(a)
        return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)""", """        a = math.radians(self.rot[b])
        c, s = math.cos(a), math.sin(a)
        return ((v[0] * c - v[1] * s) * self.sx, v[0] * s + v[1] * c)""")
# plates: lay out unflipped, then flip / squash the outline about the feet
sub('kjr.py', """        base = (rig.ox + rig.sc * (bp[0] - DX0), rig.oy + rig.sc * (bp[1] - DY0))
        parts.append((plate_part(plate_poly(base, d, rig.R(h), rig.R(w)), glow, dim=(row == 'far'),
                                 flash=flash and glow > 0), g, s))""", """        base = (rig.ox + rig.sc * (bp[0] - DX0), rig.oy + rig.sc * (bp[1] - DY0))
        pts = plate_poly(base, d, rig.R(h), rig.R(w))
        if rig.sx != 1.0:
            pts = [(rig.fx_(x), y) for (x, y) in pts]
        parts.append((plate_part(pts, glow, dim=(row == 'far'), flash=flash and glow > 0), g, s))""")
# the ridge is read in world design space; under sx the plates' base points are built unflipped (above)
# sprite sampling under sx
sub('kjr.py', """            vx, vy = tx + 0.5 - ax, ty + 0.5 - ay
            ux = (vx * ca + vy * sa) / k""", """            vx, vy = tx + 0.5 - ax, ty + 0.5 - ay
            vx = vx / rig.sx
            ux = (vx * ca + vy * sa) / k""")
sub('kjr.py', """    rad = int(math.ceil(max(span) * max(1.0, k))) + 2""", """    rad = int(math.ceil(max(span) * max(1.0, k) / min(1.0, abs(rig.sx)))) + 2""")
# belly half widths squash a little with the turn
sub('kjr.py', """    half = [rig.R(h) for h in BELLY_HALF]""", """    half = [rig.R(h) * (0.5 + 0.5 * abs(rig.sx)) for h in BELLY_HALF]""")
print('patched')
