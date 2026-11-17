"""Halaman Operasional, Pembelian, Kas, dan Kebijakan Usaha NEXAFISH ERP."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from base import Halaman
from theme import C, f
from utils import rupiah, parse_angka
from widgets import TabModern, Tombol, Isian, Dialog, buat_combo, buat_tabel, isi_tabel, kartu
from pages.jurnal import JurnalManualDialog


class OperasionalPage(Halaman):
    """Master data, pembelian, jurnal kas, kas kecil, bagan akun, dan kebijakan usaha."""

    def __init__(self, parent, main):
        super().__init__(parent, main)
        self.nb = TabModern(self)
        self.nb.pack(fill="both", expand=True)

        if self.is_owner:
            self._buat_master()
            self._buat_akun()
            self._buat_kebijakan()

    def _buat_master(self):
        tab=tk.Frame(self.nb,bg=C["bg"])
        self.nb.add(tab,text=" Customer ")
        box=kartu(tab); box.pack(fill="both",expand=True,padx=8,pady=12)
        kepala=tk.Frame(box,bg="white"); kepala.pack(fill="x",padx=16,pady=12)
        tk.Label(kepala,text="Pelanggan / Customer",font=f(11,True),bg="white",fg=C["text"]).pack(side="left")
        Tombol(kepala,"+ Customer",lambda:self._dialog_pihak("customer"),tinggi=32,ukuran=9).pack(side="right")
        fr,self.tree_customer=buat_tabel(box,[("nama","Nama",220,"w"),("tel","Telepon",150,"w"),("saldo","Saldo Awal",140,"e")],tinggi=14)
        fr.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self._muat_pihak("customer")

    def _dialog_pihak(self, jenis):
        customer = jenis == "customer"
        title = "Tambah Pelanggan (Customer)" if customer else "Tambah Pemasok (Supplier)"
        saldo = "Saldo Awal Piutang" if customer else "Saldo Awal Utang"
        Dialog(self, title, [
            ("nama", "Nama Lengkap / Instansi", "text", None, ""),
            ("telepon", "Nomor Telepon / WhatsApp", "text", None, ""),
            ("alamat", "Alamat Domisili", "text", None, ""),
            ("saldo", f"{saldo} (Rp)", "number", None, "0")
        ], lambda v: (
            self.db.tambah_pihak(jenis, v["nama"], v["telepon"], v["alamat"], parse_angka(v["saldo"] or "0", saldo), self.user),
            self._muat_pihak(jenis)
        ), info=f"Mendaftarkan kontak mitra bisnis ke sistem buku besar {saldo.lower()}.")

    def _muat_pihak(self, jenis):
        tree = getattr(self, "tree_" + jenis, None)
        if tree:
            isi_tabel(tree, [(n, t or "-", rupiah(s)) for _i, n, t, _a, s in self.db.daftar_pihak(jenis)])
        if jenis == "supplier" and hasattr(self, "cb_supplier"):
            self.cb_supplier.config(values=["Supplier Umum"] + [r[1] for r in self.db.daftar_pihak("supplier")])

    def _buat_pembelian(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Pembelian Stok ")

        form = kartu(tab)
        form.pack(fill="x", padx=8, pady=(12, 8))

        w = tk.Frame(form, bg="white")
        w.pack(fill="x", padx=16, pady=14)

        # Baris Label
        tk.Label(w, text="Pemasok (Supplier)", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=0, sticky="w")
        tk.Label(w, text="Produk Ikan Bawal", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(w, text="Jumlah (kg)", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=2, sticky="w", padx=8)
        tk.Label(w, text="Harga Beli / kg", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=3, sticky="w", padx=8)
        tk.Label(w, text="Metode Bayar", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=4, sticky="w", padx=8)

        # Baris Input
        sups = [r[1] for r in self.db.daftar_pihak("supplier")]
        self.cb_supplier = buat_combo(w, ["Supplier Umum"] + sups, lebar=20, editable=True)
        self.cb_supplier.set("Supplier Umum")
        self.cb_supplier.grid(row=1, column=0, padx=(0, 8), sticky="ew", pady=(4, 0))

        self.produk_opsi = {f"#{i} {n} ({stok:g} kg)": i for i, n, _k, stok, _b, _j in self.db.daftar_produk()}
        self.cb_beli_produk = buat_combo(w, list(self.produk_opsi), lebar=26)
        self.cb_beli_produk.grid(row=1, column=1, padx=8, sticky="ew", pady=(4, 0))

        self.in_beli_jumlah = Isian(w, numeric=True, placeholder="kg")
        self.in_beli_jumlah.grid(row=1, column=2, padx=8, sticky="ew", pady=(4, 0))

        self.in_beli_harga = Isian(w, numeric=True, placeholder="Harga/kg")
        self.in_beli_harga.grid(row=1, column=3, padx=8, sticky="ew", pady=(4, 0))

        self.cb_beli_metode = buat_combo(w, ["Tunai", "Kredit"], lebar=12)
        self.cb_beli_metode.set("Tunai")
        self.cb_beli_metode.grid(row=1, column=4, padx=8, sticky="ew", pady=(4, 0))

        Tombol(w, "Catat Pembelian", self._simpan_pembelian, warna=C["income"], tinggi=34, ukuran=9).grid(row=1, column=5, padx=(8, 0), pady=(4, 0))

        for i in range(5):
            w.columnconfigure(i, weight=1)

        info_bar = tk.Frame(tab, bg=C["bg"])
        info_bar.pack(fill="x", padx=12, pady=(0, 4))
        self.lbl_beli = tk.Label(info_bar, text="Ongkir otomatis: Rp 5.000/kg untuk 1-3 kg; gratis untuk pesanan di atas 3 kg.",
                                 font=f(8), bg=C["bg"], fg=C["muted"])
        self.lbl_beli.pack(anchor="w")

        kolom_beli = [
            ("waktu", "Tanggal & Waktu", 140, "w"),
            ("sup", "Supplier", 150, "w"),
            ("prod", "Produk Bawal", 190, "w"),
            ("kg", "Jumlah (kg)", 90, "e"),
            ("total", "Total Nilai", 125, "e"),
            ("met", "Metode", 90, "w"),
            ("oleh", "Petugas", 120, "w")
        ]
        fr, self.tree_beli = buat_tabel(tab, kolom_beli, tinggi=12)
        fr.pack(fill="both", expand=True, padx=8, pady=(4, 12))
        self._muat_pembelian()

    def _simpan_pembelian(self):
        pid = self.produk_opsi.get(self.cb_beli_produk.get())
        if not pid:
            return messagebox.showwarning("Pembelian", "Silakan pilih produk ikan bawal terlebih dahulu.", parent=self)
        try:
            total, ongkir = self.db.pembelian_produk(
                pid, self.cb_supplier.get(), parse_angka(self.in_beli_jumlah.get(), "Jumlah"),
                parse_angka(self.in_beli_harga.get(), "Harga"), self.cb_beli_metode.get(), self.user)
        except (ValueError, sqlite3.Error) as e:
            return messagebox.showwarning("Pembelian", str(e), parent=self)
        self.lbl_beli.config(text=f"Pembelian berhasil dicatat: {rupiah(total)} (Termasuk ongkir: {rupiah(ongkir)}).")
        self._muat_pembelian()
        self.produk_opsi = {f"#{i} {n} ({stok:g} kg)": i for i, n, _k, stok, _b, _j in self.db.daftar_produk()}
        self.cb_beli_produk.config(values=list(self.produk_opsi))
        self.in_beli_jumlah.clear()
        self.in_beli_harga.clear()

    def _muat_pembelian(self):
        isi_tabel(self.tree_beli, [(w[:16], s, p, f"{q:g} kg", rupiah(t), m, o)
                                   for w, s, p, q, t, m, o in self.db.daftar_pembelian()])

    def _buat_kas(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Kas & Kas Kecil ")

        self.nb_kas = TabModern(tab)
        self.nb_kas.pack(fill="both", expand=True, padx=8, pady=12)

        self._form_kas("Penerimaan", False, False)
        self._form_kas("Pengeluaran", False, False)
        self._form_kas("Pengeluaran", True, True)

    def _form_kas(self, jenis, kas_kecil, tambah_tab):
        label = "Kas Kecil (Petty Cash)" if kas_kecil else f"{jenis} Kas Operasional"
        tab = tk.Frame(self.nb_kas, bg="white")
        self.nb_kas.add(tab, text=f"  {label}  ")

        wrap = tk.Frame(tab, bg="white")
        wrap.pack(anchor="nw", fill="x", padx=24, pady=20)

        tk.Label(wrap, text=label, font=f(13, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(wrap, text="Transaksi kas langsung mempengaruhi saldo kas utama / kas kecil dan membukukan mutasi debit-kredit.",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w", pady=(2, 10))

        tk.Frame(wrap, bg=C["border"], height=1).pack(fill="x", pady=(0, 12))

        # Keterangan
        tk.Label(wrap, text="Keterangan Transaksi Kas", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(0, 3))
        ket = Isian(wrap, placeholder="Contoh: Pembelian Bawal Konsumsi/Pembelian Bibit")
        ket.pack(fill="x")

        # Akun Lawan
        tk.Label(wrap, text="Akun Lawan (Rekening Alokasi)", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(10, 3))
        akunops = [f"{k} - {n}" for k, n, _t, _s in self.db.daftar_akun() if k != "1101"]
        cb = buat_combo(wrap, akunops, lebar=38)
        cb.pack(anchor="w", ipady=2)
        if kas_kecil and "5102 - Beban Operasional" in akunops:
            cb.set("5102 - Beban Operasional")

        # Pihak Pelunasan (Opsional)
        tk.Label(wrap, text="Customer / Supplier Terkait Pelunasan (Opsional)", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(10, 3))
        party = buat_combo(wrap, [""] + [f"Customer - {r[1]}" for r in self.db.daftar_pihak("customer")] +
                           [f"Supplier - {r[1]}" for r in self.db.daftar_pihak("supplier")], lebar=38)
        party.pack(anchor="w", ipady=2)

        # Jumlah
        tk.Label(wrap, text="Nominal Jumlah (Rp)", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(10, 3))
        jumlah = Isian(wrap, numeric=True, placeholder="Nominal Rp")
        jumlah.pack(anchor="w")

        def simpan():
            kode = cb.get().split(" - ")[0]
            nama_pihak = party.get()
            if nama_pihak.startswith("Customer - "):
                nama_pihak = nama_pihak[11:]
            elif nama_pihak.startswith("Supplier - "):
                nama_pihak = nama_pihak[11:]
            else:
                nama_pihak = ""
            try:
                self.db.catat_kas(jenis, ket.get(), parse_angka(jumlah.get(), "Jumlah"), kode, self.user, kas_kecil, nama_pihak)
            except (ValueError, sqlite3.Error) as e:
                return messagebox.showwarning(label, str(e), parent=self)
            ket.clear()
            jumlah.clear()
            messagebox.showinfo(label, "Transaksi kas berhasil dicatat dan dibukukan ke jurnal.", parent=self)

        Tombol(wrap, "Catat Transaksi Kas", simpan, warna=C["primary"], tinggi=36, ukuran=10).pack(anchor="w", pady=(16, 0))

    def _buat_akun(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Bagan Akun (COA) ")

        form = kartu(tab)
        form.pack(fill="x", padx=8, pady=(12, 8))

        w = tk.Frame(form, bg="white")
        w.pack(fill="x", padx=16, pady=12)

        tk.Label(w, text="Kode", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=0, sticky="w")
        tk.Label(w, text="Nama Akun", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=1, sticky="w", padx=4)
        tk.Label(w, text="Klasifikasi Tipe", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=2, sticky="w", padx=4)
        tk.Label(w, text="Saldo Normal", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=3, sticky="w", padx=4)
        tk.Label(w, text="Saldo Awal", font=f(8, True), bg="white", fg=C["text"]).grid(row=0, column=4, sticky="w", padx=4)

        self.akun_kode = Isian(w, placeholder="Kode (4 digit)")
        self.akun_kode.grid(row=1, column=0, padx=(0, 4), sticky="ew", pady=(4, 0))

        self.akun_nama = Isian(w, placeholder="Nama Akun Rekening")
        self.akun_nama.grid(row=1, column=1, padx=4, sticky="ew", pady=(4, 0))

        self.akun_tipe = buat_combo(w, ["Aset", "Kewajiban", "Modal", "Pendapatan", "Beban"])
        self.akun_tipe.set("Aset")
        self.akun_tipe.grid(row=1, column=2, padx=4, sticky="ew", pady=(4, 0))

        self.akun_normal = buat_combo(w, ["Debit", "Kredit"])
        self.akun_normal.set("Debit")
        self.akun_normal.grid(row=1, column=3, padx=4, sticky="ew", pady=(4, 0))

        self.akun_saldo = Isian(w, placeholder="Saldo Awal (Rp)", numeric=True)
        self.akun_saldo.grid(row=1, column=4, padx=4, sticky="ew", pady=(4, 0))

        Tombol(w, "Simpan / Ubah", self._simpan_akun, warna=C["primary"], tinggi=32, ukuran=9).grid(row=1, column=5, padx=4, pady=(4, 0))
        Tombol(w, "Hapus", self._hapus_akun, gaya="soft", warna=C["red_text"], tinggi=34, ukuran=9).grid(row=1, column=6, padx=(4, 0), pady=(4, 0))

        for i in range(5):
            w.columnconfigure(i, weight=1)

        kolom_akun = [
            ("kode", "Kode Akun", 90, "center"),
            ("nama", "Nama Akun Rekening", 320, "w"),
            ("tipe", "Klasifikasi Tipe", 140, "w"),
            ("normal", "Posisi Saldo Normal", 140, "w"),
        ]
        fr, self.tree_akun = buat_tabel(tab, kolom_akun, tinggi=14)
        fr.pack(fill="both", expand=True, padx=8, pady=(4, 12))
        self.tree_akun.bind("<<TreeviewSelect>>", self._pilih_akun)
        self._muat_akun()

    def _muat_akun(self):
        isi_tabel(self.tree_akun, self.db.daftar_akun())

    def _pilih_akun(self, _e=None):
        s = self.tree_akun.selection()
        if s:
            k, n, t, normal = self.tree_akun.item(s[0], "values")
            self.akun_kode.set(k)
            self.akun_nama.set(n)
            self.akun_tipe.set(t)
            self.akun_normal.set(normal)
            self.akun_saldo.set("0")

    def _simpan_akun(self):
        try:
            self.db.kelola_akun(self.akun_kode.get(), self.akun_nama.get(), self.akun_tipe.get(),
                                self.akun_normal.get(), parse_angka(self.akun_saldo.get() or "0", "Saldo awal"), self.user)
        except (ValueError, sqlite3.Error) as e:
            return messagebox.showwarning("Bagan Akun", str(e), parent=self)
        self._muat_akun()
        self.akun_saldo.clear()
        messagebox.showinfo("Bagan Akun", "Akun berhasil disimpan ke bagan akun.", parent=self)

    def _hapus_akun(self):
        try:
            self.db.hapus_akun(self.akun_kode.get(), self.user)
        except (ValueError, sqlite3.Error) as e:
            return messagebox.showwarning("Bagan Akun", str(e), parent=self)
        self._muat_akun()

    def _buat_kebijakan(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Kebijakan Usaha ")

        box = kartu(tab)
        box.pack(anchor="nw", fill="x", padx=14, pady=14)

        tk.Label(box, text="Kebijakan Usaha", font=f(12, True), bg="white", fg=C["text"]).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(box, text="Atur denda keterlambatan dan batas waktu termin. Ongkos kirim kasir mengikuti ketentuan tetap pada revisi aplikasi.",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w", padx=20, pady=(0, 10))

        tk.Frame(box, bg=C["border"], height=1).pack(fill="x", padx=20, pady=(0, 12))

        row = tk.Frame(box, bg="white")
        row.pack(fill="x", padx=20, pady=8)

        self.kebijakan_inputs = []
        labels = [
            ("Persentase Denda Keterlambatan (%)", "denda_persen"),
            ("Batas Waktu Termin Pembayaran (Hari)", "termin_hari")
        ]

        for i, (label, key) in enumerate(labels):
            tk.Label(row, text=label, font=f(9, True), bg="white", fg=C["text"]).grid(row=i, column=0, sticky="w", pady=6)
            ent = Isian(row, numeric=True)
            ent.grid(row=i, column=1, sticky="ew", padx=(16, 0), pady=6)
            res = self.db.conn.execute("SELECT nilai FROM kebijakan WHERE nama=?", (key,)).fetchone()
            ent.set(res[0] if res else "")
            self.kebijakan_inputs.append(ent)

        row.columnconfigure(1, weight=1)

        Tombol(box, "Simpan Perubahan Kebijakan", self._simpan_kebijakan, warna=C["primary"], tinggi=36, ukuran=10).pack(anchor="w", padx=20, pady=(14, 16))

    def _simpan_kebijakan(self):
        try:
            self.db.set_kebijakan(*(parse_angka(x.get(), "Kebijakan") for x in self.kebijakan_inputs), user=self.user)
        except ValueError as e:
            return messagebox.showwarning("Kebijakan", str(e), parent=self)
        messagebox.showinfo("Kebijakan", "Kebijakan bisnis berhasil diperbarui.", parent=self)

    def _buat_penyesuaian(self):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=" Jurnal Penyesuaian ")

        toolbar = kartu(tab)
        toolbar.pack(fill="x", padx=8, pady=(12, 8))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left")

        tk.Label(kiri, text="Jurnal Penyesuaian Akhir Periode (Adjusting Entries)", font=f(11, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(kiri, text="Catat penyesuaian akrual, penyusutan, atau perlengkapan. Laporan keuangan menampilkan angka sebelum & sesudah penyesuaian.",
                 font=f(8), bg="white", fg=C["muted"]).pack(anchor="w")

        kanan = tk.Frame(tb_inner, bg="white")
        kanan.pack(side="right")

        Tombol(kanan, "+ Jurnal Penyesuaian",
               lambda: JurnalManualDialog(self, self.db, self.user, self._refresh_adj, ref="JURNAL-PENYESUAIAN"),
               warna=C["primary"], tinggi=34, ukuran=9).pack(side="right")

        kolom_adj = [
            ("no", "No. Jurnal", 90, "center"),
            ("tgl", "Tanggal & Waktu", 160, "w"),
            ("ket", "Keterangan Penyesuaian", 450, "w"),
            ("oleh", "Dibuat Oleh", 160, "w")
        ]
        fr, self.tree_adj = buat_tabel(tab, kolom_adj, tinggi=12)
        fr.pack(fill="both", expand=True, padx=8, pady=(4, 12))
        self._refresh_adj()

    def _refresh_adj(self):
        rows = self.db.conn.execute(
            "SELECT id_jurnal, tanggal, keterangan, dibuat_oleh FROM jurnal WHERE referensi='JURNAL-PENYESUAIAN' ORDER BY id_jurnal DESC"
        ).fetchall()
        isi_tabel(self.tree_adj, [(f"J-{i:04d}", t, k, o) for i, t, k, o in rows])



