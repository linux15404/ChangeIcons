class Platform:
    # что умеет каждая ОС — общий набор, реализуется в linux.py / windows.py
    name = "base"

    def backup(self, app):
        raise NotImplementedError

    def apply(self, app, icon_dir):
        # icon_dir — папка с нашими icon-256.png ... icon-16.png
        raise NotImplementedError

    def restore(self, app):
        raise NotImplementedError


def get_platform():
    import sys

    if sys.platform == "win32":
        from .windows import WindowsPlatform
        return WindowsPlatform()
    from .linux import LinuxPlatform
    return LinuxPlatform()
