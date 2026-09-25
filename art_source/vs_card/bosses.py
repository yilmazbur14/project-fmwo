"""Per-boss card data. One row per fight; the card generator reads nothing else.

fight    the number shown top-left (playable order - Eric first, because the
         BURAK row in Scripts/GameProgress.gd has no scene and Burak is the
         player, and Matt has no design yet)
rank     the rank WINNING promotes the player to, straight out of GameProgress.gd
epithet  canon - all eight approved by the user 2026-09-20
ramp     5-step dark->light ramp for the boss's half of the band
accent   the two hairline rules along the diagonal split
mark     (emblem, colour, alpha) for the ghosted watermark behind the bust
name     lines for the baked name plate; two lines at 55 for the pair bosses,
         because GREYSON & COMPUTAH is 989px on one line at 99 and would run
         clean across both busts
fill_as_is  (optional, HUD only) use `ramp` as the boss bar's fill ramp verbatim
         instead of pushing it through hud_bars/boss_bar.bar_ramp()'s saturation
         boost - for a ramp that is already a fill, measured off the sprite
fill_trim   (optional, HUD only) a colour for the fill's lit top line, on the
         fill and the hot fill alike - a costume's edging, run along the bar
"""

BOSSES = [
    dict(key="eric", name=["ERIC"], name_size=99, epithet="THE WHITE KNIGHT",
         fight=1, rank="@regular", portrait="Eric/portrait.png",
         ramp=["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"],
         accent=("#C48A2C", "#F2C457"), mark=("cross", "#B0242A", 52)),

    dict(key="mason", name=["MASON"], name_size=99, epithet="THE SHITPOSTER",
         fight=3, rank="@trusted", portrait="Mason/mason.png",
         ramp=["#3A2408", "#6B4410", "#9E6A1C", "#D19A2E", "#F5C84E"],
         accent=("#AC3232", "#D95763"), mark=("star", "#FFFFFF", 44)),

    dict(key="josh", name=["JOSH"], name_size=99, epithet="THE CARD SHARK",
         fight=4, rank="@vip", portrait="Josh/josh_redesign.png",
         ramp=["#10182E", "#1C2A4E", "#2E4478", "#4766A8", "#7091D4"],
         accent=("#C48A2C", "#F2C457"), mark=("spade", "#9FBCEC", 46)),

    dict(key="danny", name=["DANNY"], name_size=99, epithet="THE SLEEPING GIANT",
         fight=5, rank="@helper", portrait="Danny/portrait.png",
         ramp=["#2E0F14", "#521A20", "#7E2A2E", "#AC3F3F", "#D9716A"],
         accent=("#C48A2C", "#F2C457"), mark=("moon", "#CBDBFC", 46)),

    dict(key="carter", name=["CARTER"], name_size=99, epithet="THE DEMON",
         fight=6, rank="@moderator", portrait="Carter/carter_akuma_pose.png",
         ramp=["#140A1C", "#2A1030", "#4A1A46", "#78265E", "#B03A70"],
         accent=("#8A1F38", "#E2402F"), mark=("demon", "#E2402F", 52)),

    dict(key="liam", name=["LIAM", "& BIXBY"], name_size=55,
         epithet="THE THRONE AND THE BEAST",
         fight=7, rank="@admin", portrait="Liam/portrait.png",
         ramp=["#161016", "#2E1A1C", "#54291F", "#8A4A24", "#C87038"],
         accent=("#9A8F80", "#EDE4D6"), mark=("crown", "#F2C457", 50)),

    dict(key="jordan", name=["JORDAN"], name_size=99, epithet="THE ADMIN",
         fight=8, rank="", portrait="Jordan/portrait.png",
         ramp=["#12142A", "#1E2248", "#2E3680", "#5B6EE1", "#93A4F7"],
         accent=("#5FCDE4", "#CBDBFC"), mark=("shield", "#FFFFFF", 44)),

    # --- bar-only rows -------------------------------------------------------
    # These two never get a VS card of their own: Computah shares Greyson's card
    # and Bixby is a mid-fight identity swap on Liam's. They exist here so the
    # HUD can key a fill ramp, an accent and an emblem off the same roster.
    dict(key="computah", name=["COMPUTAH"], name_size=55, epithet="", fight=2,
         rank="", portrait="Computah/computah.png", bar_only=True,
         ramp=["#0E2036", "#14406E", "#2A6FB0", "#59B8F2", "#A6DFFF"],
         accent=("#1F9A38", "#4FE066"), mark=("bolt", "#4FE066", 56)),

    # Greyson, the takeover in Computah's fight (FIGHT 03): when Computah falls, the bar switches to
    # him, full.  APPROVED by the user 2026-09-24.  This replaces the old pair row (GREYSON /
    # & COMPUTAH, purple + a green dumbbell), which went with the pair fight on 09-22; that row's
    # two-line plate bakes (boss_plate_name_greyson_a / _b / _pair) are left in Assets/UI.
    #   ramp       Computah's armour paint (art_source/computah_redesign/computah_mm.py "armour"),
    #              dark -> light; his trunks are drawn in its four darker steps
    #   fill_as_is his trunks as drawn, #7C3BB4: a violet, where Computah's bar is azure
    #   accent     his forehead vein (greyson_redesign.png): hot heats purple -> raspberry #A5478F.
    #              His blonde would grey it (#B37E92), as the old green accent did (#787182)
    #   mark       the double biceps (emblems.GRIDS) in his base skin tone.  Alpha 0: HUD only
    dict(key="greyson", name=["GREYSON"], name_size=55, epithet="", fight=3, rank="",
         portrait="Greyson/portrait.png", bar_only=True,
         ramp=["#391555", "#592687", "#7C3BB4", "#A063DC", "#C892F2"], fill_as_is=True,
         accent=("#9E3A48", "#D95763"), mark=("double_biceps", "#F0B98E", 0)),

    dict(key="bixby", name=["BIXBY"], name_size=55, epithet="", fight=7,
         rank="", portrait="Bixby/bixby.png", bar_only=True,
         ramp=["#1A0A0C", "#3E1214", "#71201E", "#B03A24", "#E8622E"],
         accent=("#AC3232", "#F58A38"), mark=("flame", "#F58A38", 52)),

    # Matt has a VS card, but it is vs_card_v2's (bands.py), so he is bar-only HERE:
    # that keeps card_roster() - and so the v1 card generator - from ever building a
    # Matt card over the shipped one.  fight and rank are his VsCardArtLayout.gd entry.
    #   ramp    his sweatshirt, measured off matt.png (art_source/matt/pal.py F..B),
    #           the same five steps as his VsCardArtLayout.gd ramp
    #   fill_as_is  bar_ramp()'s boost turns this lavender into #2B2FCE, Jordan's
    #           royal blue (#172BE2); as-is it stays his shirt
    #   accent  his roar's red eyes (pal.py Q, P): the bar heats lavender -> raspberry
    #           when he snaps.  His yellow would grey it - lavender and butter yellow
    #           are complements, and the mix lands on the chip trail's own grey
    #   mark    the speaker glyph (emblems.GRIDS) in his butter yellow (pal.py b):
    #           hair tips, collar and port rims.  Alpha 0 because his card, like
    #           bands.py's, ghosts no watermark - the rings behind his pose are his mark
    dict(key="matt", name=["MATT"], name_size=99, epithet="THE WALL OF SOUND", fight=3,
         rank="@veteran", portrait="Matt/portrait.png", bar_only=True,
         ramp=["#332F68", "#4F4D96", "#6D6FBC", "#8E91DA", "#B3B6F2"], fill_as_is=True,
         accent=("#CF1E38", "#FF4A58"), mark=("speaker", "#F8DB66", 0)),

    # Captain Burak, boss 1 - bar-only here for Matt's reason: his VS card is vs_card_v2's.
    # fight, name and rank are his GameProgress.gd row ("BURAK", @member, first in the ladder).
    #   ramp       his greatcoat ramp from his rig (art_source/burak_boss/kit.py v..U); the four
    #              darker steps are the coat as drawn in burak_boss.png, the palest is unused there
    #   fill_as_is bar_ramp()'s boost turns this crimson into #F30624, Bixby's #F30B06
    #   fill_trim  the coat's gold edging (kit.py O) as the fill's top line.  Without it the
    #              deep crimson is still one more red beside Eric (#CA2F36), who fights next
    #   accent     his gold (kit.py G, O): the hot fill heats crimson -> copper.  Gold sits
    #              ~50 degrees from his crimson, nowhere near opposite, so it cannot grey out
    #   mark       the Jolly Roger (emblems.GRIDS) in the same gold, so crimson and gold is
    #              the whole block.  Alpha 0: the HUD ignores it and he has no v1 card
    dict(key="burak", name=["BURAK"], name_size=99, epithet="", fight=1,
         rank="@member", portrait="BurakBoss/burak_boss.png", bar_only=True,
         ramp=["#4A0C1B", "#7E162B", "#B02436", "#D8434F", "#F07F7A"], fill_as_is=True,
         fill_trim="#F5D94E", accent=("#B07D22", "#F5D94E"), mark=("jolly_roger", "#F5D94E", 0)),
]


def card_roster():
    """Bosses that get a VS card - everything except the bar-only rows."""
    return [b for b in BOSSES if not b.get("bar_only")]


# Burak's half never changes between cards.
BURAK_RAMP = ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"]
BURAK_STRIPE = "#3A5BA8"


def by_key(k):
    for b in BOSSES:
        if b["key"] == k:
            return b
    raise KeyError(k)
