"""Design system NEXAFISH: palet warna, font bergaya iOS, skala layar (DPI), gaya ttk, dan helper bentuk.

Hanya tampilan. Nama-nama lama (C, f, fi, mix, titik_bulat, titik_segienam, atur_gaya) dipertahankan
agar seluruh halaman tetap kompatibel.
"""

import os
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# Penyebab teks tampak "pecah / 8-bit" di layar resolusi tinggi: secara bawaan Tkinter di Windows tidak
# mendaftarkan diri sebagai aplikasi sadar-DPI, sehingga Windows memperbesar jendela sebagai gambar (bitmap).
# DPI_AWARE = True membuat teks digambar langsung pada resolusi asli layar (tajam) dan seluruh ukuran
# (jarak, tinggi tombol, ikon) ikut diskalakan otomatis. Bila ada masalah tampilan, ubah ke False.
DPI_AWARE = True

SKALA = 1.0  # faktor skala layar (1.0 = 96 DPI / 100%); diisi oleh atur_skala()


def px(n):
    """Ukuran desain (px pada 100%) -> piksel fisik sesuai skala layar."""
    if not n:
        return 0
    tanda = -1 if n < 0 else 1
    return tanda * max(1, int(round(abs(n) * SKALA)))


class Fisik(str):
    """Ukuran yang SUDAH berupa piksel fisik (tidak diskalakan lagi oleh penskala opsi Tk)."""


def fisik(n):
    return Fisik(str(int(round(n))))


def aktifkan_dpi():
    """Daftarkan proses sebagai sadar-DPI. HARUS dipanggil sebelum jendela Tk pertama dibuat."""
    if not DPI_AWARE or os.name != "nt":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# --- Penskala opsi Tk: ukuran angka pada widget & geometri (padx, pady, width, height, ...) dikalikan SKALA ---
_PX_UMUM = {"-padx", "-pady", "-ipadx", "-ipady", "-bd", "-borderwidth", "-highlightthickness",
            "-wraplength", "-minsize", "-pad", "-x", "-y", "-selectborderwidth", "-insertwidth"}
_PX_UKURAN = {"-width", "-height"}
_WIDGET_PX = {"frame", "canvas", "toplevel", "labelframe", "panedwindow"}
_options_asli = tk.Misc._options
_terpasang = False


def _skala_nilai(v):
    if isinstance(v, Fisik) or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return px(v)
    if isinstance(v, str) and v.strip():
        token = v.split()
        if all(t.lstrip("-").isdigit() for t in token):
            return " ".join(str(px(int(t))) for t in token)
    return v


def _options_skala(self, cnf, kw=None):
    hasil = _options_asli(self, cnf, kw)
    if not hasil:
        return hasil
    nama = getattr(self, "widgetName", "")
    out = list(hasil)
    for i in range(0, len(out) - 1, 2):
        k = out[i]
        if k in _PX_UMUM or (k in _PX_UKURAN and nama in _WIDGET_PX):
            out[i + 1] = _skala_nilai(out[i + 1])
    return tuple(out)


def atur_skala(root):
    """Hitung skala layar dan pasang penskala. Panggil tepat setelah Tk() dibuat, sebelum widget lain."""
    global SKALA, _terpasang
    try:
        dpi = float(root.winfo_fpixels("1i"))
    except tk.TclError:
        dpi = 96.0
    SKALA = max(1.0, round(dpi / 96.0, 2))
    try:
        root.tk.call("tk", "scaling", dpi / 72.0)
    except tk.TclError:
        pass
    if SKALA > 1.02 and not _terpasang:
        tk.Misc._options = _options_skala
        _terpasang = True
    return SKALA


# Urutan preferensi font: SF Pro (Apple) -> Segoe UI Variable (Windows 11) -> Segoe UI -> lainnya.
DAFTAR_FONT = (
    "SF Pro Text", "SF Pro Display", "Segoe UI Variable Text", "Segoe UI Variable Display",
    "Segoe UI", "Helvetica Neue", "Inter", "Roboto", "Arial",
)
FONT = "Segoe UI"
FONT_IKON = "Segoe UI Symbol"

# Tampilan logo di sidebar & login:
#   "ikon"     -> logo.png ditampilkan sebagai emblem persegi di samping teks NEXAFISH
#   "wordmark" -> logo.png sudah memuat tulisan NEXAFISH, tampil sendiri tanpa teks tambahan
LOGO_MODE = "ikon"

# Palet warna
C = {
    # Sidebar (navy)
    "side": "#0F2547",
    "side_secondary": "#163159",
    "side_hover": "#173560",
    "side_active": "#1E4278",
    "side_line": "#233F6C",
    "side_text": "#A9BBD8",
    "side_muted": "#6F88B0",

    # Latar & permukaan
    "bg": "#EEF2F8",
    "header": "#FFFFFF",
    "card": "#FFFFFF",
    "head": "#F5F8FC",
    "zebra": "#F9FBFE",
    "select": "#DDE9FB",
    "border": "#E2E8F1",

    # Warna utama
    "primary": "#1E4E9C",
    "primary_hover": "#2A62BB",
    "accent": "#4C8DF6",
    "accent_hover": "#3B7BE0",
    "teal": "#1E4E9C",
    "blue": "#4C8DF6",
    "blue_soft": "#E8F0FE",

    # Teks
    "text": "#14253D",
    "text_primary": "#14253D",
    "muted": "#6B7A90",
    "text_secondary": "#6B7A90",
    "faint": "#A3AFC0",

    # Status
    "green": "#12A375",
    "success": "#12A375",
    "green_soft": "#E3F7EF",
    "green_text": "#0B7B58",

    "amber": "#F5A524",
    "warning": "#F5A524",
    "amber_soft": "#FFF5DD",
    "amber_text": "#A8650A",

    "red": "#EF4A5B",
    "danger": "#EF4A5B",
    "red_soft": "#FEECEE",
    "red_text": "#BE2A3B",

    "purple": "#8B5CF6",
    "purple_soft": "#F1EBFE",
    "indigo": "#5B6CF2",
    "indigo_soft": "#ECEEFE",
    "teal2": "#14B8A6",

    # Grafik
    "income": "#12A375",
    "expense": "#EF4A5B",
}


def init_fonts(root):
    """Pilih font terbaik yang tersedia (gaya iOS) lalu fallback ke font sistem."""
    global FONT, FONT_IKON
    ada = set(tkfont.families(root))
    FONT = next((n for n in DAFTAR_FONT if n in ada),
                tkfont.nametofont("TkDefaultFont").actual("family"))
    FONT_IKON = next((n for n in ("Segoe UI Symbol", "Apple Symbols", "DejaVu Sans", "Arial Unicode MS")
                      if n in ada), FONT)


def f(ukuran=10, tebal=False):
    """Font teks aplikasi."""
    return (FONT, ukuran, "bold" if tebal else "normal")


def fi(ukuran=12):
    """Font simbol Unicode."""
    return (FONT_IKON, ukuran)


def mix(c1, c2, t):
    """Interpolasi linier warna hex."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lembut(warna, t=0.88):
    """Versi sangat pucat sebuah warna (untuk latar ikon / chip)."""
    return mix(warna, "#FFFFFF", t)


def titik_bulat(x1, y1, x2, y2, r):
    """Titik poligon rounded rectangle (dipakai bila Pillow tidak tersedia)."""
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def titik_segienam(cx, cy, r, rotasi=0.0):
    import math
    pts = []
    for i in range(6):
        a = math.radians(60 * i + 30 + rotasi)
        pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


def atur_gaya(root):
    """Daftarkan seluruh gaya ttk (Treeview, Combobox, Scrollbar)."""
    s = ttk.Style(root)
    s.theme_use("clam")
    init_fonts(root)

    root.option_add("*TCombobox*Listbox.font", f(10))
    root.option_add("*TCombobox*Listbox.background", "white")
    root.option_add("*TCombobox*Listbox.foreground", C["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", C["select"])
    root.option_add("*TCombobox*Listbox.selectForeground", C["text"])
    root.option_add("*TCombobox*Listbox.borderWidth", "0")

    # Tabel
    s.configure("Nexa.Treeview", background="white", fieldbackground="white",
                foreground=C["text"], rowheight=px(42), borderwidth=0, relief="flat", font=f(10))
    s.configure("Nexa.Treeview.Heading", background=C["head"], foreground=C["muted"],
                font=f(9, True), relief="flat", padding=(px(12), px(11)), borderwidth=0,
                bordercolor=C["head"], lightcolor=C["head"], darkcolor=C["head"])
    s.map("Nexa.Treeview",
          background=[("selected", C["select"])],
          foreground=[("selected", C["text"])])
    s.map("Nexa.Treeview.Heading", background=[("active", "#EAF0F9")])
    s.layout("Nexa.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # Combobox ttk (cadangan; komponen utama memakai Combo buatan sendiri di widgets.py)
    s.configure("Nexa.TCombobox", padding=(px(8), px(7)), fieldbackground="white", background="white",
                bordercolor=C["border"], lightcolor=C["border"], darkcolor=C["border"],
                arrowsize=px(15), foreground=C["text"], arrowcolor=C["muted"], relief="flat")

    # Scrollbar tipis tanpa panah (vertikal & horizontal)
    for arah, sisi, nama in (("Vertical", "ns", "Vertical"), ("Horizontal", "ew", "Horizontal")):
        gaya = f"{arah}.TScrollbar"
        s.configure(gaya, background="#CBD5E3", troughcolor="white", bordercolor="white",
                    lightcolor="#CBD5E3", darkcolor="#CBD5E3", arrowsize=px(9), relief="flat", borderwidth=0)
        s.map(gaya, background=[("active", "#A9B8CE"), ("pressed", "#94A6C0")])
        try:
            s.layout(gaya, [(f"{nama}.Scrollbar.trough", {
                "sticky": sisi, "children": [(f"{nama}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        except tk.TclError:
            pass
