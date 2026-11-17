"""Kelas dasar semua halaman."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

try:
    from ui.theme import C
except ImportError:
    from theme import C


class Halaman(tk.Frame):
    """Dasar halaman. JUDUL / DESKRIPSI ditampilkan oleh MainFrame di kepala halaman."""

    JUDUL = ""
    DESKRIPSI = ""

    def __init__(self, parent, main):
        super().__init__(parent, bg=C["bg"])
        self.main = main
        self.db = main.db
        self.user = main.user
        self.is_owner = main.user["jabatan"] == "Owner"

    def coba(self, fn, *args):
        try:
            fn(*args)
            return True
        except ValueError as e:
            messagebox.showwarning("Tidak bisa diproses", str(e), parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("Kesalahan database", str(e), parent=self)
        return False



