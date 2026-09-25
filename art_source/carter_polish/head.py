"""Carter's head, front view, drawn pixel by pixel.

The approved head, kept: bald, 26px wide, dome top on row 24, heavy brows on rows 35-37, red eye
slits on rows 39-40, a short orange beard to a chin on row 51, cross earring on his right ear
(screen left). What changed is execution:
  * the dome is a real arc (8 px on top, stepping 3-2-1-1-1-0-1) instead of an 11px flat run;
  * each eye is a black lash line over a 2-row glowing slit and a short black lower lid, open at
    both corners - the old black box round each slit (and the black bar across the whole face
    above them) read as red sunglasses;
  * the sideburns are thinned where they pass the eyes so there is cheek skin between beard and eye;
  * the moustache is its own lobe, lit on top and dark underneath, over a flat deadpan mouth;
  * one light, upper left: highlight on the dome's upper left, shadow down the right side.
"""
from lib import amap

X0, Y0 = 30, 24

HEAD = [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64      y
    "..... ..... ....k kkkkk kk... ..... .....",       # 24
    "..... ..... .kkkt ssstt uukkk ..... .....",       # 25
    "..... ....k ktsss ssstt tuuuv kk... .....",       # 26
    "..... ...kt tssss stttt uuuuu vvk.. .....",       # 27
    "..... ..ktt sssst tttuu uuuuu vvwk. .....",       # 28
    "..... .ktts ssttt tuuuu uuuuu vvvwk .....",       # 29
    "..... .ktts stttu uuuuu uuuuu uvvwk .....",       # 30
    "..... kttts tttuu uuuuu uuuuu uvvvw k....",       # 31
    "..... ktttt tuuuu uuuuu uuuuu uvvvw k....",       # 32
    "..... ktttt tttuu uuuuu uuuuu uvvvw k....",       # 33
    "..... ktttt tttuu uutuu uuuuu uvvvw k....",       # 34
    "...kk ktu54 4445u uutuu uu555 556vw kkk..",       # 35
    "..kut ktu65 55555 5utuv 55555 566vw kuvk.",       # 36
    "..kuk ktuvv v6555 6utuv 65556 vvvvw kkvk.",       # 37
    "..kuk v3ukk kkkkk vutuv vkkkk kkkv4 vkvk.",       # 38
    "..kuw v3uk7 VOOV7 vutuv v7VOO V7kv4 vwvk.",       # 39
    "..kvu k3uv8 77778 vtsuv v8777 78vv4 kvwk.",       # 40
    "...kv k3uuv kkkkv utstv wvkkk kvuv4 kwk..",       # 41
    "...kk k33ku tuuuu vkvvk wvuuu uuk44 kkk..",       # 42
    "..... k233k uuv32 22333 344vu uk445 k....",       # 43
    "..... k2233 k1122 22333 33344 k4445 k....",       # 44
    "..... .k323 34333 34444 44445 4455k .....",       # 45
    "..... .k333 4k555 kkkkk k555k 4455k .....",       # 46
    "..... ..k23 33344 5WwwW 54444 455k. .....",       # 47
    "..... ...k2 33333 45555 44444 55k.. .....",       # 48
    "..... ....k k3333 34444 44455 kk... .....",       # 49
    "..... ..... .kk43 44444 555kk ..... .....",       # 50
    "..... ..... ...kk kkkkk kkk.. ..... .....",       # 51
]

# Latin cross (bar in the top third - the old one sat in the middle and read as a '+'), hung from
# the lobe of his right ear on a black link.
EARRING = [
    # x: 31-35
    "..k..",     # 43
    ".k#k.",     # 44
    "k###k",     # 45
    ".k%k.",     # 46
    ".k%k.",     # 47
    ".k&k.",     # 48
    "..k..",     # 49
]


def head():
    return amap(HEAD, X0, Y0)


def earring():
    return amap(EARRING, 31, 43)
