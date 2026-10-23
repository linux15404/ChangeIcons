import os
import tkinter as tk
from tkinter import filedialog, font as tkfont
from pathlib import Path

from PIL import Image, ImageTk

from ..core import backup
from ..core import icons
from ..core.apps import from_path
from ..platforms.base import get_platform
from .strings import LANGS

# чёрно-белая палитра: от чёрного к светло-серому
BG = "#0a0a0a"
PANEL = "#151515"
PANEL2 = "#212121"
HOVER = "#2c2c2c"
TEXT = "#f2f2f2"
MUTED = "#8d8d8d"

LOGO = Path(__file__).parent.parent / "assets/logo.png"

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def _initial_dir():
    if os.name == "nt":
        return str(Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs")
    d = "/usr/share/applications"
    return d if os.path.isdir(d) else str(Path.home())


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChangeIcons")
        self.configure(bg=BG)
        self.geometry("460x330")
        self.minsize(430, 310)

        fams = tkfont.families()
        self.fam = next((f for f in ("Ubuntu", "Noto Sans", "Segoe UI", "DejaVu Sans") if f in fams), "TkDefaultFont")

        try:
            self.iconphoto(True, ImageTk.PhotoImage(Image.open(LOGO)))
        except Exception:
            pass

        self.lang = "ru"
        self.t = LANGS[self.lang]
        self.platform = get_platform()
        self.selected = None   # собранный из пути App
        self.app_path = None
        self.image_path = None
        self._thumb = None     # PhotoImage надо держать в поле, иначе его удалит сборщик

        self._build()

    # ---------- каркас ----------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        head = tk.Frame(self, bg=PANEL)
        head.grid(row=0, column=0, sticky="ew")
        logo = Image.open(LOGO).resize((26, 26), Image.LANCZOS)
        self._logo_img = ImageTk.PhotoImage(logo)
        tk.Label(head, image=self._logo_img, bg=PANEL).pack(side="left", padx=(14, 8), pady=8)
        tk.Label(head, text="ChangeIcons", bg=PANEL, fg=TEXT,
                 font=(self.fam, 12, "bold")).pack(side="left")
        self.lang_btn = self._button(head, LANGS["en"]["lang"], self._switch_lang,
                                     PANEL, MUTED, padx=10)
        self.lang_btn.pack(side="right", padx=12)

        body = tk.Frame(self, bg=BG)
        body.grid(row=1, column=0, sticky="nsew")
        box = tk.Frame(body, bg=BG)
        box.pack(expand=True, fill="both")
        inner = tk.Frame(box, bg=BG)
        inner.pack(expand=True)

        # приложение: поле пути + кнопка выбора
        row1 = tk.Frame(inner, bg=BG)
        row1.pack(fill="x", pady=(0, 8))
        self.app_entry = self._entry(row1, self.t["app_ph"])
        self.app_entry.pack(side="left", fill="x", expand=True, ipadx=6, ipady=6)
        self.app_entry.bind("<Return>", self._load_app_from_entry)
        self.app_btn = self._button(row1, self.t["pick_app"], self._pick_app, PANEL2, TEXT, padx=12)
        self.app_btn.pack(side="left", padx=(8, 0))

        # картинка: миник превью + поле пути + кнопка
        row2 = tk.Frame(inner, bg=BG)
        row2.pack(fill="x", pady=(0, 18))
        self.thumb = tk.Label(row2, text="", bg=PANEL2, width=3, fg=MUTED)
        self.thumb.pack(side="left", ipady=3, ipadx=3, padx=(0, 8))
        self.img_entry = self._entry(row2, self.t["img_ph"])
        self.img_entry.pack(side="left", fill="x", expand=True, ipadx=6, ipady=6)
        self.img_entry.bind("<Return>", self._load_img_from_entry)
        self.img_btn = self._button(row2, self.t["pick_img"], self._pick_image, PANEL2, TEXT, padx=12)
        self.img_btn.pack(side="left", padx=(8, 0))

        row3 = tk.Frame(inner, bg=BG)
        row3.pack()
        self.apply_btn = self._button(row3, self.t["apply"], self._apply, TEXT, BG, padx=18, bold=True)
        self.apply_btn.pack(side="left", padx=(0, 8))
        self.restore_btn = self._button(row3, self.t["restore"], self._restore, PANEL2, TEXT, padx=18)
        self.restore_btn.pack(side="left")

        self.status = tk.Label(inner, bg=BG, fg=MUTED, font=(self.fam, 9))
        self.status.pack(pady=(14, 0))
        self._say(self.t["hint"])

        self._texts()

    def _entry(self, parent, ph):
        e = tk.Entry(parent, bg=PANEL2, fg=MUTED, relief="flat", highlightthickness=0,
                     insertbackground=TEXT, font=(self.fam, 9))
        e.insert(0, ph)
        e.bind("<FocusIn>", lambda e: self._out(e.widget))
        e.bind("<FocusOut>", lambda e: self._back(e.widget, ph))
        return e

    def _out(self, e):
        if e.get() in (self.t["app_ph"], self.t["img_ph"]):
            e.delete(0, "end")
        e.configure(fg=TEXT)

    def _back(self, e, ph):
        if not e.get():
            e.insert(0, ph)
            e.configure(fg=MUTED)

    def _button(self, parent, text, cmd, bg, fg, padx=6, bold=False):
        # все кнопки одного размера и стиля; активная — белая
        b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="hand2", padx=padx, pady=5,
                     font=(self.fam, 9, "bold" if bold else "normal"))
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>", lambda e, r=b, c=bg: r.configure(bg=HOVER if c != TEXT else "#d0d0d0"))
        b.bind("<Leave>", lambda e, r=b, c=bg: r.configure(bg=c))
        return b

    # ---------- выбор ----------
    def _pick_app(self):
        kinds = [("Desktop", "*.desktop")] if os.name != "nt" else [("Shortcuts", "*.lnk *.exe")]
        path = filedialog.askopenfilename(title=self.t["dlg_app"],
                                          initialdir=_initial_dir(), filetypes=[kinds[0], ("All files", "*.*")])
        if path:
            self.app_entry.delete(0, "end")
            self.app_entry.insert(0, path)
            self._load_app(path)

    def _pick_image(self):
        path = filedialog.askopenfilename(title=self.t["dlg_img"],
                                          filetypes=[self.t["img_types"], ("All files", "*.*")])
        if path:
            self.img_entry.delete(0, "end")
            self.img_entry.insert(0, path)
            self._load_image(path)

    def _load_app_from_entry(self, _e=None):
        self._load_app(self.app_entry.get())

    def _load_img_from_entry(self, _e=None):
        self._load_image(self.img_entry.get())

    def _load_app(self, path):
        try:
            self.selected = from_path(path)
        except Exception:
            self.selected = None
            return self._say(self.t["bad_path"])
        self.app_path = path
        self._say(self.selected.name + "  —  " + self.t["hint"])

    def _load_image(self, path):
        if not os.path.isfile(path):
            return
        self.image_path = path
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((28, 28), Image.LANCZOS)
            self._thumb = ImageTk.PhotoImage(img)
            self.thumb.configure(image=self._thumb, text="", width=28)
        except Exception:
            self.thumb.configure(image="", text="!", width=3)

    # ---------- действия ----------
    def _apply(self):
        if self.selected is None:
            return self._say(self.t["need_app"])
        if not self.image_path:
            return self._say(self.t["need_img"])
        out = backup.ROOT / "icons" / self.selected.id
        out.mkdir(parents=True, exist_ok=True)
        try:
            icons.make_icons(self.image_path, out)
            self.platform.apply(self.selected, out)
        except Exception as e:
            return self._say(str(e))
        self._say(self.t["applied"])

    def _restore(self):
        if self.selected is None:
            return self._say(self.t["need_app"])
        try:
            self.platform.restore(self.selected)
        except Exception as e:
            return self._say(str(e))
        self._say(self.t["restored"])

    # ---------- язык ----------
    def _texts(self):
        t = self.t
        self.lang_btn.configure(text=LANGS["en" if self.lang == "ru" else "ru"]["lang"])
        self.app_btn.configure(text=t["pick_app"])
        self.img_btn.configure(text=t["pick_img"])
        self.apply_btn.configure(text=t["apply"])
        self.restore_btn.configure(text=t["restore"])
        self._field(self.app_entry, self.app_path, t["app_ph"])
        self._field(self.img_entry, self.image_path, t["img_ph"])
        self._say(self.t["hint"])

    def _field(self, e, path, ph):
        e.delete(0, "end")
        e.insert(0, path or ph)

    def _switch_lang(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.t = LANGS[self.lang]
        self._texts()

    def _say(self, text, color=MUTED):
        self.status.configure(text=text, fg=color)
