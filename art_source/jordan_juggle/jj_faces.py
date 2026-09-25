"""Jordan's juggle faces, written the way his fight rig writes its expressions: whole replacement
rows over the approved head (rig head.HEAD) or the approved shout, in head space (x 37..59, rows
from 10), 23 characters a row once the ruling spaces are gone. Only the face rows (22 down) are
used: a whole hair map goes over every face, as on the approved v2 heads.

  OW     the hit: the fight set's PAIN eyes (squeezed shut, brows crushed) over the laugh's dropped
         jaw, so his mouth hangs wide open on the blow
  AAH    the tumble: the same with the brows let up a row, a scream
  KO     on the mat: swirl eyes (new) in the approved eye sockets, the defeat's jaw hanging open on a
         gasp

The rest are the fight rig's own (frozen in jj_snap): PAIN (the crash), DAZE (the apex, the bounce).

The hair: the blow knocks his quiff flat and it stays flat to the mat, as it did on every frame of the
09-23 sheet, so the hit, the juggle and the crash read as one sequence. Every juggle face wears the
fight rig's shipped v2 flopped quiff (jordan_hit, jordan_defeat); PAIN and DAZE wear it as the fight
rig's own flopped heads. A face left out of FLOPPED_FACES would wear v2's standing hair instead.
"""
import jj_base as J
from jj_base import S

X0, Y0 = S.X0, S.Y0


def rows_of(name):
    return S.head_rows(name)


def over(base, repl):
    return S.over(base, repl)


def take(rows, y0, y1):
    """{y: row} for rows y0..y1 of a head."""
    return {y: rows[y - Y0] for y in range(y0, y1 + 1) if y - Y0 < len(rows)}


PAIN = S.PAIN
LAUGH = S.LAUGH
DAZE = S.DAZE

# the pain eyes and brows (24-27), the laugh's open jaw (31-39)
OW = over(S.SHOUT, {**take(PAIN, 24, 27), **take(LAUGH, 31, 39)})

AAH = over(OW, {
    24: ".kdci ichhh bbbbd dhhhb ck.",     # the brows lifted off the squeezed lids
})

def patch(rows, spans):
    """rows with (y, i0, keys) spans laid over them ('.' keeps the pixel underneath); i is the
    column in head space (x = 37 + i)."""
    out = [list(r) for r in rows]
    for y, i0, keys in spans:
        for j, ch in enumerate(keys):
            if ch != '.':
                out[y - Y0][i0 + j] = ch
    return [''.join(r) for r in out]


# The swirls: each eye a small white "@" wound into its own socket (the approved eyes sit on row 26,
# the near eyeball in columns 8-12 under its lash line, the far one foreshortened into 17-19), five
# rows tall so it reads at 3x. The far one is four across; the nose bridge between them is kept.
SWIRL_NEAR = [".kkk.", "kWWWk", "kWkWk", "kWWkk", ".kk.."]
SWIRL_FAR = [".kk.", "kWWk", "kWkk", "kWWk", ".kk."]
KO_EYES = ([(24 + r, 8, row) for r, row in enumerate(SWIRL_NEAR)]
           + [(24 + r, 16, row) for r, row in enumerate(SWIRL_FAR)])
KO = patch(DAZE, KO_EYES)

FACES = {'OW': OW, 'AAH': AAH, 'KO': KO}
FLOPPED_FACES = {'OW', 'AAH', 'KO'}


def head(name):
    """('rows', rows, flopped) for jj_fig.head_part, or the rig's own head by its name (which is
    flopped when the fight rig's is: jj_snap.FLOPPED)."""
    if name in FACES:
        return ('rows', FACES[name], name in FLOPPED_FACES)
    return name.lower()


def check():
    bad = []
    for n, rows in FACES.items():
        for i, r in enumerate(rows):
            if len(r) != 23:
                bad.append('%s row %d is %d wide' % (n, Y0 + i, len(r)))
    return bad


if __name__ == '__main__':
    print(check() or 'faces ok')
