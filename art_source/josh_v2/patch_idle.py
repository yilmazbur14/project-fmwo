"""Hand-placed accents for the idle, in FINAL frame coordinates (after the 1px shift)."""
PATCHES = [
    # chin cast shadow on upper chest
    (29, 30, ["dddddddddd"]),
    (30, 31, ["ddddddd"]),
    # near pec highlight + spec
    (19, 31, ["1aaaa"]),
    (19, 32, ["aaaa"]),
    (20, 30, ["aaa"]),
    # far pec highlight
    (35, 32, ["aaa"]),
    (36, 31, ["aa"]),
    # navel
    (32, 42, ["f"]),
    # bicep repaint (lit upper-left, crisp shadow lower-right)
    (12, 24, ["a1"]),
    (12, 25, ["aas"]),
    (11, 26, ["aaass"]),
    (11, 27, ["aasss"]),
    (11, 28, ["sssss"]),
    (11, 29, ["sssdd"]),
    (11, 30, ["ssddd"]),
    (10, 31, ["sssddd"]),
    (9, 32, ["ssssddd"]),
]


def apply(c, block):
    for (x, y, rows) in PATCHES:
        block(c, x, y, rows)
