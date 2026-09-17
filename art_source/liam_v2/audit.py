import sys
from lib import *
def audit(cv, label=''):
    issues = []
    for y in range(64):
        for x in range(64):
            c = cv[y][x]
            if c == '.':
                continue
            # orphan: opaque pixel with no opaque 4-neighbour
            n4 = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
            opaque = [1 for X,Y in n4 if 0<=X<64 and 0<=Y<64 and cv[Y][X] != '.']
            if not opaque:
                issues.append(('orphan', x, y, c))
            # non-outline colour touching transparency orthogonally (outline gap)
            if c != '#':
                for X,Y in n4:
                    if not (0<=X<64 and 0<=Y<64) or cv[Y][X] == '.':
                        issues.append(('fill-touches-bg', x, y, c))
                        break
            # single isolated colour pixel surrounded by one other colour (noise), ignore outline
            if c != '#':
                n8 = [cv[Y][X] for X,Y in [(x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1)] if 0<=X<64 and 0<=Y<64]
                if len(n8) == 8 and all(k == n8[0] for k in n8) and n8[0] != c and n8[0] != '#':
                    issues.append(('speck', x, y, c + '/' + n8[0]))
    return issues
if __name__ == '__main__':
    cv = from_text(open(sys.argv[1]).read())
    iss = audit(cv)
    from collections import Counter
    print(Counter(i[0] for i in iss))
    for i in iss:
        print(i)
