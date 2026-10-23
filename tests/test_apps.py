from changeicons.core import apps


def _make(tmp_path, name="Test", icon="star", hidden=False, nodisplay=False):
    lines = ["[Desktop Entry]", f"Name={name}", "Type=Application", "Exec=true"]
    if icon is not None:
        lines.append(f"Icon={icon}")
    if hidden:
        lines.append("Hidden=true")
    if nodisplay:
        lines.append("NoDisplay=true")
    f = tmp_path / "test.desktop"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f


def test_read_norm(tmp_path):
    assert apps._read(_make(tmp_path)) == {"name": "Test", "icon": "star", "exec": "true"}


def test_read_skips_hidden(tmp_path):
    assert apps._read(_make(tmp_path, hidden=True)) is None
    assert apps._read(_make(tmp_path, nodisplay=True)) is None


def test_read_missing_icon(tmp_path):
    assert apps._read(_make(tmp_path, icon=None))["icon"] == ""


def test_read_duplicated_section(tmp_path):
    # повторы секций в реальных файлах встречаются — парсер не должен упасть
    f = tmp_path / "d.desktop"
    f.write_text(_make(tmp_path).read_text() + "[Desktop Entry]\nName=Other\n", encoding="utf-8")
    assert apps._read(f)["name"] == "Other"
