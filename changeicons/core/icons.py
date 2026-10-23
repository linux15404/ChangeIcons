from PIL import Image, ImageOps
import io

SIZES = (256, 128, 64, 48, 32, 16)


def make_icons(src, out_dir):
    # режем по центру до квадрата, потом ужмем до каждого размера
    img = Image.open(src).convert("RGBA")
    img = ImageOps.fit(img, (max(SIZES), max(SIZES)))

    paths = []
    for size in SIZES:
        small = img.resize((size, size), Image.LANCZOS)
        path = f"{out_dir}/icon-{size}.png"
        small.save(path)
        paths.append(path)
    return paths


def make_ico(src):
    # .ico для Windows собираем в памяти: внутрь кладём все размеры сразу
    img = ImageOps.fit(Image.open(src).convert("RGBA"), (256, 256))
    buf = io.BytesIO()
    img.save(buf, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
    return buf.getvalue()
