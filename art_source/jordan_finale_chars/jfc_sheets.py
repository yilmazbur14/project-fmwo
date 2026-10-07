"""Assemble and check the three sheets (nothing here writes a file; jfc_export does that).

  jordan_seated     11 frames of 128x128, anchor (64, 127) = the chair's floor contact (the front
                    caster's keyline under x = 64), his y-sort point
                      0-3  gaming, back to the camera, headset on (loop)
                      4-5  swivelling to face screen-left, pulling the headset down
                      6-7  friendly talk pair (shut, open)
                      8-9  glare talk pair (shut, open): "You're Burak!"
                      10   the empty chair, swivelled, same anchor
  player_moustache  8 x 4 of 32x32 (jfc_player)
  moustache_prop    5 of 16x16 (jfc_player)
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402
import jfc_back  # noqa: E402
import jfc_front  # noqa: E402
import jfc_turn  # noqa: E402
import jfc_player as P  # noqa: E402
import jfc_chair as C  # noqa: E402
from PIL import Image  # noqa: E402

SEATED_NAMES = ['gaming_0', 'gaming_1', 'gaming_2', 'gaming_3', 'swivel_tapped', 'swivel_pull',
                'friendly_shut', 'friendly_open', 'glare_shut', 'glare_open', 'empty_chair']
# suggested timings (seconds); 0-3 loop, the talk pairs alternate while a line plays
SEATED_TIMES = [0.18, 0.14, 0.18, 0.14, 0.12, 0.10, 0.16, 0.12, 0.16, 0.12, 0.2]


def seated_frames():
    """[(px, fx)] for the 11 frames, in 128-frame pixels."""
    fr = jfc_back.frames() + jfc_turn.frames() + jfc_front.frames()
    cv, fx = jfc_turn.frame_empty()
    fr.append((cv.px, fx))
    assert len(fr) == 11
    return fr


def seated_image(frames=None):
    frames = frames or seated_frames()
    out = Image.new('RGBA', (B.FW * len(frames), B.FH), (0, 0, 0, 0))
    for i, (px, fx) in enumerate(frames):
        out.alpha_composite(B.image(px), (i * B.FW, 0))
    return out


def chair_pixels(frame_index):
    """The pixels of the chair alone at that frame's yaw (to split the black ratio)."""
    yaw = {4: -20, 5: -100}.get(frame_index, 0 if frame_index < 4 else -135)
    return set(C.build(yaw).px)


def check_seated():
    """Per frame: numbers and lint. Returns (rows, problems)."""
    frames = seated_frames()
    allowed = {B.PAL[k][:3] for k in B.ALLOWED}
    rows, problems = [], []
    for i, (px, fx) in enumerate(frames):
        im = B.image(px)
        st = B.stats(im)
        a = B.audit(px, fx)
        cols = {c[:3] for c in im.get_flattened_data() if c[3]}
        low = max(y for (x, y) in px)
        under = [x for (x, y) in px if y == low]
        chair = chair_pixels(i)
        him = {q: k for q, k in px.items() if q not in chair and q not in fx}
        him_black = sum(1 for k in him.values() if k == 'k') / max(1, len(him))
        rows.append((i, SEATED_NAMES[i], st['opaque'], st['colours'], st['black'], him_black, st['semi'],
                     {k: len(v) for k, v in a.items()}, low, (min(under), max(under))))
        tag = 'jordan_seated f%d' % i
        if cols - allowed:
            problems.append('%s: colours outside the approved 40' % tag)
        if st['semi']:
            problems.append('%s: semi-transparent pixels' % tag)
        if any(a[k] for k in ('gaps', 'lone', 'holes', 'keys')):
            problems.append('%s: lint %s' % (tag, {k: a[k][:4] for k in a if a[k]}))
        if low != B.ANCHOR[1] or not (min(under) <= B.ANCHOR[0] <= max(under)):
            problems.append('%s: floor contact not on the anchor (%d, %s)' % (tag, low, (min(under), max(under))))
    return rows, problems


def check_player():
    src = P.measure_source()
    im = P.sheet_image()
    data = list(im.get_flattened_data())
    op = [c for c in data if c[3]]
    allowed = {v[:3] for v in P.PPAL.values()}
    problems = []
    if {c[:3] for c in op} - allowed:
        problems.append('player_moustache: colours outside his 7')
    if sorted({c[3] for c in data}) != [0, 255]:
        problems.append('player_moustache: semi-alpha')
    # every frame keeps his soles on his own sole row (27/28) and his body on its own columns
    fr = P.frames()
    sheet = P.source()
    for ri, rn in enumerate(P.ROWS):
        ref = P.cell_px(sheet, ri, 0)
        ref_low = max(y for (x, y) in ref)
        for cn in P.COLS:
            low = max(y for (x, y) in fr[rn][cn])
            if low != ref_low:
                problems.append('player_moustache %s %s: lowest row %d, his is %d' % (rn, cn, low, ref_low))
    pr = P.prop_image()
    pdata = list(pr.get_flattened_data())
    if {c[:3] for c in pdata if c[3]} - {(0, 0, 0)}:
        problems.append('moustache_prop: not his black')
    low4 = max(y for (x, y) in P.PROP[4])
    if low4 != 15:
        problems.append('moustache_prop f4: lowest texel %d, not 15' % low4)
    return {'source': src, 'sheet_colours': len({c[:3] for c in op}),
            'sheet_black': sum(1 for c in op if c[:3] == (0, 0, 0)) / len(op)}, problems


if __name__ == '__main__':
    rows, problems = check_seated()
    for r in rows:
        print('f%-2d %-14s opaque %4d colours %2d black %.3f (him alone %.3f) semi %d lint %s floor row %d x %s'
              % r)
    info, p2 = check_player()
    print(info)
    for p in problems + p2:
        print('PROBLEM', p)
    print('problems:', len(problems + p2))
