import configparser
from dataclasses import dataclass
from pathlib import Path


@dataclass
class App:
    id: str          # имя .desktop-файла, например org.gimp.GIMP.desktop
    name: str        # человеческое название
    icon: str        # что написано в Icon=
    desktop: Path    # где лежит файл сейчас
    writable: bool   # наш собственный файл (можно править напрямую) или системный


# папки в порядке приоритета: пользовательская главнее
USER_APPS = Path.home() / ".local/share/applications"
FLATPAK_USER = Path.home() / ".local/share/flatpak/exports/share/applications"
FLATPAK_SYSTEM = Path("/var/lib/flatpak/exports/share/applications")
SNAP = Path("/var/lib/snapd/desktop/applications")


def _dirs():
    return [USER_APPS, FLATPAK_USER, FLATPAK_SYSTEM, SNAP,
            Path("/usr/local/share/applications"), Path("/usr/share/applications")]


def _read(path):
    # .desktop это почти ini, но бывает с дублями секций — strict=False
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    cfg.read_string(path.read_text(encoding="utf-8", errors="ignore"))
    if not cfg.has_section("Desktop Entry"):
        return None
    entry = cfg["Desktop Entry"]
    if entry.get("Type") != "Application" or entry.getboolean("Hidden", False):
        return None
    if entry.getboolean("NoDisplay", False):
        return None
    name = entry.get("Name") or path.stem
    return {"name": name, "icon": entry.get("Icon", ""), "exec": entry.get("Exec", "")}


def list_apps():
    apps = {}
    for d in _dirs():
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.desktop")):
            info = _read(f)
            if info is None:
                continue
            writable = f.parent == USER_APPS
            # первый найденный файл с таким id и есть главный, дубли пропускаем
            if f.name in apps and not writable:
                continue
            apps[f.name] = App(f.name, info["name"], info["icon"], f, writable)
    return sorted(apps.values(), key=lambda a: a.name.lower())
