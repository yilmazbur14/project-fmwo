"""Main-menu background 'The Ladder' (six tiers). 640x360, DB32 only, built as separate layers.

Night. A tower of stacked boxing-ring tiers; each tier is one rank of the server, lit in its role
colour, with that rank's member(s) standing on it as rim-lit silhouettes. A red-carpet stair climbs
the middle to a chained, padlocked INVITE glowing at the top. The newcomer stands at the foot of the
carpet, back to camera. A dim crowd of server members lines the horizon. Left ~270px stays calm
for the logo / NEW GAME / VOLUME UI.
"""
import math, os, random
from lib import *
import invite
import player2


def load_masks(path):
    """Read the [name] + ASCII-grid silhouette file written by design.py."""
    ms, cur = {}, None
    for line in open(path):
        line = line.rstrip()
        if line.startswith('['):
            cur = line[1:-1]
            ms[cur] = []
        elif line.strip() and cur:
            ms[cur].append(line)
    for n, m in ms.items():
        assert len(set(len(r) for r in m)) == 1, n
    return ms


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

W, H = 640, 360
CX = 440
BASE_Y = 316                 # bottom row of tier 1's apron
GLOW = (CX, 34)
CARD_X, CARD_Y = CX - 38, 8  # invite canvas origin (card rect at +3..+72, +4..+44)

# role colour ramps (hi, base, lo) per tier, bottom (1) to top (6)
ROLE = {
    1: (LG, GR, OG),        # green   - Eric
    2: (WH2, CY, BL),       # cyan    - Computah & Greyson
    3: (SK, OR, BR),        # orange  - Carter & Josh
    4: (WH2, MG, PU),       # pink    - Mason
    5: (SK, PK, RD),        # red     - Liam & Bixby
    6: (WH, YL, TN),        # gold    - Jordan (final boss)
}


def _tiers():
    spec = [(32, 7, 150), (30, 6, 126), (28, 6, 104), (26, 5, 84), (24, 5, 66), (22, 4, 50)]   # (face, strip, half-width)
    out, fb = [], BASE_Y
    for face, strip, hw in spec:
        ft = fb - face + 1
        st = ft - strip
        out.append((st, ft, fb, hw))
        fb = st - 1
    return out


TIERS = _tiers()             # (strip_top, face_top, face_bottom, half_width)
N_TIERS = len(TIERS)
SUMMIT = TIERS[-1][0]


def stair_hw(y):
    return int(round(11 + (y - SUMMIT) * (20 - 11) / float(BASE_Y - SUMMIT)))


def feet_y(k):
    st, ft, fb, hw = TIERS[k - 1]
    return st + (ft - st) // 2


# ------------------------------------------------------------------ sky
BIG_STARS = [(38, 140), (230, 18), (606, 150), (126, 250), (300, 96), (620, 38), (22, 46), (186, 176)]


def layer_sky(stars=True):
    c = Canvas(W, H)
    rnd = random.Random(11)
    gx, gy = GLOW
    for y in range(H):
        for x in range(W):
            col = N0
            t = (y - 170) / 150.0
            if t > 0 and dith(x, y, min(1.0, t) * 0.85):
                col = P0
            dx, dy = x - gx, (y - gy) * 1.25
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            ray = max(0.0, math.cos(ang * 4 + 0.4)) ** 8
            outer = max(0.0, 1.0 - r / 112.0)
            v = outer ** 1.8 * 0.9 + ray * outer ** 1.5 * 0.3
            if v > 0 and dith(x, y, min(1.0, v)):
                col = IN
            inner = max(0.0, 1.0 - r / 58.0)
            if inner > 0.05 and dith(x, y, min(1.0, inner * 1.3)):
                col = RB if inner > 0.35 else IN
            core = max(0.0, 1.0 - r / 44.0)
            if core > 0.25 and dith(x, y, min(1.0, (core - 0.25) * 1.6)):
                col = SB
            c.set(x, y, col)
    if not stars:
        return c
    for i in range(200):
        x, y = rnd.randrange(W), rnd.randrange(0, 270)
        if math.hypot(x - gx, (y - gy) * 1.25) < 105:
            continue
        v = rnd.random()
        col = G5 if v < 0.55 else WH2 if v < 0.85 else WH
        if y > 190:
            col = G4 if v < 0.7 else G5
        c.set(x, y, col)
    for (x, y) in BIG_STARS:
        c.set(x, y, WH)
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(x + ddx, y + ddy, G5)
    return c


# ------------------------------------------------------------------ drifting server-icon lanterns
SKY_LANTERNS = [  # x, y, size (5 or 7), tier colour -- kept clear of the UI column (x < 250)
    (272, 150, 7, 4), (306, 62, 5, 2), (612, 120, 7, 5), (598, 238, 5, 6), (288, 238, 5, 1),
]
ICON7 = ['..KKK..', '.KhbbK.', 'KhbbbbK', 'KbbbblK', 'KbbbllK', '.KbllK.', '..KKK..']
ICON5 = ['.KKK.', 'KhbbK', 'KbbbK', 'KbblK', '.KKK.']


def layer_lanterns(bob=None):
    c = Canvas(W, H)
    for i, (x, y, s, k) in enumerate(SKY_LANTERNS):
        if bob:
            y += bob[i]
        hi, base, lo = ROLE[k]
        R = s + 3.5
        for yy in range(int(y - R) - 1, int(y + R) + 2):
            for xx in range(int(x - R) - 1, int(x + R) + 2):
                d = math.hypot(xx - x, yy - y)
                if d < R and dith(xx, yy, (1 - d / R) ** 1.2 * 0.85):
                    c.set(xx, yy, IN)
        icon = ICON7 if s == 7 else ICON5
        c.grid(x - s // 2, y - s // 2, icon, {'K': K, 'h': hi, 'b': base, 'l': lo}, skip='.')
    return c


# ------------------------------------------------------------------ distant crowd on the horizon
CROWD_PNG = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Environment/crowd_v2.png"
CROWD_FW, CROWD_FH = 640, 40
CROWD_TOP = BASE_Y - CROWD_FH + 1
# screen x range -> source x offset. The tower hides x 290..590, so the right-hand sliver borrows the
# stretch of the strip that holds the blurple speech-bubble sign.
CROWD_SLICES = [((0, 289), 0), ((590, 639), 430 - 590)]
CROWD_NIGHT = {}          # optional colour remap for the night scene (filled below if enabled)
NIGHT_DIM = os.environ.get('CROWD_NIGHT', '1') == '1'
if NIGHT_DIM:
    CROWD_NIGHT = {'eec39a': 'd9a066', 'd9a066': '8f563b', '8f563b': '663931', '663931': '45283c',
                   'ac3232': '663931', 'd95763': 'ac3232', '9badb7': '847e87', 'cbdbfc': '9badb7',
                   '306082': '3f3f74', '4b692f': '323c39', '37946e': '4b692f', '76428a': '45283c',
                   'df7126': '8f563b', 'd77bba': '76428a', '5fcde4': '306082', '8a6f30': '524b24'}
_crowd_cache = {}


def crowd_frame(i):
    if i not in _crowd_cache:
        w, h, px = read_png(CROWD_PNG)
        rev = {v: k for k, v in DB32.items()}
        _crowd_cache[i] = [[(None if px[y][i * CROWD_FW + x][3] == 0 else rev[px[y][i * CROWD_FW + x][:3]])
                            for x in range(CROWD_FW)] for y in range(CROWD_FH)]
    return _crowd_cache[i]


def layer_crowd(frame=0):
    """The approved arena crowd (crowd_v2.png, Punch-Out style) lining the horizon behind the tower."""
    c = Canvas(W, H)
    fr = crowd_frame(frame)
    for (x0, x1), off in CROWD_SLICES:
        for x in range(x0, x1 + 1):
            sx = (x + off) % CROWD_FW
            for y in range(CROWD_FH):
                col = fr[y][sx]
                if col is not None:
                    c.set(x, CROWD_TOP + y, CROWD_NIGHT.get(col, col))
    return c


# ------------------------------------------------------------------ tower
def draw_tier(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    hi, base, lo = ROLE[k]
    x0, x1 = CX - hw, CX + hw
    for y in range(st, ft):
        for x in range(x0, x1 + 1):
            col = OG
            if y == st:
                col = G1
            elif y == ft - 1:
                col = TE
            elif y == st + 1 and dith(x, y, 0.5):
                col = G1
            c.set(x, y, col)
    for y in range(ft, fb + 1):
        yy = y - ft
        for x in range(x0, x1 + 1):
            col = N0
            if yy == 0:
                col = TN
            elif yy == 1:
                col = GO
            elif yy == 2:
                col = K
            elif yy == 3:
                col = base
            elif yy == 4:
                col = lo
            elif yy == 5:
                col = K
            elif yy < 10 and dith(x, y, 0.5 - (yy - 6) * 0.14):
                col = IN
            if y == fb:
                col = K
            c.set(x, y, col)
    for y in range(st, fb + 1):
        c.set(x0, y, K)
        c.set(x1, y, K)
    c.hline(x0, x1, st - 1, K)
    # role pennants hanging off the apron at both ends
    ph = min(16, fb - ft - 8)
    for side in (-1, 1):
        bx = CX + side * (hw - 16) - 4
        for j in range(ph + 1):
            for i in range(9):
                notch = j >= ph - 3 and abs(i - 4) <= (j - (ph - 3))
                if notch:
                    continue
                edge = i in (0, 8) or j == ph or (j >= ph - 3 and abs(i - 4) == (j - (ph - 3)) + 1)
                col = K if edge else (hi if i == 1 else lo if i == 7 else base)
                c.set(bx + i, ft + 3 + j, col)
        c.hline(bx - 1, bx + 9, ft + 2, K)
        c.hline(bx, bx + 8, ft + 3, K)
        # tier number (Arena #1 at the bottom .. #6 at the top)
        g = F35[str(k)]
        ex, ey = bx + 3, ft + 3 + (ph - 3) // 2 - 2
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == '#':
                    c.set(ex + i, ey + j, K if k in (2, N_TIERS) else lo)


LANTERN = ['..KKK..', '.KhbbK.', 'KhbbbbK', 'KbbbblK', 'KbbbllK', '.KbllK.', '..KKK..']


def draw_post(c, px, st, k):
    hi, base, lo = ROLE[k]
    top = st - 14
    for y in range(top, st + 2):
        c.set(px - 1, y, K)
        c.set(px + 2, y, K)
        c.set(px, y, TN)
        c.set(px + 1, y, GO)
    ly = top - 4
    for yy in range(ly - 10, ly + 11):
        for xx in range(px - 10, px + 12):
            d = math.hypot(xx - (px + 0.5), yy - ly)
            if d < 10.5 and c.get(xx, yy) is None and dith(xx, yy, (1 - d / 10.5) ** 1.4 * 0.9):
                c.set(xx, yy, IN)
    c.grid(px - 2, ly - 3, LANTERN, {'K': K, 'h': hi, 'b': base, 'l': lo}, skip='.')


def draw_ropes(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    pl, pr = CX - hw + 4, CX + hw - 5
    gap = stair_hw(st) + 3
    for ry in (st - 5, st - 10):
        for x in range(pl + 2, pr):
            if abs(x - CX) <= gap:
                continue
            c.set(x, ry, WH2 if abs(x - CX) < hw * 0.55 else G5)
    draw_post(c, pl, st, k)
    draw_post(c, pr, st, k)


def draw_stairs(c):
    for y in range(SUMMIT, BASE_Y + 1):
        hw = stair_hw(y)
        ph = (y - SUMMIT) % 4
        t = (y - SUMMIT) / float(BASE_Y - SUMMIT)          # 0 at the summit (lit) .. 1 at the base
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            if e == hw:
                col = K
            elif e == hw - 1:
                col = (GO if ph else TN) if t < 0.6 else (OL if ph else GO)
            elif e == hw - 2:
                col = (TN if ph != 3 else GO) if t < 0.6 else (GO if ph != 3 else OL)
            else:
                nose = PK if t < 0.45 or (t < 0.7 and dith(x, y, 1.6 - t * 2.2)) else RD
                body = RD if t < 0.55 or dith(x, y, 1.9 - t * 2.0) else BR
                riser = BR if t < 0.6 or dith(x, y, 2.2 - t * 2.4) else P0
                col = [nose, body, body, riser][ph]
                if ph == 0 and e >= hw - 4:
                    col = body
                if ph in (1, 2) and e >= hw - 4:
                    col = riser
            c.set(x, y, col)
        c.set(CX - hw - 1, y, K)
        c.set(CX + hw + 1, y, K)


def draw_floor(c):
    for y in range(BASE_Y + 1, H):
        for x in range(W):
            c.set(x, y, N0)
    VPY = 180
    for xb in range(-1400, 2400, 80):
        for y in range(BASE_Y + 1, H):
            t = (y - VPY) / float(BASE_Y + 1 - VPY)
            x = int(round(CX + (xb - CX) * t))
            c.set(x, y, K)
    for y in [BASE_Y + 1, 322, 330, 341, 356]:
        c.hline(0, W - 1, y, K)
    for y in range(BASE_Y + 2, H):
        for x in range(W):
            d = math.hypot((x - CX) / 220.0, (y - BASE_Y) / 44.0)
            if d < 1 and c.get(x, y) == N0 and dith(x, y, (1 - d) * 0.75):
                c.set(x, y, P0)


def draw_carpet_runout(c):
    for y in range(BASE_Y + 1, H):
        t = (y - BASE_Y) / float(H - BASE_Y)
        hw = int(round(20 + 30 * t))
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            col = BR
            if e >= hw:
                col = K
            elif e >= hw - 2:
                col = GO if e == hw - 1 else OL
            elif dith(x, y, 0.55 - t * 0.35):
                col = RD
            c.set(x, y, col)


def layer_tower():
    c = Canvas(W, H)
    for k in range(N_TIERS, 0, -1):
        draw_tier(c, k)
    draw_stairs(c)
    for k in range(1, N_TIERS + 1):
        draw_ropes(c, k)
    return c


def layer_floor():
    c = Canvas(W, H)
    draw_floor(c)
    draw_carpet_runout(c)
    return c


# ------------------------------------------------------------------ members
MASKS = load_masks(os.path.join(HERE, 'masks_clean.txt'))
PLACE = [  # name, tier, x of anchor column, anchor column
    ('eric', 1, CX, 23),
    ('computah', 2, CX - 44, 7),
    ('greyson', 2, CX + 44, 11),
    ('carter', 3, CX - 44, 11),
    ('josh', 3, CX + 44, 14),
    ('mason', 4, CX, 14),
    ('liam', 5, CX - 38, 14),
    ('bixby', 5, CX + 38, 14),
    ('jordan', 6, CX, 8),
]


def put_member(c, rows, ax, feet, k, anchor):
    h, w = len(rows), len(rows[0])
    x0, y0 = ax - anchor, feet - h + 1
    hi, base, lo = ROLE[k]
    S = lambda x, y: 0 <= y < h and 0 <= x < w and rows[y][x] != '.'
    toward = 0 if abs(ax - CX) < 6 else (1 if ax < CX else -1)   # side facing the light column
    for y in range(h):
        for x in range(w):
            ch = rows[y][x]
            if ch == '.':
                continue
            run_l = 0
            while S(x - run_l - 1, y):
                run_l += 1
            run_r = 0
            while S(x + run_r + 1, y):
                run_r += 1
            width = run_l + run_r + 1
            col = K
            if ch == '+':
                col = N0
            elif ch == 'o':
                col = WH2
            elif ch == 'R':
                col = PK
            elif ch == 'y':
                col = YL
            elif not S(x, y - 1):
                col = hi
            elif not S(x - 1, y) or not S(x + 1, y):
                left_edge = not S(x - 1, y)
                if toward == 1:
                    faces = not left_edge
                elif toward == -1:
                    faces = left_edge
                elif width <= 2:
                    faces = left_edge if x < anchor else not left_edge
                else:
                    faces = True
                if faces and not (width <= 2 and toward == 0 and x == anchor):
                    col = base
            c.set(x0 + x, y0 + y, col)


def layer_members():
    c = Canvas(W, H)
    for name, k, ax, anchor in PLACE:
        put_member(c, MASKS[name], ax, feet_y(k), k, anchor)
    return c


# ------------------------------------------------------------------ invite + player
def layer_invite():
    c = Canvas(W, H)
    c.blit(invite.card(), CARD_X, CARD_Y)
    return c


def layer_player():
    c = Canvas(W, H)
    rows = player2.rows()
    c.grid(CX - 16, H - len(rows) - 2, rows, player2.CMAP, skip='.')
    return c


LAYERS = [('sky', layer_sky), ('lanterns', layer_lanterns), ('crowd', layer_crowd), ('floor', layer_floor), ('tower', layer_tower),
          ('members', layer_members), ('invite', layer_invite), ('player', layer_player)]


def build():
    out = Canvas(W, H)
    parts = []
    for name, fn in LAYERS:
        lc = fn()
        parts.append((name, lc))
        out.blit(lc, 0, 0)
    return out, parts


if __name__ == '__main__':
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v2'
    out, parts = build()
    p = out.save(os.path.join(OUT, 'bg_%s.png' % tag))
    crop_zoom(p, os.path.join(OUT, 'bg_%s_2x.png' % tag), 0, 0, W, H, 2)
    crop_zoom(p, os.path.join(OUT, 'bg_%s_top_4x.png' % tag), CX - 132, 0, 264, 180, 4)
    crop_zoom(p, os.path.join(OUT, 'bg_%s_bot_3x.png' % tag), CX - 185, 170, 370, 190, 3)
    print('tiers', TIERS)
