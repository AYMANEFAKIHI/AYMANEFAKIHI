# Synthetic assets so the pipeline can be validated before the real photo lands.
# A properly-framed head-and-shoulders bust with directional lighting + features,
# on a flat mid-tone wall (separable in colour for dark-mode segmentation, but
# not so dark that light-mode inks the whole background).
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1000, 1130
cx = W // 2

# ---- flat background wall (mid neutral, distinct hue from skin) --------------
bg = np.zeros((H, W, 3), np.float64)
bg[:] = (150, 156, 166)
img_arr = bg.copy()

# ---- directional light field (upper-left key light) -------------------------
yy, xx = np.mgrid[0:H, 0:W]
light = 1.0 - 0.6 * (np.hypot(xx - (cx - 140), yy - 300) / 700.0)
light = np.clip(light, 0.35, 1.15)

def paint_ellipse(arr, cx0, cy0, rx, ry, color):
    m = ((xx - cx0) / rx) ** 2 + ((yy - cy0) / ry) ** 2 <= 1.0
    for c in range(3):
        arr[..., c][m] = color[c]
    return m

skin = np.array([196, 170, 150], np.float64)
skin_shadow = np.array([120, 100, 92], np.float64)
hair = np.array([48, 40, 44], np.float64)

# shoulders (well below, filling lower third)
paint_ellipse(img_arr, cx, H + 120, 470, 470, (128, 120, 150))
# neck
paint_ellipse(img_arr, cx, 780, 95, 150, tuple(skin_shadow * 1.05))
# hair mass behind head
paint_ellipse(img_arr, cx, 470, 285, 330, hair)
# face
face_m = paint_ellipse(img_arr, cx, 500, 230, 300, skin)
# apply lighting to face region
for c in range(3):
    img_arr[..., c][face_m] = np.clip(img_arr[..., c][face_m] * light[face_m], 0, 255)

d = ImageDraw.Draw(Image.fromarray(img_arr.astype(np.uint8)))  # placeholder; use PIL below
im = Image.fromarray(img_arr.astype(np.uint8))
dr = ImageDraw.Draw(im)
# brows
dr.line([cx-150, 430, cx-60, 415], fill=(60, 50, 52), width=12)
dr.line([cx+60, 415, cx+150, 430], fill=(60, 50, 52), width=12)
# eyes
for sx in (-105, 105):
    dr.ellipse([cx+sx-45, 460, cx+sx+45, 505], fill=(238, 238, 240))
    dr.ellipse([cx+sx-18, 468, cx+sx+18, 500], fill=(60, 45, 40))
    dr.ellipse([cx+sx-7, 474, cx+sx+7, 490], fill=(20, 15, 15))
# nose (shadow to one side)
dr.polygon([(cx-8, 500), (cx-38, 590), (cx+30, 590)], fill=tuple((skin*0.82).astype(int)))
dr.ellipse([cx-34, 578, cx+34, 610], fill=tuple((skin*0.9).astype(int)))
# mouth
dr.chord([cx-70, 630, cx+70, 705], 10, 170, fill=(150, 90, 90))
dr.line([cx-70, 660, cx+70, 660], fill=(110, 70, 70), width=6)
# jaw/cheek shading
dr.arc([cx-235, 300, cx+235, 810], 25, 155, fill=tuple(skin_shadow.astype(int)), width=10)
# hair top highlight
dr.arc([cx-285, 150, cx+285, 780], 200, 340, fill=(72, 62, 66), width=22)

im = im.filter(ImageFilter.GaussianBlur(2.2))
im.save("assets/photo.jpg", quality=94)

# ---- three logo rasters (dark ink on white) ---------------------------------
def canvas(): return Image.new("L", (400, 400), 255)

l1 = canvas(); d = ImageDraw.Draw(l1)          # </> code glyph
d.line([150, 120, 90, 200, 150, 280], fill=0, width=26, joint="curve")
d.line([250, 120, 310, 200, 250, 280], fill=0, width=26, joint="curve")
d.line([215, 110, 185, 290], fill=0, width=22)
l1.save("assets/logos/logo1.png")

l2 = canvas(); d = ImageDraw.Draw(l2)          # triangle (Vercel-style)
d.polygon([(200, 90), (320, 300), (80, 300)], fill=0)
l2.save("assets/logos/logo2.png")

l3 = canvas(); d = ImageDraw.Draw(l3)          # bolt
d.polygon([(210, 80), (120, 220), (190, 220), (160, 320), (280, 170), (205, 170)], fill=0)
l3.save("assets/logos/logo3.png")

print("demo assets written: realistic bust + 3 logos")
