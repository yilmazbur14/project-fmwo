"""Hand-drawn stamps for the quake ring's crest: what the crack throws up. Bottom row is the stamp's root.

Flames are the Inferno FX's own small flames (art_source/bixby_inferno_fx/firelib.py, drawn after
bixby_fire_trail.png's tongues), so the ring's fire is the same fire as the rest of his attacks.
Thrown ground is lit the way everything near the crack is: light brown on top, the fire's red and orange
underneath.
"""

FLAME_S = ["..N..",
           ".NpN.",
           ".pPp.",
           "..p.."]
FLAME_M = ["..r..",
           ".rNr.",
           ".NpN.",
           "rpPpr",
           "rPYPr",
           ".rpr."]
FLAME_L = ["...r...",
           "..rNr..",
           "..NpN..",
           ".rpPpr.",
           ".NPYPN.",
           "rpPYPpr",
           "rpYWYpr",
           ".rPYPr.",
           "..rrr.."]
# Upthrust slabs: broken pieces of the floor heaved up along the crack, lit from the upper left, the fire
# glowing under them. They stand on their bottom row.
SHARDS = {
    # big slab tilted up, leaning left: lit face, its thickness dark on the right, fire at the root
    'L1': ["44.....",
           "3443...",
           "33443..",
           "233432.",
           "2233221",
           ".222211",
           ".12221n",
           "..1nNn.",
           "..nPN.."],
    # big slab leaning right
    'L2': [".....44",
           "...4434",
           "..44332",
           ".443322",
           "4433221",
           "332221.",
           "n2211..",
           ".nNn1..",
           "..NPn.."],
    # spike: two broken faces meeting at a ridge
    'S1': ["..4..",
           "..43.",
           ".443.",
           ".4321",
           "44321",
           "33221",
           "3221n",
           "nNNn."],
    # wide broken slab
    'W1': ["...444..",
           ".443333.",
           "44332222",
           "33222111",
           ".2211nn.",
           "..nNNn.."],
    # small chunk
    'M1': [".44.",
           "4432",
           "3321",
           "2n1n",
           ".nN."],
}
# Thrown pieces, two turns each for the tumble: a slab shard, a scorched rock, a clod of earth.
THROWN = {
    'shard': [["..43",
               "4332",
               "221n",
               ".nN."],
              ["4...",
               "332.",
               "2213",
               ".nNn"]],
    'rock': [[".d.",
              "dcb",
              "bnb"],
             ["dd.",
              "cdb",
              ".nb"]],
    'pebble': [["dc",
                "bn"],
               ["cd",
                "nb"]],
    'clod': [["32",
              "21"],
             ["3.",
              "21"]],
}

EMBERS = ['Y', 'P', 'p']
