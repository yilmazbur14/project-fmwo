from pngio import *
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Danny/portrait.png"
w, h, rows = read_png(P)
M = {'#000000':'K','#ac3232':'r','#eec39a':'s','#d95763':'p','#ffffff':'W','#9badb7':'g','#d9a066':'d','#fbf236':'y'}
print('    ' + ''.join(str(x//10) for x in range(64)))
print('    ' + ''.join(str(x%10) for x in range(64)))
for y, row in enumerate(rows):
    print('%3d ' % y + ''.join('.' if px[3]==0 else M.get(hexc(px),'?') for px in row))
