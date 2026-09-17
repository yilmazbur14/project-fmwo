"""motion smear for the big-frame whirlwind (white/pale, no outline, like the approved sheet FX)"""
import math
import scaled  # noqa: path setup
from lib import PALC

CX, CY = 128, 168          # spin centre (belt height)
RX, RY = 121, 26           # tip path ellipse (x reach matches the blade tip)


def whirl_smear(fr, back):
    """Crescent trail following the blade tip backwards around the spin.
    The blade points right (0 deg); the trail runs over the far side (top of the ellipse) toward the left,
    thick right behind the blade and thinning out. back=True draws it (behind the body)."""
    if not back:
        return
    for y in range(fr.H):
        for x in range(fr.W):
            dx, dy = (x + 0.5 - CX), (y + 0.5 - CY)
            if dy > 2:
                continue
            ex, ey = dx / RX, dy / RY
            r = math.sqrt(ex * ex + ey * ey)
            if r > 1.0 or r < 0.55:
                continue
            ang = math.degrees(math.atan2(-dy, dx))     # 0 right, 90 far side, 180 left
            if ang < -4 or ang > 200:
                continue
            t = max(0.0, min(1.0, ang / 200.0))
            thick = 0.34 * (1 - t) + 0.05                 # normalised band thickness
            if r < 1.0 - thick:
                continue
            q = (r - (1.0 - thick)) / thick
            if q > 0.6:
                fr.px[y][x] = PALC['W']
            elif q > 0.25:
                if t < 0.8:
                    fr.px[y][x] = PALC['A']
            elif t < 0.45:
                fr.px[y][x] = PALC['B']
