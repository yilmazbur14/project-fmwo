"""NEW hair maps for the kaiju sheets (the rig's keys): v2's greasy hair with the quiff blown back by
the leap's wind (WHIP_A / WHIP_B). Rows 15..21 are v2's own (jv2_head.HAIR, the face edge, the
forelock, the rat-tail); rows 7..14 are redrawn: the crest laid back flat over the crown, its oily
shine band dragged back with it, the mass streaming off the back of his head in clumps."""
import sys
sys.dont_write_bytecode = True
import jr_common as C

V2H = C.JB.jv2_head
X0 = 29                      # the whip maps start 6 columns left of v2's (35)
V2_ROWS = C.JB.rows_of(V2H.HAIR)

WHIP_A_TOP = [
    # x: 29-33 34-38 39-43 44-48 49-53 54-58 59-61       y
    "..... ..kkk kk... ..... ..... ..... ...",       # 7   the streaming clump's top edge
    "...kk kkjlA Yhkkk kk... ..... ..... ...",       # 8
    ".kkjl jhAYA hjlji hjkk. ..... ..... ...",       # 9   the quiff swept back off the crown
    "kjljh iAYhj lihjl jiAYk kk... ..... ...",       # 10  into a greasy clump streaming behind him,
    ".kkkj ljhik jljhi ljAYh ijkkk ..... ...",       # 11  its oily shine dragged back along it
    "...kk kjljj hjlih jlihA Yhjik k.... ...",       # 12
    "..... .kkli jhkjh iljli hjiAY Akkk. ...",       # 13
    "..... ..kkk khjkj iljhi ljhij hAYhk ...",       # 14
]
WHIP_B_TOP = [
    # x: 29-33 34-38 39-43 44-48 49-53 54-58 59-61       y
    "..... ..... ..... ..... ..... ..... ...",       # 7
    "kkk.. .kkkk kkk.. ..... ..... ..... ...",       # 8   the clump whipped down a pixel, its tip
    "kjlkk kjlAY Ahkkk kk... ..... ..... ...",       # 9   flicked up the other way
    ".kkjh iAYAh jljih jlkk. ..... ..... ...",       # 10
    "..kkj lAYhj lihjl jiAYk kk... ..... ...",       # 11
    "....k kljik jljhi ljAYh ijkkk ..... ...",       # 12
    "..... kkkli jhkjh iljlA Yhjik k.... ...",       # 13
    "..... ..kkk khjkj iljhi ljhAY kkkkk ...",       # 14
]


def build(top):
    rows = [r.replace(' ', '') for r in top]
    for i, r in enumerate(rows):
        if len(r) != 33:
            raise ValueError('row %d is %d wide' % (7 + i, len(r)))
    part = C.amap(rows, X0, 7)
    for i, r in enumerate(V2_ROWS):
        y = V2H.HY0 + i
        if y < 15:
            continue
        for c, ch in enumerate(r):
            if ch != '.':
                part[(V2H.HX0 + c, y)] = ch
    part.update(V2H.TAIL_TIP)
    return part


def whip_a():
    return build(WHIP_A_TOP)


def whip_b():
    return build(WHIP_B_TOP)


if __name__ == '__main__':
    import jr_fig as F
    import jr_gridlook as G
    F.HAIRS.update({'whip_a': whip_a, 'whip_b': whip_b})
    for n in ('whip_a', 'whip_b'):
        hd = F.head('grit', hair=n)
        a = C.JB.audit(hd)
        print(n, 'gaps', a['gaps'][:20], 'lone', a['lone'], 'holes', a['holes'])
        print(G.gridlook(hd, 'grid_%s.png' % n, 27, 5, 62, 40, 14))
