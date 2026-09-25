"""The heads the entrance's turn wears, at the angles of intro_frames.TURN (phi: 0 his back, 90 edge-on,
180 facing us; he turns so his face comes round through screen LEFT).

    back_40()     phi 40, still his back: his LEFT ear has slid in off the screen-left edge and the
                  beard along that jaw turns into view; the right ear, and the cross on it, have gone
                  round the far side - only the cross's foot shows under the jaw
    left_48()     phi 132, the face ~50 deg round to screen left: the near (left) eye a full slit, the
                  far one behind the nose, brow, moustache, a flat mouth; the left ear back on the side
                  of the head. The face turns INTO the light here, so it is a step lighter than the
                  look-back's (which turns away from it)
    near_front(dx)  phi 162: the approved front head, the face slid dx px toward screen left inside
                  its outline - the last of the turn

    eyes(part, level) -> the slits kindled to a level (0 out ... 1 the approved glow), as
                  intro_profile.ignite_eyes did: the eyes come on as he comes round

All are drawn on the polish head's grid (dome rows 24-33 are the approved sphere, features on the
approved rows) and lit from the upper left. They go on bodies turned by turn34 / hsq; the neck meets
the collar on row 48.
"""
from lib import amap
import head as HD
import backview
import lookback

# ---------------------------------------------------------------- phi 40: the back, turning

def back_40():
    """lookback.QUARTER (the head turning toward screen RIGHT) mirrored, its skin re-lit by taking
    the approved back head's own tone wherever both are skin - the same skull under the same light -
    and its ear and beard kept. The cross stays behind his jaw; its foot shows below it."""
    q = amap(lookback.QUARTER, 30, 24)
    m = {(95 - x, y): k for (x, y), k in q.items()}
    bh = backview.head_back()
    skin = set('stuvwW')
    out = {}
    for p, k in m.items():
        b = bh.get(p)
        out[p] = b if (k in skin and b in skin) else k
    return out


# ---------------------------------------------------------------- phi 132: the face round to the left

LEFT_48 = lookback.DOME + [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64 65-66
    "..... ktttu uuuuu uuuuu uuuuv vvvvw k.... ..",   # 34
    "....k 45555 554tu uuuuu uuukk uvvvw k.... ..",   # 35  brow ridge; his left ear's top
    "....k 55555 5555v uuuuu uuukt ukuvw k.... ..",   # 36
    "....k 65555 5556v uuuuu u33kt wkuvw k.... ..",   # 37  the sideburn in front of the ear
    "..... kttkk kkkkk uuuuu u33ku wkuvw k.... ..",   # 38  lash line, the nose's bridge
    "....k tst7V OOV7k uuuuu u32ku wkuvw k.... ..",   # 39  the near eye
    "...kt stu87 7778u uuuuu u33ku vkuvw k.... ..",   # 40  the nose breaks the outline
    "...kt utuuk kkkuu uuuuu 333ku kuvwk ..... ..",   # 41  lower lid, the lobe
    "....k ukuuu uuuuu uuuu2 3332k uuuvk ..... ..",   # 42  nostril
    "....k 11222 2222k 33333 333ku uuvk. ..... ..",   # 43  moustache, lit on its front
    "....k 22233 3333k 33333 334ku vvvk. ..... ..",   # 44
    "....k 34444 4444k 44444 444kw uvvk. ..... ..",   # 45
    "....k kkkkk kkk55 44444 444kv vvwk. ..... ..",   # 46  a flat mouth
    "....k 34Www W4444 44444 444kw vvwk. ..... ..",   # 47  lower lip
    "....k 44444 45544 44444 445kk kkkk. ..... ..",   # 48
    "....k 44555 55555 55555 55k.. ..... ..... ..",   # 49
    "..... .k455 55555 5555k ..... ..... ..... ..",   # 50
    "..... ..kkk kkkkk kkk.. ..... ..... ..... ..",   # 51
]


def left_48():
    return amap(LEFT_48, 30, 24)


# ---------------------------------------------------------------- phi 162: nearly front

def near_front(dx=1):
    """The approved head with everything inside its outline between the ears slid dx px to screen
    left, rows 35-50: the eyes, nose, mouth and the beard's pattern move, the skull does not."""
    h = amap(HD.HEAD, HD.X0, HD.Y0)
    out = dict(h)
    for y in range(35, 51):
        row = sorted(x for (x, yy) in h if yy == y and 35 <= x <= 60)
        if not row:
            continue
        ks = [x for x in row if h[(x, y)] == 'k']
        lo, hi = min(ks), max(ks)               # the head's own keylines on this row
        inner = [x for x in range(lo + 1, hi) if (x, y) in h]
        if len(inner) < 6:
            continue
        for x in inner:
            src = x + dx
            if src < hi:
                out[(x, y)] = h[(src, y)]
            else:
                out[(x, y)] = h[(hi - 1, y)]
    return out


def earring_front():
    return amap(HD.EARRING, 31, 43)


# ---------------------------------------------------------------- the eyes kindling

_KINDLE = [
    (0.22, {'O': '9', 'V': '8', '7': '9', 'M': '8'}),
    (0.52, {'O': '7', 'V': '8', '7': '8', 'M': '7'}),
    (0.80, {'O': 'V', 'V': '7', '7': '7', 'M': 'V'}),
]


def eyes(part, level):
    """intro_profile.ignite_eyes' ladder, on the slit keys of this head only (rows 38-41)."""
    for lim, m in _KINDLE:
        if level < lim:
            return {q: (m.get(k, k) if 38 <= q[1] <= 41 else k) for q, k in part.items()}
    return dict(part)


def check():
    errs = []
    for i, r in enumerate(LEFT_48):
        if len(r.replace(' ', '')) != 37:
            errs.append('left_48 row %d is %d wide' % (24 + i, len(r.replace(' ', ''))))
    return errs or None
