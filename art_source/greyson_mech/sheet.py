import sys, math
import rig, fx as FX
from rig import pose, arm_from_joints, st, ARM0, FIST, W, H
from pngio import write_png, scale, blank, paste

S = (20.35, 37.05)
BG = (120, 160, 120, 255)

SPARK_S = ".r.\nrPr\n.r."
SPARK_L = "..r..\n..P..\nrPPPr\n..P..\n..r.."
SPARK_X = "r...r\n.rPr.\n.PPP.\n.rPr.\nr...r"
FLARE = "...r...\n..rPr..\n.rP0Pr.\nrP000Pr\n.rP0Pr.\n..rPr..\n...r..."

ARC1 = "r...\n.r..\n.Pr.\n..P.\n..rr\n....r"
ARC2 = "..r\n.r.\nrP.\n.P.\n..r\n.r."
ARC3 = "...r\n..r.\n.P..\nrPr.\n...r"

ROCKET_T = """.kk.....
kRRk....
kPRXk...
.kRXXk..
.kWWik..
..kWWik.
..kWiik.
...kXXVk
...kWijk"""
FLASH = "...2...\n.2.1.2.\n..101..\n2100012\n..101..\n.2.1.2.\n...2..."
FLASH_L = "....2....\n.2..1..2.\n..21012..\n..10001..\n210000012\n..10001..\n..21012..\n.2..1..2.\n....2...."
PUFF_A = "..kkk..\n.k667k.\nk66677k\nk67778k\n.k788k.\n..kkk.."
PUFF_B = ".kk..\nk67k.\nk678k\n.k8k.\n..k.."

def rack_rockets(cx, cy, a_deg):
    """ROCKET_T stamps sitting in the rack's top edge (left coords, pre-body offset)."""
    a = math.radians(a_deg)
    out = []
    for sx in (-5.5, -0.5, 4.5):
        px = cx + sx * math.cos(a) - (-5.5) * math.sin(a)
        py = cy + sx * math.sin(a) + (-5.5) * math.cos(a)
        out.append((round(px - 4.5), round(py - 7), ROCKET_T))
    return out

def legs(h, spread=0.6, kdrop=0.45):
    """crouch legs: hip drops h, knees splay out, feet planted."""
    kdx, kdy = -spread * h, kdrop * h
    thigh = [(33, 59 + h), (46, 60 + h), (46 + kdx * 0.3, 67 + (h + kdy) / 2), (43 + kdx, 76 + kdy),
             (29 + kdx, 77 + kdy), (27 + kdx * 0.7, 69 + (h + kdy) / 2), (29 + kdx * 0.3, 63 + h * 0.8)]
    knee = (35 + kdx, 77 + kdy, 7, 5)
    shin = [(27 + kdx, 79 + kdy), (43 + kdx, 79 + kdy), (45 + kdx * 0.5, 84 + kdy * 0.5), (46, 90), (24, 90),
            (23 + kdx * 0.5, 84 + kdy * 0.5)]
    return dict(thigh_poly=thigh, knee=knee, shin_poly=shin,
                boot_seam=(round(28 + kdx * 0.5), round(82 + kdy * 0.5)))

SWEAT = ".k.\nkik\nk0k\n.k."

def mirror_grid(g):
    NL = chr(10)
    return NL.join(r[::-1] for r in g.split(NL))

def debris_chest(cx, cy, level='off'):
    def f():
        rig.render_part('chestplate', rig.ell_mask(cx, cy, 13.5, 10.5), 'metal', R=7, th=rig.TH_METAL, shadow_below=0)
        st(rig.CHEST_EYE, round(cx - 10), round(cy - 8.5), level=level)
        st(mirror_grid(rig.CHEST_EYE), round(cx + 4), round(cy - 8.5), level=level)
        st(rig.GRIN, round(cx - 10), round(cy - 1.5), level=level)
    return f

def debris_pod(cx, cy, ang, mirror=False):
    def f():
        m = rig.poly_mask(rig.rot_rect(cx, cy, 18, 11, ang, ch=1))
        if mirror:
            m = rig.mirror_mask(m)
        rig.render_part('pod', m, 'dark', R=3, th=rig.TH_METAL, shadow_below=0)
        rig.pod_detail_one(m, cx, cy, ang, mirror)
    return f

def debris_paul(cx, cy, ang, mirror=False):
    def f():
        rig.draw_pauldron(cx, cy, ang, mirror)
    return f

SMOKE = ('7', '8', '9')
DSMOKE = ('6', '7', '8', '9', '9')

def wires(by):
    return FX.pixels([(44, 44 + by, '3'), (44, 45 + by, '3'), (45, 46 + by, '3'), (45, 47 + by, '4'),
                      (51, 43 + by, '2'), (52, 44 + by, '2'), (52, 45 + by, '2'), (51, 46 + by, '3'),
                      (48, 42 + by, '7'), (48, 43 + by, '8'), (49, 44 + by, '7')], pair=False)

def socket(by):
    def f():
        rig.render_part('elbow', rig.ell_mask(21, 36.5 + by, 5.5, 5.0), 'dark', R=4, th=rig.TH_METAL, shadow_below=0)
        rig.render_part('elbow', rig.ell_mask(21, 36.5 + by, 2.5, 2.2), 'shoe', R=2, th=rig.TH_METAL, shadow_below=0)
    return f

def pod_top(cx, cy, a_deg, ox=0, oy=0):
    a = math.radians(a_deg)
    return (cx + ox + 5.5 * math.sin(a), cy + oy - 5.5 * math.cos(a)), (math.sin(a), -math.cos(a))

def fxs(*items):
    """items: (grid, x, y, mirror_pair)"""
    def f():
        for g, x, y, pair in items:
            st(g, x, y)
            if pair:
                st(g, x, y, mirror=True)
    return f

def idle(i):
    by = [0, 1, 2, 1][i]
    glow = [1, 2, 1, 0][i]
    ant = [0, -1, 0, 1][i]
    A = dict(ARM0, muzzle=glow)
    return pose(body=(0, by), pelvis=(0, by // 2), glow_chest=glow, glow_ant=glow, antenna=ant, armL=A)

def laser_arm(kind, muzzle):
    if kind == 'swing':
        return arm_from_joints(S, (10, 46), (28, 58), 0, muzzle)
    if kind == 0:
        return arm_from_joints(S, (10, 41), (26, 53), 0, muzzle)
    if kind == 45:
        return arm_from_joints(S, (12, 46.5), (28, 56), 45, muzzle)
    if kind == 90:
        return arm_from_joints(S, (16, 50), (30, 60), 90, muzzle)

def frames():
    F = []
    for i in range(4):
        F.append(idle(i))
    # 4 laser charge: anticipation dip, arms swinging out
    F.append(pose(body=(0, 2), pelvis=(0, 1), face='grit', glow_chest=2, glow_ant=2, antenna=-1,
                  armL=laser_arm('swing', 2),
                  fx=[fxs((ARC2, 1, 37, True), (SPARK_S, 5, 55, True))]))
    # 5 laser charge: arms out, flare
    F.append(pose(body=(0, -1), pelvis=(0, 0), face='shout', glow_chest=3, glow_ant=3, antenna=1,
                  armL=laser_arm(0, 3),
                  fx=[fxs((ARC1, 0, 28, True), (ARC3, 3, 49, True), (SPARK_S, 10, 33, True))]))
    # 6-8 laser fire
    F.append(pose(body=(0, -1), face='shout', glow_chest=3, glow_ant=3, antenna=0,
                  armL=laser_arm(0, 3), fx=[fxs((ARC2, 1, 31, True), (ARC1, 1, 49, True))]))
    F.append(pose(body=(0, 0), face='shout', glow_chest=3, glow_ant=3, antenna=-1,
                  armL=laser_arm(45, 3)))
    F.append(pose(body=(0, 1), pelvis=(0, 1), face='shout', glow_chest=3, glow_ant=3, antenna=0,
                  armL=laser_arm(90, 3)))
    # 9 rocket aim: racks rise and tilt outward, body braces
    F.append(pose(body=(0, -1), glow_chest=2, glow_ant=2, antenna=1, pod=(16, 16.5, -24),
                  rockets=rack_rockets(16, 15.5, -24), armL=dict(ARM0, muzzle=2)))
    # 10 launch flash: rockets gone, flash at rack mouths
    (tx, ty), _ = pod_top(16, 16.5, -24, 0, 1)
    F.append(pose(body=(0, 1), pelvis=(0, 1), glow_chest=3, glow_ant=3, antenna=-1, pod=(16, 16.5, -24),
                  rockets=[], armL=dict(ARM0, muzzle=2),
                  fx=[FX.cloud([(tx - 5, ty + 1, 3.2), (tx + 4, ty - 1, 2.6)]),
                      FX.burst(tx - 1.5, ty - 3, 7.5, spikes=8, phase=0.3)]))
    # 11 recoil: body pushed down, racks kicked down, smoke
    F.append(pose(body=(0, 3), pelvis=(0, 1), face='grit', glow_chest=2, glow_ant=2, antenna=1,
                  pod=(16, 18.5, -12), pod_off=(0, 1), rockets=[], armL=dict(ARM0, muzzle=1),
                  fx=[FX.cloud([(10, 11, 4.2), (16, 8, 4.8), (21, 10, 3.6), (13, 5, 3.0)]),
                      FX.pixels([(5, 3, '6'), (24, 1, '6')])]))
    # 12 ground pound anticipation: deep crouch, fists low, head tucked
    F.append(pose(body=(0, 8), head=(0, 1), pelvis=(0, 7), thigh=(0, 0), face='grit', glow_chest=2, glow_ant=2,
                  antenna=-1, armL=arm_from_joints(S, (10, 50), (25, 68), 0, 2), **legs(7)))
    # 13 rise, fists raised overhead (stretch)
    F.append(pose(body=(0, 2), head=(0, -1), pelvis=(0, 2), face='shout', glow_chest=3, glow_ant=3, antenna=1,
                  armL=arm_from_joints(S, (13, 22), (33, 7.5), 0, 2), **legs(1)))
    # 14 SLAM: huge squash, fists on floor
    F.append(pose(body=(0, 12), head=(0, 1), pelvis=(0, 11), face='shout', glow_chest=3, glow_ant=3, antenna=-1,
                  armL=arm_from_joints(S, (10, 54), (28, 77.5), 0, 3),
                  fx=[FX.lines([(6, 22, 3, 36), (3, 36, 2, 50), (10, 26, 7, 38), (7, 38, 6, 48)], '5'),
                      FX.lines([(13, 26, 11, 34)], '6')], **legs(12, 0.7)))
    # 15 hold on impact
    F.append(pose(body=(0, 11), head=(0, 1), pelvis=(0, 10), face='grit', glow_chest=2, glow_ant=2, antenna=1,
                  armL=arm_from_joints(S, (10, 55), (28, 78.5), 0, 2), **legs(11, 0.7)))
    # 16-17 vulnerable: slumped, overheating, steam, pilot winded
    for i in range(2):
        by = 9 + i
        W5 = ('5', '5', '6')
        if i == 0:
            plume = [(29, 36, 3.2), (28, 31, 3.8), (29, 25, 4.3), (27, 19, 4.4), (29, 13, 4.0), (27, 7, 3.2)]
        else:
            plume = [(28, 35, 2.8), (29, 30, 3.6), (27, 24, 4.4), (29, 17, 4.6), (27, 11, 4.2), (29, 4, 3.4)]
        F.append(pose(body=(0, by), head=(0, 1), pelvis=(0, by - 1), face=['winded', 'winded2'][i],
                      glow_chest=[0, 'off'][i], glow_ant='off', antenna=-1, pod=(16, 18.5, -2), pod_off=(0, 4),
                      paul_off=(0, 2), armL=arm_from_joints(S, (14, 58), (19, 87.5 - by), 0, ['heat', 'heat2'][i]),
                      fx_back=[FX.cloud(plume, light=W5, rim='7')],
                      fx_face=[fxs((SWEAT, 35, 22 + by + 2 * i, False), (SWEAT, 57, 26 + by - i, False))],
                      **legs(by - 1, 0.6)))
    # 18 hit flinch
    F.append(pose(body=(0, -1), head=(0, -2), pelvis=(0, 0), face='grimace', glow_chest=2, glow_ant=0, antenna=1,
                  pod_off=(0, -2), paul_off=(0, -1), armL=arm_from_joints(S, (10, 45), (27, 57), 0, 2)))
    # 19 defeat: sparks + smoke, jolt, right rack knocked loose
    F.append(pose(body=(0, 2), head=(0, -1), pelvis=(0, 1), face='grimace', glow_chest=0, glow_ant='off', antenna=1,
                  podR=(16, 15.5, 14, 3, -4), rocketsR=[],
                  armL=arm_from_joints(S, (10, 48), (26, 60), 0, 0),
                  armR=arm_from_joints(S, (10, 52), (28, 62), 0, 'off'),
                  fx_back=[FX.cloud2([(70, 31, 4.5), (73, 25, 5.0), (69, 18, 4.6), (74, 12, 4.0), (70, 7, 3.2)], ramp=DSMOKE)],
                  fx=[
                      FX.burst(62, 46, 5.5, spikes=6, phase=0.2, pair=False, cols=('0', '1', 'G', '2')),
                      FX.burst(27, 32, 4.0, spikes=6, phase=0.9, pair=False, cols=('0', '1', 'G', '2')),
                      FX.burst(8, 55, 3.5, spikes=6, phase=0.5, pair=False, cols=('0', '1', '2', '3'))]))
    # 20 plates falling away
    F.append(pose(body=(0, 6), head=(0, 0), pelvis=(0, 5), face='dazed', glow_chest='off', glow_ant='off', antenna=-1,
                  hide={'chestplate', 'podR'}, paul=(22, 32, -42), paul_off=(-3, -3), paulR=(22, 32, -12, 0, 0),
                  armL=arm_from_joints(S, (12, 56), (21, 76), 0, 'off'),
                  armR=arm_from_joints(S, (10, 54), (25, 72), 0, 'off'),
                  debris=[debris_chest(49, 70, 'off'), debris_pod(15, 7, 42, mirror=True)],
                  fx=[
                      FX.burst(43, 52, 5.0, spikes=6, phase=0.1, pair=False, cols=('0', '1', 'G', '2')),
                      FX.burst(26, 38, 3.5, spikes=6, phase=0.7, pair=False, cols=('0', '1', 'G', '2'))],
                  **legs(5, 0.6)))
    # 21 collapse: kneel, plates hit the floor
    crack = lambda hy: FX.lines([(58, 5 + hy, 56, 8 + hy), (56, 8 + hy, 59, 11 + hy), (59, 11 + hy, 57, 14 + hy)], 'k', pair=False)
    F.append(pose(body=(0, 13), head=(0, 1), pelvis=(0, 12), face='dazed', glow_chest='off', glow_ant='off', antenna=-1,
                  hide={'chestplate', 'paulL', 'podR'},
                  armL=arm_from_joints(S, (13, 58), (20, 75.5), 0, 'off'),
                  armR=arm_from_joints(S, (15, 60), (22, 75.5), 0, 'off'),
                  fx_head_back=[crack(14)],
                  debris=[socket(13), debris_paul(13, 85.5, 4), debris_chest(66, 84.5, 'off'), debris_pod(9, 89.5, -8, mirror=True)],
                  fx_back=[FX.cloud2([(68, 42, 5.5), (73, 34, 6.2), (67, 26, 6.0), (73, 17, 5.4), (68, 10, 4.6), (71, 5, 3.0)], ramp=DSMOKE)],
                  fx=[wires(13),
                      FX.burst(40, 60, 3.5, spikes=6, phase=0.4, pair=False, cols=('0', '1', 'G', '2'))],
                  **legs(12, 0.7)))
    # 22 final wreck (holds)
    F.append(pose(body=(0, 14), head=(0, 1), pelvis=(0, 13), face='ko', glow_chest='off', glow_ant='off', antenna=-1,
                  hide={'chestplate', 'paulL', 'podR'},
                  armL=arm_from_joints(S, (14, 59), (20, 74.5), 0, 'off'),
                  armR=arm_from_joints(S, (15, 60), (22, 74.5), 0, 'off'),
                  fx_head_back=[crack(15)],
                  debris=[socket(14), debris_paul(13, 85.5, 4), debris_chest(66, 84.5, 'off'), debris_pod(9, 89.5, -8, mirror=True)],
                  fx_back=[FX.cloud2([(69, 40, 3.4), (70, 36, 3.6), (70, 32, 3.4), (69, 28, 3.0), (70, 24, 2.6), (71, 20, 2.0), (70, 17, 1.4)], ramp=('5', '6', '7', '7', '8'), rim='8', R=3.0)],
                  fx=[wires(14)],
                  **legs(13, 0.7)))
    return F

def strip(idxs, out, s=6):
    FR = frames()
    imgs = [rig.render(FR[i]) for i in idxs]
    Wt = len(imgs) * 96 * s + (len(imgs) + 1) * 8
    cv = blank(Wt, 96 * s + 16, (70, 90, 76, 255))
    for n, im in enumerate(imgs):
        paste(cv, scale(im, s, BG), 8 + n * (96 * s + 8), 8)
    write_png(out, Wt, 96 * s + 16, cv)
    return imgs

if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2])
    s = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    strip(list(range(a, b + 1)), f'view_{a:02d}_{b:02d}.png', s)
