"""Staging B: from behind, at the bottom centre, firing straight up the screen. 48x48 cells, Burak's own texel scale,
soles on the same rows as his 32x32 sheet's when the cell is drawn centred on MainPlayer's origin (+8, +8)."""
from pix import *

P4 = repo_img("Assets/Characters/MainPlayer/player_4dir_sheet.png")


def head(g, x, y, tails="up0"):
    """Back of the head, hair top row y, head columns x..x+4."""
    g.put(x + 1, y, "###")
    g.put(x, y + 1, "#####")
    g.put(x, y + 2, "rrrrr")
    g.put(x, y + 3, "##r##")
    g.put(x, y + 4, "#####")
    g.put(x, y + 5, "d###d")
    g.put(x + 1, y + 6, "sds")
    kx, ky = x + 2, y + 3
    T = {
        "up0": [(-1, -1), (-2, -2), (-2, -3), (-3, -4), (1, -1), (2, -2), (3, -2)],
        "up1": [(-1, -1), (-1, -2), (-2, -3), (-2, -4), (1, -1), (2, -1), (3, -2)],
        "up2": [(-1, -1), (-2, -1), (-3, -2), (-3, -3), (1, -1), (2, -2), (2, -3)],
        # pressed down by the recoil, streaming back towards the camera
        "down0": [(-3, 0), (-4, 1), (-4, 2), (-5, 3), (3, 0), (4, 1), (4, 2), (5, 3)],
        "down1": [(-3, 0), (-3, 1), (-4, 2), (-4, 3), (3, 0), (3, 1), (4, 2), (4, 3)],
        "rest": [(-3, -1), (-2, 0)],
    }
    for dx, dy in T[tails]:
        g.put(kx + dx, ky + dy, "r")
    return g


def back(g, x, y):
    """His back, shoulders at row y, columns x..x+9."""
    g.put(x, y, "sdssdssds")
    g.put(x, y + 1, "ssdsdsdss")
    g.put(x + 1, y + 2, "sssdssss")
    g.put(x + 1, y + 3, "sssdsss")
    g.put(x + 2, y + 4, "ssdsss")
    g.put(x + 2, y + 5, "ssssss")
    return g


def legs_wide(g, x=17, y=25, slide=0):
    g.put(x + 2, y, "bblblbln")
    g.put(x + 1, y + 1, "bbbbbbbbbn")
    g.put(x, y + 2, "bbbbbbbbbbbn")
    g.put(x, y + 3, "bbbbbbbbbbbbn")
    g.put(x - 1, y + 4, "bbbbb...bbbbbn")
    g.put(x - 1, y + 5, "bbbb.....bbbbn")
    g.put(x - 2, y + 6, "lsd.......ssd")
    g.put(x - 2, y + 7, "sd.........ssd")
    g.put(x - 3 - slide, y + 8, "sd...........ssd")
    g.put(x - 3 - slide, y + 9, "##...........###")
    g.put(x - 4 - slide, y + 10, "###.........." + " " * slide + "####")
    return g


def idle():
    return from_sheet(P4, 0, 1)


def step():
    g = G()
    head(g, 21, 13, "rest")
    back(g, 19, 20)
    # arms dropping, the right one drawing back to the hip
    g.put(18, 20, "bb").put(18, 21, "bn").put(18, 22, "s").put(18, 23, "sd")
    g.put(28, 20, "sd").put(29, 21, "sd").put(29, 22, "sd").put(29, 23, "bb").put(29, 24, "nn")
    g.put(20, 26, "bblblbl")
    g.put(19, 27, "bbbbbbbbn")
    g.put(19, 28, "bbbbbbbbbn")
    g.put(18, 29, "bbbbbbbbbbbn")
    g.put(18, 30, "bbbbb..bbbbn")
    g.put(18, 31, "bbbb....bbbn")
    g.put(18, 32, "sd.......ssd")
    g.put(17, 33, "sd........ssd")
    g.put(17, 34, "##.........ssd")
    g.put(16, 35, "###........###")
    g.put(28, 36, "####")
    return g


def cup(tails="up0", bob=0, hem=0):
    g = G()
    head(g, 21, 14 + bob, tails)
    back(g, 19, 21 + bob)
    # left arm: the near shoulder dips, the forearm crosses in front of him (hidden), its glove under the right one
    g.put(18, 21 + bob, "s").put(18, 22 + bob, "sd")
    # right arm: elbow cocked out and back, gloves cupped at the right hip, the cup open to the right
    g.put(28, 21 + bob, "sd")
    g.put(29, 22 + bob, "ssd")
    g.put(30, 23 + bob, "sssd")
    g.put(32, 24, "sd")
    g.put(31, 25, "bbb")
    g.put(31, 26, "bnn")
    # the left hand comes across under him (hidden) and cups from below
    g.put(29, 29, "dd")
    g.put(31, 29, "nbb")
    g.put(31, 30, "nnn")
    legs_wide(g)
    if hem == 1:
        g.put(15, 30, "b").put(30, 29, "n")
    if hem == 2:
        g.put(16, 29, "b").put(31, 30, "n")
    return g


def thrust1():
    """Arms coming up from the hip, gloves at shoulder height, closing on the middle."""
    g = G()
    head(g, 21, 14, "down0")
    back(g, 19, 21)
    g.put(17, 21, "ss").put(16, 20, "sd").put(16, 19, "sd").put(16, 17, "bb").put(16, 18, "bn")
    g.put(28, 21, "ss").put(29, 20, "sd").put(29, 19, "sd").put(29, 17, "bb").put(29, 18, "nb")
    legs_wide(g)
    return g


def thrust2(tails="down0", shake=0, slide=0):
    """Both arms thrust straight up the screen (forward, at him), gloves together over his head."""
    g = G()
    head(g, 21, 15, tails)
    back(g, 19, 22)
    # arms: up from the shoulders, converging to the gloves above the head
    s = shake
    g.put(18, 21, "sd").put(18, 20, "sd").put(19, 19, "sd").put(19, 18, "sd").put(19, 17, "sd")
    g.put(27, 21, "sd").put(27, 20, "sd").put(26, 19, "ds").put(26, 18, "ds").put(26, 17, "ds")
    g.put(20, 16, "s").put(26, 16, "s")
    g.put(20, 12 + s, "bbb.bbb")
    g.put(20, 13 + s, "bbn.bnb")
    g.put(20, 14 + s, "nnb.bnn")
    g.put(20, 15, "sd")
    g.put(25, 15, "ds")
    legs_wide(g, y=26, slide=slide)
    return g


def hold(i):
    return thrust2("down%d" % (i % 2), shake=(i % 2), slide=i % 2)


def fail1():
    """The ball pops: thrown back, arms flung out wide, head tipped back."""
    g = G()
    head(g, 21, 15, "down1")
    back(g, 19, 22)
    g.put(17, 22, "ss").put(15, 21, "sss").put(13, 20, "sss").put(11, 18, "bb").put(11, 19, "bn")
    g.put(28, 22, "ss").put(29, 21, "sss").put(31, 20, "sss").put(34, 18, "bb").put(34, 19, "nb")
    legs_wide(g, y=27)
    return g


def fail2():
    """Stumbling back towards the camera, gloves up by his face."""
    g = from_sheet(P4, 0, 1)
    g.shift(0, 2)
    g.put(17, 18, "bb").put(17, 19, "bn").put(28, 18, "bb").put(28, 19, "nb")
    g.put(18, 20, "s").put(27, 20, "s")
    g.clear(26, 34, 31, 38)
    g.put(26, 34, "ssd").put(26, 35, "###").put(26, 36, "####")
    return g


def fail3():
    """Bent double, hands on knees, out of breath (his back to us, head dropped)."""
    g = G()
    head(g, 21, 19, "rest")
    g.clear(21, 19, 25, 19)
    g.put(19, 23, "sdssdssds")
    g.put(19, 24, "ssdsdsdss")
    g.put(19, 25, "sssdssss")
    g.put(17, 24, "sd").put(16, 25, "sd").put(16, 26, "sd").put(15, 27, "bb").put(15, 28, "nn")
    g.put(28, 24, "sd").put(29, 25, "sd").put(29, 26, "sd").put(29, 27, "bb").put(29, 28, "nn")
    legs_wide(g, y=26)
    return g


FRAMES = {
    "idle": idle,
    "step": step,
    "charge0": lambda: cup("up0", 0, 0),
    "charge1": lambda: cup("up1", -1, 1),
    "charge2": lambda: cup("up2", 0, 2),
    "thrust1": thrust1,
    "thrust2": lambda: thrust2("down0"),
    "hold0": lambda: hold(0),
    "hold1": lambda: hold(1),
    "fail0": fail1,
    "fail1": fail2,
    "fail2": fail3,
}

if __name__ == "__main__":
    imgs = [f().img() for f in FRAMES.values()]
    zoomed(strip(imgs[:6]), 8).save(WORK + "/poses_b_1.png")
    zoomed(strip(imgs[6:]), 8).save(WORK + "/poses_b_2.png")
