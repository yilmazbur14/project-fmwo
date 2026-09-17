p = 'whirl.py'
s = open(p).read()
s = s.replace("K = 0.40           # ground-plane compression for the swing", "K = 0.36           # ground-plane compression for the swing")
s = s.replace("AX, HANDS_Y, SH_Y = 64.0, 93.0, 83.0", "AX, HANDS_Y, SH_Y = 64.0, 90.0, 83.0")
old = """    th = math.radians(theta)
    U = (math.cos(th), K * math.sin(th))
    Pv = (-math.sin(th), K * math.cos(th))
    grip_a = -10.0
    o = (hands[0] - U[0] * grip_a, hands[1] - U[1] * grip_a)
    S = AffineSword(o, U, Pv)"""
new = """    th = math.radians(theta)
    U = (math.cos(th), K * math.sin(th))
    lu = math.hypot(*U)
    ang = math.degrees(math.atan2(U[1], U[0]))
    grip_a = -10.0
    o = (hands[0] - U[0] * grip_a, hands[1] - U[1] * grip_a)
    S = Sword(o, ang, sa=lu, sb=1.0)      # billboarded: the flat always faces the viewer"""
assert old in s
s = s.replace(old, new)
s = s.replace("""    smear(fr, theta, 70, 112, 0.5, 9, 'back')
    smear(fr, theta, 55, 78, 0.5, 5, 'back')""", """    for args in ARCS:
        smear(fr, theta, *args, 'back')""")
s = s.replace("""    smear(fr, theta, 70, 112, 0.5, 9, 'front')
    smear(fr, theta, 55, 78, 0.5, 5, 'front')""", """    for args in ARCS:
        smear(fr, theta, *args, 'front')""")
s = s.replace("TIP_R_EXTRA = 101.0      # grip point to tip", "TIP_R_EXTRA = 101.0      # grip point to tip\n# trailing arcs: (span deg, radius, thickness at tail, thickness at blade)\nARCS = [(95, 118, 0.5, 16), (70, 84, 0.5, 9), (45, 56, 0.5, 4)]")
s = s.replace("""    imgs = [whirl_frame(i).rgba() for i in idx]
    strip(imgs, 3, '../w_proto_3x.png')""", """    imgs = [whirl_frame(i).rgba() for i in idx]
    strip(imgs, 3, '../w_proto_3x.png')
    from pngio import blank, paste
    out = blank(4 * 130, 2 * 130, (40, 40, 40, 255))
    for k, im in enumerate(imgs):
        paste(out, rgba_on(im), (k % 4) * 130, (k // 4) * 130)
    zoom(out, 3, '../w_proto_grid_3x.png')""")
open(p, 'w').write(s)
print('ok')
