"""Hand-authored idle (frame 0) as row segments -> idle.txt (the editable source grid).
Each row: list of (x_start, chars). Overlapping segments are an error."""
from lib import *

ROWS = {
    # ---------------- head: egg dome + gloss streak ----------------
    3: [(28, "########")],
    4: [(25, "###HHHHHssm###")],
    5: [(23, "##HHWWWWHHssssmm##")],
    6: [(22, "#HWWWHHHssssssssmmd#")],
    7: [(22, "#HHHHsssssssssssmmd#")],
    8: [(21, "#HHHsssssssssssssmmmd#")],
    9: [(21, "#HHsssssssssssssmmmmd#")],
    10: [(21, "#Hssssssssssssssmmmmd#")],
    # brows (angled down to the nose)
    11: [(21, "#HsRRRsssssssssmRRRmd#")],
    12: [(19, "###Hs##RRRRssmsRRRR##md###")],
    13: [(18, "#Hs#ssss#####Hm#####mmmd#mm#")],
    # eyes: thick lid / sclera+iris
    14: [(18, "#smdss######sHms######mdDdm#")],
    15: [(18, "#sdmrs#WiiWdsHmsdWiiW#mRdDm#")],
    16: [(18, "#sdmoHHsmmsssHmmssddmmmrdDm#")],
    17: [(18, "#sm#OosssssssHsmsmmmmmrR#dm#")],
    18: [(19, "#s##OosssssdmdDmmmmmrR##m#")],
    # mustache / mouth / earring
    19: [(20, "###OoossoOOoorrrmmrrR###")],
    20: [(19, "#c#"), (23, "#OooOOooRrrrrRRrR#")],
    21: [(18, "#CcC##Ooorr######RRrrR###")],
    22: [(19, "#C#Hs#OoooommmdrrrrR#dmm###")],
    23: [(17, "##H#HHm#OooOoooorrRrrR#dmmmmm##")],
    # ---------------- shoulders / chest ----------------
    24: [(14, "###HHHssHsm#oOooOoorrrRR#ddmmmmss###")],
    25: [(12, "##HHs#HHssssm#ooOooOorrRrR#dmmmmmm#ssm##")],
    26: [(11, "#HHHHssm#HHsssm#oOooOorrRR#dmmmmm#ssmmmmd#")],
    27: [(10, "#HHHssssm#HHHssm#oOooOorRrR#dmmmmd#ssmmmmmd#")],
    28: [(10, "#HHsssssmm#HHsssm#oOooorrR#dsmmmd#ssmmmmmmdd#")],
    29: [(9, "#HHsssssmmd#Hsssssm#oOorrR#dssmmmd#smmmmmmddd#")],
    30: [(9, "#Hsssssmmdd#Hssssssm#oOrR#dsssmmmmd#dmmmmmmddD#")],
    31: [(8, "#HssssssmmdD#ssssssssm#oR#dssssmmmmd#ddmmmmdddD#")],
    32: [(8, "#HmmsssssmdD#mssssssssd##dsssssmmmdD#DddsmmmddD#")],
    33: [(8, "#HsmHHsssmd#dmmsssssssmddssssssmmmdDD#dssmmmdddD#")],
    34: [(8, "#HsmHsssmmd#DddmmmmmmmdDDdmmmmmddddDD#dsmmmmdddD#")],
    35: [(8, "#Hsmsssmmd#DDddddddddddDDddddddddddDDD#dsmmmdddD#")],
    # ---------------- abs ----------------
    36: [(8, "#Hmssssmdd#dmssmHHssssmdDmsssssmdmmdD#"), (47, "#dmmmmddD#")],
    37: [(8, "#Hmsssmdd#"), (19, "#dssmssssssmdDmssssmdmmmd#"), (47, "#dmmmdddD#")],
    38: [(8, "#ssssmmdD#"), (19, "#dmsmmmmmmmddDdddddddmmdD#"), (48, "#dmmddD#")],
    39: [(8, "#sHssmdD#"), (20, "#dsmHsssssmdDmssssmdmmd#"), (47, "#dmsmmdD#")],
    40: [(9, "#Hsssmd#"), (21, "#mmssssssmdDmssssmddD#"), (46, "#sssmmmdD#")],
    41: [(9, "#Hsssmd#"), (21, "#dmmmmmmmddDddddddddD#"), (46, "#ssmmmdD#")],
    42: [(10, "#Hsssmd#"), (22, "#dssssssmdDmsssmmdD#"), (44, "##ssmmmddD#")],
    43: [(10, "#Hsssmd#"), (22, "######################sssmmmddD#")],
    # ---------------- speedo / fists ----------------
    44: [(11, "#Hsssmd#"), (22, "#BBBBBBBBbbbbbbuu#ssssmmmmmdddD#")],
    45: [(11, "#sHHssmd#"), (22, "#uuuuuuuuuuuuuuUU#sHsmmdmmddD##")],
    46: [(12, "#Hssssmd##bBBbbbbbbbbbuuuuU#mdmdmdddD##")],
    47: [(12, "#sHHHsmd##bBbbbbbbbubuuuuUU#mdmdmdD##")],
    48: [(12, "#smdddmd#s##bbbbbbuuuuuuUUU##dDd###")],
    49: [(12, "#HsHsHsd#Hsm#ubbbbuuuuuUUUU#####")],
    50: [(12, "#sdsdsdD#Hssm###uuuUUUUUU##mmdd#")],
    51: [(12, "#mdmdmdD#Hssmmdd#########smmmmdD#")],
    52: [(13, "#dDdDd#Hssssssmmd#"), (33, "#ssmmmmmmdD#")],
    53: [(14, "#####Hssssssmmd#"), (34, "#smmmmmddD#")],
    # ---------------- boots ----------------
    54: [(18, "############"), (34, "############")],
    55: [(18, "#ggkkkkkkkK#"), (34, "#kgkkkkkKKK#")],
    56: [(18, "#gkkkkkkkKK#"), (34, "#kkkkkkKKKK#")],
    57: [(17, "#KKKKKKKKKKK#"), (34, "#KKKKKKKKKK#")],
    58: [(17, "#gkkkkgkkkKK#"), (34, "#kgkkgkkKKK#")],
    59: [(17, "#gkkkkkgkkKK#"), (34, "#kgkkkgkKKKK#")],
    60: [(16, "#gkkkkkgkkkKK#"), (34, "#kkkkgkkKKKK#")],
    61: [(16, "#ggkkkkkkkkKK#"), (34, "#kkkkkkkkgKKK#")],
    62: [(16, "#kkkkkkkkkKKK#"), (34, "#KkkkkkkkkgKKK#")],
    63: [(15, "###############"), (34, "###############")],
}


def compose(rows):
    g = blank()
    errors = []
    for y, segs in rows.items():
        used = {}
        for x0, s in segs:
            for i, c in enumerate(s):
                x = x0 + i
                if not (0 <= x < 64):
                    errors.append('row %d: x=%d out of range' % (y, x)); continue
                if x in used:
                    errors.append('row %d: x=%d overlap' % (y, x))
                if c not in PAL:
                    errors.append('row %d: bad char %r' % (y, c))
                used[x] = c
                g[y][x] = c
    return g, errors


if __name__ == '__main__':
    g, errs = compose(ROWS)
    for e in errs:
        print('ERR', e)
    save_grid(os.path.join(HERE, 'idle.txt'), g)
    save(os.path.join(HERE, 'idle_8x.png'), zoom(grid_to_pix(g), 8))
    save(os.path.join(HERE, 'idle_1x.png'), grid_to_pix(g))
    print('ok', len(errs), 'errors')
