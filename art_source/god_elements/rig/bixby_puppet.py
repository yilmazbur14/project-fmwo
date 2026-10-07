"""BIXBY's puppet: a recipe for the approved puppet treatment (the scratch copy of jp_core, take B), in the
shape of the roster's own (jp_bosses.Boss), run on his live flight sheet Bixby/bixby_beast_fly.png (192x160,
frames 0-1: wings up, wings down). The twin rule holds: same frame, same silhouette, pure-black keyline,
no semi-alpha, every colour mapped. Two takes of his FUR for approval:
  ash   - his red fur goes dead ash like every puppet's skin; the red lives on in the blood-dipped ear flames,
          the collar, the wing membranes and the tongue (recommended: it reads as the family)
  blood - his fur stays red (blood ramp); the ear flames burn out to bone, the collar goes iron
"""
from ge_common import *

SHEET = 'Bixby/bixby_beast_fly.png'
FWB, FHB = 192, 160

COMMON = '''
line   K   000000
# cream: blaze, muzzle, chest fluff, legs, tail tip -> bone
cream  B1  FFF6E6
cream  A5  E3D2BC
cream  A4  B09A8E
cream  A3  74606E
# the dark body, the wing frames and the tail -> pitch (the purple rim light -> ash)
pitch  D2  362A3E
pitch  P1  221A28 120D16 1E0C16
pitch  A2  4E3F5A
pitch  A3  7A5AAE
pitch  A4  A98AE6
# the wing membranes -> blood
wing   R2  5E1C30
wing   R1  3A1424
# the tongue -> blood
tongue R3  E0561A
tongue R4  FF8C2E
tongue R2  9A2A10
# the eyes burn rune blue (take B glow)
eye    G1  36C487
eye    G2  0F4A38
eye    B1  B6FFDC
# the headband and its tails -> bone (as Liam's puppet's), the plate's top edge -> bone highlight
band   A5  B3C0C9
band   A4  7B8893
band   A3  4A5563
metal  B1  EEF4F7
# the collar spikes (gold) -> bone
spike  B1  FFE488
spike  A5  E0A632
spike  A4  A66C1A
spike  A3  5C360C
'''
TAKES = {
    'ash': COMMON + '''
fur    P1  2C0610
fur    D2  570C18
fur    A2  87151F
fur    A3  B42424
fur    A4  DE4E2C
flame  R3  FF8C45
flame  R4  FFC45A
collar R2  6E1230
collar R3  A4203E
collar R1  3E0A1E
collar R4  D04A5A
''',
    'blood': COMMON + '''
fur    P1  2C0610
fur    R1  570C18
fur    R2  87151F
fur    R3  B42424
fur    R4  DE4E2C
flame  A5  FF8C45
flame  B1  FFC45A
collar I2  6E1230
collar I3  A4203E
collar P1  3E0A1E
collar B1  D04A5A
''',
}
# inside the mouths the fur darks are the mouth: blood deep; the plate on the middle brow is iron, as Liam's
MOUTH = '''
mouth  R1  2C0610
mouth  R2  570C18
'''
PLATE = '''
metal  I3  B3C0C9
metal  I2  7B8893
metal  P1  4A5563
'''
PARTS = {
    'mid_head': {'box': (76, 4, 132, 84), 'radius': 8, 'min': 0.6},
    'mid_face': {'box': (84, 24, 124, 60), 'radius': 8, 'min': 0.6},
    'crown': {'box': (88, 8, 120, 24), 'radius': 8, 'min': 0.6},
    'head_l': {'box': (18, 42, 62, 96), 'radius': 8, 'min': 0.55},
    'head_r': {'box': (142, 46, 188, 100), 'radius': 8, 'min': 0.55},
    'chest': {'box': (80, 98, 120, 132), 'radius': 8, 'min': 0.6},
    'paw_l': {'box': (62, 112, 86, 148), 'radius': 8, 'min': 0.6},
    'paw_r': {'box': (120, 112, 152, 148), 'radius': 8, 'min': 0.6},
    'hind_l': {'box': (16, 112, 44, 148), 'radius': 8, 'min': 0.6},
    'hind_r': {'box': (138, 118, 158, 150), 'radius': 8, 'min': 0.6},
    'wing_l': {'box': (12, 2, 70, 40), 'radius': 6, 'min': 0.6},
    'wing_r': {'box': (136, 2, 192, 40), 'radius': 6, 'min': 0.6},
}
REGIONS = [
    {'name': 'mouth_mid', 'part': 'mid_head', 'boxes': [(88, 58, 118, 84)], 'table': MOUTH},
    {'name': 'mouth_l', 'part': 'head_l', 'boxes': [(28, 74, 54, 94)], 'table': MOUTH},
    {'name': 'mouth_r', 'part': 'head_r', 'boxes': [(150, 78, 178, 98)], 'table': MOUTH},
    {'name': 'plate', 'part': 'crown', 'boxes': [(95, 11, 115, 21)], 'table': PLATE},
]


def overlays():
    seam = {}
    for y in range(104, 127):
        seam[(99, y)] = '2'
    for y in range(105, 126, 3):
        seam[(98, y)] = 'S'
        seam[(100, y)] = 'S'
    scar = {}
    for x in range(113, 124):
        scar[(x, 45 + (x - 113) // 4)] = '2'
    for x in range(114, 124, 3):
        scar[(x, 44 + (x - 113) // 4)] = 'S'
        scar[(x, 46 + (x - 113) // 4)] = 'S'
    return [JB.ov('chest_seam', 'chest', seam, on=('cream',)),
            JB.ov('cheek_scar', 'mid_face', scar, on=('fur',))]


HOOKS = {
    'head': JB.ring_hook('crown', 104, 25),
    'head_l': JB.ring_hook('head_l', 38, 52),
    'head_r': JB.ring_hook('head_r', 160, 57),
    'back': JB.back_hook('chest', 104, 96, fallback=('mid_head',)),
    'wrist_l': JB.ring_hook('paw_l', 74, 130),
    'wrist_r': JB.ring_hook('paw_r', 135, 130),
    'knee_l': JB.ring_hook('hind_l', 30, 126),
    'knee_r': JB.ring_hook('hind_r', 147, 133),
    'wing_l': JB.ring_hook('wing_l', 26, 14),
    'wing_r': JB.ring_hook('wing_r', 174, 13),
}
TATTER = [
    # the wing membranes' edges, torn (inner: where a membrane's hem lies over a head or the body, that shows
    # through the notch)
    {'part': 'wing_l', 'mats': ('wing',), 'centre_x': 40, 'seed': 5, 'depth': 3, 'keep': 2, 'spacing': (3, 6),
     'depths': (1, 2, 3), 'inner': True},
    {'part': 'wing_r', 'mats': ('wing',), 'centre_x': 164, 'seed': 9, 'depth': 3, 'keep': 2, 'spacing': (3, 6),
     'depths': (1, 2, 3), 'inner': True},
]


def detached(src):
    """The source frame's detached motes and speed streaks (every 8-connected piece but the body): they keep
    their colour and get no keyline (the twin rule's FX motes, generalised past 4 px for his speed lines)."""
    op = src[:, :, 3] > 0
    H, W = op.shape
    lab = np.zeros(op.shape, int)
    n = 0
    sizes = {}
    for y0, x0 in zip(*np.nonzero(op)):
        if lab[y0, x0]:
            continue
        n += 1
        stack = [(x0, y0)]
        lab[y0, x0] = n
        cnt = 0
        while stack:
            x, y = stack.pop()
            cnt += 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    u, v = x + dx, y + dy
                    if 0 <= u < W and 0 <= v < H and op[v, u] and not lab[v, u]:
                        lab[v, u] = n
                        stack.append((u, v))
        sizes[n] = cnt
    big = max(sizes, key=sizes.get)
    return {(int(x), int(y)) for y, x in zip(*np.nonzero(op & (lab != big)))}


def streaks(src):
    """His speed lines where they touch his body: one-texel-tall horizontal runs (3+ texels, not keyline) with
    air above and below. With the detached ones they are FX: recoloured by the table, never keylined."""
    op = src[:, :, 3] > 0
    H, W = op.shape
    blk = op & (src[:, :, 0] == 0) & (src[:, :, 1] == 0) & (src[:, :, 2] == 0)
    thin = np.zeros_like(op)
    thin[1:-1] = op[1:-1] & ~op[:-2] & ~op[2:] & ~blk[1:-1]
    out = set()
    for y in range(H):
        x = 0
        while x < W:
            if thin[y, x]:
                x1 = x
                while x1 < W and thin[y, x1]:
                    x1 += 1
                if x1 - x >= 3:
                    out |= {(xx, y) for xx in range(x, x1)}
                x = x1
            else:
                x += 1
    return out


def boss(take, fx=()):
    return JB.Boss('bixby_' + take, 'Bixby (%s fur)' % take, SHEET, (FWB, FHB), (96, 159), [0], TAKES[take],
                   parts=PARTS, overlays=overlays(), hooks=HOOKS, tatter=TATTER, regions=REGIONS, fx_specks=fx)


def build(take, frames=(0, 1)):
    key = C.frame(SHEET, FWB, FHB, 0)
    out, infos = [], []
    for f in frames:
        src = C.frame(SHEET, FWB, FHB, f)
        b = boss(take, detached(src) | streaks(src))
        # the wing rings are left off: the down-stroke frame cannot place them (the roster's all-or-nothing rule)
        im, info = C.treat(b, src, TAKE, key_src=key, sheet_rel=SHEET, frame_no=f, skip_rings=('wing_l', 'wing_r'))
        a = np.array(im)
        info['src'] = src
        info['fx'] = b.fx_specks
        out.append(a)
        infos.append(info)
    return out, infos


def audit(frames, infos):
    probs = []
    pal = {tuple(v) for v in PUP.values()}
    for f, (a, info) in enumerate(zip(frames, infos)):
        src = info['src']
        if ((a[:, :, 3] > 0) != (src[:, :, 3] > 0)).any():
            probs.append('f%d silhouette differs' % f)
        if ((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).any():
            probs.append('f%d semi-alpha' % f)
        fx = info['fx']
        cols = {tuple(a[y, x]) for y, x in zip(*np.nonzero(a[:, :, 3] > 0)) if (x, y) not in fx}
        if cols - pal:
            probs.append('f%d off-palette %s' % (f, sorted(cols - pal)[:4]))
        for k in ('gaps', 'lone', 'holes', 'bad_keys', 'silhouette', 'edge_black_lost'):
            if info['lint'].get(k):
                probs.append('f%d lint %s %d %s' % (f, k, len(info['lint'][k]), info['lint'][k][:4]))
        if info['unknown']:
            probs.append('f%d unmapped %s' % (f, info['unknown']))
    return probs


if __name__ == '__main__':
    for take in ('ash', 'blood'):
        frames, infos = build(take)
        for f, info in enumerate(infos):
            print(take, 'f%d' % f, 'parts', {k: v[3] for k, v in info['parts'].items()})
            print('    hooks', info['hooks'], '| skipped', info['skipped'], '| tatter', info.get('tatter'),
                  '| nudged', info.get('nudged'), '| clipped', info.get('clipped'), '| fx px', len(info['fx']))
            s = stats(frames[f])
            print('    black %.1f%% colours %d semi %d' % (100 * s['black'], s['colours'], s['semi']))
        print(take, 'PROBLEMS', audit(frames, infos))
        im = Image.fromarray(strip(frames), 'RGBA')
        im.save(os.path.join(LOOK, 'bixby_puppet_%s_draft.png' % take))
        up(im, 3, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'bixby_puppet_%s_draft_3x.png' % take))
