"""Liam entrance palette.  Ramps run brightest -> darkest.
Identity colours are copied exactly from approved sprites:
  LIAM_*   <- Assets/Characters/Liam/liam.png
  BIX_*    <- Assets/Characters/Bixby/bixby.png
  WING/LAVA/HORN <- Assets/Characters/Bixby/bixby_beast.png (art_source/bixby_beast/pal.py)
  MASCOT   <- the INVITE card in Assets/UI/Screens/main_menu_bg.png (DB32)
  BRASS    <- Assets/UI/ui_dialogue_frame.png (DB32)
New ramps (throne gold/velvet, carrier clothes) are DB32 colours plus a few in-between steps."""


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def ramp(*cs):
    return [hx(c) for c in cs]


K = BLACK = (0, 0, 0, 255)
WHITE = hx('ffffff')

# ---------------------------------------------------------------- Liam (exact)
L_SKIN = ramp('fadcb8', 'eec39a', 'd9a066', 'b8794a', '8a5236')
L_HAIR = ramp('56352a', '36201a', '1b0f0d', '120a08')
L_JACKET = ramp('c3885a', 'a96b43', '8f563b', '663931', '45283c')
L_COLLAR = ramp('ffffff', 'd6dee5', 'a3b1bc')
L_TIE = ramp('c4d2da', '9badb7', '6e7d86', '4a5563')
L_STEEL = ramp('eef4f7', 'b3c0c9', '7b8893', '4b555e')
L_PANTS = ramp('6b6bb0', '4c4c8c', '3a3a70', '26264c', '181830')
L_SHOES = ramp('6a4a3a', '45302a', '2a1b16')
L_LENS = ramp('ffffff', 'cbdbfc')
L_MOUTH = ramp('9a3a3a', '5a1f22')

# ---------------------------------------------------------------- Bixby (exact)
B_TAN = ramp('e9a55f', 'c97a3c', '9c5428', '6b3419')
B_FUR = ramp('ffffff', 'ede4d6', 'c7bbab', '948779')
B_EAR = ramp('8a5530', '6a3c22', '4a2818', '2c1810')
B_EYE = ramp('f4e9dc', '3b1e12')
B_SADDLE = ramp('7e7a8c', '5c5868', '3a3542', '26222c')
B_COLLAR = ramp('e0524a', 'ac3232', '6e1e22', '5a1a22')
B_IRON = ramp('e8ecf2', 'a8b0be', '5e6674')
B_NOSE = hx('6e6e78')
B_TONGUE = ramp('ffb3c0', 'e8788a', 'b84a60')

# ---------------------------------------------------------------- beast (exact)
WING = ramp('e0524a', 'ac3232', '8a1f38', '5e142c', '3c0c20')
LAVA = ramp('ffffff', 'fff7a0', 'fbf236', 'f58a38', 'df7126', 'ac3232', '6e1e22')
HORN = ramp('7e7a8c', '5c5868', '3a3542', '26222c', '121016')

# ---------------------------------------------------------------- server motifs (DB32)
MASCOT_WHITE = ramp('ffffff', 'cbdbfc', '9badb7')
BLURPLE = ramp('639bff', '5b6ee1', '3f3f74', '222034')
ONLINE = ramp('99e550', '6abe30', '37946e')
BRASS = ramp('fbf236', 'eec39a', 'd9a066', '8a6f30', '524b24')
ROLE_GREY = ramp('c4d2da', '9badb7', '6e7d86', '4a5563')
ROLE_PINK = ramp('f2a5b0', 'd95763', 'ac3232')
ROLE_CYAN = ramp('cbdbfc', '5fcde4', '306082')
ROLE_GREEN = ramp('99e550', '6abe30', '37946e')
ROLE_YELLOW = ramp('fff7a0', 'fbf236', 'd4cc2e')

# ---------------------------------------------------------------- throne (new)
GOLD_A = ramp('fff7a0', 'fbf236', 'e8b23a', 'c07a2c', '8a5424', '4e3018')     # saturated gold
GOLD_B = ramp('fff7a0', 'fbf236', 'd9a066', '8a6f30', '524b24', '2e2a14')     # UI brass-derived
VELVET = ramp('9aa9ff', '7385f0', '5b6ee1', '4a51b8', '3f3f74', '29264f')
WOOD = ramp('c3885a', '8f563b', '663931', '45283c', '2b1a26')

# ---------------------------------------------------------------- carriers (new)
SKIN_LIGHT = L_SKIN
SKIN_TAN = ramp('eec39a', 'd9a066', 'b8794a', '8a5236', '5e3424')
SKIN_DEEP = ramp('b8794a', '8a5236', '663931', '45283c', '2b1a26')
HOODIE_GREEN = ramp('99e550', '6abe30', '37946e', '2b5e4c', '223a33')
HOODIE_PINK = ramp('f5bde3', 'd77bba', 'a9589e', '76428a', '45283c')
TEE_ORANGE = ramp('f7b26a', 'df7126', 'b04e22', '7e3420', '4a2018')
SHIRT_YELLOW = ramp('fff7a0', 'fbf236', 'd4cc2e', '9a8a24', '5e5418')
BEANIE_RED = ramp('e0524a', 'ac3232', '6e1e22', '45141a')
DENIM = ramp('5a8cc4', '306082', '2b4868', '222034')
DARKCLOTH = ramp('6e6a78', '4a4654', '332f3c', '1e1c26')
KHAKI = ramp('e6c58f', 'c9a36a', '9c7a4a', '6e5234', '45301f')
GREYSWEAT = ramp('b9c3ca', '8d98a2', '66707a', '454c55')
HAIR_BLACK = ramp('4a3a44', '2e2230', '1b0f0d', '120a08')
HAIR_BROWN = ramp('a8683a', '7a4628', '52301f', '301a12')
HAIR_BLOND = ramp('fbf236', 'e0b44a', 'b07e34', '6e4e24')
HEADSET = ramp('8a8f99', '5a5e68', '3a3c46', '22222c')
LED = ramp('ffffff', '5fcde4')
CAN = ramp('d8f59c', '99e550', '6abe30', '37946e')
SNEAKER = ramp('ffffff', 'cbd6dc', '9badb7', '6e7d86')
SWEAT = ramp('ffffff', 'cbdbfc', '639bff')
BLUSH = hx('f08a9a')
MOUTH = ramp('d95763', '8a2a3a', '4a1420')

# ---------------------------------------------------------------- fx
IMPACT = ramp('ffffff', 'fff7a0', 'fbf236', 'f58a38', 'df7126', 'ac3232')
VEIN = ramp('ff6a5a', 'e0524a', 'ac3232')


def darker(c, ramps):
    for r in ramps:
        if c in r:
            i = r.index(c)
            return r[min(i + 1, len(r) - 1)]
    return c


ALL_RAMPS = [L_SKIN, L_HAIR, L_JACKET, L_COLLAR, L_TIE, L_STEEL, L_PANTS, L_SHOES, B_TAN, B_FUR, B_EAR, B_SADDLE, B_COLLAR,
             B_IRON, B_TONGUE, WING, LAVA, HORN, MASCOT_WHITE, BLURPLE, ONLINE, BRASS, ROLE_GREY, GOLD_A, GOLD_B, VELVET, WOOD,
             SKIN_TAN, SKIN_DEEP, HOODIE_GREEN, HOODIE_PINK, TEE_ORANGE, SHIRT_YELLOW, BEANIE_RED, DENIM, DARKCLOTH, KHAKI,
             GREYSWEAT, HAIR_BLACK, HAIR_BROWN, HAIR_BLOND, HEADSET, CAN, SNEAKER, SWEAT, IMPACT, VEIN]
