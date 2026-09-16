from canvas import Canvas
# variant A: front face of the fist = four stacked curled fingers, thumb tucked on top
A = [
"......KKKKKK..........",
"....KKssssssKK........",
"...KsssssssssdKK......",
"..KssssssKKKKKddK.....",
"..KsssssKssssssKdK....",
".KsssssKssssssssKK....",
".KsssssKsssssssssdK...",
".KsssssKKsssssssddK...",
".KssssssdKKKKKKKKK....",
".KsssssKsssssssssdK...",
".KsssssKssssssssddK...",
".KssssssKKKKKKKKKK....",
".KsssssKssssssssddK...",
".KsssssKsssssssdddK...",
".KssssssKKKKKKKKKK....",
".KsssssKsssssssddK....",
"..KssssKssssssdddK....",
"..KssssdKKKKKKKKK.....",
"...KssssddddddK.......",
"...KsssssdddddK.......",
"....KssssddddK........",
]
# variant B: rounded mitten fist, knuckle bumps along the top edge, 3 short finger creases
B = [
"........KKK.KKK.......",
"......KKsssKsssKK.....",
".....KsssssKssssdKK...",
"....KssssssKsssssddK..",
"...KsssssssKssssdddK..",
"...KssssssssKssdddK...",
"..KssssssssssKKKKdK...",
"..KsssssssssssssKKK...",
"..KssssssssssssKsdK...",
"..KsssssssssKKKssdK...",
"..KssssssssKsssdddK...",
"..KsssssssssKKKKddK...",
"..KsssssssssssssdK....",
"..KssssssssssKKKdK....",
"...KsssssssssKdddK....",
"...KssssssssssKKdK....",
"...KsssssssssssddK....",
"....KssssssssdddK.....",
"....KsssssssddddK.....",
".....KssssssdddK......",
]
# variant C: fist seen from the knuckle side, fingers wrapping toward the cheek (right)
C = [
".......KKKKKKK........",
".....KKsssssssKK......",
"....KsssssssssssK.....",
"...KsssssssssssddK....",
"...KssssssKKKKKdddK...",
"..KssssssKsssssKddK...",
"..KssssssKssssssKdK...",
"..KsssssssKKKsssKKK...",
"..KssssssKssssKKsdK...",
"..KssssssKsssssssdK...",
"..KsssssssKKKKssddK...",
"..KssssssKssssKKddK...",
"..KssssssKssssssddK...",
"..KsssssssKKKKKdddK...",
"..KsssssssssssKddK....",
"...KssssssssssKKK.....",
"...KssssssssssddK.....",
"....KsssssssssddK.....",
"....KssssssssdddK.....",
".....KssssssdddK......",
]
cv = Canvas(3 * 34 + 4, 32, 's')
for i, g in enumerate([A, B, C]):
    for j, line in enumerate(g):
        for k, ch in enumerate(line):
            if ch != '.':
                cv.set(4 + i * 34 + k, 4 + j, ch)
cv.save('fist_variants_8x.png', 8)
