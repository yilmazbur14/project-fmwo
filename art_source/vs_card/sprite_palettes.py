"""Palettes sampled straight out of the shipped sheets - nothing invented.

Every hex below was counted in the character's own sprite (see the docstring on
each entry for the file). The rule for the busts is: if the sprite gives a
material three tones, the bust uses three. No new intermediate shades, because
adding them is exactly what made the first pass read as smooth portraits instead
of as the characters.

lock() at the bottom snaps a finished bust to its palette as a safety net.
"""

BK = "#000000"

# MainPlayer/player_4dir_sheet.png - the whole sprite is SEVEN colours, and
# there is no white in it at all, so Burak gets no sclera and no catchlights.
BURAK = dict(
    skin=["#D79864", "#AC714F"],
    blue=["#3883C9", "#2464BD", "#162FBB"],
    band=["#AC3232"],
    ink=[BK],
)

# Eric/eric_sheet_v2.png
ERIC = dict(
    plate=["#EAF0F6", "#CDD7E2", "#A3B1C2", "#7A86A0", "#525A74"],
    steel=["#A3A8AE", "#7C8187", "#5C6067", "#41444B", "#2B2D33"],
    hair=["#FFB45E", "#F58A38", "#DF6C22", "#B04C16", "#7A3010", "#4A1C08"],
    skin=["#FDE6CC", "#F3C9A2", "#DCA27A", "#B8795A", "#8A5040"],
    cape=["#8A1F38", "#5E142C", "#3C0C20"],
    cross=["#E2402F", "#B0242A"],
    gold=["#FFF0A8", "#F2C457", "#C48A2C", "#8A5A1C"],
    leather=["#9C6038", "#74432A", "#4E2C1C"],
    white=["#FFFFFF"], eye=["#4E2C1C"], ink=[BK],
    # every colour actually present in frame 0, so lock() never collapses one
    sheet=[
        "#7C8187", "#000000", "#CDD7E2", "#41444B", "#A3B1C2", "#5C6067",
        "#A3A8AE", "#2B2D33", "#7A86A0", "#5E142C", "#3C0C20", "#EAF0F6",
        "#B04C16", "#DF6C22", "#7A3010", "#D4D8DC", "#525A74", "#4A1C08",
        "#F58A38", "#F3C9A2", "#B0242A", "#331C12", "#FFFFFF", "#4E2C1C",
        "#DCA27A", "#8A1F38", "#9C6038", "#74432A", "#E2402F", "#FDE6CC",
        "#B8795A", "#FFB45E", "#C48A58", "#8A5040", "#F2C457", "#3A2418",
        "#C48A2C", "#8A5A1C", "#FFF0A8",
    ],
)

# Greyson/greyson_idle.png - thin dark moustache, NO beard; a gold band across
# the eyes with blue pupils, and a small red mark on the forehead.
GREYSON = dict(
    skin=["#FFF2E2", "#FFDCBE", "#F6CCA8", "#DCA57C", "#B07E58", "#835438"],
    hair=["#FFE6BC", "#FFC77E", "#F2A94E", "#CE8436", "#A16224", "#6E4116"],
    gold=["#F0CC5E"], eye=["#4A6E9E"], lip=["#CE7A60"],
    trunk=["#DEB8FA", "#C08CEE", "#A063DC", "#7E42B8", "#5A288A"],
    boot=["#F2F6FE", "#DCE2F0", "#BCC4DA", "#949CB8"],
    white=["#FFFFFF"], ink=[BK],
)

# Computah/computah_idle.png - note the greens and the eye red are its own.
COMPUTAH = dict(
    chassis=["#F2F8FF", "#D8E4F2", "#CEDCEA", "#A6B8CC", "#8091A8", "#6C7A8E", "#5E6C82", "#3F4A5C"],
    purple=["#C892F2", "#A063DC", "#7C3BB4", "#592687", "#391555"],
    green=["#A9FFB4", "#4FE066", "#1F9A38", "#2A7A3C"],
    eye=["#FF4436", "#93302C"],
    dark=["#222A38", "#0D1118", "#0C111A"], ink=[BK],
)

# Mason/mason.png - fifteen colours total.
MASON = dict(
    suit=["#FADCB8", "#EEC39A", "#D6AA7C", "#AE8358", "#90765E", "#7D5631"],
    yellow=["#FBF236", "#D4CC2E", "#A09050", "#726E17", "#605020"],
    red=["#D95763", "#AC3232"],
    white=["#FFFFFF"], ink=[BK],
)

# Josh/josh_idle.png
JOSH = dict(
    coat=["#F4EAD6", "#E8E2CE", "#C6BFA4", "#918B72", "#5E5A48", "#39362B"],
    hat=["#7E7E90", "#50505E", "#45487F", "#32335C", "#32323E", "#20203C", "#1C1C24", "#0D0D13"],
    band=["#C96C74", "#A63B4B", "#7A2032", "#5E1A24", "#4D1420", "#2B0A12"],
    gold=["#FFF3B0", "#F5D94E", "#E0AB35", "#B07D22", "#7A5216"],
    hair=["#5F3C29", "#3D261A", "#3A2014", "#24160F", "#130B09"],
    skin=["#FFF0DC", "#FBD6B0", "#F0B98E", "#DB976C", "#B86C4E", "#84412F"],
    ink=[BK],
)

# Danny/Sumo/danny_sumo_idle.png - four skin tones; the beanie stripes run
# VERTICALLY; the face is two black bars and an open mouth, not a moustache.
DANNY = dict(
    skin=["#EEC39A", "#D9A066", "#8F563B", "#663931"],
    beanie=["#CBDBFC", "#639BFF", "#5B6EE1", "#3F3F74"],
    grey=["#9BADB7", "#847E87", "#696A6A"],
    gold=["#FBF236", "#DF7126"],
    red=["#D95763", "#AC3232"],
    dark=["#45283C", "#222034"],
    white=["#FFFFFF"], ink=[BK],
)

# Carter/carter_akuma.png - bald tan crown with a dark purple spiked mane;
# eyes are red slits set in orange-tan sockets.
CARTER = dict(
    skin=["#FBD6B0", "#F0B98E", "#DB976C", "#C08A58", "#B86C4E", "#84412F", "#552619", "#4A2210"],
    mane=["#4E1878", "#2E0C4C", "#23184E", "#19062A"],
    maneRed=["#C01830", "#780C28"],
    gi=["#4A6ED8", "#2D4392", "#1D2B60", "#1B1C4C", "#14204A", "#0C1430"],
    wrap=["#F0D8A4", "#D0AE74", "#C8A46A", "#A07E4C", "#74562E", "#50381C", "#32210F"],
    fire=["#FFB45E", "#F09040", "#D66C28", "#B05B21", "#703414"],
    eye=["#FFD2D8", "#E0203C"],
    ink=[BK],
)

# Liam/liam.png - grey-framed glasses with pale lenses, full dark beard, grin.
LIAM = dict(
    coat=["#C3885A", "#B8794A", "#A96B43", "#8F563B", "#6A4A3A", "#663931", "#56352A", "#45302A", "#36201A"],
    hair=["#2A1B16", "#1B0F0D", "#120A08"],
    skin=["#FADCB8", "#EEC39A", "#D9A066"],
    glass=["#EEF4F7", "#D6DEE5", "#C4D2DA", "#B3C0C9", "#A3B1BC", "#9BADB7", "#7B8893", "#6E7D86", "#4A5563"],
    tie=["#6B6BB0", "#4C4C8C", "#3A3A70", "#26264C", "#181830"],
    plum=["#45283C"], white=["#FFFFFF"], ink=[BK],
)

# Bixby/bixby_beast.png
BIXBY = dict(
    fur=["#948779", "#7E7A8C", "#6B6157", "#6E6E78", "#5C5868", "#5E6674", "#3A3542", "#26222C", "#121016"],
    bone=["#EDE4D6", "#C7BBAB"],
    helm=["#9C5428", "#6B3419", "#6A3C22", "#4A2818", "#2C1810"],
    wing=["#B84A60", "#8A1F38", "#6E1E22", "#5E142C", "#5A1A22", "#3C0C20"],
    fire=["#FFF7A0", "#FBF236", "#F58A38", "#E9A55F", "#DF7126", "#C97A3C", "#E0524A"],
    red=["#AC3232"],
    steel=["#B3C0C9", "#9BADB7", "#7B8893", "#6E7D86", "#4A5563"],
    white=["#FFFFFF"], ink=[BK],
)

# Jordan/jordan.png - white cap crown with a green patch and a RED brim.
JORDAN = dict(
    skin=["#FADCB8", "#EEC39A", "#D6AA7C", "#AE8358", "#90765E", "#8F563B", "#663931"],
    pink=["#F2C0DF", "#E49ACD", "#D77BBA", "#B05E97", "#8A4574", "#5E2F52"],
    cap=["#FFFFFF", "#E8E6E0", "#CBC8C0", "#9B968C", "#5C5850"],
    green=["#4B692F"],
    red=["#AC3232", "#7A2626"],
    gold=["#FBF236", "#DF7126"],
    navy=["#6B70A8", "#53548C", "#3F3F74", "#2B2A52", "#272546"],
    grey=["#9BADB7"], ink=[BK],
)

ALL = dict(burak=BURAK, eric=ERIC, greyson=GREYSON, computah=COMPUTAH, mason=MASON,
           josh=JOSH, danny=DANNY, carter=CARTER, liam=LIAM, bixby=BIXBY, jordan=JORDAN)


def flat(*pals):
    """Every hex from one or more palette dicts, as a flat list."""
    out = []
    for p in pals:
        for v in p.values():
            out.extend(v)
    return sorted(set(out))


def lock(im, allowed):
    """Snap every opaque pixel to the nearest allowed colour. Safety net that
    catches any tone that crept in from a blend or a stray constant."""
    cols = [(int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)) for c in allowed]
    cache = {}
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            k = (r, g, b)
            v = cache.get(k)
            if v is None:
                v = min(cols, key=lambda c: (c[0] - r) ** 2 * 3 + (c[1] - g) ** 2 * 6 + (c[2] - b) ** 2)
                cache[k] = v
            px[x, y] = (v[0], v[1], v[2], 255)
    return im
