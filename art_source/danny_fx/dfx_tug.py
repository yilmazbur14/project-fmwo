"""The sumo tug-of-war meter (UI, Assets/UI/), in the house brass-bar style of qte_meter3 (DB32, a black keyline,
alpha 0/255), each part with a pre-scaled _3x copy for the HUD like the other meters:
  tug_meter_frame        160x24   the brass bar (x 22-137, y 4-19) with its dark channel, a round end plate
                                  each side (the player's red heart on the left, Danny's striped beanie on
                                  the right) and brass notches on the rails over and under the centre line
  tug_meter_fill_player  102x6    the player's side: his hearts' reds (#FF7A8A #D95763 #AC3232 #6E1F22)
  tug_meter_fill_danny   102x6    Danny's side: his beanie's knit ribs (#F0F5FF #CBDBFC #97ABEF #5B6EE1)
  tug_meter_centre       3x8      the centre line, drawn over the fills: a black line capped in brass
  tug_meter_marker       4 x 9x16 the struggle point where the two sides meet, flickering white-hot and gold
Layout (1x texels, x3 for the _3x copies): the channel is at (29, 9), 102x6. Reveal the player's fill from
its left edge to the marker and Danny's from the marker to its right edge (both drawn at (29, 9), cropped by
region, never stretched). The centre line goes at (79, 8) (the channel's middle, column 80); the marker's
pivot is its centre (4, 8), put on (the marker's x, 12). Player on the left: if the player stands on Danny's
right, flip the whole meter.
"""
import dfx_pal as pal

K = '000000'; N0 = '222034'; P0 = '45283C'; BR2 = '8F563B'
TN = 'D9A066'; SK = 'EEC39A'; YL = 'FBF236'; GO = '8A6F30'; OL = '524B24'
IN = '3F3F74'; WH = 'FFFFFF'
HEART = ('FF7A8A', 'D95763', 'AC3232', '6E1F22')
BEANIE = ('F0F5FF', 'CBDBFC', '97ABEF', '5B6EE1', '3F3F74')

W, H = 160, 24
BAR_X, BAR_Y, BAR_W, BAR_H = 22, 4, 116, 16
CH_X, CH_Y, CH_W, CH_H = 29, 9, 102, 6
CENTRE_X = CH_X + CH_W // 2 - 1                 # column 79 | 80: the line sits on column 80
PARTS = ['tug_meter_frame', 'tug_meter_fill_player', 'tug_meter_fill_danny', 'tug_meter_centre', 'tug_meter_marker']


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[None] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def image(self):
        from PIL import Image
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        px = im.load()
        for y in range(self.h):
            for x in range(self.w):
                c = self.p[y][x]
                if c:
                    px[x, y] = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        return im


def bar(c, x0, y0, w, h=16):
    """The qte meter's brass bar at any width: keyline, a lit top rail, a shaded bottom rail, end caps, the
    dark channel inside (margins L8 T6 R8 B6 as qte_meter_frame)."""
    MT, MB, ML, MR = 6, 6, 8, 8
    top = [K, YL, TN, GO, K, K]
    bot = [IN, K, TN, GO, OL, K]
    left = [K, YL, SK, TN, TN, GO, K, K]
    right = [IN, K, SK, TN, TN, GO, OL, K]
    for y in range(h):
        for x in range(w):
            col = N0
            if y < MT:
                col = top[y]
            elif y >= h - MB:
                col = bot[y - (h - MB)]
            if x < ML and MT <= y < h - MB:
                col = left[x]
            elif x >= w - MR and MT <= y < h - MB:
                col = right[x - (w - MR)]
            c.set(x0 + x, y0 + y, col)
    for x in range(6, w - 6):
        c.set(x0 + x, y0 + 4, K)
        c.set(x0 + x, y0 + 11, K)
    for y in range(4, 12):
        c.set(x0 + 6, y0 + y, K)
        c.set(x0 + w - 7, y0 + y, K)
    for (x, y) in [(0, 0), (1, 0), (0, 1), (w - 1, 0), (w - 2, 0), (w - 1, 1), (0, h - 1), (1, h - 1), (0, h - 2),
                   (w - 1, h - 1), (w - 2, h - 1), (w - 1, h - 2)]:
        c.set(x0 + x, y0 + y, None)
    for (x, y) in [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]:
        c.set(x0 + x, y0 + y, K)


def plate(c, cx, cy, r=11.5):
    """A round brass plate: keyline, a brass ring lit on its upper left, a dark face."""
    import math
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            lit = (-dx - dy) / (d + 1e-6)
            if d > r - 1.0:
                col = K
            elif d > r - 2.2:
                col = YL if lit > 0.3 else (TN if lit > -0.4 else GO)
            elif d > r - 3.4:
                col = TN if lit > 0.2 else (GO if lit > -0.5 else OL)
            elif d > r - 4.3:
                col = K
            else:
                col = N0
            c.set(x, y, col)


def heart(c, x0, y0):
    """The player's heart, as on his HUD: 11x10, lit top left."""
    art = ["..KKK.KKK..",
           ".K112K233K.",
           "K112222333K",
           "K1222223333",
           "K2222223334",
           ".K22223334K",
           "..K223334K.",
           "...K2334K..",
           "....K34K...",
           ".....KK...."]
    cols = {'K': K, '1': HEART[0], '2': HEART[1], '3': HEART[2], '4': HEART[3]}
    for j, row in enumerate(art):
        for i, ch in enumerate(row[:11]):
            if ch in cols:
                c.set(x0 + i, y0 + j, cols[ch])


def beanie(c, x0, y0):
    """Danny's knit beanie: a striped dome 13x10 with a folded brim, lit top left."""
    import math
    for y in range(10):
        for x in range(13):
            dx, dy = x + 0.5 - 6.5, y + 0.5 - 8.0
            if y < 7:
                inside = (dx / 6.5) ** 2 + (dy / 7.6) ** 2 <= 1.0
            else:
                inside = True
            if not inside:
                continue
            edge = (dx / 6.5) ** 2 + (dy / 7.6) ** 2 > 0.8 and y < 7
            if y >= 7:
                col = BEANIE[1] if y == 7 else (BEANIE[2] if y == 8 else BEANIE[3])     # the folded brim
                if x in (0, 12):
                    col = K
            elif edge:
                col = K
            else:
                # knit ribs a texel wide, pale and mid blue, lit on the left of the dome and shaded on the right
                rib = x % 2
                lit = dx < -1.0 or (dx < 1.5 and dy < -4.0)
                col = (BEANIE[0] if rib else BEANIE[1]) if lit else (BEANIE[1] if rib else BEANIE[2])
                if dx > 3.0 and not rib:
                    col = BEANIE[3]
            c.set(x0 + x, y0 + y, col)
    for x in range(13):
        c.set(x0 + x, y0 + 10, K)


def frame_part():
    c = Canvas(W, H)
    bar(c, BAR_X, BAR_Y, BAR_W, BAR_H)
    plate(c, 11.5, 12.0)
    plate(c, W - 11.5, 12.0)
    heart(c, 6, 7)
    beanie(c, W - 18, 6)
    # brass notches over and under the centre line, pointing at it
    for (y, w_) in ((1, 3), (2, 3), (3, 1)):
        for i in range(w_):
            c.set(CENTRE_X + 1 - w_ // 2 + i, y, YL if y < 3 else TN)
    for (y, w_) in ((22, 3), (21, 3), (20, 1)):
        for i in range(w_):
            c.set(CENTRE_X + 1 - w_ // 2 + i, y, TN if y > 20 else GO)
    for (x, y) in ((CENTRE_X - 1, 0), (CENTRE_X, 0), (CENTRE_X + 1, 0), (CENTRE_X - 2, 1), (CENTRE_X + 2, 1),
                   (CENTRE_X - 1, 23), (CENTRE_X, 23), (CENTRE_X + 1, 23), (CENTRE_X - 2, 22), (CENTRE_X + 2, 22)):
        c.set(x, y, K)
    return c


def fill_player():
    c = Canvas(CH_W, CH_H)
    for y in range(CH_H):
        for x in range(CH_W):
            c.set(x, y, HEART[0] if y == 0 else (HEART[2] if y == CH_H - 2 else (HEART[3] if y == CH_H - 1 else HEART[1])))
    return c


def fill_danny():
    c = Canvas(CH_W, CH_H)
    for y in range(CH_H):
        for x in range(CH_W):
            rib = (x // 2) % 2
            if y == 0:
                col = BEANIE[0]
            elif y == CH_H - 1:
                col = BEANIE[3]
            else:
                col = BEANIE[1] if rib == 0 else BEANIE[2]
            c.set(x, y, col)
    return c


def centre_part():
    c = Canvas(3, 8)
    for y in range(8):
        c.set(1, y, K)
    for x in (0, 2):
        c.set(x, 0, K)
        c.set(x, 7, K)
    c.set(1, 0, YL)
    c.set(1, 7, TN)
    return c


def marker_frames():
    """The struggle point: a white-hot bar through the channel with a knob above and below, flickering."""
    out = []
    for f in range(4):
        c = Canvas(9, 16)
        hot = (WH, YL) if f % 2 == 0 else (YL, TN)
        for y in range(3, 13):
            c.set(3, y, K)
            c.set(5, y, K)
            c.set(4, y, hot[0] if 5 <= y <= 10 else hot[1])
        for (cy, d) in ((1, 1), (14, -1)):
            for (dx, dy, col) in ((0, 0, K), (-1, d, K), (1, d, K), (0, d, hot[1]), (-2, 2 * d, K), (2, 2 * d, K),
                                  (-1, 2 * d, hot[1]), (0, 2 * d, hot[0]), (1, 2 * d, hot[1])):
                c.set(4 + dx, cy + dy, col)
        if f in (0, 2):
            for (x, y) in (((1, 6), (7, 9)) if f == 0 else ((7, 5), (1, 10))):
                c.set(x, y, WH)
        out.append(c)
    return out


def parts():
    """name -> list of Canvas frames (one for a still)."""
    return {'tug_meter_frame': [frame_part()], 'tug_meter_fill_player': [fill_player()],
            'tug_meter_fill_danny': [fill_danny()], 'tug_meter_centre': [centre_part()],
            'tug_meter_marker': marker_frames()}
