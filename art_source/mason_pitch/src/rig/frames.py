import rig, props
from rig import BLACK, YEL, YEL_MID, YEL_DEEP, KHAKI, KHAKI_DK, draw_part
from props import limb, pair, STINK

# ---------------------------------------------------------------------------
def foot_piece(side, dx, dy):
    """A standing foot drawn as its own outlined piece, for poses where the legs
    are hidden. Same shape, toes and shading as the approved foot."""
    FOOT = [(42,57),(46,57),(49,58),(51,60),(51,63),(34,63),(34,58),(35,57)]
    toes, outer = (41, 46), (lambda u: u >= 47)
    if side == 'l':
        FOOT = props.mirror_x(FOOT); toes = (22, 17); outer = (lambda u: u <= 16)
    def f(c):
        pts = props.shifted(FOOT, dx, dy)
        def sh(x, y):
            u, v = x - dx, y - dy
            return YEL_MID if (v >= 62 or outer(u)) else YEL
        line, inter = draw_part(c, pts, sh)
        for t in toes:
            for v in range(59, 63):
                if (t + dx, v + dy) in inter: c.put(t + dx, v + dy, BLACK)
            if (t + dx, 58 + dy) in inter: c.put(t + dx, 58 + dy, YEL_DEEP)
    return f

def sole_foot(heel, toes, flip=False):
    """KO foot seen sole-on, three toes fanned upward (absolute coords)"""
    def f(c):
        m = {}
        for tip in toes:
            mm = props.limb_mask([heel, tip], [2.7, 2.0])
            for k, v in mm.items():
                if k not in m or v[0] < m[k][0]: m[k] = v
        pad = props.limb_mask([heel, (heel[0], heel[1] + 0.5)], [3.6, 3.6])
        for k, v in pad.items():
            if k not in m or v[0] < m[k][0]: m[k] = v
        props.mask_draw(c, m, props.yellow_colour)
        # no interior crease marks: any dots inside the sole read as eyes
    return f

# ---------------------------------------------------------------------------
# 0-1 idle
IDLE_A = {}
IDLE_B = dict(body=(0, 1, 1.0, 1.0), googly='lag_up')

# 2-5 waddle: lean onto the planted foot, lift the other, head lags the body,
# googly pupils swing loose behind the motion
WADDLE_L = dict(body=(-2, 0, 1.0, 1.0), head=(-1, 0), wing_l=(0, 1), wing_r=(1, -2),
                foot_r=(-1, -3), googly='swing_r', sym=False)
WADDLE_PASS_1 = dict(body=(0, 1, 1.0, 1.0), head=(-1, 0), wing_r=(0, -1), googly='lag_up', sym=False)
WADDLE_R = dict(body=(2, 0, 1.0, 1.0), head=(1, 0), wing_r=(0, 1), wing_l=(-1, -2),
                foot_l=(1, -3), googly='swing_l', sym=False)
WADDLE_PASS_2 = dict(body=(0, 1, 1.0, 1.0), head=(1, 0), wing_l=(0, -1), googly='lag_up', sym=False)

# 6-7 poop
POOP_STRAIN = dict(body=(0, 3, 1.08, 0.92), head=(0, 1), wing_r=(-1, 1), wing_l=(1, 1),
                   foot_r=(3, 0), foot_l=(-3, 0), face='strain', googly='lag_up', sym=True,
                   over=[props.sweat([(14, 5), (49, 6)]),
                         props.lines([[(7, 29), (9, 30)], [(5, 33), (8, 33)], [(7, 37), (9, 36)],
                                      [(56, 29), (54, 30)], [(58, 33), (55, 33)], [(56, 37), (54, 36)]])])
POOP_RELEASE = dict(body=(0, 1, 0.96, 1.05), head=(0, 0), wing_r=(1, -3), wing_l=(-1, -3),
                    foot_r=(3, 0), foot_l=(-3, 0), face='relief', googly='normal', sym=True,
                    over=[props.lines([[(6, 57), (5, 55), (6, 53), (5, 51), (6, 49)],
                                       [(57, 57), (58, 55), (57, 53), (58, 51), (57, 49)],
                                       [(3, 50), (2, 48), (3, 46)], [(60, 50), (61, 48), (60, 46)]],
                                      col=STINK)])

# 8-9 eat
EAT_WING_R = ([(49, 42), (51, 36), (48, 31), (44, 29), (40, 28)], [3.0, 3.2, 3.2, 3.5, 3.8])
EAT_WING_L = ([(14, 43), (13, 38), (17, 36), (22, 38)], [3.0, 3.2, 3.4, 3.8])
EAT_OPEN = dict(body=(0, 0, 1.0, 1.0), head=(0, 1), wing_r_mode='off', wing_l_mode='off',
                face='chomp_open', googly='in', sym=True,
                over=[limb(*EAT_WING_L, grooves=[(20, 37), (21, 38)]),
                      props.fries(18, 30),
                      limb(*EAT_WING_R, grooves=[(42, 27), (43, 28)]),
                      props.nugget(33, 20)])
EAT_SHUT = dict(body=(0, 1, 1.0, 1.0), head=(0, 0), wing_r_mode='off', wing_l_mode='off',
                face='chomp_shut', googly='in', sym=True,
                over=[limb(*EAT_WING_L, grooves=[(20, 37), (21, 38)]),
                      props.fries(18, 30),
                      limb([(49, 42), (51, 37), (49, 32), (45, 30), (42, 30)], [3.0, 3.2, 3.2, 3.5, 3.8],
                           grooves=[(44, 29), (45, 30)]),
                      props.nugget(35, 22, bitten=True, crumbs=[(-6, 10), (-3, 12), (-8, 13)])])

# 10-11 phone
PHONE_WING_R = ([(49, 42), (51, 37), (49, 32), (45, 28), (41, 26)], [3.0, 3.2, 3.3, 3.6, 3.8])
PHONE_SHOUT = dict(body=(0, 0, 1.0, 1.0), wing_r_mode='off', wing_l=(0, -2),
                   face='shout', googly='right', sym=False,
                   over=[props.phone(37, 13), limb(*PHONE_WING_R, grooves=[(43, 26), (44, 27)]),
                         props.lines([[(14, 9), (11, 7)], [(12, 13), (9, 12)], [(16, 6), (15, 3)]], local='head')])
PHONE_TALK = dict(body=(0, 1, 1.0, 1.0), wing_r_mode='off', face='talk', googly='right', sym=False,
                  over=[props.phone(37, 13), limb(*PHONE_WING_R, grooves=[(43, 26), (44, 27)])])

# 12 hit
FLUNG = ([(48, 39), (52, 34), (55, 29)], [3.0, 3.6, 4.6])
HIT = dict(body=(0, 2, 1.10, 0.88), head=(0, 1), wing_r_mode='off', wing_l_mode='off',
           face='pain', googly='knocked', sym=True,
           over=pair(FLUNG[0], FLUNG[1], grooves_r=[(55, 27), (56, 28), (53, 29), (54, 30)], dy=2))

# 13-14 defeated
COLLAPSE = dict(body=(-1, 4, 1.07, 0.90), head=(-4, 2), wing_r_mode='off', wing_l_mode='off',
                foot_l=(-3, 0), foot_r=(2, 0),
                face='dizzy', googly='crossed', sym=False,
                over=[limb([(49, 42), (53, 47), (55, 52)], [3.0, 3.5, 4.2], grooves=[(55, 52), (54, 53)]),
                      limb([(15, 42), (10, 39), (6, 35)], [3.0, 3.5, 4.2], grooves=[(6, 35), (7, 34)]),
                      props.star(12, 3), props.star(45, 1)])
KO = dict(body=(0, 10, 1.10, 0.80), head=(-3, 1), wing_r_mode='off', wing_l_mode='off',
          feet_detached=True, face='dizzy', googly='wall', sym=False,
          over=[limb([(51, 52), (54, 56), (57, 59)], [3.0, 3.4, 3.7], frame='abs'),
                limb([(12, 52), (9, 56), (6, 59)], [3.0, 3.4, 3.7], frame='abs'),
                sole_foot((25, 59), [(20, 51), (25, 49), (30, 51)]),
                sole_foot((38, 59), [(33, 51), (38, 49), (43, 51)])])

FRAMES = [
    ('idle', IDLE_A), ('idle', IDLE_B),
    ('waddle', WADDLE_L), ('waddle', WADDLE_PASS_1), ('waddle', WADDLE_R), ('waddle', WADDLE_PASS_2),
    ('poop', POOP_STRAIN), ('poop', POOP_RELEASE),
    ('eat', EAT_OPEN), ('eat', EAT_SHUT),
    ('phone', PHONE_SHOUT), ('phone', PHONE_TALK),
    ('hit', HIT),
    ('defeated', COLLAPSE), ('defeated', KO),
]
assert len(FRAMES) == 15
