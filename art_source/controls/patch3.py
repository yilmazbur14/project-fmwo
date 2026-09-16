src = open('bg.py', encoding='utf-8').read()

rows = []
rows.append("..#################..")
rows.append(".#" + "W" * 16 + "g" + "#.")
body = [
    "WW" + "w" * 15 + "gg",
    "W" * 18 + "g",                        # bend over the seat edge
    "W" + "w" * 16 + "gg",
    "W" + "ggg" + "w" * 10 + "ggggg",      # shadow tucked under the bend
    "W" + "w" * 7 + "g" + "w" * 9 + "g",
    "W" + "w" * 7 + "g" + "w" * 9 + "g",
    "W" + "w" * 8 + "g" + "w" * 8 + "g",
    "W" + "w" * 8 + "g" + "w" * 8 + "g",
    "W" + "w" * 8 + "g" + "w" * 8 + "g",
    "W" + "w" * 8 + "g" + "w" * 8 + "g",
    "W" + "w" * 9 + "g" + "w" * 7 + "g",
    "p" + "r" * 17 + "R",
    "R" * 19,
    "W" + "w" * 9 + "g" + "w" * 7 + "g",
    "p" + "r" * 17 + "R",
    "R" * 19,
    "W" + "w" * 10 + "g" + "w" * 6 + "g",
    "W" + "w" * 10 + "g" + "w" * 6 + "g",
    "w" * 11 + "g" + "w" * 6 + "g",
    "g" + "w" * 10 + "g" + "w" * 6 + "g",
    "gggg" + "w" * 7 + "g" + "w" * 5 + "gg",
]
for b in body:
    assert len(b) == 19, (b, len(b))
    rows.append("#" + b + "#")
rows.append("." + "####" + "ggg" + "wwww" + "g" + "wwwww" + "gg" + "#")
rows.append("....." + "####" + "ggggg" + "www" + "ggg" + "#")
rows.append("........." + "######" + "gggg" + "#" + ".")
rows.append("..............." + "####" + "..")
for r in rows:
    assert len(r) == 21, (r, len(r))

a = src.index('TOWEL = [')
b = src.index(']\n', a) + 2
block = 'TOWEL = [\n' + ''.join('    "%s",\n' % r for r in rows) + ']\n'
src = src[:a] + block + src[b:]
open('bg.py', 'w', encoding='utf-8').write(src)
print('\n'.join(rows))
