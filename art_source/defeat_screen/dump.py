"""dump a png region as a char grid. python dump.py file.png [x y w h]"""
import sys
from lib import load
CH = {'000000': 'K', 'eec39a': 'h', 'd9a066': 't', '8f563b': 's', '663931': 'd', '45283c': 'p',
      'd95763': 'r', 'ac3232': 'R', '3883c9': 'l', '2464bd': 'b', '162fbb': 'B', '222034': 'n',
      '3f3f74': 'I', '595652': 'g', '847e87': 'G', 'ffffff': 'w', 'cbdbfc': 'i', '639bff': 'L',
      '5b6ee1': 'u', '9badb7': 'e', '8f974a': 'o', '4b692f': 'v', '323c39': 'c', 'fbf236': 'y',
      '8a6f30': 'a', '524b24': 'A', 'ac3232': 'R', '306082': 'q', '76428a': 'P', 'd77bba': 'k', 'df7126': 'O'}
a = sys.argv
im = load(a[1])
x0, y0, w, h = (map(int, a[2:6]) if len(a) > 2 else (0, 0, im.w, im.h))
print('    ' + ''.join(str((x0 + i) // 10 % 10) if (x0 + i) % 10 == 0 else ' ' for i in range(w)))
for y in range(y0, y0 + h):
    print('%3d ' % y + ''.join('.' if im.get(x, y) is None else CH.get(im.get(x, y), '?') for x in range(x0, x0 + w)))
