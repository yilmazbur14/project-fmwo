import sys
from build import *

BG = (120, 160, 120, 255)
OUT = sys.argv[1] if (len(sys.argv) > 1 and __name__=='__main__') else 'stage3'

def LR(pts):
    m = poly_mask(pts)
    return m, mirror_mask(m)

def LRm(m):
    return m, mirror_mask(m)

POD_A = -14
pod_L, pod_R = LR(rot_rect(16, 18.5, 18, 11, POD_A, ch=1))
helmet = ell_mask(48, 19.5, 16, 15)
bolt_L, bolt_R = LR([(29, 17), (33, 16), (33, 24), (29, 23)])
torso = poly_mask(sym_poly([(48, 29), (40, 29), (34, 31), (30, 35), (28, 41), (29, 47), (33, 54), (38, 59), (48, 61)]))
chestplate = ell_mask(48, 48.5, 13.5, 10.5)
collar = poly_mask(sym_poly([(48, 30), (39, 30), (35, 33), (36, 37), (41, 39), (48, 40)]))
pelvis = poly_mask(sym_poly([(48, 56), (37, 56), (35, 60), (38, 66), (43, 70), (48, 71)]))
thigh_L, thigh_R = LR([(33, 59), (46, 60), (46, 67), (43, 76), (29, 77), (27, 69), (29, 63)])
knee_L, knee_R = LRm(ell_mask(35, 77, 7, 5))
shin_L, shin_R = LR([(27, 79), (43, 79), (45, 84), (46, 90), (24, 90), (23, 84)])
foot_L, foot_R = LR([(21, 89), (44, 88), (47, 90), (47, 96), (18, 96), (18, 92)])
paul_L, paul_R = LRm(rot_ell_mask(22, 32, 12.5, 9.5, -12))
uarm_L, uarm_R = LR(rot_rect(15, 43, 16, 11, 132))
elbow_L, elbow_R = LRm(ell_mask(9, 50, 5.5, 5.5))
emit_L, emit_R = LR(rot_rect(4.5, 49.5, 9, 11, 0, ch=1))
farm_L, farm_R = LR(rot_rect(19, 55, 22, 14, 24, ch=3))
fist_L, fist_R = LR([(26, 55), (35, 55), (38, 58), (38, 65), (35, 68), (27, 68), (24, 64), (24, 58)])

FACE = """
......kkkkkkkkkk......
....kkZZZZZZZZZZkk....
...kZYyyyyyyyyyyYZk...
..kZylHHllyyyyyyyYZk..
.kZylHllyyyyyyyyyyYZk.
kZyllyyyyykkyyyyyyyYZk
kZylyyyyykSSkyyyyyYYZk
kZyyyyyykSTTskyyyYYZZk
kZyyyyYkSTTTTckYyYYZZk
kZyYkZZSsssscccZZkYZZk
kZYkskkZZssccZZkkckZZk
.ksssWBBksscckBBWcbbk.
"""
FACE2 = """
.ksssckksssccckkccbbk.
.kSssssssscbccccccbbk.
.kssssssskcbkccccbbbk.
.ksscYllyyyyyyYYYcbbk.
.kscYlykkkkkkkkyYZbbk.
.kccYlkWWWWiiijkYZbak.
.kcbYykMMMXXMMMkZZbak.
..kcYZZkkkkkkkkZZZak..
...kZbccccccbbbbbZk...
"""
CHEST_EYE = """
kk....
kkkk..
.kPRk.
.kRXk.
.kXVk.
.kkkk.
"""
GRIN = """
kkkkkkkkkkkkkkkkkkkk
kqkqqkqqkqqkqqkqqkqk
kVXRrrPPPPPPPPrrRXVk
.kVXRrrrrrrrrrrRXVk.
..kVXRRrrrrrrRRXVk..
...kkVXXRRRRXXVkk...
.....kkkkkkkkkk.....
"""
ANTENNA = """
.....kkkk
....kkPRk
...kdkXXk
..kdk.kk.
.kdk.....
.kek.....
"""
ROCKET = """
..k..
.kRk.
kPRXk
kRRXk
kWWik
kWWik
kWiik
kXXVk
kWijk
"""
Y_EMB = """
kkk....kkk
kGFk..kFyk
.kGFkkFyk.
..kGFFyk..
...kFyk...
...kFyk...
...kFyk...
...kkkk...
"""
EMIT = """
.kkkkkkkk
kRRXkfdek
krRRkddek
kPrRkdDek
kPrRkkkkk
kPrRkdDek
kPrRkkkkk
kPrRkdDek
krRRkdeek
kRRXkeffk
.kkkkkkkk
"""

def check_sym(name, grid):
    rows = [r for r in grid.strip('\n').split('\n')]
    bad = []
    for i, r in enumerate(rows):
        ks = [j for j, c in enumerate(r) if c == 'k']
        w = len(r)
        mk = sorted(w - 1 - j for j in ks)
        if ks != mk:
            bad.append(i)
        if w != len(rows[0]):
            print(name, 'row', i, 'width', w, '!=', len(rows[0]))
    if bad:
        print(name, 'asymmetric k rows:', bad)

for n, g in [('FACE', FACE), ('FACE2', FACE2), ('GRIN', GRIN), ('Y', Y_EMB)]:
    check_sym(n, g)
import sys as _s

def rockets():
    # behind pod box; staggered with pod tilt (right side higher)
    for x0, y0 in [(8, 7), (13, 6), (18, 5)]:
        stamp(ROCKET, x0, y0)
        stamp(ROCKET, x0, y0, mirror=True)

def face_detail():
    stamp(FACE, 37, 10)
    stamp(FACE2, 37, 22)

def chest_detail():
    stamp(CHEST_EYE, 38, 40)
    stamp(CHEST_EYE, 38, 40, mirror=True)
    stamp(GRIN, 38, 47)
    # ab plate seams under grin
    # collar rivets
    stamp("kD", 38, 33); stamp("kD", 38, 33, mirror=True)

def pelvis_detail():
    stamp(Y_EMB, 43, 58)

def paul_detail():
    for m in (paul_L, paul_R):
        band, line = bottom_band(m, 3)
        recolor_region(band, 'purple', R=2, line_mask=line)
    # rivets
    riv = """
k
"""
    for x, y in [(13, 37), (25, 38)]:
        stamp("Uk", x, y); stamp("Uk", x, y, mirror=True)

def farm_detail():
    for m, cx in ((farm_L, 31), (farm_R, 95 - 31 + 1)):
        cuffline = ring_mask(m, cx, 61.5, 9.0, 10.0)
        cuff = ring_mask(m, cx, 61.5, 10.0, 13.0)
        recolor_region(cuff, 'purple', R=2, line_mask=cuffline)

FIST = """
..kkkkkkkkkk..
.kDdkDdkDdkdk.
kDddkdddkddkek
kdddkdddkdekek
kdddkddekeekfk
kkkkkkkkkkkkfk
kDDdddddeeekfk
kdddddddeeefgk
kkkkkkkkkkfggk
.kdddeeeeffggk
.keeeeefffgghk
..kfffffggghk.
...kkkkkkkkk..
"""

def fist_detail():
    stamp(FIST, 24, 55)
    stamp(FIST, 24, 55, mirror=True)

def pod_detail():
    a = math.radians(POD_A)
    for msk, cx in ((pod_L, 16), (pod_R, 96 - 16)):
        sgn = 1 if cx < 48 else -1
        band = [[False] * W for _ in range(H)]
        seam = [[False] * W for _ in range(H)]
        rim = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                if not msk[y][x]:
                    continue
                dx, dy = (x + 0.5 - cx) * sgn, y + 0.5 - 18.5
                v = -dx * math.sin(a) + dy * math.cos(a)
                if v > 0.2:
                    band[y][x] = True
                elif v > -0.8:
                    seam[y][x] = True
                if y >= 2 and msk[y - 1][x] and not msk[y - 2][x]:
                    rim[y][x] = True
        recolor_region(band, 'purple', R=2, line_mask=seam)
        for y in range(H):
            for x in range(W):
                if rim[y][x] and canvas[y][x] != BLACK:
                    canvas[y][x] = PALC['h']

def boot_detail():
    b = """
......o...
......o...
......o...
"""
    stamp(b, 28, 82)
    stamp(b, 28, 82, mirror=True)

def foot_detail():
    f = """
.......
..k....
..k....
.......
"""
    stamp(f, 26, 90)
    stamp(f, 26, 90, mirror=True)

def final_detail():
    stamp(ANTENNA, 47, 0)
    stamp(EMIT, 0, 44)
    stamp(EMIT, 0, 44, mirror=True)

order = [
    rockets,
    ('pod', union(pod_L, pod_R), 'dark', 3, TH_METAL, 0),
    pod_detail,
    ('thigh', union(thigh_L, thigh_R), 'metal', 6, TH_METAL, 0),
    ('torso', torso, 'metal', 8, TH_METAL, 0),
    ('chestplate', chestplate, 'metal', 7, TH_METAL, 0),
    ('bolt', union(bolt_L, bolt_R), 'dark', 2, TH_METAL, 0),
    ('helmet', helmet, 'metal', 9, TH_METAL, 0),
    face_detail,
    ('collar', collar, 'dark', 3, TH_METAL, 2),
    chest_detail,
    ('pelvis', pelvis, 'purple', 5, TH_SOFT, 2),
    pelvis_detail,
    ('knee', union(knee_L, knee_R), 'metal', 4, TH_METAL, 0),
    ('shin', union(shin_L, shin_R), 'white', 6, TH_SOFT, 1),
    boot_detail,
    ('foot', union(foot_L, foot_R), 'shoe', 3, TH_SOFT, 1),
    foot_detail,
    ('uarm', union(uarm_L, uarm_R), 'dark', 5, TH_METAL, 0),
    ('paul', union(paul_L, paul_R), 'metal', 8, TH_METAL, 2),
    paul_detail,
    ('emit', union(emit_L, emit_R), 'dark', 3, TH_METAL, 0),
    ('elbow', union(elbow_L, elbow_R), 'dark', 4, TH_METAL, 0),
    ('farm', union(farm_L, farm_R), 'metal', 7, TH_METAL, 2),
    farm_detail,
    fist_detail,
    final_detail,
]

def run_item(item):
    if callable(item):
        item()
    else:
        name, m, ramp, R, th, sh = item
        render_part(name, m, ramp, R=R, th=th, shadow_below=sh)

if __name__ == '__main__':
    for item in order:
        run_item(item)
    save(OUT + '.png')
    save(OUT + '_8x.png', 8, BG)
