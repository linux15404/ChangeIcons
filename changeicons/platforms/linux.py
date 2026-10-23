from pathlib import Path

from ..core import backup
from .base import Platform

USER_APPS = Path.home() / ".local/share/applications"


class LinuxPlatform(Platform):
    name = "linux"

    def backup(self, app):
        # сохраняем исходный .desktop только если это наш пользовательский файл,
        # системные не трогаем вообще — переопределяем копией
        if app.writable:
            saved = backup.saved_name(app.id, app.id)
            if not saved.exists():
                backup.save_file(app.id, app.desktop)

    def apply(self, app, icon_dir):
        icon = Path(icon_dir) / "icon-256.png"
        self.backup(app)

        target = USER_APPS / app.id
        text = app.desktop.read_text(encoding="utf-8", errors="ignore")

        # меняем только строку Icon=, остальное оставляем как было
        lines = text.splitlines()
        replaced = False
        for i, line in enumerate(lines):
            if line.lower().startswith("icon="):
                lines[i] = f"Icon={icon}"
                replaced = True
                break
        if not replaced and lines and lines[0].strip() == "[Desktop Entry]":
            lines.insert(1, f"Icon={icon}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target

    def restore(self, app):
        target = USER_APPS / app.id
        if backup.restore_file(app.id, app.id, target):
            return True
        # наш копии исходника нет — значит был системный файл, просто убираем оверрайд
        if target.exists():
            target.unlink()
            return True
        return False
