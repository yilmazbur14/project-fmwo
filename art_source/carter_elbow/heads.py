"""Head patches. ' ' = keep what is underneath."""

# Carter's exact front head from carter.png frame 0, rows 4..19, x 23..40
FRONT = [
    "    KKKKKKKKKK    ",
    "  KKssssssssssKK  ",
    "  KshhhsssssssssK ",
    " KshhhssssssssssK ",
    " KshhsssssssssssK ",
    "KssssssssssssssssK",
    "KsooossssssssooosK",
    "KssssossssssossssK",
    "KsswessssssssewmsK",
    "KsswessssssssewsmK",
    "KmssssssmmsssssGmK",
    "KmssssssmssssssgsK",
    " KOOOssssssssOOOK ",
    " KOOOOOOOOOOOOOOK ",
    "  KOOOOnnnnOOOOK  ",
    "   rOOOOOOOOOrK   ",
]

# 3/4 view turned to image-left (we see his left side -> ear + gold stud on image right)
TQ_LEFT = [
    "    KKKKKKKKKK    ",
    "  KKssssssssssKK  ",
    "  KshhhsssssssssK ",
    " KshhhssssssssssK ",
    " KshhsssssssssssK ",
    "KssssssssssssssmmK",
    "KooossssoooossssmK",
    "KsssossosssssssdmK",
    "KsewssssewssssdmmK",
    "KsewssssewssssdmsK",
    "KmsssmmssssssssdsK",
    "KmssssmssssssssGsK",
    " KOOOssssssOOOOgK ",
    " KOOOOOOOOOOOOOOK ",
    " KOOnnnOOOOOOOOK  ",
    "  KrOOOOOOOOOrK   ",
    "   KKrrrrrrrKK    ",
]

# same but eyes squeezed shut + gritted teeth (impact)
TQ_LEFT_OUCH = [
    "    KKKKKKKKKK    ",
    "  KKssssssssssKK  ",
    "  KshhhsssssssssK ",
    " KshhhssssssssssK ",
    " KshhsssssssssssK ",
    "KssssssssssssssmmK",
    "KsooossssoooosssmK",
    "KssssosossssssdmmK",
    "KseeessseeesssdmmK",
    "KssssssssssssssdmK",
    "KmsssmmssssssssdsK",
    "KmssssmssssssssGsK",
    " KOOOssssssOOOOgK ",
    " KOOOOOOOOOOOOOOK ",
    " KOnwwwnOOOOOOOK  ",
    "  KrOnnnOOOOOOrK  ",
    "   KKrrrrrrrKK    ",
]


def check(name, rows):
    for i, r in enumerate(rows):
        assert len(r) == 18, (name, i, len(r), r)


for _n, _r in [('FRONT', FRONT), ('TQ_LEFT', TQ_LEFT), ('TQ_LEFT_OUCH', TQ_LEFT_OUCH)]:
    check(_n, _r)
