import rig
disc = {(dx, dy) for dx in range(-6, 7) for dy in range(-6, 7) if dx * dx + dy * dy <= 28}
N4 = ((1,0),(-1,0),(0,1),(0,-1))
outline = {p for p in disc if any((p[0]+a, p[1]+b) not in disc for a, b in N4)}
N8 = N4 + ((1,1),(1,-1),(-1,1),(-1,-1))
def clean(mark, off):
    """every mark pixel inside the white, and no mark pixel touches the outline
    (8-neighbour) - otherwise the mark fuses into the rim and stops reading"""
    for (dx, dy) in mark:
        p = (dx + off[0], dy + 1 + off[1])
        if p not in disc or p in outline: return False
        if any((p[0]+a, p[1]+b) in outline for a, b in N8): return False
    return True
for name, mk in (('PLUS', rig.PLUS), ('EX', rig.EX)):
    ok = [(x, y) for y in range(-3, 4) for x in range(-3, 4) if clean(mk, (x, y))]
    print(name, 'clean offsets:', ok)
bad = []
for v, (lo, ro) in rig.GOOGLY.items():
    l, r = clean(rig.PLUS, lo), clean(rig.EX, ro)
    print('%-9s left + %-8s %s   right x %-8s %s' % (v, lo, 'ok' if l else 'FUSES', ro, 'ok' if r else 'FUSES'))
