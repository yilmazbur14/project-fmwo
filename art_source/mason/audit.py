from collections import Counter
from png import read_png
import rig, frames
APPROVED = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason.png'
PALETTE = {  # approved + cast-palette props
    '#000000': 'outline', '#EEC39A': 'cream', '#FADCB8': 'cream hi', '#D6AA7C': 'cream mid',
    '#AE8358': 'cream deep', '#90765E': 'face lit', '#7D5631': 'face shad', '#AC3232': 'comb',
    '#D95763': 'comb hi/tongue', '#FBF236': 'yellow', '#D4CC2E': 'yellow mid', '#726E17': 'yellow deep',
    '#FFFFFF': 'white', '#A09050': 'khaki', '#605020': 'khaki dk',
    '#D9A066': 'nugget (Greyson)', '#1A1A1A': 'phone (Greyson)', '#666666': 'phone hi (Greyson)',
    '#639BFF': 'glint/sweat (Greyson)', '#4B692F': 'stink (Jordan)'}
_, _, ref = read_png(APPROVED)
problems = 0
total = Counter()
for i, (name, pose) in enumerate(frames.FRAMES):
    g = rig.render(pose); c = rig.make_ctx(pose)
    cols = Counter('#%02X%02X%02X' % p[:3] for row in g for p in row if p[3])
    total.update(cols)
    alphas = {p[3] for row in g for p in row}
    ys = [y for y in range(64) for x in range(64) if g[y][x][3]]
    notes = []
    stray = [k for k in cols if k not in PALETTE]
    if stray: notes.append('STRAY COLOURS %s' % stray)
    if not alphas <= {0, 255}: notes.append('SEMI-TRANSPARENT %s' % alphas)
    if max(ys) != 63: notes.append('NOT ON GROUND (max y %d)' % max(ys))
    if min(ys) < 0: notes.append('clipped top')
    # googly marks: every mark pixel black, every other disc-interior pixel white
    hx, hy = c.head; lo, ro = rig.GOOGLY[pose.get('googly', 'normal')]
    for (cx, cy, mark, off, lab) in ((16, 19, rig.PLUS, lo, '+'), (47, 19, rig.EX, ro, 'x')):
        disc = {(cx + dx, cy + dy) for dx in range(-6, 7) for dy in range(-6, 7) if dx * dx + dy * dy <= 28}
        rimset = {p for p in disc if any((p[0]+a, p[1]+b) not in disc for a, b in ((1,0),(-1,0),(0,1),(0,-1)))}
        mk = {(cx + dx + off[0], cy + dy + 1 + off[1]) for (dx, dy) in mark}
        blk = sum(1 for (x, y) in mk if g[y + hy][x + hx][:3] == (0, 0, 0))
        whites = sum(1 for p in disc - rimset - mk if g[p[1] + hy][p[0] + hx][:3] == (255, 255, 255))
        need = len(disc - rimset - mk)
        if blk != len(mk): notes.append('googly %s mark incomplete %d/%d' % (lab, blk, len(mk)))
        if whites < need * 0.8: notes.append('googly %s eye covered: %d/%d white' % (lab, whites, need))
    feats = {'comb red': cols['#AC3232'], 'ring yellow': cols['#FBF236'] + cols['#D4CC2E'], 'eye white': cols['#FFFFFF']}
    for k, v in feats.items():
        if v < 20: notes.append('%s low (%d)' % (k, v))
    exact = ''
    if i == 0:
        d = sum(1 for y in range(64) for x in range(64)
                if (g[y][x][3] > 0) != (ref[y][x][3] > 0) or (g[y][x][3] and tuple(g[y][x][:3]) != tuple(ref[y][x][:3])))
        exact = '  == approved mason.png (%d diff)' % d
        if d: notes.append('FRAME 0 DIFFERS')
    problems += len(notes)
    print('f%02d %-8s colours %2d  y %2d-63%s  %s' % (i, name, len(cols), min(ys), exact, '; '.join(notes) if notes else 'ok'))
print('\ncolours used across the sheet:')
for k, v in total.most_common():
    print('  %s %-22s %5d' % (k, PALETTE.get(k, '??? NOT IN PALETTE'), v))
print('\nPROBLEMS:', problems)
