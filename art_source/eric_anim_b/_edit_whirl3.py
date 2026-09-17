p = 'whirl.py'
s = open(p).read()
s = s.replace("AX, HANDS_Y, SH_Y = 64.0, 90.0, 83.0", "AX, HANDS_Y, SH_Y = 64.0, 91.0, 82.0")
s = s.replace("HANDS_R, SH_R = 22.0, 22.0", "HANDS_R, SH_R = 25.0, 22.0\nSH_K = 0.12       # shoulders sit on the pauldrons, which use the body tilt")
old = """    sh_r = gp(SH_R, phi + 90, SH_Y)     # his right shoulder
    sh_l = gp(SH_R, phi - 90, SH_Y)     # his left shoulder"""
new = """    def shp(a):
        ar = math.radians(a)
        return (AX + SH_R * math.cos(ar), SH_Y + SH_K * SH_R * math.sin(ar))
    sh_r = shp(phi + 90)     # his right shoulder
    sh_l = shp(phi - 90)     # his left shoulder"""
assert old in s
s = s.replace(old, new)
old = """        score = lambda e: abs(e[0] - AX) + 0.3 * e[1]"""
new = """        score = lambda e: e[1] + 0.35 * abs(e[0] - AX)"""
assert old in s
s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
