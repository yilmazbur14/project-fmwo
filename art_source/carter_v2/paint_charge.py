"""Charge-down key pose (frame 1), hand-authored as back-to-front layers.
Each layer: {y: [(x_start, chars)]}; '.' inside a string means 'leave as is'."""
from lib import *

SPEED = [  # (x, y_top, y_bottom, width): streaks trailing up off the head/shoulders of a downward charge
    (9, 5, 19, 2), (14, 10, 19, 1), (18, 3, 15, 1), (27, 0, 7, 1), (36, 1, 8, 1), (44, 2, 14, 1),
    (49, 3, 18, 2), (55, 8, 18, 1), (2, 17, 34, 1), (62, 17, 33, 1), (13, 47, 57, 1), (51, 48, 59, 1),
]

L_BOOT_BACK = {
    55: [(36, "############")],
    56: [(36, "#gggggggggq#")],
    57: [(36, "#qkkkkkkkKK#")],
    58: [(36, "#qkkkkkkkKK#")],
    59: [(36, "#qkkkkkkkkKK#")],
    60: [(36, "#qkkkkkkkkKK#")],
    61: [(35, "#kkkkkkkkkkkKK#")],
    62: [(35, "#qqqqqqqqqqqgK#")],
    63: [(35, "###############")],
}
L_LEG_BACK = {
    49: [(33, "#mmmmmmmmmmm#")],
    50: [(34, "#smmmmmmmmdd#")],
    51: [(35, "#smmmmmmmdD#")],
    52: [(35, "#smmmmmmmdD#")],
    53: [(36, "#smmmmmmdD#")],
    54: [(36, "#mmmmmmmdD#")],
}
L_BOOT_FRONT = {
    54: [(18, "#kkkkkkkkkkkkkk#")],
    55: [(18, "#ggggggggggggqq#")],
    56: [(18, "#qkkkkkkkkkkkKK#")],
    57: [(18, "#qkkkkkkkkkkkKK#")],
    58: [(18, "#ggqqqqqqqqqqqK#")],
    59: [(19, "#KKKKKKKKKKKK#")],
    60: [(20, "############")],
}
L_LEG_FRONT = {
    47: [(20, "#sssssssssss#")],
    48: [(19, "#Hsssssssssmd#")],
    49: [(19, "#Hssssssssssmd#")],
    50: [(18, "#HHsssssssssmmd#")],
    51: [(18, "#HssHHssssmmddD#")],
    52: [(18, "#sssHHHsssmmmdD#")],
    53: [(18, "#msssssssmmmdD#")],
    54: [(18, "##dmmmmmmmdDD##")],
    55: [(20, "###########")],
}
L_SPEEDO = {
    44: [(22, "##########################")],
    45: [(21, "#BBBBBBBBBBbbbbbbbbbbbbbbu#")],
    46: [(21, "#uuuuuuuuuuuuuuuuuuuuuuuUU#")],
    47: [(21, "#bBBbbbbbbbbbbbbbbbuuuuuuU#")],
    48: [(21, "#bBbbbbbbbbbbbbbbuuuuuuUUU#")],
    49: [(22, "#bbbbbbbbbbbbbuuuuuuuUUU#")],
    50: [(24, "###ubbbbbbuuuuuUU###")],
    51: [(27, "##############")],
}
L_TORSO = {
    16: [(43, "#")],
    17: [(20, "#"), (43, "d#")],
    18: [(18, "##H"), (43, "md##")],
    19: [(15, "###H"), (45, "md##")],
    20: [(12, "###HHs"), (46, "d")],
    26: [(42, "d")],
    27: [(41, "dd")],
    28: [(41, "md")],
    29: [(40, "smd")],
    30: [(40, "ssmd")],
    31: [(24, "D"), (39, "dssmmd")],
    32: [(24, "D"), (39, "dssmmmd")],
    33: [(24, "DD"), (38, "dsssmmmmdd")],
    34: [(24, "DD"), (38, "dssssmmmmdD")],
    35: [(23, "DDDD"), (37, "dDdddddddmdddD")],
    36: [(22, "DDDDDD"), (36, "DsmdmmmdmmdmdD#")],
    37: [(21, "D"), (35, "DHssmdmmmdmmmdD#")],
    38: [(34, "dddddDdmmmdmmmdD#")],
    39: [(30, "D"), (33, "dHsssmdmmmdmmmdD#")],
    40: [(29, "DDD"), (32, "dsssssmdmmmdmmmdD#")],
    41: [(29, "DDD"), (32, "ddddddDdmmmdmmdD##")],
    42: [(28, "DDDD"), (32, "dsssssmdmmmdmdD#")],
    43: [(20, "DDdddmmmmmmm"), (32, "msssssmdmmmdmD#")],
}
L_ARM_TRAIL = {
    20: [(47, "#######")],
    21: [(45, "##sssssmm##")],
    22: [(45, "#sssssmmmmd#")],
    23: [(45, "#sssmmmmmmdd#")],
    24: [(44, "#dssmmmmmmmdd#")],
    25: [(43, "#dsmmmmmmmmmdd#")],
    26: [(43, "#dmmmmmmmmmmdd#")],
    27: [(43, "#dmmmmmmmmmddD#")],
    28: [(43, "#ddmmmmmmmmddD#")],
    29: [(43, "#DddmmmmmmdddD#")],
    30: [(44, "#DdddmmmmdddD#")],
    31: [(45, "#DsmmmmmmddDD#")],
    32: [(46, "##smmmmmmddD#")],
    33: [(48, "#smmmmmmddD#")],
    34: [(49, "##smmmmmdD#")],
    35: [(51, "#smmmmmdD#")],
    36: [(52, "#smmmmddD#")],
    37: [(53, "#smmmddD#")],
    38: [(54, "#smmddD#")],
    39: [(54, "########")],
    40: [(53, "#smdmdmd#")],
    41: [(53, "#smmmmmdD#")],
    42: [(53, "#dmdmdmdD#")],
    43: [(53, "#mdmdmddD#")],
    44: [(54, "#DdDdDD#")],
    45: [(55, "######")],
}
L_DELT_LEAD = {
    21: [(10, "########")],
    22: [(8, "##HHHHHHHs#")],
    23: [(7, "#HHHHHHHsss#")],
    24: [(6, "#HHHHHHssssmd#")],
    25: [(5, "#HHHHHsssssssmd#")],
    26: [(5, "#HHHHssssssssssmd#")],
    27: [(5, "#HHHsssssssssssmmd#")],
    28: [(4, "#HHHsssssssssssmmdD#")],
    29: [(4, "#HHsssssssssssmmmddD#")],
    30: [(4, "#HsssssssssssmmmmddD#")],
    31: [(4, "#HssssssssssmmmmddD#")],
    32: [(4, "#ssssssssssmmmmdddD#")],
    33: [(5, "#ssssssssmmmmddddD#")],
    34: [(5, "#mssssssmmmmmdddDD#")],
    35: [(5, "#mmsssmmmmmmdddDD#")],
    36: [(6, "#mmmmmmmmdddDDD#")],
    37: [(7, "#dmmmmmdddDDD#")],
    38: [(8, "#ddddddDDDD#")],
    39: [(9, "##########")],
}
L_HEAD = {
    10: [(28, "########")],
    11: [(25, "###HHHHHHsm###")],
    12: [(23, "##HHHWWWWWWHssmm##")],
    13: [(22, "#HHWWWWHHHHsssssmmd#")],
    14: [(22, "#HWWHHssssssssssmmd#")],
    15: [(21, "#HWHHHsssssssssssmmmd#")],
    16: [(21, "#HHHHssssssssssssmmmd#")],
    17: [(21, "#HHHsssssssssssssmmmd#")],
    18: [(21, "#HHssssssssssssssmmmd#")],
    19: [(21, "#Hsssssssssssssssmmmd#")],
    20: [(21, "#Hssssssssssssssmmmmd#")],
    21: [(21, "#HsRRRsssssssssmRRRmd#")],
    22: [(21, "#rs##RRRRssmsRRRR##mR#")],
    23: [(21, "#rmmm#####Hm#####dddR#")],
    24: [(21, "#or######mHdm######rR#")],
    25: [(22, "#rWWiWW#msdm#WWiWWR#")],
    26: [(22, "#omdddmmmsmdmdddddr#")],
    27: [(23, "#OmmdoOOoorrrdddR#")],
    28: [(23, "#OooOOooRrrrrRRrR#")],
    29: [(24, "#Oorr######RRrR#")],
    30: [(24, "#OoooodddDrrrrR#")],
    31: [(25, "#oOooOoorrrRR#")],
    32: [(25, "#ooOooOorrRrR#")],
    33: [(26, "#oOooOorrRR#")],
    34: [(26, "#oOooOorRrR#")],
    35: [(27, "#oOooorrR#")],
    36: [(28, "#oOorrR#")],
    37: [(29, "#oOrR#")],
    38: [(30, "#oR#")],
    39: [(31, "##")],
}
L_EARS = {
    19: [(19, "##"), (43, "##")],
    20: [(18, "#Hs#"), (42, "#mm#")],
    21: [(18, "#smd"), (42, "Ddm#")],
    22: [(18, "#sdm"), (42, "dDm#")],
    23: [(18, "#sdm"), (42, "dDm#")],
    24: [(18, "#sm#"), (42, "#dm#")],
    25: [(19, "#s#"), (42, "#m#")],
    26: [(20, "##"), (42, "##")],
}
L_EARRING = {
    27: [(19, "#c#")],
    28: [(18, "#CcC#")],
    29: [(19, "#C#")],
    30: [(20, "#")],
}
L_FOREARM = {
    37: [(17, "####")],
    38: [(14, "###HHH")],
    39: [(11, "###HHHsss")],
    40: [(9, "##HHHssssss")],
    41: [(8, "#HHssssssmmm")],
    42: [(8, "#Hssssmmmddd#")],
    43: [(8, "#dmmmmdddD##")],
    44: [(9, "#dddDD##")],
    45: [(10, "#####")],
}
L_FIST = {  # knuckles-forward fist, wider than tall, in line with the forearm
    37: [(22, "#######")],
    38: [(20, "##HHHsssm#")],
    39: [(20, "#HHsHsHsm#")],
    40: [(20, "#sdsdsdsd#")],
    41: [(20, "#dDdDdDdD#")],
    42: [(20, "#ssmsmsmd#")],
    43: [(21, "#mdmdmdD#")],
    44: [(22, "#######")],
}

LAYERS = [L_BOOT_BACK, L_LEG_BACK, L_BOOT_FRONT, L_LEG_FRONT, L_SPEEDO, L_TORSO, L_ARM_TRAIL, L_DELT_LEAD,
          L_HEAD, L_EARS, L_EARRING, L_FOREARM, L_FIST]


def speed_layer(g):
    for x, a, b, w in SPEED:
        n = b - a + 1
        for i, y in enumerate(range(a, b + 1)):
            t = i / max(1, n - 1)          # 0 = far (top) end, 1 = next to the body
            g[y][x] = 'L' if t < 0.25 else ('F' if t < 0.55 else 'f')
            if w == 2 and t >= 0.4:
                g[y][x + 1] = 'L' if t < 0.6 else 'F'


def paint(layers, with_speed=True):
    g = blank()
    errs = []
    if with_speed:
        speed_layer(g)
    for li, layer in enumerate(layers):
        for y, segs in layer.items():
            seen = set()
            for x0, s in segs:
                for i, c in enumerate(s):
                    x = x0 + i
                    if not (0 <= x < 64):
                        errs.append('layer %d row %d x=%d out of range' % (li, y, x)); continue
                    if x in seen:
                        errs.append('layer %d row %d x=%d overlap' % (li, y, x))
                    seen.add(x)
                    if c == '.':
                        continue
                    if c not in PAL:
                        errs.append('layer %d row %d bad char %r' % (li, y, c)); continue
                    g[y][x] = c
    return g, errs


if __name__ == '__main__':
    g, errs = paint(LAYERS)
    for e in errs:
        print('ERR', e)
    save_grid(os.path.join(HERE, 'charge.txt'), g)
    save(os.path.join(HERE, 'charge_8x.png'), zoom(grid_to_pix(g), 8))
    save(os.path.join(HERE, 'charge_1x.png'), grid_to_pix(g))
    print('ok', len(errs), 'errors')
