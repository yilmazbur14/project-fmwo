from lib import Canvas
st = Canvas.load('out/street_buildings.png')
b = st.crop(348, 34, 30, 78)
b.save('view/sign_ctx_6x.png', 6)
print('ok')
