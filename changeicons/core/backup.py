import shutil
from pathlib import Path

ROOT = Path.home() / ".local/share/changeicons"


def backup_dir(app_id):
    return ROOT / "backup" / app_id


def save_file(app_id, path):
    # копия оригинала, чтобы всегда можно было вернуть
    dst = backup_dir(app_id) / Path(path).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def saved_name(app_id, name):
    return backup_dir(app_id) / name


def restore_file(app_id, name, dest):
    src = saved_name(app_id, name)
    if not src.exists():
        return False
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True
