"""Hand-authored face for the right side head (frame-0 coordinates, the head at frame.SIDE); the left
head is its mirror. '.' keeps the projected head underneath (ears, crest, ruff, collar, forehead).

The head is turned toward the centre and tilted outward, so the far eye (left) is small and tucked
against the blaze, the near eye (right) is the big one, and the snout points down and in at the
player.
"""
from pal import amap

# x: 143 ... 154
FAR_EYE = [
    ".uu.. ..... ..",      # 61
    ".kkuu ..... ..",      # 62
    ".kkkk uu... ..",      # 63
    ".khhk kkuu. ..",      # 64
    ".kiih hkkku ..",      # 65
    ".kjiW ihhkk u.",      # 66
    "..kji kkihk k.",      # 67
    "...kj kkjik ..",      # 68
    "....k jjjk. ..",      # 69
    "..... kkk.. ..",      # 70
]
FAR_EYE_XY = (143, 61)

# x: 156 ... 169
NEAR_EYE = [
    "..... ...uu u...",     # 62
    "..... .uukk ku..",     # 63
    "....u ukkkk kku.",     # 64
    "..uuk kkkhh ikk.",     # 65
    "..kkk khhiW jk..",     # 66
    ".kkkh hiiij k...",     # 67
    "kkhik kiijk ....",     # 68
    "khijk kjjk. ....",     # 69
    "kjjjj jkk.. ....",     # 70
    ".kkkk k.... ....",     # 71
]
NEAR_EYE_XY = (156, 62)

# x: 141 ... 166
MOUTH = [
    ".kkkk kxxxx xxxkk kkkyy .....",   # 84  the lip lifted over both canines
    ".kkwx kkkkk kkkkw xykkk y....",   # 85
    ".kkwy kxkxx kxkkw xykqq ky...",   # 86
    ".kkwk kkkkk kkkkw ykqqq qk...",   # 87
    ".kkxk qqqqk kkkqk xkqqq qqk..",   # 88
    ".kqkq qqqkk kkkkk xkqqq qks..",   # 89
    ".kqqq qqqkk kkkkq kqqqq qks..",   # 90
    ".xkqq qqqkk kkkkq qqqkq qks..",   # 91
    ".xkqq qqqkk kkkqq qqkxk kss..",   # 92
    ".xkqq qqqqk kkqqq qqkwx kss..",   # 93
    ".xxkq qqqqq qqqqq qqkwx kss..",   # 94
    ".xxkq qqqqq qqqqq qqkwy kss..",   # 95
    ".xxxk kxkxk xkxkx kqkwy kss..",   # 96
    ".xxxx kkkkk kkkkk kkkkk kss..",   # 97
    ".xxxx xwwww wwwww wwxxx kss..",   # 98
    ".xxxx xxxxx xxxxx xxxxy kss..",   # 99
    "kxxxx xxxxx xxxxx xxyyk .....",   # 100
    "kxxxx xxxxx xxxxx xyyyk .....",   # 101
    ".kxxx xxxxx xxxxx yyyk. .....",   # 102
    ".kxxx xxxxx xxyyy yyk.. .....",   # 103
    "..kky yyyyy yzzzz kk... .....",   # 104
    "....k kkkkk kkkkk ..... .....",   # 105
]
MOUTH_XY = (141, 84)

# x: 148 ... 160
TONGUE = [
    "...kk kkk.. ...",     # 92
    "..kpp NNNk. ...",     # 93
    ".kppN NNnnk ...",     # 94
    ".kpNN NnNnk ...",     # 95
    ".kpNN NnNnk ...",     # 96
    ".kpNN nNNnk ...",     # 97
    ".kpNN nNNnk ...",     # 98
    ".kpPN nNNnk ...",     # 99
    ".kpNN nNnnk ...",     # 100
    ".kpNN nNNnk ...",     # 101
    ".kpPN nNnk. ...",     # 102
    ".kpNN nNnk. ...",     # 103
    ".kpNn NNnk. ...",     # 104
    ".kpNn Nnnk. ...",     # 105
    "..kpn Nnk.. ...",     # 106
    "..kpn Nnk.. ...",     # 107
    "..kpN nk... ...",     # 108
    "...kn nk... ...",     # 109
    "....k k.... ...",     # 110
]
TONGUE_XY = (148, 92)


# Frame 2: the roar. Same lip and upper teeth; the jaw drops 4 rows lower, opening more throat.
ROAR = MOUTH[:7] + [
    ".kqqq qqqkk kkkkq qqqqq qks..",   # 91
    ".kqqq qqqkk kkkkq qqqqq qks..",   # 92
    ".kqqq qqqqk kkkqq qqqqq qks..",   # 93
    ".kqqq qqqqq kkqqq qqqqq qks..",   # 94
] + MOUTH[7:]
ROAR_TONGUE_DY = 4


def parts(dx=0, dy=0, roar=False):
    """The right side head's face maps, back to front."""
    out = []
    mouth = ROAR if roar else MOUTH
    tdy = ROAR_TONGUE_DY if roar else 0
    for rows, (x0, y0) in ((mouth, MOUTH_XY), (TONGUE, (TONGUE_XY[0], TONGUE_XY[1] + tdy)),
                           (FAR_EYE, FAR_EYE_XY), (NEAR_EYE, NEAR_EYE_XY)):
        out.append(amap(rows, x0 + dx, y0 + dy))
    return out
