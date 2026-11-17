"""Komponen UI NEXAFISH: Tombol, Isian, Kartu, Chip, Tabel, Dialog, Logo, dan kawan-kawan.

Hanya tampilan. Nama dan tanda tangan fungsi lama (Tombol, Isian, Logo, kartu, kartu_stat, buat_combo,
buat_tabel, isi_tabel, Dialog, nexa_dialog) dipertahankan agar halaman lain tetap berjalan.
"""

import os
import sqlite3
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

try:
    import gfx
    from theme import C, f, fi, mix, lembut, titik_bulat, px, fisik
except ImportError:  # struktur paket lama: ui/...
    from ui import gfx
    from ui.theme import C, f, fi, mix, lembut, titik_bulat, px, fisik

PIL_OK = gfx.PIL_OK


def _latar(widget, default=None):
    """Warna latar widget induk dalam format #rrggbb (aman untuk nama warna sistem)."""
    try:
        warna = widget.cget("bg")
        r, g, b = widget.winfo_rgb(warna)
        return "#%02x%02x%02x" % (r >> 8, g >> 8, b >> 8)
    except (tk.TclError, AttributeError):
        return default or C["bg"]


def _ukur(teks, fnt):
    return tkfont.Font(font=fnt).measure(teks)


# ------------------------------------------------------------
#  Pojok membulat untuk Frame biasa
# ------------------------------------------------------------
class PojokBulat:
    """Menempelkan empat gambar sudut di pojok Frame agar tampak membulat (butuh Pillow).

    radius & tinggi pita adalah ukuran desain; diskalakan otomatis ke piksel fisik."""

    def __init__(self, frame, radius, latar, isi, garis, bar=None, isi_atas=None):
        self.frame, self.r, self.latar, self.isi = frame, px(radius), latar, isi
        self.bar = (bar[0], bar[1], px(4)) if bar else None
        self.isi_atas = isi_atas
        self.label = []
        self._img = None
        if not PIL_OK:
            return
        for _ in range(4):
            self.label.append(tk.Label(frame, bd=0, highlightthickness=0, padx=0, pady=0, bg=latar))
        self.ganti(garis)
        kiri_atas, kanan_atas, kiri_bawah, kanan_bawah = self.label
        kiri_atas.place(x=0, y=0)
        kanan_atas.place(relx=1.0, y=0, anchor="ne")
        kiri_bawah.place(x=0, rely=1.0, anchor="sw")
        kanan_bawah.place(relx=1.0, rely=1.0, anchor="se")
        frame.bind("<Configure>", self.angkat, add="+")
        frame.bind("<Map>", self.angkat, add="+")
        frame.after_idle(self.angkat)

    def ganti(self, garis):
        if not self.label:
            return
        self._img = gfx.sudut(self.r, self.latar, self.isi, garis, self.bar, tebal=px(1), isi_atas=self.isi_atas)
        for lb, im in zip(self.label, self._img):
            lb.configure(image=im)

    def angkat(self, _e=None):
        for lb in self.label:
            try:
                lb.lift()
            except tk.TclError:
                pass


# ------------------------------------------------------------
#  Tombol
# ------------------------------------------------------------
class Tombol(tk.Canvas):
    """Tombol membulat halus.

    gaya="solid"   -> terisi warna primer (atau parameter warna)
    gaya="outline" -> putih berborder tipis
    gaya="soft"    -> latar pucat dengan teks berwarna
    gaya="success" / "danger" / "warning" -> warna status
    """

    def __init__(self, master, teks, command, warna=None, fg="white", lebar=None,
                 tinggi=38, ukuran=10, radius=10, gaya="solid", ikon=""):
        self.gaya = gaya
        self.garis = None
        if gaya == "outline":
            self.warna, self.fg = "#FFFFFF", warna or C["text"]
            self.hover, self.tekan = "#F3F6FB", "#E8EEF7"
            self.garis = C["border"]
        elif gaya == "soft":
            dasar = warna or C["primary"]
            self.warna, self.fg = lembut(dasar, 0.9), dasar
            self.hover, self.tekan = lembut(dasar, 0.8), lembut(dasar, 0.7)
        else:
            if gaya == "success":
                dasar = C["success"]
            elif gaya == "danger":
                dasar = C["danger"]
            elif gaya == "warning":
                dasar = C["warning"]
            else:
                dasar = warna or C["primary"]
            self.warna, self.fg = dasar, fg
            self.hover, self.tekan = mix(dasar, "#000000", 0.10), mix(dasar, "#000000", 0.2)

        self.radius = radius
        self.command = command
        self.teks = f"{ikon}  {teks}" if ikon else teks
        self.fnt = f(ukuran, gaya != "outline")
        self._img = None
        if lebar is None:
            lebar = fisik(_ukur(self.teks, self.fnt) + px(36))
        super().__init__(master, width=lebar, height=tinggi, bg=_latar(master),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.bind("<Configure>", lambda e: self._gambar(self.warna))
        self.bind("<Enter>", lambda e: self._gambar(self.hover))
        self.bind("<Leave>", lambda e: self._gambar(self.warna))
        self.bind("<ButtonPress-1>", lambda e: self._gambar(self.tekan))
        self.bind("<ButtonRelease-1>", self._klik)

    def _gambar(self, warna=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        warna = warna or self.warna
        self.delete("all")
        if PIL_OK:
            self._img = gfx.kotak_bulat(w, h, px(self.radius), warna, self.garis, px(1))
            self.create_image(0, 0, anchor="nw", image=self._img)
        else:
            self.create_polygon(titik_bulat(1, 1, w - 1, h - 1, px(self.radius)), smooth=True,
                                fill=warna, outline=self.garis or warna)
        self.create_text(w / 2, h / 2, text=self.teks, fill=self.fg, font=self.fnt)

    def _klik(self, e):
        self._gambar(self.hover)
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            if callable(self.command):
                self.command()


# ------------------------------------------------------------
#  Chip, kotak ikon, kontrol segmen
# ------------------------------------------------------------
class Chip(tk.Canvas):
    """Label kecil berbentuk pil (status, badge). Ukuran mengikuti teks."""

    def __init__(self, master, teks, fg=None, bg=None, ukuran=8, tebal=True, ikon=None,
                 tinggi=24, padx=10, garis=None):
        fg = fg or C["primary"]
        bg = bg or lembut(fg, 0.88)
        fnt = f(ukuran, tebal)
        ik = gfx.ikon(ikon, 13, fg) if ikon else None
        h, pad = px(tinggi), px(padx)
        w = pad * 2 + _ukur(teks, fnt) + (px(18) if ik else 0)
        super().__init__(master, width=fisik(w), height=fisik(h), bg=_latar(master),
                         highlightthickness=0, bd=0)
        if PIL_OK:
            self._bg = gfx.kotak_bulat(w, h, h // 2, bg, garis, px(1))
            self.create_image(0, 0, anchor="nw", image=self._bg)
        else:
            self.create_polygon(titik_bulat(1, 1, w - 1, h - 1, h // 2), smooth=True, fill=bg, outline=bg)
        x = pad
        if ik:
            self._ik = ik
            self.create_image(x, h / 2, anchor="w", image=ik)
            x += px(18)
        self.create_text(x, h / 2, text=teks, anchor="w", fill=fg, font=fnt)


class IkonKotak(tk.Canvas):
    """Ikon di dalam kotak membulat berlatar pucat (seperti ikon kartu KPI)."""

    def __init__(self, master, nama, warna, ukuran=40, radius=12, ukuran_ikon=None, latar=None):
        u = px(ukuran)
        super().__init__(master, width=fisik(u), height=fisik(u), bg=latar or _latar(master),
                         highlightthickness=0, bd=0)
        pucat = lembut(warna, 0.88)
        if PIL_OK:
            self._bg = gfx.kotak_bulat(u, u, px(radius), pucat)
            self.create_image(0, 0, anchor="nw", image=self._bg)
        else:
            self.create_polygon(titik_bulat(1, 1, u - 1, u - 1, px(radius)), smooth=True,
                                fill=pucat, outline=pucat)
        self._ik = gfx.ikon(nama, ukuran_ikon or int(ukuran * 0.5), warna)
        if self._ik:
            self.create_image(u / 2, u / 2, image=self._ik)
        else:
            self.create_text(u / 2, u / 2, text="●", fill=warna, font=fi(11))


class Segmen(tk.Canvas):
    """Kontrol segmen ala iOS. opsi = [(kunci, teks), ...]; command(kunci) dipanggil saat berganti."""

    def __init__(self, master, opsi, nilai, command, tinggi=36, ukuran=9):
        self.fnt = f(ukuran, True)
        self.opsi = [(k, t, _ukur(t, self.fnt) + px(34)) for k, t in opsi]
        self.nilai, self.command, self.h = nilai, command, px(tinggi)
        self.w = sum(o[2] for o in self.opsi) + px(6)
        self._imgs = []
        super().__init__(master, width=fisik(self.w), height=fisik(self.h), bg=_latar(master),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.bind("<Button-1>", self._klik)
        self._gambar()

    def pilih(self, nilai):
        self.nilai = nilai
        self._gambar()

    def _gambar(self):
        self.delete("all")
        self._imgs = []
        w, h, t = self.w, self.h, px(3)
        if PIL_OK:
            bg = gfx.kotak_bulat(w, h, px(11), "#E6ECF5")
            self._imgs.append(bg)
            self.create_image(0, 0, anchor="nw", image=bg)
        else:
            self.create_polygon(titik_bulat(1, 1, w - 1, h - 1, px(10)), smooth=True, fill="#E6ECF5", outline="#E6ECF5")
        x = t
        for kunci, teks, lb in self.opsi:
            aktif = kunci == self.nilai
            if aktif:
                if PIL_OK:
                    im = gfx.kotak_bulat(lb, h - 2 * t, px(9), "#FFFFFF", C["border"], px(1))
                    self._imgs.append(im)
                    self.create_image(x, t, anchor="nw", image=im)
                else:
                    self.create_polygon(titik_bulat(x, t, x + lb, h - t, px(8)), smooth=True,
                                        fill="#FFFFFF", outline=C["border"])
            self.create_text(x + lb / 2, h / 2, text=teks, font=self.fnt,
                             fill=C["primary"] if aktif else C["muted"])
            x += lb

    def _klik(self, e):
        x = px(3)
        for kunci, _t, lb in self.opsi:
            if x <= e.x < x + lb:
                if kunci != self.nilai:
                    self.nilai = kunci
                    self._gambar()
                    if callable(self.command):
                        self.command(kunci)
                return
            x += lb


# ------------------------------------------------------------
#  Kartu
# ------------------------------------------------------------
class Kartu(tk.Frame):
    """Kontainer putih dengan sudut membulat dan garis tipis. bar=(warna1, warna2) menambah pita gradasi di dasar."""

    def __init__(self, parent, radius=12, bg="white", garis=None, bar=None, isi_atas=None):
        garis = garis or C["border"]
        super().__init__(parent, bg=bg, highlightbackground=garis, highlightthickness=1)
        self._bar = bar
        if bar:
            self.kanvas_bar = tk.Canvas(self, height=4, bg=bg, highlightthickness=0, bd=0)
            self.kanvas_bar.pack(side="bottom", fill="x")
            self.kanvas_bar.bind("<Configure>", self._gambar_bar)
        self._pojok = PojokBulat(self, radius, _latar(parent), bg, garis, bar=bar, isi_atas=isi_atas)

    def _gambar_bar(self, e):
        w, tinggi = e.width, max(e.height, 1)
        c1, c2 = self._bar
        self.kanvas_bar.delete("all")
        n = max(w // px(6), 1)
        for i in range(n):
            warna = mix(c1, c2, i / max(n - 1, 1))
            self.kanvas_bar.create_rectangle(int(i * w / n), 0, int((i + 1) * w / n) + 1, tinggi,
                                             fill=warna, outline=warna, width=0)

    def angkat_sudut(self):
        self._pojok.angkat()


def kartu(parent):
    """Kontainer card putih standar (sudut membulat)."""
    return Kartu(parent)


def kartu_stat(parent, judul, nilai, warna, ikon=None, sub="", chip=None, chip_warna=None, warna2=None):
    """Kartu KPI: judul kecil, ikon berlatar pucat, angka besar, chip/keterangan, pita gradasi di dasar."""
    k = Kartu(parent, bar=(warna, warna2 or mix(warna, "#FFFFFF", 0.5)))
    isi = tk.Frame(k, bg="white")
    isi.pack(fill="both", expand=True, padx=22, pady=(20, 14))

    atas = tk.Frame(isi, bg="white")
    atas.pack(fill="x")
    tk.Label(atas, text=judul.upper(), font=f(8, True), fg=C["muted"], bg="white",
             anchor="w").pack(side="left")
    if ikon:
        IkonKotak(atas, ikon, warna, ukuran=38, radius=11).pack(side="right")

    tk.Label(isi, text=nilai, font=f(20, True), fg=C["text"], bg="white",
             anchor="w").pack(fill="x", pady=(8, 8))

    bawah = tk.Frame(isi, bg="white")
    bawah.pack(fill="x")
    if chip:
        cw = chip_warna or warna
        Chip(bawah, chip, fg=cw, bg=lembut(cw, 0.88)).pack(side="left")
    if sub:
        tk.Label(bawah, text=sub, font=f(8), fg=C["muted"], bg="white").pack(side="left", padx=(8 if chip else 0, 0))
    if not chip and not sub:
        tk.Frame(bawah, bg="white", height=24).pack()
    return k


# ------------------------------------------------------------
#  Dialog pesan
# ------------------------------------------------------------
def nexa_dialog(judul, pesan, jenis="info", parent=None, konfirmasi=False):
    induk = parent.winfo_toplevel() if parent is not None else tk._default_root
    if induk is None:
        return False

    gaya = {
        "info": (C["primary"], "seru"),
        "success": (C["green"], "cek"),
        "warning": (C["amber"], "peringatan"),
        "error": (C["red"], "silang"),
        "question": (C["primary"], "seru"),
    }
    aksen, nama_ikon = gaya.get(jenis, gaya["info"])

    dlg = tk.Toplevel(induk)
    dlg.title(judul)
    dlg.configure(bg=C["border"])
    dlg.resizable(False, False)
    dlg.transient(induk)

    kartu_ = tk.Frame(dlg, bg="white")
    kartu_.pack(fill="both", expand=True, padx=1, pady=1)
    isi = tk.Frame(kartu_, bg="white")
    isi.pack(fill="both", expand=True, padx=28, pady=(26, 20))

    baris = tk.Frame(isi, bg="white")
    baris.pack(fill="x")
    IkonKotak(baris, nama_ikon, aksen, ukuran=44, radius=14).pack(side="left", padx=(0, 14))
    tk.Label(baris, text=judul, font=f(13, True), bg="white", fg=C["text"], anchor="w",
             wraplength=340, justify="left").pack(side="left", fill="x", expand=True)

    tk.Label(isi, text=str(pesan), font=f(10), bg="white", fg=C["muted"],
             justify="left", anchor="w", wraplength=420).pack(fill="x", pady=(16, 6))

    hasil = {"ok": False}

    def tutup(nilai=False):
        hasil["ok"] = nilai
        try:
            dlg.grab_release()
        except tk.TclError:
            pass
        dlg.destroy()

    aksi = tk.Frame(isi, bg="white")
    aksi.pack(fill="x", pady=(16, 0))
    if konfirmasi:
        Tombol(aksi, "Batal", lambda: tutup(False), gaya="outline", tinggi=36, ukuran=9).pack(side="right", padx=(8, 0))
        Tombol(aksi, "Ya, Lanjutkan", lambda: tutup(True), warna=aksen, tinggi=36, ukuran=9).pack(side="right")
    else:
        Tombol(aksi, "Mengerti", lambda: tutup(True), warna=aksen, tinggi=36, ukuran=9).pack(side="right")

    dlg.protocol("WM_DELETE_WINDOW", lambda: tutup(False))
    dlg.bind("<Escape>", lambda _e: tutup(False))
    dlg.bind("<Return>", lambda _e: tutup(True))
    dlg.update_idletasks()

    lebar, tinggi = max(dlg.winfo_reqwidth(), px(460)), dlg.winfo_reqheight()
    x = induk.winfo_rootx() + max((induk.winfo_width() - lebar) // 2, 0)
    y = induk.winfo_rooty() + max((induk.winfo_height() - tinggi) // 2, 0)
    dlg.geometry(f"{lebar}x{tinggi}+{x}+{y}")

    try:
        dlg.wait_visibility()
        dlg.grab_set()
        dlg.focus_set()
    except tk.TclError:
        pass
    dlg.wait_window()
    return hasil["ok"]


def _nexa_message(kind):
    return lambda title, message, **options: nexa_dialog(
        title, message, kind, options.get("parent"))


messagebox.showinfo = _nexa_message("info")
messagebox.showwarning = _nexa_message("warning")
messagebox.showerror = _nexa_message("error")
messagebox.askyesno = lambda title, message, **options: nexa_dialog(
    title, message, "question", options.get("parent"), konfirmasi=True)


# ------------------------------------------------------------
#  Isian (input)
# ------------------------------------------------------------
class Isian(tk.Frame):
    """Kolom input membulat: border tipis, cincin biru saat fokus, placeholder, tombol lihat sandi."""

    def __init__(self, master, placeholder="", password=False, numeric=False, ikon=""):
        super().__init__(master, bg=C["border"])
        self.placeholder, self.password, self.numeric = placeholder, password, numeric
        self._ph = False

        dalam = tk.Frame(self, bg="white")
        dalam.pack(fill="x", padx=1, pady=1)

        if ikon:
            tk.Label(dalam, text=ikon, font=fi(11), bg="white", fg=C["muted"]).pack(side="left", padx=(12, 0))

        if password:
            self.lihat = tk.Label(dalam, text="Lihat", bg="white", fg=C["primary"],
                                  font=f(9, True), cursor="hand2", padx=12, pady=4)
            self.lihat.pack(side="right", fill="y")
            self.lihat.bind("<Button-1>", self._toggle)

        self.entry = tk.Entry(dalam, relief="flat", bd=0, bg="white", fg=C["text"],
                              insertbackground=C["text"], font=f(10), highlightthickness=0,
                              disabledbackground="#F3F6FA", disabledforeground=C["muted"],
                              show="*" if password else "")

        if numeric:
            self._validasi_cmd = (self.register(self._validasi_angka), "%P")
            self.entry.configure(validate="key", validatecommand=self._validasi_cmd)

        self.entry.pack(side="left", fill="x", expand=True, padx=(13, 8), pady=10)
        self.entry.bind("<FocusIn>", self._fokus_masuk)
        self.entry.bind("<FocusOut>", self._fokus_keluar)

        if placeholder and not password:
            self._pasang_ph()
        self._pojok = PojokBulat(self, 9, _latar(master), "white", C["border"])

    @staticmethod
    def _validasi_angka(teks):
        return all(ch in "0123456789., " for ch in teks)

    def _pasang_ph(self):
        if self.numeric:
            self.entry.configure(validate="none")
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        if self.numeric:
            self.entry.configure(validate="key", validatecommand=self._validasi_cmd)
        self.entry.config(fg=C["faint"])
        self._ph = True

    def _garis(self, warna):
        self.config(bg=warna)
        self._pojok.ganti(warna)

    def _fokus_masuk(self, _e=None):
        self._garis(C["accent"])
        if self._ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=C["text"])
            self._ph = False

    def _fokus_keluar(self, _e=None):
        self._garis(C["border"])
        if self.placeholder and not self.password and not self.entry.get():
            self._pasang_ph()

    def _toggle(self, _e=None):
        if self.entry.cget("show") == "*":
            self.entry.config(show="")
            self.lihat.config(text="Sembunyi")
        else:
            self.entry.config(show="*")
            self.lihat.config(text="Lihat")

    def get(self):
        return "" if self._ph else self.entry.get()

    def set(self, teks):
        self._ph = False
        self.entry.config(fg=C["text"])
        self.entry.delete(0, "end")
        self.entry.insert(0, teks)
        if not teks and self.placeholder and not self.password:
            self._pasang_ph()

    def clear(self):
        self.set("")

    def fokus(self):
        self.entry.focus_set()


# ------------------------------------------------------------
#  Logo NEXAFISH
# ------------------------------------------------------------
_KANDIDAT_LOGO = ("logo.png", "logp.png", "logo.jpg", "logo.jpeg")


def cari_logo():
    """Path file logo bila ada (logo.png di folder aplikasi), selain itu None."""
    folder = [os.path.dirname(os.path.abspath(__file__)), os.getcwd(),
              os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))]
    for d in folder:
        for nama in _KANDIDAT_LOGO:
            p = os.path.join(d, nama)
            if os.path.isfile(p):
                return p
    return None


def muat_logo(maks_w, maks_h):
    """PhotoImage logo yang dimuat muat di kotak maks_w x maks_h (proporsi terjaga), atau None."""
    path = cari_logo()
    if not path:
        return None
    maks_w, maks_h = px(maks_w), px(maks_h)
    if PIL_OK:
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGBA")
            rasio = min(maks_w / img.width, maks_h / img.height)
            w, h = max(1, int(img.width * rasio)), max(1, int(img.height * rasio))
            img = img.resize((w, h), getattr(Image, "Resampling", Image).LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
    try:
        foto = tk.PhotoImage(file=path)
        faktor = max(1, int(max(foto.width() / maks_w, foto.height() / maks_h)))
        return foto.subsample(faktor, faktor) if faktor > 1 else foto
    except Exception:
        return None


class LogoEmblem(tk.Canvas):
    """Logo persegi (emblem) di dalam kotak membulat. Memakai logo.png; bila tidak ada, ikon ikan."""

    def __init__(self, master, ukuran=44, radius=13, warna_kotak=None, latar=None):
        u = px(ukuran)
        super().__init__(master, width=fisik(u), height=fisik(u), bg=latar or _latar(master),
                         highlightthickness=0, bd=0)
        kotak = warna_kotak or "#FFFFFF"
        if PIL_OK:
            self._bg = gfx.kotak_bulat(u, u, px(radius), kotak)
            self.create_image(0, 0, anchor="nw", image=self._bg)
        else:
            self.create_polygon(titik_bulat(1, 1, u - 1, u - 1, px(radius)), smooth=True,
                                fill=kotak, outline=kotak)
        self._logo = muat_logo(ukuran - 12, ukuran - 12)
        if self._logo:
            self.create_image(u / 2, u / 2, image=self._logo)
        else:
            self._ik = gfx.ikon("ikan", int(ukuran * 0.56), C["primary"])
            if self._ik:
                self.create_image(u / 2, u / 2, image=self._ik)
            else:
                self.create_text(u / 2, u / 2, text="N", fill=C["primary"], font=f(14, True))


class Logo(tk.Canvas):
    """Logo NEXAFISH (kompatibel dengan versi lama): logo.png bila ada, selain itu logo vektor."""

    def __init__(self, master, skala=1.0, terang=False):
        s = skala
        bg_parent = _latar(master, C["side"])
        self._img_tk = muat_logo(int(210 * s), int(60 * s))
        if self._img_tk:
            super().__init__(master, width=fisik(self._img_tk.width()), height=fisik(self._img_tk.height()),
                             bg=bg_parent, highlightthickness=0, bd=0)
            self.create_image(0, 0, anchor="nw", image=self._img_tk)
            return

        def P(v):
            return px(v * s)

        super().__init__(master, width=fisik(P(220)), height=fisik(P(52)), bg=bg_parent,
                         highlightthickness=0, bd=0)
        if PIL_OK:
            self._bg = gfx.kotak_bulat(P(44), P(44), P(12), C["primary"])
            self.create_image(P(2), P(4), anchor="nw", image=self._bg)
            self._ik = gfx.ikon("ikan", int(26 * s), "#FFFFFF")
            if self._ik:
                self.create_image(P(24), P(26), image=self._ik)
        else:
            self.create_polygon(titik_bulat(P(2), P(4), P(44), P(46), P(10)), smooth=True,
                                fill=C["primary"], outline=C["primary"])
        warna_teks = "white" if bg_parent.lower() in (C["side"].lower(), C["side_secondary"].lower()) else C["text"]
        t = self.create_text(P(54), P(19), text="NEXA", anchor="w", fill=warna_teks,
                             font=f(max(9, int(15 * s)), True))
        x2 = self.bbox(t)[2]
        self.create_text(x2, P(19), text="FISH", anchor="w", fill=C["accent"],
                         font=f(max(9, int(15 * s)), True))
        self.create_text(P(54), P(38), text="FISH TECH ERP", anchor="w",
                         fill=C["accent"] if warna_teks == "white" else C["muted"],
                         font=f(max(7, int(8 * s)), True))


# ------------------------------------------------------------
#  Combo (pengganti ttk.Combobox)
# ------------------------------------------------------------
class Combo(tk.Frame):
    """Kotak pilihan membulat dengan daftar dropdown. API mirip ttk.Combobox:
    get(), set(), config(values=...), cget("values"), current(), dan event <<ComboboxSelected>>.

    editable=True -> teks boleh diketik bebas (mis. nama pelanggan / pemasok)."""

    MAKS_BARIS = 7

    def __init__(self, master, values=(), lebar=None, editable=False, placeholder="Pilih..."):
        super().__init__(master, bg=C["border"], takefocus=1)
        self._values = list(values)
        self.editable = editable
        self.placeholder = placeholder
        self._teks = ""
        self._popup = None
        self._id_klik_luar = None

        self.dalam = tk.Frame(self, bg="white")
        self.dalam.pack(fill="both", expand=True, padx=1, pady=1)

        self._chev = gfx.ikon("chevron", 16, C["muted"])
        if self._chev:
            self.panah = tk.Label(self.dalam, image=self._chev, bg="white", bd=0, cursor="hand2")
        else:
            self.panah = tk.Label(self.dalam, text="▾", bg="white", fg=C["muted"], font=fi(10), cursor="hand2")
        self.panah.pack(side="right", padx=(2, 12))

        if editable:
            self.isi = tk.Entry(self.dalam, relief="flat", bd=0, bg="white", fg=C["text"],
                                insertbackground=C["text"], font=f(10), highlightthickness=0,
                                width=lebar or 12)
            self.isi.bind("<FocusIn>", lambda e: self._garis(C["accent"]))
            self.isi.bind("<FocusOut>", lambda e: self._garis(C["border"]))
            self.isi.bind("<Down>", lambda e: self._buka())
        else:
            self.isi = tk.Label(self.dalam, text="", anchor="w", bg="white", fg=C["text"], font=f(10),
                                width=lebar or 12, cursor="hand2")
            self.isi.bind("<Button-1>", lambda e: self._toggle())
            self.bind("<FocusIn>", lambda e: self._garis(C["accent"]))
            self.bind("<FocusOut>", lambda e: self._garis(C["border"]) if not self._popup else None)
            self.bind("<Down>", lambda e: self._geser(1))
            self.bind("<Up>", lambda e: self._geser(-1))
            self.bind("<Return>", lambda e: self._buka())
            self.bind("<space>", lambda e: self._buka())
        self.isi.pack(side="left", fill="x", expand=True, padx=(13, 4), pady=8)
        self.panah.bind("<Button-1>", lambda e: self._toggle())
        self.dalam.bind("<Button-1>", lambda e: self._toggle())
        self._pojok = PojokBulat(self, 9, _latar(master), "white", C["border"])
        self.bind("<Destroy>", lambda e: self._tutup() if e.widget is self else None, add="+")
        self._tampil()

    # --- API mirip ttk.Combobox ---
    def get(self):
        return self.isi.get() if self.editable else self._teks

    def set(self, nilai):
        nilai = "" if nilai is None else str(nilai)
        if self.editable:
            self.isi.delete(0, "end")
            self.isi.insert(0, nilai)
        else:
            self._teks = nilai
            self._tampil()

    def current(self, indeks=None):
        if indeks is None:
            try:
                return self._values.index(self.get())
            except ValueError:
                return -1
        self.set(self._values[indeks])

    def configure(self, cnf=None, **kw):
        if isinstance(cnf, dict) and "values" in cnf:
            cnf = dict(cnf)
            self._values = list(cnf.pop("values"))
        if "values" in kw:
            self._values = list(kw.pop("values"))
        if cnf or kw:
            return super().configure(cnf, **kw)
        return None

    config = configure

    def cget(self, key):
        if key == "values":
            return tuple(self._values)
        return super().cget(key)

    __getitem__ = cget

    def fokus(self):
        (self.isi if self.editable else self).focus_set()

    # --- tampilan ---
    def _tampil(self):
        if self.editable:
            return
        if self._teks:
            self.isi.config(text=self._teks, fg=C["text"])
        else:
            self.isi.config(text=self.placeholder, fg=C["faint"])

    def _garis(self, warna):
        self.config(bg=warna)
        self._pojok.ganti(warna)

    def _geser(self, arah):
        if not self._values:
            return
        i = self.current()
        i = 0 if i < 0 else min(max(i + arah, 0), len(self._values) - 1)
        self.set(self._values[i])
        self.event_generate("<<ComboboxSelected>>")

    # --- dropdown ---
    def _toggle(self):
        if not self.editable:
            self.focus_set()
        if self._popup:
            self._tutup()
        else:
            self._buka()

    def _buka(self):
        if self._popup or not self._values:
            return
        self._garis(C["accent"])
        top = tk.Toplevel(self)
        top.withdraw()
        top.overrideredirect(True)
        top.configure(bg=C["border"])
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        isi = tk.Frame(top, bg="white")
        isi.pack(fill="both", expand=True, padx=1, pady=1)
        baris = min(len(self._values), self.MAKS_BARIS)
        lb = tk.Listbox(isi, height=baris, font=f(10), bd=0, highlightthickness=0, activestyle="none",
                        selectmode="browse", bg="white", fg=C["text"], exportselection=False,
                        selectbackground=C["select"], selectforeground=C["text"], relief="flat")
        for v in self._values:
            lb.insert("end", v)
        if len(self._values) > baris:
            sb = ttk.Scrollbar(isi, orient="vertical", command=lb.yview)
            lb.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        try:
            i = self._values.index(self.get())
            lb.selection_set(i)
            lb.see(i)
        except ValueError:
            pass
        lb.bind("<Motion>", lambda e: self._sorot(lb, e))
        lb.bind("<ButtonRelease-1>", lambda e: self._pilih(lb, e))
        lb.bind("<Return>", lambda e: self._pilih(lb, e))
        top.bind("<Escape>", lambda e: self._tutup())

        top.update_idletasks()
        lebar = max(self.winfo_width(), 120)
        tinggi = top.winfo_reqheight()
        x, y = self.winfo_rootx(), self.winfo_rooty() + self.winfo_height() + px(2)
        if y + tinggi > self.winfo_screenheight() - px(40):
            y = max(self.winfo_rooty() - tinggi - px(2), 0)
        top.geometry(f"{lebar}x{tinggi}+{x}+{y}")
        top.deiconify()
        top.lift()
        self._popup = top
        self._id_klik_luar = self.winfo_toplevel().bind("<Button-1>", self._klik_luar, add="+")

    def _sorot(self, lb, e):
        i = lb.nearest(e.y)
        lb.selection_clear(0, "end")
        lb.selection_set(i)

    def _pilih(self, lb, _e=None):
        sel = lb.curselection()
        if sel:
            self.set(self._values[sel[0]])
        self._tutup()
        self.event_generate("<<ComboboxSelected>>")

    def _klik_luar(self, e):
        if not self._popup:
            return
        jalur = str(e.widget)
        if jalur.startswith(str(self._popup)) or jalur.startswith(str(self)):
            return
        self._tutup()

    def _tutup(self):
        top, self._popup = self._popup, None
        if self._id_klik_luar:
            try:
                self.winfo_toplevel().unbind("<Button-1>", self._id_klik_luar)
            except tk.TclError:
                pass
            self._id_klik_luar = None
        if top is not None:
            try:
                top.destroy()
            except tk.TclError:
                pass
        try:
            self._garis(C["border"])
        except tk.TclError:
            pass


def buat_combo(parent, nilai, lebar=None, editable=False):
    """Kotak pilihan (dropdown) membulat. editable=True agar teks boleh diketik bebas."""
    return Combo(parent, values=nilai, lebar=lebar, editable=editable)


# ------------------------------------------------------------
#  Tabel adaptif
# ------------------------------------------------------------
def buat_tabel(parent, kolom, tinggi=10):
    """Tabel Treeview modern dalam kartu membulat.

    Lebar kolom otomatis menyesuaikan lebar layar dan isi (judul & data tidak terpotong); bila ruang
    benar-benar tidak cukup muncul scrollbar horizontal. Tinggi tabel mengikuti ruang yang tersedia."""
    frame = Kartu(parent, radius=12, isi_atas=C["head"])
    tree = ttk.Treeview(frame, columns=[k[0] for k in kolom], show="headings",
                        height=max(3, min(tinggi, 6)), style="Nexa.Treeview", selectmode="browse")

    for kid, judul, lebar, anc in kolom:
        tree.heading(kid, text=judul, anchor=anc)
        tree.column(kid, width=px(lebar), minwidth=px(40), anchor=anc, stretch=False)

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    sbx = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    keadaan = {"x": False}
    font_judul, font_data = tkfont.Font(font=f(9, True)), tkfont.Font(font=f(10))

    def xset(a, b):
        sbx.set(a, b)
        perlu = not (float(a) <= 0.0 and float(b) >= 1.0)
        if perlu and not keadaan["x"]:
            sbx.pack(side="bottom", fill="x", padx=(1, 1), before=tree)
            keadaan["x"] = True
        elif not perlu and keadaan["x"]:
            sbx.pack_forget()
            keadaan["x"] = False

    tree.configure(yscrollcommand=sb.set, xscrollcommand=xset)

    def lebar_minimum():
        """Lebar minimum tiap kolom: judul + isi terpanjang (maks. 420 px desain)."""
        hasil = [font_judul.measure(k[1]) + px(34) for k in kolom]
        for iid in tree.get_children()[:300]:
            nilai = tree.item(iid, "values")
            for i in range(min(len(nilai), len(kolom))):
                hasil[i] = max(hasil[i], min(font_data.measure(str(nilai[i])) + px(30), px(420)))
        return hasil

    def sesuaikan(_e=None):
        tersedia = tree.winfo_width() - px(4)
        if tersedia < px(80):
            return
        dasar = [px(k[2]) for k in kolom]
        total_dasar = sum(dasar)
        mins = lebar_minimum()
        lebar_kol = [max(int(d * tersedia / total_dasar), m) for d, m in zip(dasar, mins)]
        selisih = sum(lebar_kol) - tersedia
        if selisih > 0:  # terlalu lebar: kecilkan kolom yang masih punya ruang di atas minimumnya
            sisa = [w - m for w, m in zip(lebar_kol, mins)]
            total_sisa = sum(sisa)
            if total_sisa > 0:
                kurang = min(selisih, total_sisa)
                lebar_kol = [w - int(kurang * sl / total_sisa) for w, sl in zip(lebar_kol, sisa)]
        elif selisih < 0:  # ada ruang lebih: bagikan sesuai proporsi
            tambah = -selisih
            lebar_kol = [w + int(tambah * d / total_dasar) for w, d in zip(lebar_kol, dasar)]
        for (kid, *_r), w in zip(kolom, lebar_kol):
            tree.column(kid, width=w, stretch=False)

    tree.sesuaikan = sesuaikan
    tree.bind("<Configure>", sesuaikan)
    tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
    sb.pack(side="right", fill="y", padx=(0, 2), pady=6)

    tree.tag_configure("ganjil", background=C["zebra"])
    tree.tag_configure("genap", background="white")
    tree.tag_configure("judul", background="#EEF3FA", foreground=C["text"], font=f(10, True))
    tree.tag_configure("rendah", foreground=C["red"], font=f(10, True))
    tree.tag_configure("total", background="#E6EEFA", font=f(10, True), foreground=C["primary"])

    frame.angkat_sudut()
    return frame, tree


def isi_tabel(tree, baris, tag_fn=None):
    """Mengisi data ke Treeview dengan tagging genap/ganjil otomatis."""
    tree.delete(*tree.get_children())
    for i, b in enumerate(baris):
        iid, nilai = b if isinstance(b, tuple) and len(b) == 2 and isinstance(b[1], (list, tuple)) else (None, b)
        tag = ["genap" if i % 2 == 0 else "ganjil"]
        if tag_fn:
            ekstra = tag_fn(nilai)
            if ekstra:
                tag = [ekstra]
        if iid is not None:
            tree.insert("", "end", iid=str(iid), values=nilai, tags=tag)
        else:
            tree.insert("", "end", values=nilai, tags=tag)
    sesuaikan = getattr(tree, "sesuaikan", None)
    if sesuaikan:
        tree.after_idle(sesuaikan)


# ------------------------------------------------------------
#  Area gulir & tab modern
# ------------------------------------------------------------
class AreaGulir(tk.Frame):
    """Area konten yang otomatis bisa digulir bila isinya lebih tinggi dari jendela.

    Bila ruang cukup, isi dibentangkan memenuhi area (tabel ikut melebar). Letakkan halaman di `.isi`."""

    def __init__(self, master, bg=None):
        bg = bg or _latar(master)
        super().__init__(master, bg=bg)
        self.kanvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=fisik(px(40)))
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.kanvas.yview)
        self.kanvas.configure(yscrollcommand=self.sb.set)
        self.kanvas.pack(side="left", fill="both", expand=True)
        self.isi = tk.Frame(self.kanvas, bg=bg)
        self._jendela = self.kanvas.create_window((0, 0), window=self.isi, anchor="nw")
        self._sb_tampil = False
        self._tertunda = None
        self.kanvas.bind("<Configure>", self._jadwal)
        self.isi.bind("<Configure>", self._jadwal)
        self.bind_all("<MouseWheel>", self._roda, add="+")
        self.bind_all("<Button-4>", lambda e: self._roda(e, 1), add="+")
        self.bind_all("<Button-5>", lambda e: self._roda(e, -1), add="+")

    def reset(self):
        self.kanvas.yview_moveto(0)

    def _jadwal(self, _e=None):
        if self._tertunda is None:
            self._tertunda = self.after_idle(self._ukuran)

    def _ukuran(self):
        self._tertunda = None
        try:
            w, h = self.kanvas.winfo_width(), self.kanvas.winfo_height()
            if w < 10 or h < 10:
                return
            butuh = self.isi.winfo_reqheight()
            tinggi = max(h, butuh)
            self.kanvas.itemconfigure(self._jendela, width=fisik(w), height=fisik(tinggi))
            self.kanvas.configure(scrollregion=(0, 0, w, tinggi))
            perlu = butuh > h + 1
            if perlu and not self._sb_tampil:
                self.sb.pack(side="right", fill="y", padx=(6, 0))
                self._sb_tampil = True
            elif not perlu and self._sb_tampil:
                self.sb.pack_forget()
                self._sb_tampil = False
                self.kanvas.yview_moveto(0)
        except tk.TclError:
            pass

    def _roda(self, e, arah=None):
        try:
            if not self.winfo_exists() or not self._sb_tampil:
                return
            w = e.widget
            if not isinstance(w, tk.Misc):
                return
            if w.winfo_class() in ("Treeview", "Listbox", "Text"):
                return  # widget ini menggulir dirinya sendiri
            p = w
            while p is not None and p is not self:
                p = p.master
            if p is None:
                return
            if arah is None:
                arah = 1 if e.delta > 0 else -1
            self.kanvas.yview_scroll(-arah, "units")
        except tk.TclError:
            pass


class _PilTab(tk.Canvas):
    """Satu tombol tab berbentuk kapsul."""

    def __init__(self, master, teks, command):
        self.fnt = f(9, True)
        self.teks, self.command = teks, command
        self.aktif = self.hover = False
        self._img = None
        self.lebar = _ukur(teks, self.fnt) + px(38)
        self.tinggi = px(38)
        super().__init__(master, width=fisik(self.lebar), height=fisik(self.tinggi), bg=_latar(master),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.bind("<Enter>", lambda e: self._set(hover=True))
        self.bind("<Leave>", lambda e: self._set(hover=False))
        self.bind("<Button-1>", lambda e: self.command())
        self._gambar()

    def _set(self, hover=None, aktif=None):
        if hover is not None:
            self.hover = hover
        if aktif is not None:
            self.aktif = aktif
        self._gambar()

    def _gambar(self):
        self.delete("all")
        if self.aktif:
            isi, garis, fg = C["primary"], None, "white"
        elif self.hover:
            isi, garis, fg = "#EEF3FA", C["border"], C["text"]
        else:
            isi, garis, fg = "white", C["border"], C["muted"]
        w, h = self.lebar, self.tinggi
        if PIL_OK:
            self._img = gfx.kotak_bulat(w, h, h // 2, isi, garis, px(1))
            self.create_image(0, 0, anchor="nw", image=self._img)
        else:
            self.create_polygon(titik_bulat(1, 1, w - 1, h - 1, h // 2), smooth=True, fill=isi,
                                outline=garis or isi)
        self.create_text(w / 2, h / 2, text=self.teks, fill=fg, font=self.fnt)


class TabModern(tk.Frame):
    """Pengganti ttk.Notebook: tombol tab berbentuk kapsul yang otomatis turun baris bila layar sempit.

    Pemakaian sama: t = tk.Frame(tab, bg=...); tab.add(t, text="Judul")."""

    def __init__(self, master, **_kw):
        latar = _latar(master)
        super().__init__(master, bg=latar)
        self.bar = tk.Frame(self, bg=latar)
        self.bar.pack(fill="x", pady=(0, 4))
        self.konten = tk.Frame(self, bg=latar)
        self.konten.pack(fill="both", expand=True)
        self._tab = []
        self._aktif = None
        self._susunan = None
        self.bar.bind("<Configure>", self._atur)

    def add(self, frame, text="", **_kw):
        pil = _PilTab(self.bar, text.strip(), lambda fr=frame: self.select(fr))
        self._tab.append((frame, pil))
        if self._aktif is None:
            self.select(frame)
        self._susunan = None
        self._atur()

    def select(self, frame=None):
        if frame is None:
            return self._aktif
        for fr, pil in self._tab:
            if fr is frame:
                fr.pack(in_=self.konten, fill="both", expand=True)
                pil._set(aktif=True)
            else:
                fr.pack_forget()
                pil._set(aktif=False)
        self._aktif = frame

    def _atur(self, _e=None):
        lebar = self.bar.winfo_width()
        if lebar < 20 or not self._tab:
            return
        jarak = px(8)
        susunan, x, baris, kolom = [], 0, 0, 0
        for _fr, pil in self._tab:
            w = pil.lebar
            if x + w > lebar and x > 0:
                baris, kolom, x = baris + 1, 0, 0
            susunan.append((baris, kolom))
            x += w + jarak
            kolom += 1
        if susunan == self._susunan:
            return
        self._susunan = susunan
        for (_fr, pil), (r, c) in zip(self._tab, susunan):
            pil.grid(row=r, column=c, padx=(0, 8), pady=(0, 8), sticky="w")


# ------------------------------------------------------------
#  Dialog formulir generik
# ------------------------------------------------------------
class Dialog(tk.Toplevel):
    """Dialog formulir modal untuk input data."""

    def __init__(self, master, judul, fields, on_submit, tombol="Simpan", info=None, lebar=420):
        super().__init__(master)
        self.title(judul)
        self.configure(bg=C["border"])
        self.resizable(False, False)
        self.on_submit = on_submit
        self.kontrol = {}

        dalam = tk.Frame(self, bg="white")
        dalam.pack(fill="both", expand=True, padx=1, pady=1)

        wrap = tk.Frame(dalam, bg="white")
        wrap.pack(fill="both", expand=True, padx=30, pady=26)

        tk.Frame(wrap, bg="white", width=lebar, height=1).pack()
        tk.Label(wrap, text=judul, font=f(15, True), bg="white", fg=C["text"]).pack(anchor="w")

        if info:
            tk.Label(wrap, text=info, font=f(9), bg="white", fg=C["muted"],
                     wraplength=lebar, justify="left").pack(anchor="w", pady=(4, 6))

        tk.Frame(wrap, bg=C["border"], height=1).pack(fill="x", pady=(12, 4))

        pertama = None
        for kunci, label, jenis, opsi, default in fields:
            tk.Label(wrap, text=label, font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(12, 4))
            if jenis == "combo":
                w = buat_combo(wrap, opsi)
                w.set(default if default else (opsi[0] if opsi else ""))
                w.pack(fill="x", ipady=3)
            else:
                w = Isian(wrap, numeric=jenis == "number")
                if default not in (None, ""):
                    w.set(str(default))
                w.pack(fill="x")
                pertama = pertama or w
            self.kontrol[kunci] = w

        self.pesan = tk.Label(wrap, text="", fg=C["red"], bg="white", font=f(9),
                              wraplength=lebar, justify="left")
        self.pesan.pack(anchor="w", pady=(14, 0))

        baris = tk.Frame(wrap, bg="white")
        baris.pack(fill="x", pady=(10, 0))
        Tombol(baris, tombol, self.kirim, warna=C["primary"]).pack(side="right")
        Tombol(baris, "Batal", self.destroy, gaya="outline").pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self.kirim())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()

        induk = master.winfo_toplevel()
        x = induk.winfo_rootx() + (induk.winfo_width() - self.winfo_reqwidth()) // 2
        y = induk.winfo_rooty() + (induk.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.transient(induk)
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        if pertama:
            pertama.fokus()

    def kirim(self):
        nilai = {k: w.get().strip() for k, w in self.kontrol.items()}
        try:
            self.on_submit(nilai)
        except ValueError as e:
            self.pesan.config(text=str(e))
            return
        except sqlite3.Error as e:
            self.pesan.config(text=f"Kesalahan database: {e}")
            return
        self.destroy()
