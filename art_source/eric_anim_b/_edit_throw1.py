p = 'throw.py'
s = open(p).read()

# ---- 32: sweep smear from the idle-ish pose to the heave pose, behind the body
old = """    def before_head(fr):
        afx.smear_arc(fr, (26, 74), 70, 1, 8, 238, 290)
        sword_at(fr, Hd, -56, sa=0.9, sb=1.0, grip_a=-10)
    body(fr, upper=U, shoulders=S, cape=(-0.8, 0.5, 0), skip=('head', 'armL_back'),
         hooks={'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -1)})"""
new = """    def first(fr):
        sweep.sweep(fr, pose_at((29, 92), -100, 0.97), pose_at(Hd, -56, 0.9), a_min=34.0)
        w128()

    def before_head(fr):
        sword_at(fr, Hd, -56, sa=0.9, sb=1.0, grip_a=-10)
    body(fr, upper=U, shoulders=S, cape=(-0.8, 0.5, 0), skip=('head', 'armL_back'),
         hooks={'cape': first, 'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -1)})"""
assert old in s
s = s.replace(old, new)

# helper
s = s.replace('''GRIT = [(45, 31, "eeeeee"), (45, 32, "kkkkkk")]''', '''GRIT = [(45, 31, "eeeeee"), (45, 32, "kkkkkk")]
import sweep


def pose_at(hand, ang, sa, sb=1.0, grip_a=-10.0):
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    return ((hand[0] - u[0] * grip_a * sa, hand[1] - u[1] * grip_a * sa), ang, sa, sb)''')

# ---- 34: sweep from a lower, more upright pose (just out of the hand) to the airborne pose, behind the body
old = """    cx, cy = LOB['cxy']
    ang = LOB['ang']
    afx.smear_arc(fr, (62, 70), 58, 1, 9, 196, 236)
    bfx.crescent(cv(fr), cx, cy, 60, 60, 190 + ang, 238 + ang, 0.5, 4, dash_tail=0.45)
    bfx.crescent(cv(fr), cx, cy, 60, 60, 10 + ang, 58 + ang, 0.5, 4, dash_tail=0.45)
    sword_at(fr, (cx, cy), ang, sa=LOB['sa'], sb=LOB['sb'], grip_a=32)"""
new = """    cx, cy = LOB['cxy']
    ang = LOB['ang']
    sweep.sweep(fr, pose_at((40, 40), -62, 0.9, 0.9, grip_a=32), pose_at((cx, cy), ang, LOB['sa'], LOB['sb'], grip_a=32),
                a_min=-26.5, keep_out=occupied(fr))
    w128()
    sword_at(fr, (cx, cy), ang, sa=LOB['sa'], sb=LOB['sb'], grip_a=32)"""
assert old in s
s = s.replace(old, new)
s = s.replace('''def pose_at(hand''', '''def occupied(fr):
    return set((x, y) for y in range(128) for x in range(128) if fr.px[y][x] is not None)


def pose_at(hand''')

# ---- 35: arm-swing trail down the viewer-left side, drawn behind the body
old = """    def back(fr):
        afx.smear_arc(fr, (58, 78), 54, 0, 4, 188, 250)
        w128()"""
new = """    def back(fr):
        c = cv(fr)
        bfx.crescent(c, 40, 80, 36, 40, 112, 262, 7, 0.5, dash_tail=0.0)
        w128()"""
assert old in s
s = s.replace(old, new)

# ---- 39: burst after the weapon so it reads on top, but keep the fist clean
old = """    CATCH['fist_centre'] = (cx, cy)
    burst(fr, cx, cy)
    AW.draw(fr, dx=-1, dy=-3, arm_dx=0, arm_dy=1, fist_dx=fdx, fist_dy=fdy)
    return fr"""
new = """    CATCH['fist_centre'] = (cx, cy)
    AW.draw(fr, dx=-1, dy=-3, arm_dx=0, arm_dy=1, fist_dx=fdx, fist_dy=fdy)
    burst(fr, cx, cy)
    return fr"""
assert old in s
s = s.replace(old, new)
s = s.replace("""    for ang, r0, ln, w in [(-150, 9, 14, 2.2), (-110, 9, 11, 1.8), (170, 9, 13, 2.0), (140, 9, 10, 1.6),
                           (-30, 9, 9, 1.6), (40, 10, 9, 1.4), (100, 9, 8, 1.4), (-70, 9, 8, 1.4)]:""",
"""    for ang, r0, ln, w in [(-150, 10, 15, 2.4), (-120, 12, 10, 1.8), (175, 10, 15, 2.4), (145, 10, 11, 1.8),
                           (-35, 12, 9, 1.6), (35, 11, 10, 1.8), (105, 9, 9, 1.6), (-80, 12, 8, 1.4)]:""")
open(p, 'w').write(s)
print('ok')
