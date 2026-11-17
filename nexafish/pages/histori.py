"""Halaman Histori Aktivitas (Audit Trail) NEXAFISH ERP."""

import tkinter as tk

from base import Halaman
from theme import C, f
from widgets import buat_tabel, isi_tabel, kartu, Tombol


class HistoriPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)

        # Toolbar Card
        toolbar = kartu(self)
        toolbar.pack(fill="x", pady=(0, 12))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left")

        tk.Label(kiri, text="Log Audit & Jejak Aktivitas Sistem", font=f(11, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(kiri, text="Rekam jejak otomatis: siapa melakukan apa dan kapan (login, transaksi penjualan, restock, perubahan data).",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w")

        kanan = tk.Frame(tb_inner, bg="white")
        kanan.pack(side="right")
        Tombol(kanan, "Segarkan Log", self.muat, gaya="outline", tinggi=32, ukuran=9, ikon="↻").pack(side="right")

        # Tabel Audit Trail
        kolom = [
            ("waktu", "Waktu Aktivitas", 160, "w"),
            ("nama", "Nama Pengguna", 160, "w"),
            ("jab", "Hak Akses", 100, "center"),
            ("akt", "Rincian Aktivitas / Catatan Sistem", 520, "w"),
        ]
        fr, self.tree = buat_tabel(self, kolom, tinggi=16)
        fr.pack(fill="both", expand=True)

        self.muat()

    def muat(self):
        isi_tabel(self.tree, self.db.daftar_histori())



