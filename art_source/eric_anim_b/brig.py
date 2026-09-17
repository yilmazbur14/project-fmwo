"""Layered rig for the Eric redesign (128x128 frames).
Body layers are rendered once in the designer's 96-space with the untouched parts code,
then everything else (arms, sword, fx) is drawn in 128-space."""
import math
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT, TH_CLOTH, hexc, RAMPS
from pngio import write_png, read_png, scale, blank, paste, crop

FW = FH = 128
OX, OY = 16, 32
FL = (136, 180, 99, 255)

# draw order of the approved build (sword128.body96)
ORDER = ['cape', 'legs', 'flap', 'tassets', 'belt', 'torso', 'beltdet', 'gorget',
         'uarm_R', 'uarm_L', 'paul_L', 'paul_R', 'farm_R', 'head']


def _layers96():
    import parts as P
    import weapons as Wp
    from legstamp import stamp_legs
    from headrender import render_head
    from headstrokes import STROKES
    L = {}
    lib.W = lib.H = 96

    def lay(name, fn):
        cv = lib.Canvas()
        fn(cv)
        L[name] = cv.px

    lay('cape', P.cape)
    lay('legs', stamp_legs)
    lay('flap', P.flap)
    lay('tassets', lambda cv: (P.tassets(cv), P.tasset_details(cv)))
    lay('belt', P.belt)
    lay('torso', lambda cv: P.torso_details(cv, P.torso(cv)))
    lay('beltdet', P.belt_details)
    lay('gorget', P.gorget)
    lay('uarm_R', Wp.arm_right_back)
    lay('uarm_L', Wp.arm_left_back)

    def paul(f):
        def fn(cv):
            d, l1, l2 = P.pauldron(cv, f)
            P.pauldron_details(cv, f, d, l1, l2)
        return fn
    lay('paul_L', paul(P.ID))
    lay('paul_R', paul(P.mirror))
    lay('farm_R', Wp.arm_right_front)
    lay('head', lambda cv: render_head(cv, STROKES))
    return L


_CACHE = {}


def layers():
    if not _CACHE:
        _CACHE.update(_layers96())
        lib.W = lib.H = FW
    return _CACHE


def use128():
    lib.W = lib.H = FW


class Frame128:
    def __init__(self):
        use128()
        self.cv = lib.Canvas()

    @property
    def px(self):
        return self.cv.px

    def put(self, name_or_layer, dx=0, dy=0):
        layer96 = layers()[name_or_layer] if isinstance(name_or_layer, str) else name_or_layer
        n = len(layer96)
        for y in range(n):
            row = layer96[y]
            for x in range(len(row)):
                p = row[x]
                if p is not None:
                    X, Y = x + OX + dx, y + OY + dy
                    if 0 <= X < FW and 0 <= Y < FH:
                        self.cv.px[Y][X] = p

    def put128(self, px, dx=0, dy=0):
        for y in range(len(px)):
            for x in range(len(px[0])):
                p = px[y][x]
                if p is not None and (len(p) < 4 or p[3]):
                    X, Y = x + dx, y + dy
                    if 0 <= X < FW and 0 <= Y < FH:
                        self.cv.px[Y][X] = p

    def rgba(self):
        return self.cv.rgba()


def save_zoom(px, path, s=8, bg=FL):
    z = scale(px, s, bg)
    write_png(path, len(z[0]), len(z), z)
