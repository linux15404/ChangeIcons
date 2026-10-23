from PIL import Image, ImageOps

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
