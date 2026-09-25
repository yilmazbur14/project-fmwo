"""Captain Burak's faces for the fight set: the approved 'idle' smirk and 'shot' grin (head.py), the
juggle's faces (jhead.py), and the new ones below. Feature overlays on the approved face, x 36-60 from
y 28 (head.FEAT_X0 / FEAT_Y0); '.' keeps the skin underneath.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(os.path.dirname(HERE), 'burak_boss'), os.path.join(os.path.dirname(HERE), 'burak_boss_juggle')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import head as H  # noqa: E402
import jhead  # noqa: E402
from kit import amap  # noqa: E402

AFACES = {
    # the cutscene laugh, AT the player, reared back: eyes squeezed into ^ ^, brows flung up in high
    # arches, the mouth a huge open laugh with the corners hauled right up, top teeth and tongue
    'laugh_big': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "....h hh... ..... ...hh h....",       # 28  brows flung up in two high arches
        "..hh. ..h.. ..... ..h.. .hh..",       # 29
        "..... ..... ..... ..... .....",       # 30
        "....k kk... ..... ...kk k....",       # 31  ^ ^  squeezed shut with laughing
        "...kk .kk.. ..... ..kk. kk...",       # 32
        "..kk. ..kk. ..... .kk.. .kk..",       # 33
        ".BB.. ..... ..... ..... ..BB.",       # 34  tears of laughter at the corners
        ".A... ..... .2... ..... ...A.",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... k...4 65565 ....k .....",       # 39  the corners hauled right up
        "..... kkkkk kkkkk kkkkk .....",       # 40  the upper lip
        "..... kWWWW WWWWW WWWWk .....",       # 41  top teeth
        "..... kxxxx xxxxx xxxxk .....",       # 42  the throat
        "..... .kxxx xxxxx xxxk. .....",       # 43
        "..... .kxxy yyyyy yxxk. .....",       # 44  the tongue
        "..... ..kyy yyyyy yyk.. .....",       # 45
        "..... ...kk kkkkk kk... .....",       # 46
    ],
    # doubled over at the peak of it: eyes screwed into > <, tears squeezed out, the jaw bounced
    'laugh_big2': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ..... .....",       # 28
        "..... ..hhh ..... hhh.. .....",       # 29  brows up at the inner ends
        "..hhh h.... ..... ....h hhh..",       # 30
        "..kk. ..... ..... ..... .kk..",       # 31  > <
        "....k kk... ..... ...kk k....",       # 32
        "..kk. ..... ..... ..... .kk..",       # 33
        ".BB.. ..... ..... ..... ..BB.",       # 34  tears squeezed out
        ".A... ..... .2... ..... ...A.",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... k...4 65565 ....k .....",       # 39
        "..... kkkkk kkkkk kkkkk .....",       # 40
        "..... kWWWW WWWWW WWWWk .....",       # 41
        "..... .kxxx xxxxx xxxk. .....",       # 42
        "..... .kxxy yyyyy yxxk. .....",       # 43
        "..... ..kyy yyyyy yyk.. .....",       # 44
        "..... ...kk kkkkk kk... .....",       # 45
        "..... ..... s.s.s ..... .....",       # 46
    ],
    # --- talk: pairs, mouth shut / open -------------------------------------------------------
    # smug, open: the approved smirk parted on a word, the top teeth showing under its hooked side
    'smug_open': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        ".kkkk kkkkk ..... kkkk. .....",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kW9 k9W4. ..... .4W9k 9Wk..",       # 33
        "...49 994.. ..... ..499 94...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk WWWWk 5....",       # 42  the smirk parted, teeth bared under its hook
        "..... ..kWW WWWxx xxxk. .....",       # 43
        "..... ...kk kkkkk kkk.. .....",       # 44
        "..... ....4 ppp4. ..... .....",       # 45  the full lower lip, dropped
        "..... ..... 444.. ..... .....",       # 46
    ],
    # laugh, shut: a pleased chuckle, eyes creased into ^ ^, a closed lopsided grin
    'chuckle': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        "..... ..... ..... ..... .....",       # 30
        "....k kk... ..... ...kk k....",       # 31  ^ ^
        "...kk .kk.. ..... ..kk. kk...",       # 32
        "..kk. ..kk. ..... .kk.. .kk..",       # 33
        "..... ..... ..... ..... .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ...kk .....",       # 40  the grin hooked up on his left
        "..... .k... ..... kkk.. 5....",       # 41
        "..... ..kkk kkkkk ..... .....",       # 42
        "..... ...4p pppp4 ..... .....",       # 43
        "..... ....4 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # laugh, open: "heh heh", the grin opened on the top teeth
    'chuckle_open': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        "..... ..... ..... ..... .....",       # 30
        "....k kk... ..... ...kk k....",       # 31  ^ ^
        "...kk .kk.. ..... ..kk. kk...",       # 32
        "..kk. ..kk. ..... .kk.. .kk..",       # 33
        "..... ..... ..... ..... .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ...kk .....",       # 40
        "..... .kkkk kkkkk kkk.. 5....",       # 41  the upper lip
        "..... ..kWW WWWWW WWk.. .....",       # 42  top teeth
        "..... ...kx xyyyx xk... .....",       # 43
        "..... ....k kkkkk k.... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # point, "Think!": a knowing look sideways at the player, the near brow flat and low, the far one
    # cocked sky-high, the smirk / the smirk parted on the word
    'think': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ...hh hh...",       # 28  the far brow cocked right up
        "..... ..... ..... ..h.. ..hh.",       # 29
        "..hhh hhhhh ..... ..... .....",       # 30  the near brow flat and low
        ".kkkk kkkk. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32  heavy lids
        "..kWW Wk94. ..... .4WWW k9k..",       # 33  irises slid to the player
        "...44 4994. ..... ..444 99...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    'think_open': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ...hh hh...",       # 28  the far brow cocked right up
        "..... ..... ..... ..h.. ..hh.",       # 29
        "..hhh hhhhh ..... ..... .....",       # 30  the near brow flat and low
        ".kkkk kkkk. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32  heavy lids
        "..kWW Wk94. ..... .4WWW k9k..",       # 33  irises slid to the player
        "...44 4994. ..... ..444 99...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk WWWWk 5....",       # 42  the smirk parted, teeth bared under its hook
        "..... ..kWW WWWxx xxxk. .....",       # 43
        "..... ...kk kkkkk kkk.. .....",       # 44
        "..... ....4 ppp4. ..... .....",       # 45  the full lower lip, dropped
        "..... ..... 444.. ..... .....",       # 46
    ],
    # shrug: "eh". Brows up at the inner ends, the unbothered lids, a flat mouth / a small open "eh"
    'shrug': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..hh. ..... .hh.. .....",       # 28  brows up at the inner ends
        "..hhh hh... ..... ...hh hhh..",       # 29
        ".kkkk ..... ..... ..... kkkk.",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kW9 k9W4. ..... .4W9k 9Wk..",       # 33  unbothered
        "...49 994.. ..... ..499 94...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ..... .....",       # 40
        "..... ..... ..... ..... .....",       # 41
        "..... ..kkk kkkkk kk... .....",       # 42  flat
        "..... .k.4p pppp4 ..k.. .....",       # 43  the corners turned down
        "..... ....4 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    'shrug_open': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..hh. ..... .hh.. .....",       # 28  brows up at the inner ends
        "..hhh hh... ..... ...hh hhh..",       # 29
        ".kkkk ..... ..... ..... kkkk.",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kW9 k9W4. ..... .4W9k 9Wk..",       # 33  unbothered
        "...49 994.. ..... ..499 94...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ..... .....",       # 40
        "..... ..... ..... ..... .....",       # 41
        "..... ..kkk kkkkk k.... .....",       # 42  "eh": flat, the teeth showing
        "..... ..kWW WWWWW k.... .....",       # 43
        "..... ...kk kkkkk ..... .....",       # 44
        "..... ....4 ppp4. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # --- defeat --------------------------------------------------------------------------------
    # beaten: brows up at the inner ends, the eyes shut and drooping, the smirk turned to a frown
    'defeat': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ..... .....",       # 28
        "..... ..hhh ..... hhh.. .....",       # 29  brows up at the inner ends
        "..hhh h.... ..... ....h hhh..",       # 30
        "..... ..... ..... ..... .....",       # 31
        "...kk kkk.. ..... ..kkk kk...",       # 32  eyes shut, drooping at the outer corners
        "..k.. ..... ..... ..... ..k..",       # 33
        "..... ..... ..... ..... .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ..... .....",       # 40
        "..... ..... ..... ..... .....",       # 41
        "..... ...kk kkkkk kk... .....",       # 42  the frown
        "..... ..k.4 pppp4 ..k.. .....",       # 43
        "..... ..... 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # the held last frame: the lip wobbling, one tear run down from the near eye
    'defeat2': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ..... .....",       # 28
        "..... ..hhh ..... hhh.. .....",       # 29
        "..hhh h.... ..... ....h hhh..",       # 30
        "..... ..... ..... ..... .....",       # 31
        "...kk kkk.. ..... ..kkk kk...",       # 32
        "..k.. ..... ..... ..... ..k..",       # 33
        "..B.. ..... ..... ..... .....",       # 34  a tear
        "..B.. ..... .2... ..... .....",       # 35
        "..A.. ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ..... .....",       # 40
        "..... ..... ..... ..... .....",       # 41
        "..... ...kk .kkk. kk... .....",       # 42  the lip wobbling
        "..... ..k.. k...k ..k.. .....",       # 43
        "..... ....4 ppp4. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # the idle's blink: the smoulder's heavy lids come right down, the smirk stays
    'blink': [
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        ".kkkk kkkkk ..... kkkk. .....",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..444 4444. ..... .4444 444..",       # 32
        "..kkk kkkk. ..... .kkkk kkk..",       # 33  shut
        "..... ..... ..... ..... .....",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # swordplay: brows down, eyes narrowed on the target to his left (screen right), a wolfish grin
    'fierce': [
        "..... ..... ..... ..... .....",       # 28
        "..hhh hhhh. ..... ..hhh hhh..",       # 29
        "...kk kkkhk ..... khkkk kk...",       # 30  brows angled down to the nose
        "..444 44... ..... ...44 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kWW Wk9k. ..... .4WWk 9kk..",       # 33  narrowed, irises on the target
        "...44 444.. ..... ..444 44...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..... ..... ..kkk .....",       # 40  the grin hooked up on his left
        "..... ..kkk kkkkk kkWWk .....",       # 41
        "..... ..kWW WWWWW WWWk. .....",       # 42  bared teeth
        "..... ...kk kkkkk kkk.. .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # the taunt: blowing the smoke off his muzzle. Eyes shut in smug contentment, brows up, lips
    # pursed and blowing off to his left (screen right)
    'blow': [
        "..... ..... ..... ..... .....",       # 28
        "...hh hhh.. ..... ...hh hhh..",       # 29  brows lifted, relaxed
        "..h.. ...h. ..... ..h.. ...h.",       # 30
        "..... ..... ..... ..... .....",       # 31
        "..... ..... ..... ..... .....",       # 32
        "..kkk kkkk. ..... .kkkk kkk..",       # 33  eyes shut, content
        ".k..4 444.. ..... ..444 4..k.",       # 34  lashes flicked at the outer corners
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.s.k k.... .....",       # 40  the pout, pushed to his left
        "..... ..... ...kp pk... .....",       # 41
        "..... ..... ...kx xk... .....",       # 42  lips pursed round a breath
        "..... ..... ....k k.... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # the heave: teeth gritted in a grin, brows down, putting his back into it
    'strain': [
        "..... ..... ..... ..... .....",       # 28
        "...hh hhhh. ..... .hhhh hh...",       # 29  brows down hard at the middle
        ".kkkk kkkhk ..... khkkk kkk..",       # 30
        "..444 44... ..... ...44 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kWk kkW4. ..... .4Wkk kWk..",       # 33  eyes narrowed to slits
        "...44 444.. ..... ..444 44...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... .kkkk kkkkk kkkk. .....",       # 40  gritted teeth, a wide grin
        "..... kWkWk WkWkW kWkWk .....",       # 41
        "..... .kkkk kkkkk kkkk. .....",       # 42
        "..... ..... ..... ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # the "click": a knowing wink over the smirk
    'wink': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        ".kkkk kkkkk ..... kkkk. .....",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... ..... .....",       # 32
        "..kW9 k9W4. ..... .kkkk kk...",       # 33  the far eye shut in a smiling wink
        "...49 994.. ..... k.... ..k..",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # eyes on the job: a side glance at the gun held up beside his head, the smirk kept
    'look_side': [
        "..... ..... ..... ....h hhh..",       # 28
        "...hh hhhhh ..... hhhhk kkki.",       # 29
        ".kkkk kkkkk ..... kkkk. .....",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kWW Wk94. ..... .4WWW k9k..",       # 33  irises slid to the right
        "...44 4994. ..... ..444 99...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # eyes on the job: looking down at the gun in his hand, the smirk kept
    'look_down': [
        "..... ..... ..... ..... .....",       # 28
        "...hh hhhhh ..... hhhhh hhh..",       # 29  brows level, relaxed
        ".kkkk kkkkk ..... kkkkk kk...",       # 30
        "..444 4444. ..... .4444 444..",       # 31
        "..kkk kkkk. ..... .kkkk kkk..",       # 32
        "..kkk kkkk. ..... .kkkk kkk..",       # 33  lids dropped: eyes down
        "...4W 99W.. ..... ..W99 W4...",       # 34  irises low, looking down
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
    # aiming down the barrel: the near eye screwed shut, the far one narrowed on the target, the smirk
    'aim': [
        # x: 36-40 41-45 46-50 51-55 56-60      y
        "..... ..... ..... ....h hhh..",       # 28  the sighting eye's brow cocked
        "..... ..... ..... hhhhk kkki.",       # 29
        "..hhh hhhhh ..... kkkk. .....",       # 30  the shut side's brow pulled down
        ".kkkk kkkk. ..... .4444 444..",       # 31
        "..... ..... ..... .kkkk kkk..",       # 32
        "..kkk kkkk. ..... .4W9k 9Wk..",       # 33  squeezed shut / sighting
        "...44 444.. ..... ..499 94...",       # 34
        "..... ..... .2... ..... .....",       # 35
        "..... ..... .2.4. ..... .....",       # 36
        "..... ..... .2.44 ..... .....",       # 37
        "..... ..... 31245 ..... .....",       # 38
        "..... ....4 65565 ..... .....",       # 39
        "..... ..s.s s.ss. ....k k....",       # 40
        "..... ..... ..... kkkk. 5....",       # 41  the smirk
        "..... .kkkk kkkkk ..... 5....",       # 42
        "..... ..4pp ppp4. ..... .....",       # 43
        "..... ...44 444.. ..... .....",       # 44
        "..... ....s .s.s. ..... .....",       # 45
        "..... ..... s...s ..... .....",       # 46
    ],
}


def features(expr):
    if expr in ('idle', 'shot'):
        return H.features(expr)
    if expr in jhead.FACES:
        return jhead.features(expr)
    return amap(AFACES[expr], H.FEAT_X0, H.FEAT_Y0)
