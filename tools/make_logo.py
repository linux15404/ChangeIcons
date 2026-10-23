# перегенерация логотипа: python tools/make_logo.py
from PIL import Image, ImageDraw

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

BLACK = (10, 10, 10, 255)
WHITE = (245, 245, 245, 255)

# чёрный скруглённый фон
d.rounded_rectangle([64, 64, S - 64, S - 64], radius=200, fill=BLACK)

# картинка (рамка, солнце, горы)
d.rounded_rectangle([256, 292, 704, 616], radius=48, outline=WHITE, width=32)
d.ellipse([596, 348, 664, 416], fill=WHITE)
d.polygon([(288, 592), (424, 416), (532, 592)], fill=WHITE)
d.polygon([(452, 592), (556, 476), (648, 592)], fill=WHITE)

# белая плашка со стрелками обмена поверх угла рамки
d.rounded_rectangle([568, 588, 896, 816], radius=64, fill=WHITE)

# стрелка влево
d.polygon([(604, 684), (676, 656), (676, 712)], fill=BLACK)
d.rectangle([676, 672, 788, 696], fill=BLACK)
# стрелка вправо
d.rectangle([644, 708, 748, 732], fill=BLACK)
d.polygon([(808, 720), (748, 692), (748, 748)], fill=BLACK)

logo = img.resize((256, 256), Image.LANCZOS)
logo.save("changeicons/assets/logo.png")
print("ok")
