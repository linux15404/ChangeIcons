<div align="center">

# 🎨 ChangeIcons

**Утилита для смены иконок приложений**

Подставь любую свою картинку вместо иконки программы: утилита сама подготовит нужные размеры, применит иконку и сохранит оригинал — всё всегда можно вернуть обратно.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Pillow](https://img.shields.io/badge/Pillow-10%2B-blue?logo=pillow&logoColor=white)](https://python-pillow.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

> 🎯 **Статус:** v1.1.0 — работающая программа. Тёмный GUI, RU/EN, Linux + Windows.

## Что умеет

- 🖼️ принимает любые картинки (PNG, JPG, WebP) и превращает их в иконку нужных размеров
- 🐧 **Linux** — замена иконок у `.desktop`-запускальщиков
- 🪟 **Windows** — замена иконки у `.exe` и ярлыков `.lnk`
- 💾 бэкап оригинальной иконки перед заменой — один клик и всё как было
- 🎛️ удобное GUI-окно: список приложений + подбор своей картинки

## Установка

Нужен Python 3.10+.

```bash
git clone https://github.com/linux15404/ChangeIcons.git
cd ChangeIcons
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Запуск

```bash
python -m changeicons
```

## Как устроено

```
changeicons/
├── __main__.py       — точка входа: python -m changeicons
├── core/             — логика без привязки к интерфейсу и ОС
│   ├── icons.py      — картинка → иконка нужных размеров (Pillow)
│   ├── apps.py       — поиск установленных приложений
│   └── backup.py     — бэкап и восстановление оригинальных иконок
├── platforms/        — различия между ОС
│   ├── base.py       — общий контракт для всех платформ
│   ├── linux.py      — .desktop-файлы и папки иконок
│   └── windows.py    — .exe / .lnk
├── gui/
│   ├── app.py        — главное окно (tkinter)
│   └── strings.py    — строки интерфейса (RU/EN)
```

Слои простые: **gui** просит **core** сделать работу, **core** делегирует конкретику **platforms**. Каждый слой можно тестировать отдельно.

На Linux иконка применяется через переопределение `.desktop`-файла в `~/.local/share/applications` — системные файлы не трогаются, откат всегда чистый. На Windows меняется иконка у ярлыка `.lnk` и встраивается внутрь `.exe` (для `.exe` автоматически ставится `pywin32`).

## Лицензия

MIT — см. [LICENSE](LICENSE).
