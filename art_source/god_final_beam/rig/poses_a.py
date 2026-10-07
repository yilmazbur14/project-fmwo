"""Staging A: side-on, facing right. 48x48 cells, Burak's own texel scale; the cell drawn centred on MainPlayer's
origin keeps his soles exactly where his 32x32 sheet puts them (sole rows 35-36 here = rows 27-28 there, +8)."""
from pix import *

P4 = repo_img("Assets/Characters/MainPlayer/player_4dir_sheet.png")


def head(g, x, y, tails="up0", face="calm"):
    """Right-facing head with its hair top at (x+1, y). Tails stream from the band's back end at (x-2, y+2)."""
    g.put(x + 1, y, "###")
    g.put(x, y + 1, "#####")
    g.put(x - 1, y + 2, "rrrrrr")
    g.put(x, y + 3, "#rrrr")
    g.put(x, y + 4, "dssss")
    g.put(x, y + 5, "dsss")
    if face == "shout":
        g.put(x + 4, y + 5, "d")      # open mouth notch
    if face == "grit":
        g.put(x + 3, y + 5, "d")
    bx, by = x - 2, y + 2
    T = {
        # updraft: both ends lifting
        "up0": [(0, -1), (-1, -2), (-1, -3), (-2, -4), (-1, 0), (-2, -1), (-3, -1)],
        "up1": [(0, -1), (0, -2), (-1, -3), (-1, -4), (-1, 0), (-2, 0), (-3, -1)],
        "up2": [(0, -1), (-1, -1), (-2, -2), (-2, -3), (-1, 0), (-2, 1), (-3, 0)],
        # blown straight back by the recoil
        "back0": [(0, 0), (-1, 0), (-2, -1), (-3, -1), (-1, 1), (-2, 1), (-3, 2)],
        "back1": [(0, 0), (-1, -1), (-2, -1), (-3, 0), (-1, 1), (-2, 2), (-3, 2)],
        # resting (as his own idle)
        "rest": [(0, -2), (1, -1), (0, 0)],
        "fall": [(0, 0), (-1, 1), (-1, 2), (0, 1), (-2, 2)],
    }
    for dx, dy in T[tails]:
        g.put(bx + dx, by + dy, "r")
    return g


def legs_wide(g, dy=0):
    g.put(21, 27 + dy, "nlblbl")
    g.put(19, 28 + dy, "nnbbbbbbb")
    g.put(19, 29 + dy, "nbbbbbbbbb")
    g.put(18, 30 + dy, "nbbbbbbbbbbb")
    g.put(17, 31 + dy, "lbbbbnnbbbbbb")
    g.put(17, 32 + dy, "lbbn....bbbbbb")
    g.put(16, 33 + dy, "bln.......bbbbb")
    g.put(16, 34, "sd.........dss")
    g.put(15, 35, "sd..........dss")
    g.put(14, 36, "##...........###")
    g.put(13, 37, "###...........####")
    return g


def torso_open(g, dy=0):
    g.put(21, 20 + dy, "dsssssd")
    g.put(20, 21 + dy, "dssssssd")
    g.put(20, 22 + dy, "ddsdsdsd")
    g.put(20, 23 + dy, "dsdssdsd")
    g.put(21, 24 + dy, "dsssssd")
    g.put(21, 25 + dy, "ddssss")
    g.put(22, 26 + dy, "dsss")
    return g


def idle():
    return from_sheet(P4, 0, 3)


def step():
    g = G()
    head(g, 24, 13, "rest")
    # torso as his idle, dropping a row; arms swinging down and back towards the hip
    g.put(21, 19, "dsssssd")
    g.put(20, 20, "dssssssd")
    g.put(20, 21, "dsdsdsdd")
    g.put(20, 22, "dssdssd")
    g.put(20, 23, "dssssssd")
    g.put(21, 24, "dsssss")
    g.put(22, 25, "dsss")
    g.put(19, 20, "s").put(18, 21, "sd").put(18, 22, "sd").put(18, 23, "sd").put(18, 24, "sd")
    g.put(17, 25, "bbb").put(17, 26, "bnn")
    # far glove coming down at the front of the hips
    g.put(27, 21, "sd").put(27, 22, "sd").put(27, 23, "bb").put(27, 24, "nn")
    g.put(21, 26, "nlblbl")
    g.put(20, 27, "nbbbbbbb")
    g.put(19, 28, "nbbbbbbbbb")
    g.put(19, 29, "nbbbbbbbbbb")
    g.put(18, 30, "lbbbbnnbbbbb")
    g.put(18, 31, "lbbn...bbbbbb")
    g.put(18, 32, "bln.....bbbbb")
    g.put(18, 33, "sd.......dss")
    g.put(17, 34, "sd........dss")
    g.put(17, 35, "sd.........ds")
    g.put(16, 36, "##.........###")
    g.put(15, 37, "###.........####")
    return g


def cup(tails="up0", bob=0, hem=0, face="grit"):
    g = G()
    head(g, 24, 14 + bob, tails, face)
    torso_open(g, bob)
    # near arm: chunky upper arm back and down, elbow behind, forearm in to the hip
    g.put(19, 21 + bob, "s")
    g.put(18, 22 + bob, "ssd")
    g.put(17, 23 + bob, "ssd")
    g.put(16, 24 + bob, "sdd")
    g.put(15, 25, "sd")
    # gloves cupped at the rear hip: near glove on top, far glove under, the mouth of the cup to the back
    g.put(14, 26, "bbb")
    g.put(14, 27, "nb")
    g.put(14, 30, "bn")
    g.put(14, 31, "nnn")
    g.put(16, 30, "sd")
    g.put(17, 29, "d")
    legs_wide(g)
    if hem == 1:   # shorts hem fluttering in the aura
        g.put(16, 33, "l").put(15, 33, "b").put(31, 33, "b")
    if hem == 2:
        g.put(17, 32, "l").put(31, 32, "bb").put(32, 33, "n")
    return g


def thrust1():
    """Arms swinging through: gloves together in front of the belly, travelling up and out."""
    g = G()
    head(g, 25, 14, "back0", "shout")
    g.put(22, 20, "dsssssd")
    g.put(21, 21, "dsssssssd")
    g.put(21, 22, "ddsdsdsdd")
    g.put(21, 23, "dsdssdssd")
    g.put(22, 24, "dsssssd")
    g.put(22, 25, "ddssss")
    g.put(23, 26, "dsss")
    # arms forward and down-out of the hip, gloves leading at waist height out front
    g.put(28, 21, "sd").put(29, 22, "ssd").put(30, 23, "ssd").put(31, 24, "ssd")
    g.put(33, 23, "bb").put(33, 24, "bnb").put(34, 25, "nn").put(34, 26, "nn")
    legs_wide(g)
    return g


def arms_out(g, sx, sy, n, shake=0):
    """Both arms thrust up-right along the 45 degree line from the shoulder (sx, sy), gloves at the end."""
    for i in range(n):
        g.put(sx + i, sy - i + shake, "ssd")
        g.put(sx + i, sy - i + 1 + shake, "dd")
    ex, ey = sx + n, sy - n + shake
    g.put(ex, ey - 2, "bb")
    g.put(ex, ey - 1, "bbbn")
    g.put(ex + 1, ey, "bnnn")
    g.put(ex + 2, ey + 1, "nn")
    return ex, ey


def thrust2(tails="back0", shake=0, slide=0):
    g = G()
    # lunge: front knee bent forward, back leg long and straight
    head(g, 24, 15, tails, "shout")
    g.put(21, 21, "dsssssd")
    g.put(20, 22, "dssssssd")
    g.put(20, 23, "ddsdsdsd")
    g.put(20, 24, "dsdssdsd")
    g.put(21, 25, "dsssssd")
    g.put(21, 26, "ddssss")
    g.put(22, 27, "dsss")
    arms_out(g, 26, 21, 6, shake)
    g.put(21, 28, "nlblbl")
    g.put(19, 29, "nnbbbbbbb")
    g.put(18, 30, "nbbbbbbbbbb")
    g.put(17, 31, "lbbbbbnnbbbbb")
    g.put(16, 32, "lbbbn....bbbbbb")
    g.put(15, 33, "lbln.......bbbbb")
    g.put(14 - slide, 34, "sd..........dss")
    g.put(13 - slide, 35, "sd...........dss")
    g.put(12 - slide, 36, "##............###")
    g.put(11 - slide, 37, "###...........####")
    return g


def hold(i):
    return thrust2("back%d" % (i % 2), shake=(i % 2), slide=i % 2)


def fail1():
    """The ball pops in his hands: thrown back, arms flung out, chin up."""
    g = G()
    head(g, 22, 13, "fall")
    g.clear(22, 18, 26, 18)
    g.put(22, 17, "dssss")
    g.put(22, 18, "dsss")
    g.put(26, 18, "d")
    g.put(19, 19, "dssssd")
    g.put(18, 20, "dssssssd")
    g.put(18, 21, "dsdsdsdd")
    g.put(18, 22, "dssdssd")
    g.put(19, 23, "dsssssd")
    g.put(19, 24, "dssss")
    g.put(20, 25, "dsss")
    # arms flung wide: near arm up and back, far arm out front, gloves open
    g.put(17, 19, "sd").put(16, 18, "sd").put(15, 17, "sd").put(13, 15, "bb").put(13, 16, "bn")
    g.put(25, 20, "ssd").put(27, 19, "ssd").put(29, 17, "bb").put(29, 18, "nn")
    g.put(19, 26, "nlblbl")
    g.put(18, 27, "nbbbbbbb")
    g.put(18, 28, "nbbbbbbbbb")
    g.put(17, 29, "lbbbbnnbbbb")
    g.put(17, 30, "lbbn..bbbbb")
    g.put(17, 31, "bln....bbbbb")
    g.put(17, 32, "sd......dss")
    g.put(16, 33, "sd.......dss")
    g.put(16, 34, "sd........dss")
    g.put(15, 35, "##.........dss")
    g.put(14, 36, "###.........###")
    g.put(26, 37, "####")
    return g


def fail2():
    """Stumbling back a step, gloves up by his face, front foot off the floor."""
    g = G()
    head(g, 22, 14, "fall", "grit")
    g.put(20, 20, "dsnnnsdd")
    g.put(19, 21, "dssnnnsdd")
    g.put(19, 22, "dsdsdsddd")
    g.put(19, 23, "dssdssdd")
    g.put(19, 24, "dssssssd")
    g.put(20, 25, "dsssss")
    g.put(21, 26, "dsss")
    g.put(27, 18, "bb").put(27, 19, "bb")
    g.put(20, 27, "nlblbl")
    g.put(20, 28, "nbbbbbb")
    g.put(19, 29, "nbbbbbbbb")
    g.put(19, 30, "nbbbbbbbbb")
    g.put(18, 31, "lbbbbnnbbbbb")
    g.put(18, 32, "lbbn...bbbbb")
    g.put(18, 33, "bln.....ddsb")
    g.put(19, 34, "sd.....dss")
    g.put(18, 35, "sd......###")
    g.put(17, 36, "##......####")
    g.put(16, 37, "###")
    return g


def fail3():
    """Hunched, hands on knees, out of breath."""
    g = G()
    head(g, 26, 17, "fall", "grit")
    g.put(21, 22, "dsssss")
    g.put(20, 23, "dsssssssd")
    g.put(20, 24, "dsdsdsdsd")
    g.put(20, 25, "dssdssdd")
    g.put(21, 26, "ddsssd")
    g.put(28, 23, "sd").put(28, 24, "sd").put(28, 25, "sd").put(28, 26, "bbb").put(28, 27, "nbn")
    g.put(19, 27, "nlblbl")
    g.put(18, 28, "nbbbbbbbb")
    g.put(18, 29, "nbbbbbbbbbb")
    g.put(17, 30, "lbbbbnnbbbbb")
    g.put(17, 31, "lbbbn..bbbbbb")
    g.put(16, 32, "lbbn.....bbbbb")
    g.put(16, 33, "bln.......bbbb")
    g.put(16, 34, "sd.........dss")
    g.put(15, 35, "sd..........dss")
    g.put(14, 36, "##...........###")
    g.put(13, 37, "###...........####")
    return g


FRAMES = {
    "idle": idle,
    "step": step,
    "charge0": lambda: cup("up0", 0, 0),
    "charge1": lambda: cup("up1", -1, 1),
    "charge2": lambda: cup("up2", 0, 2),
    "thrust1": thrust1,
    "thrust2": lambda: thrust2("back0"),
    "hold0": lambda: hold(0),
    "hold1": lambda: hold(1),
    "fail0": fail1,
    "fail1": fail2,
    "fail2": fail3,
}

if __name__ == "__main__":
    imgs = [f().img() for f in FRAMES.values()]
    zoomed(strip(imgs[:6]), 8).save(WORK + "/poses_a_1.png")
    zoomed(strip(imgs[6:]), 8).save(WORK + "/poses_a_2.png")
