import sys
from PIL import Image
p = sys.argv[1]; out = sys.argv[2]
tags = ['walk', 'hoh', 'behind']; views = ['front', 'side', 'back']
d = r'D:/TheLivingCanvas/ArtSource/NPC/_tmp_%s_%s_%s.png'
ims = [[Image.open(d % (p, t, v)) for v in views] for t in tags]
w, h = ims[0][0].size
sheet = Image.new('RGB', (w * 3, h * 3))
for r, row in enumerate(ims):
    for c, im in enumerate(row): sheet.paste(im, (c * w, r * h))
sheet = sheet.resize((w * 3 * 2 // 3, h * 3 * 2 // 3)); sheet.save(out)
