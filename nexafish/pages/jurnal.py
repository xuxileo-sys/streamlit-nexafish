"""Halaman Jurnal Umum dan Dialog Jurnal Manual / Penyesuaian NEXAFISH ERP."""

import datetime
import tkinter as tk

from base import Halaman
from theme import C, f
from utils import rupiah, parse_angka
from widgets import Kartu, Tombol, Isian, buat_combo, buat_tabel, isi_tabel, kartu


class JurnalManualDialog(tk.Toplevel):
    TEMPLATE = {
        "Setor modal pemilik": ("1101", "3101"),
        "Bayar beban operasional": ("5102", "1101"),
        "Terima pelunasan piutang": ("1101", "1102"),
        "Bayar utang usaha": ("2101", "1101"),
    }

    def __init__(self, master, db, user, setelah, ref="MANUAL"):
        super().__init__(master)
        self.db, self.user, self.setelah, self.ref = db, user, setelah, ref
        self.baris = []
        judul_teks = "Jurnal Penyesuaian" if ref == "JURNAL-PENYESUAIAN" else "Input Jurnal Manual"
        self.title(judul_teks)
        self.configure(bg=C["border"])
        self.resizable(False, False)
        
        akun = db.daftar_akun()
        self.opsi_akun = [f"{k} - {n}" for k, n, _t, _s in akun]

        dalam = tk.Frame(self, bg="white")
        dalam.pack(fill="both", expand=True, padx=1, pady=1)

        w = tk.Frame(dalam, bg="white")
        w.pack(padx=28, pady=24)

        tk.Label(w, text=judul_teks, font=f(14, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(w, text="Prinsip Double Entry: Total Debit dan Total Kredit wajib seimbang sebelum disimpan.",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w", pady=(2, 8))

        tk.Frame(w, bg=C["border"], height=1).pack(fill="x", pady=(0, 10))

        # Keterangan Jurnal
        tk.Label(w, text="Keterangan Jurnal", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(0, 3))
        self.ket = Isian(w, placeholder="Contoh: Pembayaran Listrik Toko")
        self.ket.pack(fill="x")
        self.tanggal = Isian(w)
        self.tanggal.set(datetime.date.today().isoformat())
        tk.Label(w, text="Tanggal (YYYY-MM-DD)", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(8, 3))
        self.tanggal.pack(fill="x")

        # Template Cepat
        tpl_box = Kartu(w, radius=12, bg="#F4F8FD")
        tpl_box.pack(fill="x", pady=(12, 10))
        
        tpl_inner = tk.Frame(tpl_box, bg="#F4F8FD")
        tpl_inner.pack(fill="x", padx=12, pady=10)

        tk.Label(tpl_inner, text="Pilih Template Cepat", font=f(8, True), bg="#F4F8FD", fg=C["text"]).grid(row=0, column=0, sticky="w")
        tk.Label(tpl_inner, text="Nominal (Rp)", font=f(8, True), bg="#F4F8FD", fg=C["text"]).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.cb_tpl = buat_combo(tpl_inner, list(self.TEMPLATE), lebar=26)
        self.cb_tpl.grid(row=1, column=0, ipady=2, sticky="ew")

        self.nominal = Isian(tpl_inner, numeric=True, placeholder="Nominal Rp")
        self.nominal.grid(row=1, column=1, padx=(10, 10), sticky="ew")

        Tombol(tpl_inner, "Terapkan Template", self.isi_template, warna=C["primary"], tinggi=32, ukuran=8).grid(row=1, column=2)
        tpl_inner.columnconfigure(0, weight=1)
        tpl_inner.columnconfigure(1, weight=1)

        # Baris Tambah Akun Manual
        tk.Label(w, text="Tambah Akun Debit / Kredit", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(6, 3))
        br = tk.Frame(w, bg="white")
        br.pack(fill="x")

        self.cb_akun = buat_combo(br, self.opsi_akun, lebar=28)
        self.cb_akun.pack(side="left", ipady=2)

        self.in_debit = Isian(br, placeholder="Debit (Rp)", numeric=True)
        self.in_debit.pack(side="left", padx=(8, 0), fill="x", expand=True)

        self.in_kredit = Isian(br, placeholder="Kredit (Rp)", numeric=True)
        self.in_kredit.pack(side="left", padx=(8, 8), fill="x", expand=True)

        Tombol(br, "+ Baris", self.tambah_baris, gaya="soft", warna=C["green_text"], tinggi=36, ukuran=9).pack(side="left")

        # Tabel Baris Jurnal
        fr, self.tree = buat_tabel(w, [
            ("akun", "Akun Rekening", 280, "w"),
            ("debit", "Debit (Rp)", 130, "e"),
            ("kredit", "Kredit (Rp)", 130, "e")
        ], tinggi=6)
        fr.pack(fill="x", pady=(10, 6))

        # Baris Status Keseimbangan (Balanced Indicator)
        bawah = tk.Frame(w, bg="white")
        bawah.pack(fill="x", pady=(4, 0))

        self.lbl_total = tk.Label(bawah, text="", font=f(9, True), bg="white")
        self.lbl_total.pack(side="left")

        Tombol(bawah, "Hapus Baris Terpilih", self.hapus_baris, gaya="soft", warna=C["red_text"], tinggi=32, ukuran=8).pack(side="right")

        self.pesan = tk.Label(w, text="", font=f(8), bg="white", fg=C["danger"], wraplength=560, justify="left")
        self.pesan.pack(anchor="w", pady=(6, 0))

        # Aksi Simpan / Batal
        aksi = tk.Frame(w, bg="white")
        aksi.pack(fill="x", pady=(10, 0))

        Tombol(aksi, "Simpan Jurnal", self.simpan, warna=C["primary"], tinggi=36, ukuran=10).pack(side="right")
        Tombol(aksi, "Batal", self.destroy, gaya="outline", tinggi=36, ukuran=10).pack(side="right", padx=(0, 10))

        self.bind("<Escape>", lambda e: self.destroy())
        self.segarkan()
        self.update_idletasks()

        induk = master.winfo_toplevel()
        x = induk.winfo_rootx() + max((induk.winfo_width() - self.winfo_reqwidth()) // 2, 0)
        y = induk.winfo_rooty() + 40
        self.geometry(f"+{x}+{y}")
        self.transient(induk)
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass

    def isi_template(self):
        t = self.cb_tpl.get()
        if t not in self.TEMPLATE:
            self.pesan.config(text="Pilih template terlebih dahulu.")
            return
        try:
            n = parse_angka(self.nominal.get(), "Nominal")
        except ValueError as e:
            self.pesan.config(text=str(e))
            return
        if n <= 0:
            self.pesan.config(text="Nominal harus lebih dari 0.")
            return
        d, k = self.TEMPLATE[t]
        self.baris = [(d, n, 0.0), (k, 0.0, n)]
        if not self.ket.get():
            self.ket.set(t)
        self.pesan.config(text="")
        self.segarkan()

    def tambah_baris(self):
        kode = self.cb_akun.get().split(" - ")[0]
        if not kode:
            self.pesan.config(text="Silakan pilih akun terlebih dahulu.")
            return
        try:
            d = parse_angka(self.in_debit.get() or "0", "Debit")
            k = parse_angka(self.in_kredit.get() or "0", "Kredit")
        except ValueError as e:
            self.pesan.config(text=str(e))
            return
        if (d > 0) == (k > 0):
            self.pesan.config(text="Isi salah satu saja: Debit ATAU Kredit (lebih dari Rp 0).")
            return
        self.baris.append((kode, d, k))
        self.in_debit.clear()
        self.in_kredit.clear()
        self.pesan.config(text="")
        self.segarkan()

    def hapus_baris(self):
        sel = self.tree.selection()
        if sel:
            del self.baris[int(sel[0])]
            self.segarkan()

    def segarkan(self):
        nama = {k: n for k, n, _t, _s in self.db.daftar_akun()}
        isi_tabel(self.tree, [(i, (f"{k} - {nama.get(k, '')}", rupiah(d) if d else "", rupiah(kr) if kr else ""))
                              for i, (k, d, kr) in enumerate(self.baris)])
        td = sum(b[1] for b in self.baris)
        tk_ = sum(b[2] for b in self.baris)
        ok = self.baris and abs(td - tk_) < 0.005
        
        status_teks = "✓ SEIMBANG (BALANCED)" if ok else "✕ BELUM SEIMBANG"
        warna_status = C["income"] if ok else C["danger"]
        
        self.lbl_total.config(
            text=f"Total Debit: {rupiah(td)}  |  Total Kredit: {rupiah(tk_)}  —  {status_teks}",
            fg=warna_status
        )

    def simpan(self):
        try:
            if self.ref == "JURNAL-PENYESUAIAN":
                tanggal = self.tanggal.get().strip()
                datetime.datetime.strptime(tanggal, "%Y-%m-%d")
                self.db.jurnal_penyesuaian(self.ket.get(), self.baris, self.user, tanggal)
            else:
                self.db.jurnal_manual(self.ket.get(), self.baris, self.user)
        except ValueError as e:
            self.pesan.config(text=str(e))
            return
        self.setelah()
        self.destroy()


class JurnalPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)

        # Toolbar Card
        toolbar = kartu(self)
        toolbar.pack(fill="x", pady=(0, 12))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        # Keterangan Kiri
        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left")

        tk.Label(kiri, text="Buku Jurnal Umum (General Journal)", font=f(11, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(kiri, text="Semua transaksi operasional dan akuntansi tercatat dalam format double-entry secara kronologis.",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w")

        # Tombol Kanan
        kanan = tk.Frame(tb_inner, bg="white")
        kanan.pack(side="right")
        Tombol(kanan, "+ Jurnal Manual", self.manual, warna=C["primary"], tinggi=38, ukuran=9).pack(side="right")

        # Tabel Jurnal Umum
        kolom = [
            ("no", "No. Jurnal", 90, "center"),
            ("tgl", "Tanggal & Waktu", 150, "w"),
            ("akun", "Akun Rekening / Keterangan Transaksi", 430, "w"),
            ("debit", "Debit (Rp)", 135, "e"),
            ("kredit", "Kredit (Rp)", 135, "e"),
        ]
        fr, self.tree = buat_tabel(self, kolom, tinggi=16)
        fr.pack(fill="both", expand=True)

        self.muat()

    def muat(self):
        self.tree.delete(*self.tree.get_children())
        for (idj, tgl, ket, oleh), lines in self.db.daftar_jurnal():
            self.tree.insert("", "end", values=(f"J-{idj:04d}", tgl, f"● {ket}  [Dicatat oleh: {oleh}]", "", ""), tags=("judul",))
            for kode, nama, d, k in lines:
                indent = "      " if d else "      "
                self.tree.insert("", "end", values=("", "", f"{indent}{kode}  {nama}",
                                                    rupiah(d) if d else "", rupiah(k) if k else ""))

    def manual(self):
        JurnalManualDialog(self, self.db, self.user, self.muat)



