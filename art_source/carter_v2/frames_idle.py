from approved import *


def f0():
    return copyg(IDLE)


def f1():
    return shifted(IDLE, IDLE_LABEL, UPPER, 0, 1)


def f2():
    return shifted(IDLE, IDLE_LABEL, HEADG, 0, 1)
