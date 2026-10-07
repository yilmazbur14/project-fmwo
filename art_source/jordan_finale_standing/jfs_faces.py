"""Jordan's furious faces for the standing finale sheets, and the anger effects round his head.

The faces are row overrides of the approved face (janim_heads' method, head space x 37.., y 10..,
facing screen-right as the approved head does), so the face stays the approved one pixel for pixel
wherever a row is not overridden. The glare pair is the finale's own ("You're Burak!", drawn by the
finale-chars artist in art_source/jordan_finale_chars/jfc_front.py), snapshotted here as rows so the
standing Jordan in the room and the seated one glare with the same face:
  glare_shut  brows crushed down at the nose with a crease between them, pupils pinned small, the jaw
              clenched on a bar of teeth (the summon wind-up's grit)
  glare_open  the same brows over the laugh's dropped jaw: shouting
  rage_shut   glare_shut with the lips pulled back off the clenched teeth at both corners: seething
The ear burns red on all of them (jfc_front's EAR_HOT).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402

HD = B.HD
IDLE, SHOUT, LAUGH = HD.IDLE, HD.SHOUT, HD.LAUGH
over = HD.over


def edit(row, cols):
    """A face row with some columns replaced: {col: key}, col 0 = x 37."""
    r = list(row)
    for c, k in cols.items():
        r[c] = k
    return ''.join(r)


def _row(rows, y):
    return rows[y - HD.Y0]


# jfc_front's glare brows, as written there
G_BROWS = {22: edit(_row(SHOUT, 22), {12: 'd', 13: 'd', 14: 'b', 15: 'd', 16: 'd'}),
           23: edit(_row(SHOUT, 23), {7: 'h', 8: 'h', 9: 'h', 10: 'h', 11: 'h', 12: 'i', 13: 'i', 14: 'i', 15: 'b'}),
           24: edit(_row(SHOUT, 24), {8: 'h', 9: 'h', 10: 'h', 14: 'b', 18: 'h', 19: 'b'}),
           26: edit(_row(IDLE, 26), {10: 'W', 18: 'W'})}
GLARE_SHUT = over(HD.rows('grit'), dict(G_BROWS))
GLARE_OPEN = over(LAUGH, {**G_BROWS, 25: _row(IDLE, 25), 27: _row(IDLE, 27)})
# seething: the lips pulled back off the clenched teeth, the bar of teeth wider at both corners
RAGE_SHUT = over(GLARE_SHUT, {31: "...ki jjclj kWWWW WWWWk ik."})

FACES = {'glare_shut': GLARE_SHUT, 'glare_open': GLARE_OPEN, 'rage_shut': RAGE_SHUT}

EAR = {(x, y) for x in (37, 38, 39) for y in range(25, 30)}
EAR_HOT = {'a': 'V', 'b': 'R', 'c': 'R', 'd': 'T', 'e': 'T'}


def face_rows(name):
    return FACES[name] if name in FACES else HD.rows(name)


def head(name, dx, dy, hair='v2', hot=True):
    """A furious head in build coordinates, moved by (dx, dy): the face rows under v2's hair (or the
    flopped quiff), the ear burning red."""
    part = B.head(face_rows(name), 0, 0, hair=hair)
    if hot:
        for q in EAR:
            if part.get(q) in EAR_HOT:
                part[q] = EAR_HOT[part[q]]
    return B.shift(part, dx, dy)


def anger(cv, hd, fx, steam=True, flip_steam=False):
    """The anger mark popped on the back of his hair (screen-left: he faces right) and steam off both
    sides of his head. `hd` is the head part as stamped."""
    x0 = min(x for x, y in hd)
    x1 = max(x for x, y in hd)
    y0 = min(y for x, y in hd)
    B.overlay(cv, B.ANGER, x0 + 3, y0 + 5)
    if steam:
        puffs = ((B.STEAM, x0 - 7, y0 + 13), (B.STEAM_S, x0 - 9, y0 + 8),
                 (B.STEAM, x1 + 2, y0 + 11), (B.STEAM_S, x1 + 5, y0 + 7))
        if flip_steam:
            puffs = ((B.STEAM_S, x0 - 6, y0 + 12), (B.STEAM, x0 - 9, y0 + 7),
                     (B.STEAM_S, x1 + 2, y0 + 10), (B.STEAM, x1 + 4, y0 + 5))
        for rows, sx, sy in puffs:
            B.overlay(cv, rows, sx, sy, fx=fx, only_empty=True)
