import json
import struct
from pathlib import Path

from ..core import backup, icons
from .base import Platform

RT_ICON = 3
RT_GROUP_ICON = 14


def _shortcut(path):
    # COM-объект ярлыка для чтения/записи .lnk
    import pythoncom
    from win32com.client import Dispatch

    pythoncom.CoInitialize()
    shell = Dispatch("WScript.Shell")
    return shell.CreateShortCut(str(path))


class WindowsPlatform(Platform):
    name = "windows"

    # ---------- бэкап ----------
    def _meta(self, app):
        p = backup.backup_dir(app.id) / "meta.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {}

    def _save_meta(self, app, meta):
        p = backup.backup_dir(app.id) / "meta.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(meta), encoding="utf-8")

    def backup(self, app):
        # мету ярлыка запоминаем, exe копируем целиком
        meta = self._meta(app)
        lnk = Path(app.desktop)
        meta.setdefault("lnk", str(lnk))
        if "lnk_icon" not in meta:
            sc = _shortcut(lnk)
            meta["lnk_icon"] = sc.IconLocation
        target = getattr(app, "exec", "") or ""
        if target.lower().endswith(".exe"):
            meta["exe"] = target
            kept = backup.backup_dir(app.id) / "original.exe"
            if not kept.exists():
                kept.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy2(target, kept)
        self._save_meta(app, meta)

    # ---------- применение ----------
    def apply(self, app, icon_dir):
        ico_dir = backup.ROOT / "icons" / app.id
        ico_dir.mkdir(parents=True, exist_ok=True)
        ico_file = ico_dir / "icon.ico"
        ico_file.write_bytes(icons.make_ico(Path(icon_dir) / "icon-256.png"))

        target = getattr(app, "exec", "") or ""
        if target.lower().endswith(".exe"):
            self._patch_exe(target, ico_file.read_bytes())

        lnk = Path(app.desktop)
        if lnk.suffix.lower() == ".lnk":
            self.backup(app)
            sc = _shortcut(lnk)
            sc.IconLocation = f"{ico_file},0"
            sc.Save()

    # ---------- откат ----------
    def restore(self, app):
        meta = self._meta(app)
        if not meta:
            return False
        kept = backup.backup_dir(app.id) / "original.exe"
        exe = meta.get("exe")
        if exe and kept.exists():
            import shutil

            shutil.copy2(kept, exe)
        lnk = meta.get("lnk")
        if lnk and Path(lnk).exists():
            try:
                sc = _shortcut(lnk)
                sc.IconLocation = meta.get("lnk_icon", "")
                sc.Save()
            except Exception:
                pass
        return True

    # ---------- врезание иконки в exe ----------
    @staticmethod
    def _parse_ico(data):
        # .ico: шапка 6 байт, записи по 16, за ними сами картинки
        _, _, cnt = struct.unpack_from("<HHH", data, 0)
        images = []
        for i in range(cnt):
            w, h, cc, _, planes, bits, size, off = struct.unpack_from("<4B2HII", data, 6 + i * 16)
            images.append((w, h, cc, planes, bits, data[off:off + size]))
        return images

    def _patch_exe(self, exe, ico_bytes):
        import win32api
        import win32con

        images = self._parse_ico(ico_bytes)

        # exe открываем как файл данных, чтобы посмотреть его иконки
        gid, old_ids, old_type = 1, [], 3
        lib = win32api.LoadLibraryEx(str(exe), 0, win32con.LOAD_LIBRARY_AS_DATAFILE)
        try:
            try:
                groups = list(win32api.EnumResourceNames(lib, RT_GROUP_ICON))
            except Exception:
                groups = []
            if groups:
                gid = groups[0]
                grp = win32api.LoadResource(lib, RT_GROUP_ICON, gid)
                _, old_type, cnt = struct.unpack_from("<HHH", grp, 0)
                for i in range(cnt):
                    entry = struct.unpack_from("<4BHHIH", grp, 6 + i * 14)
                    old_ids.append(entry[6])
        finally:
            win32api.FreeLibrary(lib)

        h = win32api.BeginUpdateResource(str(exe), 0)
        ok = False
        try:
            # пишем сами иконки: нашим хватит первых id, лишние старые удаляем
            for i, (w, hgt, cc, planes, bits, blob) in enumerate(images):
                if i < len(old_ids):
                    rid = old_ids[i]
                else:
                    rid = (max(old_ids) + 1 + i) if old_ids else i + 1
                    old_ids.append(rid)
                win32api.UpdateResource(h, RT_ICON, rid, blob)
            for rid in old_ids[len(images):]:
                win32api.UpdateResource(h, RT_ICON, rid)

            # и переписываем группу под новые картинки
            entries = b""
            for i, (w, hgt, cc, planes, bits, blob) in enumerate(images):
                entries += struct.pack("<4BHHIH", w % 256, hgt % 256, cc, 0, planes, bits, len(blob), old_ids[i])
            grp = struct.pack("<HHH", 0, old_type, len(images)) + entries
            win32api.UpdateResource(h, RT_GROUP_ICON, gid, grp)
            ok = True
        finally:
            win32api.EndUpdateResource(h, 0 if ok else 1)
