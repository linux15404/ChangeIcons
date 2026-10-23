from PIL import Image

from changeicons.core import backup
from changeicons.core.apps import App
from changeicons.platforms import linux


def make_app(folder, writable=True):
    f = folder / "test.desktop"
    f.write_text("[Desktop Entry]\nName=Test\nExec=true\nIcon=orig\nType=Application\n", encoding="utf-8")
    return App(f.name, "Test", "orig", f, writable), f


def make_icon_dir(tmp_path):
    d = tmp_path / "icons-out"
    d.mkdir()
    Image.new("RGBA", (256, 256), "blue").save(d / "icon-256.png")
    return d


def test_override_cycle(tmp_path, monkeypatch):
    # системный файл: оверрайд создаётся, restore удаляет, оригинал не менялся
    system = tmp_path / "system"
    system.mkdir()
    user = tmp_path / "user"
    user.mkdir()
    monkeypatch.setattr(linux, "USER_APPS", user)
    monkeypatch.setattr(backup, "ROOT", tmp_path / "root")

    app, f = make_app(system, writable=False)
    p = linux.LinuxPlatform()
    p.apply(app, make_icon_dir(tmp_path))

    override = user / "test.desktop"
    assert override.exists()
    assert any(line.startswith("Icon=") for line in override.read_text().splitlines())
    assert "Icon=orig" in f.read_text()  # системный файл нетронут

    assert p.restore(app) is True
    assert not override.exists()


def test_user_file_cycle(tmp_path, monkeypatch):
    # пользовательский файл правится напрямую и возвращается бэкапом
    user = tmp_path / "user"
    user.mkdir()
    monkeypatch.setattr(linux, "USER_APPS", user)
    monkeypatch.setattr(backup, "ROOT", tmp_path / "root")

    app, f = make_app(user, writable=True)
    p = linux.LinuxPlatform()
    p.apply(app, make_icon_dir(tmp_path))

    assert "Icon=" in f.read_text() and "orig" not in f.read_text()
    assert (tmp_path / "root/backup/test.desktop/test.desktop").exists()

    assert p.restore(app) is True
    assert "Icon=orig" in f.read_text()
