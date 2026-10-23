import tkinter as tk
from tkinter import filedialog, font as tkfont
from tkinter import ttk

from PIL import Image, ImageTk

from ..core import backup
from ..core import icons
from ..core.apps import list_apps
from ..platforms.base import get_platform
from .strings import LANGS

BG = "#16161e"
PANEL = "#1f2335"
PANEL2 = "#262b40"
ACCENT = "#7aa2f7"
TEXT = "#c0caf5"
MUTED = "#565f89"
GREEN = "#9ece6a"
RED = "#f7768e"

ICON_DIRS = [
    # где ищем текущую иконку приложения для превью
    "/usr/share/icons/hicolor/256x256/apps",
    "/usr/share/icons/hicolor/128x128/apps",
    "/usr/share/icons/hicolor/64x64/apps",
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/pixmaps",
]


def _find_icon(name):
    if not name:
        return None
    if name.startswith("/"):
        return name if name.endswith((".png", ".xpm", ".gif")) else None
    for d in ICON_DIRS:
        for ext in (".png", ".xpm"):
            p = f"{d}/{name}{ext}"
            try:
                with open(p, "rb"):
                    return p
            except OSError:
                pass
    return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChangeIcons")
        self.configure(bg=BG)
        self.geometry("820x540")
        self.minsize(720, 460)

        fams = tkfont.families()
        self.fam = next((f for f in ("Ubuntu", "Noto Sans", "Segoe UI", "DejaVu Sans") if f in fams), "TkDefaultFont")

        self.lang = "ru"
        self.t = LANGS[self.lang]
        self.platform = get_platform()
        self.all_apps = list_apps()
        self.selected = None
        self.image_path = None
        self._thumb = None    #PhotoImage надо держать в поле, иначе удалит сборщик мусора
        self._cur_thumb = None
        self._rows = []

        self._build()
        self._fill_list()

    # ---------- каркас окна ----------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        head = tk.Frame(self, bg=PANEL)
        head.grid(row=0, column=0, sticky="ew")
        tk.Frame(head, bg=ACCENT, height=2).pack(fill="x", side="bottom")

        inner = tk.Frame(head, bg=PANEL)
        inner.pack(fill="x", padx=20, pady=12)
        tk.Label(inner, text="ChangeIcons", bg=PANEL, fg=ACCENT,
                 font=(self.fam, 16, "bold")).pack(side="left")
        self.subtitle = tk.Label(inner, bg=PANEL, fg=MUTED, font=(self.fam, 10))
        self.subtitle.pack(side="left", padx=10)
        self.lang_btn = self._button(inner, "", self._switch_lang, PANEL2, MUTED, small=True,
                                     padx=10, pady=3)
        self.lang_btn.pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        # --- левая колонка: список приложений ---
        left = tk.Frame(body, bg=PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._fill_list())
        self.search = tk.Entry(left, textvariable=self.search_var, bg=PANEL2, fg=MUTED,
                               relief="flat", insertbackground=TEXT, highlightthickness=0,
                               font=(self.fam, 10))
        self.search.bind("<FocusIn>", self._placeholder_out)
        self.search.bind("<FocusOut>", self._placeholder_in)
        self.search.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4), ipady=5)

        listwrap = tk.Frame(left, bg=PANEL)
        listwrap.grid(row=1, column=0, sticky="nsew", padx=(4, 0))
        listwrap.rowconfigure(0, weight=1)
        listwrap.columnconfigure(0, weight=1)

        self.list = tk.Canvas(listwrap, bg=PANEL, highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(listwrap, orient="vertical", command=self.list.yview)
        self.list.configure(yscrollcommand=self.scroll.set)
        self.list.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.inner = tk.Frame(self.list, bg=PANEL)
        self._win = self.list.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.list.configure(scrollregion=self.list.bbox("all")))
        self.list.bind("<Configure>", lambda e: self.list.itemconfigure(self._win, width=e.width))
        self._wheel(self.list)

        self.count_label = tk.Label(left, bg=PANEL, fg=MUTED, font=(self.fam, 9))
        self.count_label.grid(row=2, column=0, sticky="w", padx=14, pady=(2, 8))

        # --- правая колонка: превью и действия ---
        right = tk.Frame(body, bg=PANEL)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        self.app_name = tk.Label(right, bg=PANEL, fg=TEXT, font=(self.fam, 13, "bold"),
                                 justify="center", wraplength=320)
        self.app_name.pack(pady=(24, 0))

        box_cur = tk.Frame(right, bg=PANEL2)
        box_cur.pack(pady=(8, 4), ipadx=10, ipady=10)
        self.cur_prev = tk.Label(box_cur, bg=PANEL2, width=12, fg=MUTED)
        self.cur_prev.pack()
        self.cur_title = tk.Label(right, bg=PANEL, fg=MUTED, font=(self.fam, 9))
        self.cur_title.pack()

        box_new = tk.Frame(right, bg=PANEL2)
        box_new.pack(pady=(12, 0), ipadx=10, ipady=10)
        self.new_prev = tk.Label(box_new, bg=PANEL2, width=12, fg=MUTED)
        self.new_prev.pack()
        self.new_title = tk.Label(right, bg=PANEL, fg=MUTED, font=(self.fam, 9))
        self.new_title.pack()

        self.pick_btn = self._button(right, "", self._pick_image, PANEL2, ACCENT, padx=14)
        self.pick_btn.pack(pady=(14, 4))
        self.apply_btn = self._button(right, "", self._apply, ACCENT, "#10121a",
                                      padx=20, bold=True)
        self.apply_btn.pack(pady=4)
        self.restore_btn = self._button(right, "", self._restore, PANEL2, RED, padx=14)
        self.restore_btn.pack(pady=4)

        self.status = tk.Label(self, bg=BG, fg=MUTED, font=(self.fam, 10), justify="center")
        self.status.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self._texts()

    # навешиваем колесо прокрутки на всё дерево списка
    def _wheel(self, w):
        w.bind("<MouseWheel>", lambda e: self.list.yview_scroll(-e.delta // 120, "units"))
        w.bind("<Button-4>", lambda e: self.list.yview_scroll(-1, "units"))
        w.bind("<Button-5>", lambda e: self.list.yview_scroll(1, "units"))
        for c in w.winfo_children():
            self._wheel(c)

    def _button(self, parent, text, cmd, bg, fg, small=False, bold=False, padx=6, pady=1):
        b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="hand2", padx=padx,
                     pady=3 if small else pady + 4,
                     font=(self.fam, 9 if small else 10, "bold" if bold else "normal"))
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e: b.configure(bg=PANEL2 if bg == PANEL2 else "#8fb0f9"))
        b.bind("<Leave>", lambda e: b.configure(bg=bg))
        return b

    # ---------- список ----------
    def _fill_list(self):
        for r in self._rows:
            r.destroy()
        self._rows = []

        q = self.search_var.get().strip().lower()
        if q == self.t["search"]:
            q = ""
        shown = [a for a in self.all_apps if q in a.name.lower()]

        for a in shown:
            row = tk.Frame(self.inner, bg=PANEL, cursor="hand2")
            row.pack(fill="x")
            bar = tk.Frame(row, bg=ACCENT, width=3)
            lbl = tk.Label(row, text=a.name, bg=PANEL, fg=TEXT, anchor="w",
                           font=(self.fam, 10), padx=14, pady=7)
            lbl.pack(fill="x")
            a._row = row
            a._bar = bar
            a._lbl = lbl
            row.bind("<Button-1>", lambda e, x=a: self._select(x))
            lbl.bind("<Button-1>", lambda e, x=a: self._select(x))
            row.bind("<Enter>", lambda e, x=a: self._row_bg(x, PANEL2))
            lbl.bind("<Enter>", lambda e, x=a: self._row_bg(x, PANEL2))
            row.bind("<Leave>", lambda e, x=a: self._row_bg(x, PANEL))
            lbl.bind("<Leave>", lambda e, x=a: self._row_bg(x, PANEL))
            self._wheel(row)
            self._wheel(lbl)
            self._rows.append(row)

        self.count_label.configure(text=self.t["loaded"].format(len(shown)))
        self.list.yview_moveto(0)

    def _row_bg(self, app, color):
        if self.selected is app:
            return
        if not app._row.winfo_exists():
            return
        app._row.configure(bg=color)
        app._lbl.configure(bg=color)

    def _select(self, app):
        if self.selected is not None and self.selected._row.winfo_exists():
            self._row_bg_plain(self.selected)
            self.selected._bar.pack_forget()
        self.selected = app
        app._bar.pack(side="left", fill="y")
        app._row.configure(bg=PANEL2)
        app._lbl.configure(bg=PANEL2)
        self.app_name.configure(text=app.name)
        self._show_current(app)

    def _row_bg_plain(self, app):
        app._row.configure(bg=PANEL)
        app._lbl.configure(bg=PANEL)

    # ---------- превью ----------
    def _show_current(self, app):
        path = _find_icon(app.icon)
        self._cur_thumb = None
        if path:
            try:
                img = Image.open(path).convert("RGBA").resize((88, 88), Image.LANCZOS)
                self._cur_thumb = ImageTk.PhotoImage(img)
                self.cur_prev.configure(image=self._cur_thumb, text="", width=88)
                return
            except Exception:
                pass
        self.cur_prev.configure(image="", text="?", width=12)

    def _show_new(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((88, 88), Image.LANCZOS)
            self._thumb = ImageTk.PhotoImage(img)
            self.new_prev.configure(image=self._thumb, text="", width=88)
        except Exception:
            self.new_prev.configure(image="", text="!", width=12)

    # ---------- действия ----------
    def _pick_image(self):
        path = filedialog.askopenfilename(
            title=self.t["new"],
            filetypes=[self.t["img_types"], ("All files", "*.*")])
        if not path:
            return
        self.image_path = path
        self._show_new(path)
        self._say(path.rsplit("/", 1)[-1])

    def _apply(self):
        if self.selected is None:
            return self._say(self.t["need_app"], RED)
        if not self.image_path:
            return self._say(self.t["need_image"], RED)
        app = self.selected
        out = backup.ROOT / "icons" / app.id
        try:
            icons.make_icons(self.image_path, out)
            self.platform.apply(app, out)
        except Exception as e:
            return self._say(str(e), RED)
        self._show_current(app)
        self._say(self.t["applied"], GREEN)

    def _restore(self):
        if self.selected is None:
            return self._say(self.t["need_app"], RED)
        try:
            self.platform.restore(self.selected)
        except Exception as e:
            return self._say(str(e), RED)
        self._show_current(self.selected)
        self._say(self.t["restored"], GREEN)

    # ---------- язык и мелочи ----------
    def _texts(self):
        t = self.t
        self.subtitle.configure(text=t["subtitle"])
        self.lang_btn.configure(text=LANGS["en" if self.lang == "ru" else "ru"]["lang"])
        self.cur_title.configure(text=t["current"])
        self.new_title.configure(text=t["new"])
        if not self.image_path:
            self.new_prev.configure(text=t["new"], image="", width=12)
        self.pick_btn.configure(text=t["pick"])
        self.apply_btn.configure(text=t["apply"])
        self.restore_btn.configure(text=t["restore"])
        self._say(t["select_hint"])
        val = self.search_var.get()
        was_placeholder = val == LANGS["en" if self.lang == "en" else "ru"]["search"] or val == ""
        self.search_var.set(t["search"] if not self.search.get() else val)
        if was_placeholder:
            self.search_var.set(t["search"])

    def _switch_lang(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.t = LANGS[self.lang]
        self._texts()
        self._fill_list()

    def _say(self, text, color=MUTED):
        self.status.configure(text=text, fg=color)

    def _placeholder_out(self, _e=None):
        if self.search_var.get() == self.t["search"]:
            self.search.delete(0, "end")

    def _placeholder_in(self, _e=None):
        if not self.search_var.get():
            self.search.insert(0, self.t["search"])
