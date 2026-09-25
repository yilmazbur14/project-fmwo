"""A head projection that can also tip the head back (pitch), for heads thrown back to spit upward.

heads.Xf turns a head (phi) and tilts it in the picture (theta). PXf first rotates head space about
the x axis through the eye line by `pitch` degrees (positive tips the nose up and back: forward points
rise, the chin comes forward and up), then does exactly what heads.Xf does. With pitch 0 it is heads.Xf.
"""
import math

from common import heads


class PXf(heads.Xf):
    def __init__(self, cx=heads.HX, cy=heads.HY, phi=0.0, s=1.0, theta=0.0, pitch=0.0, pivot=(0.0, 0.0)):
        super().__init__(cx, cy, phi, s, theta)
        self.pitch = pitch
        self.cq, self.sq = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        self.pv = pivot            # (ly, z) of the pitch axis in head space, relative to (HX, HY)

    def _tip(self, ly, z):
        py, pz = self.pv
        a, b = ly - py, z - pz
        return py + a * self.cq - b * self.sq, pz + a * self.sq + b * self.cq

    def p(self, x, y, z=0.0):
        lx, ly = x - heads.HX, y - heads.HY
        ly2, z2 = self._tip(ly, z)
        x1 = lx * self.cp + z2 * self.sp
        x2, y2 = self.s * x1, self.s * ly2
        return (self.cx + x2 * self.ct - y2 * self.st, self.cy + x2 * self.st + y2 * self.ct)

    def inv(self, X, Y, z=0.0):
        x3, y3 = X - self.cx, Y - self.cy
        x2 = x3 * self.ct + y3 * self.st
        y2 = -x3 * self.st + y3 * self.ct
        x1, ly2 = x2 / self.s, y2 / self.s
        py, pz = self.pv
        # ly2 = py + a*cq - (z - pz)*sq  ->  a
        b = z - pz
        a = (ly2 - py + b * self.sq) / (self.cq or 1e-6)
        ly = a + py
        z2 = pz + a * self.sq + b * self.cq
        lx = (x1 - z2 * self.sp) / (self.cp or 1e-6)
        return (lx + heads.HX, ly + heads.HY)
