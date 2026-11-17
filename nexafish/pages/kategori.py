"""Halaman Kategori Ukuran Ikan Bawal NEXAFISH ERP."""

import tkinter as tk
from tkinter import messagebox

from base import Halaman
from theme import C, f
from widgets import Tombol, Dialog, buat_tabel, isi_tabel, kartu


class KategoriPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)

        # Toolbar Card
        toolbar = kartu(self)
        toolbar.pack(fill="x", pady=(0, 12))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        # Keterangan Sisi Kiri
        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left", fill="x", expand=True)

        tk.Label(kiri, text="Klasifikasi Ukuran Ikan Bawal", font=f(11, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(kiri, text="Kelola standar ukuran ikan bawal. Kategori yang masih terikat dengan data produk aktif tidak dapat dihapus.",
                 font=f(8), bg="white", fg=C["muted"], wraplength=560, justify="left").pack(anchor="w")

        # Tombol Aksi Sisi Kanan
        kanan = tk.Frame(tb_inner, bg="white")
        kanan.pack(side="right")

        Tombol(kanan, "Hapus", self.hapus, gaya="soft", warna=C["red_text"], tinggi=38, ukuran=9).pack(side="right", padx=(6, 0))
        Tombol(kanan, "Ubah", self.ubah, gaya="soft", warna=C["primary"], tinggi=38, ukuran=9).pack(side="right", padx=(6, 0))
        Tombol(kanan, "+ Kategori", self.tambah, warna=C["primary"], tinggi=38, ukuran=9).pack(side="right")

        # Tabel Kategori Ukuran
        kolom = [
            ("kode", "Kode", 90, "center"),
            ("nama", "Nama Kategori Ukuran", 220, "w"),
            ("ket", "Keterangan Klasifikasi / Bobot", 380, "w"),
            ("jml", "Jumlah Produk Terkait", 140, "e"),
        ]

        frame_tabel, self.tree = buat_tabel(self, kolom, tinggi=14)
        frame_tabel.pack(fill="both", expand=True)

        self.muat()

    def muat(self):
        isi_tabel(self.tree, [(i, (kode, n, k or "-", j))
                              for i, kode, n, k, j in self.db.daftar_kategori_lengkap()])

    def terpilih(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Pilih Kategori", "Silakan klik salah satu baris kategori pada tabel terlebih dahulu.", parent=self)
            return None
        return int(sel[0])

    def tambah(self):
        def simpan(v):
            self.db.tambah_kategori(v["nama"], v["ket"], self.user, v["kode"])
            self.muat()

        Dialog(self, "Tambah Kategori Ukuran", [
            ("kode", "Kode Kategori (contoh: BWL01 / PKN01)", "text", None, ""),
            ("nama", "Nama Kategori", "text", None, ""),
            ("ket", "Keterangan Klasifikasi / Bobot", "text", None, ""),
        ], simpan, info="Kode kategori diisi manual dan harus unik.")

    def ubah(self):
        kid = self.terpilih()
        if kid is None:
            return
        kode, nama, ket, _j = next((c, n, k, j) for i, c, n, k, j in self.db.daftar_kategori_lengkap() if i == kid)

        def simpan(v):
            self.db.ubah_kategori(kid, v["nama"], v["ket"], self.user, v["kode"])
            self.muat()

        Dialog(self, "Ubah Kategori Ukuran", [
            ("kode", "Kode Kategori", "text", None, kode),
            ("nama", "Nama Kategori Ukuran", "text", None, nama),
            ("ket", "Keterangan Klasifikasi / Bobot", "text", None, ket or ""),
        ], simpan)

    def hapus(self):
        kid = self.terpilih()
        if kid is None:
            return
        if messagebox.askyesno("Hapus Kategori", "Apakah Anda yakin ingin menghapus kategori terpilih?", parent=self):
            if self.coba(self.db.hapus_kategori, kid, self.user):
                self.muat()



