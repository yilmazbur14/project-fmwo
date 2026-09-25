"""matt_glass_glint.png: a twinkle on the glass bed. 4 frames of 7x7 at 0.06 s, one strip.
THE PIVOT IS THE CENTRE TEXEL (3, 3). The code scatters them over the landed glass. The glass ramp, opaque:
  f0  a spark: a white texel in a small #E6FBFF cross
  f1  a four-point star, white arms tipped #B8ECF5
  f2  the star at full size with #E6FBFF diagonals
  f3  fading back to a small cross
"""
FRAME_SIZE = (7, 7)
NOTE = '4 frames at 0.06 s; pivot = centre texel (3,3)'

FRAMES = [
    ['.......',
     '.......',
     '...E...',
     '..EWE..',
     '...E...',
     '.......',
     '.......'],
    ['.......',
     '...I...',
     '...W...',
     '.IWWWI.',
     '...W...',
     '...I...',
     '.......'],
    ['...I...',
     '...W...',
     '..EWE..',
     'IWWWWWI',
     '..EWE..',
     '...W...',
     '...I...'],
    ['.......',
     '.......',
     '...I...',
     '..IEI..',
     '...I...',
     '.......',
     '.......'],
]


def frames():
    return [list(f) for f in FRAMES]
