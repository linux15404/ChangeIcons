import struct
from pathlib import Path

from changeicons.core.icons import make_icons, make_ico
from changeicons.platforms.windows import WindowsPlatform


def test_sizes_and_files(tmp_path):
    src = tmp_path / "in.png"
    from PIL import Image

    Image.new("RGBA", (300, 200), (0, 0, 0, 255)).save(src)
    paths = make_icons(str(src), str(tmp_path))
    assert [Path(p).name for p in paths] == [f"icon-{s}.png" for s in (256, 128, 64, 48, 32, 16)]
    for p in paths:
        assert Image.open(p).size == (Image.open(p).size[0],) * 2


def test_center_crop(tmp_path):
    # картинка 300x200 не должна растягиваться — обрезается по центру
    from PIL import Image

    src = tmp_path / "in.png"
    Image.new("RGB", (300, 200), "red").save(src)
    paths = make_icons(str(src), str(tmp_path))
    assert Image.open(paths[0]).size == (256, 256)


def test_parse_ico(tmp_path):
    from PIL import Image

    png = tmp_path / "in.png"
    Image.new("RGBA", (256, 256), "blue").save(png)
    data = make_ico(png)
    images = WindowsPlatform._parse_ico(data)
    sizes = [i[0] for i in images]
    _, _, cnt = struct.unpack_from("<HHH", data, 0)
    assert cnt == len(images) and 16 in sizes
