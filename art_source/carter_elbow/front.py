"""Front-view frames 3-4 composited from Carter's real idle torso pixels + new limbs."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from puppet import *
import heads

CARTER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/CarterAndJosh/carter.png'
IDLE = load_grid_from_png(CARTER, 64, 0)


def blank():
    return [['.'] * 64 for _ in range(64)]


def layer(base, top):
    for y in range(64):
        for x in range(64):
            if top[y][x] != '.':
                base[y][x] = top[y][x]


def idle_rows(rows, x0=0, x1=64, drop_cols=None):
    """return list of row-strings from idle frame; '.' outside torso kept as ' ' (skip)."""
    out = []
    for r in rows:
        line = ''
        for x in range(x0, x1):
            ch = IDLE[r][x]
            if drop_cols and drop_cols(r, x):
                ch = '.'
            line += ' ' if ch == '.' else ch
        out.append(line)
    return out


def torso_patch(rows, left_arm=True, right_arm=True):
    """Carter idle upper body, optionally without the hanging arms.
    arms occupy x<=21 / x>=42 from row 32 down; deltoid bulge x<=17 / x>=46 rows 26-31."""
    def drop(r, x):
        if r >= 32 and ((x <= 21 and not left_arm) or (x >= 42 and not right_arm)):
            return True
        if r >= 32 and (x <= 21 or x >= 42):
            return True  # always drop hanging forearms; arms are redrawn
        if 26 <= r <= 31:
            if not left_arm and x <= 17:
                return True
            if not right_arm and x >= 46:
                return True
        return False
    return idle_rows(rows, 0, 64, drop)


def render_parts(parts):
    g, _ = render(parts)
    return g


def superman():
    g = blank()
    # legs + boots (behind torso)
    legs = [cap(27.5, 55, 26.5, 58, 3.8, 3.5, group='legL'),
            poly([(22.25, 57.25), (30.75, 57.25), (29.75, 62.25), (23.25, 62.25)], rad=2.0, mat='boot', group='legL'),
            cap(36.5, 55, 37.5, 56.5, 3.8, 3.5, group='legR', bias=-0.1),
            poly([(33.75, 55.75), (41.75, 55.75), (40.75, 60.75), (34.75, 60.75)], rad=2.0, mat='boot', group='legR')]
    layer(g, render_parts(legs))
    # idle torso rows 20..51 shifted +3, both deltoid bulges removed (arms redrawn)
    rows = list(range(20, 52))
    patch = torso_patch(rows, left_arm=False, right_arm=False)
    stamp(g, 0, 23, patch)
    # image-right arm: deltoid capping the shoulder, fist clenched on hip
    armR = [cap(50.5, 40, 46.5, 47, 3.3, 2.9, group='armRf'),
            ell(45.5, 49, 3.5, 3.3, 0, group='armRf'),
            ell(44.5, 30.5, 4.8, 4.4, 0, group='armR'),
            cap(45, 31, 50.5, 40, 4.1, 3.3, group='armR')]
    layer(g, render_parts(armR))
    # image-left arm straight up from the shoulder
    armL = [ell(19.5, 29.5, 4.8, 4.4, 0, group='armL'),
            cap(19.5, 28, 17, 17, 4.1, 3.4, group='armL'),
            cap(17, 17, 16, 9, 3.4, 3.1, group='armL'),
            ell(16, 5.5, 3.9, 3.6, 0, group='armL')]
    layer(g, render_parts(armL))
    stamp(g, 23, 9, heads.FRONT)
    return g


def squat():
    g = blank()
    # legs: thighs out to knees, shins down, boots wide
    legs = []
    for sgn, grp in ((-1, 'legL'), (1, 'legR')):
        X = lambda dx: 32.0 + sgn * dx
        legs += [cap(X(6), 52, X(15), 53.5, 4.4, 4.0, group=grp),
                 cap(X(15), 53.5, X(15), 58, 4.0, 3.5, group=grp),
                 poly([(X(10.75), 57.25), (X(19.25), 57.25), (X(19.25), 62.25), (X(10.75), 62.25)], rad=2.0, mat='boot', group=grp)]
    layer(g, render_parts(legs))
    # compressed idle torso: drop two ab rows + two trunk rows
    rows = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 40, 42, 43, 44, 45, 48, 50, 51]
    patch = torso_patch(rows, left_arm=True, right_arm=True)
    stamp(g, 0, 31, patch)
    # arms swung down/back: fists behind knees
    for sgn, grp in ((-1, 'armL'), (1, 'armR')):
        X = lambda dx: 32.0 + sgn * dx
        arm = [cap(X(19.5), 50, X(16), 54, 3.0, 2.8, group=grp + 'f', bias=-0.1),
               ell(X(16), 55, 3.3, 3.1, 0, group=grp + 'f', bias=-0.1),
               ell(X(14.5), 40.5, 4.4, 4.2, 0, group=grp),
               cap(X(15), 41, X(19.5), 50, 3.8, 3.1, group=grp)]
        layer(g, render_parts(arm))
    stamp(g, 23, 16, heads.FRONT)
    return g


if __name__ == '__main__':
    fr = [squat(), superman()]
    for i, gg in zip((3, 4), fr):
        with open(os.path.join(HERE, 'frame%d_base.txt' % i), 'w') as f:
            f.write(grid_to_text(gg))
    write_strip(os.path.join(HERE, 'front_wip.png'), fr)
    print('ok')
