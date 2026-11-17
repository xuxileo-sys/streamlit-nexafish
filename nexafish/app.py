"""Modul utama aplikasi NEXAFISH ERP (LoginScreen, MainFrame, dan App).

Redesain tampilan saja: alur login, validasi, menu per jabatan, dan pemanggilan database tidak berubah.
"""

import os
import tkinter as tk
from tkinter import messagebox

import gfx
from database import Database
from sidebar import Sidebar
from theme import C, aktifkan_dpi, atur_gaya, atur_skala, f, fisik, mix, px, titik_segienam
from utils import tanggal_indonesia
from widgets import AreaGulir, Chip, Isian, Kartu, Tombol, buat_combo, cari_logo, muat_logo
from pages import (
    BukuBesarPage,
    DashboardPage,
    KasKecilPage,
    HistoriPage,
    JurnalPage,
    KasirPage,
    KategoriPage,
    LaporanPage,
    OperasionalPage,
    PengaturanPage,
    StokPage,
)


class LoginScreen(tk.Frame):
    """Layar login: panel merek navy di kiri, formulir di kartu putih membulat di kanan."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["bg"])
        self.app = app
        self.db = app.db
        self.percobaan = 0
        self.kunci = 0
        self._job = None
        self._job_kunci = None
        self._imgs = []

        self.columnconfigure(0, weight=5, uniform="login")
        self.columnconfigure(1, weight=6, uniform="login")
        self.rowconfigure(0, weight=1)

        self.kiri = tk.Canvas(self, width=10, bg=C["side"], highlightthickness=0, bd=0)
        self.kiri.grid(row=0, column=0, sticky="nsew")
        self.kiri.bind("<Configure>", self._ubah_ukuran)
        self._logo = muat_logo(58, 58)

        self.kanan = tk.Frame(self, bg=C["bg"])
        self.kanan.grid(row=0, column=1, sticky="nsew")
        self.card = Kartu(self.kanan, radius=18)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self._bangun_kartu()

    def destroy(self):
        for j in (self._job, self._job_kunci):
            if j:
                try:
                    self.after_cancel(j)
                except tk.TclError:
                    pass
        super().destroy()

    def _bangun_kartu(self):
        p = tk.Frame(self.card, bg="white")
        p.pack(padx=44, pady=40)
        tk.Frame(p, bg="white", width=360, height=1).pack()

        tk.Label(p, text="Selamat Datang", font=f(22, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(p, text="Masuk ke sistem NEXAFISH untuk melanjutkan.", font=f(10), bg="white",
                 fg=C["muted"]).pack(anchor="w", pady=(4, 22))

        # Hak akses / jabatan
        tk.Label(p, text="Hak Akses / Jabatan", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(0, 6))
        self.combo = buat_combo(p, ["Owner", "Karyawan"])
        self.combo.set("Pilih Jabatan Anda")
        self.combo.pack(fill="x", ipady=4)
        self.combo.bind("<<ComboboxSelected>>", self.ubah_form_jabatan)

        # Nama
        self.lbl_nama = tk.Label(p, text="Nama Lengkap", font=f(9, True), bg="white", fg=C["text"])
        self.lbl_nama.pack(anchor="w", pady=(16, 6))
        self.nama = Isian(p, placeholder="Masukkan Nama Lengkap")
        self.nama.pack(fill="x")

        # Password
        tk.Label(p, text="Password Akun", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(16, 6))
        self.sandi = Isian(p, password=True)
        self.sandi.pack(fill="x")

        # Pesan validasi
        self.pesan = tk.Label(p, text="", font=f(9), bg="white", fg=C["red"], wraplength=360, justify="left")
        self.pesan.pack(anchor="w", pady=(10, 0))

        Tombol(p, "Masuk ke Sistem", self.masuk, tinggi=46, ukuran=11, radius=12,
               warna=C["primary"]).pack(fill="x", pady=(14, 0))

        for w in (self.nama.entry, self.sandi.entry, self.combo):
            w.bind("<Return>", lambda e: self.masuk())

    def ubah_form_jabatan(self, _e=None):
        jabatan = self.combo.get()
        self.nama.entry.configure(state="normal")
        if jabatan == "Owner":
            self.lbl_nama.config(text="Nama Akun")
            self.nama.set("Owner")
            self.nama.entry.configure(state="disabled")
        else:
            self.lbl_nama.config(text="Nama Lengkap")
            self.nama.clear()

    # --- panel merek (kiri) ---
    def _ubah_ukuran(self, _e):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(30, self._gambar)

    def _gambar(self):
        c = self.kiri
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        c.delete("all")
        self._imgs = []

        # Latar gradasi navy
        awal, akhir = "#0C1F3E", "#1C4079"
        for x in range(0, w, 8):
            warna = mix(awal, akhir, x / w)
            c.create_rectangle(x, 0, x + 8, h, fill=warna, outline=warna)

        # Ornamen garis lengkung
        for pts, warna in [
            ([w * .03, 0, w * .10, h * .35, w * .18, h * .70, w * .20, h], "#18386A"),
            ([w * .12, 0, w * .22, h * .30, w * .28, h * .65, w * .32, h], "#1F4682"),
            ([w * .96, 0, w * .90, h * .40, w * .84, h * .75, w * .88, h], "#18386A"),
        ]:
            c.create_line(*pts, smooth=True, fill=warna, width=px(2))

        # Segi enam halus
        m = min(w, h)
        for fx, fy, fr, col in [
            (.86, .14, .10, "#17386B"), (.92, .30, .05, "#21487F"), (.80, .26, .04, "#1D4276"),
            (.10, .90, .12, "#17386B"), (.26, .94, .06, "#1D4276"), (.90, .88, .09, "#21487F"),
        ]:
            c.create_polygon(titik_segienam(w * fx, h * fy, m * fr, 8), fill=col, outline=col)

        # Merek
        x0 = max(w * 0.12, px(44))
        y0 = h * 0.36
        tile_u = px(86)
        if gfx.PIL_OK:
            tile = gfx.kotak_bulat(tile_u, tile_u, px(26), "#FFFFFF")
            self._imgs.append(tile)
            c.create_image(x0, y0, anchor="nw", image=tile)
        else:
            c.create_rectangle(x0, y0, x0 + tile_u, y0 + tile_u, fill="#FFFFFF", outline="#FFFFFF")
        if self._logo:
            c.create_image(x0 + tile_u / 2, y0 + tile_u / 2, image=self._logo)
        else:
            ik = gfx.ikon("ikan", 48, C["primary"])
            if ik:
                self._imgs.append(ik)
                c.create_image(x0 + tile_u / 2, y0 + tile_u / 2, image=ik)
        c.create_text(x0, y0 + px(118), text="NEXAFISH", anchor="nw", fill="white", font=f(34, True))
        c.create_text(x0, y0 + px(172), text="Sistem Informasi Akuntansi & Operasional Ikan Bawal",
                      anchor="nw", fill="#A9BBD8", font=f(12), width=fisik(max(w * 0.7, px(240))))

    def tampil_pesan(self, teks, warna=None):
        self.pesan.config(text=teks, fg=warna or C["red"])

    def masuk(self):
        if self.kunci > 0:
            return
        nama = self.nama.get().strip()
        jabatan = self.combo.get()
        if jabatan == "Owner":
            nama = "Owner"
        sandi = self.sandi.get()
        if not nama:
            return self.tampil_pesan("Nama lengkap wajib diisi.")
        if jabatan not in ("Owner", "Karyawan"):
            return self.tampil_pesan("Pilih jabatan Anda terlebih dahulu.")
        if not sandi:
            return self.tampil_pesan("Password wajib diisi.")
        if self.db.verifikasi_login(jabatan, sandi):
            if jabatan == "Owner":
                nama_owner = self.db.validasi_nama_owner(nama)
                if not nama_owner:
                    terdaftar = self.db.nama_owner()
                    self.db.catat_histori(nama, jabatan, "Percobaan login GAGAL (nama Owner tidak cocok)")
                    return self.tampil_pesan(
                        f"Akun Owner hanya terdaftar untuk {terdaftar}. Gunakan nama tersebut.")
                nama = nama_owner
            self.app.user = {"nama": nama, "jabatan": jabatan}
            self.db.catat_histori(nama, jabatan, f"Login berhasil sebagai {jabatan}")
            self.app.tampil_utama()
            return
        self.percobaan += 1
        self.db.catat_histori(nama, jabatan, "Percobaan login GAGAL (password salah)")
        if self.percobaan >= 3:
            self.percobaan = 0
            self.kunci = 15
            self._hitung_mundur()
        else:
            self.tampil_pesan(f"Password salah untuk jabatan {jabatan}. "
                              f"Sisa percobaan: {3 - self.percobaan}")

    def _hitung_mundur(self):
        if self.kunci > 0:
            self.tampil_pesan(f"Terlalu banyak percobaan gagal. Coba lagi dalam {self.kunci} detik.")
            self.kunci -= 1
            self._job_kunci = self.after(1000, self._hitung_mundur)
        else:
            self.tampil_pesan("Silakan coba login kembali.", C["muted"])


class MainFrame(tk.Frame):
    """Kerangka utama: sidebar kiri, topbar putih, dan area konten."""

    DESKRIPSI = {
        "Dashboard": "Ringkasan metrik keuangan, arus kas, dan analisis operasional.",
        "Kas & Kas Kecil": "Pencatatan penerimaan, pengeluaran, dana kas kecil, dan riwayat kas.",
        "Stok & Produk": "Manajemen katalog ikan bawal, kontrol kuantitas stok, dan harga.",
        "Kategori Ukuran": "Pengelompokan klasifikasi ukuran ikan bawal.",
        "Kasir": "Point of Sales terintegrasi double-entry bookkeeping otomatis.",
        "Jurnal Umum": "Pencatatan transaksi akuntansi debit-kredit terinci.",
        "Buku Besar": "Riwayat mutasi dan saldo akun akuntansi.",
        "Laporan Keuangan": "Laporan laba rugi, neraca, arus kas, dan neraca lajur.",
        "Histori Aktivitas": "Audit trail jejak aktivitas pengguna sistem.",
        "Operasional": "Transaksi pembelian, pelanggan, pemasok, dan kas kecil.",
        "Transaksi": "Pencatatan pembelian dan operasional kas.",
        "Pengaturan": "Konfigurasi keamanan akun, kata sandi, dan backup database.",
    }

    def __init__(self, master, app):
        super().__init__(master, bg=C["bg"])
        self.app, self.db, self.user = app, app.db, app.user
        owner = self.user["jabatan"] == "Owner"
        if owner:
            self.menu = [
                ("Dashboard", DashboardPage),
                ("Stok & Produk", StokPage),
                ("Kategori Ukuran", KategoriPage),
                ("Kasir", KasirPage),
                ("Kas & Kas Kecil", KasKecilPage),
                ("Jurnal Umum", JurnalPage),
                ("Buku Besar", BukuBesarPage),
                ("Laporan Keuangan", LaporanPage),
                ("Histori Aktivitas", HistoriPage),
                ("Operasional", OperasionalPage),
                ("Pengaturan", PengaturanPage),
            ]
        else:
            self.menu = [
                ("Kasir", KasirPage),
                ("Kas & Kas Kecil", KasKecilPage),
                ("Pengaturan", PengaturanPage),
            ]

        # Sidebar kiri
        self.sidebar = Sidebar(self, self.user, [nama for nama, _k in self.menu], self.buka, self.keluar)
        self.sidebar.pack(side="left", fill="y")

        kanan = tk.Frame(self, bg=C["bg"])
        kanan.pack(side="left", fill="both", expand=True)

        # Topbar
        self.header = tk.Frame(kanan, bg=C["header"], height=90)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        tk.Frame(kanan, bg=C["border"], height=1).pack(fill="x")

        header_isi = tk.Frame(self.header, bg=C["header"])
        header_isi.pack(fill="both", expand=True, padx=28)

        kiri_header = tk.Frame(header_isi, bg=C["header"])
        kiri_header.pack(side="left", fill="y", pady=12)
        self.judul = tk.Label(kiri_header, text="", font=f(17, True), bg=C["header"], fg=C["text"])
        self.judul.pack(anchor="w")
        self.subjudul = tk.Label(kiri_header, text="Enterprise Resource Planning & Accounting",
                                 font=f(9), bg=C["header"], fg=C["muted"])
        self.subjudul.pack(anchor="w", pady=(2, 0))

        kanan_header = tk.Frame(header_isi, bg=C["header"])
        kanan_header.pack(side="right", fill="y")
        isi_kanan = tk.Frame(kanan_header, bg=C["header"])
        isi_kanan.pack(expand=True)

        if owner:
            Chip(isi_kanan, self.user["jabatan"].upper(), fg=C["green_text"], bg=C["green_soft"],
                 ukuran=8, tinggi=34, padx=14).pack(side="right", padx=(12, 0))
        else:
            Chip(isi_kanan, self.user["jabatan"].upper(), fg=C["primary"], bg="#E8F0FE",
                 ukuran=8, tinggi=34, padx=14).pack(side="right", padx=(12, 0))
        Chip(isi_kanan, tanggal_indonesia(), fg=C["text"], bg="#F4F7FB", garis=C["border"], ukuran=9,
             tebal=False, ikon="kalender", tinggi=38, padx=14).pack(side="right")

        # Area konten
        self.gulir = AreaGulir(kanan, bg=C["bg"])
        self.gulir.pack(fill="both", expand=True, padx=(28, 14), pady=(24, 0))
        self.isi = self.gulir.isi
        self.halaman = None
        self.buka("Dashboard" if owner else "Kasir")

    def buka(self, nama):
        if self.halaman is not None:
            self.halaman.destroy()
        kelas = dict(self.menu)[nama]
        self.halaman = kelas(self.isi, self)
        self.halaman.pack(fill="both", expand=True, pady=(0, 24))
        self.gulir.reset()

        self.judul.config(text=nama)
        self.subjudul.config(text=self.DESKRIPSI.get(nama, "NEXAFISH Enterprise Fish Tech ERP"))
        self.sidebar.set_aktif(nama)

    def keluar(self):
        if messagebox.askyesno("Konfirmasi Keluar", "Apakah Anda yakin ingin keluar dari sistem?", parent=self):
            self.db.catat_histori(self.user["nama"], self.user["jabatan"], "Logout")
            self.app.tampil_login()


class App(tk.Tk):
    """Jendela utama aplikasi NEXAFISH ERP."""

    def __init__(self):
        aktifkan_dpi()  # harus sebelum jendela Tk dibuat: teks tajam di layar resolusi tinggi
        super().__init__()
        atur_skala(self)  # hitung skala layar & pasang penskala ukuran
        self.title("NEXAFISH Enterprise — Sistem Akuntansi & Manajemen Ikan Bawal")
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        # Ukuran mengikuti layar (maks. ukuran desain), tidak pernah melebihi layar
        lebar = min(px(1360), int(sw * 0.94))
        tinggi = min(px(840), int(sh * 0.88))
        self.minsize(min(px(960), sw - 40), min(px(620), sh - 80))
        x = max((sw - lebar) // 2, 0)
        y = max((sh - tinggi) // 2 - px(20), 0)
        self.geometry(f"{lebar}x{tinggi}+{x}+{y}")
        self.configure(bg=C["bg"])
        self.db = Database()
        self.user = None
        atur_gaya(self)
        self.protocol("WM_DELETE_WINDOW", self.tutup)

        # Ikon jendela dari logo.png bila tersedia
        path_logo = cari_logo()
        if path_logo:
            try:
                self._ikon_jendela = tk.PhotoImage(file=path_logo)
                self.iconphoto(False, self._ikon_jendela)
            except Exception:
                pass

        self.tampil_login()

    def report_callback_exception(self, exc, val, tb):
        import traceback
        traceback.print_exception(exc, val, tb)
        messagebox.showerror("Terjadi Kesalahan", f"{val}\n\n(Rincian kesalahan dicatat di log terminal)")

    def bersihkan(self):
        for w in self.winfo_children():
            w.destroy()

    def tampil_login(self):
        self.bersihkan()
        self.user = None
        LoginScreen(self, self).pack(fill="both", expand=True)

    def tampil_utama(self):
        self.bersihkan()
        MainFrame(self, self).pack(fill="both", expand=True)

    def tutup(self):
        try:
            self.db.tutup()
        finally:
            self.destroy()


if __name__ == "__main__":
    App().mainloop()

    ## password owner: owner999
    ## password karyawan: kerja111
