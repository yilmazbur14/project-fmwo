"""THE ELEMENT WHEEL, the full set (the approved design; the coordinator's technical calls 2026-10-06):

  element_wheel.png        8 x 192x192: the disc turned 0, 11.25 ... 78.75 degrees CLOCKWISE (frame 0 = rest).
                           The code adds whole 90-degree turns (pixel-exact on this even, corner-centred square):
                           32 positions.
  element_wheel_lit.png    8 x 192x192 stop states at REST orientation (the code turns them by the same 90-degree
                           multiple as the stop): water, earth, fire, air, then fire+air, air+water, water+earth,
                           earth+fire (a quadrant plus its clockwise neighbour).
  element_wheel_pointer.png  3 x 40x40: rest, click-bump, lit; drawn for the TOP-RIGHT diagonal, aimed at the hub.
  element_icons.png        8 x 32x32, pivot (16, 16): pop + hold for fire, air, water, earth (upright badges).
  element_wheel_blur.png   4 x 192x192 (soft): the disc at speed, a quarter-turn's phases.
  element_wheel_form.png   6 x 192x192 (soft): the wheel drawing itself in runes (backward: the dissolve).
  element_wheel_shatter.png 6 x 208x208 (soft): the crash.

Layout (approved): quadrants on the diagonals - TL water, TR earth, BR fire, BL air (clockwise water, earth,
fire, air; opposites across the hub); spokes on the axes, hidden behind Liam's cross-shaped body.

LIGHT AND THE 90-DEGREE TURNS. Everything that turns with the disc and has volume - the rim, the studs, the
spokes, the hub - is lit SYMMETRICALLY (bevels that read the same at any angle), so neither the 11.25-degree
frames nor the code's quarter turns ever make the light jump. The icons are painted on the disc and turn with
it; they are drawn RADIALLY (each one's top points out along its diagonal), so whichever element stops under the
top-right pointer it reads the same way, tilted 45 degrees toward the pointer. The pointer does not turn with the
disc: it is lit from the upper left.
"""
import math
from ge_common import *
import le_rig as R
import le_parts as LPARTS
import elements_pal as E
import wheel as W1                 # the approved pass: palette, field tones, icon drawings, lift/drop tables

S = 192
CX = CY = 96.0
R_OUT, R_RIM, R_HUB = W1.R_OUT, W1.R_RIM, W1.R_HUB          # 90.5, 80.5, 18.5
SPOKE = W1.SPOKE
ICON_R = W1.ICON_R
SEG = W1.SEG                       # TL, TR, BR, BL
PALETTE = W1.PALETTE
FIELD, LIFT, DROP, BRIGHT, HALO = W1.FIELD, W1.LIFT, W1.DROP, W1.BRIGHT, W1.HALO
# each quadrant's diagonal, clockwise from screen-right (y down), and its icon's radial tilt (rotsprite: + = CCW)
DIAG = {0: -135.0, 1: -45.0, 2: 45.0, 3: 135.0}
TILT = {0: 45.0, 1: -45.0, 2: -135.0, 3: 135.0}
YY, XX = np.mgrid[0:S, 0:S]
SX = XX + 0.5 - CX
SY = YY + 0.5 - CY


def local(phi, sx=SX, sy=SY):
    """Screen offsets -> disc-local offsets for a disc turned phi degrees clockwise on screen."""
    a = math.radians(phi)
    c, s = math.cos(a), math.sin(a)
    return c * sx + s * sy, -s * sx + c * sy


def quad_of(x, y):
    return np.where(y < 0, np.where(x < 0, 0, 1), np.where(x >= 0, 2, 3))


def regions(lx, ly):
    rr = np.hypot(lx, ly)
    reg = np.zeros(lx.shape, int)
    disc = rr <= R_OUT
    reg[disc] = 1
    field = disc & (rr <= R_RIM)
    reg[field] = 10 + quad_of(lx, ly)[field]
    reg[field & ((np.abs(lx) <= SPOKE) | (np.abs(ly) <= SPOKE))] = 3
    reg[rr <= R_HUB] = 2
    return reg, rr


def keylines(reg):
    """One texel on every boundary (on the higher-numbered side), then thinned to pixel-perfect: a keyline texel
    that only closes an L between two others is given back to its region."""
    k = np.zeros(reg.shape, bool)
    P = np.pad(reg, 1, constant_values=0)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = P[1 + dy:S + 1 + dy, 1 + dx:S + 1 + dx]
        k |= (nb != reg) & (reg > nb)
    k &= reg > 0
    H, W_ = reg.shape

    def on(x, y):
        return 0 <= x < W_ and 0 <= y < H and k[y, x]
    changed = True
    while changed:
        changed = False
        for y, x in zip(*np.nonzero(k)):
            for (ax, ay), (bx, by) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                if on(x + ax, y + ay) and on(x + bx, y + by) and not on(x + ax + bx, y + ay + by)                         and not on(x - ax, y - ay) and not on(x - bx, y - by):
                    # an L corner between two inner regions only: the silhouette keeps its full line
                    nbrs = [reg[y + dy, x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                            if 0 <= x + dx < W_ and 0 <= y + dy < H]
                    if min(nbrs) == 0:
                        continue
                    k[y, x] = False
                    changed = True
                    break
    return k


def disc(phi, runes=True, icons=True, lit=(), field_only=False):
    """The disc turned phi degrees clockwise, as a char canvas. `lit`: elements stopped on (the rest dimmed)."""
    lx, ly = local(phi)
    reg, rr = regions(lx, ly)
    cv = np.full((S, S), '.', dtype='<U1')
    mid = (R_OUT + R_RIM) / 2
    half = (R_OUT - R_RIM) / 2
    # the rim: a symmetric bevel (dark lips, a lit crown just outward of its middle)
    t = (rr - mid) / half
    rim = np.where(np.abs(t) > 0.72, 'P', np.where((t > -0.05) & (t < 0.42), 'J', 'I'))
    cv[reg == 1] = rim[reg == 1]
    # the spokes: lit along their middles
    sp = np.where(((np.abs(lx) <= 0.6) & (np.abs(ly) > SPOKE)) | ((np.abs(ly) <= 0.6) & (np.abs(lx) > SPOKE)), 'J', 'I')
    sp = np.where(((np.abs(lx) <= 0.6) | (np.abs(ly) <= 0.6)), 'J', 'I')
    cv[reg == 3] = sp[reg == 3]
    # the hub: a dome lit at its crown, with its rune ring
    hub = np.where(rr < 6.5, 'J', np.where(rr < 14.5, 'I', 'P'))
    cv[reg == 2] = hub[reg == 2]
    ring = (reg == 2) & (np.abs(rr - 11.5) < 0.6)
    cv[ring] = 'h'
    cv[ring & (np.cos(np.arctan2(ly, lx) * 4) > 0.6)] = 'g'
    # the fields: shadow along every edge, a lit band inside the rim all the way round, the element's texture
    q = quad_of(lx, ly)
    for i, el in enumerate(SEG):
        m = reg == 10 + i
        tones = FIELD[el]
        d_edge = np.minimum.reduce([R_RIM - rr, rr - R_HUB, np.abs(lx) - SPOKE, np.abs(ly) - SPOKE])
        ch = np.where(d_edge < 3.0, tones[0], tones[1])
        ch = np.where((R_RIM - rr < 5.0) & (R_RIM - rr >= 3.0), tones[2], ch)
        texture(ch, el, m & (d_edge >= 3.0), tones, lx, ly, rr)
        cv[m] = ch[m]
    key = keylines(reg)
    cv[key] = '#'
    if runes:
        rim_runes(cv, reg, phi)
        studs(cv, reg, phi)
    if lit:
        for i, el in enumerate(SEG):
            m = (reg == 10 + i) & (cv != '#')
            table = LIFT[el] if el in lit else DROP[el]
            cv[m] = np.vectorize(lambda c: table.get(c, c))(cv[m])
        Kp = np.pad(key, 1)
        nearkey = (Kp[:-2, 1:-1] | Kp[2:, 1:-1] | Kp[1:-1, :-2] | Kp[1:-1, 2:]) & ~key
        for i, el in enumerate(SEG):
            if el in lit:
                cv[(reg == 10 + i) & nearkey] = BRIGHT[el]
    if icons:
        for i, el in enumerate(SEG):
            place_icon(cv, reg, el, i, phi, lit)
    if lit:
        for i, el in enumerate(SEG):
            if el not in lit:
                continue
            qm = (q == i) & (reg == 1)
            lift = {'g': 'H', 'h': 'g', 'P': 'I', 'I': 'J', 'J': 'B'}
            cv[qm] = np.vectorize(lambda c: lift.get(c, c))(cv[qm])
            ang = np.degrees(np.abs(((np.arctan2(ly, lx) - math.radians(DIAG[i])) + math.pi) % (2 * math.pi) - math.pi))
            for (r0, r1, c, dith) in ((R_OUT, R_OUT + 1.3, HALO[el], 0), (R_OUT + 1.3, R_OUT + 2.6, BRIGHT[el], 0),
                                      (R_OUT + 2.6, R_OUT + 4.2, HALO[el], 1)):
                band = (rr > r0) & (rr <= r1) & (q == i) & (ang < (44 if not dith else 38))
                if dith:
                    band &= (XX + YY) % 2 == 0
                cv[band & (cv == '.')] = c
    return cv, reg


def texture(ch, el, inner, tones, lx, ly, rr):
    """The element's pattern in its field's own tones, laid in DISC coordinates (it turns with the disc)."""
    if el == 'water':
        w = np.floor(ly + 2.2 * np.sin(lx / 5.0)).astype(int)
        ch[inner & (w % 9 == 0)] = tones[2]
        ch[inner & (w % 9 == 8) & (np.sin(lx / 5.0) < -0.6)] = tones[0]
    elif el == 'fire':
        w = np.floor(lx + 2.0 * np.sin(ly / 4.5)).astype(int)
        ch[inner & (w % 10 == 0)] = tones[2]
        ch[inner & (w % 10 == 0) & (np.sin(ly / 4.5) > 0.7)] = tones[3]
        ch[inner & (w % 10 == 5) & (np.sin(ly / 4.5 + 2.0) > 0.85)] = tones[0]
    elif el == 'earth':
        rnd = np.random.RandomState(4)
        pts = []
        for _ in range(9):
            a = rnd.uniform(-math.pi / 2, 0)
            r0 = rnd.uniform(26, 70)
            x, y = r0 * math.cos(a), r0 * math.sin(a)
            for k in range(rnd.randint(5, 11)):
                pts.append((x, y, 0))
                x += rnd.choice([-1, 0, 1])
                y += rnd.choice([0, 1])
        for _ in range(26):
            a = rnd.uniform(-math.pi / 2, 0)
            r0 = rnd.uniform(24, 78)
            pts.append((r0 * math.cos(a), r0 * math.sin(a), 2))
        fx, fy = np.floor(lx).astype(int), np.floor(ly).astype(int)
        for (x, y, t) in pts:
            m = inner & (fx == int(math.floor(x))) & (fy == int(math.floor(y)))
            ch[m] = tones[t]
    elif el == 'air':
        d = np.floor(lx - ly + 3 * np.sin((lx + ly) / 9.0)).astype(int)
        ch[inner & (d % 11 == 0)] = tones[2]
        ch[inner & (d % 11 == 1) & (np.sin((lx + ly) / 9.0) > 0.5)] = tones[3]


def rim_runes(cv, reg, phi):
    mid = (R_OUT + R_RIM) / 2
    for q in range(4):
        for k in range(7):
            if k == 3:
                continue
            a = math.radians(q * 90 + 11.25 * (k + 1) + phi)
            for rr in np.arange(mid - 2.0, mid + 2.01, 0.25):
                x, y = int(math.floor(CX + rr * math.cos(a))), int(math.floor(CY + rr * math.sin(a)))
                if reg[y, x] == 1 and cv[y, x] != '#':
                    cv[y, x] = 'g' if abs(rr - mid) < 1.1 else 'h'
        a = math.radians(q * 90 + 45 + phi)
        gx, gy = CX + mid * math.cos(a), CY + mid * math.sin(a)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = abs(dx) + abs(dy)
                x, y = int(math.floor(gx + dx)), int(math.floor(gy + dy))
                if reg[y, x] == 1 and d <= 3:
                    cv[y, x] = '#' if d == 3 else ('g' if d <= 1 else 'h')


def studs(cv, reg, phi):
    """The four pegs where the spokes meet the rim (the ticks: each one passing a pointer clicks it)."""
    mid = (R_OUT + R_RIM) / 2
    for a0 in (0, 90, 180, 270):
        a = math.radians(a0 + phi)
        sx, sy = CX + mid * math.cos(a), CY + mid * math.sin(a)
        d = np.hypot(XX + 0.5 - sx, YY + 0.5 - sy)
        sm = d <= 3.2
        cv[sm] = np.where(d < 1.2, 'B', np.where(d < 2.2, 'A', 'I'))[sm]
        cv[sm & (d > 2.3)] = '#'


def icon_canvas(el):
    return W1.ICONS[el]()


def place_icon(cv, reg, el, i, phi, lit):
    """The element's icon, radial: turned so its top points out along its quadrant's diagonal, then with the disc
    (RotSprite, his rig's own rotation)."""
    ic = icon_canvas(el)
    if lit and el not in lit:
        ic = np.vectorize(lambda c: DROP[el].get(c, c) if c not in '.#' else c)(ic)
    deg = TILT[i] - phi
    big = 80
    rot = LPARTS.rotsprite(ic, deg, pivot=(W1.IB / 2.0, W1.IB / 2.0), out_size=(big, big), out_pivot=(big / 2.0, big / 2.0))
    a = math.radians(DIAG[i] + phi)
    cx, cy = CX + ICON_R * math.cos(a), CY + ICON_R * math.sin(a)
    x0, y0 = int(round(cx - big / 2.0)), int(round(cy - big / 2.0))
    m = rot != '.'
    if lit and el in lit:
        P = np.pad(m, 2)
        dil1 = np.zeros_like(m)
        dil2 = np.zeros_like(m)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                sh = P[2 + dy:2 + dy + big, 2 + dx:2 + dx + big]
                if abs(dx) + abs(dy) <= 1:
                    dil1 |= sh
                if abs(dx) + abs(dy) <= 3:
                    dil2 |= sh
        for (mm, c) in ((dil2 & ~m, BRIGHT[el]), (dil1 & ~m, HALO[el])):
            for y, x in zip(*np.nonzero(mm)):
                X_, Y_ = x0 + x, y0 + y
                if 0 <= X_ < S and 0 <= Y_ < S and cv[Y_, X_] != '#' and reg[Y_, X_] >= 10:
                    if c == BRIGHT[el] and (X_ + Y_) % 2:
                        continue
                    cv[Y_, X_] = c
    for y, x in zip(*np.nonzero(m)):
        X_, Y_ = x0 + x, y0 + y
        if 0 <= X_ < S and 0 <= Y_ < S:
            cv[Y_, X_] = rot[y, x]


def to_rgba(cv, pal=PALETTE):
    out = np.zeros(cv.shape + (4,), np.uint8)
    for k, c in pal.items():
        out[cv == k] = c
    return out


# ------------------------------------------------------------------ the sheets
SUB = [11.25 * k for k in range(8)]
LIT = [('water',), ('earth',), ('fire',), ('air',), ('fire', 'air'), ('air', 'water'), ('water', 'earth'), ('earth', 'fire')]
LIT_NAMES = ['water', 'earth', 'fire', 'air', 'fire_air', 'air_water', 'water_earth', 'earth_fire']


def wheel_frames():
    return [to_rgba(disc(p)[0]) for p in SUB]


def lit_frames():
    return [to_rgba(disc(0.0, lit=l)[0]) for l in LIT]


# ------------------------------------------------------------------ the pointer (top-right, aimed at the hub)
PW = 40
PTR_TL = (150, 2)                  # its frame's top-left, in wheel texels
PTR_PIVOT = (CX - PTR_TL[0], CY - PTR_TL[1])     # the wheel's centre corner in pointer texels: (-54, 94)


def pointer_frame(kind):
    """A bone talon set in an iron mount, its point on the rim's outer edge at the top-right diagonal, aimed at the
    hub; a rune gem in the mount. bump: knocked a texel and a half outward and cocked (a peg passed); lit: the gem
    and the talon's edge burn."""
    cv = np.full((PW, PW), '.', dtype='<U1')
    ys, xs = np.mgrid[0:PW, 0:PW]
    wx = xs + 0.5 + PTR_TL[0] - CX
    wy = ys + 0.5 + PTR_TL[1] - CY
    # u: distance from the hub along the diagonal (out), v: across it
    d = np.array([math.cos(math.radians(-45)), math.sin(math.radians(-45))])
    u = wx * d[0] + wy * d[1]
    v = -wx * d[1] + wy * d[0]
    if kind == 'bump':
        u = u - 1.5
        v = v - 0.12 * (u - 100)
    tip_u = R_OUT - 2.0
    # the talon: from the tip (tip_u) out to its root (tip_u + 19), widening to 5.5, curved slightly
    tl = (u - tip_u) / 19.0
    curve = 1.2 * tl * tl
    talon = (tl >= 0) & (tl <= 1.0) & (np.abs(v - curve) <= 0.6 + 4.9 * tl)
    # the mount: an iron collar round the talon's root, then a rounded cap
    mount = (u > tip_u + 16) & (u < tip_u + 26) & (np.abs(v - 1.2) <= 7.0) & \
        ((u - (tip_u + 21)) ** 2 / 25.0 + (v - 1.2) ** 2 / 49.0 <= 1.15)
    gem = ((u - (tip_u + 21.5)) ** 2 + (v - 1.2) ** 2) <= 4.4
    L = np.array(R.LIGHT[:2]) / np.linalg.norm(R.LIGHT[:2])
    # talon shading: lit on the side facing the upper left (screen), bone ramp
    nx = -d[1] * np.sign(v - curve)
    ny = d[0] * np.sign(v - curve)
    facing = nx * L[0] + ny * L[1]
    across = np.abs(v - curve) / (0.6 + 4.9 * np.clip(tl, 0, 1))
    tal = np.where(across < 0.35, 'A', np.where(facing > 0, 'B', 'n'))
    tal = np.where((tl < 0.25) & (across < 0.6), 'B', tal)
    mt = np.where((v - 1.2) * (-d[1] * L[0] + d[0] * L[1]) > 1.5, 'J', np.where((v - 1.2) * (-d[1] * L[0] + d[0] * L[1]) < -2.5, 'P', 'I'))
    ch = np.full((PW, PW), '.', dtype='<U1')
    ch[talon] = tal[talon]
    ch[mount] = mt[mount]
    ch[gem] = 'h'
    ch[gem & (((u - (tip_u + 21.5)) ** 2 + (v - 0.4) ** 2) <= 1.3)] = 'g'
    if kind == 'lit':
        ch[gem] = 'g'
        ch[gem & (((u - (tip_u + 21.5)) ** 2 + (v - 0.4) ** 2) <= 1.3)] = 'H'
    m = ch != '.'
    R.paint_part(cv, m, ch)
    if kind == 'lit':
        # the talon's lit edge burns rune-blue, and a glow sits round the gem
        edge = talon & (tal == 'B')
        cv[edge & (cv != '#')] = 'g'
        ring = (~m) & (np.hypot(u - (tip_u + 21.5), v - 1.2) <= 9.5) & ((xs + ys) % 2 == 0) & \
            ((u - (tip_u + 21)) ** 2 / 25.0 + (v - 1.2) ** 2 / 49.0 > 1.15)
        cv[ring] = 'h'
    tip = None
    for y_, x_ in zip(*np.nonzero(m)):
        if tip is None or u[y_, x_] < u[tip[1], tip[0]]:
            tip = (int(x_), int(y_))
    return cv, tip


def pointer_frames():
    out, tips = [], []
    for k in ('rest', 'bump', 'lit'):
        cv, tip = pointer_frame(k)
        out.append(to_rgba(cv))
        tips.append(tip)
    return out, tips


# ------------------------------------------------------------------ the badge icons (upright, 32x32)
IW = 32


def badge(el, pop):
    K0 = W1.K
    W1.IB, W1.K = 28, 28 / 40.0
    try:
        ic = small_air() if el == 'air' else W1.ICONS[el]()
    finally:
        W1.IB, W1.K = 54, K0
    if pop:
        ic = np.vectorize(lambda c: LIFT[el].get(c, c) if c not in '.#' else c)(ic)
    cv = np.full((IW, IW), '.', dtype='<U1')
    R.composite(cv, ic, 2, 2)
    m = cv != '.'
    P = np.pad(m, 2)
    d1 = np.zeros_like(m)
    d2 = np.zeros_like(m)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            sh = P[2 + dy:2 + dy + IW, 2 + dx:2 + dx + IW]
            if abs(dx) + abs(dy) <= 1:
                d1 |= sh
            if abs(dx) + abs(dy) <= 2:
                d2 |= sh
    cv[d1 & ~m] = HALO[el] if not pop else BRIGHT[el]
    if pop:
        cv[d2 & ~d1 & ((XX[:IW, :IW] + YY[:IW, :IW]) % 2 == 0)] = HALO[el]
    return cv


def small_air():
    """The air glyph at badge size: one spiral and a quarter, a single stroke streaming off into one gust."""
    IB, K = W1.IB, W1.K
    cv = R.blank(IB, IB)
    pts = []
    for i in range(160):
        t = i / 159
        a = 1.25 * 2 * math.pi * t + 3.6
        r = 1.5 + 12.0 * t
        pts.append((19 + r * math.cos(a), 18 + r * math.sin(a)))
    end = pts[-1]
    tail = [(end[0] + k * 1.4, end[1] + k * 0.15) for k in range(1, 9)]
    Xi, Yi = R.centres(IB, IB)
    v = (-(Xi / K - 19) * 0.55 - (Yi / K - 18) * 0.75) / 15.0
    ch = R.quant(v, 'vwW', [-0.3, 0.25])
    R.paint_part(cv, R.polyline_mask([(x * K, y * K) for x, y in pts + tail], 2.1, IB, IB), ch)
    return cv


def icon_frames():
    out = []
    for el in ('fire', 'air', 'water', 'earth'):
        out.append(to_rgba(badge(el, True)))
        out.append(to_rgba(badge(el, False)))
    return out


# ------------------------------------------------------------------ soft: blur, form, shatter
def blur_frames():
    out = []
    for k in range(4):
        cv, reg = disc(22.5 * k, runes=True, icons=True)
        out.append(to_rgba(swirl(cv, reg, 22.5 * k)))
    return out


def swirl(cv, reg, phi):
    """The approved spin smear, laid in disc coordinates so its four phases tile a quarter turn."""
    out = cv.copy()
    lx, ly = local(phi)
    rr = np.hypot(lx, ly)
    inside = (rr <= R_RIM) & (rr > R_HUB)
    th = np.arctan2(ly, lx)
    sw = th + 0.010 * np.clip(rr - R_HUB, 0, None) ** 1.2
    q = quad_of(np.cos(sw), np.sin(sw))
    for i, el in enumerate(SEG):
        tones = FIELD[el]
        m = inside & (q == i)
        frac = (sw % (math.pi / 2)) / (math.pi / 2)
        ch = np.where(frac > 0.72, tones[2], np.where(frac < 0.12, tones[0], tones[1]))
        out[m] = ch[m]
    out[inside & (np.abs(sw % (math.pi / 2)) < 0.05)] = '#'
    stripe = {'water': '34W', 'earth': 'mor', 'fire': 'efW', 'air': 'wWv'}
    for i, el in enumerate(SEG):
        a0 = math.radians(DIAG[i])
        for dr, c in ((-9, stripe[el][0]), (-4, stripe[el][1]), (0, stripe[el][2]), (4, stripe[el][1]), (8, stripe[el][0])):
            span = 70 - abs(dr) * 3
            for t in range(int(span * 3)):
                a = a0 - math.radians(t / 3.0) + math.radians(phi)
                r = ICON_R + dr
                for r2 in (r, r + 0.6):
                    x, y = int(math.floor(CX + r2 * math.cos(a))), int(math.floor(CY + r2 * math.sin(a)))
                    if inside[y, x]:
                        out[y, x] = c
    for r0, a0, span, c in ((27, 20, 70, 'W'), (39, 160, 80, 'w'), (67, 260, 70, 'W'), (73, 60, 50, 'w'),
                            (33, 210, 50, 'w'), (75, 120, 55, 'W'), (24, 300, 45, 'w')):
        for k in range(int(span * 2)):
            a = math.radians(a0 + k * 0.5 + phi)
            x, y = int(math.floor(CX + r0 * math.cos(a))), int(math.floor(CY + r0 * math.sin(a)))
            if inside[y, x]:
                out[y, x] = c
    return out


def form_frames():
    """The wheel drawing itself in his rune blue: a rune ring sparks round, closes, the iron and spokes set, the
    four fields pour in dim, the icons strike, and it stands at rest."""
    rest, reg = disc(0.0)
    lx, ly = local(0.0)
    rr = np.hypot(lx, ly)
    th = (np.degrees(np.arctan2(ly, lx)) + 360 + 90) % 360        # 0 at 12 o'clock, clockwise
    out = []
    ring = (rr > R_OUT - 1.5) & (rr <= R_OUT)
    for k in range(6):
        cv = np.full((S, S), '.', dtype='<U1')
        if k == 0:
            m = ring & (th < 140) & ((XX + YY) % 3 != 0)
            cv[m] = 'g'
            cv[ring & (th < 140) & (np.abs(th - 135) < 6)] = 'H'
        elif k == 1:
            cv[ring] = 'g'
            cv[ring & (np.abs(th - 300) < 8)] = 'H'
            spokes = ((np.abs(lx) <= 0.6) | (np.abs(ly) <= 0.6)) & (rr < R_OUT - 1) & ((XX + YY) % 2 == 0)
            cv[spokes] = 'h'
        elif k == 2:
            frame_ = (reg == 1) | (reg == 2) | (reg == 3)
            cv[frame_] = rest[frame_]
            cv[ring] = 'g'
        elif k == 3:
            frame_ = (reg == 1) | (reg == 2) | (reg == 3)
            cv[frame_] = rest[frame_]
            for i, el in enumerate(SEG):
                m = reg == 10 + i
                cv[m & ((XX + YY) % 2 == 0)] = FIELD[el][0]
                cv[m & ((XX + YY) % 2 == 1)] = FIELD[el][1]
            key = keylines(reg)
            cv[key] = '#'
        elif k == 4:
            cv = rest.copy()
            for i, el in enumerate(SEG):
                m = (reg == 10 + i) & (cv != '#')
                cv[m] = np.vectorize(lambda c: DROP[el].get(c, c))(cv[m])
            cv[ring & (cv == 'P')] = 'g'
        else:
            cv = rest.copy()
        out.append(to_rgba(cv))
    return out


SH = 208


def shatter_frames():
    """The crash: cracks race across the disc, it splits along its spokes into four quarters that fly apart and
    break up into dimming shards, then only sparks. 208x208, centre corner (104, 104)."""
    rest, reg = disc(0.0)
    base = to_rgba(rest)
    out = []
    rnd = np.random.RandomState(9)
    cracks = []
    for q in range(4):
        a = math.radians(DIAG[q])
        for j in range(3):
            pts = [(0, 0)]
            ang = a + rnd.uniform(-0.5, 0.5)
            r = 0
            while r < R_OUT:
                r += rnd.uniform(5, 9)
                ang += rnd.uniform(-0.25, 0.25)
                pts.append((r * math.cos(ang), r * math.sin(ang)))
            cracks.append((q, pts))
    lx, ly = SX, SY
    qmap = quad_of(lx, ly)
    for k in range(6):
        img = np.zeros((SH, SH, 4), np.uint8)
        dist = (0, 0, 3, 8, 14, 20)[k]
        for q in range(4):
            piece = base.copy()
            piece[(qmap != q)] = 0
            if k >= 1:
                for (cq, pts) in cracks:
                    if cq != q:
                        continue
                    upto = len(pts) if k >= 1 else 2
                    for (x0, y0), (x1, y1) in zip(pts[:upto], pts[1:upto]):
                        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
                        for t in range(n + 1):
                            x = int(math.floor(CX + x0 + (x1 - x0) * t / n))
                            y = int(math.floor(CY + y0 + (y1 - y0) * t / n))
                            if 0 <= x < S and 0 <= y < S and piece[y, x, 3]:
                                piece[y, x] = (0, 0, 0, 255) if k < 2 else PUP['G1']
            if k >= 4:
                keep = (np.random.RandomState(q + k).rand(S, S) < (0.55 if k == 4 else 0.2))
                piece[~keep] = 0
            a = math.radians(DIAG[q])
            ox = int(round(8 + dist * math.cos(a)))
            oy = int(round(8 + dist * math.sin(a)))
            m = piece[:, :, 3] > 0
            ys, xs = np.nonzero(m)
            ys2, xs2 = ys + oy, xs + ox
            ok = (ys2 >= 0) & (ys2 < SH) & (xs2 >= 0) & (xs2 < SH)
            img[ys2[ok], xs2[ok]] = piece[ys[ok], xs[ok]]
        if k == 0:
            # the first crack: a white-hot split from the hub, before it breaks
            for (cq, pts) in cracks[::3]:
                for (x0, y0), (x1, y1) in zip(pts[:3], pts[1:3]):
                    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
                    for t in range(n + 1):
                        x = int(math.floor(8 + CX + x0 + (x1 - x0) * t / n))
                        y = int(math.floor(8 + CY + y0 + (y1 - y0) * t / n))
                        if img[y, x, 3]:
                            img[y, x] = HOT
        if k == 5:
            img[:] = 0
            for i in range(26):
                a = rnd.uniform(0, 2 * math.pi)
                r = rnd.uniform(60, 100)
                x, y = int(104 + r * math.cos(a)), int(104 + r * math.sin(a))
                img[y, x] = (PUP['G1'], HOT, E.FIRE['y'], E.WATER['L'], E.EARTH['g'], E.AIR['p'])[i % 6]
        out.append(img)
    return out
