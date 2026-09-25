"""Frame 0 from the belt down: the rope belt and its knot, the gi trousers, shins and bare feet.

Kept: a brown rope belt with a front knot and two hanging ends, baggy navy gi trousers that burn
toward violet at a torn hem just under the knee, bare shins and feet planted on row 95.
Changed:
  * the belt is a twisted rope (lit strand, shadow, groove, repeating on the diagonal) instead of a
    flat strap hatched with black lines; the knot is a real knot with two frayed ends;
  * the trousers are continuous under the belt (the approved frame let a band of bare skin show
    between the knot's ends) and carry folds;
  * each shin is lit on its own axis - the approved rig shaded the right shin with the LEFT shin's
    cylinder, so it rendered as a solid dark-brown sock;
  * feet are drawn: ankle, instep, four toes with the big toe inside, keylined;
  * the belt sits tight on the gi, so its shadow is a second line under it (frame 1: the folded
    forearms cast the same line on the belt).
"""
from lib import amap, poly, mirror_set, shade, n_cyl, fill, stroke, sym

# ------------------------------------------------------------------ belt

BELT_X0, BELT_X1 = 30, 65      # rope interior; keylines at 29 and 66


def belt():
    """Rows 68 (keyline) 69-71 (rope) 72 (keyline). The strands run '////' and each is lit on its
    upper left; the rope as a whole is lit on top and in shadow underneath."""
    part = {}
    lay = {69: 'nnop', 70: 'nopq', 71: 'opqr'}
    for y, pat in lay.items():
        for x in range(BELT_X0, BELT_X1 + 1):
            part[(x, y)] = pat[(x + y) % 4]
    for x in range(BELT_X0 - 1, BELT_X1 + 2):
        part[(x, 68)] = 'k'
        part[(x, 72)] = 'k'
    for y in (69, 70, 71):
        part[(BELT_X0 - 1, y)] = 'k'
        part[(BELT_X1 + 1, y)] = 'k'
    return part


KNOT = [
    # x: 42-46 47-51 52-53     y
    "...kk kkkk. ..",         # 66
    "..knn noopk ..",         # 67  the knot rides two rows above the belt
    ".knno ooppq k.",         # 68
    ".knno qropq k.",         # 69  a crease between the two lobes
    ".knoo qropq k.",         # 70
    ".koop qrpqr k.",         # 71
    "..kpq qrqrk ..",         # 72
    "...kk kkkk. ..",         # 73
]

# the two ends hang from under the knot over the trousers, drifting apart, frayed at the tips
TAILS = [
    # x: 42-46 47-51 52-53     y
    ".kopk ..kop k.",         # 74
    ".knpk ..knp k.",         # 75
    ".kopk ...ko pk",         # 76
    "kopk. ...ko pk",         # 77
    "knpk. ...kn pk",         # 78
    "kopk. ...ko qk",         # 79
    "kok.. ....k qk",         # 80  frayed: the strands end at different lengths
    ".k... ..... k.",         # 81
]


def knot():
    return amap(KNOT, 42, 66)


def tails():
    return amap(TAILS, 42, 74)


# ------------------------------------------------------------------ trousers

LEG_L = [(32, 70), (47, 70), (47, 76), (46, 79.5), (45.5, 83), (31.5, 83), (31, 80), (31, 76), (31.5, 73)]

# the torn hem: teeth hanging below row 83, per leg (left leg; the right is mirrored)
HEM_TEETH_L = [
    [(31.5, 82), (33.5, 82), (32.0, 85.0)],
    [(34.0, 82), (36.5, 82), (35.5, 84.0)],
    [(37.0, 82), (39.5, 82), (38.0, 85.5)],
    [(40.0, 82), (42.5, 82), (41.5, 84.5)],
    [(43.0, 82), (45.2, 82), (44.0, 85.0)],
]


def trouser_mask_l():
    m = poly(LEG_L)
    for t in HEM_TEETH_L:
        m |= poly(t)
    return m


GI_TH = [0.97, 0.80, 0.55, 0.25, 0.0]
# navy (upper) and the violet it burns toward at the hem; same ordering light -> dark
NAVY = 'abcdef'
VIOLET = 'ABCDEF'


def trousers():
    out = {}
    for side in (0, 1):
        m = trouser_mask_l()
        ax = (39.0, 70.0), (38.0, 84.0)
        if side:
            m = mirror_set(m)
            ax = (95 - 39.0, 70.0), (95 - 38.0, 84.0)
        part = shade(m, NAVY, n_cyl(ax[0], ax[1], 9.5), GI_TH, bias=1)
        # folds: from the crotch out and down, and one down the front of each thigh
        if side == 0:
            stroke(part, [(45, 74), (42, 77), (40, 80)], 'k')      # the deep crease out of the crotch
            stroke(part, [(44, 74), (41, 77)], 'b', only='cd')
            stroke(part, [(35, 74), (34, 78), (34, 81)], 'e')
            stroke(part, [(36, 74), (35, 78)], 'b', only='cd')
        else:
            stroke(part, [(50, 74), (53, 77), (55, 80)], 'k')
            stroke(part, [(51, 74), (54, 77)], 'c', only='de')
            stroke(part, [(60, 74), (61, 78), (61, 81)], 'e')
            stroke(part, [(59, 74), (60, 78)], 'c', only='de')
        # burn toward violet below the knee
        for (x, y), k in list(part.items()):
            if k in NAVY and (y >= 80 or (y == 79 and (x + y) % 2 == 0)):
                part[(x, y)] = VIOLET[NAVY.index(k)]
        out.update(part)
    # the rope belt is thick and sits tight on the gi: its shadow is a second line right under it
    for (x, y), k in list(out.items()):
        if y == 73 and k in NAVY + VIOLET:
            out[(x, y)] = 'k'
    # the seam between the legs runs up under the knot: two legs, so a keyline
    for y in range(73, 77):
        out[(47, y)] = 'k'
        out[(48, y)] = 'e'
    return out


# ------------------------------------------------------------------ shins and feet

SHIN_L = ((35.5, 82.0), (35.5, 88.5), 3.9, 3.7)


def shins():
    (a, b, r0, r1) = SHIN_L
    from lib import capsule
    l = capsule(a, b, r0, r1)
    part = shade(l, 'skin', n_cyl(a, b, 4.8), [0.93, 0.78, 0.52, 0.25, 0.0])
    ra, rb = (95 - a[0], a[1]), (95 - b[0], b[1])
    part.update(shade(mirror_set(l), 'skin', n_cyl(ra, rb, 4.8), [0.93, 0.78, 0.52, 0.25, 0.0]))
    return part


FOOT_L = [
    # x: 26-30 31-35 36-40 41     y
    "..... ktstu uuvwk .",        # 88  ankle
    "....k tsttu uuvvk .",        # 89
    "..ktt sttuu uuvvk .",        # 90  instep, widening to the outside
    ".ktst ttuuu uuvwk .",        # 91
    ".kttu uuuuu uvvwk .",        # 92
    ".ktuk tuktu kstuk .",        # 93  toes, lit on top; big toe inside
    ".kuvk uvkuv ktuvk .",        # 94
    "..kkk kkkkk kkkk. .",        # 95  sole
]

# the mirrored shape, still lit from screen left: its inner side and big toe take the light
FOOT_R = [
    # x: 54-58 59-63 64-68 69     y
    ".ktst uuuvw k.... .",        # 88
    ".ktst tuuuv vk... .",        # 89
    ".ktst tuuuu vvwk. .",        # 90
    ".ktst tuuuu uvvwk .",        # 91
    ".kttu uuuuu vvwwk .",        # 92
    ".kstu ktukt ukuvk .",        # 93
    ".ktuv kuvku vkvwk .",        # 94
    "..kkk kkkkk kkkk. .",        # 95
]


def feet():
    return [amap(FOOT_L, 26, 88), amap(FOOT_R, 54, 88)]
