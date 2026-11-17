"""Halaman Buku Besar (General Ledger) NEXAFISH ERP."""

import tkinter as tk

from base import Halaman
from theme import C, f
from utils import rupiah
from widgets import buat_combo, buat_tabel, isi_tabel, kartu


class BukuBesarPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)

        # Toolbar Card
        toolbar = kartu(self)
        toolbar.pack(fill="x", pady=(0, 12))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        # Sisi Kiri: Pilihan Akun
        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left")

        tk.Label(kiri, text="Pilih Akun Buku Besar:", font=f(9, True), bg="white", fg=C["text"]).pack(side="left", padx=(0, 8))
        self.opsi = [f"{k} - {n}" for k, n, _t, _s in self.db.daftar_akun()]
        self.cb = buat_combo(kiri, self.opsi, lebar=34)
        self.cb.set(self.opsi[0] if self.opsi else "")
        self.cb.pack(side="left", ipady=2)
        self.cb.bind("<<ComboboxSelected>>", lambda e: self.muat())

        # Sisi Kanan: Badge Saldo Akhir
        kanan = tk.Frame(tb_inner, bg="white")
        kanan.pack(side="right")

        self.lbl = tk.Label(kanan, text="", font=f(11, True), bg="white", fg=C["primary"])
        self.lbl.pack(side="right")

        # Tabel Mutasi Buku Besar
        kolom = [
            ("tgl", "Tanggal & Waktu", 150, "w"),
            ("ket", "Keterangan Transaksi", 340, "w"),
            ("debit", "Debit (Rp)", 125, "e"),
            ("kredit", "Kredit (Rp)", 125, "e"),
            ("saldo", "Saldo Berjalan (Rp)", 135, "e"),
        ]
        fr, self.tree = buat_tabel(self, kolom, tinggi=16)
        fr.pack(fill="both", expand=True)

        self.muat()

    def muat(self):
        val = self.cb.get()
        if not val:
            return
        kode = val.split(" - ")[0]
        akun, rows = self.db.buku_besar(kode)
        isi_tabel(self.tree, [(t, k, rupiah(d) if d else "", rupiah(kr) if kr else "", rupiah(s))
                              for t, k, d, kr, s in rows])
        akhir = rows[-1][4] if rows else 0
        self.lbl.config(text=f"Saldo Akhir ({akun[1]}): {rupiah(akhir)}")



