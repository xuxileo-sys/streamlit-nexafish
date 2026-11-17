"""Fungsi bantu non-visual (format angka, tanggal, hash). Isi dipindahkan apa adanya dari nexafish.py."""

import datetime
import hashlib
import os
import re

def _dapatkan_db_file():
    folder_app = os.path.dirname(os.path.abspath(__file__))
    path_app = os.path.join(folder_app, "nexafish.db")
    path_root = os.path.join(os.path.dirname(folder_app), "nexafish.db")
    if os.path.exists(path_app):
        return path_app
    elif os.path.exists(path_root):
        return path_root
    return path_app

DB_FILE = _dapatkan_db_file()

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sekarang():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def angka(x):
    return f"{x:,.0f}".replace(",", ".")


def rupiah(x):
    if x < 0:
        return "-Rp " + angka(abs(x))
    return "Rp " + angka(x)


def parse_angka(teks, nama="Nilai"):
    """Ubah teks seperti '45000', '45.000', '1.500.000' atau '2,5' menjadi float."""
    t = str(teks).strip().lower().replace("rp", "").replace(" ", "")
    if not t:
        raise ValueError(f"{nama} tidak boleh kosong.")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        raise ValueError(f"{nama} harus berupa angka (contoh: 45000).")


def tanggal_indonesia():
    d = datetime.date.today()
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"



