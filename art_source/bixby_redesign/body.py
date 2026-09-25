"""Body parts (right side authored; the frame mirrors them): tail, hind legs, the black saddle, the
white chest, front legs, side necks, collars and the headband.

Beagle colouring carried through: black saddle over the shoulders and back, tan (ember) on the
thighs and upper legs, white chest, lower legs, paws and tail tip.
"""
from pal import AX, fill, poly
from shapes import capsule, chain, edge, half, poly_line, recolor, spt


def fur_shade(part, lit='u', base='t', shade='s', deep='r'):
    """Top-lit volume for a red fur part: lit top rim, shaded bottom."""
    recolor(part, edge(part, 0, -1, 1), lit, only=base)
    recolor(part, edge(part, 0, 1, 2), shade, only=base)
    recolor(part, edge(part, 0, 1, 1), deep)


def white_shade(part):
    recolor(part, edge(part, 0, -1, 1), 'w', only='x')
    recolor(part, edge(part, 0, 1, 2), 'y', only='x')
    recolor(part, edge(part, 0, 1, 1), 'z')


def black_shade(part, rim_dx=1):
    recolor(part, edge(part, 0, -1, 1), 'd', only='c')
    recolor(part, edge(part, 0, 1, 2), 'b', only='c')
    recolor(part, edge(part, rim_dx, 0, 1), 'e')


#TAIL (only on the left, not mirrored)

# The tail swings through the flap: up on the upstroke, down (clear of the left wing's wrist) on the
# downstroke.
TAIL_PATHS = {'up': [(66, 126), (48, 140), (30, 146), (16, 140), (9, 127), (10, 116)],
              'down': [(66, 128), (48, 142), (30, 148), (17, 147), (10, 141), (10, 134)]}
TAIL_TIP_DY = {'up': 0, 'down': 16}


def tail(dy=0, pose='up'):
    """The saddle's black runs down the tail; a whip curling out low on the left and up."""
    t = fill(chain(spt(TAIL_PATHS[pose], 0, dy), 4.2, 2.8), 'c')
    recolor(t, edge(t, 0, -1, 1), 'd')
    recolor(t, edge(t, 0, 1, 1), 'b')
    recolor(t, edge(t, -1, 0, 1), 'e')
    return t


def tail_tip(dy=0, pose='up'):
    """Bixby's white tail tip, licking up like a pale flame."""
    pts = spt([(6, 118), (5, 110), (8, 102), (10, 106), (12, 95), (15, 103), (19, 94), (18, 106),
               (16, 116), (12, 121)], 0, dy + TAIL_TIP_DY[pose])
    t = fill(poly(pts), 'x')
    recolor(t, edge(t, -1, 0, 1), 'w')
    recolor(t, edge(t, 1, 0, 1), 'y')
    recolor(t, edge(t, 0, 1, 1), 'y')
    return t


#LEGS

HIND = dict(hip=(136, 110), hock=(152, 128), ankle=(152, 139), paw=(153, 144))


def hind_leg(dy=0):
    """Splayed out past the front legs: a tan (ember) thigh with a fur tuft off its back, a white
    lower leg, a paw with hooked claws."""
    H = {k: (v[0], v[1] + dy) for k, v in HIND.items()}
    thigh = fill(capsule(H['hip'], H['hock'], 10, 6.5), 't')
    thigh.update({p: 't' for p in poly([(146, 110 + dy), (158, 115 + dy), (152, 118 + dy),
                                        (159, 122 + dy), (152, 124 + dy)])})
    recolor(thigh, edge(thigh, 0, -1, 1), 'u')
    recolor(thigh, edge(thigh, 1, 0, 1), 's')
    recolor(thigh, edge(thigh, 0, 1, 2), 's')
    recolor(thigh, edge(thigh, 0, 1, 1), 'r')
    for seg in ([(149, 115 + dy), (154, 121 + dy)], [(141, 118 + dy), (146, 124 + dy)]):
        for q in poly_line(seg):
            if q in thigh:
                thigh[q] = 'k'
    shin = fill(capsule(H['hock'], H['ankle'], 5, 4.6), 'x')
    recolor(shin, edge(shin, -1, 0, 1), 'w', only='x')
    recolor(shin, edge(shin, 1, 0, 2), 'y')
    recolor(shin, edge(shin, 1, 0, 1), 'z')
    return [thigh, shin]


def paw(c, rx, ry):
    """A white paw from the front, toes split by keylines, black claws hooking down."""
    cx, cy = c
    p = fill(poly([(cx - rx, cy + 1), (cx - rx + 1, cy - ry + 1), (cx - rx + 3, cy - ry), (cx + rx - 3, cy - ry),
                   (cx + rx - 1, cy - ry + 1), (cx + rx, cy + 1), (cx + rx - 1, cy + ry - 1),
                   (cx - rx + 1, cy + ry - 1)]), 'x')
    white_shade(p)
    for tx in (int(cx - rx // 2 - 1), int(cx), int(cx + rx // 2 + 1)):
        for yy in range(int(cy) - 1, int(cy + ry)):
            if (tx, yy) in p:
                p[(tx, yy)] = 'k'
    return p


def claws(c, rx, ry):
    cx, cy = c
    out = {}
    for tx in (cx - rx + 2, cx - 2, cx + 2, cx + rx - 2):
        for i, (dx, dy) in enumerate(((0, 0), (0, 1), (1, 2))):
            out[(tx + dx, cy + ry + dy - 1)] = 'k' if i < 2 else 'k'
    return out


FRONT = dict(shoulder=(119, 100), elbow=(128, 119), wrist=(124, 137), paw=(123, 143))


def front_leg(dy=0):
    """Dangling with a bend: black saddle over a heavy shoulder, the upper arm tan (ember) with a
    jagged fur tuft off the back of the elbow, a white forearm angling back in, a heavy paw."""
    F = {k: (v[0], v[1] + dy) for k, v in FRONT.items()}
    shoulder = fill(capsule(F['shoulder'], (124, 110 + dy), 10, 9), 'c')
    black_shade(shoulder)
    for q in poly_line([(116, 104 + dy), (122, 113 + dy)]):
        if q in shoulder and shoulder[q] == 'c':
            shoulder[q] = 'b'
    upper = fill(capsule((123, 108 + dy), F['elbow'], 8, 7), 't')
    # the elbow tuft: two flame-shaped blades raking back and out
    tuft = poly([(130, 112 + dy), (137, 117 + dy), (133, 118 + dy), (138, 123 + dy), (131, 124 + dy),
                 (128, 126 + dy)])
    upper.update({p: 't' for p in tuft})
    recolor(upper, edge(upper, 0, -1, 1), 'u')
    recolor(upper, edge(upper, 1, 0, 1), 's')
    recolor(upper, edge(upper, 0, 1, 2), 's')
    recolor(upper, edge(upper, 0, 1, 1), 'r')
    # the elbow tuft split off by a black cut, and a shadow cut down the arm's back
    for seg in ([(130, 115 + dy), (134, 120 + dy)], [(127, 113 + dy), (128, 118 + dy)]):
        for q in poly_line(seg):
            if q in upper:
                upper[q] = 'k'
    fore = fill(capsule((127, 121 + dy), F['wrist'], 6.4, 5.4), 'x')
    recolor(fore, edge(fore, -1, 0, 2), 'w', only='x')
    recolor(fore, edge(fore, 1, 0, 3), 'y')
    recolor(fore, edge(fore, 1, 0, 1), 'z')
    for q in poly_line([(128, 124 + dy), (126, 133 + dy)]):
        if q in fore and fore[q] == 'x':
            fore[q] = 'y'
    return [shoulder, upper, fore]


# Hand-drawn paws (right side; the frame mirrors them): four toes split by keylines, lit on top,
# shaded under, charcoal claws with a violet glint hooking in toward the middle.
FRONT_PAW = [
    # 114-118 119-123 124-128 129-132   y
    "...kk kkkkk kkkkk kkk.",   # 138
    "..kww wwwxx xxxxx yk..",   # 139
    ".kwwx xxxxx xxxxx yyk.",   # 140
    ".kwxx xxxxx xxxxx yyk.",   # 141
    "kwxxx xxxxx xxxxx yyzk",   # 142
    "kwxxk wxxxk wxxxk xyzk",   # 143
    "kxxyk xxxyk xxxyk xyzk",   # 144
    "kxxyk xxxyk xxxyk yyzk",   # 145
    "kxyyk xyyyk xyyyk yzzk",   # 146
    ".kyyk yyzzk yyzzk zzk.",   # 147
    "..kkk kkkkk kkkkk kk..",   # 148
    ".kdk. kdck. kdck. kdk.",   # 149
    "..k.. .kck. kck.. .k..",   # 150
    "..... ..k.. .k... ....",   # 151
]
FRONT_PAW_XY = (114, 138)
HIND_PAW = [
    # 145-149 150-154 155-159 160-161  y
    "...kk kkkkk kkkkk ..",    # 139
    "..kww wxxxx xxxyk ..",    # 140
    ".kwxx xxxxx xxxxy k.",    # 141
    "kwxxx xxxxx xxxxy zk",    # 142
    "kwxxk wxxkw xxkxy zk",    # 143
    "kxxyk xxykx xykxy zk",    # 144
    "kxyyk xyykx yykyz zk",    # 145
    ".kyyk yzzky zzkzz k.",    # 146
    "..kkk kkkkk kkkkk ..",    # 147
    ".kdk. kdk.k dk.kd k.",    # 148
    "..k.. .k... k...k ..",    # 149
]
HIND_PAW_XY = (145, 139)


def paw_map(front=True, dy=0):
    from pal import amap
    rows, (x0, y0) = (FRONT_PAW, FRONT_PAW_XY) if front else (HIND_PAW, HIND_PAW_XY)
    return amap(rows, x0, y0 + dy)


def big_paw(c, small=False):
    """A heavy paw seen from the front, hanging: toes split by keylines."""
    cx, cy = c
    w = 7 if small else 9
    h = 5 if small else 6
    pts = [(cx - w, cy + 2), (cx - w, cy - 1), (cx - w + 3, cy - h + 1), (cx + w - 3, cy - h + 1),
           (cx + w, cy - 1), (cx + w, cy + 2), (cx + w - 2, cy + h), (cx - w + 2, cy + h)]
    p = fill(poly(pts), 'x')
    recolor(p, edge(p, 0, -1, 1), 'w')
    recolor(p, edge(p, 0, 1, 2), 'y')
    recolor(p, edge(p, 0, 1, 1), 'z')
    step = 4 if small else 5
    for tx in (cx - step, cx, cx + step):
        for yy in range(cy, cy + h + 1):
            if (tx, yy) in p:
                p[(tx, yy)] = 'k'
    return p


def claws(c, small=False):
    """Hooked black claws under a paw, one per toe, curling inward."""
    cx, cy = c
    h = 5 if small else 6
    step = 4 if small else 5
    toes = [cx - step - 2, cx - 2, cx + 2, cx + step + 2]
    out = {}
    for tx in toes:
        inward = 1 if tx < cx else -1
        for (dx, dy) in ((0, 1), (0, 2), (0, 3), (inward, 4)):
            out[(tx + dx, cy + h + dy)] = 'k'
        out[(tx - inward, cy + h + 1)] = 'k'
    return out


#TORSO

def mantle(dy=0):
    """The black saddle: a spiky ruff rising behind the three necks (it shows in the V between the
    heads) and wrapping over the shoulders."""
    pts = spt(half([(95.5, 60), (104, 50), (110, 40), (114, 48), (121, 34), (124, 46), (131, 40),
                    (130, 52), (140, 54), (136, 62), (150, 66), (142, 74), (156, 80), (146, 86),
                    (156, 94), (144, 96), (148, 106), (136, 106), (134, 116), (95.5, 118)]), 0, dy)
    m = fill(poly(pts), 'c')
    recolor(m, edge(m, 0, -1, 1), 'd')
    recolor(m, edge(m, 0, 1, 2), 'b')
    recolor(m, edge(m, 1, 0, 1), 'e')
    recolor(m, edge(m, -1, 0, 1), 'e')
    # black fur partings running down from each spike
    for seg in ([(121, 38), (124, 56)], [(131, 44), (134, 60)], [(144, 68), (140, 80)], [(150, 84), (144, 92)],
                [(110, 44), (112, 58)], [(138, 96), (133, 104)], [(124, 98), (122, 108)]):
        for s in (seg, [(191 - x, y) for (x, y) in seg]):
            for q in poly_line(spt(s, 0, dy)):
                if q in m and m[q] in 'cbd':
                    m[q] = 'k'
    return m


def chest(dy=0):
    pts = spt(half([(95.5, 84), (106, 85), (113, 91), (116, 101), (115, 111), (111, 117), (110, 126),
                    (106, 120), (103, 130), (99, 122), (95.5, 131)]), 0, dy)
    c = fill(poly(pts), 'x')
    recolor(c, edge(c, 0, 1, 2), 'y')
    recolor(c, edge(c, 1, 0, 1), 'y')
    recolor(c, edge(c, -1, 0, 1), 'y')
    hi = poly(spt(half([(95.5, 90), (102, 90), (107, 96), (106, 104), (100, 108), (95.5, 108)]), 0, dy))
    recolor(c, hi, 'w', only='x')
    # fur partings
    for seg in ([(104, 110), (106, 118)], [(100, 112), (101, 121)], [(110, 104), (111, 112)]):
        for s in (seg, [(191 - x, y) for (x, y) in seg]):
            for q in poly_line(spt(s, 0, dy)):
                if q in c and c[q] in 'xw':
                    c[q] = 'y'
    return c


def belly(dy=0):
    pts = spt(half([(95.5, 114), (105, 114), (108, 122), (104, 133), (95.5, 136)]), 0, dy)
    b = fill(poly(pts), 'y')
    recolor(b, edge(b, 0, 1, 2), 'z')
    return b


def side_neck(dy=0):
    """The saddle runs up the back of each side neck."""
    n = fill(capsule((118, 98 + dy), (142, 82 + dy), 10, 10), 'c')
    black_shade(n)
    return n


#COLLARS

def collar_band(pts, spikes, studs):
    """Wine leather band with gold studs; gold spikes (triangles) stamped separately."""
    band = fill(poly(pts), 'L')
    recolor(band, edge(band, 0, -1, 1), 'm')
    recolor(band, edge(band, 0, 1, 1), 'l')
    for s in studs:
        if s in band:
            band[s] = 'O'
    spike_parts = []
    for tri in spikes:
        sp = fill(poly(tri), 'o')
        recolor(sp, edge(sp, -1, 0, 1), 'O')
        recolor(sp, edge(sp, 1, 0, 1), 'G')
        spike_parts.append(sp)
    return band, spike_parts


def mid_collar(dy=0):
    pts = spt(half([(95.5, 84), (104, 83), (112, 80), (118, 76), (120, 82), (113, 88), (104, 91),
                    (95.5, 92)]), 0, dy)
    spikes = []
    for base_l, base_r, tip in [((99, 92), (103, 91), (101, 98)), ((107, 90), (111, 88), (111, 95)),
                                ((114, 86), (118, 83), (120, 90))]:
        for tri in ([base_l, base_r, tip], [(191 - x, y) for (x, y) in (base_l, base_r, tip)]):
            spikes.append(spt(tri, 0, dy))
    studs = [(100, 87 + dy), (108, 85 + dy), (115, 81 + dy), (91, 87 + dy), (83, 85 + dy), (76, 81 + dy)]
    return collar_band(pts, spikes, studs)


def side_collar(dy=0):
    pts = spt([(124, 84), (131, 88), (139, 88), (147, 84), (150, 89), (141, 94), (130, 94), (122, 89)], 0, dy)
    spikes = [spt(t, 0, dy) for t in ([(127, 93), (131, 94), (128, 100)], [(134, 94), (138, 94), (136, 101)],
                                      [(142, 92), (146, 90), (147, 97)])]
    studs = [(129, 90 + dy), (136, 91 + dy), (143, 89 + dy)]
    return collar_band(pts, spikes, studs)


#HEADBAND (Liam's): steel plate on the middle head's forehead, the band round the skull, the tails
# streaming off the knot behind the right ear

def headband(dx=0, dy=0):
    """Worn high on the skull's curve, so the crest flames rise above the plate."""
    band = fill(poly(spt([(74, 18), (80, 14), (88, 11), (95.5, 10), (103, 11), (111, 14), (117, 18),
                          (117, 22), (111, 18), (103, 15), (95.5, 14), (88, 15), (80, 18), (74, 22)],
                         dx, dy)), 'T')
    recolor(band, edge(band, 0, -1, 1), 'U')
    recolor(band, edge(band, 0, 1, 1), 'S')
    plate = fill(poly(spt([(86, 9), (105, 9), (105, 17), (86, 17)], dx, dy)), 'U')
    recolor(plate, edge(plate, 0, -1, 1), 'W')
    recolor(plate, edge(plate, -1, 0, 1), 'W')
    recolor(plate, edge(plate, 1, 0, 1), 'T')
    recolor(plate, edge(plate, 0, 1, 1), 'T')
    # a scratch across the plate
    for q in poly_line(spt([(91, 11), (94, 14)], dx, dy)):
        plate[q] = 'T'
    return band, plate


def headband_tails(dx=0, dy=0):
    tails = []
    for path, r in (([(116, 17), (124, 12), (132, 12), (140, 7), (148, 7), (155, 2)], 1.3),
                    ([(116, 19), (125, 17), (133, 18), (141, 14), (149, 15), (157, 11)], 1.1)):
        t = fill(chain(spt(path, dx, dy), r, r * 0.8), 'T')
        recolor(t, edge(t, 0, -1, 1), 'U')
        recolor(t, edge(t, 0, 1, 1), 'S')
        tails.append(t)
    return tails
