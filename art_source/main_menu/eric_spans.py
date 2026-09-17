W,H=38,42
g=[['.']*W for _ in range(H)]
def S(y,x0,x1,ch='#'):
    for x in range(x0,x1+1):
        if 0<=x<W and 0<=y<H: g[y][x]=ch
# colossal greatsword planted point-down beside him
S(0,4,6); S(1,3,7); S(2,3,7); S(3,4,6)          # pommel
for y in range(4,9): S(y,4,6)                     # grip
S(9,0,10); S(10,0,10)                             # crossguard
S(11,2,8)
for y in range(12,41): S(y,2,8)                   # blade
S(41,1,9)                                         # bite into the floor
for y in range(12,40): g[y][5]='+'                # fuller line
D=2  # body offset
# head: hair + beard
for y,a,b in [(10,19,23),(11,17,25),(12,16,26),(13,16,26),(14,16,26),(15,15,27),(16,15,27),(17,15,27),(18,16,26),
              (19,16,26),(20,16,26),(21,16,26),(22,16,26),(23,16,26),(24,16,26),(25,17,25),(26,17,25),(27,18,24),(28,19,23)]:
    S(y,a+D,b+D)
for y,a,b in [(19,10,13),(20,9,14),(21,9,14),(22,9,14),(23,9,14),(24,9,15),(25,9,15)]: S(y,a+D,b+D)
for y,a,b in [(19,29,32),(20,28,33),(21,28,34),(22,28,34),(23,28,34),(24,27,34),(25,27,34)]: S(y,a+D,b+D)
for y in range(24,34): S(y,12+D,31+D)
# arms, fists at hips
for y in range(26,31): S(y,9+D,13+D); S(y,29+D,34+D)
for y in range(30,36): S(y,8+D,12+D); S(y,30+D,35+D)
for y,a,b in [(33,11,32),(34,11,33),(35,10,34),(36,10,34),(37,9,35),(38,9,35),(39,9,35),(40,9,35)]: S(y,a+D,b+D)
for a,b in [(9,11),(13,17),(19,21),(23,27),(29,31),(33,35)]: S(41,a+D,b+D)
for y,x in [(25,16),(26,16),(27,17),(28,18),(29,19),(25,26),(26,26),(27,25),(28,24),(29,23),(30,20),(30,21),(30,22)]:
    g[y][x+D]='+'
for y in range(27,31): g[y][14+D]='+'; g[y][28+D]='+'
for y in range(36,41): g[y][22+D]='+'
print('[eric]'); print('\n'.join(''.join(r) for r in g))
