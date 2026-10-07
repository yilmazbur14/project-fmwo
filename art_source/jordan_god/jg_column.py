"""The fire column: a separate layer, the lava-fire he rises out of. It stands from the bottom of
the screen up to his feet (its top tucks behind his legs and tail), hottest down its spine,
licking flames along its sides, embers riding up, and at its foot a boil of flame with black
clawed hands reaching up out of it (keylined, they are things, not light). Everything else is
effect art: no keyline, no semi-alpha.

Size 96x224 texels; its pivot (48, 64) sits on his anchor, so its tip rises between his legs to
his hips (seen through the gap between them) and its foot reaches the bottom of the screen."""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402
import jg_body as Y  # noqa: E402
import jg_fx as FX  # noqa: E402
from jg_lord_pal import LORD  # noqa: E402

W, H = 96, 224
PIVOT = (48, 64)    # sits on his anchor: the column's top rises 64 texels up between his legs
CX = 47.5
PAL = dict(LORD)
HEAT = ('V', 'R', 'T', 'r', 'O', 'Y', 'w')


def column_field(seed=2):
    """Heat for every texel: a narrow lava stream rising between his legs, flaring into a burst
    of tongues round his feet and tail, then a column whose width breathes down to a boil at
    the foot. Wobbled so each colour band licks upward."""
    rnd = random.Random(seed)
    out = {}
    tongues = [(CX + rnd.uniform(-14, 14), rnd.uniform(100, H - 30), rnd.uniform(8, 18), rnd.uniform(2.5, 4.5),
                rnd.choice((-1, 1)) * rnd.uniform(1, 4)) for _ in range(14)]
    # the burst round his feet and tail (his anchor is at row 64)
    for dx, hgt in ((-23, 16), (-17, 30), (-11, 22), (-6, 38), (-1, 26), (5, 34), (10, 19), (16, 28), (22, 14)):
        tongues.append((CX + dx, 78 + rnd.uniform(-2, 2), hgt + rnd.uniform(-3, 3),
                        3.0 + rnd.uniform(0, 1.4), (1 if dx > 0 else -1) * rnd.uniform(2, 7) + rnd.uniform(-1.5, 1.5)))
    for y in range(H):
        cx = CX + 1.2 * math.sin(y / 17.0)
        if y < 8:
            half = 1.0 + y * 0.35                          # the tip, at his hips
        elif y < 46:
            half = 3.8 + 0.6 * math.sin(y / 5.0)           # the stream between his legs
        elif y < 78:
            half = 3.8 + 9.0 * math.sin((y - 46) / 32.0 * math.pi / 2)   # flaring round his feet
        else:
            t = (y - 78) / float(H - 78)
            half = 11.0 + 6.0 * t ** 1.3 + 1.6 * math.sin(y / 9.0)
        boil = 0.0
        if y > H - 44:
            u = (y - (H - 44)) / 44.0
            boil = 26.0 * math.sin(min(1.0, u * 1.3) * math.pi / 2)
        for x in range(W):
            best = -1.0
            hw = max(half, boil)
            d = abs(x - cx) / hw
            if d < 1.0:
                best = (1.0 - d) * 0.95 + (0.25 if y > 8 else 0.1)
            for (tx, ty, th, tw, lean) in tongues:
                u = (ty - y) / th
                if 0 <= u <= 1:
                    xc = tx + lean * u * u
                    hh = tw * (1 - u) ** 0.8
                    if hh > 0.4 and abs(x - xc) < hh:
                        v = (1 - abs(x - xc) / hh) * 0.55 + (1 - u) * 0.3
                        best = max(best, v)
            if best > 0:
                n = FX.wobble(x, y * 0.5, amp=0.18, seed=seed * 0.37)
                out[(x, y)] = best + n
    return out


def clawed_hand(base, angle, scale, curl, side):
    """A black, reaching hand: forearm, splayed fingers, hooked claws. Keylined."""
    parts = []
    dx, dy = math.cos(angle), math.sin(angle)
    wrist = (base[0] + dx * 10 * scale, base[1] + dy * 10 * scale)
    parts.append(Y.limb([base, wrist], [2.6 * scale, 1.9 * scale], ('1', '2', '3'), cuts=[0.45, 0.8]))
    palm = (wrist[0] + dx * 2.5 * scale, wrist[1] + dy * 2.5 * scale)
    parts.append(B.shade(B.ellipse(palm[0], palm[1], 2.4 * scale, 2.4 * scale), ('1', '2', '3'), radius=2,
                         cuts=[0.45, 0.8]))
    for j, off in enumerate((-0.55, -0.18, 0.18, 0.55)):
        a = angle + off
        k1 = (palm[0] + math.cos(a) * 5 * scale, palm[1] + math.sin(a) * 5 * scale)
        a2 = a + curl * side
        tip = (k1[0] + math.cos(a2) * 4 * scale, k1[1] + math.sin(a2) * 4 * scale)
        parts.append(Y.limb([palm, k1, tip], [0.9 * scale, 0.8 * scale, 0.3], ('1', '2', '3'), cuts=[0.45, 0.8]))
    return parts


def build():
    C = B.Canvas(W, H)
    field = column_field()
    fire = FX.colour_heat(field, ramp=HEAT, cuts=(0.16, 0.34, 0.52, 0.70, 0.86, 1.02))
    C.px.update(fire)
    # black clawed hands reaching up out of the flames at its foot, in front of the fire
    hands = [((14, H + 2), math.radians(-66), 1.35, 0.55, 1), ((82, H + 2), math.radians(-114), 1.35, 0.55, -1),
             ((30, H + 3), math.radians(-80), 1.1, 0.45, 1), ((66, H + 3), math.radians(-100), 1.05, 0.45, -1),
             ((3, H + 4), math.radians(-58), 1.0, 0.5, 1), ((93, H + 4), math.radians(-122), 1.0, 0.5, -1)]
    for (base, ang, sc, curl, side) in hands:
        for p in clawed_hand(base, ang, sc, curl, side):
            C.stamp(p)
    # the fire lights them: a warm rim on their edges
    lit = {}
    for (x, y), k in C.px.items():
        if k in ('1', '2', '3') and any(C.px.get(q) == 'k' and any(r not in C.px or C.px.get(r) in HEAT
                                                                     for r in B.neighbours4(q))
                                        for q in B.neighbours4((x, y))):
            lit[(x, y)] = 'V' if k == '1' else 'R'
    C.px.update(lit)
    # flames licking back over their wrists
    rnd = random.Random(12)
    for i in range(10):
        x0 = rnd.uniform(4, 92)
        base = H
        h = rnd.uniform(8, 16)
        for (x, y), k in FX.colour_heat(FX.fire_tail(x0, base - 1, base, 3, [(x0, h, 3.2, rnd.uniform(-2, 2))]),
                                          ramp=HEAT, cuts=(0.2, 0.4, 0.6, 0.8, 0.95, 1.1)).items():
            if 0 <= x < W and 0 <= y < H:
                C.px[(x, y)] = k
    # embers riding up
    rnd = random.Random(8)
    for i in range(34):
        x = int(CX + rnd.gauss(0, 16))
        y = rnd.randrange(4, H - 24)
        if 0 <= x < W and (x, y) not in C.px:
            C.px[(x, y)] = rnd.choice(('r', 'O', 'T', 'Y'))
    return {q: ('k' if k == '1' else k) for q, k in C.px.items() if 0 <= q[0] < W and 0 <= q[1] < H}


def image():
    return B.image(build(), W, H, PAL)


if __name__ == '__main__':
    out = sys.argv[1]
    im = image()
    B.up(im, 3, bg=(8, 6, 16, 255)).save(os.path.join(out, 'column_3x.png'))
    print(B.stats(im))
