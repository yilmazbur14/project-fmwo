"""Funko rig: per-figure HEAD (rows 0-7 of master) + TORSO block, shared role-coloured BODY poses.

Coordinates: body pose grids span x = -4..7 (12 cols) and y = -2..4 (7 rows) relative to the torso's
left column (x=0) and first standard torso row (y=0). In the 24x24 frame, x=0 -> 10, y=0 -> 17
(so the grounded feet outline row y=3 lands on frame row 20).

Body role chars:
  K outline     # torso (from TORSO block rows: y=-1 -> row0, y=0 -> row1, y=1 -> row2)
  a sleeve/arm  A arm light   h hand   H hand shadow
  n near leg    N far leg (shadow)
  s near shoe   S near shoe dark   z near shoe accent
  f far shoe    F far shoe dark    Z far shoe accent
"""
from lib import *

FX0, FY0 = 10, 17  # frame position of body origin

BODY_X0, BODY_Y0 = -4, -2


def parse_rows(text):
    rows = [ln for ln in text.strip('\n').split('\n')]
    return rows


class Figure:
    def __init__(self, name, pal, head, head_torso_l, torso, roles, head_rows=8):
        """head: master text (rows 0..7 used as head); head_torso_l: master column of torso-left;
        torso: 3-row text 4 wide; roles: map role char -> palette char"""
        self.name = name
        self.pal = pal
        rows = parse_rows(head)
        self.head_rows_txt = rows[:head_rows]
        self.head = grid('\n'.join(rows[:head_rows]), pal, w=max(len(r) for r in rows))
        self.head_dx = -head_torso_l  # head grid x relative to torso-left
        self.head_dy = -head_rows      # head top relative to torso row y=0
        self.torso = [list(r) for r in parse_rows(torso)]
        self.roles = roles

    def color(self, ch):
        return hx(self.pal[ch]) if isinstance(self.pal[ch], str) else self.pal[ch]

    def body_px(self, pose_text):
        rows = parse_rows(pose_text)
        W = max(len(r) for r in rows)
        out = [[T] * W for _ in rows]
        for yi, r in enumerate(rows):
            y = yi + BODY_Y0
            for xi, ch in enumerate(r):
                x = xi + BODY_X0
                if ch in '. ':
                    continue
                if ch == 'K':
                    out[yi][xi] = BLACK
                elif ch == '#':
                    tr = y + 1
                    if 0 <= tr < len(self.torso) and 0 <= x < len(self.torso[tr]):
                        c = self.torso[tr][x]
                        out[yi][xi] = BLACK if c == 'K' else self.color(c)
                    else:
                        out[yi][xi] = BLACK
                else:
                    pc = self.roles.get(ch, ch)
                    out[yi][xi] = BLACK if pc == 'K' else self.color(pc)
        return out

    def frame(self, pose_text, head_off=(0, 0), body_off=(0, 0), head=None, extra_under=None,
              extra_over=None):
        f = blank(24, 24)
        if extra_under:
            for (x, y, c) in extra_under:
                if 0 <= x < 24 and 0 <= y < 24:
                    f[y][x] = c
        body = self.body_px(pose_text)
        bx, by = body_off
        paste(f, body, FX0 + BODY_X0 + bx, FY0 + BODY_Y0 + by)
        hp = head if head is not None else self.head
        hx_, hy_ = head_off
        paste(f, hp, FX0 + self.head_dx + bx + hx_, FY0 + self.head_dy + by + hy_)
        if extra_over:
            for (x, y, c) in extra_over:
                if 0 <= x < 24 and 0 <= y < 24:
                    f[y][x] = c
        return f


# ------------------------------------------------------------------ poses
#            x: -4 -3 -2 -1  0  1  2  3  4  5  6  7
STAND = """
............
....####....
.KaK####KaK.
.KhK####KhK.
..KsSKKffFK.
..KKKK.KKKK.
............
"""
