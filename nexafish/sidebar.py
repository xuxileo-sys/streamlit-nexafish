"""Sidebar NEXAFISH: navy, menu berkelompok dengan ikon garis, kartu pengguna, dan tombol keluar."""

import tkinter as tk

try:
    import gfx
    from theme import C, LOGO_MODE, f, fi, fisik, px, titik_bulat
    from widgets import Chip, LogoEmblem, muat_logo, _latar
except ImportError:
    from ui import gfx
    from ui.theme import C, LOGO_MODE, f, fi, fisik, px, titik_bulat
    from ui.widgets import Chip, LogoEmblem, muat_logo, _latar

# Ikon garis per menu (nama ikon ada di gfx.py) dan simbol cadangan bila Pillow tidak terpasang
IKON = {
    "Dashboard": "dashboard",
    "Stok & Produk": "stok",
    "Kategori Ukuran": "kategori",
    "Kasir": "kasir",
    "Jurnal Umum": "jurnal",
    "Buku Besar": "buku",
    "Laporan Keuangan": "laporan",
    "Histori Aktivitas": "histori",
    "Operasional": "operasional",
    "Transaksi": "operasional",
    "Pengaturan": "pengaturan",
}
SIMBOL = {
    "Dashboard": "⊞", "Stok & Produk": "▥", "Kategori Ukuran": "◈", "Kasir": "⊙",
    "Jurnal Umum": "☰", "Buku Besar": "▤", "Laporan Keuangan": "▧", "Histori Aktivitas": "↻",
    "Operasional": "⇄", "Transaksi": "⇄", "Pengaturan": "⚙",
}

# Pengelompokan menu pada sidebar (hanya pengelompokan tampilan; urutan tetap mengikuti app.py)
GRUP = {
    "Dashboard": "NAVIGASI UTAMA", "Stok & Produk": "NAVIGASI UTAMA",
    "Kategori Ukuran": "NAVIGASI UTAMA", "Kasir": "NAVIGASI UTAMA", "Transaksi": "NAVIGASI UTAMA",
    "Jurnal Umum": "KEUANGAN & AKUNTANSI", "Buku Besar": "KEUANGAN & AKUNTANSI",
    "Laporan Keuangan": "KEUANGAN & AKUNTANSI",
    "Histori Aktivitas": "SISTEM & KONTROL", "Operasional": "SISTEM & KONTROL",
    "Pengaturan": "SISTEM & KONTROL",
}

WARNA_IKON_BIASA = "#8FA6C9"
WARNA_IKON_AKTIF = "#FFFFFF"


class NavItem(tk.Canvas):
    """Satu baris menu: kapsul membulat, ikon garis, bilah aksen saat aktif, efek hover."""

    TINGGI = 44

    def __init__(self, master, teks, command):
        super().__init__(master, width=10, height=self.TINGGI, bg=C["side"], highlightthickness=0,
                         bd=0, cursor="hand2")
        self.teks = teks
        self.nama_ikon = IKON.get(teks)
        self.aktif = False
        self.hover = False
        self.command = command
        self._imgs = []
        self._ik_biasa = gfx.ikon(self.nama_ikon, 20, WARNA_IKON_BIASA) if self.nama_ikon else None
        self._ik_aktif = gfx.ikon(self.nama_ikon, 20, WARNA_IKON_AKTIF) if self.nama_ikon else None

        self.bind("<Configure>", lambda e: self._gambar())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self.command())

    def _set_hover(self, nilai):
        self.hover = nilai
        self._gambar()

    def set_aktif(self, aktif):
        self.aktif = aktif
        self._gambar()

    def _gambar(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10:
            return
        self.delete("all")
        self._imgs = []

        if self.aktif:
            bg, fg, ik = C["side_active"], "white", self._ik_aktif
        elif self.hover:
            bg, fg, ik = C["side_hover"], "white", self._ik_aktif
        else:
            bg, fg, ik = None, C["side_text"], self._ik_biasa

        m = px(2)
        if bg:
            if gfx.PIL_OK:
                im = gfx.kotak_bulat(w - 2 * m, h - 2 * m, px(12), bg)
                self._imgs.append(im)
                self.create_image(m, m, anchor="nw", image=im)
            else:
                self.create_polygon(titik_bulat(m, m, w - m, h - m, px(10)), smooth=True, fill=bg, outline=bg)

        if self.aktif:
            if gfx.PIL_OK:
                bar = gfx.kotak_bulat(px(4), h - px(20), px(2), C["accent"])
                self._imgs.append(bar)
                self.create_image(0, px(10), anchor="nw", image=bar)
            else:
                self.create_rectangle(0, px(10), px(4), h - px(10), fill=C["accent"], outline=C["accent"])

        if ik:
            self._imgs.append(ik)
            self.create_image(px(28), h / 2, image=ik)
        else:
            self.create_text(px(28), h / 2, text=SIMBOL.get(self.teks, "•"),
                             fill=WARNA_IKON_AKTIF if self.aktif else WARNA_IKON_BIASA, font=fi(13))
        self.create_text(px(50), h / 2, text=self.teks, fill=fg, font=f(10, self.aktif), anchor="w")


class TombolIkon(tk.Canvas):
    """Tombol ikon kecil (mis. keluar) dengan efek hover."""

    def __init__(self, master, nama, command, ukuran=36, warna="#9DB2D4", warna_hover="#FFFFFF",
                 latar_hover=None, latar=None):
        super().__init__(master, width=ukuran, height=ukuran, bg=latar or _latar(master),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.u, self.command = px(ukuran), command
        self.latar_hover = latar_hover or C["side_active"]
        self._ik = gfx.ikon(nama, 18, warna)
        self._ik_h = gfx.ikon(nama, 18, warna_hover)
        self._imgs = []
        self._gambar(False)
        self.bind("<Enter>", lambda e: self._gambar(True))
        self.bind("<Leave>", lambda e: self._gambar(False))
        self.bind("<Button-1>", lambda e: self.command())

    def _gambar(self, hover):
        self.delete("all")
        self._imgs = []
        u = self.u
        if hover:
            if gfx.PIL_OK:
                im = gfx.kotak_bulat(u, u, px(11), self.latar_hover)
                self._imgs.append(im)
                self.create_image(0, 0, anchor="nw", image=im)
            else:
                self.create_polygon(titik_bulat(1, 1, u - 1, u - 1, px(9)), smooth=True,
                                    fill=self.latar_hover, outline=self.latar_hover)
        ik = self._ik_h if hover else self._ik
        if ik:
            self._imgs.append(ik)
            self.create_image(u / 2, u / 2, image=ik)
        else:
            self.create_text(u / 2, u / 2, text="⏻", fill="#9DB2D4", font=fi(12))


class Sidebar(tk.Frame):
    """Sidebar navy NEXAFISH."""

    LEBAR = 264

    def __init__(self, master, user, menu, on_buka, on_keluar):
        super().__init__(master, bg=C["side"], width=self.LEBAR)
        self.pack_propagate(False)

        # Merek: emblem logo + nama aplikasi
        merek = tk.Frame(self, bg=C["side"])
        merek.pack(fill="x", padx=20, pady=(20, 10))
        if LOGO_MODE == "wordmark":
            self._logo = muat_logo(self.LEBAR - 56, 56)
            if self._logo:
                tk.Label(merek, image=self._logo, bg=C["side"], bd=0).pack(anchor="w")
            else:
                self._merek_ikon(merek)
        else:
            self._merek_ikon(merek)

        # Kartu pengguna + tombol keluar
        bawah = tk.Frame(self, bg=C["side"])
        bawah.pack(side="bottom", fill="x", padx=14, pady=(8, 14))
        tk.Frame(bawah, bg=C["side_line"], height=1).pack(fill="x", pady=(0, 12))

        baris = tk.Frame(bawah, bg=C["side"])
        baris.pack(fill="x")

        av = px(40)
        avatar = tk.Canvas(baris, width=fisik(av), height=fisik(av), bg=C["side"], highlightthickness=0)
        avatar.pack(side="left")
        if gfx.PIL_OK:
            self._av = gfx.kotak_bulat(av, av, av // 2, C["side_active"], "#35609C", px(1))
            avatar.create_image(0, 0, anchor="nw", image=self._av)
        else:
            avatar.create_oval(1, 1, av - 1, av - 1, fill=C["side_active"], outline="#35609C")
        inisial = (user["nama"] or "U")[0].upper()
        avatar.create_text(av / 2, av / 2, text=inisial, fill="white", font=f(13, True))

        info = tk.Frame(baris, bg=C["side"])
        info.pack(side="left", fill="x", expand=True, padx=(10, 4))
        tk.Label(info, text=user["nama"], font=f(10, True), bg=C["side"], fg="white",
                 anchor="w").pack(fill="x")
        if user["jabatan"] == "Owner":
            Chip(info, user["jabatan"].upper(), fg=C["green_text"], bg=C["green_soft"], ukuran=7,
                 tinggi=18, padx=8).pack(anchor="w", pady=(3, 0))
        else:
            Chip(info, user["jabatan"].upper(), fg=C["primary"], bg="#E8F0FE", ukuran=7,
                 tinggi=18, padx=8).pack(anchor="w", pady=(3, 0))

        TombolIkon(baris, "keluar", on_keluar).pack(side="right")
        self._tinggi_item = NavItem.TINGGI
        self.bind("<Configure>", self._sesuaikan_tinggi)

        # Menu berkelompok
        area = tk.Frame(self, bg=C["side"])
        area.pack(fill="x", padx=12)
        self.nav = {}
        grup_terakhir = None
        for nama in menu:
            grup = GRUP.get(nama, "MENU")
            if grup != grup_terakhir:
                tk.Label(area, text=grup, font=f(8, True), bg=C["side"], fg=C["side_muted"],
                         anchor="w").pack(fill="x", padx=10, pady=(12 if grup_terakhir else 4, 4))
                grup_terakhir = grup
            item = NavItem(area, nama, lambda n=nama: on_buka(n))
            item.pack(fill="x", pady=1)
            self.nav[nama] = item

    def _merek_ikon(self, induk):
        baris = tk.Frame(induk, bg=C["side"])
        baris.pack(anchor="w")
        LogoEmblem(baris, ukuran=46, radius=14, latar=C["side"]).pack(side="left")
        teks = tk.Frame(baris, bg=C["side"])
        teks.pack(side="left", padx=(12, 0))
        tk.Label(teks, text="NEXAFISH", font=f(14, True), bg=C["side"], fg="white", anchor="w").pack(anchor="w")
        tk.Label(teks, text="FISH TECH ERP", font=f(7, True), bg=C["side"], fg=C["side_muted"],
                 anchor="w").pack(anchor="w", pady=(1, 0))

    def _sesuaikan_tinggi(self, e):
        """Menu dipadatkan otomatis pada jendela yang pendek agar kartu pengguna tetap terlihat."""
        tinggi = e.height / max(px(100) / 100.0, 1.0)  # tinggi dalam satuan desain
        t = 44 if tinggi >= 800 else 40 if tinggi >= 720 else 36
        if t != self._tinggi_item:
            self._tinggi_item = t
            for item in self.nav.values():
                item.configure(height=t)

    def set_aktif(self, nama):
        for n, item in self.nav.items():
            item.set_aktif(n == nama)
