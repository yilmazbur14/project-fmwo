"""hand-drawn lower legs (knee cop + sabaton). Left leg authored; right leg mirrored in
geometry while keeping the left-lit tone gradient."""
LEFT = [
    "............................",
    ".........kWAAAABBBBBBBCCDk..",
    "........kAWAAABBBBBBBBCCDDk.",
    "........kBBBBBBCCCCCCCDDDEk.",
    "....kkkkkkkkkkkkkkkkkkkkkkk.",
    "...kAWWAAAAABBBBBBBBBCCCCDk.",
    "..kBAAAABBBBBBBBBBCCCCCCDDDk",
    ".kkkkkkkkkkkkkkkkkkkkkkkkkkk",
    "kAWWAAAAABBBBBBBBBBBCCCCCDDk",
    "kBBBCCCCCCCCCCCCCDDDDDDDDEEk",
    ".kkkkkkkkkkkkkkkkkkkkkkkkkk.",
]
X0L, Y0 = 17, 85


def _right_rows(dark_shift=True):
    shift = {'W': 'A', 'A': 'B', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E'}
    out = []
    for row in LEFT:
        r = row[::-1]
        # re-orient each tone run so light stays on the left
        chars = list(r)
        i = 0
        while i < len(chars):
            if chars[i] not in 'k.':
                j = i
                while j < len(chars) and chars[j] not in 'k.':
                    j += 1
                run = chars[i:j][::-1]
                if dark_shift:
                    run = [shift.get(c, c) for c in run]
                chars[i:j] = run
                i = j
            else:
                i += 1
        out.append(''.join(chars))
    return out


def stamp_legs(cv):
    left = '\n'.join(LEFT)
    right = '\n'.join(_right_rows())
    cv.stamp(left, X0L, Y0)
    # mirror x: left spans X0L..X0L+27 -> right spans 95-(X0L+27)..95-X0L
    cv.stamp(right, 95 - (X0L + len(LEFT[0]) - 1), Y0)


if __name__ == '__main__':
    for r in _right_rows():
        print(r)
