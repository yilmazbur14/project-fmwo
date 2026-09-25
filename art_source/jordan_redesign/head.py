"""Jordan's head, hand-authored (12.webp is the face reference): short dark hair swept up and back
into a quiff at the front with shorter sides, heavy straight dark brows, brown eyes, a full short
dark beard and moustache, light olive skin, a squarish jaw. Three-quarter view facing screen-right,
lit from the upper left like the rest of the cast.

Columns run x = 37..59 (x0 = 37); rows start at y0 = 10. '.' is transparent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import amap  # noqa: E402

X0, Y0 = 37, 10

HEAD = [
    # x: 37-41 42-46 47-51 52-56 57-59      y
    "..... ..... ..... ..kkk k..",           # 10  crest of the quiff, highest at the front
    "..... ..... ...kk kkmml ik.",           # 11
    "..... ..... kkklm mlilj jik",           # 12  greasy locks swept up and back, a lit
    "..... ..kkk mljim ljjil jik",           # 13  edge on each and a dark parting under it
    "..... kkmlj imlji lljji jhk",           # 14
    "....k ijill jillj iljji hhk",           # 15
    "...ki jjiil jjhlj jhlji hhk",           # 16
    "..kii jjiih jjihj jihji hhk",           # 17
    "..kji jiihi ijiih iihhi hk.",           # 18  underside of the quiff; short sides below
    ".kiij ijhcc ddddd ddicc bk.",           # 19  hairline; a loose strand falls on the forehead
    ".kiii jhdee eeeed dddic bk.",           # 20
    ".kijj ihdee eeeed ddddc bk.",           # 21
    ".kijj idiii iiide djiii ik.",           # 22  heavy straight brows, 2 rows
    ".kiji hchhh hhhhd echhh hk.",           # 23
    ".kdci icccb bbbbd edcbb ck.",           # 24  heavy lid under the brow
    "kdbci ickkk kkkdd eckkk ck.",           # 25  lash lines
    "kdaci jccWW lhWdd ecWlh ck.",           # 26  eyes: white, brown iris, pupil
    "kdbci jcdcc ccddd ebccd ck.",           # 27  tired: bags under both eyes
    "kccbj cldee ddddd eebcd ck.",           # 28  nose tip; the sideburn thins out
    ".kbbj lcjdc dddcb dabcj ck.",           # 29  nostril; stubble specks on the cheeks
    "..kij lcdjc djlji jljic jk.",           # 30  thin moustache, bare at both corners
    "...ki jjclj dbkkk kkkbj ik.",           # 31  mouth
    "...kh icjjc jippd ppijc ik.",           # 32  lower lip; gaps in the jaw beard
    "....k hijcj ijihi jljic ik.",           # 33  fuller on the chin
    ".....k hijj ljiij ljiih k..",           # 34
    "......k hhi ijjjj jiiih k..",           # 35
    ".......k hh iiiii iiihk ...",           # 36
    "........ kk kkkkk kkkk. ...",           # 37  squared chin
]

# Messy lock tips breaking the silhouette: the quiff going a bit wild. (x, y) -> key.
TUFTS = {
    # a lock flicking up off the back of the crest
    (52, 11): 'm', (52, 10): 'l', (51, 10): 'k', (53, 10): 'k', (52, 9): 'k',
    # the front lock flicking forward
    (57, 10): 'm', (58, 9): 'l', (57, 9): 'k', (58, 8): 'k', (59, 8): 'k', (59, 9): 'k', (58, 10): 'k',
    # a tuft sticking out at the back of the head
    (41, 15): 'i', (40, 14): 'j', (40, 15): 'k', (39, 14): 'k', (40, 13): 'k', (41, 14): 'k',
}


# Frame 1: the fist-pump shout. Brows pulled down at the inner ends, mouth open on the teeth, the
# jaw a row lower. Rows 22..38 replace the idle ones (rows keep the idle head's width).
SHOUT = [
    # x: 37-41 42-46 47-51 52-56 57-59      y
    ".kijj idiii iiddd ddiii ik.",           # 22  brows slant down to the nose
    ".kiji hchhh hiiii eiihh hk.",           # 23
    ".kdci icccb bhhhh dhhbb ck.",           # 24
    "kdbci ickkk kkkdd eckkk ck.",           # 25
    "kdaci jccWW lhWdd ecWlh ck.",           # 26
    "kdbci jcdcc ccddd ebccd ck.",           # 27
    "kccbj cldee ddddd eebcd ck.",           # 28
    ".kbbj lcjdc dddcb dabcj ck.",           # 29
    "..kij lcdjc djlji jljic jk.",           # 30  moustache
    "...ki jjclj dkWWW WWWkj ik.",           # 31  upper teeth
    "...kh icjjc jkaap paakc ik.",           # 32  open mouth, tongue
    "...kh icjjc jippd dppic ik.",           # 33  lower lip
    "....k hijcj ijihi jljic ik.",           # 34
    ".....k hijj ljiij ljiih k..",           # 35
    "......k hhi ijjjj jiiih k..",           # 36
    ".......k hh iiiii iiihk ...",           # 37
    "........ kk kkkkk kkkk. ...",           # 38
]


# A greasy sheen on the brightest spot of each lock.
SHEEN = ((55, 11), (52, 12), (51, 13), (48, 14))


def head(shout=False):
    rows = [r.replace(' ', '') for r in HEAD]
    if shout:
        rows = rows[:22 - Y0] + [r.replace(' ', '') for r in SHOUT]
    part = amap(rows, X0, Y0)
    part.update(TUFTS)
    for q in SHEEN:
        part[q] = 'A'
    return part
