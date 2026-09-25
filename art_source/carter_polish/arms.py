"""Frame 0's arms and wrapped fists, by hand.

One continuous shape per arm, shoulder to wrist: muscle breaks are dark skin, never keyline. Light
from the upper left, so BOTH arms are lit on their screen-left side - on his right arm (screen left)
that is the outer edge, on his left arm it is the inner edge facing the torso.

The fists are shown knuckles-forward, the house view for fists (see carter_redesign.png): cream
wraps over the wrist and the back of the hand, the keyline where the wrap ends at the knuckles, and
three bare fingers under it. The approved sheet's fists were one khaki oval with two white dots.
The forearms angle out 1-2 px further than they did so there is real air between fist and thigh.
"""
from lib import amap

# his right arm, screen left: x 18..31, rows 56..72 (the gi cap is stamped over the top of it)
ARM_L = [
    # x: 18-22 23-27 28-31      y
    "..ktt ssttu uuvv",        # 56
    "..kts sttuu uvvv",        # 57
    "..kts ttuuu uvvw",        # 58
    "..ktt tuuuu vvww",        # 59
    "..kut tuuuv vvww",        # 60
    "..kuv vvvuv vwwk",        # 61  bottom of the deltoid
    "..ktt stuuu vwk.",        # 62  biceps, lit on its upper left
    "..kts sttuu vwk.",        # 63
    ".ktts tttuv wk..",        # 64
    ".kttt tuuvv wk..",        # 65
    ".kutu uuvvw wk..",        # 66
    ".kutu uvvww k...",        # 67  elbow: the crease is on the inner side
    ".ktst tuuvw k...",        # 68  forearm: the brachioradialis bulge takes the light
    "ktstt uuvvw k...",        # 69
    "ktstu uuvwk ....",        # 70
    "kttuu uvvwk ....",        # 71
    "kutuu vvwwk ....",        # 72
]

# his left arm, screen right: the mirrored shape, still lit from screen left (its inner side)
ARM_R = [
    # x: 64-68 69-73 74-77      y
    "uttst tuuuv vk..",        # 56
    "utsst tuuvv wk..",        # 57
    "utttt uuuvv wk..",        # 58
    "uuttu uuvvw wk..",        # 59
    "uutuu uvvvw wk..",        # 60
    "kuvvv vuvww wk..",        # 61
    ".ktts tuuvv wk..",        # 62
    ".ktss ttuuv wk..",        # 63
    "..ktt sttuu vwk.",        # 64
    "..ktt ttuuv vwk.",        # 65
    "..kut uuuvv wwk.",        # 66
    "...kw vutuu vwk.",        # 67
    "...kt sttuu vwk.",        # 68
    "...kt sttuu vvwk",        # 69
    "....k tstuu vvwk",        # 70
    "....k ttuuu vwwk",        # 71
    "....k utuuv vwwk",        # 72
]

FIST = [
    # x: +0..+4 +5..+9      y
    "kkkkk kkkkk",          # 71  where the wrap starts on the forearm
    "khghh iijlk",          # 72  wrist wrap
    "kihhi ijjlk",          # 73
    "kjjjl lllmk",          # 74  the edge of the next turn of cloth (a groove: same wrap)
    "khggh hijlk",          # 75  wrap over the back of the hand
    "khghh iijlk",          # 76
    "kihhh ijjlk",          # 77
    "kiiii jjllk",          # 78
    "kjijj jllmk",          # 79  the wrap's lower edge, in shadow
    "kkkkk kkkkk",          # 80  where the wrap stops at the knuckles
    "kstkt tkuvk",          # 81  three bare fingers
    "ktuku ukvvk",          # 82
    "kuvkv vkvwk",          # 83
    ".kk.k k.kk.",          # 84  fingertips
]


def arm_l():
    return amap(ARM_L, 18, 56)


def arm_r():
    return amap(ARM_R, 64, 56)


def fist_l():
    return amap(FIST, 18, 71)


def fist_r():
    return amap(FIST, 68, 71)
