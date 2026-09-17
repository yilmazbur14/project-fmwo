from pngio import read_png, write_png, upscale
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/"
names = ['ui_dialogue_frame','ui_card_frame','ui_portrait_frame','ui_button','ui_button_hover','ui_button_pressed']
tiles=[]; x=8
for n in names:
    w,h,p = read_png(P+n+'.png')
    W,H,o = upscale(w,h,p,12,bg='checker')
    tiles.append((x,o,W,H)); x+=W+8
out=[[(60,60,60,255)]*x for _ in range(32*12+16)]
for tx,o,W,H in tiles:
    for yy in range(H):
        for xx in range(W):
            out[8+yy][tx+xx]=o[yy][xx]
write_png('ref/kit_12x.png', x, 32*12+16, out)
