"""Halaman Kasir Penjualan (Point of Sales) Terintegrasi Double-Entry Bookkeeping NEXAFISH ERP."""

import datetime
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from base import Halaman
from theme import C, f
from utils import rupiah, parse_angka
from widgets import Kartu, Tombol, Isian, Dialog, TabModern, buat_combo, buat_tabel, isi_tabel, kartu


class KasirPage(Halaman):
    METODE = ["Tunai"]

    def __init__(self, parent, main):
        super().__init__(parent, main)
        self.nb=TabModern(self); self.nb.pack(fill="both",expand=True)
        self.tab_jual=tk.Frame(self.nb,bg=C["bg"]); self.nb.add(self.tab_jual,text=" Penjualan ")
        self.tab_beli=tk.Frame(self.nb,bg=C["bg"]); self.nb.add(self.tab_beli,text=" Pembelian ")
        self.tab_indukan=tk.Frame(self.nb,bg=C["bg"]); self.nb.add(self.tab_indukan,text=" Pembelian Indukan ")
        self.tab_jual.columnconfigure(0,weight=0); self.tab_jual.columnconfigure(1,weight=1)
        self.tab_jual.rowconfigure(0,weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ---------------- Sisi Kiri: Form Transaksi POS ----------------
        form_card = kartu(self.tab_jual)
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        isi = tk.Frame(form_card, bg="white")
        isi.pack(fill="both", expand=True, padx=22, pady=20)
        
        # Spacer lebar minimum
        tk.Frame(isi, bg="white", width=290, height=1).pack()

        tk.Label(isi, text="Point of Sales (Kasir)", font=f(13, True), bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(isi, text="Pencatatan transaksi kasir langsung memutasi stok dan membukukan jurnal umum.",
                 font=f(8), bg="white", fg=C["muted"], wraplength=280, justify="left").pack(anchor="w", pady=(2, 10))

        tk.Frame(isi, bg=C["border"], height=1).pack(fill="x", pady=(0, 12))

        # Pilih Produk
        tk.Label(isi, text="Produk Ikan Bawal", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(0, 3))
        self.cb_produk = buat_combo(isi, [])
        self.cb_produk.pack(fill="x", ipady=3)
        self.cb_produk.bind("<<ComboboxSelected>>", lambda e: self.hitung())

        self.info = tk.Label(isi, text="", font=f(8), bg="white", fg=C["primary"], justify="left")
        self.info.pack(anchor="w", pady=(3, 6))

        # Kuantitas kg
        tk.Label(isi, text="Kuantitas (kg)", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(2, 3))
        self.jumlah = Isian(isi, numeric=True, placeholder="Contoh: 5 atau 2.5")
        self.jumlah.pack(fill="x")
        self.jumlah.entry.bind("<KeyRelease>", lambda e: self.hitung())

        # Nama Pembeli
        tk.Label(isi, text="Nama Pelanggan / Pembeli", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(8, 3))
        self.pembeli = buat_combo(isi, [r[1] for r in self.db.daftar_pihak("customer")], editable=True)
        self.pembeli.set("Umum")
        self.pembeli.pack(fill="x", ipady=2)

        # Metode Pembayaran
        tk.Label(isi, text="Metode Pembayaran", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(8, 3))
        self.cb_metode = buat_combo(isi, self.METODE)
        self.cb_metode.set(self.METODE[0])
        self.cb_metode.pack(fill="x", ipady=3)
        self.cb_metode.bind("<<ComboboxSelected>>", lambda e: self.hitung())

        # Akun Pendapatan
        tk.Label(isi, text="Alokasi Akun Pendapatan", font=f(9, True), bg="white", fg=C["text"]).pack(anchor="w", pady=(8, 3))
        self.akun_jual = "4101"
        tk.Label(isi,text="Penjualan Ikan Bawal",font=f(10),bg="white",fg=C["text"],anchor="w").pack(fill="x",pady=(4,2))

        # Total Bayar Display Card
        total_box = Kartu(isi, radius=12, bg="#F4F8FD")
        total_box.pack(fill="x", pady=(14, 6))

        tk.Label(total_box, text="TOTAL TAGIHAN + ONGKIR", font=f(8, True), bg="#F4F8FD", fg=C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
        self.lbl_total = tk.Label(total_box, text="Rp 0", font=f(16, True), bg="#F4F8FD", fg=C["primary"])
        self.lbl_total.pack(anchor="w", padx=12, pady=(2, 8))

        # Status Error / Sukses
        self.status = tk.Label(isi, text="", font=f(8), bg="white", wraplength=280, justify="left")
        self.status.pack(anchor="w", pady=(0, 6))

        # Tombol Proses Transaksi
        Tombol(isi, "Proses Transaksi", self.proses, warna=C["income"], tinggi=46, ukuran=10, radius=12, ikon="✓").pack(fill="x")

        # ---------------- Sisi Kanan: Live Journal Preview + Riwayat Penjualan ----------------
        kanan = tk.Frame(self.tab_jual, bg=C["bg"])
        kanan.grid(row=0, column=1, sticky="nsew")

        # 1. Pratinjau Jurnal Otomatis (Double Entry)
        header_jurnal = tk.Frame(kanan, bg=C["bg"])
        header_jurnal.pack(fill="x", pady=(0, 6))
        tk.Label(header_jurnal, text="Pratinjau Jurnal Otomatis (Sistem Double Entry)", font=f(11, True),
                 bg=C["bg"], fg=C["text"]).pack(side="left")
        tk.Label(header_jurnal, text="Debit dan Kredit tercatat otomatis seimbang", font=f(8),
                 bg=C["bg"], fg=C["muted"]).pack(side="left", padx=(10, 0))

        kolom_jurnal = [
            ("akun", "Nama Akun Rekening", 260, "w"),
            ("debit", "Debit (Rp)", 130, "e"),
            ("kredit", "Kredit (Rp)", 130, "e"),
        ]
        f1, self.pratinjau = buat_tabel(kanan, kolom_jurnal, tinggi=5)
        f1.pack(fill="x", pady=(0, 16))

        # 2. Riwayat Penjualan Kasir Terbaru
        header_riwayat = tk.Frame(kanan, bg=C["bg"])
        header_riwayat.pack(fill="x", pady=(0, 6))
        tk.Label(header_riwayat, text="Riwayat Transaksi Penjualan Terbaru", font=f(11, True),
                 bg=C["bg"], fg=C["text"]).pack(side="left")

        kolom_riwayat = [
            ("bukti", "Bukti", 90, "center"),
            ("waktu", "Waktu Transaksi", 125, "w"),
            ("pembeli", "Pelanggan", 130, "w"),
            ("produk", "Varian Produk", 150, "w"),
            ("kg", "Kuantitas", 75, "e"),
            ("subtotal", "Subtotal", 120, "e"),
            ("metode", "Metode", 70, "w"),
            ("kasir", "Kasir", 90, "w"),
        ]
        f2, self.riwayat = buat_tabel(kanan, kolom_riwayat, tinggi=8)
        f2.pack(fill="both", expand=True)

        self.muat_produk()
        self.muat_riwayat()
        self.hitung()
        self._buat_pembelian()
        self._buat_indukan()

    def muat_produk(self):
        self.opsi = {}
        for pid, kode, kind, jenis, _idkat, _kodekat, kat, _ket, stok, _ekor, beli, jual in self.db.daftar_produk_lengkap(jenis_produk="Ikan"):
            self.opsi[f"{kode} {jenis} ({kat}) - Stok: {stok:g} kg"] = pid
        self.cb_produk.config(values=list(self.opsi))
        if self.cb_produk.get() not in self.opsi:
            self.cb_produk.set("")
        if hasattr(self, "pembeli"):
            cust = [r[1] for r in self.db.daftar_pihak("customer")]
            vals = ["Umum"] + [c for c in cust if c != "Umum"]
            self.pembeli.config(values=vals)

    def muat_riwayat(self):
        isi_tabel(self.riwayat, [(f"PJ-{i:03d}",w[5:16],p,n,f"{j:g} kg",rupiah(sub),m,k)
                                 for i,w,p,n,j,sub,_ongkir,_total,m,k in self.db.daftar_penjualan_rinci()])

    def metode(self):
        return "Tunai"

    def hitung(self):
        pid = self.opsi.get(self.cb_produk.get())
        try:
            qty = parse_angka(self.jumlah.get(), "Jumlah")
        except ValueError:
            qty = 0.0
        rows = []
        total = 0.0
        if pid:
            try:
                p = self.db.ambil_produk(pid)
            except ValueError:
                p = None
            if p:
                ongkir_satuan = self.db.ongkir_otomatis(qty) if qty > 0 else 0
                self.info.config(text=f"Harga: {rupiah(p['harga_jual'])}/kg  |  Stok: {p['stok']:g} kg  |  Ongkir: {rupiah(ongkir_satuan)}")
                subtotal = round(qty * p["harga_jual"], 2)
                ongkir = self.db.ongkir_otomatis(qty)
                total = subtotal + ongkir
                if qty > 0:
                    akun = "Kas" if self.metode() == "Tunai" else "Piutang Usaha"
                    rows += [(akun, rupiah(total), ""), ("   Penjualan Ikan Bawal", "", rupiah(subtotal))]
                    if ongkir:
                        rows += [("   Pendapatan Ongkir", "", rupiah(ongkir))]
                    if p["harga_beli"] > 0:
                        hpp = round(qty * p["harga_beli"], 2)
                        rows += [("Harga Pokok Penjualan (HPP)", rupiah(hpp), ""),
                                 ("   Persediaan Ikan Bawal", "", rupiah(hpp))]
        else:
            self.info.config(text="")
        self.lbl_total.config(text=rupiah(total))
        isi_tabel(self.pratinjau, rows)

    def proses(self):
        pid = self.opsi.get(self.cb_produk.get())
        if not pid:
            self.status.config(text="Silakan pilih produk ikan bawal terlebih dahulu.", fg=C["danger"])
            return
        try:
            qty = parse_angka(self.jumlah.get(), "Jumlah")
            id_jual,total,subtotal,ongkir = self.db.jual(pid, qty, self.pembeli.get(), self.metode(), self.user, self.akun_jual)
        except ValueError as e:
            self.status.config(text=str(e), fg=C["danger"])
            return
        self.status.config(text=f"Faktur PJ-{id_jual:03d} berhasil dibukukan: {rupiah(total)}", fg=C["income"])
        self.jumlah.clear()
        self.pembeli.set("Umum")
        self.muat_produk()
        self.muat_riwayat()
        self.hitung()





    def _buat_pembelian(self):
        box=kartu(self.tab_beli); box.pack(fill="x",padx=8,pady=(12,8))
        form=tk.Frame(box,bg="white"); form.pack(fill="x",padx=16,pady=14)
        tk.Label(form,text="Pemasok",font=f(8,True),bg="white",fg=C["text"]).grid(row=0,column=0,sticky="w")
        self.cb_supplier=buat_combo(form,[r[1] for r in self.db.daftar_pihak("supplier")],editable=True)
        self.cb_supplier.grid(row=1,column=0,sticky="ew",padx=(0,8))
        Tombol(form,"+ Supplier",self._tambah_supplier,gaya="outline",tinggi=30,ukuran=8).grid(row=1,column=1,padx=4)
        tk.Label(form,text="Produk Ikan / Pakan",font=f(8,True),bg="white",fg=C["text"]).grid(row=0,column=2,sticky="w")
        self.opsi_beli={}
        for row in self.db.daftar_produk_lengkap():
            self.opsi_beli[f"{row[1]} {row[3]} ({row[2]}) - {row[8]:g} kg"]=row[0]
        self.cb_beli_produk=buat_combo(form,list(self.opsi_beli)); self.cb_beli_produk.grid(row=1,column=2,sticky="ew",padx=8)
        tk.Label(form,text="Jumlah (kg)",font=f(8,True),bg="white",fg=C["text"]).grid(row=0,column=3,sticky="w")
        self.beli_kg=Isian(form,numeric=True,placeholder="kg"); self.beli_kg.grid(row=1,column=3,sticky="ew",padx=8)
        tk.Label(form,text="Ekor Masuk (ikan)",font=f(8,True),bg="white",fg=C["text"]).grid(row=0,column=4,sticky="w")
        self.beli_ekor=Isian(form,numeric=True,placeholder="0 untuk pakan"); self.beli_ekor.grid(row=1,column=4,sticky="ew",padx=8)
        tk.Label(form,text="HPP / kg",font=f(8,True),bg="white",fg=C["text"]).grid(row=0,column=5,sticky="w")
        self.beli_hpp=Isian(form,numeric=True,placeholder="HPP/kg"); self.beli_hpp.grid(row=1,column=5,sticky="ew",padx=8)
        for i in range(6): form.columnconfigure(i,weight=1)
        tk.Label(form,text="Metode pembayaran: Tunai",font=f(9,True),bg="white",fg=C["primary"]).grid(row=2,column=0,columnspan=3,sticky="w",pady=(10,0))
        Tombol(form,"Catat Pembelian",self._simpan_pembelian,warna=C["income"],tinggi=34,ukuran=9).grid(row=2,column=5,sticky="e",pady=(8,0))
        _fr,self.tree_beli=buat_tabel(self.tab_beli,[("bukti","Bukti",95,"center"),("tanggal","Tanggal",130,"w"),
            ("supplier","Pemasok",150,"w"),("produk","Produk",170,"w"),("jumlah","Jumlah (kg)",100,"e"),
            ("subtotal","Subtotal",125,"e"),("metode","Metode",85,"w"),("oleh","Kasir",100,"w")],tinggi=12)
        _fr.pack(fill="both",expand=True,padx=8,pady=(0,12))
        tk.Label(self.tab_beli,text="Daftar Pemasok",font=f(11,True),bg=C["bg"],fg=C["text"]).pack(anchor="w",padx=10,pady=(0,5))
        _fr,self.tree_supplier=buat_tabel(self.tab_beli,[("nama","Nama Pemasok",220,"w"),("telepon","Telepon",160,"w"),("saldo","Saldo Awal Utang",170,"e")],tinggi=6)
        _fr.pack(fill="x",padx=8,pady=(0,10))
        self._muat_pembelian()
        self._muat_supplier()

    def _tambah_supplier(self):
        Dialog(self,"Tambah Supplier",[("nama","Nama Supplier","text",None,""),
            ("telepon","Telepon","text",None,""),("alamat","Alamat","text",None,"")],
            lambda v:self._simpan_supplier(v),info="Data supplier digunakan pada pembelian stok.")

    def _simpan_supplier(self,v):
        self.db.tambah_pihak("supplier",v["nama"],v["telepon"],v["alamat"],0,self.user)
        self._muat_supplier()

    def _muat_supplier(self):
        nama=[r[1] for r in self.db.daftar_pihak("supplier")]
        self.cb_supplier.config(values=nama)
        if self.cb_supplier.get() not in nama and nama: self.cb_supplier.set(nama[-1])
        if hasattr(self,"tree_supplier"):
            isi_tabel(self.tree_supplier,[(n,t or "-",rupiah(s)) for _i,n,t,_alamat,s in self.db.daftar_pihak("supplier")])

    def _simpan_pembelian(self):
        pid=self.opsi_beli.get(self.cb_beli_produk.get())
        if not pid:
            return messagebox.showwarning("Pembelian","Pilih produk terlebih dahulu.",parent=self)
        try:
            ident,total,_ongkir=self.db.pembelian_produk(
                pid,self.cb_supplier.get(),parse_angka(self.beli_kg.get(),"Jumlah"),
                parse_angka(self.beli_hpp.get(),"HPP"),"Tunai",self.user,
                parse_angka(self.beli_ekor.get() or "0","Ekor"))
        except (ValueError,sqlite3.Error) as e:
            return messagebox.showwarning("Pembelian",str(e),parent=self)
        self._muat_pembelian(); self._muat_supplier(); self.muat_produk()
        self.beli_kg.clear(); self.beli_ekor.clear(); self.beli_hpp.clear()
        messagebox.showinfo("Pembelian",f"Pembelian tercatat: PB-{ident:03d} • {rupiah(total)}",parent=self)

    def _muat_pembelian(self):
        if not hasattr(self,"tree_beli"): return
        self.tree_beli.delete(*self.tree_beli.get_children())
        for ident,waktu,supplier,produk,jumlah,_hpp,total,metode,oleh in self.db.daftar_pembelian_rinci():
            self.tree_beli.insert("","end",values=(f"PB-{ident:03d}",str(waktu)[:16],supplier,produk,
                                                   f"{jumlah:g} kg",rupiah(total),metode,oleh))

    def _buat_indukan(self):
        box=kartu(self.tab_indukan); box.pack(fill="x",padx=8,pady=12)
        isi=tk.Frame(box,bg="white"); isi.pack(fill="x",padx=18,pady=16)
        tk.Label(isi,text="Pembelian Indukan Bawal",font=f(12,True),bg="white",fg=C["text"]).grid(row=0,column=0,columnspan=3,sticky="w",pady=(0,10))
        tk.Label(isi,text="Tanggal",font=f(9,True),bg="white",fg=C["text"]).grid(row=1,column=0,sticky="w")
        self.indukan_tanggal=Isian(isi); self.indukan_tanggal.set(datetime.date.today().isoformat()); self.indukan_tanggal.grid(row=2,column=0,sticky="ew",padx=(0,10))
        tk.Label(isi,text="Harga / Jumlah (Rp)",font=f(9,True),bg="white",fg=C["text"]).grid(row=1,column=1,sticky="w")
        self.indukan_jumlah=Isian(isi,numeric=True); self.indukan_jumlah.grid(row=2,column=1,sticky="ew",padx=10)
        tk.Label(isi,text="Keterangan",font=f(9,True),bg="white",fg=C["text"]).grid(row=1,column=2,sticky="w")
        self.indukan_ket=Isian(isi); self.indukan_ket.set("Beli Indukan Bawal"); self.indukan_ket.grid(row=2,column=2,sticky="ew",padx=10)
        for i in range(3): isi.columnconfigure(i,weight=1)
        Tombol(isi,"Catat Pembelian",self._simpan_indukan,warna=C["primary"],tinggi=34,ukuran=9).grid(row=3,column=2,sticky="e",pady=(10,0))
        _fr,self.tree_indukan=buat_tabel(self.tab_indukan,[("bukti","Bukti",95,"center"),("tanggal","Tanggal",140,"w"),
            ("ket","Keterangan",350,"w"),("nilai","Jumlah (Rp)",150,"e"),("oleh","Petugas",130,"w")],tinggi=12)
        _fr.pack(fill="both",expand=True,padx=8,pady=(0,12))
        self._muat_indukan()

    def _simpan_indukan(self):
        try:
            tanggal=self.indukan_tanggal.get().strip()
            datetime.datetime.strptime(tanggal,"%Y-%m-%d")
            bukti=self.db.beli_indukan(parse_angka(self.indukan_jumlah.get(),"Jumlah"),
                                       self.indukan_ket.get(),self.user,tanggal)
        except (ValueError,sqlite3.Error) as e:
            return messagebox.showwarning("Pembelian Indukan",str(e),parent=self)
        self._muat_indukan(); self.indukan_jumlah.clear()
        self.indukan_ket.set("Beli Indukan Bawal")
        messagebox.showinfo("Pembelian Indukan",f"Pembelian tersimpan: {bukti}",parent=self)

    def _muat_indukan(self):
        if not hasattr(self,"tree_indukan"): return
        self.tree_indukan.delete(*self.tree_indukan.get_children())
        for ident,waktu,jumlah,ket,oleh in self.db.daftar_indukan():
            self.tree_indukan.insert("","end",values=(f"PI-{ident:03d}",str(waktu)[:16],ket,rupiah(jumlah),oleh))
