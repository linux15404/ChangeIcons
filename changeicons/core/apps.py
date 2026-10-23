import configparser
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class App:
    id: str          # имя .desktop-файла (linux) или путь к ярлыку (windows)
    name: str        # человеческое название
    icon: str        # что написано в Icon=
    desktop: Path    # где лежит файл сейчас
    writable: bool   # наш собственный файл (можно править напрямую) или системный
    exec: str = ""   # команда запуска; на windows тут путь к exe


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
    if sys.platform == "win32":
        return _list_windows()
    return _list_linux()


def _list_windows():
    # хотим ярлыки из «Пуска» — у большинства программ они есть
    import os

    appdata = os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming"))
    progdata = os.environ.get("PROGRAMDATA", str(Path.home() / ".."))
    bases = [
        Path(appdata) / "Microsoft/Windows/Start Menu/Programs",
        Path(progdata) / "Microsoft/Windows/Start Menu/Programs",
    ]
    try:
        import pythoncom
        from win32com.client import Dispatch
    except ImportError:
        return []

    pythoncom.CoInitialize()
    shell = Dispatch("WScript.Shell")
    apps = {}
    for d in bases:
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.lnk")):
            # id из относительного пути — folders с одинаковыми именами не конфликтуют
            rid = "__".join(f.relative_to(d).parts).replace(" ", "_")
            if rid in apps:
                continue
            try:
                sc = shell.CreateShortCut(str(f))
                target = sc.Targetpath
                icon = sc.IconLocation
            except Exception:
                target, icon = "", ""
            apps[rid] = App(rid, f.stem, icon, f, True, target)
    return sorted(apps.values(), key=lambda a: a.name.lower())


def _list_linux():
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
