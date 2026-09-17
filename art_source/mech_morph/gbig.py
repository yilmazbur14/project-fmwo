"""Greyson (unarmoured) at mech scale, 96x96, same pose as the mech."""
import build as B
from build import *
import mparts as M

def add_ramp(name, cols):
    B.RAMPS[name] = cols
    cs = [hexc(c) for c in cols]
    for i, c in enumerate(cs):
        B._DARKER.setdefault(c, cs[min(i + 1, len(cs) - 1)])
        B._LIGHTER.setdefault(c, cs[max(i - 1, 0)])

add_ramp('gskin', ['fff0dc', 'fadcb8', 'eec39a', 'd9a066', 'b8794a', '8a5236'])
add_ramp('trunks', ['b49ce6', '9270cc', '7858b0', '5c3e94', '46287a', '2e1656'])
add_ramp('sock', ['ffffff', 'f0f4f8', 'd6dee5', 'aab6c2', '808c9a', '5e6874'])

def LR(pts):
    m = poly_mask(pts); return m, mirror_mask(m)

ear_L, ear_R = LR([(33.5, 19), (37.5, 18), (38, 26), (35, 26), (33, 23)])
torso = poly_mask(sym_poly([(48, 25), (42, 25), (41, 28), (35, 30), (29, 32), (26.5, 36), (27, 42), (30, 48), (34, 54), (36, 57), (48, 58)]))
delt_L, delt_R = LRm = (None, None)
delt_L = rot_ell_mask(24, 37, 8.5, 7.5, -30); delt_R = mirror_mask(delt_L)
uarm_L, uarm_R = LR(rot_rect(15.5, 44, 15, 12, 132, ch=3))
farm_L, farm_R = LR(rot_rect(19, 55.5, 22, 12, 24, ch=4))
fist_L, fist_R = LR([(26, 55.5), (34, 55.5), (37, 58.5), (37, 65), (34, 67), (27, 67), (24.5, 64), (24.5, 58)])
trunks = poly_mask(sym_poly([(48, 54), (36, 54), (33, 58), (30, 64), (29, 68), (38, 69), (44, 66), (48, 65)]))
thigh_L, thigh_R = LR([(29, 62), (46, 62), (46, 70), (43, 77), (31, 78), (28, 71)])
calf_L, calf_R = LR([(29, 76), (43, 76), (44.5, 82), (43, 89), (27, 89), (25.5, 82)])
shoe_L, shoe_R = LR([(22, 89), (44, 88.5), (46.5, 91), (46.5, 96), (19, 96), (19, 92)])


def interior(mask):
    """mask pixels currently not black on canvas"""
    return [[mask[y][x] and B.canvas[y][x] is not None and B.canvas[y][x] != BLACK for x in range(W)] for y in range(H)]

def muscle(mask, parent, R=3, ramp='gskin', th=None, crease=(), crease_col='b', vbias=0.15, lift=0):
    th = th or TH_SOFT
    inner = interior(parent)
    m = [[mask[y][x] and inner[y][x] for x in range(W)] for y in range(H)]
    idx = shade_part(m, R, th, vbias)
    rp = [hexc(c) for c in B.RAMPS[ramp]]
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                B.canvas[y][x] = rp[max(0, min(idx[y][x] - lift, len(rp) - 1))]
    cc = PALC[crease_col] if crease_col in PALC else hexc(crease_col)
    for (dx, dy) in crease:
        pts = []
        for y in range(H):
            for x in range(W):
                if inner[y][x] and not m[y][x]:
                    xx, yy = x - dx, y - dy
                    if 0 <= xx < W and 0 <= yy < H and m[yy][xx]:
                        pts.append((x, y))
        for x, y in pts:
            B.canvas[y][x] = cc

def mir(m):
    return m, mirror_mask(m)

def U(a, b): return union(a, b)


arm_all = union(U(uarm_L, uarm_R), U(farm_L, farm_R), U(delt_L, delt_R))
legs_all = U(U(calf_L, calf_R), U(thigh_L, thigh_R))
pec_L, pec_R = LR([(47.5, 31), (40, 30.5), (33, 31.5), (29, 34), (28, 38), (30, 42), (35, 44.5), (41, 45), (47.5, 43)])
trap_L, trap_R = LR([(42.5, 26), (41, 29), (35, 30.5), (29.5, 32), (31, 33.5), (38, 32.5), (43, 31)])
abs_blocks = []
for cy, hh in ((47.5, 3.2), (51.3, 3.2), (55.0, 3.0)):
    l = poly_mask(rot_rect(43.5, cy, 7.2, hh, 0, ch=1))
    abs_blocks += [l, mirror_mask(l)]
obl_L, obl_R = LR([(29, 42), (33, 45), (38, 49), (38.5, 57), (35, 55), (30.5, 49)])
dl_L, dl_R = mir(rot_ell_mask(23.5, 36.5, 7.5, 6.5, -35))
bic_L, bic_R = mir(rot_ell_mask(16.5, 44.5, 7.5, 4.3, 132))
fore_L, fore_R = mir(rot_ell_mask(19, 55, 9.5, 4.8, 24))
quad_L, quad_R = mir(rot_ell_mask(33.5, 69, 4.8, 8, -8))
vmo_L, vmo_R = mir(ell_mask(41, 73, 4, 4))
knee_L, knee_R = mir(ell_mask(36, 78.5, 5, 2.5))
calfb_L, calfb_R = mir(rot_ell_mask(31, 82.5, 4, 5, 10))
sock_L, sock_R = LR([(24, 81), (46, 81), (46, 90), (24, 90)])

def anat_legs():
    muscle(U(quad_L, quad_R), legs_all, R=3, crease=((1, 0), (-1, 0)), crease_col='c')
    muscle(U(vmo_L, vmo_R), legs_all, R=2, crease=((0, 1),), crease_col='c')
    muscle(U(calfb_L, calfb_R), legs_all, R=2, crease=((0, -1),), crease_col='c')
    muscle(U(sock_L, sock_R), legs_all, R=3, ramp='sock', crease=((0, -1),), crease_col='k', lift=1)

def anat_torso():
    muscle(U(trap_L, trap_R), torso, R=2, crease=((0, 1),), crease_col='c')
    muscle(U(pec_L, pec_R), torso, R=4, crease=((0, 1),), crease_col='a')
    stamp('''
c
c
c
c
c
c
c
c
c
b
b
b
''', 47, 32, mirror=False)
    stamp('''
c
c
c
c
c
c
c
c
c
b
b
b
''', 47, 32, mirror=True)
    for blk in abs_blocks:
        muscle(blk, torso, R=2, crease=((0, 1), (1, 0), (-1, 0)), crease_col='c')
    muscle(U(obl_L, obl_R), torso, R=2, crease=((1, 0), (-1, 0)), crease_col='c')

def anat_arms():
    muscle(U(dl_L, dl_R), arm_all, R=4, crease=((0, 1), (1, 1), (-1, 1)), crease_col='b')
    muscle(U(bic_L, bic_R), arm_all, R=3, crease=((1, 0), (-1, 0)), crease_col='c')
    muscle(U(fore_L, fore_R), arm_all, R=3, crease=((0, -1),), crease_col='c')

def render(clip=True):
    for y in range(H):
        for x in range(W):
            B.canvas[y][x] = None
    render_part('leg', legs_all, 'gskin', R=6, th=TH_SOFT)
    anat_legs()
    render_part('shoe', U(shoe_L, shoe_R), 'shoe', R=3, th=TH_SOFT, shadow_below=1)
    render_part('torso', torso, 'gskin', R=9, th=TH_SOFT)
    anat_torso()
    render_part('trunks', trunks, 'trunks', R=4, th=TH_SOFT, shadow_below=1)
    stamp(M.Y_EMB, 43, 58)
    render_part('arm', arm_all, 'gskin', R=6, th=TH_SOFT)
    anat_arms()
    render_part('fist', U(fist_L, fist_R), 'gskin', R=4, th=TH_SOFT)
    FG = '''
............
...++++++...
............
...b..b..b..
...b..b..b..
...b..b..b..
....a..a..a.
'''
    stamp(FG, 25, 57); stamp(FG, 25, 57, mirror=True)
    render_part('ear', U(ear_L, ear_R), 'gskin', R=2, th=TH_SOFT)
    M.face_detail()
    if clip:
        from pngio import read_png
        _, _, mech = read_png('rebuilt.png')
        removed = [[B.canvas[y][x] is not None and mech[y][x][3] == 0 for x in range(W)] for y in range(H)]
        for y in range(H):
            for x in range(W):
                if removed[y][x]:
                    B.canvas[y][x] = None
        for y in range(H):
            for x in range(W):
                if B.canvas[y][x] is None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H and removed[yy][xx]:
                        B.canvas[y][x] = BLACK
    snap = [row[:] for row in B.canvas]
    return snap

def dump(x0, y0, w, h):
    cols = {hexc(c): str(i) for i, c in enumerate(B.RAMPS['gskin'])}
    cols[BLACK] = 'k'
    print('    ' + ''.join(str((x0 + i) % 10) for i in range(w)))
    for y in range(y0, y0 + h):
        print('%3d ' % y + ''.join(('.' if B.canvas[y][x] is None else cols.get(B.canvas[y][x], '?')) for x in range(x0, x0 + w)))

if __name__ == '__main__':
    render()
    import sys
    if len(sys.argv)>1: dump(0,24,49,72)
    save('gbig.png'); save('gbig_8x.png', 8, (120, 160, 120, 255))
