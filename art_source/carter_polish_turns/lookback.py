"""The KO look-back's head: back still turned, the head comes round over his RIGHT shoulder (screen
right, so the cross stays on our side) to stare at the player - one red slit, a brow pressing down on
it, a flat mouth. Deadpan; he isn't even angry.

The body under it is carter_akuma frame 2 without its head (backview.headless()) and does not move.
Each head is drawn at pixel level on the polish head's own grid - dome rows 24-33 are the back head's
(the same sphere under the same light), and the features sit on the rows the approved front face has
them: brow 35-37, lash line 38, slit 39-40, lower lid 41, nostril 42, moustache 43-45, mouth 46, beard
to a chin keyline on 51. Light from the upper left, so the side of the head facing us is lit and the
face, turned toward screen right, falls a step into shade.

    k = 0   the back of the head (the approved back view's own head)
    k = 1   ~40 deg: still the skull; the right ear has slid in and the beard shows along the jaw
    k = 2   edge-on: the ear mid-head, the face is the right outline - brow ridge, socket, the eye,
            the nose, the moustache, the lips, the beard to the chin
    k = 3   ~115 deg, cranked past profile: the near eye a full slit looking straight back at us

    head(k) -> [part, ...] to stamp over backview.headless() (the earring is the approved cross,
               stamped on its own at EARRING_X[k] so its shape never drifts)
"""
from lib import amap
import head as HD
import backview

DOME = [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64 65-66
    "..... ..... ....k kkkkk kk... ..... ..... ..",   # 24
    "..... ..... .kkks sssst tukkk ..... ..... ..",   # 25
    "..... ....k kssss sssst tuuuv kk... ..... ..",   # 26
    "..... ...ks sssss ttttu uuuuu vvk.. ..... ..",   # 27
    "..... ..kts sssst tttuu uuuuu vvwk. ..... ..",   # 28
    "..... .ktts stttt uuuuu uuuuu vvvwk ..... ..",   # 29
    "..... .ktts tttuu uuuuu uuuuu uvvwk ..... ..",   # 30
    "..... ktttt tuuuu uuuuu uuuuu uvvvw k.... ..",   # 31
    "..... kttuu uuuuu uuuuu uuuuu uvvvw k.... ..",   # 32
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k.... ..",   # 33
]

QUARTER = DOME + [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64 65-66
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k.... ..",   # 34
    "..... ktuuu uuuuu uuuuu uuuuv kkvvw k.... ..",   # 35  his right ear, slid in off the edge
    "..... ktuuu uuuuu uuuuu uuuvk tvkvw k.... ..",   # 36
    "..... kuuuu uuuuu uuuuu uuvvk twk34 k.... ..",   # 37  the sideburn past it
    "..... kuuuu uuuuu uuuuu vvvvk uwk33 k.... ..",   # 38
    "..... kuuuu uuuuu uuuuv vvvvk uwk32 k.... ..",   # 39
    "..... kuuuu uuuuv vvvvv vvvvk vvk33 k.... ..",   # 40
    "..... .kuuu uuuvv vvvvv vvvvv kvk33 k.... ..",   # 41
    "..... .kvuu uuvvv vvvvv vvvww wk233 3k... ..",   # 42  the lobe; the beard along his jaw
    "..... ..kvv vvvvv wwwww wwwww wk234 4k... ..",   # 43  the nape under the occiput's crease
    "..... ..kvv vvvvv vvvvw wwwww Wk334 4k... ..",   # 44
    "..... ..kvu vvvvv vvvvw wwwwW Wk344 4k... ..",   # 45
    "..... ..kvv vvvvv vvvww wwwWW Wk445 k.... ..",   # 46
    "..... ..kvv vvvvv vvwww wwwWW Wk455 k.... ..",   # 47
    "..... ..kkk kkkkk kkkkk kkkkk kk45k ..... ..",   # 48
    "..... ..... ..... ..... ..... .kkk. ..... ..",   # 49
]

PROFILE = DOME + [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64 65-66
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k.... ..",   # 34
    "..... ktuuu uuuuk kuuuu uuuuv v4555 5k... ..",   # 35  ear top, brow ridge
    "..... ktuuu uuukt ukuuu uuuvv 55555 5k... ..",   # 36
    "..... kuuuu uuukt wk33u uuuvv 66556 6k... ..",   # 37  sideburn
    "..... kuuuu uuuku wk33u uuvvv vkkkk k.... ..",   # 38  lash line, the socket
    "..... kuuuu uuuku wk32u uuvvv vk7VO uk... ..",   # 39  the slit
    "..... kuuuu uuuku vk33u uuvvv vv877 uvk.. ..",   # 40
    "..... .kuuu uuuuk vk333 uuuvv vvkkv utvk. ..",   # 41  lower lid, the nose's tip
    "..... .kvuu uuuuu k2223 3uuuv vvvvk vvk.. ..",   # 42  lobe, nostril
    "..... ..kvu uuuuu uk223 3333u vk112 22k.. ..",   # 43  moustache, lit on top
    "..... ..kvv uuuuv uk233 33333 k2223 333k. ..",   # 44
    "..... ..kvv vuuuw vk333 34444 k3344 44k.. ..",   # 45
    "..... ..kvv vvuuv wk334 44444 454kk kk... ..",   # 46  the lips
    "..... ..kvv vvvvw wk344 44444 45Ww4 44k.. ..",   # 47  lower lip, dark skin
    "..... ..kkk kkkkk kk344 44444 44445 5k... ..",   # 48
    "..... ..... ..... .k444 44444 44555 k.... ..",   # 49
    "..... ..... ..... ..k45 55555 5555k ..... ..",   # 50
    "..... ..... ..... ...kk kkkkk kkkk. ..... ..",   # 51
]

LOOK = DOME + [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64 65-66
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k.... ..",   # 34
    "..... ktuuu kkuuu uuuuu uuu44 55555 5k... ..",   # 35  ear top, brow
    "..... ktuuk tukuu uuuuu uv555 55555 5k... ..",   # 36
    "..... kuuuk twk33 uuuuu vv655 55566 6k... ..",   # 37  the brow pressing down
    "..... kuuuk uwk33 uuuuv vkkkk kkkvt k.... ..",   # 38  lash line
    "..... kuuuk uwk32 uuuvv vk7VO OV7vt vk... ..",   # 39  the slit, looking straight back
    "..... kuuuk vwk33 uuuvv vv877 778vt tvk.. ..",   # 40  the nose breaks the outline
    "..... .kuuu kvk33 3uuvv vvvkk kkvtu uvk.. ..",   # 41  lower lid, the nose's tip
    "..... .kvuu uk233 32uuv vvvvv vvvvk vk... ..",   # 42  lobe, nostril
    "..... ..kvu uwk22 33333 3k112 22222 2k... ..",   # 43  moustache
    "..... ..kvv uvk23 33333 3k223 33333 3k... ..",   # 44
    "..... ..kvv uwk33 33444 4k334 44444 4k... ..",   # 45
    "..... ..kvv vvk34 44444 455kk kkkkk kk... ..",   # 46  a flat mouth
    "..... ..kvv vwk34 44444 44455 WwwW5 4k... ..",   # 47  lower lip
    "..... ..kkk kkk34 44444 44455 44445 5k... ..",   # 48
    "..... ..... ...k4 44444 44555 55555 5k... ..",   # 49
    "..... ..... ..... .k455 55555 5555k ..... ..",   # 50
    "..... ..... ..... ...kk kkkkk kkkk. ..... ..",   # 51
]

MAPS = {1: QUARTER, 2: PROFILE, 3: LOOK}
EARRING_X = {1: 56, 2: 45, 3: 41}        # the column of the cross's stem, hung from the lobe


def earring(cx):
    return amap(HD.EARRING, cx - 2, 43)


def head(k):
    if k == 0:
        return [backview.head_back(), backview.earring_back()]
    return [amap(MAPS[k], 30, 24), earring(EARRING_X[k])]


def body(k):
    """The look-back frame's figure: the unmoving back view, this head on it (no mark, no aura)."""
    if k == 0:
        return backview.body()
    cv = backview.headless()
    for p in head(k):
        cv.stamp(p, outline=False)
    return cv


def check():
    errs = []
    for k, rows in MAPS.items():
        for i, r in enumerate(rows):
            if len(r.replace(' ', '')) != 37:
                errs.append('look-back head %d row %d is %d wide' % (k, 24 + i, len(r.replace(' ', ''))))
    return errs or None
