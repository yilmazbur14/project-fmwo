"""Matt's juggle faces, built the way the intro's are (mi_faces): the approved idle face with its
features swapped by patches, and the approved roar's own lower rows where the jaw drops.

  HIT      the approved roar's jaw, dropped as far as it goes, under eyes squeezed shut: the
           uppercut lands and the loudest mouth in the cast is knocked open
  YELL     the tumble's scream: eyes squeezed, the intro's yell jaw (mi_faces.YELL_ROWS)
  YELL_BIG the same scream a row deeper (mi_faces.ENOUGH_ROWS), so the loop's mouth wobbles
  GAPE     the apex: eyes popped wide with pinprick pupils, a dark little "o" (mf_faces.M_O)
  OOF      squeezed eyes and the fight set's round "OOF" (mf_recover.M_OOF)
  GRIT     the crash: squeezed eyes and the intro's gritted teeth, the whole jaw clenched
  DAZED    the bounce: blank white eyes, jaw slack in the yell
  KO       the mat: swirl eyes (new) over the approved roar's jaw hanging open, and his tongue
           lolling out of the corner of it (new, a separate keylined part: see ko_tongue)

Every map is x 31-65 from row 29, in the rig's LOCAL coordinates at the head's rest position.
"""
import mj_base as J
from mj_base import G, FF, MR

X0, Y0 = G.X0, G.Y0
ROAR_JAW = G.ROAR[14:]          # the approved roar from row 43 down: lip, fangs, throat, tongue, chin


def eyes(rows, x0, y0):
    """A patch list from map rows ('.' keeps the pixel underneath)."""
    return [(y0 + i, x0, ''.join('_' if ch == '.' else ch for ch in r)) for i, r in enumerate(rows)]


# The swirl: a white eye with a black spiral wound into it, the dizzy "@". Seven wide and seven
# tall, so it reads as round at 3x; the right eye is the left one mirrored.
SWIRL = [
    ".kkkk..",
    "kWWWWk.",
    "kWkkWWk",
    "kWkWkWk",
    "kWWkWWk",
    ".kWWWk.",
    "..kkk..",
]
EY_SWIRL = eyes(SWIRL, 37, 33) + eyes([r[::-1] for r in SWIRL], 53, 33)

# Slack brows for the KO: the worried brows, but their inner ends let down a row, so he looks
# out cold rather than upset.
BR_SLACK = [(32, 40, 'hhhh'), (33, 38, 'hhhhhhh'), (32, 53, 'hhhh'), (33, 52, 'hhhhhhh')]

HIT = G.with_jaw(G.face(G.BR_WORRY, G.EY_SQUEEZE), ROAR_JAW)
YELL = G.with_jaw(G.face(G.BR_WORRY, G.EY_SQUEEZE), G.YELL_ROWS)
YELL_BIG = G.with_jaw(G.face(G.BR_WORRY, G.EY_SQUEEZE), G.ENOUGH_ROWS)
GAPE = G.face(G.BR_HIGH, G.EY_WIDE, FF.M_O)
OOF = G.face(G.BR_WORRY, G.EY_SQUEEZE, MR.M_OOF)
GRIT = G.face(G.BR_WORRY, G.EY_SQUEEZE, G.M_GRIT)
DAZED = G.with_jaw(G.face(G.BR_WORRY, G.EY_BLANK), G.YELL_ROWS)
KO = G.with_jaw(G.face(BR_SLACK, EY_SWIRL), ROAR_JAW)


# His tongue lolling out of the corner of the hanging jaw: the approved roar tongue's own ramp
# (R lit, r base, q shade, p deep), keylined as its own piece and laid over the right-hand corner
# of the mouth and jaw. It hangs toward local +x, which is screen DOWN once he is lying on his back
# with his head to the right (turned 90), so it flops onto the mat.
TONGUE = [
    # x: 55-59 60-64 65-68
    "...kk kk... ....",      # 50
    "..kRr rrkk. ....",      # 51
    ".kRrr rrrqk k...",      # 52
    ".krrr rrqqq qk..",      # 53
    "..kqr rrrqq pk..",      # 54
    "...kq qrrqp pk..",      # 55
    "....k kqqpp k...",      # 56
    "..... .kkkk ....",      # 57
]
TONGUE_X0, TONGUE_Y0 = 55, 50


def ko_tongue(head):
    """The lolling tongue at the head's offset (hx, hy), as a part for the 'front' layer."""
    return J.moved(G.B.amap([r.replace(' ', '') for r in TONGUE], TONGUE_X0, TONGUE_Y0), *head)


FACES = {'HIT': HIT, 'YELL': YELL, 'YELL_BIG': YELL_BIG, 'GAPE': GAPE, 'OOF': OOF, 'GRIT': GRIT,
         'DAZED': DAZED, 'KO': KO}


def check():
    bad = []
    for n, rows in FACES.items():
        bad += G.B.check_map(rows, G.W, n)
    bad += G.B.check_map(TONGUE, 14, "TONGUE")
    return bad


if __name__ == '__main__':
    print(check() or 'faces ok')
