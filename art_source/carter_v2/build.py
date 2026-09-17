"""Final build: idle + charge with enlarged head, plain boots; writes grids, previews, strip."""
from lib import *
import paint_idle, paint_charge as pc

R = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'


def enlarge(H, dup_row, cl=26, cr=37):
    """Grow a head-group grid 1px up (duplicating dup_row) and 1px out each side (duplicating cols cl, cr)."""
    out = blank()
    for y in range(64):
        sy = y + 1 if y < dup_row else y
        for x in range(64):
            sx = x + 1 if x < cl else (x - 1 if x > cr else x)
            if 0 <= sy < 64 and 0 <= sx < 64:
                out[y][x] = H[sy][sx]
    return out


def over(base, top):
    g = [r[:] for r in base]
    for y in range(64):
        for x in range(64):
            if top[y][x] != '.':
                g[y][x] = top[y][x]
    return g


def holes(g):
    return [(x, y) for y in range(1, 63) for x in range(1, 63)
            if g[y][x] == '.' and all(g[y + dy][x + dx] != '.' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]


# ---------------- idle ----------------
IDLE_HEAD = {3: [(28, 35)], 4: [(25, 38)], 5: [(23, 40)], 6: [(22, 41)], 7: [(22, 41)], 8: [(21, 42)], 9: [(21, 42)],
             10: [(21, 42)], 11: [(21, 42)], 12: [(19, 44)], 13: [(18, 45)], 14: [(18, 45)], 15: [(18, 45)],
             16: [(18, 45)], 17: [(18, 45)], 18: [(19, 44)], 19: [(20, 43)], 20: [(19, 21), (23, 40)],
             21: [(18, 40)], 22: [(19, 21), (24, 39)], 23: [(20, 20), (24, 39)], 24: [(25, 38)], 25: [(25, 38)],
             26: [(26, 37)], 27: [(26, 37)], 28: [(27, 36)], 29: [(28, 35)], 30: [(29, 34)], 31: [(30, 33)],
             32: [(31, 32)]}
IDLE_BOOTS = {
    54: [(18, "############"), (34, "############")],
    55: [(18, "#gggggggggq#"), (34, "#gggggggggq#")],
    56: [(18, "#qkkkkkkkKK#"), (34, "#qkkkkkkkKK#")],
    57: [(17, "#qkkkkkkkkKK#"), (34, "#qkkkkkkkKK#")],
    58: [(17, "#qkkkkkkkkKK#"), (34, "#qkkkkkkkKK#")],
    59: [(17, "#qkkkkkkkkKK#"), (34, "#qkkkkkkkkKK#")],
    60: [(16, "#kkkkkkkkkkKK#"), (34, "#qkkkkkkkkKK#")],
    61: [(16, "#ggqqqqqqqqqK#"), (34, "#qqqqqqqqqggK#")],
    62: [(16, "#KKKKKKKKKKKK#"), (34, "#KKKKKKKKKKKKK#")],
    63: [(15, "###############"), (34, "###############")],
}

base, e1 = paint_idle.compose(paint_idle.ROWS)
for y, segs in IDLE_BOOTS.items():
    for x0, s in segs:
        for i, ch in enumerate(s):
            base[y][x0 + i] = ch
Hi = blank()
for y, spans in IDLE_HEAD.items():
    for a, b in spans:
        for x in range(a, b + 1):
            Hi[y][x] = base[y][x]
Hi2 = enlarge(Hi, dup_row=9)
old = {(x, y) for y in range(64) for x in range(64) if Hi[y][x] != '.'}
new = {(x, y) for y in range(64) for x in range(64) if Hi2[y][x] != '.'}
idle = over(base, Hi2)
strays = sorted(old - new, key=lambda p: (p[1], p[0]))
print('idle head strays (old head px not covered by new head):', strays)
# strays sit on the traps where the earring used to be: repaint them as trap skin
for (x, y) in strays:
    if idle[y][x] == '#':
        idle[y][x] = 's'
idle[20][21] = '.'  # keep the original transparent gap between earring and head

# ---------------- charge ----------------
body = [pc.L_BOOT_BACK, pc.L_LEG_BACK, pc.L_BOOT_FRONT, pc.L_LEG_FRONT, pc.L_SPEEDO, pc.L_TORSO, pc.L_ARM_TRAIL,
        pc.L_DELT_LEAD]
gb, e2 = pc.paint(body, with_speed=True)
gh, e3 = pc.paint([pc.L_HEAD, pc.L_EARS, pc.L_EARRING], with_speed=False)
gf, e4 = pc.paint([pc.L_FOREARM, pc.L_FIST], with_speed=False)
charge = over(over(gb, enlarge(gh, dup_row=17)), gf)

for name, g, errs in (('idle', idle, e1), ('charge', charge, e2 + e3 + e4)):
    print(name, 'paint errors:', errs, 'holes:', holes(g))
    save_grid(os.path.join(HERE, name + '_final.txt'), g)

pi, pch = grid_to_pix(idle), grid_to_pix(charge)
save(os.path.join(HERE, 'frames_8x.png'), hcat([zoom(pi, 8), zoom(pch, 8)]))
write_png(R + 'Carter/carter_redesign.png', 128, 64, [pi[y] + pch[y] for y in range(64)])

bg = (236, 236, 240, 255)
w, h, old_sheet = read_png(R + 'CarterAndJosh/carter.png')
w, h, mason = read_png(R + 'Mason/mason.png')
save(os.path.join(HERE, 'carter_compare_3x.png'),
     hcat([zoom(p, 3, bg) for p in (crop_pix(old_sheet, 0, 0, 64, 64), pi, pch, mason)]))
w, h, josh = read_png(R + 'Josh/josh_redesign.png')
dark = (52, 56, 66, 255)
duo = [zoom(p, 3, dark) for p in (crop_pix(josh, 0, 0, 64, 64), pi, crop_pix(josh, 64, 0, 64, 64), pch)]
save(os.path.join(HERE, 'duo_josh_carter_3x.png'), hcat(duo, bg=dark))
print('built')
