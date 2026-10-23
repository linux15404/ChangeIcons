from changeicons.core.icons import make_icons

if __name__ == "__main__":
    # временно: пока нет окна, проверяем ядро через консоль
    import sys

    if len(sys.argv) < 2:
        print("использование: python -m changeicons <картинка>")
        sys.exit(1)
    for p in make_icons(sys.argv[1], "."):
        print(p)
