"""Halaman Pengaturan Akun, Keamanan Sandi, dan Backup Database NEXAFISH ERP."""

import datetime
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from base import Halaman
from theme import C, f
from widgets import TabModern, Tombol, Isian, kartu


class PengaturanPage(Halaman):
    """Pengaturan keamanan akun pengguna dan backup/restore database usaha."""

    def __init__(self, parent, main):
        super().__init__(parent, main)
        self.nb = TabModern(self)
        self.nb.pack(fill="both", expand=True)

        if self.is_owner:
            self._buat_keamanan()
        self._buat_backup()

    def _buat_keamanan(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Keamanan & Sandi ")

        box = kartu(tab)
        box.pack(anchor="nw", fill="x", padx=16, pady=16)

        tk.Label(box, text="Perbarui Kata Sandi (Password)", font=f(12, True), bg="white", fg=C["text"]).pack(anchor="w", padx=20, pady=(18, 4))
        
        role = self.user["jabatan"]
        pesan = "Kata sandi Karyawan digunakan bersama oleh seluruh staf kasir operasional." if role == "Karyawan" else "Kata sandi ini digunakan secara privat untuk otorisasi akun Owner."
        tk.Label(box, text=pesan, font=f(8), bg="white", fg=C["muted"]).pack(anchor="w", padx=20, pady=(0, 10))

        tk.Frame(box, bg=C["border"], height=1).pack(fill="x", padx=20, pady=(0, 12))

        self.pw_lama = Isian(box, password=True, placeholder="Masukkan sandi saat ini")
        self.pw_baru = Isian(box, password=True, placeholder="Masukkan sandi baru")
        self.pw_ulang = Isian(box, password=True, placeholder="Ulangi sandi baru")

        for label, field in (("Password Saat Ini", self.pw_lama),
                             ("Password Baru", self.pw_baru),
                             ("Ulangi Password Baru", self.pw_ulang)):
            tk.Label(box, text=label, font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", padx=20, pady=(6, 2))
            field.pack(fill="x", padx=20)

        self.pw_pesan = tk.Label(box, text="", font=f(8), bg="white", fg=C["muted"])
        self.pw_pesan.pack(anchor="w", padx=20, pady=(8, 0))

        Tombol(box, "Simpan Kata Sandi", self._simpan_password, warna=C["primary"], tinggi=36, ukuran=10).pack(anchor="w", padx=20, pady=(12, 18))

    def _simpan_password(self):
        baru = self.pw_baru.get()
        ulang = self.pw_ulang.get()
        if baru != ulang:
            self.pw_pesan.config(text="Password baru dan konfirmasi pengulangan tidak cocok.", fg=C["danger"])
            return
        try:
            self.db.ganti_password(self.user["jabatan"], self.pw_lama.get(), baru, self.user)
        except (ValueError, sqlite3.Error) as e:
            self.pw_pesan.config(text=str(e), fg=C["danger"])
            return
        self.pw_lama.clear()
        self.pw_baru.clear()
        self.pw_ulang.clear()
        self.pw_pesan.config(text="Password berhasil diperbarui dan tersimpan permanen di database.", fg=C["income"])

    def _buat_backup(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Backup & Pemulihan Database ")

        box = kartu(tab)
        box.pack(anchor="nw", fill="x", padx=16, pady=16)

        tk.Label(box, text="Cadangan & Pemulihan Data (Backup & Restore)", font=f(12, True), bg="white", fg=C["text"]).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(box, text="Simpan berkas backup ke direktori aman secara berkala. Saat melakukan pemulihan data, sistem akan secara otomatis membuat salinan proteksi database aktif sebelum menimpa data.",
                 font=f(8), bg="white", fg=C["muted"], wraplength=760, justify="left").pack(anchor="w", padx=20, pady=(0, 12))

        tk.Frame(box, bg=C["border"], height=1).pack(fill="x", padx=20, pady=(0, 16))

        aksi = tk.Frame(box, bg="white")
        aksi.pack(anchor="w", padx=20, pady=(0, 20))

        Tombol(aksi, "Buat Cadangan (Backup)", self._buat_backup_file, warna=C["primary"], tinggi=38, ukuran=10, ikon="↓").pack(side="left")
        Tombol(aksi, "Pulihkan Data (Restore)", self._pulihkan_file, gaya="soft", warna=C["amber_text"], tinggi=38, ukuran=10, ikon="↺").pack(side="left", padx=(12, 0))

    def _buat_backup_file(self):
        awal = "Nexafish_backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
        path = filedialog.asksaveasfilename(
            title="Simpan Berkas Cadangan Nexafish", initialfile=awal,
            defaultextension=".db", filetypes=[("Database SQLite", "*.db"), ("Semua Berkas", "*.*")])
        if not path:
            return
        try:
            tujuan = self.db.backup_database(path)
        except (ValueError, sqlite3.Error, OSError) as e:
            return messagebox.showerror("Gagal Membuat Backup", str(e), parent=self)
        messagebox.showinfo("Backup Berhasil", f"Berkas cadangan berhasil disimpan di:\n{tujuan}", parent=self)

    def _pulihkan_file(self):
        path = filedialog.askopenfilename(
            title="Pilih Berkas Cadangan Nexafish", filetypes=[("Database SQLite", "*.db *.bak"), ("Semua Berkas", "*.*")])
        if not path:
            return
        if not messagebox.askyesno(
            "Konfirmasi Pemulihan",
            "Data aktif saat ini akan diganti dengan isi dari berkas backup. Lanjutkan?\n\n(Salinan keselamatan database aktif saat ini akan dibuat otomatis terlebih dahulu).",
            parent=self
        ):
            return
        try:
            aman = self.db.pulihkan_database(path)
        except (ValueError, sqlite3.Error, OSError) as e:
            return messagebox.showerror("Pemulihan Gagal", str(e), parent=self)
        messagebox.showinfo("Pemulihan Berhasil", f"Data berhasil dipulihkan dari berkas backup.\nSalinan keselamatan database sebelumnya:\n{aman}", parent=self)



